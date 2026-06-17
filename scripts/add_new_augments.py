"""
add_new_augments.py
Safely add new augments from arammayhem.com to augments.json.

Classification logic based on detail page scraping:
- Real effect text → active (genuinely available)
- "已在 26.12 版本上线" (launched, no data) → active (brand new)
- "已在 26.12 版本从正式 ARAM Mayhem 中移除" → removed (historical)
- Player guide text (not real effect) → active but no effect field
"""
import json
import os
import shutil
from datetime import datetime

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, 'data')
OUTPUT_DIR = os.path.join(PROJECT_ROOT, 'pipeline', 'output')

REMOVED_TEXT = "该强化符文已在 26.12 版本从正式 ARAM Mayhem 中移除"
LAUNCHED_TEXT = "该强化符文已在 26.12 版本上线"

# Known player-guide text (not actual effect descriptions)
GUIDE_INDICATORS = [
    "虚空裂隙前期秒脆皮",  # flash_2 strategy text
    "装备出法穿补伤害",
    "打团千万别着急",
]


def is_removed(effect):
    return REMOVED_TEXT in effect if effect else False


def is_launched_no_data(effect):
    return LAUNCHED_TEXT in effect if effect else False


def is_guide_text(effect):
    if not effect:
        return False
    return any(g in effect for g in GUIDE_INDICATORS)


def main():
    # Load source data
    with open(os.path.join(OUTPUT_DIR, 'augment_change_candidates.json'), 'r', encoding='utf-8') as f:
        candidates = json.load(f)
    with open(os.path.join(OUTPUT_DIR, 'arammayhem_details_scrape.json'), 'r', encoding='utf-8') as f:
        details = json.load(f)

    # Build effect lookup by id
    effect_map = {}
    for d in details['results']:
        effect_map[d['id']] = d.get('effect_cn', '')

    # Load current augments
    aug_path = os.path.join(DATA_DIR, 'augments.json')
    with open(aug_path, 'r', encoding='utf-8') as f:
        augments = json.load(f)

    existing_ids = {a['id'] for a in augments}

    # Backup
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = os.path.join(OUTPUT_DIR, f'augments_backup_{ts}.json')
    shutil.copy2(aug_path, backup_path)
    print(f'Backed up: {backup_path}')

    # Classify and build new entries
    to_add = candidates['to_add']
    stats = {'active_with_effect': 0, 'active_no_effect': 0, 'removed_historical': 0,
             'skipped_duplicate': 0, 'skipped_mystery': 0}

    new_entries = []
    for item in to_add:
        aid = item['id']

        # Skip if already exists
        if aid in existing_ids:
            stats['skipped_duplicate'] += 1
            continue

        # Skip mystery/??? augments
        if aid == 'mystery_augment' or item['name'] == '???':
            stats['skipped_mystery'] += 1
            print(f'  SKIP: {aid} (mystery/unnamed)')
            continue

        effect = effect_map.get(aid, '')

        # Determine status
        if is_removed(effect):
            status = 'removed'
            stats['removed_historical'] += 1
            effect_final = ''  # Don't store the "removed" message as effect
            print(f'  REMOVED: {aid} ({item["name"]}) — historical, not in current ARAM Mayhem')
        else:
            status = 'active'
            if is_launched_no_data(effect):
                effect_final = ''  # Newly launched, no effect text available
                stats['active_no_effect'] += 1
                print(f'  NEW (no data yet): {aid} ({item["name"]})')
            elif is_guide_text(effect):
                effect_final = ''  # Guide text, not real effect
                stats['active_no_effect'] += 1
                print(f'  ACTIVE (guide text skipped): {aid} ({item["name"]})')
            elif effect:
                effect_final = effect
                stats['active_with_effect'] += 1
                print(f'  ACTIVE (with effect): {aid} ({item["name"]})')
            else:
                effect_final = ''
                stats['active_no_effect'] += 1
                print(f'  ACTIVE (no effect): {aid} ({item["name"]})')

        # Build entry matching existing augments.json schema
        entry = {
            'id': aid,
            'name': item['name'],
            'name_en': item.get('name_en', ''),
            'tier': item.get('tier', 'unknown'),
            'status': status,
            'effect': effect_final,
            'effect_en': '',
            'source': 'arammayhem_com',
            'aliases': [],
            'patch_added': '26.12',
            'tags': [],
        }

        # Add stats if available
        if 'win_rate' in item:
            entry['win_rate'] = item['win_rate']
        if 'pick_rate' in item:
            entry['pick_rate'] = item['pick_rate']
        if 'site_rank' in item:
            entry['site_rank'] = item['site_rank']

        entry['stats_source'] = 'arammayhem_com'
        entry['stats_updated'] = '2026-06-17'

        new_entries.append(entry)

    # Add to augments list
    augments.extend(new_entries)

    # Validate
    all_ids = [a['id'] for a in augments]
    duplicates = [x for x in all_ids if all_ids.count(x) > 1]
    if duplicates:
        print(f'\nERROR: Duplicate IDs found: {set(duplicates)}')
        print('Rolling back...')
        shutil.copy2(backup_path, aug_path)
        return

    # Write
    with open(aug_path, 'w', encoding='utf-8') as f:
        json.dump(augments, f, ensure_ascii=False, indent=2)

    print(f'\n=== Summary ===')
    print(f'  Total candidates: {len(to_add)}')
    print(f'  Active with effect: {stats["active_with_effect"]}')
    print(f'  Active (no effect yet): {stats["active_no_effect"]}')
    print(f'  Removed (historical): {stats["removed_historical"]}')
    print(f'  Skipped (duplicate): {stats["skipped_duplicate"]}')
    print(f'  Skipped (mystery): {stats["skipped_mystery"]}')
    print(f'  Total added: {len(new_entries)}')
    print(f'  Augments total: {len(existing_ids)} → {len(augments)}')
    print(f'  Saved to: {aug_path}')

    # Count final stats
    active = sum(1 for a in augments if a.get('status') == 'active')
    removed = sum(1 for a in augments if a.get('status') == 'removed')
    with_effect = sum(1 for a in augments if a.get('effect'))
    with_wr = sum(1 for a in augments if a.get('win_rate'))
    print(f'\n  Active: {active}, Removed: {removed}')
    print(f'  With effect: {with_effect}, With win_rate: {with_wr}')


if __name__ == '__main__':
    main()
