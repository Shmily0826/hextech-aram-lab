#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
review_candidates.py — AI 候选数据人工审核工具

逐条审核 pipeline/output/ 下 AI 提取的候选 Bug 和组合数据，
审核通过后写入正式 data/issues.json 或 data/synergies.json，
并自动运行 validate_data.py 校验。

用法：
    python pipeline/review_candidates.py
    python pipeline/review_candidates.py --type bugs       # 只审核 bug 候选
    python pipeline/review_candidates.py --type synergies  # 只审核组合候选
"""

import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

# 导入实体名称标准化模块
try:
    from processors.normalize_entities import (
        normalize_champion_name, normalize_champion_list,
        normalize_augment_name, normalize_augment_list,
    )
except ImportError:
    # 如果从项目根目录运行，尝试备用路径
    _pipe_dir = Path(__file__).resolve().parent
    if str(_pipe_dir) not in sys.path:
        sys.path.insert(0, str(_pipe_dir))
    from processors.normalize_entities import (
        normalize_champion_name, normalize_champion_list,
        normalize_augment_name, normalize_augment_list,
    )

# ---------------------------------------------------------------------------
# Windows 终端 UTF-8 兼容
# ---------------------------------------------------------------------------
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

# ---------------------------------------------------------------------------
# 路径配置
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
OUTPUT_DIR = SCRIPT_DIR / "output"
DATA_DIR = PROJECT_ROOT / "data"

CANDIDATE_BUGS_PATH = OUTPUT_DIR / "candidate_bugs.json"
CANDIDATE_SYNS_PATH = OUTPUT_DIR / "candidate_synergies.json"
REJECTED_PATH = OUTPUT_DIR / "rejected_candidates.json"

ISSUES_PATH = DATA_DIR / "issues.json"
SYNERGIES_PATH = DATA_DIR / "synergies.json"
AUGMENTS_PATH = DATA_DIR / "augments.json"
CHANGELOG_PATH = DATA_DIR / "changelog.json"
VALIDATE_SCRIPT = PROJECT_ROOT / "scripts" / "validate_data.py"

# ---------------------------------------------------------------------------
# IO 工具
# ---------------------------------------------------------------------------

def load_json(path: Path) -> list:
    """加载 JSON 文件。不存在或为空时返回空列表。"""
    if not path.exists():
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            return []
    except (json.JSONDecodeError, Exception):
        return []


def save_json(path: Path, data: list) -> None:
    """保存 JSON 文件（带缩进，UTF-8）。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def now_iso() -> str:
    """返回当前 UTC 时间的 ISO-8601 字符串。"""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def now_human() -> str:
    """返回当前日期的人类可读字符串（中文）。"""
    return datetime.now().strftime("%Y-%m-%d")


# ---------------------------------------------------------------------------
# 增强稀有度查找（从 augments.json 中按名称匹配）
# ---------------------------------------------------------------------------

def build_augment_rarity_map() -> dict[str, str]:
    """从 augments.json 构建 {增强名: rar} 映射表。"""
    augments = load_json(AUGMENTS_PATH)
    return {a["name"]: a["rar"] for a in augments if isinstance(a, dict) and "name" in a and "rar" in a}


# ---------------------------------------------------------------------------
# 候选展示
# ---------------------------------------------------------------------------

def display_candidate(c: dict, index: int, total: int, cand_type: str) -> None:
    """在终端中展示一条候选数据的详细信息。"""
    sep = "=" * 64
    thin = "-" * 64
    print(f"\n{sep}")
    print(f"  候选 [{index + 1} / {total}]  ({cand_type})")
    print(sep)

    cid = c.get("candidate_id", c.get("id", "N/A"))
    ctype = c.get("type", cand_type)
    confidence = c.get("confidence", "N/A")
    status = c.get("status", "N/A")
    created_at = c.get("created_at", "N/A")
    evidence = c.get("evidence", [])

    # Bug 类候选
    if cand_type == "bug_report":
        title = c.get("title", "无标题")
        heroes = c.get("champions", c.get("heroes", []))
        augs = c.get("augments", c.get("augs", []))
        desc = c.get("description", c.get("desc", ""))
        trigger = c.get("trigger", "")
        severity = c.get("severity", c.get("sev", "N/A"))

        print(f"  ID          : {cid}")
        print(f"  类型        : {ctype}")
        print(f"  标题        : {title}")
        print(f"  严重度      : {severity}")
        print(f"  涉及英雄    : {', '.join(heroes) if heroes else '无'}")
        print(f"  涉及增强    : {', '.join(augs) if augs else '无'}")
        print(f"  描述        : {desc}")
        if trigger:
            print(f"  触发条件    : {trigger}")
        print(f"  置信度      : {confidence}%")
        print(f"  状态        : {status}")
        print(f"  补丁版本    : {c.get('patch', c.get('ver', 'N/A'))}")
        print(f"  创建时间    : {created_at}")

    # 组合类候选
    else:
        hero = c.get("hero", "?")
        aug = c.get("augment", c.get("aug", "?"))
        rating = c.get("rating_type", c.get("tier", "N/A"))
        desc = c.get("description", c.get("desc", ""))
        trigger = c.get("trigger", "")

        print(f"  ID          : {cid}")
        print(f"  类型        : {ctype}")
        print(f"  英雄 × 增强 : {hero} × {aug}")
        print(f"  评级        : {rating}")
        print(f"  描述        : {desc}")
        if trigger:
            print(f"  触发条件    : {trigger}")
        print(f"  置信度      : {confidence}%")
        print(f"  状态        : {status}")
        print(f"  补丁版本    : {c.get('patch', c.get('ver', 'N/A'))}")
        print(f"  创建时间    : {created_at}")

    # 通用：证据
    if evidence and len(evidence) > 0:
        print(thin)
        print("  证据链接:")
        for ev in evidence:
            if isinstance(ev, dict):
                url = ev.get("url", "")
                label = ev.get("type", ev.get("source", ""))
                summary = ev.get("summary", "")
                print(f"    - [{label}] {url}")
                if summary:
                    print(f"      摘要: {summary}")
            elif isinstance(ev, str):
                print(f"    - {ev}")
    else:
        print("  证据链接    : (无)")

    print(thin)
    needs = c.get("needs_review", True)
    print(f"  待审核      : {'是' if needs else '否'}")
    print()


# ---------------------------------------------------------------------------
# 去重检查
# ---------------------------------------------------------------------------

def is_dup_issue(title: str, issues: list) -> bool:
    """issues.json 中是否已有相同 title。"""
    return any(i.get("title") == title for i in issues if isinstance(i, dict))


def is_dup_synergy(hero: str, aug: str, tier: str, synergies: list) -> bool:
    """synergies.json 中是否已有相同 hero + aug + tier。"""
    return any(
        s.get("hero") == hero and s.get("aug") == aug and s.get("tier") == tier
        for s in synergies if isinstance(s, dict)
    )


# ---------------------------------------------------------------------------
# 字段转换
# ---------------------------------------------------------------------------

def convert_bug_to_issue(c: dict) -> dict:
    """将 candidate_bugs 条目转换为 issues.json 格式。"""
    severity = c.get("severity", "minor")
    if severity not in {"minor", "major", "critical"}:
        severity = "minor"

    ver = c.get("patch", c.get("ver", "unknown"))
    if not ver or ver.lower() == "unknown":
        ver = "unknown"

    evidence = c.get("evidence", [])
    if not isinstance(evidence, list):
        evidence = []

    # source_note 优先级: _force_source_note > 默认逻辑
    if c.get("_force_source_note"):
        source_note = c["_force_source_note"]
    elif not evidence:
        source_note = "该条目来自 AI 候选提取，尚无充分证据，需继续验证。"
    else:
        source_note = ""

    # 标准化英雄名称（英 → 中）
    raw_heroes = c.get("champions", c.get("heroes", []))
    if isinstance(raw_heroes, list):
        normalized_heroes = normalize_champion_list(raw_heroes)
    else:
        normalized_heroes = [normalize_champion_name(str(raw_heroes))]

    # 标准化增强名称（英 → 中）
    raw_augs = c.get("augments", c.get("augs", []))
    if isinstance(raw_augs, list):
        normalized_augs = normalize_augment_list(raw_augs)
    else:
        normalized_augs = [normalize_augment_name(str(raw_augs))]

    return {
        "sev": severity,
        "title": c.get("title", "未知问题"),
        "heroes": normalized_heroes,
        "augs": normalized_augs,
        "desc": c.get("description", c.get("desc", "")),
        "ver": ver,
        "time": now_human(),
        "status": c.get("status", "investigating"),
        "confirm": 0,
        "tip": c.get("tip", ""),
        "confidence": c.get("confidence", 50),
        "evidence": evidence,
        "updated_at": now_iso(),
        "source_note": source_note,
    }


def convert_syn_to_synergy(c: dict, rar_map: dict[str, str]) -> dict:
    """将 candidate_synergies 条目转换为 synergies.json 格式。"""
    raw_aug = c.get("augment", c.get("aug", ""))
    aug_name = normalize_augment_name(raw_aug) if raw_aug else ""

    # tier 来自 rating_type，处理 trap_warning → avoid
    rating = c.get("rating_type", c.get("tier", "recommend"))
    if rating == "trap_warning":
        tier = "avoid"
    elif rating in {"transform", "recommend", "avoid", "bug"}:
        tier = rating
    else:
        tier = "recommend"

    # rar 从 augments.json 查找
    rar = rar_map.get(aug_name, "unknown")
    if rar not in {"silver", "gold", "prism", "unknown"}:
        rar = "unknown"

    ver = c.get("patch", c.get("ver", "unknown"))
    if not ver or ver.lower() == "unknown":
        ver = "unknown"

    evidence = c.get("evidence", [])
    if not isinstance(evidence, list):
        evidence = []

    # source_note 优先级: _force_source_note > 默认逻辑
    if c.get("_force_source_note"):
        source_note = c["_force_source_note"]
    elif not evidence:
        source_note = "该条目来自 AI 候选提取，尚无充分证据，需继续验证。"
    else:
        source_note = ""

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
        "desc": c.get("description", c.get("desc", "")),
        "trigger": c.get("trigger", ""),
        "notes": [],
        "combos": [],
        "evidence": evidence,
        "updated_at": now_iso(),
        "source_note": source_note,
    }


# ---------------------------------------------------------------------------
# 编辑候选
# ---------------------------------------------------------------------------

def edit_candidate(c: dict, cand_type: str) -> dict:
    """交互式编辑候选字段。返回修改后的候选。"""
    print("\n  === 编辑模式 ===")
    print("  (直接回车保留原值)\n")

    def ask_str(field: str, label: str, default: str) -> str:
        val = input(f"  {label} [{default}]: ").strip()
        return val if val else default

    def ask_num(field: str, label: str, default) -> int | float | str:
        val = input(f"  {label} [{default}]: ").strip()
        if not val:
            return default
        try:
            return int(val)
        except ValueError:
            try:
                return float(val)
            except ValueError:
                return default

    # 通用可编辑字段
    if "title" in c or cand_type == "bug_report":
        c["title"] = ask_str("title", "标题", c.get("title", ""))

    desc_key = "description" if "description" in c else "desc"
    c[desc_key] = ask_str("desc", "描述", c.get(desc_key, ""))
    c["trigger"] = ask_str("trigger", "触发条件", c.get("trigger", ""))

    old_status = c.get("status", "investigating")
    new_status = ask_str("status", "状态 (investigating/community/verified/disputed)", old_status)
    if new_status in {"investigating", "community", "verified", "disputed"}:
        c["status"] = new_status
    else:
        print(f"  ⚠ 无效状态 '{new_status}'，保留原值 '{old_status}'")

    c["confidence"] = ask_num("confidence", "置信度 (0-100)", c.get("confidence", 50))

    # 类型特定字段
    if cand_type == "bug_report":
        old_sev = c.get("severity", c.get("sev", "minor"))
        new_sev = ask_str("severity", "严重度 (minor/major/critical)", old_sev)
        if new_sev in {"minor", "major", "critical"}:
            c["severity"] = new_sev
        else:
            print(f"  ⚠ 无效严重度 '{new_sev}'，保留原值 '{old_sev}'")
    else:
        old_rating = c.get("rating_type", c.get("tier", "recommend"))
        new_rating = ask_str("rating_type", "评级类型 (transform/recommend/avoid/bug/trap_warning)", old_rating)
        valid_ratings = {"transform", "recommend", "avoid", "bug", "trap_warning"}
        if new_rating in valid_ratings:
            c["rating_type"] = new_rating
        else:
            print(f"  ⚠ 无效评级 '{new_rating}'，保留原值 '{old_rating}'")

    print("\n  ✓ 编辑完成\n")
    return c


# ---------------------------------------------------------------------------
# 补充证据
# ---------------------------------------------------------------------------

VALID_EVIDENCE_TYPES = {"reddit", "video", "screenshot", "official", "manual"}


def add_evidence(c: dict) -> dict:
    """交互式为候选条目补充证据链接。"""
    print("\n  === 补充证据 ===")
    print(f"  允许类型: {', '.join(sorted(VALID_EVIDENCE_TYPES))}")
    print()

    ev_type = input("  证据类型 (reddit/video/screenshot/official/manual): ").strip().lower()
    if ev_type not in VALID_EVIDENCE_TYPES:
        print(f"  ⚠ 无效类型 '{ev_type}'，已取消")
        return c

    url = input("  URL 链接: ").strip()
    if not url:
        print("  ⚠ URL 不能为空，已取消")
        return c

    summary = input("  摘要说明（可留空）: ").strip()

    evidence_entry = {
        "type": ev_type,
        "url": url,
        "summary": summary,
    }

    if "evidence" not in c or not isinstance(c["evidence"], list):
        c["evidence"] = []
    c["evidence"].append(evidence_entry)

    count = len(c["evidence"])
    print(f"\n  ✓ 已添加第 {count} 条证据: [{ev_type}] {url}\n")
    return c


# ---------------------------------------------------------------------------
# 拒绝记录
# ---------------------------------------------------------------------------

def save_rejected(c: dict, reason: str) -> None:
    """将拒绝的候选追加到 rejected_candidates.json。"""
    rejected = load_json(REJECTED_PATH)
    entry = dict(c)
    entry["rejected_at"] = now_iso()
    entry["reason"] = reason
    rejected.append(entry)
    save_json(REJECTED_PATH, rejected)


# ---------------------------------------------------------------------------
# Changelog 记录
# ---------------------------------------------------------------------------

def append_changelog(c: dict, cand_type: str) -> None:
    """approve 成功后向 changelog.json 追加一条审核记录。"""
    changelog = load_json(CHANGELOG_PATH)

    evidence = c.get("evidence", [])
    if not isinstance(evidence, list):
        evidence = []

    # 确定英雄和增强名称
    if cand_type == "bug_report":
        title = c.get("title", "")
        heroes = c.get("champions", c.get("heroes", []))
        augs = c.get("augments", c.get("augs", []))
        hero_str = ", ".join(heroes) if heroes else ""
        aug_str = ", ".join(augs) if augs else ""
    else:
        title = c.get("hero", "") + " × " + c.get("augment", c.get("aug", ""))
        hero_str = c.get("hero", "")
        aug_str = c.get("augment", c.get("aug", ""))

    record = {
        "date": now_iso(),
        "type": "bug" if cand_type == "bug_report" else "synergy",
        "title": title,
        "hero": hero_str,
        "augment": aug_str,
        "status": c.get("status", "investigating"),
        "source": "review_approve",
        "evidence_count": len(evidence),
    }

    changelog.append(record)
    save_json(CHANGELOG_PATH, changelog)


# ---------------------------------------------------------------------------
# 校验与回滚
# ---------------------------------------------------------------------------

def run_validate() -> bool:
    """运行 validate_data.py，返回是否通过（exit code 0）。"""
    print("\n  ▶ 运行数据校验 (validate_data.py)...")
    try:
        result = subprocess.run(
            [sys.executable, str(VALIDATE_SCRIPT)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
        )
        # 显示校验输出（缩进）
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
        print("  ⚠ 跳过校验\n")
        return True  # 脚本不存在时不阻止
    except subprocess.TimeoutExpired:
        print("  ⚠ 校验超时（30s），跳过\n")
        return True
    except Exception as e:
        print(f"  ⚠ 校验执行异常: {e}，跳过\n")
        return True


# ---------------------------------------------------------------------------
# 主审核循环
# ---------------------------------------------------------------------------

def review_candidates(candidates: list, cand_type: str, source_path: Path) -> dict:
    """
    逐条审核候选数据。返回统计 {approved, rejected, skipped, total}。
    审核结果直接写入正式文件，并从候选文件中移除已处理的条目。
    """
    stats = {"approved": 0, "rejected": 0, "skipped": 0, "total": len(candidates)}
    remaining = list(candidates)  # 跟踪剩余候选
    rar_map = build_augment_rarity_map()
    total = len(candidates)

    print(f"\n{'=' * 64}")
    print(f"  开始审核: {source_path.name} — 共 {total} 条候选")
    print(f"{'=' * 64}")

    i = 0
    while i < len(remaining):
        c = remaining[i]
        display_candidate(c, i, len(remaining), cand_type)

        # 获取操作
        while True:
            action = input("  操作 [a]pprove / [r]eject / [s]kip / [e]dit / [v] evidence / [q]uit > ").strip().lower()
            if action in ("a", "approve", "r", "reject", "s", "skip", "e", "edit", "v", "evidence", "q", "quit"):
                break
            print("  ⚠ 无效输入，请输入 a/r/s/e/v/q")

        # --- quit ---
        if action in ("q", "quit"):
            print("\n  退出审核。已处理的条目已保存。\n")
            # 保存剩余候选
            save_json(source_path, remaining)
            return stats

        # --- skip ---
        if action in ("s", "skip"):
            print("  ⊳ 已跳过")
            stats["skipped"] += 1
            i += 1
            continue

        # --- edit ---
        if action in ("e", "edit"):
            c = edit_candidate(c, cand_type)
            remaining[i] = c
            # 编辑后重新展示，不自动推进
            display_candidate(c, i, len(remaining), cand_type)
            while True:
                action2 = input("  编辑完成，操作 [a]pprove / [r]eject / [s]kip / [v] evidence / [q]uit > ").strip().lower()
                if action2 in ("a", "approve", "r", "reject", "s", "skip", "v", "evidence", "q", "quit"):
                    break
                print("  ⚠ 无效输入")
            if action2 in ("q", "quit"):
                save_json(source_path, remaining)
                return stats
            if action2 in ("s", "skip"):
                print("  ⊳ 已跳过")
                stats["skipped"] += 1
                i += 1
                continue
            action = action2  # 继续到 approve/reject

        # --- add evidence ---
        if action in ("v", "evidence"):
            c = add_evidence(c)
            remaining[i] = c
            # 添加证据后重新展示，不自动推进
            display_candidate(c, i, len(remaining), cand_type)
            while True:
                action2 = input("  操作 [a]pprove / [r]eject / [s]kip / [v] evidence / [q]uit > ").strip().lower()
                if action2 in ("a", "approve", "r", "reject", "s", "skip", "v", "evidence", "q", "quit"):
                    break
                print("  ⚠ 无效输入")
            if action2 in ("q", "quit"):
                save_json(source_path, remaining)
                return stats
            if action2 in ("s", "skip"):
                print("  ⊳ 已跳过")
                stats["skipped"] += 1
                i += 1
                continue
            if action2 in ("v", "evidence"):
                c = add_evidence(c)
                remaining[i] = c
                display_candidate(c, i, len(remaining), cand_type)
                # 继续回到主循环（下次迭代会再次展示和询问）
                continue
            action = action2  # 继续到 approve/reject

        # --- approve ---
        if action in ("a", "approve"):
            # 空证据保护
            ev = c.get("evidence", [])
            if not isinstance(ev, list):
                ev = []
            if not ev:
                print("\n  ⚠ 该候选没有证据链接，是否继续以 investigating 状态写入？")
                print("    - status 将强制为 investigating")
                print("    - confidence 若高于 60 将自动降至 60")
                confirm = input("  继续? [y]es / [n]o (返回重新选择) > ").strip().lower()
                if confirm not in ("y", "yes"):
                    print("  ⊳ 已取消 approve，请补充证据后再试")
                    continue  # 回到循环顶部重新展示和操作
                # 强制 status = investigating
                c["status"] = "investigating"
                # confidence 封顶 60
                old_conf = c.get("confidence", 50)
                if isinstance(old_conf, (int, float)) and old_conf > 60:
                    c["confidence"] = 60
                    print(f"  ℹ confidence 已从 {old_conf}% 降至 60%")
                # source_note 标记
                c["_force_source_note"] = "该条目暂无外部证据链接，需继续验证。"
                remaining[i] = c
                print()

            # 加载当前正式数据
            if cand_type == "bug_report":
                issues = load_json(ISSUES_PATH)
                title = c.get("title", "")
                if is_dup_issue(title, issues):
                    print(f"  ⚠ 重复: issues.json 中已有相同标题 '{title}'，跳过")
                    stats["skipped"] += 1
                    i += 1
                    continue

                converted = convert_bug_to_issue(c)
                # 备份
                backup_path = OUTPUT_DIR / "issues_backup.json"
                save_json(backup_path, issues)
                issues.append(converted)
                save_json(ISSUES_PATH, issues)

                ok = run_validate()
                if not ok:
                    print("  ✗ 校验失败！正在回滚...")
                    restore = load_json(backup_path)
                    save_json(ISSUES_PATH, restore)
                    print("  ✓ 已回滚 issues.json")
                    stats["skipped"] += 1
                    i += 1
                    continue

                print(f"  ✓ 已写入 issues.json: {title}")
                append_changelog(c, "bug_report")
                # 从候选中移除
                remaining.pop(i)
                save_json(source_path, remaining)
                stats["approved"] += 1
                continue  # 不 i+=1，因为 pop 了

            else:
                # synergy_claim 或 trap_warning
                synergies = load_json(SYNERGIES_PATH)
                hero = c.get("hero", "?")
                aug = c.get("augment", c.get("aug", "?"))

                # 预转换以确定 tier
                preview = convert_syn_to_synergy(c, rar_map)
                tier = preview["tier"]

                if is_dup_synergy(hero, aug, tier, synergies):
                    print(f"  ⚠ 重复: synergies.json 中已有 {hero} × {aug} [{tier}]，跳过")
                    stats["skipped"] += 1
                    i += 1
                    continue

                converted = preview
                backup_path = OUTPUT_DIR / "synergies_backup.json"
                save_json(backup_path, synergies)
                synergies.append(converted)
                save_json(SYNERGIES_PATH, synergies)

                ok = run_validate()
                if not ok:
                    print("  ✗ 校验失败！正在回滚...")
                    restore = load_json(backup_path)
                    save_json(SYNERGIES_PATH, restore)
                    print("  ✓ 已回滚 synergies.json")
                    stats["skipped"] += 1
                    i += 1
                    continue

                print(f"  ✓ 已写入 synergies.json: {hero} × {aug} [{tier}]")
                append_changelog(c, "synergy_claim")
                remaining.pop(i)
                save_json(source_path, remaining)
                stats["approved"] += 1
                continue

        # --- reject ---
        if action in ("r", "reject"):
            reason = input("  拒绝原因（可留空）: ").strip()
            save_rejected(c, reason)
            print(f"  ✗ 已拒绝并记录到 rejected_candidates.json")
            remaining.pop(i)
            save_json(source_path, remaining)
            stats["rejected"] += 1
            continue

    # 保存最终剩余（可能有被 skip 的条目）
    save_json(source_path, remaining)
    return stats


# ---------------------------------------------------------------------------
# 主入口
# ---------------------------------------------------------------------------

def main() -> int:
    print("=" * 64)
    print("  海克斯乱斗实验室 — AI 候选数据人工审核")
    print("=" * 64)
    print(f"  候选目录: {OUTPUT_DIR}")
    print(f"  数据目录: {DATA_DIR}")
    print()

    # 解析命令行参数
    import argparse
    parser = argparse.ArgumentParser(description="审核 AI 提取的候选数据")
    parser.add_argument(
        "--type",
        choices=["bugs", "synergies", "all"],
        default="all",
        help="审核类型: bugs=仅Bug, synergies=仅组合, all=全部 (默认 all)",
    )
    args = parser.parse_args()

    # 加载候选数据
    cand_bugs = load_json(CANDIDATE_BUGS_PATH) if args.type in ("bugs", "all") else []
    cand_syns = load_json(CANDIDATE_SYNS_PATH) if args.type in ("synergies", "all") else []

    # 空数据检查
    if not cand_bugs and not cand_syns:
        print("  暂无候选数据，请先运行 pipeline。")
        print()
        print(f"  查找路径:")
        print(f"    - {CANDIDATE_BUGS_PATH} ({'存在' if CANDIDATE_BUGS_PATH.exists() else '不存在'})")
        print(f"    - {CANDIDATE_SYNS_PATH} ({'存在' if CANDIDATE_SYNS_PATH.exists() else '不存在'})")
        return 0

    all_stats = {"approved": 0, "rejected": 0, "skipped": 0, "total": 0}

    # 审核 Bug 候选
    if cand_bugs:
        s = review_candidates(cand_bugs, "bug_report", CANDIDATE_BUGS_PATH)
        for k in all_stats:
            all_stats[k] += s[k]

    # 审核组合候选
    if cand_syns:
        s = review_candidates(cand_syns, "synergy_claim", CANDIDATE_SYNS_PATH)
        for k in all_stats:
            all_stats[k] += s[k]

    # 汇总
    print("\n" + "=" * 64)
    print("  审核完成 — 汇总")
    print("=" * 64)
    print(f"  总候选数  : {all_stats['total']}")
    print(f"  审核通过  : {all_stats['approved']}")
    print(f"  已拒绝    : {all_stats['rejected']}")
    print(f"  已跳过    : {all_stats['skipped']}")
    print(f"  剩余待审  : {all_stats['total'] - all_stats['approved'] - all_stats['rejected']}")
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
