"""apply_prismatic_numbers.py - Update prismatic CN effects with scraped numerical values."""
import json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
with open(os.path.join(ROOT, 'data', 'augments.json'), 'r', encoding='utf-8') as f:
    augs = json.load(f)

aug_map = {a['id']: a for a in augs}

# CN effects with real numbers from EN page scraping
CN_WITH_NUMBERS = {
    'ominous_pact': '你的技能现在需要消耗5%当前生命值才能施放。作为回报，基于已损失生命值获得法术强度(70%损失时最高75-150)、0-50移动速度和最高15%全能吸血。',
    
    'draw_your_sword': '变为近战状态，攻击距离改为200。此外获得30%额外攻击力、25%额外攻击速度、30%额外生命值、25%额外移动速度和20%生命偷取。这些加成基于舍弃的攻击距离进一步提升。',
    
    'empowered_by_the_faithful': '为友军提供治疗或护盾会赐福他们8秒。被赐福的友军对敌方英雄造成伤害时，你获得1层虔诚(最高50层)。满层时释放一道冲击波造成魔法伤害并处决低生命值敌人。',
    
    'stuck_in_here_with_me': '施放终极技能时创造一个500范围的领域持续2秒，期间你获得40%伤害减免。结束后嘲讽领域内的所有敌人。',
    
    'back_to_basics': '你的技能造成35%额外伤害，获得70技能急速，所有来源的治疗和护盾效果提升35%，但你的终极技能被永久封印。',
    
    'goldrend': '对敌方英雄的攻击或技能造成50-150(+40%额外AD)(+20%AP)额外魔法伤害，并获得30金币和25%额外移动速度，持续1.5秒(30秒冷却)。',
    
    'giant_slayer': '体型缩小75%，获得30%额外移动速度。对体型大于你的敌方英雄造成10/15/25/30额外伤害。',
    
    'triggered_inferno': '对不同敌方英雄的攻击或技能获得风格层数，持续6秒可无限叠加。达到S评价时自动使用炼狱扳机。',
    
    'circle_of_death': '你的治疗和生命回复会对1000范围内最近的敌方英雄造成该数值70%的魔法伤害。',
    
    'cruelty': '定身或缚地一个敌方英雄时召唤一颗彗星，1秒后着陆，对附近敌人造成50-150(+40%AP)(+4%最大生命值)魔法伤害。',
    
    'infernal_conduit': '你的技能命中英雄时施加持续5秒的灼烧，每秒造成1.2-12(+2.8%额外AD)(+1.2%AP)魔法伤害(每个施法实例1秒冷却)。灼烧效果可叠加，并且你的灼烧会降低你的基础技能冷却时间。',
    
    'master_of_duality': '攻击特效提供6-18法术强度，造成伤害的技能每次施法提供3-9攻击力，持续5秒可叠加。',
    
    'mad_scientist': '获得此强化和每次重生时，要么变大(获得30%适应之力、20%额外生命值和40%体型增大)，要么变小(获得70技能急速、40%额外移动速度和40%体型缩小)。',
    
    'fey_magic': '用终极技能伤害敌人会将其变形为无害的小动物2秒，期间基础移动速度降低60并被缴械(15秒冷却)。',
    
    'tap_dancer': '对敌方英雄和小兵的攻击特效获得10移动速度，持续5秒可无限叠加。此外，基于你的移动速度获得额外攻击速度。',
    
    'dropkick': '你的攻击和技能处决生命值低于5%(+3%每100AD)(+0.2%每1000最大生命值)的敌方英雄，将其击飞并引发爆炸，同时治疗你自身。',
    
    'cant_touch_this': '施放终极技能使你免疫伤害2秒(8秒冷却)。',
    
    'king_me': '首次进入敌方传送门或弹射器时加冕为王，获得1个随机棱彩阶强化符文，且你的第一件传说级装备升级。',
    
    'void_immolation': '即刻：获得一个斑比的熔渣并且你可以同时购买两件献祭装备。需求：持有日炎圣盾和璀璨回响。奖励：将它们合成为虚空献祭。',
}

# Also update EN effects with the clean scraped text
EN_UPDATES = {
    'ominous_pact': 'Your abilities now have a health cost of 5% current health to cast them. In return, you gain ability power based on your missing health, up to 75 to 150 at 70% missing health, 0 to 50 bonus movement speed, and up to 15% omnivamp.',
    'draw_your_sword': 'Become melee, modifying your attack range to 200 units. Additionally, gain 30% bonus attack damage, 25% bonus attack speed, 30% bonus health, 25% bonus movement speed, and 20% lifesteal. These bonuses scale with the range you give up.',
    'empowered_by_the_faithful': 'Granting a heal or shield to an allied champion blesses them for 8 seconds. Whenever a blessed ally damages an enemy champion, you generate a stack of Devotion, stacking up to 50 times. Upon reaching 50 stacks, unleash a shockwave dealing magic damage and executing low health enemies.',
    'stuck_in_here_with_me': 'Casting your ultimate ability creates an aura with a radius of 500 units around you for 2 seconds, during which you also gain 40% damage reduction. After the duration, you taunt all enemies within the area.',
    'back_to_basics': 'Your champion abilities deal 35% increased damage and you gain 70 ability haste and 35% increased healing and shielding from all sources, but your ultimate ability is permanently sealed.',
    'goldrend': 'Damaging basic attacks or abilities against enemy champions deal 50 to 150 (+40% bonus AD) (+20% AP) bonus magic damage, and grant you 30 gold and 25% bonus movement speed for 1.5 seconds (30 second cooldown).',
    'giant_slayer': 'Become tiny, reducing your size by 75% and gaining 30% bonus movement speed. Additionally, deal 10/15/25/30 bonus damage against enemy champions with greater size than you.',
    'circle_of_death': 'Healing and health regeneration you do causes you to deal 70% of that value in magic damage to the nearest enemy champion within 1000 units.',
    'cruelty': 'Immobilizing or grounding an enemy champion summons a comet above them that lands after 1 second, dealing 50 to 150 (+40% AP) (+4% max health) magic damage to nearby enemies.',
    'infernal_conduit': 'Your ability hits against champions apply a Burn for 5 seconds that deals 1.2 to 12 (+2.8% bonus AD) (+1.2% AP) bonus magic damage per second. Your Burn effects reduce your basic ability cooldowns.',
    'master_of_duality': 'Basic attacks on-hit grant 6 to 18 ability power and damaging abilities grant 3 to 9 bonus attack damage, lasting for 5 seconds, stacking.',
    'mad_scientist': 'Upon acquiring this augment and each time you respawn, gain either 30% adaptive force, 20% bonus health, and 40% increased size or 70 ability haste, 40% bonus movement speed, and 40% reduced size.',
    'fey_magic': 'Damaging enemies with your ultimate ability polymorphs them into harmless critters for 2 seconds, during which their base movement speed is reduced by 60 and disarms them (15 second cooldown).',
    'tap_dancer': 'Basic attacks against champions and minions grant 10 bonus movement speed, lasting 5 seconds, stacking infinitely. Gain bonus attack speed based on your movement speed.',
    'dropkick': 'Your attacks and abilities execute enemy champions below 5% (+3% per 100 AD) (+0.2% per 1000 max health) of their max health, knocking back and causing an explosion while healing you.',
    'cant_touch_this': 'Casting your ultimate grants you invulnerability for 2 seconds (8 second cooldown).',
    'king_me': 'Upon entering the enemy gate or Catapult for the first time, you become Kinged, gaining one random Prismatic augment and upgrading your first legendary item.',
}

cn_updated = 0
en_updated = 0

for slug, effect in CN_WITH_NUMBERS.items():
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
prismatic = [a for a in active if a.get('tier') == 'prismatic']
prism_with_nums = [a for a in prismatic if any(c.isdigit() for c in a.get('effect', ''))]
prism_without = [a for a in prismatic if not any(c.isdigit() for c in a.get('effect', ''))]

print(f'\n{"="*60}')
print(f'CN effects updated: {cn_updated}')
print(f'EN effects updated: {en_updated}')
print(f'\nPrismatic with numbers: {len(prism_with_nums)}/{len(prismatic)}')
print(f'Prismatic still without numbers: {len(prism_without)}')
if prism_without:
    print(f'\nStill missing numbers:')
    for a in prism_without:
        print(f'  {a["name"]} ({a["id"]}): {a["effect"][:80]}')
