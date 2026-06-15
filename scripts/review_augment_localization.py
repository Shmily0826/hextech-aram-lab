#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
review_augment_localization.py — 交互式审核 augment 中文本地化的 CLI 工具

功能说明：
  - 逐条审核 pipeline/output/augment_wiki_quality_todo.json 中的本地化建议
  - 支持 approve / edit / skip / reject / quit 五种操作
  - 每次 approve/edit 前备份 data/augments.json，写入后运行校验
  - 校验失败自动回滚
  - 审核结果写回 todo JSON 并追加 changelog

用法：
    python scripts/review_augment_localization.py
    python scripts/review_augment_localization.py --dry-run
    python scripts/review_augment_localization.py --id adamant
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
        "review_augment_localization.py 仅限独立 CLI 运行，不允许被 import。"
    )

# Windows UTF-8
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

# ---------------------------------------------------------------------------
# 路径常量
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "pipeline" / "output"

TODO_PATH = OUTPUT_DIR / "augment_wiki_quality_todo.json"
AUGMENTS_PATH = DATA_DIR / "augments.json"
BACKUP_PATH = OUTPUT_DIR / "augments_backup.json"
CHANGELOG_PATH = DATA_DIR / "changelog.json"
VALIDATE_SCRIPT = SCRIPT_DIR / "validate_data.py"
NORMALIZE_SCRIPT = PROJECT_ROOT / "pipeline" / "processors" / "normalize_entities.py"


# ---------------------------------------------------------------------------
# 工具函数
# ---------------------------------------------------------------------------
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


def truncate(text, maxlen=80):
    if not text:
        return "(empty)"
    if len(text) > maxlen:
        return text[:maxlen] + "..."
    return text


def display_entry(idx, total, entry, db_entry):
    """展示单条本地化审核信息。"""
    sep = "-" * 48
    aug_id = entry.get("id", "unknown")
    name_en = entry.get("name_en", "")
    tier = entry.get("tier", "")
    effect_en = entry.get("effect_en", "")

    sug_name = entry.get("suggested_zh_name", "")
    sug_effect = entry.get("suggested_effect_zh", "")
    source_url = entry.get("source_url", "")
    confidence = entry.get("confidence", "")

    cur_name = db_entry.get("name", "") if db_entry else ""
    cur_effect = db_entry.get("effect", "") if db_entry else ""

    print(f"\n[{idx}/{total}] id: {aug_id}")
    print(sep)
    print(f"  English name : {name_en}")
    print(f"  Tier         : {tier}")
    print(f"  Effect (EN)  : {truncate(effect_en)}")
    print(sep)
    print(f"  Suggested CN name   : {sug_name}")
    print(f"  Suggested CN effect : {truncate(sug_effect)}")
    print(f"  Source URL          : {source_url}")
    print(f"  Confidence          : {confidence}")
    print(sep)

    cur_name_display = cur_name if cur_name else "(empty)"
    cur_effect_display = cur_effect if cur_effect else "(empty)"
    print(f"  Current in DB: name=\"{cur_name_display}\", effect=\"{cur_effect_display}\"")

    print(sep)
    print("  DIFF:")
    old_name = cur_name if cur_name else "(empty)"
    new_name = sug_name if sug_name else "(none)"
    old_effect = cur_effect if cur_effect else "(empty)"
    new_effect = sug_effect if sug_effect else "(none)"
    print(f"    name:   \"{old_name}\" -> \"{new_name}\"")
    print(f"    effect: \"{truncate(old_effect, 50)}\" -> \"{truncate(new_effect, 50)}\"")
    print()


def find_db_entry(augments, aug_id):
    """在 augments.json 中查找对应 id 的条目。"""
    for a in augments:
        if isinstance(a, dict) and a.get("id") == aug_id:
            return a
    return None


def run_validate():
    """运行 validate_data.py，返回是否通过。"""
    print("\n  > Running validation (validate_data.py)...")
    try:
        result = subprocess.run(
            [sys.executable, str(VALIDATE_SCRIPT)],
            capture_output=True, text=True, encoding="utf-8",
            errors="replace", timeout=30,
        )
        for line in result.stdout.splitlines():
            print(f"    {line}")
        if result.returncode == 0:
            print("  [OK] Validation passed.\n")
            return True
        else:
            if result.stderr:
                for line in result.stderr.splitlines():
                    print(f"    [ERR] {line}")
            print("  [FAIL] Validation failed.\n")
            return False
    except FileNotFoundError:
        print(f"  [WARN] Validation script not found: {VALIDATE_SCRIPT}")
        print("  [WARN] Skipping validation (script missing).\n")
        return True
    except subprocess.TimeoutExpired:
        print("  [WARN] Validation timed out (30s).\n")
        return False
    except Exception as e:
        print(f"  [WARN] Validation exception: {e}\n")
        return False


def run_normalize_test():
    """运行 normalize_entities.py 测试，返回是否通过。"""
    print("  > Running normalize test (normalize_entities.py)...")
    try:
        result = subprocess.run(
            [sys.executable, str(NORMALIZE_SCRIPT), "--test"],
            capture_output=True, text=True, encoding="utf-8",
            errors="replace", timeout=30,
        )
        for line in result.stdout.splitlines():
            print(f"    {line}")
        if result.returncode == 0:
            print("  [OK] Normalize test passed.\n")
            return True
        else:
            if result.stderr:
                for line in result.stderr.splitlines():
                    print(f"    [ERR] {line}")
            print("  [FAIL] Normalize test failed.\n")
            return False
    except FileNotFoundError:
        print(f"  [WARN] Normalize script not found: {NORMALIZE_SCRIPT}")
        print("  [WARN] Skipping normalize test (script missing).\n")
        return True
    except subprocess.TimeoutExpired:
        print("  [WARN] Normalize test timed out (30s).\n")
        return False
    except Exception as e:
        print(f"  [WARN] Normalize test exception: {e}\n")
        return False


def apply_localization(augments, aug_id, zh_name, zh_effect):
    """
    在 augments 列表中更新指定 id 的条目：
      - name = zh_name
      - effect = zh_effect
      - desc = zh_effect (sync)
      - 移除 localization_status 或设为 "localized"
      - name_en 保持不变
    返回更新后的 augments 列表和是否找到。
    """
    found = False
    for a in augments:
        if isinstance(a, dict) and a.get("id") == aug_id:
            a["name"] = zh_name
            a["effect"] = zh_effect
            a["desc"] = zh_effect
            if "localization_status" in a:
                a["localization_status"] = "localized"
            found = True
            break
    return augments, found


def write_changelog(aug_id, zh_name, action_type):
    """追加一条 changelog 记录。"""
    changelog = load_json(CHANGELOG_PATH)
    changelog.append({
        "date": now_iso(),
        "type": "augment_localization",
        "title": f"Localization: {aug_id} -> {zh_name}",
        "augment": aug_id,
        "action": action_type,
        "source": "review_augment_localization",
    })
    save_json(CHANGELOG_PATH, changelog)


def mark_reviewed(todo_list, aug_id, action):
    """在 todo 列表中标记条目已审核。"""
    for entry in todo_list:
        if entry.get("id") == aug_id:
            entry["needs_human_review"] = False
            entry["reviewed_at"] = now_iso()
            entry["review_action"] = action
            break
    return todo_list


def prompt_action():
    """提示用户输入操作。"""
    try:
        raw = input("  Action: [a]pprove / [e]dit / [s]kip / [r]eject / [q]uit > ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        print("\n  Quitting (input interrupted).")
        return "q"
    if raw in ("a", "approve"):
        return "a"
    elif raw in ("e", "edit"):
        return "e"
    elif raw in ("s", "skip"):
        return "s"
    elif raw in ("r", "reject"):
        return "r"
    elif raw in ("q", "quit"):
        return "q"
    else:
        print(f"  Unknown action: '{raw}'. Please enter a/e/s/r/q.")
        return prompt_action()


def prompt_edit(default_name, default_effect):
    """编辑模式：提示用户输入自定义中文名和效果描述。"""
    print(f"\n  Current suggested CN name  : {default_name}")
    try:
        new_name = input(f"  Enter new CN name (press Enter to keep \"{default_name}\"): ").strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return None, None
    if not new_name:
        new_name = default_name

    print(f"  Current suggested CN effect: {truncate(default_effect)}")
    try:
        new_effect = input(f"  Enter new CN effect (press Enter to keep suggested): ").strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return None, None
    if not new_effect:
        new_effect = default_effect

    return new_name, new_effect


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="Interactive CLI for reviewing augment Chinese localization.",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Show all entries and what would happen without writing anything.",
    )
    parser.add_argument(
        "--id", dest="target_id", default=None,
        help="Only review a specific augment by id.",
    )
    args = parser.parse_args()

    print("=" * 56)
    print("  review_augment_localization.py")
    print("  Augment Chinese Localization Review Tool")
    print("=" * 56)
    print(f"  TODO file   : {TODO_PATH.name}")
    print(f"  Target DB   : {AUGMENTS_PATH.name}")
    print(f"  Dry Run     : {'Yes' if args.dry_run else 'No'}")
    if args.target_id:
        print(f"  Target ID   : {args.target_id}")

    # Load data
    todo_list = load_json(TODO_PATH)
    if not todo_list:
        print("\n  [ERROR] TODO file is empty or not found.")
        sys.exit(1)

    augments = load_json(AUGMENTS_PATH)
    if not augments:
        print("\n  [ERROR] Augments DB is empty or not found.")
        sys.exit(1)

    # Filter entries needing review
    review_entries = [e for e in todo_list if e.get("needs_human_review", False)]

    # If --id filter is specified, narrow down
    if args.target_id:
        review_entries = [e for e in review_entries if e.get("id") == args.target_id]
        if not review_entries:
            print(f"\n  [ERROR] No entry with id='{args.target_id}' needing review.")
            sys.exit(1)

    total = len(review_entries)
    print(f"  Entries to review: {total}")
    print()

    # Counters
    stats = {"approved": 0, "edited": 0, "skipped": 0, "rejected": 0}

    if args.dry_run:
        # --dry-run: show all entries without interaction
        print("[DRY RUN MODE] Displaying all entries — no writes will occur.\n")
        for idx, entry in enumerate(review_entries, 1):
            aug_id = entry.get("id", "unknown")
            db_entry = find_db_entry(augments, aug_id)
            display_entry(idx, total, entry, db_entry)
            sug_name = entry.get("suggested_zh_name", "")
            sug_effect = entry.get("suggested_effect_zh", "")
            print(f"  [DRY RUN] Would prompt for: approve / edit / skip / reject")
            print(f"  [DRY RUN] approve would set: name=\"{sug_name}\", effect=\"{truncate(sug_effect, 60)}\"")
            print()
        print(f"[DRY RUN MODE] Done. {total} entries displayed. No data was modified.")
        sys.exit(0)

    # Interactive review loop
    for idx, entry in enumerate(review_entries, 1):
        aug_id = entry.get("id", "unknown")
        db_entry = find_db_entry(augments, aug_id)

        display_entry(idx, total, entry, db_entry)

        action = prompt_action()

        if action == "q":
            print("\n  Quitting review session.")
            break

        elif action == "s":
            print(f"  Skipped: {aug_id}")
            stats["skipped"] += 1
            continue

        elif action == "r":
            print(f"  Rejected: {aug_id}")
            todo_list = mark_reviewed(todo_list, aug_id, "rejected")
            save_json(TODO_PATH, todo_list)
            stats["rejected"] += 1
            continue

        elif action == "a":
            zh_name = entry.get("suggested_zh_name", "")
            zh_effect = entry.get("suggested_effect_zh", "")

            # Confirm diff
            print(f"\n  Will apply:")
            print(f"    name   -> \"{zh_name}\"")
            print(f"    effect -> \"{truncate(zh_effect)}\"")
            print(f"    desc   -> (synced with effect)")

            # Backup
            print(f"\n  Backing up {AUGMENTS_PATH.name} -> {BACKUP_PATH.name}")
            save_json(BACKUP_PATH, augments)

            # Apply changes
            augments, found = apply_localization(augments, aug_id, zh_name, zh_effect)
            if not found:
                print(f"  [WARN] Augment id='{aug_id}' not found in DB. Skipping.")
                continue
            save_json(AUGMENTS_PATH, augments)

            # Validate
            ok = run_validate()
            if not ok:
                print("  [ROLLBACK] Validation failed! Restoring from backup...")
                augments = load_json(BACKUP_PATH)
                save_json(AUGMENTS_PATH, augments)
                print("  [ROLLBACK] Done. Entry not marked as reviewed.")
                continue

            # Normalize test
            ok = run_normalize_test()
            if not ok:
                print("  [ROLLBACK] Normalize test failed! Restoring from backup...")
                augments = load_json(BACKUP_PATH)
                save_json(AUGMENTS_PATH, augments)
                print("  [ROLLBACK] Done. Entry not marked as reviewed.")
                continue

            # Write changelog
            write_changelog(aug_id, zh_name, "approved")

            # Mark reviewed
            todo_list = mark_reviewed(todo_list, aug_id, "approved")
            save_json(TODO_PATH, todo_list)

            print(f"  [OK] Approved: {aug_id} -> \"{zh_name}\"")
            stats["approved"] += 1

        elif action == "e":
            default_name = entry.get("suggested_zh_name", "")
            default_effect = entry.get("suggested_effect_zh", "")

            zh_name, zh_effect = prompt_edit(default_name, default_effect)
            if zh_name is None:
                print("  Edit cancelled. Moving to next entry.")
                continue

            # Show final diff
            print(f"\n  Will apply (edited):")
            print(f"    name   -> \"{zh_name}\"")
            print(f"    effect -> \"{truncate(zh_effect)}\"")

            # Backup
            print(f"\n  Backing up {AUGMENTS_PATH.name} -> {BACKUP_PATH.name}")
            save_json(BACKUP_PATH, augments)

            # Apply changes
            augments, found = apply_localization(augments, aug_id, zh_name, zh_effect)
            if not found:
                print(f"  [WARN] Augment id='{aug_id}' not found in DB. Skipping.")
                continue
            save_json(AUGMENTS_PATH, augments)

            # Validate
            ok = run_validate()
            if not ok:
                print("  [ROLLBACK] Validation failed! Restoring from backup...")
                augments = load_json(BACKUP_PATH)
                save_json(AUGMENTS_PATH, augments)
                print("  [ROLLBACK] Done. Entry not marked as reviewed.")
                continue

            # Normalize test
            ok = run_normalize_test()
            if not ok:
                print("  [ROLLBACK] Normalize test failed! Restoring from backup...")
                augments = load_json(BACKUP_PATH)
                save_json(AUGMENTS_PATH, augments)
                print("  [ROLLBACK] Done. Entry not marked as reviewed.")
                continue

            # Write changelog
            write_changelog(aug_id, zh_name, "edited")

            # Mark reviewed
            todo_list = mark_reviewed(todo_list, aug_id, "edited")
            save_json(TODO_PATH, todo_list)

            print(f"  [OK] Edited & approved: {aug_id} -> \"{zh_name}\"")
            stats["edited"] += 1

    # Summary
    shown = stats["approved"] + stats["edited"] + stats["skipped"] + stats["rejected"]
    print()
    print("=" * 56)
    print("  REVIEW SUMMARY")
    print("=" * 56)
    print(f"  Total entries shown : {shown}")
    print(f"  Approved            : {stats['approved']}")
    print(f"  Edited              : {stats['edited']}")
    print(f"  Skipped             : {stats['skipped']}")
    print(f"  Rejected            : {stats['rejected']}")
    print("=" * 56)


if __name__ == "__main__":
    main()
