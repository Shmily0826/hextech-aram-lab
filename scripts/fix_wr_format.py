"""fix_wr_format.py - Convert decimal win_rate/pick_rate to percentage format."""
import json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
with open(os.path.join(ROOT, 'data', 'augments.json'), 'r', encoding='utf-8') as f:
    augs = json.load(f)

aug_map = {a['id']: a for a in augs}

# Fix 7 entries with decimal format (<=1) → multiply by 100 to get percentage
DECIMAL_ENTRIES = ['upgrade_mikaels', 'jeweled_gauntlet', 'soul_siphon', 
                   'shark_storm', 'zealot', 'flash_2', 'flashbang']

for aid in DECIMAL_ENTRIES:
    a = aug_map.get(aid)
    if not a:
        continue
    
    if a.get('win_rate') is not None and a['win_rate'] <= 1:
        old = a['win_rate']
        a['win_rate'] = round(old * 100, 2)
        print(f'  {aid}: win_rate {old} -> {a["win_rate"]}%')
    
    if a.get('pick_rate') is not None and a['pick_rate'] <= 1:
        old = a['pick_rate']
        a['pick_rate'] = round(old * 100, 2)
        print(f'  {aid}: pick_rate {old} -> {a["pick_rate"]}%')

# Save
with open(os.path.join(ROOT, 'data', 'augments.json'), 'w', encoding='utf-8') as f:
    json.dump(augs, f, ensure_ascii=False, indent=2)

# Verify all win_rates are now in percentage format (>1)
active = [a for a in augs if a.get('status') == 'active' and a.get('win_rate')]
dec_left = [a['id'] for a in active if a['win_rate'] <= 1]
print(f'\nAfter fix: {len(active)} with win_rate, {len(dec_left)} still in decimal format')
if dec_left:
    print(f'  Still decimal: {dec_left}')

# Range check
vals = [a['win_rate'] for a in active]
print(f'  Win rate range: {min(vals):.2f}% - {max(vals):.2f}%')
