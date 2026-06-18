"""Spot check corrected item names."""
import json

with open("data/champions.json", "r", encoding="utf-8") as f:
    data = json.load(f)

for name in ["吉格斯", "薇恩", "翠神", "卡莎", "亚索"]:
    c = next((x for x in data["champions"] if x["name"] == name), None)
    if c:
        build = c.get("build", "")
        print(f"{name}:")
        print(f"  {build[:130]}")
        print()

# Also check for any remaining old names that shouldn't be there
OLD_NAMES = [
    "实验性海克斯板甲", "纳沃利闪烁之刃", "云·塔尔野性之箭",
    "急速火炮", "宇宙驱驰", "风暴涌动", "电涡之剑", "碎裂王冠",
    "毁灭仪式", "无尽饥渴", "黑火火炬", "班德尔笛", "低语之环",
    "实现者", "吸蓝刀", "歌之冕", "恶咒", "永冬",
    "暗影焰",  # Should be replaced by 影焰
    "黎明与黄昏",  # Should be 黄昏与黎明
]

found_issues = []
for c in data["champions"]:
    build = c.get("build", "") or ""
    tips = c.get("tips", "") or ""
    for old in OLD_NAMES:
        if old in build or old in tips:
            found_issues.append((c["name"], old))

if found_issues:
    print(f"ISSUES FOUND: {len(found_issues)}")
    for name, old in found_issues:
        print(f"  {name}: still has '{old}'")
else:
    print("All old names successfully replaced!")
