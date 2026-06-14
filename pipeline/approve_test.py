#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
approve_test.py — 闭环测试用审核脚本

程序化 approve 候选数据，模拟 review_candidates.py 的人工审核流程。
仅用于闭环测试，不替代正式的人工审核工具。
"""

import json
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))

from review_candidates import (
    load_json, save_json, now_iso, now_human,
    build_augment_rarity_map,
    convert_bug_to_issue, convert_syn_to_synergy,
    is_dup_issue, is_dup_synergy,
    run_validate, append_changelog,
    CANDIDATE_BUGS_PATH, CANDIDATE_SYNS_PATH,
    ISSUES_PATH, SYNERGIES_PATH, OUTPUT_DIR,
)

def approve_bug(candidate, issues, source_path, remaining):
    """Approve a single bug candidate."""
    title = candidate.get("title", "")
    if is_dup_issue(title, issues):
        print(f"  [跳过] 重复: {title}")
        return False

    converted = convert_bug_to_issue(candidate)
    backup = load_json(OUTPUT_DIR / "issues_backup.json")
    save_json(OUTPUT_DIR / "issues_backup.json", issues)
    issues.append(converted)
    save_json(ISSUES_PATH, issues)

    ok = run_validate()
    if not ok:
        print("  [回滚] 校验失败")
        restore = load_json(OUTPUT_DIR / "issues_backup.json")
        save_json(ISSUES_PATH, restore)
        return False

    print(f"  [通过] Bug: {title}")
    append_changelog(candidate, "bug_report")
    remaining.remove(candidate)
    save_json(source_path, remaining)
    return True


def approve_synergy(candidate, synergies, rar_map, source_path, remaining):
    """Approve a single synergy candidate."""
    hero = candidate.get("hero", "?")
    aug = candidate.get("augment", "?")

    preview = convert_syn_to_synergy(candidate, rar_map)
    tier = preview["tier"]

    if is_dup_synergy(hero, aug, tier, synergies):
        print(f"  [跳过] 重复: {hero} × {aug} [{tier}]")
        return False

    save_json(OUTPUT_DIR / "synergies_backup.json", synergies)
    synergies.append(preview)
    save_json(SYNERGIES_PATH, synergies)

    ok = run_validate()
    if not ok:
        print("  [回滚] 校验失败")
        restore = load_json(OUTPUT_DIR / "synergies_backup.json")
        save_json(SYNERGIES_PATH, restore)
        return False

    print(f"  [通过] Synergy: {hero} × {aug} [{tier}]")
    append_changelog(candidate, "synergy_claim")
    remaining.remove(candidate)
    save_json(source_path, remaining)
    return True


def main():
    print("=" * 60)
    print("  闭环测试 — 程序化审核")
    print("=" * 60)

    # Load candidates
    bugs = load_json(CANDIDATE_BUGS_PATH)
    syns = load_json(CANDIDATE_SYNS_PATH)
    rar_map = build_augment_rarity_map()

    print(f"  候选 Bug: {len(bugs)} 条")
    print(f"  候选 Synergy: {len(syns)} 条")
    print()

    approved_bugs = 0
    approved_syns = 0

    # --- Approve bugs with evidence ---
    issues = load_json(ISSUES_PATH)
    for bug in list(bugs):
        ev = bug.get("evidence", [])
        if not ev:
            print(f"  [跳过] 无 evidence: {bug.get('title', '?')}")
            continue
        print(f"  审核 Bug: {bug.get('title', '?')[:60]}...")
        if approve_bug(bug, issues, CANDIDATE_BUGS_PATH, bugs):
            approved_bugs += 1
            issues = load_json(ISSUES_PATH)  # reload after write

    # --- Approve synergies with evidence ---
    synergies = load_json(SYNERGIES_PATH)
    for syn in list(syns):
        ev = syn.get("evidence", [])
        if not ev:
            print(f"  [跳过] 无 evidence: {syn.get('hero', '?')} × {syn.get('augment', '?')}")
            continue
        print(f"  审核 Synergy: {syn.get('hero', '?')} × {syn.get('augment', '?')}...")
        if approve_synergy(syn, synergies, rar_map, CANDIDATE_SYNS_PATH, syns):
            approved_syns += 1
            synergies = load_json(SYNERGIES_PATH)  # reload after write

    print()
    print(f"  通过: {approved_bugs} Bug + {approved_syns} Synergy")
    print(f"  剩余: {len(bugs)} Bug + {len(syns)} Synergy")
    print("=" * 60)

    return 0 if (approved_bugs + approved_syns) > 0 else 1


if __name__ == "__main__":
    sys.exit(main())
