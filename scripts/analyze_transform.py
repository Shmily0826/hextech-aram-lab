"""
分析 synergies.json 的数据结构，聚焦 tier="transform"（质变）组合的分布情况。
"""
import json
import os
from collections import Counter
from statistics import median

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "synergies.json")


def load_data():
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def section(title):
    width = 60
    print()
    print("=" * width)
    print(f"  {title}")
    print("=" * width)


def main():
    data = load_data()
    total = len(data)
    print(f"总条目数: {total}")

    # ── 1. tier 分布 ──────────────────────────────────────────
    section("1. Tier 分布")
    tier_counter = Counter(item.get("t", "<missing>") for item in data)
    for tier, count in tier_counter.most_common():
        pct = count / total * 100
        print(f"  {tier:<20s}  {count:>6d}  ({pct:5.1f}%)")

    # ── 2. transform 条目的 confidence 分布 ───────────────────
    section("2. Transform 条目的 confidence (c) 分布")
    transform_items = [item for item in data if item.get("t") == "transform"]
    if not transform_items:
        print("  没有找到 tier='transform' 的条目。")
        return

    confidences = [item["c"] for item in transform_items if "c" in item]
    confidences_sorted = sorted(confidences)

    print(f"  条目总数:  {len(transform_items)}")
    print(f"  有 c 字段: {len(confidences)}")
    print(f"  最小值:    {min(confidences)}")
    print(f"  最大值:    {max(confidences)}")
    print(f"  平均值:    {sum(confidences) / len(confidences):.2f}")
    print(f"  中位数:    {median(confidences)}")

    # 区间分布
    bins = [
        (0, 10),
        (11, 20),
        (21, 30),
        (31, 40),
        (41, 50),
        (51, 60),
        (61, 70),
        (71, 80),
        (81, 90),
        (91, 100),
    ]
    print()
    print("  区间分布:")
    for lo, hi in bins:
        count = sum(1 for c in confidences if lo <= c <= hi)
        bar = "#" * (count * 40 // max(len(confidences), 1))
        if count > 0 or lo >= 80:
            print(f"    [{lo:>3d} - {hi:>3d}]  {count:>6d}  {bar}")

    # 更细致的顶部区间
    print()
    fine_bins = [
        (90, 90),
        (91, 95),
        (96, 99),
        (100, 100),
    ]
    print("  高分区细分:")
    for lo, hi in fine_bins:
        count = sum(1 for c in confidences if lo <= c <= hi)
        print(f"    [{lo:>3d} - {hi:>3d}]  {count:>6d}")

    # ── 3. Top 20 transform 组合 (按 confidence 降序) ─────────
    section("3. Confidence 最高的 Top 20 Transform 组合")
    top_items = sorted(transform_items, key=lambda x: x.get("c", 0), reverse=True)[:20]
    print(f"  {'#':>3s}  {'英雄 (h)':<16s}  {'海克斯 (a)':<24s}  {'c':>4s}  {'稀有度 (r)':<14s}")
    print(f"  {'---':>3s}  {'--------':<16s}  {'----------':<24s}  {'----':>4s}  {'---------':<14s}")
    for i, item in enumerate(top_items, 1):
        h = item.get("h", "?")
        a = item.get("a", "?")
        c = item.get("c", "?")
        r = item.get("r", "?")
        print(f"  {i:>3d}  {h:<16s}  {a:<24s}  {c:>4}  {r:<14s}")

    # ── 4. Transform 中各稀有度(r)分布 ────────────────────────
    section("4. Transform 中各稀有度 (r) 分布")
    rarity_counter = Counter(item.get("r", "<missing>") for item in transform_items)
    for rarity, count in rarity_counter.most_common():
        pct = count / len(transform_items) * 100
        print(f"  {rarity:<20s}  {count:>6d}  ({pct:5.1f}%)")

    # ── 附加：各稀有度的 confidence 均值 ──────────────────────
    section("附加: 各稀有度的 confidence 均值")
    rarity_conf = {}
    for item in transform_items:
        r = item.get("r", "<missing>")
        if "c" in item:
            rarity_conf.setdefault(r, []).append(item["c"])
    for rarity in sorted(rarity_conf, key=lambda r: -(sum(rarity_conf[r]) / len(rarity_conf[r]))):
        vals = rarity_conf[rarity]
        avg = sum(vals) / len(vals)
        print(f"  {rarity:<20s}  avg={avg:6.2f}  min={min(vals):>3d}  max={max(vals):>3d}  count={len(vals):>5d}")


if __name__ == "__main__":
    main()
