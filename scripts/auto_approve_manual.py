#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
auto_approve_manual.py — 非交互式审核：从 candidate_synergies.json 中 approve 1 条高质量候选。

Approve: Dashing + Ezreal (synergy_claim, transform) — 有 Reddit 帖子证据
Skip: Growth Spurt (trap_warning) — 来自评级文章，证据不够具体，留给后续审核
"""

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

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

CAND_SYNS_PATH = OUTPUT_DIR / "candidate_synergies.json"
SYNERGIES_PATH = DATA_DIR / "synergies.json"
CHANGELOG_PATH = DATA_DIR / "changelog.json"
VALIDATE_SCRIPT = PROJECT_ROOT / "scripts" / "validate_data.py"

# 导入 normalize_entities
sys.path.insert(0, str(PIPELINE_DIR))
from processors.normalize_entities import normalize_champion_name, normalize_augment_name


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


def main():
    print("=" * 60)
    print("  非交互式审核 — manual pipeline 候选")
    print("=" * 60)

    candidates = load_json(CAND_SYNS_PATH)
    if not candidates:
        print("  没有候选数据。")
        return

    print(f"\n  候选数量: {len(candidates)}\n")

    synergies = load_json(SYNERGIES_PATH)
    changelog = load_json(CHANGELOG_PATH)

    # 构建 augments.json 的 rar 映射
    augments = load_json(DATA_DIR / "augments.json")
    rar_map = {}
    for a in augments:
        if isinstance(a, dict) and "name" in a:
            rar_map[a["name"]] = a.get("rar", "unknown")

    approved = 0
    skipped = 0
    remaining = []

    for c in candidates:
        cid = c.get("candidate_id", "N/A")
        ctype = c.get("type", "unknown")
        hero = c.get("hero", "?")
        aug = c.get("augment", "?")
        rating = c.get("rating_type", "?")
        conf = c.get("confidence", 0)
        evidence = c.get("evidence", [])

        print(f"  候选: {cid}")
        print(f"    {ctype} | {hero} x {aug} | {rating} | conf={conf}")
        print(f"    evidence: {len(evidence)} 条")

        # 审核决策: approve Dashing synergy (有 Reddit 证据), skip Growth Spurt
        if aug == "Dashing" and hero in ("伊泽瑞尔", "Ezreal") and len(evidence) > 0:
            print("    => APPROVE (有 Reddit 帖子证据，社区反馈明确)")

            # 转换格式
            aug_name = normalize_augment_name(aug)
            hero_name = normalize_champion_name(hero)

            rar = rar_map.get(aug_name, "unknown")
            if rar not in {"silver", "gold", "prism", "unknown"}:
                rar = "unknown"

            tier = "transform" if rating == "transform" else "recommend"

            converted = {
                "hero": hero_name,
                "aug": aug_name,
                "rar": rar,
                "tier": tier,
                "delta": None,
                "conf": conf,
                "sample": None,
                "ver": c.get("patch", "unknown"),
                "src": "community",
                "status": "investigating",
                "desc": c.get("description", ""),
                "trigger": c.get("trigger", ""),
                "notes": [],
                "combos": [],
                "evidence": evidence,
                "updated_at": now_iso(),
                "source_note": "",
            }

            # 备份
            backup_path = OUTPUT_DIR / "synergies_backup.json"
            save_json(backup_path, synergies)

            synergies.append(converted)
            save_json(SYNERGIES_PATH, synergies)

            # 校验
            print("    运行 validate_data.py ...")
            try:
                result = subprocess.run(
                    [sys.executable, str(VALIDATE_SCRIPT)],
                    capture_output=True, text=True, encoding="utf-8",
                    errors="replace", timeout=30,
                )
                for line in result.stdout.splitlines():
                    print(f"      {line}")

                if result.returncode != 0:
                    print("    校验失败，回滚！")
                    restore = load_json(backup_path)
                    save_json(SYNERGIES_PATH, restore)
                    remaining.append(c)
                    skipped += 1
                    continue
                else:
                    print("    校验通过")
            except Exception as e:
                print(f"    校验异常: {e}，保留写入")

            # Changelog
            changelog.append({
                "date": now_iso(),
                "type": "synergy",
                "title": f"{hero_name} x {aug_name}",
                "hero": hero_name,
                "augment": aug_name,
                "status": "investigating",
                "source": "review_approve",
                "evidence_count": len(evidence),
            })
            save_json(CHANGELOG_PATH, changelog)

            print(f"    => 已写入 synergies.json: {hero_name} x {aug_name} [{tier}]")
            approved += 1

        else:
            print(f"    => SKIP (留给后续人工审核)")
            remaining.append(c)
            skipped += 1

        print()

    # 保存剩余候选
    save_json(CAND_SYNS_PATH, remaining)

    # 汇总
    print("=" * 60)
    print(f"  审核完成:")
    print(f"    总候选: {len(candidates)}")
    print(f"    Approved: {approved}")
    print(f"    Skipped:  {skipped}")
    print(f"    Rejected: 0")
    print(f"    剩余待审: {len(remaining)}")
    print("=" * 60)


if __name__ == "__main__":
    main()
