"""
cleanup_fabricated_data.py
Clean all fabricated/prototype data from augments.json, reports.json, issues.json.

Actions:
1. augments.json:
   - Remove 13 prototype augments (marked with "原型增强" notes, not in champion_recs)
   - Strip fabricated fields (wr, pr, best, avoid, trigger, desc) from remaining augments
2. reports.json: Replace with empty array []
3. issues.json: Replace with empty array []

Safety: backs up originals to pipeline/output/ before writing.
"""
import json
import os
import shutil
from datetime import datetime

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, 'data')
BACKUP_DIR = os.path.join(PROJECT_ROOT, 'pipeline', 'output')

FABRICATED_FIELDS = {'wr', 'pr', 'best', 'avoid', 'trigger', 'desc'}


def backup_file(filepath):
    """Backup a file to pipeline/output/ with timestamp."""
    if not os.path.exists(filepath):
        return None
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    basename = os.path.basename(filepath)
    name, ext = os.path.splitext(basename)
    backup_path = os.path.join(BACKUP_DIR, f"{name}_backup_{ts}{ext}")
    shutil.copy2(filepath, backup_path)
    print(f"  Backed up: {filepath} -> {backup_path}")
    return backup_path


def load_json(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json(filepath, data):
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  Saved: {filepath}")


def get_real_augment_ids():
    """Get augment IDs that appear in champion_recs (real blitz.gg data)."""
    cr_path = os.path.join(DATA_DIR, 'champion_recs.json')
    cr = load_json(cr_path)
    return set(cr.get('data', {}).keys())


def clean_augments():
    """Clean augments.json: remove prototypes, strip fabricated fields."""
    filepath = os.path.join(DATA_DIR, 'augments.json')
    backup_file(filepath)

    augs = load_json(filepath)
    real_ids = get_real_augment_ids()

    original_count = len(augs)
    removed_prototypes = []
    stripped_count = 0
    kept_count = 0

    cleaned = []
    for a in augs:
        aid = a.get('id', '')
        notes = a.get('notes') or ''
        is_prototype = '原型' in notes and aid not in real_ids

        if is_prototype:
            removed_prototypes.append(f"  {aid}: {a.get('name', '?')}")
            continue

        # Strip fabricated fields
        removed_fields = []
        for field in FABRICATED_FIELDS:
            if field in a:
                del a[field]
                removed_fields.append(field)
        if removed_fields:
            stripped_count += 1

        # Also remove source_status if it says "prototype"
        if a.get('source_status') == 'prototype':
            del a['source_status']

        cleaned.append(a)
        kept_count += 1

    save_json(filepath, cleaned)

    print(f"\n  augments.json: {original_count} -> {kept_count}")
    print(f"  Removed {len(removed_prototypes)} prototype augments:")
    for p in removed_prototypes:
        print(f"    {p}")
    print(f"  Stripped fabricated fields from {stripped_count} augments")

    return removed_prototypes


def clean_reports():
    """Replace reports.json with empty array."""
    filepath = os.path.join(DATA_DIR, 'reports.json')
    old = load_json(filepath)
    backup_file(filepath)
    save_json(filepath, [])
    print(f"\n  reports.json: cleared (was {len(old)} entries)")


def clean_issues():
    """Replace issues.json with empty array."""
    filepath = os.path.join(DATA_DIR, 'issues.json')
    old = load_json(filepath)
    backup_file(filepath)
    save_json(filepath, [])
    print(f"\n  issues.json: cleared (was {len(old)} entries)")


def validate():
    """Validate the cleaned files."""
    print("\n=== Validation ===")

    # Check augments.json
    augs = load_json(os.path.join(DATA_DIR, 'augments.json'))
    print(f"  augments.json: {len(augs)} entries")

    # Verify no prototype augments remain
    for a in augs:
        notes = a.get('notes') or ''
        if '原型' in notes:
            print(f"  WARNING: prototype augment still present: {a['id']}")

    # Verify no fabricated fields
    fab_count = 0
    for a in augs:
        for field in FABRICATED_FIELDS:
            if field in a:
                fab_count += 1
                print(f"  WARNING: fabricated field '{field}' in {a['id']}")
                break
    if fab_count == 0:
        print(f"  OK: No fabricated fields (wr/pr/best/avoid/trigger/desc) found")

    # Check reports.json
    reports = load_json(os.path.join(DATA_DIR, 'reports.json'))
    print(f"  reports.json: {len(reports)} entries (should be 0)")

    # Check issues.json
    issues = load_json(os.path.join(DATA_DIR, 'issues.json'))
    print(f"  issues.json: {len(issues)} entries (should be 0)")

    # Cross-check: all augments should have basic required fields
    required = {'id', 'name', 'tier', 'status'}
    missing = 0
    for a in augs:
        for field in required:
            if field not in a:
                print(f"  WARNING: {a.get('id', '?')} missing required field '{field}'")
                missing += 1
    if missing == 0:
        print(f"  OK: All augments have required fields (id, name, tier, status)")

    print("\n=== Cleanup Complete ===")


if __name__ == '__main__':
    print("=== Cleaning Fabricated Data ===\n")

    print("--- Step 1: Clean augments.json ---")
    clean_augments()

    print("\n--- Step 2: Clean reports.json ---")
    clean_reports()

    print("\n--- Step 3: Clean issues.json ---")
    clean_issues()

    print("\n--- Step 4: Validate ---")
    validate()
