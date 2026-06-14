#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
audit_trust_level.py — 数据可信度审计报告

扫描 data/ 下的 synergies.json、issues.json、reports.json，
识别缺少证据链接但做出高可信度声明的条目，按风险等级分类输出。

本脚本为只读审计，不修改任何数据文件。

用法：
    python scripts/audit_trust_level.py
"""

import json
import re
import sys
from pathlib import Path

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
DATA_DIR = PROJECT_ROOT / "data"

SYNERGIES_PATH = DATA_DIR / "synergies.json"
ISSUES_PATH = DATA_DIR / "issues.json"
REPORTS_PATH = DATA_DIR / "reports.json"

# ---------------------------------------------------------------------------
# 风险等级常量
# ---------------------------------------------------------------------------
HIGH = "高风险"
MEDIUM = "中风险"
LOW = "低风险"

# ---------------------------------------------------------------------------
# 工具函数
# ---------------------------------------------------------------------------

def load_json(path: Path) -> list:
    """加载 JSON 文件。不存在或为空时返回空列表。"""
    if not path.exists():
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except (json.JSONDecodeError, Exception):
        return []


def no_evidence(item: dict) -> bool:
    """条目的 evidence 是否为空（不存在、null、空数组均视为空）。"""
    ev = item.get("evidence")
    if ev is None:
        return True
    if isinstance(ev, list) and len(ev) == 0:
        return True
    return False


# ---------------------------------------------------------------------------
# 审计规则
# ---------------------------------------------------------------------------

def audit_synergies(data: list) -> list[dict]:
    """审计 synergies.json，返回风险条目列表。"""
    findings = []

    for i, s in enumerate(data):
        if not isinstance(s, dict):
            continue

        hero = s.get("hero", "?")
        aug = s.get("aug", "?")
        label = f"{hero} × {aug}"
        status = s.get("status", "")
        src = s.get("src", "")
        sample = s.get("sample", 0)

        # 高风险: status=verified 但 evidence 为空
        if status == "verified" and no_evidence(s):
            findings.append({
                "file": "synergies.json",
                "index": i + 1,
                "label": label,
                "level": HIGH,
                "reason": "status=verified 但 evidence 为空，对外标记为已验证却无证据支撑",
                "action": "补充 evidence 链接，或将 status 降级为 community / investigating",
            })

        # 中风险: src=data 且 sample 非空但 evidence 为空
        if src == "data" and sample and sample > 0 and no_evidence(s):
            findings.append({
                "file": "synergies.json",
                "index": i + 1,
                "label": label,
                "level": MEDIUM,
                "reason": f"src=data 且 sample={sample} 但 evidence 为空，数据驱动结论缺少来源佐证",
                "action": "补充数据来源链接（数据截图、分析帖子等）",
            })

    return findings


def audit_issues(data: list) -> list[dict]:
    """审计 issues.json，返回风险条目列表。"""
    findings = []

    for i, iss in enumerate(data):
        if not isinstance(iss, dict):
            continue

        title = iss.get("title", "无标题")
        sev = iss.get("sev", "")
        confirm = iss.get("confirm", 0)

        # 高风险: severity=critical 但 evidence 为空
        if sev == "critical" and no_evidence(iss):
            findings.append({
                "file": "issues.json",
                "index": i + 1,
                "label": title,
                "level": HIGH,
                "reason": "severity=critical 但 evidence 为空，严重问题声明缺少复现证据",
                "action": "补充 Bug 复现截图、视频或官方确认链接",
            })

        # 中风险: confirm > 0 但 evidence 为空
        if confirm and confirm > 0 and no_evidence(iss):
            findings.append({
                "file": "issues.json",
                "index": i + 1,
                "label": title,
                "level": MEDIUM,
                "reason": f"confirm={confirm} 但 evidence 为空，已有用户确认却无外部证据",
                "action": "补充社区讨论帖或复现证据链接",
            })

    return findings


def audit_reports(data: list) -> list[dict]:
    """审计 reports.json，返回风险条目列表。"""
    findings = []

    # 关键词：描述中包含这些词暗示有数据支撑，但无 evidence
    keywords_pattern = re.compile(r"实测|数据分析|胜率|样本|确认")

    for i, r in enumerate(data):
        if not isinstance(r, dict):
            continue

        hero = r.get("hero", "?")
        aug = r.get("aug", "?")
        label = f"{hero} × {aug}"
        desc = r.get("desc", "")

        # 低风险: 描述含数据性关键词但 evidence 为空
        if keywords_pattern.search(desc) and no_evidence(r):
            matched = [m.group() for m in keywords_pattern.finditer(desc)]
            findings.append({
                "file": "reports.json",
                "index": i + 1,
                "label": label,
                "level": LOW,
                "reason": f"描述包含数据性声明（{'、'.join(matched)}）但 evidence 为空",
                "action": "补充相关数据来源或实测截图链接",
            })

    return findings


# ---------------------------------------------------------------------------
# 报告输出
# ---------------------------------------------------------------------------

def print_findings(findings: list[dict], level: str) -> None:
    """按风险等级输出条目。"""
    items = [f for f in findings if f["level"] == level]
    if not items:
        return

    level_colors = {HIGH: "🔴", MEDIUM: "🟡", LOW: "🔵"}
    icon = level_colors.get(level, "•")

    print(f"\n  {icon} {level}条目 ({len(items)} 条)")
    print(f"  {'─' * 60}")

    for f in items:
        print(f"    文件     : {f['file']}")
        print(f"    条目     : 第 {f['index']} 条 — {f['label']}")
        print(f"    风险原因 : {f['reason']}")
        print(f"    建议动作 : {f['action']}")
        print(f"    {'─' * 56}")


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------

def main() -> int:
    print("=" * 64)
    print("  海克斯乱斗实验室 — 数据可信度审计报告")
    print("=" * 64)
    print(f"  数据目录: {DATA_DIR}")
    print("  模式: 只读审计（不修改任何文件）")

    # 加载数据
    synergies = load_json(SYNERGIES_PATH)
    issues = load_json(ISSUES_PATH)
    reports = load_json(REPORTS_PATH)

    if not synergies and not issues and not reports:
        print("\n  ⚠ 未找到任何数据文件，请先确认 data/ 目录。")
        return 0

    print(f"\n  数据概况:")
    print(f"    synergies.json : {len(synergies)} 条")
    print(f"    issues.json    : {len(issues)} 条")
    print(f"    reports.json   : {len(reports)} 条")

    # 执行审计
    all_findings: list[dict] = []
    all_findings.extend(audit_synergies(synergies))
    all_findings.extend(audit_issues(issues))
    all_findings.extend(audit_reports(reports))

    # 去重：同一条目可能触发多条规则（如 verified + src=data），合并展示
    # 按 (file, index) 分组，保留最高风险等级
    seen: dict[tuple[str, int], dict] = {}
    for f in all_findings:
        key = (f["file"], f["index"])
        if key not in seen:
            seen[key] = f
        else:
            existing = seen[key]
            # 风险等级排序：高 > 中 > 低
            priority = {HIGH: 3, MEDIUM: 2, LOW: 1}
            if priority.get(f["level"], 0) > priority.get(existing["level"], 0):
                # 升级风险等级，合并原因
                seen[key]["level"] = f["level"]
                seen[key]["reason"] = existing["reason"] + "；" + f["reason"]
                seen[key]["action"] = f["action"]
            else:
                # 保留当前等级，合并原因
                if f["reason"] not in existing["reason"]:
                    existing["reason"] += "；" + f["reason"]

    deduped = list(seen.values())

    # 统计
    high_count = sum(1 for f in deduped if f["level"] == HIGH)
    medium_count = sum(1 for f in deduped if f["level"] == MEDIUM)
    low_count = sum(1 for f in deduped if f["level"] == LOW)

    # 输出报告
    if not deduped:
        print("\n  ✓ 未发现可信度风险条目。所有高可信度声明均有证据支撑。")
    else:
        print(f"\n  共发现 {len(deduped)} 个可信度风险条目（去重后）：")
        print_findings(deduped, HIGH)
        print_findings(deduped, MEDIUM)
        print_findings(deduped, LOW)

    # 汇总
    print("\n" + "=" * 64)
    print("  审计汇总")
    print("=" * 64)
    print(f"  🔴 高风险 : {high_count} 条")
    print(f"  🟡 中风险 : {medium_count} 条")
    print(f"  🔵 低风险 : {low_count} 条")
    print(f"  合计     : {high_count + medium_count + low_count} 条")

    if high_count == 0 and medium_count == 0 and low_count == 0:
        print("\n  ✓ 数据可信度状况良好。")
    elif high_count > 0:
        print(f"\n  ⚠ 建议优先处理 {high_count} 条高风险条目。")
    print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
