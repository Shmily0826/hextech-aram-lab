"""Translate item names in champion build strings from English to Chinese.
Uses official League of Legends Chinese translations.
"""
import json, re, shutil

SRC = "data/champions.json"
BAK = "data/champions.backup_before_i18n.json"

# Official Chinese item name mapping (patch 26.12)
# Sorted longest-first to avoid partial replacement issues
ITEM_MAP = {
    # Mythic/Legendary items
    "Rabadon's Deathcap": "灭世者的死亡之帽",
    "Liandry's Torment": "兰德里的折磨",
    "Rylai's Crystal Scepter": "瑞莱的冰晶节杖",
    "Guinsoo's Rageblade": "鬼索的狂暴之刃",
    "Shurelya's Battlesong": "舒瑞莉亚的战歌",
    "Imperial Mandate": "帝国指令",
    "Blade of the Ruined King": "破败王者之刃",
    "Lord Dominik's Regards": "多米尼克领主的致意",
    "Trinity Force": "三相之力",
    "Infinity Edge": "无尽之刃",
    "The Ruined King": "破败王者之刃",
    "Spirit Visage": "振奋盔甲",
    "Warmog's Armor": "狂徒铠甲",
    "Ardent Censer": "炽热香炉",
    "Death's Dance": "死亡之舞",
    "Winter's Approach": "凛冬之临",
    "Hextech Rocketbelt": "海克斯科技火箭腰带",
    "Hextech Gunblade": "海克斯科技枪刃",
    "Zhonya's Hourglass": "中娅沙漏",
    "Titanic Hydra": "巨型九头蛇",
    "Ravenous Hydra": "贪欲九头蛇",
    "Kraken Slayer": "海妖杀手",
    "Phantom Dancer": "幻影之舞",
    "Moonstone Renewer": "月石再生",
    "Essence Reaver": "吸蓝刀",
    "Rapid Firecannon": "急速火炮",
    "Void Staff": "虚空之杖",
    "Nashor's Tooth": "纳什之牙",
    "Runaan's Hurricane": "卢安娜的飓风",
    "The Collector": "收集者",
    "Eclipse": "蚀",
    "Heartsteel": "心之钢",
    "Terminus": "终点站",
    "Lich Bane": "巫妖之祸",
    "Luden's Echo": "卢登的回声",
    "Thornmail": "荆棘之甲",
    "Overlord's Bloodmail": "霸主血铠",
    "Unending Despair": "无尽绝望",
    "Iceborn Gauntlet": "冰脉护手",
    "Blackfire Torch": "黑火火炬",
    "Sundered Sky": "碎裂王冠",
    "Fimbulwinter": "永冬",
    "Experimental Hexplate": "实验性海克斯板甲",
    "Cosmic Drive": "宇宙驱驰",
    "Statikk Shiv": "斯塔缇克电刃",
    "Yun Tal Wildarrows": "云·塔尔野性之箭",
    "Navori Flickerblade": "纳沃利闪烁之刃",
    "Mikael's Blessing": "米凯尔的祝福",
    "Malignance": "恶咒",
    "Shadowflame": "暗影焰",
    "Stormsurge": "风暴涌动",
    "Archangel's Staff": "大天使之杖",
    "Serylda's Grudge": "赛瑞尔达的怨恨",
    "Voltaic Cyclosword": "电涡之剑",
    "Hextech Alternator": "海克斯科技发电机",
    "Stridebreaker": "挺进破坏者",
    "Wit's End": "智慧末刃",
    "Hubris": "傲慢",
    "Axiom Arc": "公理圆弧",
    "Manamune": "魔宗",
    "Redemption": "救赎",
    "Actualizer": "实现者",
    "Endless Hunger": "无尽饥渴",
    "Whispering Circlet": "低语之环",
    "Bandlepipes": "班德尔笛",
    # Boots
    "Sorcerer's Shoes": "法师之靴",
    "Berserker's Greaves": "狂战士胫甲",
    "Mercury's Treads": "水银之靴",
    "Plated Steelcaps": "铁板靴",
    "Ionian Boots": "艾欧尼亚之靴",
    "Ionian Boots of Lucidity": "明朗之靴",
    "Boots of Swiftness": "轻灵之靴",
    # Component items (short names that appear in extracted text)
    "Hunger": "无尽饥渴",
    # Augment names that might appear (keep as-is, these are already CN)
}

# Sort by length (longest first) to avoid partial replacements
SORTED_ITEMS = sorted(ITEM_MAP.items(), key=lambda x: -len(x[0]))

def translate_build(build_str):
    """Replace English item names with Chinese in a build string."""
    if not build_str:
        return build_str
    result = build_str
    for en, cn in SORTED_ITEMS:
        result = result.replace(en, cn)
    return result

def translate_tips(tips_str):
    """Replace English item names in tips text."""
    if not tips_str:
        return tips_str
    result = tips_str
    for en, cn in SORTED_ITEMS:
        result = result.replace(en, cn)
    return result

def main():
    with open(SRC, "r", encoding="utf-8") as f:
        data = json.load(f)

    shutil.copy2(SRC, BAK)
    print(f"Backup saved to {BAK}")

    translated_count = 0
    for champ in data["champions"]:
        old_build = champ.get("build", "") or ""
        old_tips = champ.get("tips", "") or ""
        
        new_build = translate_build(old_build)
        new_tips = translate_tips(old_tips)
        
        if new_build != old_build or new_tips != old_tips:
            translated_count += 1
        
        champ["build"] = new_build
        champ["tips"] = new_tips

    with open(SRC, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=None, separators=(",", ":"))

    print(f"Translated items in {translated_count}/{len(data['champions'])} champions")
    
    # Show sample
    sample = data["champions"][0]
    print(f"\nSample ({sample['name']}):")
    print(f"  Build: {sample['build'][:120]}...")
    print(f"  Tips: {sample['tips'][:120]}...")

    # Check for remaining English words (potential untranslated items)
    remaining = set()
    for champ in data["champions"]:
        build = champ.get("build", "") or ""
        # Find English words that look like item names (capitalized, >3 chars)
        matches = re.findall(r"(?<!\w)[A-Z][a-zA-Z'.]{3,}(?:\s+[A-Z][a-zA-Z'.]+)*(?!\w)", build)
        for m in matches:
            remaining.add(m.strip())
    
    if remaining:
        print(f"\nRemaining untranslated (may be skill names or non-items):")
        for r in sorted(remaining):
            print(f"  - {r}")

if __name__ == "__main__":
    main()
