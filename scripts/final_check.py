"""final_check.py - Check remaining gaps and fix edge cases."""
import json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
with open(os.path.join(ROOT, 'data', 'augments.json'), 'r', encoding='utf-8') as f:
    augs = json.load(f)

active = [a for a in augs if a.get('status') == 'active']

# 1. Check effect quality - flag guide text in CN effects
print('=== Effect quality check ===')
guide_indicators = ['前期秒脆皮', '装备出法穿', '打团千万别', '海克斯可拿']
for a in active:
    eff = a.get('effect', '')
    if any(g in eff for g in guide_indicators):
        print(f'  GUIDE TEXT: {a["id"]}: {eff[:50]}...')
        # Clear it - it's not a real effect
        a['effect'] = ''

# 2. Check effect_en quality
print('\n=== EN effect quality ===')
en_bad = ['Need a dash', 'early bursts squishies', 'Void Rift early']
for a in active:
    en = a.get('effect_en', '')
    if any(b in en for b in en_bad):
        print(f'  BAD EN: {a["id"]}: {en[:60]}...')
        a['effect_en'] = ''

# 3. Generate tags for remaining missing
print('\n=== Remaining missing tags ===')
TAG_KW = {
    '治疗': ['治疗', '回复', 'heal', 'restore'],
    '护盾': ['护盾', 'shield'],
    '攻击速度': ['攻击速度', '攻速', 'attack speed'],
    '技能急速': ['技能急速', 'ability haste', 'haste'],
    '暴击': ['暴击', 'critical', 'crit'],
    '移动速度': ['移动速度', '移速', 'movement speed'],
    '法力': ['法力', 'mana'],
    '生命值': ['生命值', 'health'],
    '法术强度': ['法术强度', 'ability power'],
    '攻击力': ['攻击力', 'attack damage'],
    '护甲': ['护甲', 'armor'],
    '魔抗': ['魔抗', 'magic resist'],
    '灼烧': ['灼烧', 'burn'],
    '减速': ['减速', 'slow'],
    '冲刺': ['冲刺', 'dash', 'leap'],
    '召唤物': ['召唤', 'summon'],
    '雪球': ['雪球', 'snowball', 'mark'],
    '任务': ['任务', 'quest'],
    '终极技能': ['终极技能', 'ultimate'],
    '装备升级': ['升级', 'upgrade'],
    '金币': ['金币', 'gold', 'coin'],
    '体型': ['体型', 'size'],
    '全能吸血': ['全能吸血', 'omnivamp'],
    '穿透': ['穿透', 'penetration'],
    '飞弹': ['飞弹', 'missile', 'projectile'],
    '复活': ['复活', 'revive'],
    '不可阻挡': ['不可阻挡', 'unstoppable'],
    '恐惧': ['恐惧', 'fear'],
    '定身': ['定身', 'root', 'snare'],
    '隐身': ['隐身', 'stealth', 'invisible'],
}

tagged = 0
for a in active:
    if not a.get('tags'):
        text = (a.get('effect', '') + ' ' + (a.get('effect_en', '') or '')).lower()
        tags = []
        for tag, keywords in TAG_KW.items():
            for kw in keywords:
                if kw.lower() in text:
                    tags.append(tag)
                    break
        if tags:
            a['tags'] = tags
            tagged += 1
            print(f'  {a["id"]}: {a["name"]} -> {tags}')
        else:
            print(f'  NO KEYWORDS: {a["id"]}: {a["name"]}')

print(f'Generated tags for {tagged} more augments')

# Save
with open(os.path.join(ROOT, 'data', 'augments.json'), 'w', encoding='utf-8') as f:
    json.dump(augs, f, ensure_ascii=False, indent=2)

# Final stats
active2 = [a for a in augs if a.get('status') == 'active']
fields = ['effect', 'effect_en', 'win_rate', 'pick_rate', 'tags']
print(f'\n=== Final Data Stats ({len(active2)} active) ===')
for f in fields:
    has = sum(1 for a in active2 if a.get(f))
    print(f'  {f}: {has}/{len(active2)} ({100*has//len(active2)}%)')

# List remaining gaps
print('\n=== Remaining gaps ===')
for f in fields:
    missing = [a['id'] for a in active2 if not a.get(f)]
    if missing:
        print(f'  {f} ({len(missing)}): {", ".join(missing[:10])}{"..." if len(missing)>10 else ""}')
