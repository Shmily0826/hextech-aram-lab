"""
cleanup_removed_augments.py
Handle 7 augments removed from arammayhem.com (patch 16.12):
  1. Remove their entries from champion_recs.json
  2. Remove their synergy entries from synergies.json
  3. Mark them as status="removed" in augments.json
Backs up all files before modifying.
"""
import json
import os
import shutil
from datetime import datetime

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, 'data')
OUTPUT_DIR = os.path.join(PROJECT_ROOT, 'pipeline', 'output')

REMOVED_IDS = [
    'bolstered',           # 加固护盾
    'can_t_touch_this',    # 碰不到我
    'earthwake',           # 大地苏醒
    'flash_forward',       # 闪现向前
    'icathian_fall',       # 艾卡西亚的陷落
    'transmute_gold',      # 质变：黄金阶
    'veil_of_protection',  # 防护面纱
]


def backup(filepath):
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    name = os.path.basename(filepath).replace('.json', '')
    dest = os.path.join(OUTPUT_DIR, f'{name}_backup_{ts}.json')
    shutil.copy2(filepath, dest)
    print(f'  Backed up: {dest}')
    return dest


def clean_champion_recs():
    path = os.path.join(DATA_DIR, 'champion_recs.json')
    backup(path)
    with open(path, 'r', encoding='utf-8') as f:
        cr = json.load(f)
    data = cr.get('data', {})
    removed_count = 0
    for rid in REMOVED_IDS:
        if rid in data:
            n = len(data[rid])
            del data[rid]
            removed_count += 1
            print(f'  champion_recs: removed {rid} ({n} hero recs)')
    cr['data'] = data
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(cr, f, ensure_ascii=False, indent=2)
    print(f'  champion_recs: {removed_count} augment entries removed')
    return removed_count


def clean_synergies():
    path = os.path.join(DATA_DIR, 'synergies.json')
    backup(path)
    with open(path, 'r', encoding='utf-8') as f:
        syns = json.load(f)
    # Get removed augment names
    aug_path = os.path.join(DATA_DIR, 'augments.json')
    with open(aug_path, 'r', encoding='utf-8') as f:
        augs = json.load(f)
    removed_names = set()
    for a in augs:
        if a['id'] in REMOVED_IDS:
            removed_names.add(a['name'])
    original = len(syns)
    cleaned = [s for s in syns if s.get('aug') not in removed_names]
    removed = original - len(cleaned)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(cleaned, f, ensure_ascii=False, indent=2)
    print(f'  synergies: {original} -> {len(cleaned)} (removed {removed} entries)')
    return removed


def mark_augments_removed():
    path = os.path.join(DATA_DIR, 'augments.json')
    backup(path)
    with open(path, 'r', encoding='utf-8') as f:
        augs = json.load(f)
    marked = 0
    for a in augs:
        if a['id'] in REMOVED_IDS:
            a['status'] = 'removed'
            a['removed_reason'] = '不在 arammayhem.com 26.12 版本列表中'
            marked += 1
            print(f'  augments: marked {a["id"]} ({a["name"]}) as removed')
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(augs, f, ensure_ascii=False, indent=2)
    print(f'  augments: {marked} marked as removed')
    return marked


def main():
    print('=== Cleaning Removed Augment References ===\n')

    print('--- Step 1: Clean champion_recs.json ---')
    cr_count = clean_champion_recs()

    print('\n--- Step 2: Clean synergies.json ---')
    syn_count = clean_synergies()

    print('\n--- Step 3: Mark augments as removed ---')
    aug_count = mark_augments_removed()

    print(f'\n=== Summary ===')
    print(f'  champion_recs: {cr_count} augment entries removed')
    print(f'  synergies: {syn_count} entries removed')
    print(f'  augments: {aug_count} marked status=removed')


if __name__ == '__main__':
    main()
