#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
merge_selected_augments.py — 小批量合并真实增强

从 augment_import_candidates.json 中挑选 25 个高置信增强，
合并到 data/augments.json。不删除当前 16 个增强。
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timezone

if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

PROJECT_ROOT = Path(__file__).resolve().parent.parent
AUGMENTS_PATH = PROJECT_ROOT / "data" / "augments.json"
CANDIDATES_PATH = PROJECT_ROOT / "pipeline" / "output" / "augment_import_candidates.json"

# ---------------------------------------------------------------------------
# 挑选的 25 个高置信增强 ID（覆盖三个 tier，效果描述清晰）
# ---------------------------------------------------------------------------
SELECTED_IDS = [
    # Silver (9)
    "adamant", "blunt_force", "deft", "erosion", "first_aid_kit",
    "goredrink", "homeguard", "marked_for_death", "guilty_pleasure",
    # Gold (9)
    "back_to_basics", "biggest_snowball_ever", "circle_of_death",
    "dont_blink", "get_excited", "goliath", "growth_spurt",
    "bread_and_butter", "fan_the_hammer",
    # Prismatic (7)
    "cant_touch_this", "celestial_body", "cerberus", "dashing",
    "dive_bomber", "dropkick", "executioner",
]

# Tier 冲突修复（针对当前 16 个中匹配的 3 个）
TIER_FIXES = {
    "all_for_you": "gold",       # 当前 silver → Wiki gold
    "big_brain": "gold",         # 当前 prismatic → Wiki gold
    "blade_waltz": "prismatic",  # 当前 gold → Wiki prismatic
}

# 原型增强标记（当前 16 个中不在 Wiki 来源的 13 个）
PROTOTYPE_IDS = [
    "chain_lightning", "toxic_amplifier", "armor_piercing",
    "annihilation_gaze", "ultimate_cooldown", "mana_fountain",
    "lethal_tempo", "untouchable", "physical_to_magical",
    "ultimate_hunter", "psionic_shield", "echo", "phantom_dance",
]

# 冲突别名清理（首字母缩写冲突）
CONFLICTING_SHORT_ALIASES = {
    "db", "ms", "bb", "ic", "rr", "sw", "sd", "sr", "sas", "ss",
    "as", "lt", "pd", "xp",
}


def clean_aliases(aliases: list[str]) -> list[str]:
    """移除冲突的短别名。"""
    cleaned = []
    for a in aliases:
        al = a.strip().lower()
        if al in CONFLICTING_SHORT_ALIASES:
            continue
        if len(al) <= 2 and al.isalpha():
            continue  # 移除所有 2 字母纯字母缩写
        cleaned.append(a)
    return cleaned


def main() -> int:
    print("=" * 64)
    print("  小批量合并真实增强")
    print("=" * 64)

    # 加载
    with open(AUGMENTS_PATH, encoding="utf-8") as f:
        current = json.load(f)
    with open(CANDIDATES_PATH, encoding="utf-8") as f:
        candidates = json.load(f)

    print(f"  当前增强: {len(current)}")
    print(f"  候选总数: {len(candidates)}")

    # 构建候选索引 (by id)
    cand_by_id = {c["id"]: c for c in candidates}

    # ---- Step 1: 修复当前 16 个的 tier 冲突 ----
    print("\n[1/4] 修复 Tier 冲突...")
    tier_fix_count = 0
    for aug in current:
        aid = aug.get("id", "")
        if aid in TIER_FIXES:
            old_tier = aug.get("tier", "")
            new_tier = TIER_FIXES[aid]
            if old_tier != new_tier:
                aug["tier"] = new_tier
                # 同步 rar（如果存在且一致）
                if aug.get("rar") and aug["rar"] != new_tier:
                    # prismatic → prismatic (不变), gold → gold
                    if new_tier == "prismatic":
                        aug["rar"] = "prism"
                    else:
                        aug["rar"] = new_tier
                note = f"Tier 已从 {old_tier} 修正为 {new_tier}（来源: LoL Wiki Module）"
                if aid == "big_brain":
                    note += "。注：Wiki 中 Big Brain 为 Gold 级别"
                aug["notes"] = (aug.get("notes", "") + " " + note).strip()
                print(f"  ✓ {aug['name_en']}: {old_tier} → {new_tier}")
                tier_fix_count += 1

        # 清理当前增强的冲突别名
        if "aliases" in aug:
            before = len(aug["aliases"])
            aug["aliases"] = clean_aliases(aug["aliases"])
            removed = before - len(aug["aliases"])
            if removed > 0:
                print(f"  ✓ {aug['name_en']}: 移除 {removed} 个冲突别名")

    # ---- Step 2: 标记原型增强 ----
    print("\n[2/4] 标记原型增强...")
    proto_count = 0
    for aug in current:
        aid = aug.get("id", "")
        if aid in PROTOTYPE_IDS:
            note = "原型增强：该增强不在 LoL Wiki ARAM:Mayhem 数据中，可能为早期占位数据。保留供后续人工审核。"
            existing_notes = aug.get("notes", "")
            if note not in existing_notes:
                aug["notes"] = (existing_notes + " " + note).strip() if existing_notes else note
            aug["source_status"] = "prototype"
            proto_count += 1
            print(f"  ✓ {aug['name_en']} ({aug['name']}) 标记为 prototype")

    # ---- Step 3: 合并新增强 ----
    print("\n[3/4] 合并新增强...")
    current_ids = {aug["id"] for aug in current}
    merged_count = 0
    missing_zh_count = 0

    for sid in SELECTED_IDS:
        if sid in current_ids:
            print(f"  ⊳ 跳过已存在: {sid}")
            continue

        cand = cand_by_id.get(sid)
        if not cand:
            print(f"  ⊳ 候选不存在: {sid}")
            continue

        # 构建正式记录（遵循当前 schema）
        entry = {
            "id": cand["id"],
            "name": cand["name_en"],  # 暂无中文名，用英文名
            "name_en": cand["name_en"],
            "aliases": clean_aliases(cand.get("aliases", [])),
            "tier": cand["tier"],
            "status": "active",
            "effect": "",
            "effect_en": cand.get("effect_en", ""),
            "tags": cand.get("tags", []),
            "patch_added": "",
            "patch_removed": None,
            "source": {
                "type": "lol_wiki_module",
                "url": cand.get("source", {}).get("url", ""),
                "verified_at": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            },
            "notes": cand.get("notes", ""),
            "localization_status": "missing_zh",
            "source_status": "potentially_outdated",
            # 兼容旧字段
            "rar": cand["tier"] if cand["tier"] != "prismatic" else "prism",
            "wr": None,
            "pr": None,
            "desc": "",
            "trigger": "",
            "best": [],
            "avoid": [],
            "tests": [],
        }

        current.append(entry)
        current_ids.add(sid)
        merged_count += 1
        missing_zh_count += 1
        print(f"  ✓ 合并: {cand['name_en']} [{cand['tier']}]")

    # 统计当前所有 missing_zh
    total_missing_zh = sum(
        1 for a in current
        if a.get("localization_status") == "missing_zh"
           or (not a.get("name") or a.get("name") == a.get("name_en"))
    )

    # ---- Step 4: 写入 ----
    print("\n[4/4] 写入 data/augments.json...")
    with open(AUGMENTS_PATH, "w", encoding="utf-8") as f:
        json.dump(current, f, ensure_ascii=False, indent=2)

    print(f"  ✓ 写入完成: {len(current)} 个增强")

    # ---- 汇总 ----
    print("\n" + "=" * 64)
    print("  合并汇总")
    print("=" * 64)
    print(f"  合并前数量        : {len(current) - merged_count}")
    print(f"  新增合并          : {merged_count}")
    print(f"  Tier 冲突修复     : {tier_fix_count}")
    print(f"  原型标记          : {proto_count}")
    print(f"  合并后总数        : {len(current)}")
    print(f"  缺少中文名        : {total_missing_zh}")
    print(f"  输出文件          : {AUGMENTS_PATH}")
    print("=" * 64)

    return 0


if __name__ == "__main__":
    sys.exit(main())
