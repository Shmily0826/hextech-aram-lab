"""Fix augment data quality issues:
1. Add win_rate for 10 augments (3 have no data yet — skip those)
2. Fix 神圣干预 '若干' placeholder → '2.5'
3. Mark 坚若磐石 as removed (confirmed removed from game)
"""
import json, shutil

SRC = "data/augments.json"
BAK = "data/augments.backup_before_fix.json"

# Win rates from arammayhem.com (patch 26.12, June 2026)
# 3 augments have no data yet (软弹啪叽抓, 活力焕发, 绝活玩家) — skip
WIN_RATES = {
    "灵魄炸弹": {"win_rate": 58.63, "pick_rate": 3.79},
    "空投熊": {"win_rate": 52.06, "pick_rate": 0.52},
    "魄罗蛮冲": {"win_rate": 40.42, "pick_rate": 0.02},
    "冰雪爆裂": {"win_rate": 45.51, "pick_rate": 0.09},
    "无尽大杀四方": {"win_rate": 48.76, "pick_rate": 2.11},
    "牙仙子": {"win_rate": 51.42, "pick_rate": 8.93},
    "自然即是治愈": {"win_rate": 48.41, "pick_rate": 5.67},
    "位面转移": {"win_rate": 39.94, "pick_rate": 0.03},
    "电涌力场": {"win_rate": 45.15, "pick_rate": 2.80},
}

# 坚若磐石 was removed from the game
REMOVED = {"坚若磐石"}

# 神圣干预: replace '若干' with actual duration
FIX_DESC = {
    "神圣干预": {
        "old_effect_fragment": "持续若干秒",
        "new_effect_fragment": "持续2.5秒",
    }
}

def main():
    with open(SRC, "r", encoding="utf-8") as f:
        augs = json.load(f)

    shutil.copy2(SRC, BAK)
    print(f"Backup saved to {BAK}")

    changes = []
    for aug in augs:
        name = aug.get("name", "")

        # Fix win rates
        if name in WIN_RATES:
            wr = WIN_RATES[name]
            old_wr = aug.get("win_rate")
            aug["win_rate"] = wr["win_rate"]
            if wr.get("pick_rate") is not None:
                aug["pick_rate"] = wr["pick_rate"]
            changes.append(f"  ✓ {name}: win_rate {old_wr} → {wr['win_rate']}%")

        # Fix removed status
        if name in REMOVED:
            old_status = aug.get("status")
            aug["status"] = "removed"
            changes.append(f"  ✓ {name}: status {old_status} → removed")

        # Fix '若干' placeholder
        if name in FIX_DESC:
            fix = FIX_DESC[name]
            for field in ["effect", "desc"]:
                val = aug.get(field, "") or ""
                if fix["old_effect_fragment"] in val:
                    aug[field] = val.replace(
                        fix["old_effect_fragment"],
                        fix["new_effect_fragment"],
                    )
                    changes.append(f"  ✓ {name}: {field} '{fix['old_effect_fragment']}' → '{fix['new_effect_fragment']}'")

    with open(SRC, "w", encoding="utf-8") as f:
        json.dump(augs, f, ensure_ascii=False, indent=None, separators=(",", ":"))

    print(f"Made {len(changes)} changes:")
    for c in changes:
        print(c)

    # Verify
    with open(SRC, "r", encoding="utf-8") as f:
        verify = json.load(f)
    missing = [a["name"] for a in verify if a.get("status") == "active" and a.get("win_rate") is None]
    print(f"\nRemaining active augments without win_rate: {len(missing)}")
    for n in missing:
        print(f"  - {n} (new in 26.12, no data yet)")

if __name__ == "__main__":
    main()
