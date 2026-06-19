"""
verify_fix.py - 验证爬虫修复后的数据
读取 pipeline/output/arammayhem_stats_scrape.json 并进行全面数据检查。
"""
import json
import statistics
import os

# ── 路径 ──────────────────────────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
DATA_PATH = os.path.join(PROJECT_ROOT, "pipeline", "output", "arammayhem_stats_scrape.json")

# ── 加载数据 ──────────────────────────────────────────────────────────
with open(DATA_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

matched = data["matched"]
unmatched_scraped = data.get("unmatched_scraped", [])
unmatched_local = data.get("unmatched_local", [])

SEP = "=" * 72

print(SEP)
print("  ARAM MAYHEM 爬虫数据验证报告")
print(SEP)
print(f"  数据来源:   {data['source']}")
print(f"  抓取时间:   {data['scraped_at']}")
print(f"  总抓取数:   {data['total_scraped']}")
print(f"  匹配成功:   {data['total_matched']}")
print(f"  未匹配(爬): {data['total_unmatched_scraped']}")
print(f"  未匹配(本): {data['total_unmatched_local']}")
print(SEP)

# ── 过滤有效 win_rate ─────────────────────────────────────────────────
valid = [a for a in matched if a.get("win_rate") is not None]
no_wr = [a for a in matched if a.get("win_rate") is None]
win_rates = [a["win_rate"] for a in valid]

# ── 1. Top 10 最高 win_rate ──────────────────────────────────────────
top10 = sorted(valid, key=lambda x: x["win_rate"], reverse=True)[:10]
print("\n[TOP 10 最高胜率增强]")
print(f"  {'#':<4} {'名称':<28} {'WinRate':>8} {'PickRate':>9} {'Tier':<10}")
print("  " + "-" * 64)
for i, a in enumerate(top10, 1):
    cn = a.get("name_cn", "")
    en = a.get("name_en", "")
    label = f"{cn} ({en})" if cn else en
    if len(label) > 27:
        label = label[:26] + "…"
    wr = f"{a['win_rate']:.2f}%"
    pr = f"{a['pick_rate']:.2f}%" if a.get("pick_rate") is not None else "N/A"
    tier = a.get("tier", "?")
    print(f"  {i:<4} {label:<28} {wr:>8} {pr:>9} {tier:<10}")

# ── 2. Bottom 5 最低 win_rate ────────────────────────────────────────
bot5 = sorted(valid, key=lambda x: x["win_rate"])[:5]
print(f"\n[BOTTOM 5 最低胜率增强]")
print(f"  {'#':<4} {'名称':<28} {'WinRate':>8} {'PickRate':>9} {'Tier':<10}")
print("  " + "-" * 64)
for i, a in enumerate(bot5, 1):
    cn = a.get("name_cn", "")
    en = a.get("name_en", "")
    label = f"{cn} ({en})" if cn else en
    if len(label) > 27:
        label = label[:26] + "…"
    wr = f"{a['win_rate']:.2f}%"
    pr = f"{a['pick_rate']:.2f}%" if a.get("pick_rate") is not None else "N/A"
    tier = a.get("tier", "?")
    print(f"  {i:<4} {label:<28} {wr:>8} {pr:>9} {tier:<10}")

# ── 3. Win Rate 分布统计 ──────────────────────────────────────────────
wr_min = min(win_rates)
wr_max = max(win_rates)
wr_avg = statistics.mean(win_rates)
wr_med = statistics.median(win_rates)
wr_std = statistics.stdev(win_rates) if len(win_rates) > 1 else 0.0

print(f"\n[WIN RATE 分布统计]")
print(f"  最小值:  {wr_min:.2f}%")
print(f"  最大值:  {wr_max:.2f}%")
print(f"  平均值:  {wr_avg:.2f}%")
print(f"  中位数:  {wr_med:.2f}%")
print(f"  标准差:  {wr_std:.2f}%")
print(f"  有效条目: {len(win_rates)} / {len(matched)}")
if no_wr:
    print(f"  无胜率条目 ({len(no_wr)}):")
    for a in no_wr:
        print(f"    - {a.get('name_cn','?')} ({a.get('name_en','?')}), tier={a.get('tier','?')}")

# ── 4. 特别检查指定增强 ──────────────────────────────────────────────
TARGETS = {
    "pursuit-of-haste":       "Pursuit of Haste / 急速之追求",
    "transmute-prismatic":    "Transmute: Prismatic / 质变：棱彩阶",
    "circle-of-death":        "Circle of Death / 死亡之环",
    "windspeakers-blessing":  "Windspeaker's Blessing / 风语者的祝福",
}

print(f"\n[特别检查 - 指定增强数值合理性]")
found_map = {}
for a in matched:
    slug = a.get("slug", "")
    if slug in TARGETS:
        found_map[slug] = a

for slug, expected_label in TARGETS.items():
    print(f"\n  >>> {expected_label}")
    if slug in found_map:
        a = found_map[slug]
        wr = a["win_rate"]
        pr = a.get("pick_rate")
        tier = a.get("tier", "?")
        rank = a.get("rank", "?")
        match_method = a.get("match_method", "?")

        print(f"      slug:         {slug}")
        print(f"      name_cn:      {a.get('name_cn', 'MISSING')}")
        print(f"      name_en:      {a.get('name_en', 'MISSING')}")
        print(f"      tier:         {tier}")
        print(f"      rank:         {rank}")
        print(f"      win_rate:     {wr:.2f}%" if wr is not None else "      win_rate:     None")
        print(f"      pick_rate:    {pr:.2f}%" if pr is not None else "      pick_rate:    None")
        print(f"      match_method: {match_method}")

        # 合理性判断
        issues = []
        if wr is None:
            issues.append("win_rate 为 None (缺失)")
        elif wr < 30 or wr > 80:
            issues.append(f"win_rate={wr:.2f}% 超出合理范围 [30, 80]")
        if pr is None:
            issues.append("pick_rate 为 None (缺失)")
        elif pr < 0 or pr > 100:
            issues.append(f"pick_rate={pr:.2f}% 超出合理范围 [0, 100]")
        if not a.get("name_cn"):
            issues.append("name_cn 为空")
        if not a.get("name_en"):
            issues.append("name_en 为空")
        if tier not in ("gold", "silver", "prismatic"):
            issues.append(f"tier='{tier}' 不是预期值")

        if issues:
            for iss in issues:
                print(f"      [WARN] {iss}")
        else:
            print(f"      [OK] 数值均在合理范围内")
    else:
        print(f"      [ERROR] 未在 matched 数据中找到 (slug={slug})")
        # 检查是否在 unmatched 中
        for u in unmatched_local:
            if slug.replace("-", "_") == u.get("id", ""):
                print(f"      [INFO] 在 unmatched_local 中找到: {u.get('name','?')} ({u.get('name_en','?')})")
        for u in unmatched_scraped:
            if slug == u.get("slug", ""):
                print(f"      [INFO] 在 unmatched_scraped 中找到: {u.get('name_en','?')}")

# ── 5. 未匹配条目汇总 ────────────────────────────────────────────────
if unmatched_scraped:
    print(f"\n[未匹配 - 爬取端 ({len(unmatched_scraped)})]")
    for u in unmatched_scraped:
        print(f"  - slug={u.get('slug','?')}, name={u.get('name_en','?')} / {u.get('name_cn','?')}, tier={u.get('tier','?')}")

if unmatched_local:
    print(f"\n[未匹配 - 本地端 ({len(unmatched_local)})]")
    for u in unmatched_local:
        print(f"  - id={u.get('id','?')}, name={u.get('name_en','?')} / {u.get('name','?')}, tier={u.get('tier','?')}")

# ── 总结 ──────────────────────────────────────────────────────────────
print(f"\n{SEP}")
total_issues = 0
if no_wr:
    total_issues += len(no_wr)
if unmatched_scraped:
    total_issues += len(unmatched_scraped)
if unmatched_local:
    total_issues += len(unmatched_local)
wr_outliers = [a for a in valid if a["win_rate"] < 30 or a["win_rate"] > 80]
if wr_outliers:
    total_issues += len(wr_outliers)

if total_issues == 0:
    print("  结论: 数据质量良好，未发现异常。")
else:
    print(f"  结论: 共发现 {total_issues} 个需关注的条目，请检查上方详情。")
print(SEP)
