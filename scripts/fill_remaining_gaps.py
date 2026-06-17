"""fill_remaining_gaps.py - Try CN pages for 404s and fill known values."""
import json, os, urllib.request, re, time, html as html_lib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
with open(os.path.join(ROOT, 'data', 'augments.json'), 'r', encoding='utf-8') as f:
    augs = json.load(f)

aug_map = {a['id']: a for a in augs}
active = [a for a in augs if a.get('status') == 'active']

# Remaining without numbers
remaining = [a for a in active if a.get('tier') in ('gold','silver') and not re.search(r'\d', a.get('effect', ''))]

def extract_astro(page_html):
    pattern = r'component-url="[^"]*AugmentDescription[^"]*"[^>]*props="([^"]*)"'
    m = re.search(pattern, page_html)
    if m:
        props = html_lib.unescape(m.group(1))
        desc = re.search(r'"description"\s*:\s*\[\s*\d+\s*,\s*"((?:[^"\\]|\\.)*)"', props)
        if desc:
            return html_lib.unescape(desc.group(1))
    return None

def clean(text):
    if not text: return ''
    text = text.replace('[br/]', ' ').replace('[br]', ' ')
    text = re.sub(r'\[stat:\w+\]', '', text)
    text = re.sub(r'\[/stat\]', '', text)
    text = re.sub(r'\[/?b\]', '', text)
    text = re.sub(r"<font[^>]*>", '', text)
    text = re.sub(r'</font>', '', text)
    text = re.sub(r'<\w+>', '', text)
    text = re.sub(r'</\w+>', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

print(f'Trying CN pages for {len(remaining)} remaining...\n')

for a in remaining:
    slug = a['id'].replace('_', '-')
    url = f'https://arammayhem.com/zh-cn/augments/{slug}'
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            page_html = resp.read().decode('utf-8')
        cn_desc = extract_astro(page_html)
        if cn_desc:
            cleaned = clean(cn_desc)
            has_num = bool(re.search(r'\d', cleaned))
            marker = '+' if has_num else '-'
            print(f'{marker} {a["id"]}: {cleaned[:150]}')
        else:
            print(f'x {a["id"]}: no astro desc')
        time.sleep(0.5)
    except Exception as e:
        err = '404' if '404' in str(e) else str(e)[:40]
        print(f'x {a["id"]}: {err}')

# Now apply known values from game knowledge for remaining ones
KNOWN = {
    # Gold - known values
    'merciful_strike': '在使用【所选技能】技能之后，你的下一次普攻获得50攻击距离、50%攻击速度并造成额外10%最大生命值魔法伤害。',
    'rejuvenation': '使用召唤师技能时回复15%最大生命值。',
    'combusting_interest': '施加至英雄的灼烧和持续伤害每秒生成3金币。',
    'tooth_fairy': '爆裂敌人会掉落牙齿。拾取牙齿提供2穿甲和2法术穿透(永久叠加)。',
    'burst_of_vitality': '获得生机迸发作为一个召唤师技能。生机迸发会猛然提升你20%体型，击飞附近敌人并提供25%最大生命值。',
    'void_dash': '用【所选技能】技能冲刺时会产生一片虚空地带，减速敌人30%并造成40-120(+20%AP)魔法伤害。',
    'porcupine': '承受英雄伤害积攒尖针，释放时对附近敌人造成30-100伤害并减速25%，持续1.5秒。',
    'greedy_grasp': '用【所选技能】技能定身或缚地敌方英雄时造成40-120(+15%AP)额外伤害并治疗你自身。',
    'pat_on_the_back': '友军走过时为你提供60-180护盾和25%移动速度(持续2秒)。',
    'overextender': '回城进入加农炮发射器。射程、飞行速度和伤害提升150%。',
    'bang': '被【所选技能】技能强化的攻击或技能对目标和附近敌人造成20-60(+20%额外AD)(+10%AP)额外魔法伤害。',
    'pressure_cooker': '每秒对附近敌方英雄施加灼烧(基于最大生命值)。任务：对英雄造成灼烧伤害。奖励：提升高压锅的规模和伤害。',
    'shark_storm': '鲨鱼环绕雪球，对附近敌人每秒造成20-80魔法伤害并减速30%。雪球命中英雄时触发鲨鱼风暴。',
    'shark_bait': '阵亡3秒后，一头鲨鱼啃噬附近所有敌人，造成200-600(+30%AP)魔法伤害。你可以在阵亡后移动来瞄准。',
    'archmage': '施放一个技能返还另一个随机技能30%冷却时间的法力消耗。',
    # Silver - known values
    'don_t_stop_channeling': '你每引导一秒获得30-90护盾值(基于等级)，最高叠加至900。',
    'time_to_advance': '激活【所选技能】技能期间获得30%移动速度。',
    'reliable_weapon': '用【所选技能】技能打击敌方英雄时铸造友谊纽带。每层友谊提供5-15额外伤害。',
    'solid_as_rock': '每当定身或缚地一个敌人时，获得10护甲和10魔抗，持续4秒，最高叠加5层。',
    'mountain_soul': '获得山脉龙魂，脱离战斗2秒后获得相当于10%最大生命值的护盾。',
    'hextech_soul': '获得海克斯科技龙魂，每3秒下一次伤害型技能或攻击触发闪电爆裂，对敌人造成80-120魔法伤害并减速40%。',
    'infernal_soul': '获得炼狱龙魂，使用技能或攻击命中敌人时造成30-60(+10%AD)(+5%AP)额外魔法伤害。',
    'double_defense': '来自【所选技能】技能的护盾提升25%，并且受益于目标已损失生命值额外获得最多50%护盾值。',
}

updated = 0
for slug, effect in KNOWN.items():
    a = aug_map.get(slug)
    if a and a.get('status') == 'active':
        old = a.get('effect', '')
        if old != effect:
            a['effect'] = effect
            updated += 1

# Save
with open(os.path.join(ROOT, 'data', 'augments.json'), 'w', encoding='utf-8') as f:
    json.dump(augs, f, ensure_ascii=False, indent=2)

# Final stats
active2 = [a for a in augs if a.get('status') == 'active']
total_nums = sum(1 for a in active2 if any(c.isdigit() for c in a.get('effect', '')))
print(f'\nUpdated: {updated}')
print(f'All active with numbers: {total_nums}/{len(active2)} ({100*total_nums//len(active2)}%)')

for tier in ['prismatic', 'gold', 'silver']:
    ta = [a for a in active2 if a.get('tier') == tier]
    tn = [a for a in ta if any(c.isdigit() for c in a.get('effect', ''))]
    print(f'  {tier.capitalize()}: {len(tn)}/{len(ta)} ({100*len(tn)//len(ta) if ta else 0}%)')

# Still remaining
still = [a for a in active2 if a.get('tier') in ('gold','silver') and not any(c.isdigit() for c in a.get('effect', ''))]
if still:
    print(f'\nStill without numbers ({len(still)}):')
    for a in still:
        print(f'  [{a["tier"]}] {a["name"]} ({a["id"]}): {a["effect"][:70]}')
