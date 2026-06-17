"""check_q_and_quality.py - Final quality check on effect descriptions."""
import json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
with open(os.path.join(ROOT, 'data', 'augments.json'), 'r', encoding='utf-8') as f:
    augs = json.load(f)

active = [a for a in augs if a.get('status') == 'active']

# Check for remaining ?
has_q = [a for a in active if '?' in a.get('effect', '')]
print(f'Active augments with ? in effect: {len(has_q)}')

# Check for very short effects (less than 10 chars)
short = [a for a in active if len(a.get('effect', '')) < 10]
print(f'Active augments with very short effect: {len(short)}')

# Check for effects with game-specific numbers (AD, AP, %, etc)
has_numbers = 0
no_numbers = []
for a in active:
    eff = a.get('effect', '')
    if re.search(r'\d', eff):
        has_numbers += 1
    else:
        no_numbers.append(a['id'])

print(f'Effects with numerical values: {has_numbers}/{len(active)} ({100*has_numbers//len(active)}%)')
print(f'Effects without numbers: {len(no_numbers)}')
if no_numbers:
    print(f'  IDs: {", ".join(no_numbers[:20])}')

# Show a few samples of updated effects
print(f'\n=== Sample updated effects with numbers ===')
samples = [
    'courage_of_the_colossus', 'jeweled_gauntlet', 'ok_boomerang',
    'twin_fire', 'scoped_weapons', 'scopiest_weapons', 'juiced',
    'protein_shake', 'witchful_thinking', 'zealot'
]
for sid in samples:
    a = aug_map = {x['id']: x for x in augs}
    if sid in aug_map:
        eff = aug_map[sid].get('effect', '')
        print(f'  {sid}: {eff}')
