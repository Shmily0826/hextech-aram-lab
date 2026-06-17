"""final_validation.py - Complete final validation."""
import json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
with open(os.path.join(ROOT, 'data', 'augments.json'), 'r', encoding='utf-8') as f:
    augs = json.load(f)

active = [a for a in augs if a.get('status') == 'active']
removed = [a for a in augs if a.get('status') == 'removed']

print(f'=== augments.json Final Report ===')
print(f'Total: {len(augs)}')
print(f'Active: {len(active)}, Removed: {len(removed)}')
print()

fields = ['effect', 'effect_en', 'win_rate', 'pick_rate', 'tags']
print('Coverage (active only):')
for f in fields:
    has = sum(1 for a in active if a.get(f))
    pct = 100 * has // len(active)
    missing = [a['id'] for a in active if not a.get(f)]
    status = '✓' if pct >= 95 else '⚠'
    print(f'  {status} {f}: {has}/{len(active)} ({pct}%)')
    if missing and len(missing) <= 20:
        print(f'    Missing: {", ".join(missing)}')

# Check for format issues
print()
print('Format checks:')
bad_wr = [a for a in active if a.get('win_rate') is not None and (a['win_rate'] <= 1 or a['win_rate'] > 100)]
print(f'  Bad win_rate values: {len(bad_wr)}')
bad_pr = [a for a in active if a.get('pick_rate') is not None and (a['pick_rate'] <= 0 or a['pick_rate'] > 100)]
print(f'  Bad pick_rate values: {len(bad_pr)}')

# Check IDs are unique
ids = [a['id'] for a in augs]
dupes = [x for x in ids if ids.count(x) > 1]
print(f'  Duplicate IDs: {len(set(dupes))}')

# Check valid tiers/statuses
valid_tiers = {'silver', 'gold', 'prismatic', 'unknown'}
valid_statuses = {'active', 'removed', 'unknown'}
bad_tier = [a['id'] for a in augs if a.get('tier') not in valid_tiers]
bad_stat = [a['id'] for a in augs if a.get('status') not in valid_statuses]
print(f'  Invalid tiers: {len(bad_tier)}')
print(f'  Invalid statuses: {len(bad_stat)}')

# issues.json
with open(os.path.join(ROOT, 'data', 'issues.json'), 'r', encoding='utf-8') as f:
    issues = json.load(f)
print(f'\n=== issues.json ===')
print(f'Total issues: {len(issues)}')

# champion_recs.json
with open(os.path.join(ROOT, 'data', 'champion_recs.json'), 'r', encoding='utf-8') as f:
    recs = json.load(f)
rec_augs = len(recs.get('data', {}))
print(f'\n=== champion_recs.json ===')
print(f'Augments with recs: {rec_augs}')
