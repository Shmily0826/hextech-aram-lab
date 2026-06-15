#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Prepare augment import candidates from chinese_augment_candidates.json
by identifying augments missing from our current augments.json.
"""

import io
import json
import re
import sys
import os

# Windows UTF-8 console output
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(
        sys.stdout.buffer, encoding="utf-8", errors="replace"
    )
    sys.stderr = io.TextIOWrapper(
        sys.stderr.buffer, encoding="utf-8", errors="replace"
    )

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CANDIDATES_PATH = os.path.join(BASE_DIR, "pipeline", "output", "chinese_augment_candidates.json")
AUGMENTS_PATH = os.path.join(BASE_DIR, "data", "augments.json")
OUTPUT_PATH = os.path.join(BASE_DIR, "pipeline", "output", "augment_import_candidates.json")


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def generate_id(name_en):
    """Generate a snake_case id from an English augment name."""
    s = name_en.lower()
    # Replace apostrophes and special chars
    s = s.replace("'", "")
    s = s.replace("!", "")
    s = s.replace("?", "")
    # Replace spaces and hyphens with underscores
    s = re.sub(r"[\s\-]+", "_", s)
    # Remove any remaining non-alphanumeric/underscore chars
    s = re.sub(r"[^a-z0-9_]", "", s)
    # Collapse multiple underscores
    s = re.sub(r"_+", "_", s)
    s = s.strip("_")
    return s


def is_removed_on_arammayhem(candidate):
    """Check if an augment is marked as removed on arammayhem.com."""
    name_zh = candidate.get("name_zh", "")
    # Removed augments have Chinese names ending with "已移除"
    if "已移除" in name_zh:
        return True
    # Also check for the mystery/??? entries that are effectively placeholders
    slug = candidate.get("slug", "")
    if slug == "mystery-augment":
        return True
    return False


def normalize_name(name):
    """Normalize an English name for comparison."""
    if not name or name == "???":
        return None
    s = name.lower().strip()
    s = s.replace("'", "'").replace("'", "")  # normalize smart quotes
    s = re.sub(r"[^a-z0-9\s]", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def main():
    candidates = load_json(CANDIDATES_PATH)
    augments = load_json(AUGMENTS_PATH)

    print(f"Loaded {len(candidates)} candidates from chinese_augment_candidates.json")
    print(f"Loaded {len(augments)} augments from augments.json")

    # Build a set of current augment English names (normalized) for matching
    current_names = set()
    for aug in augments:
        name_en = aug.get("name_en", "")
        norm = normalize_name(name_en)
        if norm:
            current_names.add(norm)

    print(f"Current augment name index: {len(current_names)} unique English names")

    # Also collect current augment IDs for dedup
    current_ids = {aug.get("id", "") for aug in augments}

    import_candidates = []
    skipped_removed = 0
    skipped_already_present = 0
    skipped_no_english_name = 0
    seen_ids = set()

    for cand in candidates:
        name_en = cand.get("name_en", "")
        name_zh = cand.get("name_zh", "")

        # Skip if no valid English name
        if not name_en or name_en == "???":
            skipped_no_english_name += 1
            continue

        # Skip removed augments
        if is_removed_on_arammayhem(cand):
            skipped_removed += 1
            continue

        # Check if already in current data by English name match
        norm = normalize_name(name_en)
        if norm and norm in current_names:
            skipped_already_present += 1
            continue

        # Generate ID
        aug_id = generate_id(name_en)

        # Dedup by generated ID (keep first occurrence)
        if aug_id in seen_ids:
            continue
        seen_ids.add(aug_id)

        # Determine tier: use tier_wiki as primary, fallback to tier_arammayhem
        tier = cand.get("tier_wiki") or cand.get("tier_arammayhem") or "unknown"
        tier = tier.lower()

        # Description from wiki
        desc_en = cand.get("description_en", "")
        # Filter out the placeholder "YourEnemy Missing pings..." description
        if desc_en.startswith("YourEnemy Missing pings"):
            desc_en = ""

        entry = {
            "id": aug_id,
            "name": name_zh,
            "name_en": name_en,
            "tier": tier,
            "status": "active",
            "effect": "",
            "effect_en": desc_en,
            "source_status": "import_candidate",
            "source": {
                "type": "arammayhem_wiki",
                "url": cand.get("source_url", "")
            }
        }
        import_candidates.append(entry)

    # Save output
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(import_candidates, f, ensure_ascii=False, indent=2)

    # Print statistics
    print(f"\n{'='*60}")
    print(f"IMPORT CANDIDATE PREPARATION COMPLETE")
    print(f"{'='*60}")
    print(f"Total candidates in source file:   {len(candidates)}")
    print(f"Skipped (already in augments.json): {skipped_already_present}")
    print(f"Skipped (removed on arammayhem):    {skipped_removed}")
    print(f"Skipped (no valid English name):    {skipped_no_english_name}")
    print(f"Import candidates generated:        {len(import_candidates)}")

    # Tier breakdown
    tier_counts = {}
    for c in import_candidates:
        t = c["tier"]
        tier_counts[t] = tier_counts.get(t, 0) + 1
    print(f"\nBy tier:")
    for t in sorted(tier_counts.keys()):
        print(f"  {t:12s}: {tier_counts[t]}")

    # Wiki description coverage
    with_desc = sum(1 for c in import_candidates if c["effect_en"])
    without_desc = len(import_candidates) - with_desc
    print(f"\nWiki description coverage:")
    print(f"  With description:    {with_desc}")
    print(f"  Without description: {without_desc}")

    print(f"\nOutput saved to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
