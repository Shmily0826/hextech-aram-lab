"""
cross_check_v2.py
Correct cross-reference: check our removed augments against actual arammayhem.com active list.
"""
import json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

with open(os.path.join(ROOT, 'data', 'augments.json'), encoding='utf-8') as f:
    augs = json.load(f)

# ACTUAL active list from arammayhem.com fetch (ONLY what was on the page, no additions)
ARAM_ACTIVE_EN_RAW = """Tank Engine, Upgrade Infinity Edge, Quest Steel Your Heart, Heavy Hitter, 
Infinite Recursion, Pressure Cooker, Warlock Juicebox, Phenomenal Evil, Draw Your Sword, Dropkick, 
Void Immolation, Scopier Weapons, Goliath, Magic Missile, Eureka, Combusting Interest, 
Transmute Prismatic, Infernal Conduit, Goredrink, Upgrade Immolate, Spirit Bomb, Ethereal Weapon, 
Blunt Force, Giant Slayer, Deft, Dual Wield, Celestial Body, Pursuit of Haste, Ocean Soul, 
Stackosaurus Rex, Back To Basics, ADAPt, Twin Fire, High Roller, Windspeaker's Blessing, 
Skilled Sniper, Wee Woo Wee Woo, Upgrade Collector, Mystic Punch, Quest Wooglet's Witchcap, 
Shrink Engine, Ice Cold, Shadow Runner, Slap Around, Donation, Witchful Thinking, Growth Spurt, 
Sonata, Forged By The Master, Escape Plan, Mind to Matter, Lil Extra Help, Archmage, 
Stats on Stats, With Haste, Siphon, escAPADe, Outlaws Grit, Mad Scientist, Stay Resolute, 
Marksmage, Tap Dancer, From Downtown, Recursion, Scoped Weapons, Soul Eater, BONK, 
Swift and Safe, Scopiest Weapons, From Beginning To End, Final Form, Upgrade Zhonyas, 
Get Excited, Big Brain, Homeguard, Dawnbringers Resolve, Upgrade Sheen, Light em Up, 
Terraind, Purist Caster, Leg Day, Tooth Fairy, Overflow, DropBear, Spin To Win, Erosion, 
FireFox, King Me, Fan The Hammer, Hand of Baron, Typhoon, Trusty Weapon, Sonic Boom, 
FirstAid Kit, Omni Soul, Overextender, Biggest Snowball Ever, Ravenous Bind, Dont Blink, 
Quest Support Main, All For You, Its Go Time, Bread And Butter, Bread and Cheese, Minionmancer, 
En Passant, Yowch, My Coins, Transmute Chaos, Dashing, Dont Change the Channel, Goldrend, 
Apex Inventor"""

ARAM_ACTIVE_CN_RAW = """坦克引擎, 升级无尽之刃, 任务钢化你心, 重量级打击手, 无限循环往复, 高压锅, 
术士果汁盒, 超凡邪恶, 亮出你的剑, 飞身踢, 任务艾卡西亚的陷落, 更万用的瞄准镜, 歌利亚巨人, 
魔法飞弹, 尤里卡, 炽燃利息, 质变棱彩阶, 炼狱导管, 渴血, 升级献祭, 灵魄炸弹, 虚幻武器, 
大力, 巨人杀手, 灵巧, 双刀流, 星界躯体, 急速之追求, 海洋龙魂, 叠角龙, 回归基本功, 
物理转魔法, 双生火焰, 掷骰狂人, 风语者的祝福, 老练狙神, 喂呜喂呜, 升级收集者, 秘术冲拳, 
任务沃格勒特的巫师帽, 缩小引擎, 冰寒, 暗影疾奔, 扇巴掌, 捐赠, 巫师式思考, 生机迸发, 
咏叹奏鸣, 大师铸就, 逃跑计划, 由心及物, 小小的额外帮助, 大法师, 属性叠属性, 急急小子, 
虹吸, 魔法转物理, 狂徒豪气, 科学狂人, 保持坚定, 神射法师, 踢踏舞, 狙神飞星, 循环往复, 
万用瞄准镜, 吞噬灵魂, 邦, 快中求稳, 最万用的瞄准镜, 有始有终, 最终形态, 升级中娅, 
罪恶快感, 超强大脑, 家园卫士, 黎明使者的坚决, 升级耀光, 点亮他们, 地形专家, 
纯粹主义者术师, 练腿日, 牙仙子, 溢流, 空投熊, 旋转至胜, 侵蚀, 火狐, 尊我为王, 
连拨击锤, 男爵之手, 台风, 可靠武器, 天音爆, 急救用具, 全能龙魂, 过量延伸者, 史上最大雪球, 
贪欲束缚, 唯快不破, 任务专精辅助, 全心为你, 前进时间到, 面包和黄油, 面包和奶酪, 仆从大师, 
吃过路兵, 哎哟我的硬币"""

def normalize(s):
    s = s.lower().strip()
    s = re.sub(r'[^a-z0-9\u4e00-\u9fff]', '', s)
    return s

active_en_set = set(normalize(n) for n in ARAM_ACTIVE_EN_RAW.split(',') if n.strip())
active_cn_set = set(normalize(n) for n in ARAM_ACTIVE_CN_RAW.split(',') if n.strip())

print(f"arammayhem.com 活跃数量: EN={len(active_en_set)}, CN={len(active_cn_set)}")
print()

removed = [a for a in augs if a.get('status') == 'removed']
active_ours = [a for a in augs if a.get('status') == 'active']

# Also count how many of OUR active augments are NOT in arammayhem's active list
our_active_not_on_site = []
for a in active_ours:
    en_norm = normalize(a.get('name_en', ''))
    cn_norm = normalize(a.get('name', ''))
    if en_norm not in active_en_set and cn_norm not in active_cn_set:
        # Try partial match
        found = False
        for site_norm in active_en_set:
            if en_norm and len(en_norm) > 4 and (en_norm in site_norm or site_norm in en_norm):
                found = True
                break
        if not found:
            for site_norm in active_cn_set:
                if cn_norm and len(cn_norm) > 2 and (cn_norm in site_norm or site_norm in cn_norm):
                    found = True
                    break
        if not found:
            our_active_not_on_site.append(a)

print(f"=== 我们的活跃海克斯不在 arammayhem 上: {len(our_active_not_on_site)} 个 ===")
for a in our_active_not_on_site:
    print(f"  {a['name']} ({a.get('name_en','?')}) [{a.get('tier','?')}]")

# Now check removed augments against the ACTUAL active list
print(f"\n=== 我们的已移除海克斯出现在 arammayhem 活跃列表: ===")
found_in_active = []
for a in removed:
    en_norm = normalize(a.get('name_en', ''))
    cn_norm = normalize(a.get('name', ''))
    
    en_match = en_norm in active_en_set
    cn_match = cn_norm in active_cn_set
    
    # Partial match
    partial = False
    match_detail = ''
    if not en_match and not cn_match:
        for site_norm in active_en_set:
            if en_norm and len(en_norm) > 4 and (en_norm in site_norm or site_norm in en_norm):
                partial = True
                match_detail = f'EN partial: {en_norm} ~ {site_norm}'
                break
        if not partial:
            for site_norm in active_cn_set:
                if cn_norm and len(cn_norm) > 2 and (cn_norm in site_norm or site_norm in cn_norm):
                    partial = True
                    match_detail = f'CN partial: {cn_norm} ~ {site_norm}'
                    break
    
    if en_match or cn_match or partial:
        found_in_active.append(a)
        how = 'EN精确' if en_match else ('CN精确' if cn_match else match_detail)
        print(f"  {a['name']} ({a.get('name_en','?')}) [{a.get('tier','?')}] -> {how}")

print(f"\n总计: {len(found_in_active)} 个已移除海克斯可能仍然活跃")

# Also check: how many total active on arammayhem vs our data
print(f"\n=== 数量对比 ===")
print(f"  arammayhem.com 活跃: ~{len(active_en_set)}")
print(f"  我们的 active: {len(active_ours)}")
print(f"  我们的 removed: {len(removed)}")
print(f"  总计: {len(augs)}")
