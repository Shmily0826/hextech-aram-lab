#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fix_data_p2.py -- P2 数据质量修复脚本

任务 1: 降级无证据的 verified 协同条目 (synergies.json)
任务 2: 合并重复的 bug 报告 (issues.json)

用法:
    python scripts/fix_data_p2.py
"""

import json
import shutil
import sys
import io
from pathlib import Path
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# Windows 终端 UTF-8 兼容 — 使用 io.TextIOWrapper
# ---------------------------------------------------------------------------
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(
        sys.stdout.buffer, encoding="utf-8", errors="replace"
    )
    sys.stderr = io.TextIOWrapper(
        sys.stderr.buffer, encoding="utf-8", errors="replace"
    )

# ---------------------------------------------------------------------------
# 路径配置
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
DATA_DIR = PROJECT_ROOT / "data"
BACKUP_DIR = PROJECT_ROOT / "pipeline" / "output"

SYNERGIES_PATH = DATA_DIR / "synergies.json"
ISSUES_PATH = DATA_DIR / "issues.json"


def load_json(path: Path) -> list:
    """读取 JSON 文件。"""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data: list) -> None:
    """写回 JSON 文件 (UTF-8, 保留中文)。"""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def backup_file(src: Path) -> Path:
    """将文件备份到 pipeline/output/ 并加时间戳后缀。"""
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = BACKUP_DIR / f"{src.stem}_p2_backup_{ts}{src.suffix}"
    shutil.copy2(src, dest)
    print(f"  [备份] {src.name} -> {dest.relative_to(PROJECT_ROOT)}")
    return dest


# ===========================================================================
# 任务 1: 降级无证据的 verified 协同条目
# ===========================================================================
def fix_synergies() -> int:
    """
    对 synergies.json 中 status=verified 但 evidence 为空的条目执行降级:
      - status -> "investigating"
      - conf 若 > 60 则 cap 到 60
      - 添加 downgraded_reason
    返回被降级的条目数量。
    """
    print("\n" + "=" * 56)
    print("  任务 1: 降级无证据的 verified 协同条目")
    print("=" * 56)

    synergies = load_json(SYNERGIES_PATH)
    downgraded = 0

    for i, entry in enumerate(synergies):
        if entry.get("status") != "verified":
            continue

        evidence = entry.get("evidence")
        # 检查 evidence 是否为空数组或不包含有效条目
        has_valid_evidence = False
        if isinstance(evidence, list) and len(evidence) > 0:
            for ev in evidence:
                if isinstance(ev, dict) and ev:  # 非空 dict
                    has_valid_evidence = True
                    break

        if has_valid_evidence:
            continue

        # 执行降级
        hero = entry.get("hero", "?")
        aug = entry.get("aug", "?")
        old_conf = entry.get("conf", 0)

        entry["status"] = "investigating"
        if old_conf > 60:
            entry["conf"] = 60
        entry["downgraded_reason"] = "无外部证据支撑，从 verified 降级为 investigating"

        conf_msg = f", conf: {old_conf} -> 60" if old_conf > 60 else ""
        print(f"  [降级] #{i + 1} {hero}+{aug}{conf_msg}")
        downgraded += 1

    print(f"\n  共降级 {downgraded} 条协同条目")
    save_json(SYNERGIES_PATH, synergies)
    print(f"  [写入] {SYNERGIES_PATH}")
    return downgraded


# ===========================================================================
# 任务 2: 合并重复的 bug 报告
# ===========================================================================
def merge_evidence(target: list, source: list) -> int:
    """将 source 中的 evidence 条目合并到 target, 返回新增数量。"""
    added = 0
    existing_urls = set()
    for ev in target:
        if isinstance(ev, dict) and "url" in ev:
            existing_urls.add(ev["url"])

    for ev in source:
        if isinstance(ev, dict):
            url = ev.get("url", "")
            if url and url not in existing_urls:
                target.append(ev)
                existing_urls.add(url)
                added += 1
            elif not url:
                # 没有 url 的 evidence 也合并（如果没有完全相同的）
                if ev not in target:
                    target.append(ev)
                    added += 1
    return added


def merge_desc_tip(target: dict, source: dict) -> list[str]:
    """
    将 source 的 desc/tip 中的额外信息合并到 target。
    返回变更描述列表。
    """
    changes = []

    # 合并 desc: 如果 source 有 target 没有的额外信息
    src_desc = source.get("desc", "")
    tgt_desc = target.get("desc", "")
    if src_desc and src_desc != tgt_desc:
        # 在 target 的 desc 后追加 source 的补充信息
        if tgt_desc:
            target["desc"] = tgt_desc + " | EN补充: " + src_desc
        else:
            target["desc"] = src_desc
        changes.append("desc 已合并英文版本补充信息")

    # 合并 tip: 如果 source 有 tip 而 target 没有
    src_tip = source.get("tip", "")
    tgt_tip = target.get("tip", "")
    if src_tip and not tgt_tip:
        target["tip"] = src_tip
        changes.append("tip 已从英文版本补充")
    elif src_tip and tgt_tip and src_tip != tgt_tip:
        target["tip"] = tgt_tip + " | EN: " + src_tip
        changes.append("tip 已合并英文版本补充信息")

    # 合并 confidence: 取较高值
    src_conf = source.get("confidence", 0)
    tgt_conf = target.get("confidence", 0)
    if src_conf > tgt_conf:
        target["confidence"] = src_conf
        changes.append(f"confidence: {tgt_conf} -> {src_conf}")

    # 合并 confirm: 累加
    src_confirm = source.get("confirm", 0)
    tgt_confirm = target.get("confirm", 0)
    if src_confirm > 0:
        target["confirm"] = tgt_confirm + src_confirm
        changes.append(f"confirm: {tgt_confirm} -> {tgt_confirm + src_confirm}")

    return changes


def fix_issues() -> int:
    """
    合并 issues.json 中的重复 bug 报告:
      - Pair 1: #1 (布兰德-毒性增幅) 和 #7 (Brand+Toxic Amplifier)
      - Pair 2: #3 (提莫-R蘑菇) 和 #8 (Teemo mushroom)
    返回移除的重复条目数。
    """
    print("\n" + "=" * 56)
    print("  任务 2: 合并重复的 bug 报告")
    print("=" * 56)

    issues = load_json(ISSUES_PATH)

    # 定义重复对: (保留的标题关键词, 删除的标题关键词)
    duplicate_pairs = [
        {
            "keep_title": "布兰德 - 毒性增幅叠加计算异常",
            "remove_title": "Brand + Toxic Amplifier damage calculation",
            "label": "布兰德-毒性增幅 / Brand+Toxic Amplifier",
        },
        {
            "keep_title": "提莫 - R蘑菇不触发连锁闪电增强",
            "remove_title": "Teemo mushroom traps do not trigger Chain Lightning",
            "label": "提莫-R蘑菇 / Teemo mushroom",
        },
    ]

    removed_count = 0
    # 从高索引到低索引处理，避免删除后索引偏移问题
    # 先找到所有需要处理的索引
    operations = []
    for pair in duplicate_pairs:
        keep_idx = None
        remove_idx = None
        for i, iss in enumerate(issues):
            title = iss.get("title", "")
            if pair["keep_title"] in title:
                keep_idx = i
            if pair["remove_title"] in title:
                remove_idx = i

        if keep_idx is not None and remove_idx is not None:
            operations.append((pair, keep_idx, remove_idx))
        else:
            print(f"  [警告] 未找到重复对: {pair['label']}")
            if keep_idx is None:
                print(f"    缺少保留条目: {pair['keep_title']}")
            if remove_idx is None:
                print(f"    缺少删除条目: {pair['remove_title']}")

    # 处理每对重复 (先处理高索引的删除，避免偏移)
    operations.sort(key=lambda x: x[2], reverse=True)

    for pair, keep_idx, remove_idx in operations:
        print(f"\n  --- {pair['label']} ---")
        keep_entry = issues[keep_idx]
        remove_entry = issues[remove_idx]

        # 合并 evidence
        ev_added = merge_evidence(
            keep_entry.setdefault("evidence", []),
            remove_entry.get("evidence", []),
        )
        print(f"  [合并] evidence: 新增 {ev_added} 条")

        # 合并 desc/tip 等字段
        changes = merge_desc_tip(keep_entry, remove_entry)
        for c in changes:
            print(f"  [合并] {c}")

        # 记录合并来源
        keep_entry["merged_from"] = remove_entry.get("title", "")

        print(f"  [保留] #{keep_idx + 1} \"{keep_entry['title']}\"")
        print(f"  [删除] #{remove_idx + 1} \"{remove_entry['title']}\"")

        # 移除英文重复条目
        issues.pop(remove_idx)
        removed_count += 1

    print(f"\n  共移除 {removed_count} 条重复报告")
    save_json(ISSUES_PATH, issues)
    print(f"  [写入] {ISSUES_PATH}")
    return removed_count


# ===========================================================================
# 运行 validate_data.py
# ===========================================================================
def run_validation() -> int:
    """运行 validate_data.py 校验脚本。"""
    import subprocess

    print("\n" + "=" * 56)
    print("  运行数据校验 (validate_data.py)")
    print("=" * 56)

    validate_script = SCRIPT_DIR / "validate_data.py"
    if not validate_script.exists():
        print(f"  [错误] 未找到校验脚本: {validate_script}")
        return 1

    result = subprocess.run(
        [sys.executable, str(validate_script)],
        cwd=str(PROJECT_ROOT),
        capture_output=False,
    )
    return result.returncode


# ===========================================================================
# 主流程
# ===========================================================================
def main() -> int:
    print("=" * 56)
    print("  P2 数据质量修复脚本")
    print(f"  项目目录: {PROJECT_ROOT}")
    print(f"  执行时间: {datetime.now().isoformat()}")
    print("=" * 56)

    # 步骤 1: 备份
    print("\n[步骤 1] 备份原始数据文件...")
    backup_file(SYNERGIES_PATH)
    backup_file(ISSUES_PATH)

    # 步骤 2: 修复 synergies.json
    print("\n[步骤 2] 修复 synergies.json ...")
    downgraded = fix_synergies()

    # 步骤 3: 修复 issues.json
    print("\n[步骤 3] 修复 issues.json ...")
    removed = fix_issues()

    # 步骤 4: 运行校验
    print("\n[步骤 4] 运行数据校验 ...")
    val_rc = run_validation()

    # 汇总
    print("\n" + "=" * 56)
    print("  执行汇总")
    print("=" * 56)
    print(f"  synergies.json: 降级 {downgraded} 条无证据 verified 条目")
    print(f"  issues.json:    移除 {removed} 条重复报告")
    print(f"  validate_data:  {'通过' if val_rc == 0 else '未通过 (有错误或警告)'}")
    print("=" * 56)

    return 0


if __name__ == "__main__":
    sys.exit(main())
