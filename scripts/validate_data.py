#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
validate_data.py — 海克斯乱斗实验室 数据校验脚本

校验 data/ 目录下所有 JSON 数据文件的结构完整性和引用一致性。

用法：
    python scripts/validate_data.py
"""

import json
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

# ---------------------------------------------------------------------------
# 枚举值定义
# ---------------------------------------------------------------------------
VALID_TIERS = {"transform", "recommend", "avoid", "bug"}
VALID_RARITIES = {"silver", "gold", "prism"}
VALID_STATUSES = {"verified", "community", "disputed", "investigating", "outdated", "fixed"}
VALID_SEVERITIES = {"minor", "major", "critical"}

# 增强图鉴专用枚举
VALID_AUG_TIERS = {"silver", "gold", "prismatic", "unknown"}
VALID_AUG_STATUSES = {"active", "removed", "unknown"}

# ---------------------------------------------------------------------------
# 各文件必需字段
# ---------------------------------------------------------------------------
CHAMPION_REQUIRED = {"name", "title", "role", "tier", "wr", "pr", "games", "kda", "build", "tips"}
AUGMENT_REQUIRED = {"name", "rar", "wr", "pr", "desc", "trigger", "best", "avoid", "tests"}
# 增强图鉴新增必需字段
AUGMENT_WIKI_REQUIRED = {"id", "name", "name_en", "aliases", "tier", "status"}
SYNERGY_REQUIRED = {"hero", "aug", "rar", "tier", "delta", "conf", "sample", "ver", "src", "status", "desc", "trigger", "notes", "combos"}
REPORT_REQUIRED = {"author", "hero", "aug", "tier", "stars", "desc", "trigger", "ver", "status", "likes", "dislikes", "comments"}
ISSUE_REQUIRED = {"sev", "title", "heroes", "augs", "desc", "ver", "time", "status", "confirm", "tip"}
CHANGELOG_REQUIRED = {"date", "type", "title", "hero", "augment", "status", "source", "evidence_count"}

# ---------------------------------------------------------------------------
# 错误收集
# ---------------------------------------------------------------------------
errors: list[str] = []
warnings: list[str] = []


def err(msg: str) -> None:
    """记录一条校验错误。"""
    errors.append(msg)


def warn(msg: str) -> None:
    """记录一条校验警告（不影响退出码）。"""
    warnings.append(msg)


# ---------------------------------------------------------------------------
# 通用工具
# ---------------------------------------------------------------------------

def load_json(filepath: Path) -> object | None:
    """加载 JSON 文件，失败时记录错误并返回 None。"""
    if not filepath.exists():
        err(f"文件不存在: {filepath.relative_to(PROJECT_ROOT)}")
        return None
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        err(f"JSON 解析失败: {filepath.relative_to(PROJECT_ROOT)} — {e}")
        return None
    except Exception as e:
        err(f"读取失败: {filepath.relative_to(PROJECT_ROOT)} — {e}")
        return None


def check_required_fields(item: dict, required: set, label: str, filename: str, index: int) -> bool:
    """检查必需字段是否存在，返回是否全部通过。"""
    missing = required - set(item.keys())
    if missing:
        err(f"[{filename}] 第 {index + 1} 条 {label} 缺少字段: {', '.join(sorted(missing))}")
        return False
    return True


def check_enum(value: str, valid: set, field_name: str, label: str, filename: str, index: int) -> None:
    """检查枚举值是否合法。"""
    if value not in valid:
        err(f"[{filename}] 第 {index + 1} 条 {label} 的 {field_name} 值 '{value}' 不合法，允许值: {', '.join(sorted(valid))}")


def _normalize_key(s: str) -> str:
    """将名称转为标准化查找键：小写、去除空格和撇号。"""
    return s.lower().replace("'", "").replace("'", "").replace(" ", "").replace("-", "")


# ---------------------------------------------------------------------------
# 各文件校验函数
# ---------------------------------------------------------------------------

def validate_champions(filepath: Path) -> tuple[set[str], set[str]]:
    """
    校验 champions.json，返回 (hero_names, champion_keys) 用于后续引用检查。
    """
    hero_names: set[str] = set()
    data = load_json(filepath)
    if data is None:
        return hero_names, set()

    # 顶层结构
    if not isinstance(data, dict):
        err(f"[champions.json] 顶层应为 object，实际为 {type(data).__name__}")
        return hero_names, set()

    if "championKeys" not in data:
        err("[champions.json] 缺少顶层字段: championKeys")
    if "champions" not in data:
        err("[champions.json] 缺少顶层字段: champions")
        return hero_names, set()

    champions = data["champions"]
    if not isinstance(champions, list):
        err("[champions.json] champions 应为数组")
        return hero_names, set()

    champion_keys = set(data.get("championKeys", {}).keys())

    for i, c in enumerate(champions):
        if not isinstance(c, dict):
            err(f"[champions.json] 第 {i + 1} 条应为 object")
            continue
        check_required_fields(c, CHAMPION_REQUIRED, "英雄", "champions.json", i)
        if "name" in c:
            name = c["name"]
            if name in hero_names:
                err(f"[champions.json] 英雄名重复: '{name}'（第 {i + 1} 条）")
            hero_names.add(name)

    # championKeys 与 champions 数量一致性（仅警告）
    if champion_keys and len(champion_keys) != len(champions):
        err(f"[champions.json] championKeys 有 {len(champion_keys)} 个键，但 champions 有 {len(champions)} 条，数量不一致")

    return hero_names, champion_keys


def validate_augments(filepath: Path) -> tuple[set[str], set[str], dict[str, str]]:
    """
    校验 augments.json，返回 (aug_names, aug_ids, alias_to_name) 用于后续引用检查。

    alias_to_name: {标准化键 → 中文正式名}，用于跨文件引用校验。
    """
    aug_names: set[str] = set()
    aug_ids: set[str] = set()
    alias_to_name: dict[str, str] = {}
    data = load_json(filepath)
    if data is None:
        return aug_names, aug_ids, alias_to_name

    if not isinstance(data, list):
        err(f"[augments.json] 顶层应为数组，实际为 {type(data).__name__}")
        return aug_names, aug_ids, alias_to_name

    # 用于 name_en 唯一性检查（大小写不敏感）
    name_en_lower_seen: dict[str, int] = {}

    for i, a in enumerate(data):
        if not isinstance(a, dict):
            err(f"[augments.json] 第 {i + 1} 条应为 object")
            continue

        # --- 旧字段检查（保持向后兼容） ---
        check_required_fields(a, AUGMENT_REQUIRED, "增强", "augments.json", i)
        if "rar" in a:
            check_enum(a["rar"], VALID_RARITIES, "rar", "增强", "augments.json", i)

        # --- 新增图鉴字段检查 (ERROR) ---

        # 1. id 必须存在
        if "id" not in a:
            err(f"[augments.json] 第 {i + 1} 条增强缺少字段: id")
        else:
            aug_id = a["id"]
            # 2. id 不能为空
            if not aug_id or not isinstance(aug_id, str) or not aug_id.strip():
                err(f"[augments.json] 第 {i + 1} 条增强的 id 不能为空")
            else:
                # 3. id 必须唯一
                if aug_id in aug_ids:
                    err(f"[augments.json] 增强 id 重复: '{aug_id}'（第 {i + 1} 条）")
                aug_ids.add(aug_id)

        # 4. name 必须存在且非空
        if "name" not in a:
            err(f"[augments.json] 第 {i + 1} 条增强缺少字段: name")
        else:
            name = a["name"]
            if not isinstance(name, str) or not name.strip():
                err(f"[augments.json] 第 {i + 1} 条增强的 name 不能为空")
            else:
                # 5. name 必须唯一
                if name in aug_names:
                    err(f"[augments.json] 增强名重复: '{name}'（第 {i + 1} 条）")
                aug_names.add(name)
                # 注册到 alias 映射
                alias_to_name[_normalize_key(name)] = name

        # 6. name_en 必须存在且非空
        if "name_en" not in a:
            err(f"[augments.json] 第 {i + 1} 条增强缺少字段: name_en")
        else:
            name_en = a["name_en"]
            if not isinstance(name_en, str) or not name_en.strip():
                err(f"[augments.json] 第 {i + 1} 条增强的 name_en 不能为空")
            else:
                # 7. name_en 唯一性（大小写不敏感）
                ne_lower = name_en.lower()
                if ne_lower in name_en_lower_seen:
                    err(f"[augments.json] 增强 name_en 重复（不区分大小写）: '{name_en}'（第 {i + 1} 条，与第 {name_en_lower_seen[ne_lower]} 条冲突）")
                else:
                    name_en_lower_seen[ne_lower] = i + 1
                alias_to_name[_normalize_key(name_en)] = a.get("name", name_en)

        # 8. aliases 必须是数组
        if "aliases" not in a:
            err(f"[augments.json] 第 {i + 1} 条增强缺少字段: aliases")
        else:
            aliases = a["aliases"]
            if not isinstance(aliases, list):
                err(f"[augments.json] 第 {i + 1} 条增强的 aliases 应为数组，实际为 {type(aliases).__name__}")
            else:
                # 9. 同一个 alias 不允许指向多个不同增强（大小写不敏感）
                cn_name = a.get("name", "")
                for alias in aliases:
                    if isinstance(alias, str) and alias:
                        norm = _normalize_key(alias)
                        if norm in alias_to_name and alias_to_name[norm] != cn_name:
                            err(f"[augments.json] 第 {i + 1} 条增强的 alias '{alias}' 与增强 '{alias_to_name[norm]}' 冲突")
                        else:
                            alias_to_name[norm] = cn_name

        # 10. tier 枚举校验
        if "tier" in a:
            check_enum(a["tier"], VALID_AUG_TIERS, "tier", "增强", "augments.json", i)

        # 11. status 枚举校验
        if "status" in a:
            check_enum(a["status"], VALID_AUG_STATUSES, "status", "增强", "augments.json", i)

        # 12. source 如果存在，必须是对象
        if "source" in a:
            source = a["source"]
            if source is not None and not isinstance(source, dict):
                err(f"[augments.json] 第 {i + 1} 条增强的 source 应为对象，实际为 {type(source).__name__}")

        # --- 新增 WARNING 级别规则 ---

        # W1. tier 为 unknown
        if a.get("tier") == "unknown":
            warn(f"[augments.json] 第 {i + 1} 条增强 '{a.get('name', '?')}' tier 为 unknown")

        # W2. effect 为空
        effect = a.get("effect", "")
        if not effect or not isinstance(effect, str) or not effect.strip():
            warn(f"[augments.json] 第 {i + 1} 条增强 '{a.get('name', '?')}' effect 为空")

        # W3. source.url 为空
        source = a.get("source")
        if isinstance(source, dict):
            if not source.get("url", "").strip():
                warn(f"[augments.json] 第 {i + 1} 条增强 '{a.get('name', '?')}' source.url 为空")

        # W4. tags 为空
        tags = a.get("tags", [])
        if not tags or not isinstance(tags, list) or len(tags) == 0:
            warn(f"[augments.json] 第 {i + 1} 条增强 '{a.get('name', '?')}' tags 为空")

        # W5. patch_added 为空
        pa = a.get("patch_added", "")
        if not pa or not isinstance(pa, str) or not pa.strip():
            warn(f"[augments.json] 第 {i + 1} 条增强 '{a.get('name', '?')}' patch_added 为空")

        # W6. status 为 unknown
        if a.get("status") == "unknown":
            warn(f"[augments.json] 第 {i + 1} 条增强 '{a.get('name', '?')}' status 为 unknown")

        # W7. aliases 为空
        aliases = a.get("aliases", [])
        if isinstance(aliases, list) and len(aliases) == 0:
            warn(f"[augments.json] 第 {i + 1} 条增强 '{a.get('name', '?')}' aliases 为空")

    return aug_names, aug_ids, alias_to_name


def _resolve_aug_ref(ref_name: str, aug_names: set[str], alias_to_name: dict[str, str]) -> str | None:
    """
    尝试解析增强引用名。返回解析后的中文正式名，或 None 表示无法解析。

    优先精确匹配，然后通过标准化键匹配。
    """
    # 精确匹配中文名
    if ref_name in aug_names:
        return ref_name
    # 标准化键匹配
    norm = _normalize_key(ref_name)
    if norm in alias_to_name:
        return alias_to_name[norm]
    return None


def validate_synergies(filepath: Path, hero_names: set[str], aug_names: set[str], alias_to_name: dict[str, str]) -> None:
    """校验 synergies.json 及其引用一致性。"""
    data = load_json(filepath)
    if data is None:
        return

    if not isinstance(data, list):
        err(f"[synergies.json] 顶层应为数组，实际为 {type(data).__name__}")
        return

    for i, s in enumerate(data):
        if not isinstance(s, dict):
            err(f"[synergies.json] 第 {i + 1} 条应为 object")
            continue
        check_required_fields(s, SYNERGY_REQUIRED, "组合", "synergies.json", i)

        # 枚举校验
        if "tier" in s:
            check_enum(s["tier"], VALID_TIERS, "tier", "组合", "synergies.json", i)
        if "rar" in s:
            check_enum(s["rar"], VALID_RARITIES, "rar", "组合", "synergies.json", i)
        if "status" in s:
            check_enum(s["status"], VALID_STATUSES, "status", "组合", "synergies.json", i)

        # 引用校验
        if "hero" in s and hero_names and s["hero"] not in hero_names:
            err(f"[synergies.json] 第 {i + 1} 条组合引用了不存在的英雄: '{s['hero']}'")
        if "aug" in s and aug_names:
            resolved = _resolve_aug_ref(s["aug"], aug_names, alias_to_name)
            if resolved is None:
                err(f"[synergies.json] 第 {i + 1} 条组合引用了不存在的增强: '{s['aug']}'")

        # evidence 类型校验（存在时必须为数组）
        ev = s.get("evidence")
        if ev is not None and not isinstance(ev, list):
            err(f"[synergies.json] 第 {i + 1} 条组合的 evidence 应为数组，实际为 {type(ev).__name__}")

        # 警告：status=verified 但 evidence 为空
        status = s.get("status")
        if status == "verified" and (ev is None or len(ev) == 0):
            warn(f"[synergies.json] 第 {i + 1} 条组合 status=verified 但 evidence 为空，建议补充证据链接")

        # 警告：src=data 且 sample 非零但 evidence 为空
        src = s.get("src")
        sample = s.get("sample", 0)
        if src == "data" and sample and sample > 0 and (ev is None or len(ev) == 0):
            warn(f"[synergies.json] 第 {i + 1} 条组合 src=data 且 sample={sample} 但 evidence 为空，建议补充数据来源")


def validate_reports(filepath: Path, hero_names: set[str], aug_names: set[str]) -> None:
    """校验 reports.json 及其引用一致性。"""
    data = load_json(filepath)
    if data is None:
        return

    if not isinstance(data, list):
        err(f"[reports.json] 顶层应为数组，实际为 {type(data).__name__}")
        return

    for i, r in enumerate(data):
        if not isinstance(r, dict):
            err(f"[reports.json] 第 {i + 1} 条应为 object")
            continue
        check_required_fields(r, REPORT_REQUIRED, "投稿", "reports.json", i)

        # 枚举校验
        if "tier" in r:
            check_enum(r["tier"], VALID_TIERS, "tier", "投稿", "reports.json", i)
        if "status" in r:
            check_enum(r["status"], VALID_STATUSES, "status", "投稿", "reports.json", i)

        # 引用校验
        if "hero" in r and hero_names and r["hero"] not in hero_names:
            err(f"[reports.json] 第 {i + 1} 条投稿引用了不存在的英雄: '{r['hero']}'")
        if "aug" in r and aug_names and r["aug"] not in aug_names:
            err(f"[reports.json] 第 {i + 1} 条投稿引用了不存在的增强: '{r['aug']}'")

        # evidence 类型校验（存在时必须为数组）
        ev = r.get("evidence")
        if ev is not None and not isinstance(ev, list):
            err(f"[reports.json] 第 {i + 1} 条投稿的 evidence 应为数组，实际为 {type(ev).__name__}")

        # 警告：status=verified 但 evidence 为空
        status = r.get("status")
        if status == "verified" and (ev is None or len(ev) == 0):
            warn(f"[reports.json] 第 {i + 1} 条投稿 status=verified 但 evidence 为空，建议补充证据链接")


def validate_issues(filepath: Path, hero_names: set[str], aug_names: set[str], alias_to_name: dict[str, str]) -> None:
    """校验 issues.json 及其引用一致性。"""
    data = load_json(filepath)
    if data is None:
        return

    if not isinstance(data, list):
        err(f"[issues.json] 顶层应为数组，实际为 {type(data).__name__}")
        return

    for i, iss in enumerate(data):
        if not isinstance(iss, dict):
            err(f"[issues.json] 第 {i + 1} 条应为 object")
            continue
        check_required_fields(iss, ISSUE_REQUIRED, "问题", "issues.json", i)

        # 枚举校验
        if "sev" in iss:
            check_enum(iss["sev"], VALID_SEVERITIES, "sev", "问题", "issues.json", i)
        if "status" in iss:
            check_enum(iss["status"], VALID_STATUSES, "status", "问题", "issues.json", i)

        # 引用校验（heroes / augs 是数组）
        if "heroes" in iss and hero_names:
            for h in iss["heroes"]:
                if h not in hero_names:
                    err(f"[issues.json] 第 {i + 1} 条问题引用了不存在的英雄: '{h}'")
        if "augs" in iss and aug_names:
            for a in iss["augs"]:
                resolved = _resolve_aug_ref(a, aug_names, alias_to_name)
                if resolved is None:
                    err(f"[issues.json] 第 {i + 1} 条问题引用了不存在的增强: '{a}'")

        # evidence 类型校验（存在时必须为数组）
        ev = iss.get("evidence")
        if ev is not None and not isinstance(ev, list):
            err(f"[issues.json] 第 {i + 1} 条问题的 evidence 应为数组，实际为 {type(ev).__name__}")

        # 警告：status=verified 但 evidence 为空
        status = iss.get("status")
        if status == "verified" and (ev is None or len(ev) == 0):
            warn(f"[issues.json] 第 {i + 1} 条问题 status=verified 但 evidence 为空，建议补充证据链接")


# ---------------------------------------------------------------------------
# changelog 校验（可选文件）
# ---------------------------------------------------------------------------

def validate_changelog(filepath: Path) -> int:
    """
    校验 changelog.json（如果存在）。
    缺失不算 error；存在时检查 JSON 合法性和字段。
    返回记录数。
    """
    if not filepath.exists():
        return 0

    data = load_json(filepath)
    if data is None:
        # JSON 解析失败算 error（文件存在但损坏）
        return 0

    if not isinstance(data, list):
        err(f"[changelog.json] 顶层应为数组，实际为 {type(data).__name__}")
        return 0

    for i, entry in enumerate(data):
        if not isinstance(entry, dict):
            err(f"[changelog.json] 第 {i + 1} 条应为 object")
            continue
        check_required_fields(entry, CHANGELOG_REQUIRED, "变更记录", "changelog.json", i)

        # type 枚举校验
        ct = entry.get("type")
        if ct is not None and ct not in {"bug", "synergy"}:
            err(f"[changelog.json] 第 {i + 1} 条的 type 值 '{ct}' 不合法，允许值: bug, synergy")

        # evidence_count 类型校验
        ec = entry.get("evidence_count")
        if ec is not None and not isinstance(ec, int):
            err(f"[changelog.json] 第 {i + 1} 条的 evidence_count 应为整数，实际为 {type(ec).__name__}")

    return len(data)


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------

def main() -> int:
    print("=" * 56)
    print("  海克斯乱斗实验室 — 数据校验")
    print("=" * 56)
    print(f"  数据目录: {DATA_DIR}")
    print()

    # 1. champions.json — 先加载，获取 hero_names 供后续引用校验
    hero_names, champion_keys = validate_champions(DATA_DIR / "champions.json")

    # 2. augments.json — 先加载，获取 aug_names + alias 映射供后续引用校验
    aug_names, aug_ids, alias_to_name = validate_augments(DATA_DIR / "augments.json")

    # 3. synergies.json
    validate_synergies(DATA_DIR / "synergies.json", hero_names, aug_names, alias_to_name)

    # 4. reports.json
    validate_reports(DATA_DIR / "reports.json", hero_names, aug_names)

    # 5. issues.json
    validate_issues(DATA_DIR / "issues.json", hero_names, aug_names, alias_to_name)

    # 6. changelog.json（可选）
    changelog_count = validate_changelog(DATA_DIR / "changelog.json")

    # 输出结果
    print()

    if errors:
        print(f"发现 {len(errors)} 个错误：")
        print("-" * 56)
        for e in errors:
            print(f"  ✗ {e}")
        print("-" * 56)

    if warnings:
        print(f"发现 {len(warnings)} 个警告：")
        print("-" * 56)
        for w in warnings:
            print(f"  ⚠ {w}")
        print("-" * 56)

    if errors:
        print(f"校验未通过：{len(errors)} 个错误，{len(warnings)} 个警告。")
        return 1
    else:
        print("数据校验通过。")
        print()
        print(f"  champions : {len(hero_names)} 位英雄, {len(champion_keys)} 个 championKeys")
        print(f"  augments  : {len(aug_names)} 个增强, {len(aug_ids)} 个 id")
        print(f"  synergies : 组合引用全部匹配 ✓")
        print(f"  reports   : 投稿引用全部匹配 ✓")
        print(f"  issues    : 问题引用全部匹配 ✓")
        if changelog_count:
            print(f"  changelog : {changelog_count} 条审核记录 ✓")
        if warnings:
            print()
            print(f"  共 {len(warnings)} 个警告（不影响退出码），建议后续补充。")
        print()
        print("所有字段、枚举值和跨文件引用均正确。")
        return 0


if __name__ == "__main__":
    sys.exit(main())
