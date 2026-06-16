"""
merge_approved_augments.py
==========================
Safely merge data/approved_augments.json into data/augments.json.

Rules:
  1. Backup augments.json before any write
  2. For overlapping IDs: preserve ALL existing rich data (tags, patch_added,
     best/avoid, tests, notes, wr, pr, trigger, aliases, rar, desc).
     Only update effect/effect_en from approved (blitz.gg data).
  3. For can_t_touch_this: KEEP existing name "碰不到我" (untouchable = "你摸不到")
  4. For new entries: add with basic structure + derive name_en from ID if empty
  5. Strip internal fields (_source_blitz, _newly_added)
  6. Sort output: prismatic first, then gold, then silver; within tier by id
  7. Validate result
"""

import json
import shutil
import sys
import os
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

# ── Paths ──────────────────────────────────────────────────
AUGMENTS_PATH = 'data/augments.json'
APPROVED_PATH  = 'data/approved_augments.json'
BACKUP_DIR     = 'pipeline/output'

# ── Name conflict overrides ────────────────────────────────
# can_t_touch_this: existing has "碰不到我", approved has "你摸不到"
# "碰不到我" is correct because untouchable = "你摸不到" (different augment)
NAME_OVERRIDES = {
    'can_t_touch_this': '碰不到我',
}

# ── Special name_en fixes (not simple title-case) ──────────
SPECIAL_NAME_EN = {
    'don_t_stop_channeling': "Don't Stop Channeling",
    'can_t_touch_this': "Can't Touch This",
    'wee_oo_wee_oo': "Wee Oo Wee Oo",
    'stackasaurus': "Stackasaurus",
    'overextender': "Overextender",
    'porcupine': "Porcupine",
    'goredrink': "Goredrink",
    'homeguard': "Homeguard",
    'dropkick': "Dropkick",
    'deft': "Deft",
    'bang': "Bang",
    'goliath': "Goliath",
    'terror': "Terror",
    'zealot': "Zealot",
    'support_main': "Support Main",
    'first_aid_kit': "First-Aid Kit",
    'all_for_you': "All For You",
    'bread_and_butter': "Bread and Butter",
    'fan_the_hammer': "Fan the Hammer",
    'back_to_basics': "Back to Basics",
    'biggest_snowball_ever': "Biggest Snowball Ever",
    'get_excited': "Get Excited",
}

# ── Tier sort order ────────────────────────────────────────
TIER_ORDER = {'prismatic': 0, 'gold': 1, 'silver': 2}

# ── Fields to strip from imported entries ──────────────────
STRIP_FIELDS = {'_source_blitz', '_newly_added', 'source_status'}


def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write('\n')


def derive_name_en(augment_id):
    """Derive a readable English name from a snake_case ID."""
    if augment_id in SPECIAL_NAME_EN:
        return SPECIAL_NAME_EN[augment_id]
    # Default: title-case the snake_case ID
    return augment_id.replace('_', ' ').title()


def merge_overlap(existing_entry, approved_entry):
    """
    For overlapping entries: preserve existing rich data,
    only update effect/effect_en from approved (blitz.gg).
    """
    merged = dict(existing_entry)  # copy all existing fields

    # Update effect descriptions from blitz.gg approved data
    if approved_entry.get('effect', '').strip():
        merged['effect'] = approved_entry['effect']
    if approved_entry.get('effect_en', '').strip():
        merged['effect_en'] = approved_entry['effect_en']

    # Preserve existing name (especially can_t_touch_this = "碰不到我")
    aid = existing_entry['id']
    if aid in NAME_OVERRIDES:
        merged['name'] = NAME_OVERRIDES[aid]
    else:
        merged['name'] = existing_entry['name']

    # Ensure name_en is filled (existing should have it)
    if not merged.get('name_en', '').strip():
        merged['name_en'] = derive_name_en(aid)

    # Strip internal fields
    for field in STRIP_FIELDS:
        merged.pop(field, None)

    return merged


def build_new_entry(approved_entry):
    """
    For new entries: build from approved data with proper structure.
    """
    entry = {
        'id': approved_entry['id'],
        'name': approved_entry['name'],
        'name_en': approved_entry.get('name_en', '').strip() or derive_name_en(approved_entry['id']),
        'tier': approved_entry.get('tier', 'unknown'),
        'status': approved_entry.get('status', 'active'),
        'effect': approved_entry.get('effect', ''),
        'effect_en': approved_entry.get('effect_en', ''),
        'source': approved_entry.get('source', {'type': 'blitz_gg'}),
    }

    # Copy any extra approved fields (but not internal ones)
    for key, val in approved_entry.items():
        if key not in entry and key not in STRIP_FIELDS:
            entry[key] = val

    return entry


def validate_result(result, existing_count, approved_count, overlap_count):
    """Basic validation of merge result."""
    errors = []
    expected = existing_count + approved_count - overlap_count

    if len(result) != expected:
        errors.append(
            f"Count mismatch: expected {expected} "
            f"({existing_count} existing + {approved_count} approved - {overlap_count} overlap), "
            f"got {len(result)}"
        )

    # Check for duplicate IDs
    ids = [e['id'] for e in result]
    dupes = [i for i in ids if ids.count(i) > 1]
    if dupes:
        errors.append(f"Duplicate IDs: {set(dupes)}")

    # Check all required fields
    required = {'id', 'name', 'tier', 'status', 'effect'}
    for e in result:
        missing = required - set(e.keys())
        if missing:
            errors.append(f"Entry {e.get('id', '?')} missing fields: {missing}")

    # Check name_en filled
    empty_en = [e['id'] for e in result if not e.get('name_en', '').strip()]
    if empty_en:
        errors.append(f"Entries with empty name_en: {empty_en}")

    return errors


def main():
    print("=" * 60)
    print("  Augment Merge: approved_augments.json -> augments.json")
    print("=" * 60)

    # 1. Load data
    existing = load_json(AUGMENTS_PATH)
    approved = load_json(APPROVED_PATH)
    print(f"\n  Loaded: {len(existing)} existing, {len(approved)} approved")

    # 2. Build lookup
    existing_map = {e['id']: e for e in existing}
    approved_map = {a['id']: a for a in approved}
    overlap_ids = set(existing_map.keys()) & set(approved_map.keys())
    new_ids = set(approved_map.keys()) - set(existing_map.keys())
    existing_only = set(existing_map.keys()) - set(approved_map.keys())

    print(f"  Overlap: {len(overlap_ids)}, New: {len(new_ids)}, Existing-only: {len(existing_only)}")

    # 3. Backup
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = os.path.join(BACKUP_DIR, f'augments_backup_{timestamp}.json')
    shutil.copy2(AUGMENTS_PATH, backup_path)
    print(f"  Backup: {backup_path}")

    # 4. Build merged result
    result = []

    # 4a. Existing-only entries (not in approved) — keep as-is
    for eid in sorted(existing_only):
        entry = dict(existing_map[eid])
        for field in STRIP_FIELDS:
            entry.pop(field, None)
        result.append(entry)
    print(f"  Existing-only kept: {len(existing_only)}")

    # 4b. Overlapping entries — preserve existing rich data, update effect/effect_en
    for oid in sorted(overlap_ids):
        merged = merge_overlap(existing_map[oid], approved_map[oid])
        result.append(merged)
    print(f"  Overlapping merged: {len(overlap_ids)}")

    # 4c. New entries — build from approved
    for nid in sorted(new_ids):
        entry = build_new_entry(approved_map[nid])
        result.append(entry)
    print(f"  New entries added: {len(new_ids)}")

    # 5. Sort: by tier (prismatic > gold > silver), then by id
    result.sort(key=lambda e: (TIER_ORDER.get(e.get('tier', 'unknown'), 99), e['id']))

    # 6. Validate
    errors = validate_result(result, len(existing), len(approved), len(overlap_ids))
    if errors:
        print(f"\n  VALIDATION ERRORS:")
        for err in errors:
            print(f"    - {err}")
        print(f"\n  Merge aborted. Backup at: {backup_path}")
        sys.exit(1)
    else:
        print(f"\n  Validation passed: {len(result)} entries, no errors")

    # 7. Write
    save_json(AUGMENTS_PATH, result)
    print(f"  Written to: {AUGMENTS_PATH}")

    # 8. Verify by re-reading
    verify = load_json(AUGMENTS_PATH)
    if len(verify) != len(result):
        print(f"  WRITE VERIFICATION FAILED: wrote {len(result)}, read back {len(verify)}")
        sys.exit(1)

    # 9. Summary
    print(f"\n{'=' * 60}")
    print(f"  MERGE COMPLETE")
    print(f"  Total augments: {len(result)}")
    print(f"    - Existing-only (untouched): {len(existing_only)}")
    print(f"    - Overlapping (effect updated): {len(overlap_ids)}")
    print(f"    - New imports: {len(new_ids)}")

    # Count by tier
    tier_counts = {}
    for e in result:
        t = e.get('tier', 'unknown')
        tier_counts[t] = tier_counts.get(t, 0) + 1
    print(f"    - By tier: {tier_counts}")

    # Name conflict resolution
    if NAME_OVERRIDES:
        print(f"  Name overrides applied:")
        for k, v in NAME_OVERRIDES.items():
            print(f"    {k}: -> {v}")

    print(f"  Backup: {backup_path}")
    print(f"{'=' * 60}")


if __name__ == '__main__':
    main()
