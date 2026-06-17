"""apply_detailed_effects.py - Apply scraped detailed effect data to augments.json."""
import json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Load scraped data
with open(os.path.join(ROOT, 'pipeline', 'output', 'astro_effects.json'), 'r', encoding='utf-8') as f:
    astro = json.load(f)

# Load augments
with open(os.path.join(ROOT, 'data', 'augments.json'), 'r', encoding='utf-8') as f:
    augs = json.load(f)

aug_map = {a['id']: a for a in augs}

def clean_markup(text):
    """Clean game markup to readable text."""
    if not text:
        return ''
    text = text.replace('[br/]', '\n').replace('[br]', '\n')
    text = re.sub(r"<font[^>]*>", '', text)
    text = text.replace('</font>', '')
    text = re.sub(r'@\w+@', '', text)  # Remove @Variable@ placeholders
    text = re.sub(r'%i:\w+%', '', text)  # Remove %i:xxx% markup
    text = re.sub(r'\[/?\w+\]', '', text)  # Remove remaining [tag] markup
    text = re.sub(r'\n+', ' ', text)  # Collapse newlines to spaces
    text = re.sub(r'\s+', ' ', text).strip()
    return text

# === Manual CN effects with real numbers from scraped CN pages ===
CN_UPDATES = {
    'courage_of_the_colossus': '定身或缚地一个敌方英雄后获得100-300(基于等级)(+5%最大生命值)护盾值。5秒冷却。',
    'empyrean_promise': '获得15%治疗和护盾强度，获得至高天诺言召唤师技能。警惕传送至你的友军并在着陆时提供持续3秒的100-250(基于等级)(+100%AP)(+10%额外生命值)护盾值。',
    'jeweled_gauntlet': '你的技能可以造成暴击，造成145%总伤害。获得25%(+4.5%每100AP)暴击几率。',
    'juiced': '攻击特效消耗2.5%最大法力值，造成相当于3.5%最大法力值的魔法伤害，该伤害可以暴击。',
    'mighty_shield': '当你获得护盾时，获得40-100(基于等级)适应之力，持续3秒。(5秒冷却时间)',
    'ok_boomerang': '每10秒朝着一个附近的敌人自动施放投掷一个回力镖，对命中的敌人们造成40-200(基于等级)(+22%额外AD)(+15%AP)自适应伤害。',
    'protein_shake': '获得25%(+35%每100额外护甲)(+35%每100额外魔抗)治疗和护盾强度。',
    'scoped_weapons': '获得100攻击距离，如果你是远程英雄则降低至50攻击距离。',
    'scopier_weapons': '获得200攻击距离，如果你是远程英雄则降低至100攻击距离。',
    'scopiest_weapons': '获得300攻击距离，如果你是远程英雄则降低至150攻击距离。',
    'twin_fire': '造成技能伤害时，发射1-4个飞弹(基于暴击率)，每个飞弹造成10-30(基于等级)(+7%额外AD)(+7%AP)魔法伤害。此外，获得15%暴击几率。',
    'witchful_thinking': '获得20-80(基于等级)法术强度。',
    'zealot': '获得25%暴击几率(+5%每100AP)和35%攻击速度(+5%每100AP)。',
    'quest_urfs_champion': '任务：参与击杀18次。奖励：完成需求后获得金铲铲。',
    'soul_siphon': '你的暴击会治疗你，治疗量相当于所造成伤害的12%。此外，获得25%暴击几率。',
}

# === Update CN effect for 【?】 -> 【所选技能】 where applicable ===
CHOSEN_SKILL_AUGS = [
    'chain_reaction', 'quickstep', 'terror', 'void_dash',
    'multishot', 'poro_stampede', 'pursuit_of_power', 'pursuit_of_haste',
    'lil_extra_help', 'from_downtown', 'support_main',
    'bread_and_cheese', 'bread_and_jam', 'bread_and_butter',
]

# === EN effects from scraped data ===
EN_UPDATES = {}
for slug, data in astro.items():
    en = data.get('en')
    if en:
        cleaned = clean_markup(en)
        if len(cleaned) > 15:
            EN_UPDATES[slug] = cleaned

cn_updated = 0
en_updated = 0
chosen_skill_updated = 0

# Apply CN number updates
for slug, effect in CN_UPDATES.items():
    a = aug_map.get(slug)
    if a:
        old = a.get('effect', '')
        if old != effect:
            a['effect'] = effect
            cn_updated += 1
            print(f'  CN [{slug}]: {effect[:80]}')

# Apply EN updates
for slug, effect in EN_UPDATES.items():
    a = aug_map.get(slug)
    if a:
        old = a.get('effect_en', '')
        if not old or len(old) < 15 or old != effect:
            a['effect_en'] = effect
            en_updated += 1

# Apply 【?】 -> 【所选技能】 for augments that reference a chosen skill
for slug in CHOSEN_SKILL_AUGS:
    a = aug_map.get(slug)
    if a and a.get('effect'):
        old_eff = a['effect']
        new_eff = old_eff.replace('【?】', '【所选技能】')
        if new_eff != old_eff:
            a['effect'] = new_eff
            chosen_skill_updated += 1
            print(f'  [?→所选技能] {slug}: {new_eff[:80]}')

# Also handle remaining 【?】 in all active augments
for a in augs:
    if a.get('status') != 'active':
        continue
    eff = a.get('effect', '')
    if '【?】' in eff and a['id'] not in CHOSEN_SKILL_AUGS:
        # Check if it's a skill-reference or something else
        new_eff = eff.replace('【?】', '【所选技能】')
        if new_eff != eff and a['id'] not in CN_UPDATES:
            a['effect'] = new_eff
            chosen_skill_updated += 1
            print(f'  [?→所选技能] {a["id"]}: {new_eff[:80]}')

# Save
with open(os.path.join(ROOT, 'data', 'augments.json'), 'w', encoding='utf-8') as f:
    json.dump(augs, f, ensure_ascii=False, indent=2)

# Stats
active = [a for a in augs if a.get('status') == 'active']
still_q = [a for a in active if '?' in a.get('effect', '')]

print(f'\n{"="*60}')
print(f'CN effects updated with numbers: {cn_updated}')
print(f'EN effects updated: {en_updated}')
print(f'【?】→【所选技能】 replaced: {chosen_skill_updated}')
print(f'Still has ? in effect: {len(still_q)}/{len(active)}')
if still_q:
    for a in still_q:
        print(f'  {a["id"]} ({a["name"]}): {a["effect"][:80]}')
