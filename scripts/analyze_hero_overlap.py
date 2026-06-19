"""
analyze_hero_overlap.py
Analyze overlap between champion_recs and synergies in hero modal.
"""
import json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

with open(os.path.join(ROOT, 'data', 'champion_recs.json'), encoding='utf-8') as f:
    cr_data = json.load(f)
cr_map = cr_data.get('data', cr_data)  # augment_id -> list of {h, rarity, grade}

with open(os.path.join(ROOT, 'data', 'synergies.json'), encoding='utf-8') as f:
    syns = json.load(f)

with open(os.path.join(ROOT, 'data', 'augments.json'), encoding='utf-8') as f:
    augs = json.load(f)

# Build augment id -> name map
id2name = {a['id']: a['name'] for a in augs if 'id' in a}

# Build hero -> sets
hero_recs = {}   # hero -> set of augment names (from champion_recs)
hero_trans = {}  # hero -> set of augment names (from synergies transform)
hero_recm = {}   # hero -> set of augment names (from synergies recommend)

# From champion_recs: augment_id -> heroes
for aug_id, recs in cr_map.items():
    aug_name = id2name.get(aug_id, aug_id)
    for r in recs:
        h = r['h']
        hero_recs.setdefault(h, set()).add(aug_name)

# From synergies
for s in syns:
    h, a, t = s['h'], s['a'], s['t']
    if t == 'transform':
        hero_trans.setdefault(h, set()).add(a)
    elif t == 'recommend':
        hero_recm.setdefault(h, set()).add(a)

# Analyze specific heroes
heroes = ['含羞蓓蕾', '亚索', '布兰德']
for hero in heroes:
    recs = hero_recs.get(hero, set())
    trans = hero_trans.get(hero, set())
    recms = hero_recm.get(hero, set())
    
    overlap_rt = recs & trans  # recs that are also transform
    only_recs = recs - trans   # only in recs
    only_trans = trans - recs  # only in transform
    
    print(f'\n=== {hero} ===')
    print(f'  champion_recs: {len(recs)} 个海克斯')
    print(f'  synergies 质变: {len(trans)} 个, 推荐: {len(recms)} 个')
    print(f'  重叠 (recs ∩ transform): {len(overlap_rt)} ({len(overlap_rt)/max(len(recs),1)*100:.0f}% of recs, {len(overlap_rt)/max(len(trans),1)*100:.0f}% of transform)')
    print(f'  仅 recs 有: {len(only_recs)} 个')
    print(f'  仅 transform 有: {len(only_trans)} 个')
    if only_trans:
        print(f'  transform 独有: {", ".join(list(only_trans)[:5])}')

# Global stats
all_heroes = set(list(hero_recs.keys()) + list(hero_trans.keys()))
total_overlap = 0
total_recs = 0
total_trans = 0
for h in all_heroes:
    r = hero_recs.get(h, set())
    t = hero_trans.get(h, set())
    o = r & t
    total_overlap += len(o)
    total_recs += len(r)
    total_trans += len(t)

print(f'\n=== 全局统计 ({len(all_heroes)} 英雄) ===')
print(f'  champion_recs 总计: {total_recs}')
print(f'  synergies transform 总计: {total_trans}')
print(f'  重叠总计: {total_overlap}')
print(f'  recs 中的重叠率: {total_overlap/max(total_recs,1)*100:.1f}%')
print(f'  transform 中的重叠率: {total_overlap/max(total_trans,1)*100:.1f}%')
print(f'  仅 recs: {total_recs - total_overlap}')
print(f'  仅 transform: {total_trans - total_overlap}')
