"""
update_aug_stats.py
Update augments.json win_rate/pick_rate from corrected scrape data.
Follows backup→write→validate→rollback pattern.
"""
import json
import os
import shutil
import sys
from datetime import datetime, timezone

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUG_PATH = os.path.join(PROJECT_ROOT, 'data', 'augments.json')
SCRAPE_PATH = os.path.join(PROJECT_ROOT, 'pipeline', 'output', 'arammayhem_stats_scrape.json')
BACKUP_DIR = os.path.join(PROJECT_ROOT, 'backups')

def main():
    # Load scrape data
    with open(SCRAPE_PATH, encoding='utf-8') as f:
        scrape_data = json.load(f)
    scrape = scrape_data.get('matched', scrape_data) if isinstance(scrape_data, dict) else scrape_data
    print(f"Loaded {len(scrape)} entries from scrape")

    # Build lookup: local_id -> {win_rate, pick_rate, rank}
    lookup = {}
    for entry in scrape:
        local_id = entry.get('local_id', '')
        name_en = entry.get('name_en', '')
        slug = entry.get('slug', '')
        wr = entry.get('win_rate')
        pr = entry.get('pick_rate')
        rank = entry.get('rank')
        if wr is not None or pr is not None:
            key = local_id or slug or name_en
            if key:
                lookup[key] = {'win_rate': wr, 'pick_rate': pr, 'rank': rank}
    print(f"Built lookup with {len(lookup)} entries")

    # Load augments
    with open(AUG_PATH, encoding='utf-8') as f:
        augs = json.load(f)
    print(f"Loaded {len(augs)} augments")

    # Backup
    os.makedirs(BACKUP_DIR, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
    backup_path = os.path.join(BACKUP_DIR, f'augments_backup_{ts}.json')
    shutil.copy2(AUG_PATH, backup_path)
    print(f"Backup: {backup_path}")

    # Update
    updated = 0
    no_match = []
    for aug in augs:
        name_en = aug.get('name_en', '')
        aug_id = aug.get('id', '')
        # Try matching by local_id (aug id), then by name_en, then by slug
        info = lookup.get(aug_id) or lookup.get(name_en) or lookup.get(aug_id.replace('_', '-'))
        if info:
            old_wr = aug.get('win_rate')
            old_pr = aug.get('pick_rate')
            if info['win_rate'] is not None:
                aug['win_rate'] = info['win_rate']
            if info['pick_rate'] is not None:
                aug['pick_rate'] = info['pick_rate']
            if info['rank'] is not None:
                aug['site_rank'] = info['rank']
            aug['stats_updated'] = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
            if old_wr != aug.get('win_rate') or old_pr != aug.get('pick_rate'):
                updated += 1
        else:
            no_match.append(f"{aug_id}: {aug.get('name', '?')} ({name_en})")

    # Validate: check win_rate range
    wr_values = [a['win_rate'] for a in augs if 'win_rate' in a and a['win_rate'] is not None]
    if wr_values:
        wr_min = min(wr_values)
        wr_max = max(wr_values)
        wr_avg = sum(wr_values) / len(wr_values)
        print(f"\nValidation: win_rate range = {wr_min:.2f}% ~ {wr_max:.2f}%, avg = {wr_avg:.2f}%")
        if wr_min < 10 or wr_max > 90:
            print("WARNING: win_rate values look suspicious! Rolling back...")
            shutil.copy2(backup_path, AUG_PATH)
            sys.exit(1)

    # Write
    with open(AUG_PATH, 'w', encoding='utf-8') as f:
        json.dump(augs, f, ensure_ascii=False, indent=2)
    print(f"\nUpdated {updated} augments")
    print(f"No match: {len(no_match)} augments")
    for nm in no_match[:5]:
        print(f"  - {nm}")

    # Verify
    with open(AUG_PATH, encoding='utf-8') as f:
        verify = json.load(f)
    if len(verify) == len(augs):
        print(f"\nVerify OK: {len(verify)} augments")
    else:
        print(f"\nVerify FAIL: expected {len(augs)}, got {len(verify)}")
        shutil.copy2(backup_path, AUG_PATH)
        sys.exit(1)

if __name__ == '__main__':
    main()
