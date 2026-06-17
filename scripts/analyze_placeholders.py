"""analyze_placeholders.py - Analyze ? placeholders in effect descriptions."""
import json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
with open(os.path.join(ROOT, 'data', 'augments.json'), 'r', encoding='utf-8') as f:
    augs = json.load(f)

active = [a for a in augs if a.get('status') == 'active']

# Find effects with ? placeholders
has_q = []
for a in active:
    eff = a.get('effect', '')
    if '?' in eff:
        # Count ? occurrences
        count = eff.count('?')
        has_q.append((a['id'], a['name'], a['tier'], count, eff[:120]))

print(f'=== Effects with ? placeholders: {len(has_q)}/{len(active)} ===\n')
for aid, name, tier, cnt, eff in has_q:
    print(f'  [{tier}] {name} ({aid}) - {cnt} placeholder(s)')
    print(f'    {eff}')
    print()

# Also check effect_en for @variable@ patterns
has_vars = []
for a in active:
    eff_en = a.get('effect_en', '')
    # Look for @VarName@ patterns (arammayhem.com variable format)
    vars_found = re.findall(r'@(\w+)@', eff_en)
    if vars_found:
        has_vars.append((a['id'], a['name'], vars_found, eff_en[:120]))

print(f'\n=== EN effects with @variable@ patterns: {len(has_vars)} ===')
for aid, name, vrs, eff in has_vars:
    print(f'  {name} ({aid}): {vrs}')
    print(f'    {eff}')
    print()

# Check for [stat:xxx] patterns in either CN or EN effects
has_stat = []
for a in active:
    for field in ['effect', 'effect_en']:
        txt = a.get(field, '')
        stats = re.findall(r'\[stat:(\w+)\]', txt)
        if stats:
            has_stat.append((a['id'], field, stats, txt[:120]))
            break

print(f'\n=== Effects with [stat:xxx] patterns: {len(has_stat)} ===')
for aid, field, stats, txt in has_stat[:10]:
    print(f'  {aid} ({field}): {stats}')
