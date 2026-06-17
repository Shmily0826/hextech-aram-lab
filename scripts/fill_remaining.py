"""fill_remaining.py - Fill remaining gaps with manual tags and known data."""
import json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
with open(os.path.join(ROOT, 'data', 'augments.json'), 'r', encoding='utf-8') as f:
    augs = json.load(f)

# Build lookup
aug_map = {a['id']: a for a in augs}

# === Manual tags for remaining 15 augments ===
MANUAL_TAGS = {
    'omni_soul': ['龙魂', '随机'],
    'echoing_release': ['回响', '施放'],
    'triggered_inferno': ['灼烧', '攻击特效'],
    'high_roller': ['金币', '属性锻造器'],
    'scopiest_weapons': ['攻击距离'],
    'mystic_punch': ['技能急速', '攻击特效'],
    'overload': ['重置', '技能'],
    'ok_boomerang': ['回力镖', '自动施放'],
    'scopier_weapons': ['攻击距离'],
    'shark_bait': ['鲨鱼', '阵亡'],
    'scoped_weapons': ['攻击距离'],
    'stats': ['属性锻造器'],
    'archmage': ['法力', '技能', '冷却'],
    'void_immolation': ['任务', '装备', '日炎'],
    'one_trick_pony': ['强化符文', '选取'],
}

tagged = 0
for aid, tags in MANUAL_TAGS.items():
    if aid in aug_map and not aug_map[aid].get('tags'):
        aug_map[aid]['tags'] = tags
        tagged += 1
print(f'Added manual tags for {tagged} augments')

# === Known CN effects from game wiki/Riot patch notes ===
KNOWN_EFFECTS = {
    'dimension_shift': '获得【当黑暗降临】召唤师技能。创造一个区域，其中的友军获得隐身效果和移动速度。',
    'one_trick_pony': '在选择强化符文时，一栏将始终只包含与你之前选择的强化符文相同稀有度的强化符文。',
    'surge_field': '施放终极技能时，创造一个区域，为其中的友军提供技能急速和移动速度。',
}

filled_eff = 0
for aid, eff in KNOWN_EFFECTS.items():
    if aid in aug_map and not aug_map[aid].get('effect'):
        aug_map[aid]['effect'] = eff
        filled_eff += 1
        print(f'  Filled CN effect: {aid}')
print(f'Filled {filled_eff} CN effects')

# === Known EN effects ===
KNOWN_EN = {
    'flash_2': 'Your Mark/Dash gains an additional charge. Mark damage is increased.',
    'cant_touch_this': 'Casting your ultimate makes you invulnerable for a duration.',
}

filled_en = 0
for aid, en in KNOWN_EN.items():
    if aid in aug_map and not aug_map[aid].get('effect_en'):
        aug_map[aid]['effect_en'] = en
        filled_en += 1
        print(f'  Filled EN effect: {aid}')
print(f'Filled {filled_en} EN effects')

# Save
with open(os.path.join(ROOT, 'data', 'augments.json'), 'w', encoding='utf-8') as f:
    json.dump(augs, f, ensure_ascii=False, indent=2)

# Final stats
active = [a for a in augs if a.get('status') == 'active']
fields = ['effect', 'effect_en', 'win_rate', 'pick_rate', 'tags']
print(f'\n=== Final Stats ({len(active)} active) ===')
for f in fields:
    has = sum(1 for a in active if a.get(f))
    print(f'  {f}: {has}/{len(active)} ({100*has//len(active)}%)')

missing = {f: [a['id'] for a in active if not a.get(f)] for f in fields}
for f, ids in missing.items():
    if ids:
        print(f'\n  Still missing {f} ({len(ids)}): {", ".join(ids[:8])}{"..." if len(ids)>8 else ""}')
