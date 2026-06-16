"""Analyze augments.json: find prototype/fake entries not backed by blitz.gg data."""
import json

# Get all augment IDs that appear in champion_recs (REAL data from blitz.gg)
with open('data/champion_recs.json', 'r', encoding='utf-8') as f:
    cr = json.load(f)
real_ids = set(cr.get('data', {}).keys())

# Get all augment IDs from augments.json
with open('data/augments.json', 'r', encoding='utf-8') as f:
    augs = json.load(f)
all_ids = set(a['id'] for a in augs)
aug_map = {a['id']: a for a in augs}

# Augments in augments.json but NOT in champion_recs
not_in_recs = all_ids - real_ids
# Augments in champion_recs but NOT in augments.json
not_in_augs = real_ids - all_ids

print(f"Total augments in augments.json: {len(all_ids)}")
print(f"Total augments in champion_recs: {len(real_ids)}")
print(f"In augments.json but NOT in champion_recs: {len(not_in_recs)}")
print(f"In champion_recs but NOT in augments.json: {len(not_in_augs)}")

# Check which of these are prototype/manual
print("\n=== Augments NOT in champion_recs (potential fakes) ===")
for aid in sorted(not_in_recs):
    a = aug_map[aid]
    src = a.get('source', {}).get('type', '?')
    name = a.get('name', '?')
    notes = (a.get('notes') or '')[:50]
    has_proto = '原型' in (a.get('notes') or '')
    has_wr = a.get('wr') is not None
    has_best = bool(a.get('best'))
    print(f"  {aid}: {name} | src={src} | proto={has_proto} | has_wr={has_wr} | has_best={has_best}")
    if notes:
        print(f"    notes: {notes}")

if not_in_augs:
    print(f"\n=== In champion_recs but NOT in augments.json ===")
    for aid in sorted(not_in_augs):
        print(f"  {aid}")

# Also check: how many augments have source.type = "manual"?
manual_augs = [a for a in augs if a.get('source', {}).get('type') == 'manual']
print(f"\n=== Augments with source.type='manual': {len(manual_augs)} ===")
for a in manual_augs:
    name = a.get('name', '?')
    aid = a.get('id', '?')
    in_recs = aid in real_ids
    has_proto = '原型' in (a.get('notes') or '')
    print(f"  {aid}: {name} | in_recs={in_recs} | proto={has_proto}")

# Check for fabricated fields on augments (wr, pr, best, avoid, trigger, desc)
print("\n=== Augments with fabricated stats (wr/pr/best/avoid) ===")
fabricated_count = 0
for a in augs:
    has_fabricated = (
        a.get('wr') is not None or
        a.get('pr') is not None or
        bool(a.get('best')) or
        bool(a.get('avoid')) or
        a.get('trigger') is not None
    )
    if has_fabricated:
        fabricated_count += 1
        aid = a.get('id', '?')
        name = a.get('name', '?')
        fields = []
        if a.get('wr') is not None: fields.append(f"wr={a['wr']}")
        if a.get('pr') is not None: fields.append(f"pr={a['pr']}")
        if a.get('best'): fields.append(f"best={len(a['best'])} items")
        if a.get('avoid'): fields.append(f"avoid={len(a['avoid'])} items")
        if a.get('trigger'): fields.append("trigger=...")
        in_recs = aid in real_ids
        print(f"  {aid}: {name} | in_recs={in_recs} | {', '.join(fields)}")
print(f"Total augments with fabricated stats: {fabricated_count}")
