#!/usr/bin/env python3
"""
Merge Chinese augment data from arammayhem.com with English Wiki data.
Produces a comprehensive candidate file for human review.

Outputs: pipeline/output/chinese_augment_candidates.json
"""
import io
import json
import os
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

LIST_PATH = os.path.join(PROJECT_ROOT, "pipeline/output/arammayhem_augment_list.json")
WIKI_PATH = os.path.join(PROJECT_ROOT, "pipeline/output/wiki_augments_english.json")
AUGMENTS_PATH = os.path.join(PROJECT_ROOT, "data/augments.json")
OUTPUT_PATH = os.path.join(PROJECT_ROOT, "pipeline/output/chinese_augment_candidates.json")


def slugify(name):
    """Convert an English name to a URL-friendly slug."""
    s = name.lower().strip()
    # Replace common special chars
    s = s.replace("'", "").replace("'", "").replace(".", "").replace("!", "")
    s = s.replace(":", "-").replace(" ", "-").replace("_", "-")
    s = s.replace("&", "and").replace("+", "and")
    # Remove non-alphanumeric except hyphens
    s = re.sub(r"[^a-z0-9-]", "", s)
    # Collapse multiple hyphens
    s = re.sub(r"-+", "-", s)
    return s.strip("-")


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    # Load data sources
    print("[1/4] Loading data sources...")
    zh_list = load_json(LIST_PATH)
    wiki_en = load_json(WIKI_PATH)
    existing = load_json(AUGMENTS_PATH)

    print(f"  arammayhem.com Chinese list: {len(zh_list)} entries")
    print(f"  Wiki English data: {len(wiki_en)} entries")
    print(f"  Existing augments.json: {len(existing)} entries")

    # Build slug → Wiki entry mapping
    print("\n[2/4] Building slug mappings...")
    wiki_by_slug = {}
    for w in wiki_en:
        slug = slugify(w["name"])
        wiki_by_slug[slug] = w

    # Build existing augment lookup by normalized key
    existing_by_key = {}
    for a in existing:
        # Map by id
        aid = a.get("id", "").lower().replace("_", "-").replace(" ", "-")
        existing_by_key[aid] = a
        # Map by English name slug
        name_en = a.get("name_en", "")
        if name_en:
            name_key = slugify(name_en)
            existing_by_key[name_key] = a
        # Map by Chinese name
        name_zh = a.get("name", "")
        if name_zh:
            existing_by_key[name_zh] = a

    # Match Chinese entries with Wiki data
    print("\n[3/4] Matching Chinese ↔ English data...")
    candidates = []
    matched = 0
    unmatched_zh = 0
    tier_conflicts = 0

    for zh in zh_list:
        slug = zh["slug"]
        entry = {
            "slug": slug,
            "name_zh": zh["name_zh"],
            "tier_arammayhem": zh.get("tier", ""),
            "tier_zh": zh.get("tier_zh", ""),
            "rank_on_site": zh.get("rank", 0),
            "source_url": f"https://arammayhem.com{zh.get('url', '')}",
        }

        # Try exact slug match
        wiki_match = wiki_by_slug.get(slug)

        # Try fuzzy match if no exact match
        if not wiki_match:
            for ws, w in wiki_by_slug.items():
                if slug == ws or slug in ws or ws in slug:
                    wiki_match = w
                    break

        # Try matching by slugifying known aliases
        if not wiki_match:
            # Try removing common prefixes/suffixes
            for ws, w in wiki_by_slug.items():
                if (slug.replace("quest-", "") == ws.replace("quest-", "") or
                    slug.replace("upgrade-", "") == ws.replace("upgrade-", "")):
                    wiki_match = w
                    break

        if wiki_match:
            entry["name_en"] = wiki_match["name"]
            entry["tier_wiki"] = wiki_match["tier"]
            entry["set"] = wiki_match.get("set", "")
            entry["description_en"] = wiki_match.get("description", "")
            entry["wiki_matched"] = True
            matched += 1

            # Check tier conflict
            if zh.get("tier") and wiki_match["tier"] and zh["tier"] != wiki_match["tier"]:
                entry["tier_conflict"] = True
                tier_conflicts += 1
            else:
                entry["tier_conflict"] = False
        else:
            entry["name_en"] = ""
            entry["tier_wiki"] = ""
            entry["set"] = ""
            entry["description_en"] = ""
            entry["wiki_matched"] = False
            entry["tier_conflict"] = False
            unmatched_zh += 1

        # Check if this augment exists in our current data
        existing_match = existing_by_key.get(slug)
        if not existing_match and entry.get("name_en"):
            # Try by English name slug
            en_key = slugify(entry["name_en"])
            existing_match = existing_by_key.get(en_key)
        if not existing_match:
            # Try by Chinese name
            existing_match = existing_by_key.get(zh["name_zh"])

        if existing_match:
            entry["in_current_data"] = True
            entry["current_name_en"] = existing_match.get("name_en", existing_match.get("name", ""))
            entry["current_name_zh"] = existing_match.get("name", "")  # 'name' field IS the Chinese name
            entry["current_effect_zh"] = existing_match.get("effect", "")
        else:
            entry["in_current_data"] = False

        candidates.append(entry)

    print(f"  Matched with Wiki: {matched}/{len(zh_list)}")
    print(f"  Unmatched Chinese: {unmatched_zh}")
    print(f"  Tier conflicts: {tier_conflicts}")

    # Find Wiki entries NOT in the Chinese list (may be removed/new)
    zh_slugs = {zh["slug"] for zh in zh_list}
    wiki_only = []
    for slug, w in wiki_by_slug.items():
        if slug not in zh_slugs:
            # Check fuzzy
            found = False
            for zs in zh_slugs:
                if slug in zs or zs in slug:
                    found = True
                    break
            if not found:
                wiki_only.append(w["name"])

    print(f"  Wiki entries not on arammayhem: {len(wiki_only)}")
    if wiki_only:
        for name in wiki_only[:10]:
            print(f"    - {name}")
        if len(wiki_only) > 10:
            print(f"    ... and {len(wiki_only) - 10} more")

    # Save candidates
    print(f"\n[4/4] Saving candidates to {OUTPUT_PATH}...")
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(candidates, f, ensure_ascii=False, indent=2)

    # Summary stats
    in_current = sum(1 for c in candidates if c.get("in_current_data"))
    new_augments = sum(1 for c in candidates if not c.get("in_current_data") and c.get("wiki_matched"))
    completely_new = sum(1 for c in candidates if not c.get("in_current_data") and not c.get("wiki_matched"))

    print(f"\n{'='*60}")
    print(f"SUMMARY")
    print(f"{'='*60}")
    print(f"  Total candidates: {len(candidates)}")
    print(f"  Already in augments.json: {in_current}")
    print(f"  New (matched Wiki): {new_augments}")
    print(f"  New (unmatched): {completely_new}")
    print(f"  Tier conflicts: {tier_conflicts}")
    print(f"  Wiki-only (not on site): {len(wiki_only)}")

    # Show examples of existing augments with Chinese name comparison
    print(f"\n--- Chinese name comparison (existing augments) ---")
    shown = 0
    for c in candidates:
        if c.get("in_current_data") and c.get("current_name_zh"):
            old_zh = c["current_name_zh"]
            new_zh = c["name_zh"]
            match = "✓" if old_zh == new_zh else "✗ DIFF"
            print(f"  {c.get('name_en', c['slug']):>25} | Old: {old_zh:<15} | New: {new_zh:<15} | {match}")
            shown += 1
            if shown >= 20:
                break


if __name__ == "__main__":
    main()
