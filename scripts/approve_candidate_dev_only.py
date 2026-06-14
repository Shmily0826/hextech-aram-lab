#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
approve_candidate_dev_only.py — 仅限本地开发测试的非交互式候选审核工具

⚠️ 注意事项：
  - 仅限本地开发测试使用，不用于自动化批量审核
  - 必须通过 --candidate-id 参数显式指定要审核的候选 ID
  - 不允许批量 approve（每次只能处理 1 条候选）
  - 审核前会显示完整 diff（候选 → 正式格式的转换对比）
  - 必须运行 validate_data.py 校验
  - validate 失败会自动回滚
  - 不允许被 run_pipeline.py 自动调用（无 import 接口，仅 CLI）

用法：
    python scripts/approve_candidate_dev_only.py --candidate-id syn_20260614043745_0
    python scripts/approve_candidate_dev_only.py --candidate-id syn_20260614043745_0 --type synergies
    python scripts/approve_candidate_dev_only.py --candidate-id bug_20260614043745_0 --type bugs
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# 禁止被其他模块 import 调用
# ---------------------------------------------------------------------------
if __name__ != "__main__":
    raise ImportError(
        "approve_candidate_dev_only.py 仅限独立 CLI 运行，不允许被 import。"
    )

# Windows UTF-8
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

SCRIPT_DIR = Path(__file__).resolve().parent
PIPELINE_DIR = SCRIPT_DIR.parent / "pipeline"
PROJECT_ROOT = SCRIPT_DIR.parent
OUTPUT_DIR = PIPELINE_DIR / "output"
DATA_DIR = PROJECT_ROOT / "data"

CAND_BUGS_PATH = OUTPUT_DIR / "candidate_bugs.json"
CAND_SYNS_PATH = OUTPUT_DIR / "candidate_synergies.json"
ISSUES_PATH = DATA_DIR / "issues.json"
SYNERGIES_PATH = DATA_DIR / "synergies.json"
AUGMENTS_PATH = DATA_DIR / "augments.json"
CHANGELOG_PATH = DATA_DIR / "changelog.json"
VALIDATE_SCRIPT = SCRIPT_DIR / "validate_data.py"

sys.path.insert(0, str(PIPELINE_DIR))
from processors.normalize_entities import (
    normalize_champion_name, normalize_augment_name,
)


def load_json(path):
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def build_augment_rar_map():
    augments = load_json(AUGMENTS_PATH)
    return {
        a["name"]: a.get("rar", "unknown")
        for a in augments
        if isinstance(a, dict) and "name" in a
    }


def convert_bug_to_issue(c):
    severity = c.get("severity", "minor")
    if severity not in {"minor", "major", "critical"}:
        severity = "minor"
    ver = c.get("patch", c.get("ver", "unknown"))
    if not ver or ver.lower() == "unknown":
        ver = "unknown"
    evidence = c.get("evidence", [])
    if not isinstance(evidence, list):
        evidence = []
    return {
        "sev": severity,
        "title": c.get("title", "未知问题"),
        "heroes": [normalize_champion_name(h) for h in c.get("champions", ["unknown"])],
        "augs": [normalize_augment_name(a) for a in c.get("augments", ["unknown"])],
        "desc": c.get("description", ""),
        "ver": ver,
        "time": datetime.now().strftime("%Y-%m-%d"),
        "status": c.get("status", "investigating"),
        "confirm": 0,
        "tip": c.get("tip", ""),
        "confidence": c.get("confidence", 50),
        "evidence": evidence,
        "updated_at": now_iso(),
        "source_note": "",
    }


def convert_syn_to_synergy(c, rar_map):
    raw_aug = c.get("augment", "")
    aug_name = normalize_augment_name(raw_aug) if raw_aug else ""
    rating = c.get("rating_type", "recommend")
    if rating == "trap_warning":
        tier = "avoid"
    elif rating in {"transform", "recommend", "avoid", "bug"}:
        tier = rating
    else:
        tier = "recommend"
    rar = rar_map.get(aug_name, "unknown")
    if rar not in {"silver", "gold", "prism", "unknown"}:
        rar = "unknown"
    ver = c.get("patch", "unknown")
    if not ver or ver.lower() == "unknown":
        ver = "unknown"
    return {
        "hero": normalize_champion_name(c.get("hero", "未知")),
        "aug": aug_name,
        "rar": rar,
        "tier": tier,
        "delta": None,
        "conf": c.get("confidence", 50),
        "sample": None,
        "ver": ver,
        "src": "community",
        "status": c.get("status", "investigating"),
        "desc": c.get("description", ""),
        "trigger": c.get("trigger", ""),
        "notes": [],
        "combos": [],
        "evidence": c.get("evidence", []),
        "updated_at": now_iso(),
        "source_note": "",
    }


def display_diff(candidate, converted, cand_type):
    """显示候选原始数据与转换后正式格式的 diff。"""
    sep = "=" * 64
    print(f"\n{sep}")
    print("  DIFF: 候选原始 → 正式格式")
    print(sep)

    if cand_type == "bug_report":
        print(f"  原始 title     : {candidate.get('title', '')}")
        print(f"  正式 title     : {converted.get('title', '')}")
        print(f"  原始 champions : {candidate.get('champions', [])}")
        print(f"  正式 heroes    : {converted.get('heroes', [])}")
        print(f"  原始 augments  : {candidate.get('augments', [])}")
        print(f"  正式 augs      : {converted.get('augs', [])}")
        print(f"  原始 severity  : {candidate.get('severity', '')}")
        print(f"  正式 sev       : {converted.get('sev', '')}")
    else:
        print(f"  原始 hero      : {candidate.get('hero', '')}")
        print(f"  正式 hero      : {converted.get('hero', '')}")
        print(f"  原始 augment   : {candidate.get('augment', '')}")
        print(f"  正式 aug       : {converted.get('aug', '')}")
        print(f"  原始 rating    : {candidate.get('rating_type', '')}")
        print(f"  正式 tier      : {converted.get('tier', '')}")
        print(f"  正式 rar       : {converted.get('rar', '')}")

    print(f"  正式 status    : {converted.get('status', '')}")
    print(f"  正式 conf      : {converted.get('conf', converted.get('confidence', ''))}")
    print(f"  evidence 数量  : {len(converted.get('evidence', []))}")
    print(sep)


def run_validate():
    """运行 validate_data.py，返回是否通过。"""
    print("\n  ▶ 运行数据校验 (validate_data.py)...")
    try:
        result = subprocess.run(
            [sys.executable, str(VALIDATE_SCRIPT)],
            capture_output=True, text=True, encoding="utf-8",
            errors="replace", timeout=30,
        )
        for line in result.stdout.splitlines():
            print(f"    {line}")
        if result.returncode == 0:
            print("  ✓ 校验通过\n")
            return True
        else:
            if result.stderr:
                for line in result.stderr.splitlines():
                    print(f"    [ERR] {line}")
            print("  ✗ 校验失败\n")
            return False
    except FileNotFoundError:
        print(f"  ⚠ 未找到校验脚本: {VALIDATE_SCRIPT}")
        return False
    except subprocess.TimeoutExpired:
        print("  ⚠ 校验超时（30s）")
        return False
    except Exception as e:
        print(f"  ⚠ 校验异常: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="仅限本地开发测试的非交互式候选审核（每次仅 1 条）",
    )
    parser.add_argument(
        "--candidate-id", required=True,
        help="要 approve 的候选 candidate_id（必填，不允许批量）",
    )
    parser.add_argument(
        "--type", choices=["bugs", "synergies"], default="synergies",
        help="候选类型: bugs 或 synergies（默认 synergies）",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="仅显示 diff，不实际写入",
    )
    args = parser.parse_args()

    target_id = args.candidate_id
    cand_type = "bug_report" if args.type == "bugs" else "synergy_claim"
    source_path = CAND_BUGS_PATH if args.type == "bugs" else CAND_SYNS_PATH
    target_path = ISSUES_PATH if args.type == "bugs" else SYNERGIES_PATH

    print("=" * 64)
    print("  approve_candidate_dev_only.py — 开发用单条审核")
    print("  ⚠ 仅限本地开发测试，不用于自动化批量审核")
    print("=" * 64)
    print(f"  目标候选 ID : {target_id}")
    print(f"  候选类型    : {cand_type}")
    print(f"  来源文件    : {source_path.name}")
    print(f"  目标文件    : {target_path.name}")
    print(f"  Dry Run     : {'是' if args.dry_run else '否'}")

    # 加载候选
    candidates = load_json(source_path)
    if not candidates:
        print("\n  ✗ 候选文件为空或不存在。")
        sys.exit(1)

    # 查找目标候选（仅匹配 1 条）
    target = None
    remaining = []
    for c in candidates:
        cid = c.get("candidate_id", c.get("id", ""))
        if cid == target_id and target is None:
            target = c
        else:
            remaining.append(c)

    if target is None:
        print(f"\n  ✗ 未找到 candidate_id = '{target_id}'")
        print(f"  可用 ID: {[c.get('candidate_id', c.get('id','')) for c in candidates]}")
        sys.exit(1)

    print(f"\n  ✓ 找到候选: {target_id}")

    # 转换
    rar_map = build_augment_rar_map()
    if cand_type == "bug_report":
        converted = convert_bug_to_issue(target)
    else:
        converted = convert_syn_to_synergy(target, rar_map)

    # 显示 diff
    display_diff(target, converted, cand_type)

    if args.dry_run:
        print("\n  [Dry Run] 不写入正式文件。")
        sys.exit(0)

    # 写入正式文件
    formal_data = load_json(target_path)
    backup_path = OUTPUT_DIR / f"{target_path.stem}_backup.json"
    save_json(backup_path, formal_data)
    formal_data.append(converted)
    save_json(target_path, formal_data)

    # 校验
    ok = run_validate()
    if not ok:
        print("  ✗ 校验失败！正在回滚...")
        restore = load_json(backup_path)
        save_json(target_path, restore)
        print("  ✓ 已回滚")
        sys.exit(1)

    # 更新 changelog
    changelog = load_json(CHANGELOG_PATH)
    if cand_type == "bug_report":
        title = target.get("title", "")
        hero_str = ", ".join(target.get("champions", []))
        aug_str = ", ".join(target.get("augments", []))
    else:
        title = f"{converted['hero']} x {converted['aug']}"
        hero_str = converted["hero"]
        aug_str = converted["aug"]

    changelog.append({
        "date": now_iso(),
        "type": "bug" if cand_type == "bug_report" else "synergy",
        "title": title,
        "hero": hero_str,
        "augment": aug_str,
        "status": converted.get("status", "investigating"),
        "source": "review_approve_dev",
        "evidence_count": len(converted.get("evidence", [])),
    })
    save_json(CHANGELOG_PATH, changelog)

    # 从候选中移除
    save_json(source_path, remaining)

    print(f"\n  ✓ 已写入 {target_path.name}: {title}")
    print(f"  ✓ 已从 {source_path.name} 移除")
    print(f"  ✓ changelog 已更新")


if __name__ == "__main__":
    main()
