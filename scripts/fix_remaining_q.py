"""fix_remaining_q.py - Replace remaining ? with '若干' and fill known values."""
import json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
with open(os.path.join(ROOT, 'data', 'augments.json'), 'r', encoding='utf-8') as f:
    augs = json.load(f)

aug_map = {a['id']: a for a in augs}

# Known values from game data/wiki for remaining augments
KNOWN_VALUES = {
    'multishot': '任务：用【所选技能】技能命中敌方英雄8次。奖励：发射数量基于任务等级的额外飞弹。',
    'pursuit_of_power': '任务：用【所选技能】技能命中敌人10次。奖励：永久提升【所选技能】技能伤害。',
    'pursuit_of_haste': '任务：用【所选技能】技能命中敌方英雄8次。奖励：【所选技能】技能获得技能急速，基于任务等级，至多至80。',
    'from_downtown': '任务：用技能狙击5个敌方英雄。奖励：一颗流星会飞向被狙击的敌方英雄，在其周围的一个区域内造成魔法伤害。',
    'support_main': '任务：治疗友方英雄2500生命值。奖励：你提供的任何治疗效果现在还会在初始治疗之后提供持续治疗。',
    'poro_stampede': '任务：收集【魄罗佳肴】并投喂5只魄罗。奖励：获得【魄罗冲锋】召唤师技能，可让魄罗们对敌方队伍发动几波攻势。每任务等级都会解锁额外的波次。',
    'lil_extra_help': '在你的【所选技能】技能持续期间获得50攻击距离和30%攻击速度。',
    'warlock_juicebox': '获得15%全能吸血。',
    'nature_heals': '站在草丛中时，每秒回复2%最大生命值。',
    'stay_firm': '当【所选技能】技能对敌方英雄造成伤害时，获得10护甲和魔法抗性。可叠加至5层。',
    'master_crafted': '使你的装备和强化符文伤害提升12%。',
    'adaptive_defense': '用【所选技能】技能打击一个敌方英雄时，为你提供持续6秒的8护甲或魔法抗性，基于该技能的伤害类型。可叠加至5层。',
}

updated = 0
for slug, effect in KNOWN_VALUES.items():
    a = aug_map.get(slug)
    if a and a.get('status') == 'active':
        old = a.get('effect', '')
        if old != effect:
            a['effect'] = effect
            updated += 1
            print(f'  {slug}: {effect[:80]}')

# For any remaining ? in active augments, replace with 若干
remaining_q = 0
for a in augs:
    if a.get('status') != 'active':
        continue
    eff = a.get('effect', '')
    if '?' in eff:
        new_eff = eff.replace('?', '若干')
        a['effect'] = new_eff
        remaining_q += 1
        print(f'  [?→若干] {a["id"]}: {new_eff[:80]}')

# Save
with open(os.path.join(ROOT, 'data', 'augments.json'), 'w', encoding='utf-8') as f:
    json.dump(augs, f, ensure_ascii=False, indent=2)

# Final check
active = [a for a in augs if a.get('status') == 'active']
still_q = [a for a in active if '?' in a.get('effect', '')]
print(f'\nUpdated with known values: {updated}')
print(f'Replaced remaining ?: {remaining_q}')
print(f'Still has ?: {len(still_q)}/{len(active)}')
