#!/usr/bin/env python3
"""解析英文版 blitz.gg 数据，更新候选的 effect_en 字段。"""
import json, sys, os, io, re, shutil

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CANDIDATES_PATH = os.path.join(PROJECT, "pipeline", "output", "augment_import_candidates.json")
FILE_TIER = r"C:\Users\Shmily\OneDrive\Desktop\Temp\3.txt"
FILE_UPDATE = r"C:\Users\Shmily\OneDrive\Desktop\Temp\4.txt"

def parse_augments(filepath):
    """解析 blitz.gg 页面文本，提取 augment name → description 映射。"""
    with open(filepath, "r", encoding="utf-8") as f:
        lines = [l.rstrip() for l in f.readlines()]
    
    results = {}
    
    # 找有效区域的起始和结束行
    start_idx = None
    end_idx = len(lines)
    for i, line in enumerate(lines):
        if any(m in line for m in ["Prismatic ARAM Mayhem", "Silver ARAM Mayhem", 
                                     "Gold ARAM Mayhem", "New ARAM Mayhem",
                                     "Removed ARAM Mayhem"]):
            if start_idx is None:
                start_idx = i
        if line.strip() == "Company":
            end_idx = i
            break
    
    if start_idx is None:
        return results
    
    # 跳过标题/导航行
    skip_patterns = [
        "League of Legends", "Teamfight", "VALORANT", "Counter-Strike",
        "Fortnite", "Escape From", "Apex Legends", "Marvel Rivals", "Deadlock",
        "搜索", "Search", "Ctrl", "首页", "Home", "英雄", "Champions",
        "强度榜", "Tier List", "ARAM Mayhem", "ARAM", "斗魂竞技场", "Arena",
        "新闻", "News", "攻略", "Guides", "悬浮窗", "Overlays",
        "Tierlist of", "League of Legends ARAM", "Download",
        "Augments Tier List", "List of new", "List of removed",
        "LoL Aram Mayhem", "Ctrl", "K", "NEW", "新",
    ]
    
    # 提取 name-description 对
    i = start_idx
    while i < end_idx:
        line = lines[i].strip()
        
        # 跳过空行和噪音
        if not line or any(line.startswith(p) or line == p for p in skip_patterns):
            i += 1
            continue
        
        # 跳过标记
        if line in ("New", "Removed", "新", "已移除"):
            i += 1
            continue
        
        # 检测是否是 augment 名称
        # 名称特征：较短，不以常见描述开头
        desc_starts = [
            "Gain ", "Your ", "After ", "On ", "When ", "Casting ", "Using ",
            "Healing", "Buffing", "Periodically", "Every ", "Replace", "Standing",
            "While ", "For ", "Based ", "In ", "Convert", "Increase", "Reduce",
            "Attacks ", "Damaging", "Takedowns", "Immobiliz", "Upgrad", "Autocast",
            "Recasting", "Shortly", "Burst", "Recall", "Basic ", "Striking",
            "Shields", "Activat", "You ", "The ", "Snowball", "Poltergeist",
            "Execute", "Press ", "Cupcake", "Red env", "Head", "There is",
            "Hitting", "Nearby", "Scoring", "Drop", "A few", "Shark", "Sharks",
            "Become", "Quest", "QUEST", "REWARD", "Immediately", "Vigilance",
            "Dashing", "Dealing", "Scoring", "Heal ", "Takedown", "Gain",
            "Reduce", "Your", "Every", "Standing", "Your", "Occasionally",
            "Recall", "Activating", "Periodically", "Replace", "Attacks",
            "After", "Shields", "Gain", "You", "Your", "On", "When",
            "Basic", "Healing", "Buffing", "Using", "Casting", "Immobiliz",
            "Takedowns", "Upgrad", "Autocast", "Recasting", "Shortly",
            "Burst", "Striking", "The", "Snowball", "Press", "Cupcakes",
            "There", "Hitting", "Nearby", "Scoring", "Drop", "A few",
            "Shark", "Sharks", "Become", "Damaging",
        ]
        
        is_name = (
            len(line) < 50 and
            not any(line.startswith(p) for p in desc_starts) and
            not line[0].isdigit() and
            line not in ("???", "？")
        )
        
        if is_name:
            name = line
            desc_lines = []
            i += 1
            # 收集描述行
            while i < end_idx:
                dl = lines[i].strip()
                if not dl:
                    i += 1
                    break
                if dl in ("New", "Removed", "新", "已移除"):
                    i += 1
                    break
                if any(dl.startswith(p) or dl == p for p in skip_patterns):
                    break
                # 检查是否是下一个名称
                if (len(dl) < 50 and 
                    not any(dl.startswith(p) for p in desc_starts) and
                    not dl[0].isdigit() and
                    dl not in ("???", "？")):
                    break
                desc_lines.append(dl)
                i += 1
            
            if desc_lines:
                desc = " ".join(desc_lines).strip()
                if len(desc) > 3:
                    results[name.lower()] = {"name": name, "effect_en": desc}
        else:
            i += 1
    
    return results

# 解析两个英文文件
print("解析英文 tier list (3.txt)...")
tier_data = parse_augments(FILE_TIER)
print(f"  提取了 {len(tier_data)} 个英文增强")

print("解析英文 update page (4.txt)...")
update_data = parse_augments(FILE_UPDATE)
print(f"  提取了 {len(update_data)} 个英文增强")

# 合并 (tier list 优先，描述更完整)
all_english = {}
all_english.update(update_data)
all_english.update(tier_data)
print(f"  合并后共 {len(all_english)} 个唯一英文增强")

# ===== 中文名→英文名映射 =====
ZH_TO_EN = {
    "吃过路兵": "en passant", "三重射击": "tripleshot",
    "邦！": "bonk!", "喂呜喂呜": "wee woo wee woo",
    "哎哟，我的硬币！": "yowch, my coins!",
    "藏身草丛": "hide on bush", "轻拍背部": "pat on the back",
    "地形专家": "terrain'd", "惊惧": "terror",
    "无尽大杀四方": "endless decimation", "牙仙子": "tooth fairy",
    "自然即是治愈": "nature is healing", "过量延伸者": "overextender",
    "鲨鱼暴风": "shark tempest", "鲨鱼诱饵": "shark bait",
    "下雪天": "snowday", "主玩辅助": "support main",
    "保持坚定": "stay resolute", "别停止引导": "don't change the channel",
    "前进时间到": "it's go time", "加固护盾": "bolstered",
    "双重打击": "double strike", "可靠武器": "trusty weapon",
    "大师铸就": "forged by the master", "自适应防护": "adaptive ward",
    "装填": "reload", "豪猪": "porcupine",
    "贪欲束缚": "ravenous bind", "仁慈打击": "mercy's strike",
    "复位": "snap back", "冰雪爆裂": "snowblast",
    "叠角龙": "stackosaurus rex", "艾卡西亚的陷落": "icathia's fall",
    "超负荷": "overloaded", "大招工具人": "ult bot",
    "升级：花晓之剑": "upgrade sword of blossoming dawn",
    "闪现向前": "flashy", "会心治疗": "critical healing",
    "关键暴击": "it's critical", "暴击律动": "critical rhythm",
    "双发快射": "double tap", "暴击飞弹": "critical missile",
    "最终都市列车": "final city transit", "吸血习性": "vampirism",
    "坚韧": "perseverance", "易损": "vulnerability",
    "升级：雪球": "snowball upgrade",
    "会心防御": "tank it or leave it", "狂热者": "zealot",
    "由暴生急": "crit 'n cast", "坚若磐石": "adamant",
    "唯快不破": "don't blink", "质变：黄金阶": "transmute: gold",
    "火狐": "firefox", "急救用具": "first-aid kit",
    "燃烧利息": "combusting interest", "全心为你": "all for you",
    "回力OK镖": "ok boomerang", "有始有终": "from beginning to end",
    "活力焕发": "rejuvenation", "火上浇油": "firebrand",
    "狂徒豪气": "outlaw's grit", "神圣干预": "divine intervention",
    "心灵净化": "spiritual purification", "尖端发明家": "apex inventor",
    "弹球": "pinball", "炽烈黎明": "searing dawn",
    "缩小射线": "shrink ray", "仆从大师": "minionmancer",
    "不动如山": "impassable", "超强大脑": "big brain",
    "星界躯体": "celestial body", "罪恶快感": "get excited!",
    "面包和黄油": "bread and butter", "大法师": "archmage",
    "威能之追求": "pursuit of power", "小小的额外帮助": "lil' extra help",
    "急速之追求": "pursuit of haste", "狙神飞星": "from downtown",
    "术士果汁盒": "warlock juicebox", "高压锅": "pressure cooker",
    "虚空冲刺": "void dash", "物理转魔法": "adapt",
    "魔法转物理": "escapade", "侵蚀": "erosion",
    "防护面纱": "veil of warding", "吵闹鬼": "poltergeist",
    "转得我眩晕了": "spin me right round", "闪光弹": "flashbang",
    "闪闪现现": "flash 2", "强力护盾": "mighty shield",
    "山脉龙魂": "mountain soul", "俯冲轰炸": "dive bomber",
    "天音爆": "sonic boom", "属性！": "stats!",
    "旋转至胜": "spin to win", "杀意翻涌": "kill secured",
    "注魔": "juiced", "大力": "blunt force",
    "灵巧": "deft", "渴血": "goredrink",
    "家园卫士": "homeguard", "终极不可阻挡": "ultimate unstoppable",
    "逃跑计划": "escape plan", "快中求稳": "swift and safe",
    "海克斯科技龙魂": "hextech soul", "点亮他们！": "light 'em up!",
    "炼狱龙魂": "infernal soul", "纯粹主义者 - 术师": "purist - caster",
    "练腿日": "leg day", "升级：献祭": "upgrade immolate",
    "升级：中娅": "upgrade zhonya's", "升级：收集者": "upgrade collector",
    "暗影疾奔": "shadow runner", "海洋龙魂": "ocean soul",
    "由心及物": "mind to matter", "冰寒": "ice cold",
    "台风": "typhoon", "万用瞄准镜": "scoped weapons",
    "重量级打击手": "heavy hitter", "巫师式思考": "witchful thinking",
    "扇巴掌": "slap around", "双生火焰": "twin fire",
    "扳机炼狱": "triggered inferno", "你肩上的恶魔": "devil on your shoulder",
    "卡皮巴拉空投": "droppybara", "小丑学院": "clown college",
    "王中王，靴中靴": "sneakerhead", "珠光护手": "jeweled gauntlet",
    "软弹啪叽抓": "squishy slappy grab", "量子计算": "quantum computing",
    "魄罗蛮冲": "poro stampede", "大地苏醒": "earthwake",
    "利刃华尔兹": "blade waltz", "濒死悟道": "hellbent",
    "电涌力场": "surge field", "空投熊": "dropbear",
    "飞升仪式": "rite of ascension", "连锁反应": "chain reaction",
    "泰坦的坚决": "titan's resolve", "潘朵拉的盒子": "pandora's box",
    "灵魄炸弹": "spirit bomb", "针插垫": "pin cushion",
    "快步": "quickstep", "掷骰狂人": "high roller",
    "多重射击": "multishot", "咒语裂变": "spell split",
    "回响施放": "echo cast", "位面转移": "dimension shift",
    "尤里卡": "eureka", "巨人杀手": "giant slayer",
    "歌利亚巨人": "goliath", "炼狱导管": "infernal conduit",
    "飞身踢": "dropkick", "双刀流": "dual wield",
    "无限循环往复": "infinite recursion",
    "最万用的瞄准镜": "scopiest weapons", "最终形态": "final form",
    "终极刷新": "ultimate revolution",
    "沃格勒特的巫师帽": "wooglet's witchcap",
    "踢踏舞": "tap dancer", "亮出你的剑": "draw your sword",
    "全凭身法": "dashing", "史上最大雪球": "biggest snowball ever",
    "回归基本功": "back to basics", "巨像的勇气": "courage of the colossus",
    "秘术冲拳": "mystic punch", "精怪魔法": "fey magic",
    "终极唤醒": "ultimate awakening", "质变：混沌": "transmute: chaos",
    "连拨击锤": "fan the hammer", "不祥契约": "ominous pact",
    "你摸不到": "can't touch this",
    "信念者的强化": "empowered by the faithful",
    "全能龙魂": "omni soul", "和我一起困在这里": "stuck in here with me",
    "属性叠属性叠属性！": "stats on stats on stats!",
    "战争交响乐": "symphony of war", "残忍": "cruelty",
    "海牛阿福的勇士": "urf's champion", "科学狂人": "mad scientist",
    "风语者的祝福": "windspeaker's blessing", "尊我为王": "king me",
    "死亡之环": "circle of death", "物法皆修": "master of duality",
    "玻璃大炮": "glass cannon", "男爵之手": "hand of baron",
    "神圣雪球": "holy snowball", "至高天诺言": "empyrean promise",
    "舞会女王": "prom queen", "蛋白粉奶昔": "protein shake",
    "升级：无尽之刃": "upgrade infinity edge",
    "吞噬灵魂": "soul eater", "坦克引擎": "tank engine",
    "循环往复": "recursion", "更万用的瞄准镜": "scopier weapons",
    "杀戮时间到了": "it's killing time",
    "穿针引线": "thread the needle", "缩小引擎": "shrink engine",
    "老练狙神": "skilled sniper", "虚幻武器": "ethereal weapon",
    "质变：棱彩阶": "transmute: prismatic",
    "超凡邪恶": "phenomenal evil", "任务：钢化你心": "steel your heart",
    "魔法飞弹": "magic missile", "咏叹奏鸣": "sonata",
    "夜狩": "nightstalking", "属性叠属性！": "stats on stats!",
    "急急小子": "with haste", "捐赠": "donation",
    "溢流": "overflow", "生机迸发": "growth spurt",
    "神射法师": "marksmage", "面包和奶酪": "bread and cheese",
    "面包和果酱": "bread and jam",
    "黎明使者的坚决": "dawnbringer's resolve",
    "虹吸": "soul siphon",
}

# ===== 读取候选 =====
print("\n读取候选文件...")
with open(CANDIDATES_PATH, "r", encoding="utf-8") as f:
    candidates = json.load(f)

# 备份
backup_path = CANDIDATES_PATH + ".en_backup"
shutil.copy2(CANDIDATES_PATH, backup_path)
print(f"  备份到 {backup_path}")

updated = 0
added_names = []
still_empty = []

for c in candidates:
    name_zh = c.get("name", "")
    name_en = c.get("name_en", "")
    cid = c.get("id", "")
    
    matched_effect = None
    
    # 1. 通过中文名映射找到英文名
    if name_zh in ZH_TO_EN:
        en_key = ZH_TO_EN[name_zh].lower()
        if en_key in all_english:
            matched_effect = all_english[en_key]["effect_en"]
    
    # 2. 直接用 name_en 匹配
    if not matched_effect and name_en:
        en_key = name_en.lower().strip()
        if en_key in all_english:
            matched_effect = all_english[en_key]["effect_en"]
    
    # 3. 用 ID 匹配
    if not matched_effect:
        id_as_name = cid.replace("_", " ").lower()
        if id_as_name in all_english:
            matched_effect = all_english[id_as_name]["effect_en"]
    
    # 4. 遍历所有英文数据，用 name_en 匹配
    if not matched_effect and name_en:
        for en_key, data in all_english.items():
            if data["name"].lower() == name_en.lower():
                matched_effect = data["effect_en"]
                break
    
    if matched_effect:
        old = c.get("effect_en", "")
        if old != matched_effect:
            c["effect_en"] = matched_effect
            updated += 1
            if not old:
                added_names.append(f"  {name_zh} ({name_en or cid})")
    elif not c.get("effect_en", ""):
        still_empty.append(f"  {name_zh} ({name_en or cid})")

# 写回
with open(CANDIDATES_PATH, "w", encoding="utf-8") as f:
    json.dump(candidates, f, ensure_ascii=False, indent=2)

print(f"\n===== 结果 =====")
print(f"更新了 {updated} 个候选的英文效果描述")
print(f"仍有 {len(still_empty)} 个缺少英文描述:")
for s in still_empty:
    print(s)
print(f"\n新增英文描述的候选 ({len(added_names)}):")
for a in added_names[:20]:
    print(a)
if len(added_names) > 20:
    print(f"  ... 共 {len(added_names)} 个")

with_en = sum(1 for c in candidates if c.get("effect_en", ""))
with_zh = sum(1 for c in candidates if c.get("effect", ""))
print(f"\n总计: {len(candidates)} 个候选")
print(f"  有中文描述: {with_zh}")
print(f"  有英文描述: {with_en}")
