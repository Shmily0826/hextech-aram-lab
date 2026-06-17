"""apply_gold_silver_numbers.py - Apply scraped numerical values to gold/silver CN effects."""
import json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
with open(os.path.join(ROOT, 'data', 'augments.json'), 'r', encoding='utf-8') as f:
    augs = json.load(f)

aug_map = {a['id']: a for a in augs}

# === CN effects translated from EN scraped data ===
CN_UPDATES = {
    # GOLD
    'all_for_you': '你对友军的治疗和护盾效果提升30%。',
    
    'tank_engine': '参与击杀敌方英雄时获得1层，可无限叠加。每层提升5%最大生命值和体型。阵亡时损失65%层数。',
    
    'pinball': '你的标记变为弹球，造成100-500额外真实伤害，碰到地形会弹射。每次弹射增加飞行距离和伤害。',
    
    'its_killing_time': '施放终极技能时对所有敌方英雄施加死亡印记(8秒冷却)。印记储存你对其造成伤害的40%，在标记结束后引爆。',
    
    'overflow': '你的技能法力消耗翻倍，但获得10%(+0.5%每100最大法力值)额外伤害以及自我和输出治疗/护盾提升。',
    
    'firebrand': '攻击施加持续5秒的灼烧，每秒造成目标最大生命值0.4%的额外魔法伤害。灼烧可无限叠加，每次施加刷新持续时间。',
    
    'searing_dawn': '获得阳光效果：你的伤害技能会标记敌人，使其受到友军下一次攻击或技能命中时40-200额外魔法伤害(每个目标0.75秒冷却)。',
    
    # SILVER
    'dive_bomber': '阵亡时爆炸，对500范围内的敌人造成相当于目标最大生命值20%的真实伤害。',
    
    'typhoon': '攻击会向一个额外目标发射一枚飞弹，造成30%AD的物理伤害并施加攻击特效。',
    
    'sonic_boom': '为友军提供增益、治疗或护盾时，对450范围内的敌人造成30-150真实伤害并减速30%，持续2秒(2秒冷却)。',
    
    'swift_and_safe': '冲刺或闪烁后获得一个持续2秒的护盾，吸收65-290(+65%AD)(+26%AP)伤害(5秒冷却)。',
    
    'shadow_runner': '冲刺、闪烁或退出隐身状态后，获得300移动速度，持续2秒。',
    
    'kill_secured': '对生命值低于40%最大生命值的敌方英雄，获得60%额外移动速度。',
    
    'mind_to_matter': '获得相当于最大法力值50%的额外生命值。',
    
    'purist_caster': '将所有额外攻击速度按0.65技能急速/1%攻速的比例转化为技能急速。此外，你的技能总冷却时间缩减10%。',
    
    'ocean_soul': '获得海洋龙魂(基础治疗值100)，如果你已有海洋龙魂则获得其他龙魂。',
    
    'flash_2': '替换一个召唤师技能为闪现。此外获得70召唤师技能急速。装备此强化时两个召唤师技能栏都是闪现，且共享冷却时间。',
    
    'spin_me_right_round': '替换一个召唤师技能为骄行荡寇。可激活3次后进入冷却，第3次需在0.5秒后才能使用。',
}

# === EN effects ===
EN_UPDATES = {
    'all_for_you': 'Your heals and shields on allied champions are increased in effectiveness by 30%.',
    'tank_engine': 'Scoring a champion takedown generates a stack, stacking infinitely. For each stack, increase your maximum health and size by 5%. Lose 65% of stacks on death.',
    'pinball': 'Your Mark is empowered to throw a pinball, dealing 100 to 500 bonus true damage and ricocheting off terrain. Each ricochet increases travel distance and damage.',
    'its_killing_time': 'Upon casting your ultimate ability, apply Death Mark to all enemy champions (8 second cooldown). The mark stores 40% of all post-mitigation damage you deal, detonating after the mark ends.',
    'overflow': 'Your abilities\' mana costs are doubled, but you gain 10% (+0.5% per 100 max mana) increased damage, healing, and shielding.',
    'firebrand': 'Basic attacks apply a Burn for 5 seconds dealing bonus magic damage equal to 0.4% of target\'s max health per second. Stacks infinitely, refreshes on reapplication.',
    'searing_dawn': 'Gain Sunlight: Your damaging abilities mark enemies, causing them to take 40 to 200 bonus magic damage from ally\'s next attack or ability (0.75s cooldown per target).',
    'dive_bomber': 'Upon death, explode to deal true damage equal to 20% of target\'s max health to enemies within 500 units.',
    'typhoon': 'Basic attacks fire a bolt at an additional target dealing 30% AD physical damage and applying on-hit effects.',
    'sonic_boom': 'Granting a buff, heal, or shield to an ally deals 30 to 150 true damage to enemies within 450 units and slows by 30% for 2 seconds (2 second cooldown).',
    'swift_and_safe': 'After dashing or blinking, gain a shield lasting 2 seconds that absorbs 65 to 290 (+65% AD) (+26% AP) damage (5 second cooldown).',
    'shadow_runner': 'After dashing, blinking, or exiting stealth, gain 300 bonus movement speed for 2 seconds.',
    'kill_secured': 'Gain 60% bonus movement speed towards enemy champions below 40% of their max health.',
    'mind_to_matter': 'Grants bonus health equal to 50% maximum mana.',
    'purist_caster': 'Convert all bonus attack speed into ability haste at 0.65 haste per 1% AS. Additionally, abilities\' total cooldowns reduced by 10%.',
    'ocean_soul': 'Grants the Ocean Dragon Soul with a modified base heal value of 100, or a different Dragon Soul if you already have it.',
    'flash_2': 'Replace a summoner spell with Flash. Gain 70 summoner spell haste. Both summoner spell slots become Flash and share a cooldown.',
    'spin_me_right_round': 'Replace a summoner spell with Heroic Swing. Can activate 3 times before cooldown; third cast requires 0.5s delay.',
}

cn_updated = 0
en_updated = 0

for slug, effect in CN_UPDATES.items():
    a = aug_map.get(slug)
    if a and a.get('status') == 'active':
        old = a.get('effect', '')
        if old != effect:
            a['effect'] = effect
            cn_updated += 1
            print(f'  CN [{slug}]: {effect[:80]}')

for slug, effect in EN_UPDATES.items():
    a = aug_map.get(slug)
    if a:
        a['effect_en'] = effect
        en_updated += 1

# Save
with open(os.path.join(ROOT, 'data', 'augments.json'), 'w', encoding='utf-8') as f:
    json.dump(augs, f, ensure_ascii=False, indent=2)

# Stats
active = [a for a in augs if a.get('status') == 'active']
for tier in ['prismatic', 'gold', 'silver']:
    tier_augs = [a for a in active if a.get('tier') == tier]
    with_nums = [a for a in tier_augs if any(c.isdigit() for c in a.get('effect', ''))]
    print(f'{tier.capitalize()}: {len(with_nums)}/{len(tier_augs)} with numbers ({100*len(with_nums)//len(tier_augs) if tier_augs else 0}%)')

total_with = sum(1 for a in active if any(c.isdigit() for c in a.get('effect', '')))
print(f'\nAll active with numbers: {total_with}/{len(active)} ({100*total_with//len(active)}%)')
print(f'CN updated: {cn_updated}, EN updated: {en_updated}')

# List remaining without numbers for gold/silver
print(f'\n=== Remaining without numbers ===')
for tier in ['gold', 'silver']:
    tier_augs = [a for a in active if a.get('tier') == tier and not any(c.isdigit() for c in a.get('effect', ''))]
    if tier_augs:
        print(f'\n{tier.upper()} ({len(tier_augs)}):')
        for a in tier_augs:
            print(f'  {a["name"]} ({a["id"]}): {a["effect"][:80]}')
