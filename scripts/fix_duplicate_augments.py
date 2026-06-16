"""
修复：删除重复的 8 个增强条目，将 blitz.gg 英文名添加为现有条目的别名
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUGMENTS_PATH = os.path.join(ROOT, 'data', 'augments.json')

# blitz.gg 英文名 → 应该对应的现有增强 id
BLITZ_TO_EXISTING = {
    "en passant": "eat_the_path",        # 吃过路兵 (已有: Eat the Path)
    "echo cast": None,                    # 回响施放 - 需要查找
    "wee woo wee woo": None,             # 喂呜喂呜 - 需要查找
    "ravenous bind": None,               # 贪欲束缚 - 需要查找
    "it's go time": None,                # 前进时间到 - 需要查找
    "trusty weapon": None,               # 可靠武器 - 需要查找
    "rejuvenation": None,                # 活力焕发 - 需要查找
    "minionmancer": None,                # 仆从大师 - 需要查找
}

# 新增条目的 id 列表（要删除）
NEW_IDS_TO_REMOVE = {
    "its_go_time", "rejuvenation", "trusty_weapon", "en_passant",
    "wee_woo_wee_woo", "echo_cast", "ravenous_bind", "minionmancer"
}


def main():
    with open(AUGMENTS_PATH, 'r', encoding='utf-8') as f:
        augments = json.load(f)
    
    # 找出需要删除的条目和保留的条目
    to_remove = []
    to_keep = []
    for a in augments:
        if a['id'] in NEW_IDS_TO_REMOVE:
            to_remove.append(a)
        else:
            to_keep.append(a)
    
    print(f"Removing {len(to_remove)} duplicate entries:")
    for a in to_remove:
        print(f"  - {a['id']}: {a['name']} ({a['name_en']})")
    
    # 为现有条目添加别名
    # 映射: 中文名 → blitz.gg 英文名别名
    cn_to_blitz_aliases = {
        "吃过路兵": ["en passant"],
        "回响施放": ["echo cast"],
        "喂呜喂呜": ["wee woo wee woo", "wee woo"],
        "贪欲束缚": ["ravenous bind"],
        "前进时间到": ["it's go time", "its go time", "go time"],
        "可靠武器": ["trusty weapon"],
        "活力焕发": ["rejuvenation"],
        "仆从大师": ["minionmancer"],
    }
    
    alias_added = 0
    for a in to_keep:
        cn_name = a.get('name', '')
        if cn_name in cn_to_blitz_aliases:
            existing_aliases = set(al.lower() for al in a.get('aliases', []))
            new_aliases = cn_to_blitz_aliases[cn_name]
            added_for_this = []
            for alias in new_aliases:
                if alias.lower() not in existing_aliases:
                    if 'aliases' not in a:
                        a['aliases'] = []
                    a['aliases'].append(alias)
                    existing_aliases.add(alias.lower())
                    added_for_this.append(alias)
            if added_for_this:
                print(f"  + aliases for '{cn_name}' ({a['id']}): {added_for_this}")
                alias_added += len(added_for_this)
    
    print(f"\nAdded {alias_added} aliases to existing entries")
    print(f"Total augments after cleanup: {len(to_keep)}")
    
    # 排序
    tier_order = {'prismatic': 0, 'gold': 1, 'silver': 2, 'unknown': 3}
    to_keep.sort(key=lambda a: (tier_order.get(a.get('tier', 'unknown'), 3),
                                 a.get('name', '')))
    
    # 写回
    with open(AUGMENTS_PATH, 'w', encoding='utf-8') as f:
        json.dump(to_keep, f, ensure_ascii=False, indent=2)
    
    print(f"Saved {len(to_keep)} augments")


if __name__ == '__main__':
    main()
