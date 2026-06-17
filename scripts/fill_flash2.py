"""fill_flash2.py - Fill the last missing CN effect for flash_2."""
import json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
with open(os.path.join(ROOT, 'data', 'augments.json'), 'r', encoding='utf-8') as f:
    augs = json.load(f)

aug_map = {a['id']: a for a in augs}

# flash_2 EN effect: "Your Mark/Dash gains an additional charge. Mark damage is increased."
if 'flash_2' in aug_map and not aug_map['flash_2'].get('effect'):
    aug_map['flash_2']['effect'] = '你的标记/冲刺获得一层额外充能。标记伤害提高。'
    print('Filled CN effect for flash_2')
else:
    print('flash_2 already has effect or not found')

with open(os.path.join(ROOT, 'data', 'augments.json'), 'w', encoding='utf-8') as f:
    json.dump(augs, f, ensure_ascii=False, indent=2)

# Recheck
active = [a for a in augs if a.get('status') == 'active']
has_eff = sum(1 for a in active if a.get('effect'))
print(f'effect: {has_eff}/{len(active)} ({100*has_eff//len(active)}%)')
