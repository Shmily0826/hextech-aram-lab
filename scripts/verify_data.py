"""verify_data.py - Verify data integrity after updates."""
import json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Verify augments.json
with open(os.path.join(ROOT, 'data', 'augments.json'), 'r', encoding='utf-8') as f:
    augs = json.load(f)

ids = [a['id'] for a in augs]
dupes = list(set(x for x in ids if ids.count(x) > 1))
active = [a for a in augs if a.get('status') == 'active']
removed = [a for a in augs if a.get('status') == 'removed']
with_effect = [a for a in augs if a.get('effect')]
with_wr = [a for a in augs if a.get('win_rate')]
new_active = [a for a in active if a.get('patch_added') == '26.12']

print('=== augments.json ===')
print(f'Total: {len(augs)}')
print(f'Active: {len(active)}, Removed: {len(removed)}')
print(f'Duplicates: {dupes if dupes else "none"}')
print(f'With effect: {len(with_effect)}, With win_rate: {len(with_wr)}')
print(f'\nNew (26.12) active augments: {len(new_active)}')
for a in new_active:
    eff = (a.get('effect', '')[:50] + '...') if a.get('effect') else '(no effect yet)'
    wr = a.get('win_rate', '-')
    print(f'  {a["id"]}: {a["name"]} [{a["tier"]}] wr={wr} eff={eff}')

# Verify issues.json
with open(os.path.join(ROOT, 'data/issues.json'), 'r', encoding='utf-8') as f:
    issues = json.load(f)
print(f'\n=== issues.json ===')
print(f'Total: {len(issues)}')
for i in issues:
    print(f'  [{i["sev"]}] {i["title"]} ({i["status"]})')

# Schema validation
valid_tiers = {'silver', 'gold', 'prismatic', 'unknown'}
valid_statuses = {'active', 'removed', 'unknown'}
bad_tiers = [a['id'] for a in augs if a.get('tier') not in valid_tiers]
bad_statuses = [a['id'] for a in augs if a.get('status') not in valid_statuses]
missing_fields = []
required = ['id', 'name', 'tier', 'status']
for a in augs:
    for f in required:
        if f not in a:
            missing_fields.append(f'{a.get("id", "?")}:{f}')

print(f'\n=== Validation ===')
print(f'Invalid tiers: {bad_tiers if bad_tiers else "none"}')
print(f'Invalid statuses: {bad_statuses if bad_statuses else "none"}')
print(f'Missing required fields: {missing_fields if missing_fields else "none"}')
