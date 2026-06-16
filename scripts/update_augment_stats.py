"""
update_augment_stats.py
Only update win_rate and pick_rate for EXISTING augments in augments.json.
Does NOT add new, remove old, or change names/tiers.
Backs up original before writing.
"""
import json
import os
import shutil
from datetime import datetime

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, 'data')
OUTPUT_DIR = os.path.join(PROJECT_ROOT, 'pipeline', 'output')


def main():
    # Load candidates
    with open(os.path.join(OUTPUT_DIR, 'augment_change_candidates.json'), 'r', encoding='utf-8') as f:
        candidates = json.load(f)

    # Load local augments
    aug_path = os.path.join(DATA_DIR, 'augments.json')
    with open(aug_path, 'r', encoding='utf-8') as f:
        augs = json.load(f)

    # Backup
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = os.path.join(OUTPUT_DIR, f'augments_backup_{ts}.json')
    shutil.copy2(aug_path, backup_path)
    print(f'Backed up: {backup_path}')

    # Build update map: id -> {win_rate, pick_rate, site_rank}
    update_map = {}
    for entry in candidates['to_update']:
        aid = entry['id']
        updates = entry['updates']
        stats = {}
        if 'win_rate' in updates:
            stats['win_rate'] = updates['win_rate']
        if 'pick_rate' in updates:
            stats['pick_rate'] = updates['pick_rate']
        if 'site_rank' in updates:
            stats['site_rank'] = updates['site_rank']
        if stats:
            update_map[aid] = stats

    print(f'Updates to apply: {len(update_map)}')

    # Apply updates
    updated_count = 0
    for a in augs:
        aid = a['id']
        if aid in update_map:
            stats = update_map[aid]
            a['win_rate'] = stats.get('win_rate', a.get('win_rate'))
            a['pick_rate'] = stats.get('pick_rate', a.get('pick_rate'))
            a['site_rank'] = stats.get('site_rank', a.get('site_rank'))
            a['stats_source'] = 'arammayhem_com'
            a['stats_updated'] = datetime.now().strftime('%Y-%m-%d')
            updated_count += 1

    # Save
    with open(aug_path, 'w', encoding='utf-8') as f:
        json.dump(augs, f, ensure_ascii=False, indent=2)

    print(f'Updated {updated_count} augments with win_rate/pick_rate')
    print(f'Saved: {aug_path}')

    # Verify
    with open(aug_path, 'r', encoding='utf-8') as f:
        verify = json.load(f)
    has_wr = sum(1 for a in verify if a.get('win_rate') is not None)
    has_pr = sum(1 for a in verify if a.get('pick_rate') is not None)
    print(f'\nVerification: {len(verify)} total, {has_wr} with win_rate, {has_pr} with pick_rate')


if __name__ == '__main__':
    main()
