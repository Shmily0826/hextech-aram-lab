#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
apply_chinese_names.py
Apply Chinese augment names from arammayhem.com to data/augments.json.

Usage:
    python scripts/apply_chinese_names.py
"""

import io
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Windows console UTF-8 support via io.TextIOWrapper
# ---------------------------------------------------------------------------
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
AUGMENTS_FILE = PROJECT_ROOT / "data" / "augments.json"
BACKUP_FILE = PROJECT_ROOT / "pipeline" / "output" / "augments_backup_before_zh.json"
VALIDATE_SCRIPT = PROJECT_ROOT / "scripts" / "validate_data.py"

# ---------------------------------------------------------------------------
# Mapping: augment id -> Chinese name (from arammayhem.com)
# ---------------------------------------------------------------------------
CHINESE_NAME_MAP = {
    "blunt_force":            "大力",
    "deft":                   "灵巧",
    "erosion":                "侵蚀",
    "first_aid_kit":          "急救用具",
    "goredrink":              "渴血",
    "homeguard":              "家园卫士",
    "back_to_basics":         "回归基本功",
    "biggest_snowball_ever":  "史上最大雪球",
    "circle_of_death":        "死亡之环",
    "get_excited":            "罪恶快感",
    "goliath":                "歌利亚巨人",
    "growth_spurt":           "生机迸发",
    "bread_and_butter":       "面包和黄油",
    "fan_the_hammer":         "连拨击锤",
    "celestial_body":         "星界躯体",
    "dashing":                "全凭身法",
    "dive_bomber":            "俯冲轰炸",
    "dropkick":               "飞身踢",
    "don_t_blink":            "唯快不破",
    "can_t_touch_this":       "你摸不到",
}


def main():
    print("=" * 60)
    print("apply_chinese_names.py")
    print("=" * 60)

    # ------------------------------------------------------------------
    # Step 1: Read augments.json
    # ------------------------------------------------------------------
    print(f"\n[1] Reading {AUGMENTS_FILE}")
    with open(AUGMENTS_FILE, "r", encoding="utf-8") as f:
        augments = json.load(f)
    print(f"    Loaded {len(augments)} augments.")

    # ------------------------------------------------------------------
    # Step 2: Create backup
    # ------------------------------------------------------------------
    print(f"\n[2] Backing up to {BACKUP_FILE}")
    BACKUP_FILE.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(str(AUGMENTS_FILE), str(BACKUP_FILE))
    print("    Backup created.")

    # ------------------------------------------------------------------
    # Step 3: Build id -> index lookup
    # ------------------------------------------------------------------
    id_to_index = {}
    for idx, aug in enumerate(augments):
        aug_id = aug.get("id")
        if aug_id:
            id_to_index[aug_id] = idx

    # ------------------------------------------------------------------
    # Step 4: Apply Chinese names
    # ------------------------------------------------------------------
    print(f"\n[3] Applying {len(CHINESE_NAME_MAP)} Chinese name mappings...\n")
    changes = []
    not_found = []

    for aug_id, chinese_name in CHINESE_NAME_MAP.items():
        if aug_id not in id_to_index:
            not_found.append(aug_id)
            print(f"    [MISSING] {aug_id} - not found in augments.json")
            continue

        idx = id_to_index[aug_id]
        aug = augments[idx]
        old_name = aug.get("name", "")

        # Update the name field
        aug["name"] = chinese_name

        # Remove localization_status if it exists
        removed_field = False
        if "localization_status" in aug:
            del aug["localization_status"]
            removed_field = True

        changes.append({
            "id": aug_id,
            "old_name": old_name,
            "new_name": chinese_name,
            "removed_localization_status": removed_field,
        })

        loc_note = " + removed localization_status" if removed_field else ""
        print(f"    [OK] {aug_id}: \"{old_name}\" -> \"{chinese_name}\"{loc_note}")

    # ------------------------------------------------------------------
    # Step 5: Write back
    # ------------------------------------------------------------------
    print(f"\n[4] Writing updated augments.json...")
    with open(AUGMENTS_FILE, "w", encoding="utf-8") as f:
        json.dump(augments, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print("    Done.")

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    print(f"\n{'=' * 60}")
    print(f"SUMMARY")
    print(f"{'=' * 60}")
    print(f"  Total augments in file:    {len(augments)}")
    print(f"  Mappings to apply:         {len(CHINESE_NAME_MAP)}")
    print(f"  Successfully applied:      {len(changes)}")
    print(f"  Not found (skipped):       {len(not_found)}")
    if not_found:
        print(f"  Missing IDs: {not_found}")

    print(f"\nChanges made:")
    for c in changes:
        loc = " [removed localization_status]" if c["removed_localization_status"] else ""
        print(f"  - {c['id']}: \"{c['old_name']}\" -> \"{c['new_name']}\"{loc}")

    # ------------------------------------------------------------------
    # Step 6: Run validate_data.py
    # ------------------------------------------------------------------
    print(f"\n{'=' * 60}")
    print(f"Running validate_data.py...")
    print(f"{'=' * 60}")

    python_exe = sys.executable
    result = subprocess.run(
        [python_exe, str(VALIDATE_SCRIPT)],
        cwd=str(PROJECT_ROOT),
        capture_output=False,
    )

    if result.returncode != 0:
        print(f"\n[WARNING] validate_data.py exited with code {result.returncode}")
        sys.exit(result.returncode)
    else:
        print(f"\n[OK] Validation passed.")


if __name__ == "__main__":
    main()
