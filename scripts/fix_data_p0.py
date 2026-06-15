#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
fix_data_p0.py -- P0 数据修复脚本

修复内容:
1. synergies.json: 修复 24 条 source_note 字段的 Unicode 编码损坏 (slash-u -> backslash-u)
2. augments.json: 将 4 个已移除增强标记为 removed (adamant, guilty_pleasure, cerberus, executioner)
3. augments.json: 修正 big_brain 的效果描述

用法:
    cd D:\CODE\project\aram-insight
    python scripts/fix_data_p0.py
"""

import io
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Windows 终端 UTF-8 兼容: 使用 io.TextIOWrapper 包装 stdout/stderr
# ---------------------------------------------------------------------------
if sys.platform == "win32":
    # 替换 stdout 为 UTF-8 编码的 TextIOWrapper
    sys.stdout = io.TextIOWrapper(
        sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True
    )
    sys.stderr = io.TextIOWrapper(
        sys.stderr.buffer, encoding="utf-8", errors="replace", line_buffering=True
    )

# ---------------------------------------------------------------------------
# 路径配置
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
DATA_DIR = PROJECT_ROOT / "data"
BACKUP_DIR = PROJECT_ROOT / "pipeline" / "output"

SYNERGIES_PATH = DATA_DIR / "synergies.json"
AUGMENTS_PATH = DATA_DIR / "augments.json"


def backup_file(filepath: Path) -> Path:
    """将文件备份到 pipeline/output/ 目录，返回备份路径。"""
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    backup_name = filepath.name.replace(".json", "_p0_backup.json")
    backup_path = BACKUP_DIR / backup_name
    shutil.copy2(filepath, backup_path)
    print(f"  [备份] {filepath.relative_to(PROJECT_ROOT)} -> {backup_path.relative_to(PROJECT_ROOT)}")
    return backup_path


def load_json(filepath: Path) -> object:
    """读取 JSON 文件。"""
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(filepath: Path, data: object) -> None:
    """写入 JSON 文件，使用 ensure_ascii=False 和 indent=2。"""
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")  # 末尾换行


# ---------------------------------------------------------------------------
# 修复 1: synergies.json Unicode 损坏
# ---------------------------------------------------------------------------

# 匹配 /u 后跟恰好 4 个十六进制数字的模式
CORRUPTED_UNICODE_RE = re.compile(r"/u([0-9a-fA-F]{4})")


def decode_corrupted_unicode(s: str) -> str:
    """
    将损坏的 Unicode 字符串还原。

    把 /uXXXX 替换为对应的 Unicode 字符。
    注意：仅匹配 /u 后跟恰好 4 个十六进制数字的模式，
    因此已解码文本中的普通 / 不会被误匹配。
    """
    def _replace(match):
        hex_code = match.group(1)
        return chr(int(hex_code, 16))

    return CORRUPTED_UNICODE_RE.sub(_replace, s)


def fix_synergies() -> int:
    """修复 synergies.json 中的 Unicode 损坏，返回修复条目数。"""
    print()
    print("=" * 60)
    print("  [修复 1] synergies.json — Unicode 编码损坏修复")
    print("=" * 60)

    backup_file(SYNERGIES_PATH)
    data = load_json(SYNERGIES_PATH)

    fixed_count = 0
    for i, entry in enumerate(data):
        source_note = entry.get("source_note", "")
        if not source_note or "/u" not in source_note:
            continue

        # 检查是否有 /uXXXX 模式（而非仅仅是普通的 /u 子串）
        if not CORRUPTED_UNICODE_RE.search(source_note):
            continue

        old_value = source_note
        new_value = decode_corrupted_unicode(source_note)
        entry["source_note"] = new_value

        hero = entry.get("hero", "?")
        aug = entry.get("aug", "?")
        print(f"  条目 {i + 1} [{hero} + {aug}]:")
        print(f"    source_note 旧值: {old_value}")
        print(f"    source_note 新值: {new_value}")
        print()
        fixed_count += 1

    save_json(SYNERGIES_PATH, data)
    print(f"  -> synergies.json 共修复 {fixed_count} 条 Unicode 损坏记录")
    return fixed_count


# ---------------------------------------------------------------------------
# 修复 2: augments.json — 标记 4 个已移除增强
# ---------------------------------------------------------------------------

REMOVED_AUGMENTS = {
    "adamant": {"patch_removed": "26.12"},
    "guilty_pleasure": {"patch_removed": "26.12"},
    "cerberus": {"patch_removed": "26.12"},
    "executioner": {"patch_removed": "26.12"},
}


def mark_removed_augments(data: list) -> int:
    """标记已移除增强，返回修改条目数。"""
    print()
    print("=" * 60)
    print("  [修复 2] augments.json — 标记 4 个已移除增强")
    print("=" * 60)

    fixed_count = 0
    for entry in data:
        aug_id = entry.get("id", "")
        if aug_id not in REMOVED_AUGMENTS:
            continue

        updates = REMOVED_AUGMENTS[aug_id]
        name = entry.get("name", "?")
        print(f"  增强: {aug_id} ({name})")

        # 修改 status
        old_status = entry.get("status", "")
        new_status = "removed"
        print(f"    status 旧值: {old_status}")
        print(f"    status 新值: {new_status}")
        entry["status"] = new_status

        # 添加/更新 patch_removed
        old_patch_removed = entry.get("patch_removed", None)
        new_patch_removed = updates["patch_removed"]
        print(f"    patch_removed 旧值: {old_patch_removed}")
        print(f"    patch_removed 新值: {new_patch_removed}")
        entry["patch_removed"] = new_patch_removed

        print()
        fixed_count += 1

    print(f"  -> 共标记 {fixed_count} 个增强为 removed")
    return fixed_count


# ---------------------------------------------------------------------------
# 修复 3: augments.json — 修正 big_brain 效果描述
# ---------------------------------------------------------------------------

BIG_BRAIN_FIXES = {
    "effect": "获得一个吸收等于300%法术强度伤害的护盾，持续至被摧毁。护盾在重生时和每70秒补充一次。",
    "effect_en": "Gain a shield that absorbs damage equal to 300% AP and lasts until destroyed. Shield is replenished upon respawn and every 70 seconds.",
    "desc": "获得一个吸收等于300%法术强度伤害的护盾，持续至被摧毁。护盾在重生时和每70秒补充一次。",
    "trigger": "被动生效，护盾在重生和定时补充时触发",
}


def fix_big_brain(data: list) -> bool:
    """修正 big_brain 增强描述，返回是否找到并修改。"""
    print()
    print("=" * 60)
    print("  [修复 3] augments.json — 修正 big_brain 效果描述")
    print("=" * 60)

    for entry in data:
        if entry.get("id") != "big_brain":
            continue

        name = entry.get("name", "?")
        print(f"  增强: big_brain ({name})")

        for field, new_value in BIG_BRAIN_FIXES.items():
            old_value = entry.get(field, "")
            if old_value != new_value:
                print(f"    {field} 旧值: {old_value}")
                print(f"    {field} 新值: {new_value}")
                entry[field] = new_value
            else:
                print(f"    {field}: 已是正确值，跳过")

        print()
        print("  -> big_brain 效果描述已修正")
        return True

    print("  !! 未找到 id=big_brain 的增强条目")
    return False


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------

def main() -> int:
    print("=" * 60)
    print("  P0 数据修复脚本")
    print(f"  项目根目录: {PROJECT_ROOT}")
    print("=" * 60)

    # --- 修复 1: synergies.json Unicode 损坏 ---
    fix_synergies()

    # --- 修复 2 & 3: augments.json ---
    # 先备份 augments.json（只做一次）
    print()
    print("  [备份 augments.json]")
    backup_file(AUGMENTS_PATH)

    aug_data = load_json(AUGMENTS_PATH)

    mark_removed_augments(aug_data)
    fix_big_brain(aug_data)

    save_json(AUGMENTS_PATH, aug_data)
    print()
    print("  -> augments.json 已保存")

    # --- 运行校验脚本 ---
    print()
    print("=" * 60)
    print("  运行 validate_data.py 进行校验")
    print("=" * 60)
    print()

    validate_script = SCRIPT_DIR / "validate_data.py"
    if not validate_script.exists():
        print(f"  !! 校验脚本不存在: {validate_script}")
        return 0

    result = subprocess.run(
        [sys.executable, str(validate_script)],
        cwd=str(PROJECT_ROOT),
        capture_output=False,
    )
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
