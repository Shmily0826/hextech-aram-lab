"""Translate English augment names in issues.json to Chinese."""
import json, shutil

SRC = "data/issues.json"
BAK = "data/issues.backup_before_i18n.json"

# English augment name → Chinese augment name
AUG_MAP = {
    "Critical Healing": "会心治疗",
    "Critical Missile": "暴击飞弹",
    "Lightning Strike": "闪电打击",
    "Methodical": "一板一眼",
    "Pandora's Box": "潘多拉的盒子",
    "Infernal Conduit": "地狱导管",
}

def main():
    with open(SRC, "r", encoding="utf-8") as f:
        issues = json.load(f)

    shutil.copy2(SRC, BAK)
    print(f"Backup saved to {BAK}")

    count = 0
    for issue in issues:
        augs = issue.get("augs", [])
        new_augs = []
        changed = False
        for a in augs:
            if a in AUG_MAP:
                new_augs.append(AUG_MAP[a])
                print(f"  ✓ '{a}' → '{AUG_MAP[a]}' in: {issue['title'][:40]}")
                changed = True
            else:
                new_augs.append(a)
        if changed:
            issue["augs"] = new_augs
            count += 1

    with open(SRC, "w", encoding="utf-8") as f:
        json.dump(issues, f, ensure_ascii=False, indent=2)

    print(f"\nFixed {count} issues")

if __name__ == "__main__":
    main()
