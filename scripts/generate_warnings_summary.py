#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate_warnings_summary.py — 统计 validate_data.py 的 warnings 并分类输出到
pipeline/output/warnings_summary.json

分类规则:
  - effect_missing:           augment effect 为空
  - patch_missing:            augment patch_added 为空
  - missing_zh:               augment localization_status = "missing_zh"
  - prototype_or_unknown:     augment source_status = "prototype" 或 status = "unknown"
  - missing_evidence:         synergy/report status=verified 但 evidence 为空
  - missing_source_url:       synergy src=data 且 sample>0 但 evidence 为空
  - sample_null:              synergy sample 为 null 或 0
  - other:                    其他
"""

import json
import subprocess
import sys
import re
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
VALIDATE_SCRIPT = PROJECT_ROOT / "scripts" / "validate_data.py"
OUTPUT_PATH = PROJECT_ROOT / "pipeline" / "output" / "warnings_summary.json"
DATA_DIR = PROJECT_ROOT / "data"

CATEGORIES = [
    "effect_missing",
    "patch_missing",
    "missing_zh",
    "prototype_or_unknown_augments",
    "missing_evidence",
    "missing_source_url",
    "sample_null",
    "other",
]


def classify_warning(msg: str) -> str:
    """根据警告文本分类。"""
    if "effect 为空" in msg:
        return "effect_missing"
    if "patch_added 为空" in msg:
        return "patch_missing"
    if "tier 为 unknown" in msg:
        return "prototype_or_unknown_augments"
    if "status 为 unknown" in msg:
        return "prototype_or_unknown_augments"
    if "aliases 为空" in msg:
        return "other"
    if "tags 为空" in msg:
        return "other"
    if "source.url 为空" in msg:
        return "other"
    if "status=verified 但 evidence 为空" in msg:
        return "missing_evidence"
    if "src=data" in msg and "evidence 为空" in msg:
        return "missing_source_url"
    return "other"


def run_validate_capture_warnings():
    """运行 validate_data.py 并捕获所有警告行。"""
    try:
        result = subprocess.run(
            [sys.executable, str(VALIDATE_SCRIPT)],
            capture_output=True, text=True, encoding="utf-8",
            errors="replace", timeout=30,
        )
        lines = result.stdout.splitlines()
        warning_lines = [l.strip() for l in lines if l.strip().startswith("⚠")]
        return warning_lines
    except Exception as e:
        print(f"  运行 validate_data.py 失败: {e}")
        return []


def enrich_with_data_warnings(warnings):
    """补充 validate_data.py 不直接输出但可从数据文件推断的警告。"""
    augments_path = DATA_DIR / "augments.json"
    if not augments_path.exists():
        return warnings

    with open(augments_path, "r", encoding="utf-8") as f:
        augments = json.load(f)

    extra = []
    for i, a in enumerate(augments):
        if not isinstance(a, dict):
            continue
        name = a.get("name", "?")
        # missing_zh
        if a.get("localization_status") == "missing_zh":
            extra.append(f"[augments.json] 第 {i+1} 条增强 '{name}' localization_status=missing_zh (中文名待翻译)")
        # prototype
        if a.get("source_status") == "prototype":
            extra.append(f"[augments.json] 第 {i+1} 条增强 '{name}' source_status=prototype (原型数据)")

    # synergies sample_null
    syns_path = DATA_DIR / "synergies.json"
    if syns_path.exists():
        with open(syns_path, "r", encoding="utf-8") as f:
            syns = json.load(f)
        for i, s in enumerate(syns):
            if not isinstance(s, dict):
                continue
            sample = s.get("sample")
            if sample is None or sample == 0:
                hero = s.get("hero", "?")
                aug = s.get("aug", "?")
                extra.append(f"[synergies.json] 第 {i+1} 条组合 {hero}×{aug} sample={sample}")

    return warnings + extra


def classify_enriched(msg):
    """分类增强后的警告（含额外推断）。"""
    if "localization_status=missing_zh" in msg:
        return "missing_zh"
    if "source_status=prototype" in msg:
        return "prototype_or_unknown_augments"
    if "sample=" in msg and ("sample=None" in msg or "sample=0" in msg):
        return "sample_null"
    return classify_warning(msg)


def main():
    print("=" * 60)
    print("  warnings_summary.py — 警告分类统计")
    print("=" * 60)

    # Step 1: 运行 validate_data.py 捕获原始警告
    raw_warnings = run_validate_capture_warnings()
    print(f"\n  validate_data.py 原始警告: {len(raw_warnings)} 条")

    # Step 2: 补充数据推断警告
    all_warnings = enrich_with_data_warnings(raw_warnings)
    print(f"  补充推断后总警告: {len(all_warnings)} 条")

    # Step 3: 分类
    classified = {cat: [] for cat in CATEGORIES}
    for w in all_warnings:
        cat = classify_enriched(w)
        classified[cat].append(w)

    # Step 4: 统计
    summary = {
        "total_warnings": len(all_warnings),
        "by_category": {},
        "generated_at": __import__("datetime").datetime.now().isoformat(),
    }

    print(f"\n  分类统计:")
    print(f"  {'分类':<35s}  {'数量':>5s}")
    print(f"  {'-'*42}")
    for cat in CATEGORIES:
        count = len(classified[cat])
        summary["by_category"][cat] = {
            "count": count,
            "examples": classified[cat][:3],  # 最多 3 条示例
        }
        print(f"  {cat:<35s}  {count:>5d}")

    print(f"\n  {'总计':<35s}  {len(all_warnings):>5d}")

    # Step 5: 写入
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print(f"\n  ✓ 已输出: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
