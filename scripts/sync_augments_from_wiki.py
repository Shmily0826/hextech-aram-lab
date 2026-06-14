#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sync_augments_from_wiki.py — 真实增强数据导入审计

从 LoL Wiki Module:MayhemAugmentData 拉取增强数据，
生成候选导入文件和差异报告，**不修改** data/augments.json。

输出:
  pipeline/output/augment_import_candidates.json
  pipeline/output/augment_import_diff.json
"""

import json
import re
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

# Windows UTF-8
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

# ---------------------------------------------------------------------------
# 路径
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
AUGMENTS_PATH = PROJECT_ROOT / "data" / "augments.json"
OUTPUT_DIR = PROJECT_ROOT / "pipeline" / "output"
CANDIDATES_PATH = OUTPUT_DIR / "augment_import_candidates.json"
DIFF_PATH = OUTPUT_DIR / "augment_import_diff.json"

WIKI_MODULE_URL = (
    "https://wiki.leagueoflegends.com/en-us/api.php"
    "?action=parse&page=Module:MayhemAugmentData/data"
    "&prop=wikitext&format=json"
)
WIKI_SOURCE_URL = "https://wiki.leagueoflegends.com/en-us/Module:MayhemAugmentData/data"

# ---------------------------------------------------------------------------
# Wiki 模板标记清理
# ---------------------------------------------------------------------------

def strip_wiki_templates(text: str) -> str:
    """移除 MediaWiki 模板标记，保留纯文本效果描述。"""
    # 移除 {{as|...}} → 取最后一个 pipe 之后的文本或第一个参数
    # 常见格式: {{as|text}}, {{as|text|stat}}, {{as|text|stat|unit}}
    # 简化策略: 移除模板标签，保留内部文本
    s = text

    # 移除嵌套模板 {{...|...}} 保留内部纯文本
    # 反复处理直到没有嵌套
    prev = ""
    while prev != s:
        prev = s
        # {{tip|word|tooltip}} → word
        s = re.sub(r'\{\{tip\|([^|]*)\|[^}]*\}\}', r'\1', s)
        # {{as|text|...}} → text (取第一个参数)
        s = re.sub(r'\{\{as\|([^|}]*)[^}]*\}\}', r'\1', s)
        # {{fd|number}} → number
        s = re.sub(r'\{\{fd\|([^|}]*)[^}]*\}\}', r'\1', s)
        # {{pp|...}} → 数值 (取第一个参数)
        s = re.sub(r'\{\{pp\|([^|}]*)[^}]*\}\}', r'\1', s)
        # {{bi|item}} → item
        s = re.sub(r'\{\{bi\|([^|}]*)[^}]*\}\}', r'\1', s)
        # {{cai|ability|champion}} → ability
        s = re.sub(r'\{\{cai\|([^|}]*)\|[^}]*\}\}', r'\1', s)
        # {{si|spell}} → spell
        s = re.sub(r'\{\{si\|([^|}]*)[^}]*\}\}', r'\1', s)
        # {{ii|item}} → item
        s = re.sub(r'\{\{ii\|([^|}]*)[^}]*\}\}', r'\1', s)
        # {{stil|text}} → text
        s = re.sub(r'\{\{stil\|([^|}]*)[^}]*\}\}', r'\1', s)
        # {{sbc|text:}} → text:
        s = re.sub(r'\{\{sbc\|([^|}]*)[^}]*\}\}', r'\1', s)
        # {{rd|...}} → numbers
        s = re.sub(r'\{\{rd\|([^|}]*)[^}]*\}\}', r'\1', s)
        # {{ft|text}} → text
        s = re.sub(r'\{\{ft\|([^|}]*)[^}]*\}\}', r'\1', s)
        # {{g|number}} → number
        s = re.sub(r'\{\{g\|([^|}]*)[^}]*\}\}', r'\1', s)
        # {{tip|word}} → word (无 tooltip 参数)
        s = re.sub(r'\{\{tip\|([^|}]*)\}\}', r'\1', s)
        # 其他未识别模板: {{name|params}} → params 的第一段
        s = re.sub(r'\{\{[^{}|]*\|([^|}]*)[^}]*\}\}', r'\1', s)
        # 空模板 {{}}
        s = re.sub(r'\{\{[^}]*\}\}', '', s)

    # 移除 [[...|display]] → display, [[text]] → text
    s = re.sub(r'\[\[[^|\]]*\|([^\]]*)\]\]', r'\1', s)
    s = re.sub(r'\[\[([^\]]*)\]\]', r'\1', s)

    # 移除 '''bold''' → bold, ''italic'' → italic
    s = re.sub(r"'''([^']*)'''", r'\1', s)
    s = re.sub(r"''([^']*)''", r'\1', s)

    # <br> → 空格或换行
    s = s.replace('<br>', ' ').replace('<br/>', ' ').replace('<br />', ' ')

    # 移除残留 HTML 标签
    s = re.sub(r'<[^>]+>', '', s)

    # 移除 [=[ ... ]=] Lua 长注释（notes 字段中可能出现）
    s = re.sub(r'\[=\[.*?\]=\]', '', s, flags=re.DOTALL)

    # 清理多余空白
    s = re.sub(r'\s+', ' ', s).strip()

    return s


# ---------------------------------------------------------------------------
# Lua 表解析
# ---------------------------------------------------------------------------

def parse_lua_augments(wikitext: str) -> list[dict]:
    """从 Lua module wikitext 中解析增强数据。"""
    augments = []

    # 匹配每个 augment entry: ["Name"] = { ... }
    # 使用非贪婪匹配找所有顶层 entry
    pattern = re.compile(
        r'\["([^"]+)"\]\s*=\s*\{(.*?)\n\t\}',
        re.DOTALL
    )

    for m in pattern.finditer(wikitext):
        name = m.group(1).strip()
        body = m.group(2)

        # 提取 tier
        tier_m = re.search(r'\["tier"\]\s*=\s*"(\w+)"', body)
        tier = tier_m.group(1) if tier_m else "unknown"

        # 提取 description
        desc_m = re.search(r'\["description"\]\s*=\s*"(.*?)"(?:,|\s*\n)', body, re.DOTALL)
        desc_raw = desc_m.group(1) if desc_m else ""
        desc_clean = strip_wiki_templates(desc_raw)

        # 提取 notes（可能不存在）
        notes_m = re.search(r'\["notes"\]\s*=\s*(\[=\[.*?\]=\])', body, re.DOTALL)
        notes_raw = notes_m.group(1) if notes_m else ""
        notes_clean = strip_wiki_templates(notes_raw) if notes_raw else ""

        # 提取 set
        set_m = re.search(r'\["set"\]\s*=\s*"(.*?)"', body)
        set_raw = set_m.group(1) if set_m else "-"
        set_clean = strip_wiki_templates(set_raw).strip() if set_raw != "-" else ""

        augments.append({
            "name_en": name,
            "tier_raw": tier,
            "effect_en_raw": desc_clean,
            "notes_raw": notes_clean,
            "set": set_clean,
        })

    return augments


# ---------------------------------------------------------------------------
# ID 生成
# ---------------------------------------------------------------------------

def make_id(name_en: str) -> str:
    """从英文名生成 stable snake_case id。"""
    # 转小写，替换非字母数字为下划线
    s = name_en.lower()
    s = re.sub(r"[^a-z0-9]+", "_", s)
    s = s.strip("_")
    return s


# ---------------------------------------------------------------------------
# Tier 映射
# ---------------------------------------------------------------------------

TIER_MAP = {
    "silver": "silver",
    "gold": "gold",
    "prismatic": "prismatic",
}


def normalize_tier(raw: str) -> str:
    return TIER_MAP.get(raw.lower(), "unknown")


# ---------------------------------------------------------------------------
# 匹配逻辑
# ---------------------------------------------------------------------------

def build_match_index(current_augs: list[dict]) -> dict:
    """
    构建匹配索引:
    - name_en (lowercase) → index
    - aliases (lowercase) → index
    - id → index
    """
    idx = {"by_name_en": {}, "by_alias": {}, "by_id": {}}

    for i, aug in enumerate(current_augs):
        ne = (aug.get("name_en") or "").strip().lower()
        if ne:
            idx["by_name_en"][ne] = i

        for alias in (aug.get("aliases") or []):
            if isinstance(alias, str):
                a = alias.strip().lower()
                if a:
                    # 只在不存在冲突时记录
                    if a not in idx["by_alias"]:
                        idx["by_alias"][a] = i

        aid = (aug.get("id") or "").strip().lower()
        if aid:
            idx["by_id"][aid] = i

    return idx


def find_match(wiki_name_en: str, index: dict) -> int | None:
    """
    尝试匹配当前 augments.json 中的条目。
    返回匹配的 index (在 current_augs 中的位置)，或 None。
    """
    key = wiki_name_en.strip().lower()

    # 1. name_en 精确匹配
    if key in index["by_name_en"]:
        return index["by_name_en"][key]

    # 2. aliases 匹配
    if key in index["by_alias"]:
        return index["by_alias"][key]

    # 3. id 匹配
    wiki_id = make_id(wiki_name_en)
    if wiki_id in index["by_id"]:
        return index["by_id"][wiki_id]

    return None


# ---------------------------------------------------------------------------
# 别名自动生成
# ---------------------------------------------------------------------------

def generate_aliases(name_en: str) -> list[str]:
    """从英文名生成基础别名列表。"""
    aliases = []
    lower = name_en.lower()
    aliases.append(lower)

    # 去空格
    no_space = lower.replace(" ", "")
    if no_space != lower:
        aliases.append(no_space)

    # 首字母缩写 (每个单词首字母)
    words = name_en.split()
    if len(words) >= 2:
        abbr = "".join(w[0].lower() for w in words if w)
        if len(abbr) >= 2:
            aliases.append(abbr)

    return aliases


# ---------------------------------------------------------------------------
# Tags 推断
# ---------------------------------------------------------------------------

def infer_tags(effect_en: str, tier: str) -> list[str]:
    """从效果描述推断 tags。"""
    tags = []
    e = effect_en.lower()

    if any(k in e for k in ["damage", "deal", "deals"]):
        tags.append("damage")
    if any(k in e for k in ["heal", "shield", "restore"]):
        tags.append("utility")
    if any(k in e for k in ["armor", "magic resistance", "resist"]):
        tags.append("tank")
    if any(k in e for k in ["attack speed", "attack damage"]):
        tags.append("attack")
    if any(k in e for k in ["movement speed", "dash", "blink"]):
        tags.append("mobility")
    if any(k in e for k in ["cooldown", "ability haste"]):
        tags.append("ability")
    if any(k in e for k in ["true damage", "execute", "takedown"]):
        tags.append("execute")
    if any(k in e for k in ["burn", "poison", "bleed", "over time"]):
        tags.append("dot")
    if any(k in e for k in ["root", "slow", "stun", "immobiliz"]):
        tags.append("cc")

    if not tags:
        tags.append("utility")

    return tags


# ---------------------------------------------------------------------------
# 主逻辑
# ---------------------------------------------------------------------------

def main() -> int:
    print("=" * 64)
    print("  真实增强数据导入审计")
    print("  来源: LoL Wiki Module:MayhemAugmentData")
    print("=" * 64)

    # ---- 1. 拉取 Wiki 数据 ----
    print("\n[1/5] 拉取 Wiki Module 数据...")
    try:
        req = urllib.request.Request(WIKI_MODULE_URL, headers={"User-Agent": "aram-insight-sync/1.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            api_data = json.loads(resp.read().decode("utf-8"))
        wikitext = api_data.get("parse", {}).get("wikitext", {}).get("*", "")
        if not wikitext:
            print("[错误] Wiki API 返回空数据")
            return 1
        print(f"  ✓ 获取 {len(wikitext)} 字符的 Lua module 数据")
    except Exception as e:
        print(f"[错误] 无法拉取 Wiki 数据: {e}")
        # 尝试使用本地缓存
        cache = OUTPUT_DIR / "wiki_module_raw.txt"
        if cache.exists():
            print(f"  ℹ 使用本地缓存: {cache}")
            wikitext = cache.read_text(encoding="utf-8")
        else:
            return 1

    # ---- 2. 解析 Lua 数据 ----
    print("\n[2/5] 解析增强数据...")
    wiki_augs = parse_lua_augments(wikitext)
    if not wiki_augs:
        print("[错误] 未解析到任何增强条目")
        return 1
    print(f"  ✓ 解析到 {len(wiki_augs)} 个增强")

    tier_counts = {}
    for wa in wiki_augs:
        t = wa["tier_raw"]
        tier_counts[t] = tier_counts.get(t, 0) + 1
    for t, c in sorted(tier_counts.items()):
        print(f"    {t}: {c}")

    # ---- 3. 加载当前 augments.json ----
    print("\n[3/5] 加载当前 augments.json...")
    with open(AUGMENTS_PATH, encoding="utf-8") as f:
        current_augs = json.load(f)
    print(f"  ✓ 当前 {len(current_augs)} 个增强")

    # ---- 4. 匹配与生成候选 ----
    print("\n[4/5] 匹配与生成候选...")
    index = build_match_index(current_augs)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    candidates = []
    matched_existing = []
    new_candidates = []
    tier_changed = []
    effect_changed = []
    missing_zh = []

    # 记录已匹配的当前增强索引
    matched_current_indices = set()

    for wa in wiki_augs:
        wiki_name_en = wa["name_en"]
        wiki_tier = normalize_tier(wa["tier_raw"])
        wiki_effect = wa["effect_en_raw"]
        aug_id = make_id(wiki_name_en)
        aliases = generate_aliases(wiki_name_en)
        tags = infer_tags(wiki_effect, wiki_tier)

        match_idx = find_match(wiki_name_en, index)

        if match_idx is not None:
            # 匹配到当前增强
            matched_current_indices.add(match_idx)
            existing = current_augs[match_idx]
            matched_existing.append({
                "wiki_name_en": wiki_name_en,
                "current_name": existing.get("name", ""),
                "current_name_en": existing.get("name_en", ""),
                "current_id": existing.get("id", ""),
            })

            # 沿用中文名
            zh_name = existing.get("name", "")
            loc_status = "ok" if zh_name and zh_name != wiki_name_en else "missing_zh"

            # 检查 tier 变化
            existing_tier = existing.get("tier", existing.get("rar", "unknown"))
            # tier 中 prismatic 对应 wiki 的 Prismatic
            if existing_tier not in (wiki_tier, "unknown") and wiki_tier != "unknown":
                tier_changed.append({
                    "name_en": wiki_name_en,
                    "current_tier": existing_tier,
                    "wiki_tier": wiki_tier,
                })

            # 检查 effect 变化
            existing_effect = existing.get("effect", existing.get("desc", ""))
            if existing_effect and wiki_effect:
                # 简单比较：去掉空格后长度差异超过 50% 就标记
                e1 = existing_effect.replace(" ", "")
                e2 = wiki_effect.replace(" ", "")
                if len(e1) > 0 and len(e2) > 0:
                    ratio = abs(len(e1) - len(e2)) / max(len(e1), len(e2))
                    if ratio > 0.5:
                        effect_changed.append({
                            "name_en": wiki_name_en,
                            "current_effect_preview": existing_effect[:80],
                            "wiki_effect_preview": wiki_effect[:80],
                        })

            # 合并别名（保留现有别名 + 新别名）
            existing_aliases = existing.get("aliases", [])
            merged_aliases = list(existing_aliases)
            for a in aliases:
                if a not in merged_aliases:
                    merged_aliases.append(a)

        else:
            # 新增强
            zh_name = wiki_name_en  # 暂用英文名
            loc_status = "missing_zh"
            new_candidates.append({
                "name_en": wiki_name_en,
                "tier": wiki_tier,
            })

        if loc_status == "missing_zh":
            missing_zh.append(wiki_name_en)

        # 构造候选记录
        candidate = {
            "id": aug_id,
            "name": zh_name,
            "name_en": wiki_name_en,
            "aliases": aliases if match_idx is None else merged_aliases,
            "tier": wiki_tier,
            "status": "active",
            "effect": existing.get("effect", "") if match_idx is not None else "",
            "effect_en": wiki_effect,
            "tags": tags,
            "patch_added": existing.get("patch_added", "") if match_idx is not None else "",
            "patch_removed": None,
            "source": {
                "type": "lol_wiki_module",
                "url": WIKI_SOURCE_URL,
                "verified_at": today,
            },
            "notes": wa.get("notes_raw", ""),
            "localization_status": loc_status,
            "source_status": "potentially_outdated",
        }

        # 保留当前已有的 gameplay 字段（仅匹配时）
        if match_idx is not None:
            existing = current_augs[match_idx]
            for field in ("rar", "wr", "pr", "desc", "trigger", "best", "avoid", "tests"):
                if field in existing:
                    candidate[field] = existing[field]

        candidates.append(candidate)

    # ---- 检查当前存在但来源中不存在的增强 ----
    possibly_removed = []
    for i, aug in enumerate(current_augs):
        if i not in matched_current_indices:
            possibly_removed.append({
                "id": aug.get("id", ""),
                "name": aug.get("name", ""),
                "name_en": aug.get("name_en", ""),
                "tier": aug.get("tier", aug.get("rar", "unknown")),
                "note": "存在于当前数据但不在 Wiki 来源中，可能是原型数据或已被移除",
            })

    # ---- 检查 alias 冲突 ----
    alias_conflicts = []
    alias_map = {}
    for c in candidates:
        for a in c.get("aliases", []):
            al = a.lower()
            if al in alias_map and alias_map[al] != c["name_en"]:
                alias_conflicts.append({
                    "alias": a,
                    "conflict_between": [alias_map[al], c["name_en"]],
                })
            else:
                alias_map[al] = c["name_en"]

    # ---- 5. 写入输出文件 ----
    print("\n[5/5] 写入输出文件...")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with open(CANDIDATES_PATH, "w", encoding="utf-8") as f:
        json.dump(candidates, f, ensure_ascii=False, indent=2)
    print(f"  ✓ 候选文件: {CANDIDATES_PATH} ({len(candidates)} 条)")

    diff_report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_url": WIKI_SOURCE_URL,
        "source_status": "potentially_outdated — Wiki 页面可能标注 WIP/outdated",
        "existing_count": len(current_augs),
        "imported_count": len(candidates),
        "matched_existing": len(matched_existing),
        "new_candidates": len(new_candidates),
        "possibly_removed_or_prototype": possibly_removed,
        "tier_changed": tier_changed,
        "effect_changed": effect_changed,
        "alias_conflicts": alias_conflicts,
        "missing_zh": missing_zh,
        "matched_details": matched_existing,
        "new_candidate_details": new_candidates,
    }

    with open(DIFF_PATH, "w", encoding="utf-8") as f:
        json.dump(diff_report, f, ensure_ascii=False, indent=2)
    print(f"  ✓ Diff 报告: {DIFF_PATH}")

    # ---- 汇总 ----
    print("\n" + "=" * 64)
    print("  审计汇总")
    print("=" * 64)
    print(f"  A. Wiki 来源解析增强数     : {len(candidates)}")
    print(f"  B. 当前 augments.json 数量 : {len(current_augs)}")
    print(f"  C. 匹配已有增强数          : {len(matched_existing)}")
    print(f"  D. 新增候选数              : {len(new_candidates)}")
    print(f"  E. 当前存在但来源中不存在  : {len(possibly_removed)}")
    print(f"  F. 缺少中文正式名          : {len(missing_zh)}")
    print(f"  G. Tier 冲突数             : {len(tier_changed)}")
    print(f"  H. Alias 冲突数            : {len(alias_conflicts)}")
    print(f"  I. 是否修改了正式数据      : 否 ✓")
    print("=" * 64)

    if possibly_removed:
        print("\n  ⚠ 以下增强在来源中不存在 (需人工审核):")
        for pr in possibly_removed:
            print(f"    - {pr['name_en']} ({pr['name']}) [{pr['tier']}]")

    if tier_changed:
        print("\n  ⚠ Tier 冲突:")
        for tc in tier_changed:
            print(f"    - {tc['name_en']}: 当前={tc['current_tier']}, Wiki={tc['wiki_tier']}")

    if alias_conflicts:
        print("\n  ⚠ Alias 冲突:")
        for ac in alias_conflicts[:10]:
            print(f"    - '{ac['alias']}' → {ac['conflict_between']}")

    print(f"\n  下一步: 人工审核 {CANDIDATES_PATH} 和 {DIFF_PATH}")
    print(f"  确认后手动合并到 data/augments.json")

    return 0


if __name__ == "__main__":
    sys.exit(main())
