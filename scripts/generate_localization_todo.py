#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate_localization_todo.py — 根据 augments.json 中 localization_status="missing_zh"
的增强，输出 pipeline/output/augment_localization_todo.csv。

字段: id, name_en, current_name, tier, effect_en, source_url, suggested_zh, verified_zh, notes

注意:
  - suggested_zh 可以为空（不自动 AI 翻译）
  - verified_zh 必须人工确认后才能合并
  - 不要把 AI 翻译自动写入正式 name
"""

import csv
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

DATA_DIR = Path(r"D:\CODE\project\aram-insight\data")
OUTPUT_PATH = Path(r"D:\CODE\project\aram-insight\pipeline\output\augment_localization_todo.csv")


def main():
    print("=" * 60)
    print("  augment_localization_todo 生成器")
    print("=" * 60)

    with open(DATA_DIR / "augments.json", "r", encoding="utf-8") as f:
        augments = json.load(f)

    missing = [a for a in augments if a.get("localization_status") == "missing_zh"]
    print(f"\n  missing_zh 增强数: {len(missing)}")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    fields = [
        "id", "name_en", "current_name", "tier",
        "effect_en", "source_url", "suggested_zh", "verified_zh", "notes",
    ]

    with open(OUTPUT_PATH, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for a in missing:
            source = a.get("source", {}) or {}
            row = {
                "id": a.get("id", ""),
                "name_en": a.get("name_en", ""),
                "current_name": a.get("name", ""),
                "tier": a.get("tier", ""),
                "effect_en": a.get("effect_en", ""),
                "source_url": source.get("url", ""),
                "suggested_zh": "",  # 不自动翻译
                "verified_zh": "",   # 人工确认
                "notes": a.get("notes", ""),
            }
            writer.writerow(row)

    print(f"  ✓ 已输出: {OUTPUT_PATH}")
    print(f"  ✓ 共 {len(missing)} 条待翻译")

    # 展示前几条
    print(f"\n  前 5 条预览:")
    for a in missing[:5]:
        print(f"    {a.get('id',''):25s}  {a.get('name_en',''):30s}  {a.get('tier','')}")


if __name__ == "__main__":
    main()
