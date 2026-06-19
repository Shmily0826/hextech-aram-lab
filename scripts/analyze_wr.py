# -*- coding: utf-8 -*-
"""
ARAM Insight - Augment Win Rate Deep Analysis
分析增强胜率(win_rate)的数据特征和可能算法
"""

import json
import os
import sys
from statistics import median, mean
from collections import defaultdict

DATA_DIR = os.path.join(os.path.dirname(__file__), os.pardir, "data")
AUGMENTS_FILE = os.path.normpath(os.path.join(DATA_DIR, "augments.json"))
CHAMPIONS_FILE = os.path.normpath(os.path.join(DATA_DIR, "champions.json"))

SEP = "=" * 70


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def section(title):
    print()
    print(SEP)
    print(f"  {title}")
    print(SEP)


# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------
augments = load_json(AUGMENTS_FILE)
champions_data = load_json(CHAMPIONS_FILE)
champions = champions_data["champions"]

# Filter augments that have a numeric win_rate
augments_with_wr = [
    a for a in augments
    if a.get("win_rate") is not None and isinstance(a["win_rate"], (int, float))
]
# Filter augments that also have pick_rate
augments_with_both = [
    a for a in augments_with_wr
    if a.get("pick_rate") is not None and isinstance(a["pick_rate"], (int, float))
]

print(f"总增强数: {len(augments)}")
print(f"有 win_rate 的增强数: {len(augments_with_wr)}")
print(f"同时有 win_rate 和 pick_rate 的增强数: {len(augments_with_both)}")

# ---------------------------------------------------------------------------
# 1. win_rate distribution
# ---------------------------------------------------------------------------
section("1. win_rate 分布统计")

wr_values = [a["win_rate"] for a in augments_with_wr]
wr_min = min(wr_values)
wr_max = max(wr_values)
wr_med = median(wr_values)
wr_avg = mean(wr_values)

print(f"  最小值  : {wr_min:.4f}%")
print(f"  最大值  : {wr_max:.4f}%")
print(f"  中位数  : {wr_med:.4f}%")
print(f"  平均值  : {wr_avg:.4f}%")
print(f"  标准差  : {(sum((x - wr_avg)**2 for x in wr_values) / len(wr_values))**0.5:.4f}%")

# Negative values check
neg_count = sum(1 for v in wr_values if v < 0)
zero_count = sum(1 for v in wr_values if v == 0)
pos_count = sum(1 for v in wr_values if v > 0)
print(f"\n  负值数量: {neg_count}  |  零值数量: {zero_count}  |  正值数量: {pos_count}")

# Bucketed distribution
buckets = [
    ("< -10%", lambda x: x < -10),
    ("-10% ~ -5%", lambda x: -10 <= x < -5),
    ("-5% ~ 0%", lambda x: -5 <= x < 0),
    ("0% (exact)", lambda x: x == 0),
    ("0% ~ 5%", lambda x: 0 < x <= 5),
    ("5% ~ 10%", lambda x: 5 < x <= 10),
    ("10% ~ 15%", lambda x: 10 < x <= 15),
    ("15% ~ 20%", lambda x: 15 < x <= 20),
    ("20% ~ 30%", lambda x: 20 < x <= 30),
    ("30% ~ 40%", lambda x: 30 < x <= 40),
    ("40% ~ 50%", lambda x: 40 < x <= 50),
    ("50% ~ 60%", lambda x: 50 < x <= 60),
    ("> 60%", lambda x: x > 60),
]

print("\n  分段统计 (细粒度):")
print(f"  {'区间':<18} {'数量':>6} {'占比':>8}")
print("  " + "-" * 36)
for label, cond in buckets:
    cnt = sum(1 for v in wr_values if cond(v))
    pct = cnt / len(wr_values) * 100
    bar = "#" * int(pct / 2)
    print(f"  {label:<18} {cnt:>6} {pct:>7.1f}%  {bar}")

# Original coarse buckets requested
print("\n  分段统计 (粗粒度):")
coarse = [
    ("< 10%", lambda x: x < 10),
    ("10% ~ 20%", lambda x: 10 <= x < 20),
    ("20% ~ 30%", lambda x: 20 <= x < 30),
    ("30% ~ 40%", lambda x: 30 <= x < 40),
    ("40% ~ 50%", lambda x: 40 <= x < 50),
    ("50% ~ 60%", lambda x: 50 <= x < 60),
    (">= 60%", lambda x: x >= 60),
]
print(f"  {'区间':<18} {'数量':>6} {'占比':>8}")
print("  " + "-" * 36)
for label, cond in coarse:
    cnt = sum(1 for v in wr_values if cond(v))
    pct = cnt / len(wr_values) * 100
    bar = "#" * int(pct / 2)
    print(f"  {label:<18} {cnt:>6} {pct:>7.1f}%  {bar}")

# ---------------------------------------------------------------------------
# Top 20 by win_rate
# ---------------------------------------------------------------------------
section("1a. win_rate TOP 20 增强")

sorted_desc = sorted(augments_with_wr, key=lambda a: a["win_rate"], reverse=True)
print(f"  {'#':>3}  {'名称':<20} {'name_en':<28} {'win_rate':>9} {'pick_rate':>10} {'tier':<12}")
print("  " + "-" * 92)
for i, a in enumerate(sorted_desc[:20], 1):
    pr = a.get("pick_rate", "-")
    pr_str = f"{pr:.2f}%" if isinstance(pr, (int, float)) else str(pr)
    print(
        f"  {i:>3}  {a['name']:<20} {a['name_en']:<28} "
        f"{a['win_rate']:>8.2f}% {pr_str:>10} {a.get('tier','-'):<12}"
    )

# ---------------------------------------------------------------------------
# Bottom 10 by win_rate
# ---------------------------------------------------------------------------
section("1b. win_rate BOTTOM 10 增强")

sorted_asc = sorted(augments_with_wr, key=lambda a: a["win_rate"])
print(f"  {'#':>3}  {'名称':<20} {'name_en':<28} {'win_rate':>9} {'pick_rate':>10} {'tier':<12}")
print("  " + "-" * 92)
for i, a in enumerate(sorted_asc[:10], 1):
    pr = a.get("pick_rate", "-")
    pr_str = f"{pr:.2f}%" if isinstance(pr, (int, float)) else str(pr)
    print(
        f"  {i:>3}  {a['name']:<20} {a['name_en']:<28} "
        f"{a['win_rate']:>8.2f}% {pr_str:>10} {a.get('tier','-'):<12}"
    )

# ---------------------------------------------------------------------------
# 2. win_rate vs pick_rate correlation
# ---------------------------------------------------------------------------
section("2. win_rate 与 pick_rate 相关性分析")

wr_list = [a["win_rate"] for a in augments_with_both]
pr_list = [a["pick_rate"] for a in augments_with_both]

n = len(wr_list)
wr_mean = mean(wr_list)
pr_mean = mean(pr_list)

# Pearson correlation coefficient
numerator = sum((w - wr_mean) * (p - pr_mean) for w, p in zip(wr_list, pr_list))
denom_wr = sum((w - wr_mean) ** 2 for w in wr_list) ** 0.5
denom_pr = sum((p - pr_mean) ** 2 for p in pr_list) ** 0.5
pearson = numerator / (denom_wr * denom_pr) if (denom_wr * denom_pr) != 0 else 0

print(f"  样本数: {n}")
print(f"  win_rate 均值: {wr_mean:.4f}%  |  pick_rate 均值: {pr_mean:.4f}%")
print(f"  Pearson 相关系数: {pearson:.4f}")

if pearson > 0.5:
    corr_desc = "强正相关 — 高选取率倾向于伴随高胜率"
elif pearson > 0.2:
    corr_desc = "弱正相关 — 略有正向关系"
elif pearson > -0.2:
    corr_desc = "几乎不相关 — 胜率和选取率独立"
elif pearson > -0.5:
    corr_desc = "弱负相关 — 高选取率略伴随低胜率"
else:
    corr_desc = "强负相关 — 高选取率倾向于伴随低胜率"
print(f"  解读: {corr_desc}")

# Group by pick_rate quartiles
pr_sorted_vals = sorted(pr_list)
q1 = pr_sorted_vals[n // 4]
q2 = pr_sorted_vals[n // 2]
q3 = pr_sorted_vals[3 * n // 4]

print(f"\n  pick_rate 四分位: Q1={q1:.2f}%  Q2={q2:.2f}%  Q3={q3:.2f}%")

quartile_groups = [
    ("Q1 (最低25%选取率)", lambda p: p <= q1),
    ("Q2 (25-50%)", lambda p: q1 < p <= q2),
    ("Q3 (50-75%)", lambda p: q2 < p <= q3),
    ("Q4 (最高25%选取率)", lambda p: p > q3),
]

print(f"\n  各选取率分位段的平均胜率:")
print(f"  {'分位段':<25} {'增强数':>6} {'平均win_rate':>14} {'中位win_rate':>14}")
print("  " + "-" * 64)
for label, cond in quartile_groups:
    group_wr = [a["win_rate"] for a in augments_with_both if cond(a["pick_rate"])]
    if group_wr:
        print(
            f"  {label:<25} {len(group_wr):>6} "
            f"{mean(group_wr):>13.2f}% {median(group_wr):>13.2f}%"
        )

# Top 10 most picked augments - what are their win rates?
section("2a. 最高选取率 TOP 10 的增强胜率")
by_pr = sorted(augments_with_both, key=lambda a: a["pick_rate"], reverse=True)
print(f"  {'名称':<20} {'pick_rate':>10} {'win_rate':>9} {'tier':<12}")
print("  " + "-" * 56)
for a in by_pr[:10]:
    print(
        f"  {a['name']:<20} {a['pick_rate']:>9.2f}% "
        f"{a['win_rate']:>8.2f}% {a.get('tier','-'):<12}"
    )

# ---------------------------------------------------------------------------
# 3. Is win_rate "relative lift" or "absolute win rate"?
# ---------------------------------------------------------------------------
section("3. win_rate 含义分析：绝对胜率 vs 相对提升")

print("\n  [关键观察]")
above_50 = sum(1 for v in wr_values if v > 50)
above_60 = sum(1 for v in wr_values if v > 60)
below_10 = sum(1 for v in wr_values if v < 10)
near_50 = sum(1 for v in wr_values if 45 <= v <= 55)

print(f"  win_rate > 50% 的数量 : {above_50} / {len(wr_values)} ({above_50/len(wr_values)*100:.1f}%)")
print(f"  win_rate > 60% 的数量 : {above_60} / {len(wr_values)} ({above_60/len(wr_values)*100:.1f}%)")
print(f"  win_rate < 10% 的数量 : {below_10} / {len(wr_values)} ({below_10/len(wr_values)*100:.1f}%)")
print(f"  win_rate 在 45-55% 范围: {near_50} / {len(wr_values)} ({near_50/len(wr_values)*100:.1f}%)")

print("\n  [判断逻辑]")
if wr_max < 60 and near_50 / len(wr_values) < 0.3:
    print("  - 所有 win_rate < 60%，且不集中在50%附近")
    print("  - 这【不是】传统意义上的'英雄胜率'(absolute win rate)")
    print("  - 传统英雄胜率应集中在 45-55% 附近，且最高一般不超过 60%")
elif wr_max < 60 and near_50 / len(wr_values) >= 0.3:
    print("  - 所有 win_rate < 60%，且大量集中在50%附近")
    print("  - 这可能是传统意义上的'英雄胜率'")
else:
    print(f"  - win_rate 最大值 = {wr_max:.2f}%，超过60%")
    if near_50 / len(wr_values) < 0.3:
        print("  - 但数据不集中在50%附近")

if wr_min < 0:
    print(f"  - 存在负的 win_rate (最小={wr_min:.2f}%)，这强烈暗示是'胜率变化量'(win rate delta/lift)")
    print("    绝对胜率不可能为负值")

print(f"\n  [可能的算法推测]")
print(f"  数据范围: {wr_min:.2f}% ~ {wr_max:.2f}%，跨度 = {wr_max - wr_min:.2f}%")
print(f"  中位数 = {wr_med:.2f}%，均值 = {wr_avg:.2f}%")
print()
print("  假设1: 胜率提升百分比 (Win Rate Lift %)")
print("    含义: 选取该增强后，相对于不选该增强时的胜率提升百分比")
print("    例如: win_rate=12% 表示选该增强比不选时胜率高12个百分点")
print("    合理范围: 通常 -15% ~ +25%，当前数据范围基本符合")
print()
print("  假设2: 增强胜率差值 (Augment WR - Baseline WR)")
print("    含义: 使用该增强的英雄胜率 - 该英雄的基础胜率")
print("    这是假设1的具体实现方式，数值上等价")
print()
print("  假设3: 标准化胜率 (Normalized WR, 以50%为基准的偏移)")
print("    含义: win_rate = actual_wr - 50%")
print("    问题: 如果是这样，中位数应接近0，但当前中位数=" + f"{wr_med:.2f}%")

# ---------------------------------------------------------------------------
# 4. Source field analysis
# ---------------------------------------------------------------------------
section("4. 增强条目完整字段及 source 分析")

# Show 3 complete augment entries
print("\n  [3个完整增强条目示例]")
for i, a in enumerate(augments[:3]):
    print(f"\n  --- 增强 #{i+1}: {a['name']} ({a['name_en']}) ---")
    for k, v in a.items():
        print(f"    {k:<18}: {v}")

# Analyze source field patterns
print("\n\n  [source 字段分析]")
source_types = defaultdict(int)
stats_sources = defaultdict(int)
for a in augments:
    src = a.get("source", {})
    src_type = src.get("type", "N/A") if isinstance(src, dict) else str(src)
    source_types[src_type] += 1
    ss = a.get("stats_source", "N/A")
    stats_sources[ss] += 1

print("  source.type 分布:")
for t, cnt in source_types.items():
    print(f"    {t}: {cnt}")

print("\n  stats_source 分布:")
for t, cnt in stats_sources.items():
    print(f"    {t}: {cnt}")

# Check for any other wr-related fields
print("\n  [检查是否有其他胜率相关字段]")
all_keys = set()
for a in augments:
    all_keys.update(a.keys())
wr_related = [k for k in all_keys if "wr" in k.lower() or "win" in k.lower() or "rate" in k.lower()]
print(f"  所有字段名: {sorted(all_keys)}")
print(f"  含 'wr/win/rate' 的字段: {wr_related}")

# ---------------------------------------------------------------------------
# 5. Champions win_rate comparison
# ---------------------------------------------------------------------------
section("5. 英雄胜率(hero wr)分布对比")

hero_wr_values = [c["wr"] for c in champions if c.get("wr") is not None and isinstance(c["wr"], (int, float))]
hero_pr_values = [c["pr"] for c in champions if c.get("pr") is not None and isinstance(c["pr"], (int, float))]

if hero_wr_values:
    hwr_min = min(hero_wr_values)
    hwr_max = max(hero_wr_values)
    hwr_med = median(hero_wr_values)
    hwr_avg = mean(hero_wr_values)

    print(f"  英雄总数 (有 wr 数据): {len(hero_wr_values)}")
    print(f"  英雄 wr 最小值 : {hwr_min:.4f}%")
    print(f"  英雄 wr 最大值 : {hwr_max:.4f}%")
    print(f"  英雄 wr 中位数 : {hwr_med:.4f}%")
    print(f"  英雄 wr 平均值 : {hwr_avg:.4f}%")

    print(f"\n  英雄 wr 分布:")
    hero_wr_buckets = [
        ("< 40%", lambda x: x < 40),
        ("40-45%", lambda x: 40 <= x < 45),
        ("45-48%", lambda x: 45 <= x < 48),
        ("48-50%", lambda x: 48 <= x < 50),
        ("50-52%", lambda x: 50 <= x < 52),
        ("52-55%", lambda x: 52 <= x < 55),
        ("55-60%", lambda x: 55 <= x < 60),
        (">= 60%", lambda x: x >= 60),
    ]
    print(f"  {'区间':<12} {'数量':>6} {'占比':>8}")
    print("  " + "-" * 30)
    for label, cond in hero_wr_buckets:
        cnt = sum(1 for v in hero_wr_values if cond(v))
        pct = cnt / len(hero_wr_values) * 100
        bar = "#" * int(pct / 2)
        print(f"  {label:<12} {cnt:>6} {pct:>7.1f}%  {bar}")

    # Top 5 / Bottom 5 heroes
    champ_sorted = sorted(
        [c for c in champions if c.get("wr") is not None],
        key=lambda c: c["wr"],
        reverse=True
    )
    print(f"\n  英雄 wr TOP 5:")
    for c in champ_sorted[:5]:
        print(f"    {c['name']:<12} wr={c['wr']:.2f}%  pr={c.get('pr','-')}%")
    print(f"\n  英雄 wr BOTTOM 5:")
    for c in champ_sorted[-5:]:
        print(f"    {c['name']:<12} wr={c['wr']:.2f}%  pr={c.get('pr','-')}%")

    print(f"\n  [英雄胜率 vs 增强胜率对比]")
    print(f"                    {'英雄 wr':<15} {'增强 win_rate':<15}")
    print(f"  {'最小值':<10} {hwr_min:>10.2f}%    {wr_min:>10.2f}%")
    print(f"  {'最大值':<10} {hwr_max:>10.2f}%    {wr_max:>10.2f}%")
    print(f"  {'中位数':<10} {hwr_med:>10.2f}%    {wr_med:>10.2f}%")
    print(f"  {'平均值':<10} {hwr_avg:>10.2f}%    {wr_avg:>10.2f}%")

    range_ratio = (wr_max - wr_min) / (hwr_max - hwr_min) if (hwr_max - hwr_min) != 0 else float('inf')
    print(f"\n  增强胜率跨度: {wr_max - wr_min:.2f}%")
    print(f"  英雄胜率跨度: {hwr_max - hwr_min:.2f}%")
    print(f"  跨度比 (增强/英雄): {range_ratio:.2f}x")

    if (wr_max - wr_min) > (hwr_max - hwr_min) * 3:
        print("\n  结论: 增强胜率跨度远大于英雄胜率跨度")
        print("  这进一步证明增强 win_rate 不是传统的绝对胜率")
    elif abs(wr_min - hwr_min) < 10 and abs(wr_max - hwr_max) < 10:
        print("\n  结论: 增强胜率和英雄胜率范围接近，可能是同一种指标")
    else:
        print("\n  结论: 两个数据范围差异明显，可能是不同类型的指标")

# ---------------------------------------------------------------------------
# Final Summary
# ---------------------------------------------------------------------------
section("综合分析结论")

print("""
  1. 增强 win_rate 的范围和中位数与英雄 wr 有显著差异
     - 英雄 wr 集中在 45-55% 附近 (典型 MOBA 英雄胜率分布)
     - 增强 win_rate 如果偏离此范围，说明不是同类指标

  2. 增强 win_rate 最可能的含义:
     a) 如果是 arammayhem.com 来源: 该站通常展示"胜率变化量"
        (即选取该增强后相比不选时的胜率提升/下降百分比)
     b) 如果是 blitz.gg 来源: 需查看其 API 文档确认

  3. 数据质量检查:
     - 负值的存在强烈暗示是 delta/lift 指标
     - 跨度大小反映的是增强影响力差异
""")

print("\n分析完成。")
