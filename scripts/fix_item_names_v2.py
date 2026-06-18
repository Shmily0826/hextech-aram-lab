"""Fix 22 incorrect item name translations to match official 国服简体中文.
Sorted longest-first to avoid partial replacement issues.
"""
import json, shutil

SRC = "data/champions.json"
BAK = "data/champions.backup_before_i18n_v2.json"

# Official Chinese item name corrections (22 fixes)
# Sorted by length of old name (longest first) to avoid substring issues
FIXES = {
    "实验性海克斯板甲": "海克斯注力刚壁",      # Experimental Hexplate
    "纳沃利闪烁之刃": "纳沃利烁刃",             # Navori Flickerblade
    "云·塔尔野性之箭": "育恩塔尔荒野箭",        # Yun Tal Wildarrows
    "急速火炮": "疾射火炮",                      # Rapid Firecannon
    "宇宙驱驰": "星界驱驰",                      # Cosmic Drive
    "暗影焰": "影焰",                            # Shadowflame
    "月石再生": "月石再生器",                     # Moonstone Renewer (add 器)
    "风暴涌动": "风暴狂涌",                      # Stormsurge
    "黎明与黄昏": "黄昏与黎明",                   # Dawn and Dusk (order reversed)
    "电涡之剑": "电震涡流剑",                    # Voltaic Cyclosword
    "碎裂王冠": "破碎王后之冕",                   # Crown of the Shattered Queen
    "毁灭仪式": "毁坏仪式",                      # Rite of Ruin
    "无尽饥渴": "无穷饥渴",                      # Thirst Unending
    "黑火火炬": "黯炎火炬",                      # Blackfire Torch
    "班德尔笛": "班德尔音管",                     # Bandlepipes
    "实现者": "实现器",                           # Actualizer
    "千变者": "千变者贾修",                      # Jak'Sho, The Protean
    "吸蓝刀": "夺萃之镰",                        # Essence Reaver
    "低语之环": "耳语头环",                       # Whispering Circlet
    "歌之冕": "歌之权冠",                        # Diadem of Songs
    "恶咒": "恶意",                              # Malignance
    "永冬": "末日寒冬",                           # Fimbulwinter
}

# Sort by length of old name (longest first)
SORTED_FIXES = sorted(FIXES.items(), key=lambda x: -len(x[0]))

def main():
    with open(SRC, "r", encoding="utf-8") as f:
        data = json.load(f)

    shutil.copy2(SRC, BAK)
    print(f"Backup saved to {BAK}")

    count = 0
    change_details = {}
    for champ in data["champions"]:
        changed = False
        for field in ["build", "tips"]:
            val = champ.get(field, "") or ""
            new_val = val
            for old, new in SORTED_FIXES:
                if old in new_val:
                    new_val = new_val.replace(old, new)
                    if old not in change_details:
                        change_details[old] = 0
                    change_details[old] += 1
            if new_val != val:
                champ[field] = new_val
                changed = True
        if changed:
            count += 1

    with open(SRC, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=None, separators=(",", ":"))

    print(f"Fixed {count}/{len(data['champions'])} champions")
    print(f"\nReplacement counts:")
    for old, new in SORTED_FIXES:
        n = change_details.get(old, 0)
        status = "✓" if n > 0 else "✗ (not found)"
        print(f"  {status} {old} → {new} ({n}x)")

    # Final verification: check no old names remain
    import re
    remaining = set()
    for c in data["champions"]:
        build = c.get("build", "") or ""
        for old, new in FIXES.items():
            if old in build:
                remaining.add(old)
    if remaining:
        print(f"\nWARNING: Old names still found: {remaining}")
    else:
        print(f"\nAll old names successfully replaced!")

if __name__ == "__main__":
    main()
