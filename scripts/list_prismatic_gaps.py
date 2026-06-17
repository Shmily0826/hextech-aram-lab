"""list_prismatic_gaps.py - List prismatic augments with vague effects needing numbers."""
import json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
with open(os.path.join(ROOT, 'data', 'augments.json'), 'r', encoding='utf-8') as f:
    augs = json.load(f)

active = [a for a in augs if a.get('status') == 'active']
prismatic = [a for a in active if a.get('tier') == 'prismatic']

print(f'=== Prismatic augments: {len(prismatic)} total ===\n')

# Categorize: has numbers vs vague
has_nums = []
vague = []

for a in prismatic:
    eff = a.get('effect', '')
    en = a.get('effect_en', '')
    # Check if effect has any digits
    cn_has_num = bool(re.search(r'\d', eff))
    en_has_num = bool(re.search(r'\d', en))
    
    if cn_has_num:
        has_nums.append(a)
    else:
        vague.append(a)

print(f'With numbers in CN effect: {len(has_nums)}')
print(f'Without numbers in CN effect: {len(vague)}\n')

print('=== PRISMATIC AUGMENTS MISSING NUMERICAL VALUES ===\n')
for a in vague:
    eff = a.get('effect', '')
    en = a.get('effect_en', '')
    print(f'{a["name"]} ({a["id"]})')
    print(f'  CN: {eff}')
    print(f'  EN: {en[:150]}')
    print()

print('\n=== PRISMATIC AUGMENTS WITH NUMBERS ===\n')
for a in has_nums:
    eff = a.get('effect', '')
    print(f'{a["name"]} ({a["id"]})')
    print(f'  CN: {eff}')
    print()
