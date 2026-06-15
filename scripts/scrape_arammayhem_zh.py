#!/usr/bin/env python3
"""
Scrape Chinese augment names and effects from arammayhem.com/zh-cn.
Uses only Python stdlib (urllib + html.parser).

Outputs: pipeline/output/arammayhem_chinese_augments.json
"""

import io
import json
import re
import sys
import time
import urllib.request
import urllib.error
from html.parser import HTMLParser

# Fix Windows console encoding for Chinese characters
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

BASE_URL = "https://arammayhem.com/zh-cn/augments"
USER_AGENT = "aram-insight-pipeline/1.0 (research bot; contact@example.com)"
DELAY_S = 1.5  # polite delay between requests
TIMEOUT_S = 30


# ---------------------------------------------------------------------------
# HTML Parsers
# ---------------------------------------------------------------------------

def clean_list_entry(raw_text):
    """Clean the raw text from the list page.

    Format: {rank}{chinese_name}[新]{tier}{stat%}{stat%}{stat%}
    Examples:
        '1质变：棱彩阶金色69.86%67.38%69.86%'
        '2急速之追求新金色70.14%64.41%70.14%'
    """
    text = raw_text.strip()

    # Step 1: Strip trailing stats (e.g. "69.86%67.38%69.86%")
    no_stats = re.sub(r"[\d.]+%[\d.]*%*[\d.]*%*$", "", text)
    # May have multiple stat groups, strip them all
    no_stats = re.sub(r"([\d.]+%)+$", "", no_stats)

    # Step 2: Find the LAST occurrence of a tier label (银色/金色/棱彩)
    # The actual tier is always the LAST one in the string
    tier_zh = ""
    tier_en = ""
    tier_pos = -1
    for tz, te in [("银色", "Silver"), ("金色", "Gold"), ("棱彩", "Prismatic")]:
        idx = no_stats.rfind(tz)
        if idx > tier_pos:
            tier_pos = idx
            tier_zh = tz
            tier_en = te

    # Step 3: Extract rank (leading digits)
    rank_match = re.match(r"^(\d+)", text)
    rank = int(rank_match.group(1)) if rank_match else 0

    # Step 4: Extract name = text between rank and tier position
    if tier_pos >= 0:
        name_part = no_stats[len(str(rank)):tier_pos]
    else:
        name_part = no_stats[len(str(rank)):]

    # Remove '新' (new) marker
    name_zh = name_part.replace("新", "").strip()

    return {
        "rank": rank,
        "name_zh": name_zh,
        "tier_zh": tier_zh,
        "tier": tier_en,
    }


class AugmentListParser(HTMLParser):
    """Parse the augment list page to extract augment slugs and Chinese names."""

    def __init__(self):
        super().__init__()
        self.augments = []  # list of {slug, name_zh, tier, ...}
        self._in_link = False
        self._current_href = ""
        self._current_text = ""
        self._capture = False

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            attrs_dict = dict(attrs)
            href = attrs_dict.get("href", "")
            if "/zh-cn/augments/" in href and href != "/zh-cn/augments/" and href != "/zh-cn/augments":
                self._in_link = True
                self._current_href = href
                self._current_text = ""
                self._capture = True

    def handle_data(self, data):
        if self._capture:
            self._current_text += data.strip()

    def handle_endtag(self, tag):
        if tag == "a" and self._in_link:
            self._in_link = False
            self._capture = False
            if self._current_text:
                # Extract slug from URL
                slug = self._current_href.rstrip("/").split("/")[-1]
                cleaned = clean_list_entry(self._current_text)
                entry = {
                    "slug": slug,
                    "name_zh": cleaned["name_zh"],
                    "tier": cleaned["tier"],
                    "tier_zh": cleaned["tier_zh"],
                    "rank": cleaned["rank"],
                    "url": self._current_href,
                }
                self.augments.append(entry)


class AugmentDetailParser(HTMLParser):
    """Parse an individual augment detail page."""

    def __init__(self):
        super().__init__()
        self.data = {}
        self._in_heading = False
        self._in_paragraph = False
        self._paragraphs = []
        self._heading_text = ""
        self._current_paragraph = ""
        self._in_span = False
        self._span_class = ""
        self._span_text = ""
        self._spans = []
        self._in_table = False
        self._in_td = False
        self._td_text = ""
        self._table_rows = []
        self._current_row = []

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        if tag in ("h1", "h2", "h3"):
            self._in_heading = True
            self._heading_text = ""
        elif tag == "p":
            self._in_paragraph = True
            self._current_paragraph = ""
        elif tag == "span":
            cls = attrs_dict.get("class", "")
            if "tier" in cls.lower() or "rarity" in cls.lower() or "badge" in cls.lower():
                self._in_span = True
                self._span_class = cls
                self._span_text = ""
        elif tag == "td":
            self._in_td = True
            self._td_text = ""
        elif tag == "tr":
            self._current_row = []
        elif tag == "table":
            self._in_table = True

    def handle_data(self, data):
        text = data.strip()
        if not text:
            return
        if self._in_heading:
            self._heading_text += text
        if self._in_paragraph:
            self._current_paragraph += text
        if self._in_span:
            self._span_text += text
        if self._in_td:
            self._td_text += text

    def handle_endtag(self, tag):
        if tag in ("h1", "h2", "h3") and self._in_heading:
            self._in_heading = False
            if self._heading_text:
                self.data.setdefault("headings", []).append(self._heading_text)
        elif tag == "p" and self._in_paragraph:
            self._in_paragraph = False
            if self._current_paragraph:
                self._paragraphs.append(self._current_paragraph)
        elif tag == "span" and self._in_span:
            self._in_span = False
            if self._span_text:
                self._spans.append({"class": self._span_class, "text": self._span_text})
        elif tag == "td" and self._in_td:
            self._in_td = False
            self._current_row.append(self._td_text)
        elif tag == "tr":
            if self._current_row:
                self._table_rows.append(self._current_row)
        elif tag == "table":
            self._in_table = False

    def get_effect(self):
        """Try to extract the effect description from paragraphs."""
        for p in self._paragraphs:
            # Skip very short paragraphs (likely tier/set labels)
            if len(p) > 30:
                return p
        return self._paragraphs[0] if self._paragraphs else ""

    def get_tier(self):
        """Try to extract tier from spans or headings."""
        tier_map = {
            "银色": "Silver", "silver": "Silver",
            "金色": "Gold", "gold": "Gold",
            "棱彩": "Prismatic", "prismatic": "Prismatic",
        }
        for span in self._spans:
            for key, val in tier_map.items():
                if key in span["text"]:
                    return val
        for heading in self.data.get("headings", []):
            for key, val in tier_map.items():
                if key in heading:
                    return val
        return ""


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

def fetch_url(url):
    """Fetch a URL and return the decoded HTML, or None on error."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_S) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except (urllib.error.URLError, urllib.error.HTTPError, OSError) as e:
        print(f"  [WARN] Failed to fetch {url}: {e}", file=sys.stderr)
        return None


# ---------------------------------------------------------------------------
# Main scraping logic
# ---------------------------------------------------------------------------

def scrape_augment_list():
    """Scrape the main augment list page."""
    print("[1/3] Fetching augment list page...")
    html = fetch_url(BASE_URL)
    if not html:
        print("  ERROR: Could not fetch augment list page", file=sys.stderr)
        return []

    parser = AugmentListParser()
    parser.feed(html)
    print(f"  Found {len(parser.augments)} augment links")
    return parser.augments


def scrape_augment_detail(slug):
    """Scrape an individual augment detail page."""
    url = f"{BASE_URL}/{slug}/"
    html = fetch_url(url)
    if not html:
        return None

    parser = AugmentDetailParser()
    parser.feed(html)
    return {
        "effect_zh": parser.get_effect(),
        "tier": parser.get_tier(),
        "headings": parser.data.get("headings", []),
    }


def scrape_all(sample=None, limit=None):
    """Main entry: scrape list + details."""
    augments_list = scrape_augment_list()
    if not augments_list:
        return []

    if sample:
        augments_list = augments_list[:sample]
    if limit:
        augments_list = augments_list[:limit]

    results = []
    total = len(augments_list)
    print(f"\n[2/3] Fetching {total} augment detail pages...")

    for i, aug in enumerate(augments_list):
        slug = aug["slug"]
        name_zh = aug["name_zh"]
        print(f"  [{i+1}/{total}] {name_zh} ({slug})")

        detail = scrape_augment_detail(slug)
        entry = {
            "slug": slug,
            "name_zh": name_zh,
            "url": aug.get("url", ""),
        }
        if detail:
            entry["effect_zh"] = detail["effect_zh"]
            entry["tier"] = detail["tier"]
        else:
            entry["effect_zh"] = ""
            entry["tier"] = ""

        results.append(entry)

        if i < total - 1:
            time.sleep(DELAY_S)

    return results


def merge_with_wiki(results, wiki_path):
    """Merge Chinese data with English Wiki data by slug→name matching."""
    try:
        with open(wiki_path, "r", encoding="utf-8") as f:
            wiki_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        print("  [WARN] Could not load Wiki data, skipping merge", file=sys.stderr)
        return results

    # Build slug → wiki entry mapping
    def slugify(name):
        return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")

    wiki_by_slug = {}
    for w in wiki_data:
        s = slugify(w["name"])
        wiki_by_slug[s] = w

    matched = 0
    for r in results:
        slug = r["slug"]
        if slug in wiki_by_slug:
            w = wiki_by_slug[slug]
            r["name_en"] = w["name"]
            r["tier_en"] = w["tier"]
            r["set_en"] = w.get("set", "")
            r["description_en"] = w.get("description", "")
            matched += 1
        else:
            # Try fuzzy match
            for ws, w in wiki_by_slug.items():
                if ws == slug or slug in ws or ws in slug:
                    r["name_en"] = w["name"]
                    r["tier_en"] = w["tier"]
                    r["set_en"] = w.get("set", "")
                    r["description_en"] = w.get("description", "")
                    matched += 1
                    break

    print(f"  Matched {matched}/{len(results)} with Wiki data")
    return results


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Scrape ARAM Mayhem Chinese augment data")
    parser.add_argument("--sample", type=int, default=0, help="Only scrape first N augments (0=all)")
    parser.add_argument("--limit", type=int, default=0, help="Limit total augments to scrape")
    parser.add_argument("--output", default="pipeline/output/arammayhem_chinese_augments.json",
                        help="Output JSON file path")
    parser.add_argument("--wiki", default="pipeline/output/wiki_augments_english.json",
                        help="Wiki English data for cross-reference")
    parser.add_argument("--list-only", action="store_true", help="Only scrape list page, skip details")
    args = parser.parse_args()

    # Resolve paths relative to project root
    import os
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_path = os.path.join(project_root, args.output)
    wiki_path = os.path.join(project_root, args.wiki)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    sample = args.sample if args.sample > 0 else None
    limit = args.limit if args.limit > 0 else None

    if args.list_only:
        results = scrape_augment_list()
        # Just save the list
        print(f"\n[3/3] Saving {len(results)} entries to {output_path}")
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"Done! Saved {len(results)} augment entries.")
    else:
        results = scrape_all(sample=sample, limit=limit)
        print(f"\n[3/3] Merging with Wiki data and saving...")
        results = merge_with_wiki(results, wiki_path)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        # Summary
        with_tier = sum(1 for r in results if r.get("tier"))
        with_effect = sum(1 for r in results if r.get("effect_zh"))
        with_en = sum(1 for r in results if r.get("name_en"))
        print(f"\nDone! Saved {len(results)} augment entries to {output_path}")
        print(f"  With Chinese tier: {with_tier}")
        print(f"  With Chinese effect: {with_effect}")
        print(f"  Matched with English: {with_en}")


if __name__ == "__main__":
    main()
