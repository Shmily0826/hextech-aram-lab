#!/usr/bin/env python3
"""展示"精选质变组合"的效果：对高胜率英雄，列出其 transform 组合并按增强胜率排序。"""

import json
import os

# ── 路径 ──────────────────────────────────────────────
BASE_DIR = os.path.join(os.path.dirname(__file__), "..", "data")

CHAMPIONS_PATH = os.path.join(BASE_DIR, "champions.json")
AUGMENTS_PATH = os.path.join(BASE_DIR, "augments.json")
SYNERGIES_PATH = os.path.join(BASE_DIR, "synergies.json")

TOP_N = 5          # 选取胜率最高的 5 个英雄
PICK_THRESHOLD = 30  # 增强胜率 >= 30% 标记为"精选"

# 稀有度中文映射
TIER_CN = {
    "prismatic": "棱彩",
    "gold": "金色",
    "silver": "银色",
}


def load_json(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    # ── 1. 读取数据 ──────────────────────────────────
    champions_data = load_json(CHAMPIONS_PATH)
    augments_list = load_json(AUGMENTS_PATH)
    synergies_list = load_json(SYNERGIES_PATH)

    champions = champions_data["champions"]  # list of dict

    # ── 2. 建立增强 name -> win_rate / tier 映射 ─────
    augment_map = {}  # name -> {"win_rate": float, "tier": str}
    for aug in augments_list:
        augment_map[aug["name"]] = {
            "win_rate": aug.get("win_rate", 0.0),
            "tier": aug.get("tier", "unknown"),
        }

    # ── 3. 选取胜率最高的 5 个英雄 ───────────────────
    sorted_champs = sorted(champions, key=lambda c: c["wr"], reverse=True)
    top_champs = sorted_champs[:TOP_N]

    # ── 4. 为每个英雄获取 transform 组合 ─────────────
    # 按英雄名索引 synergies
    hero_transforms = {}  # hero_name -> [synergy_dict, ...]
    for syn in synergies_list:
        if syn["t"] == "transform":
            hero_transforms.setdefault(syn["h"], []).append(syn)

    # ── 5. 展示结果 ──────────────────────────────────
    print("=" * 60)
    print("         精选质变组合 (Top Picks) 效果展示")
    print("=" * 60)
    print()

    # 全局统计计数器
    total_combos = 0
    ge30_count = 0
    ge40_count = 0
    ge50_count = 0

    for champ in top_champs:
        name = champ["name"]
        wr = champ["wr"]
        tier = champ["tier"]

        combos = hero_transforms.get(name, [])

        # 关联增强胜率
        enriched = []
        for c in combos:
            aug_name = c["a"]
            rarity = c["r"]
            aug_info = augment_map.get(aug_name, {"win_rate": 0.0, "tier": "unknown"})
            aug_wr = aug_info["win_rate"]
            enriched.append({
                "name": aug_name,
                "rarity": rarity,
                "aug_win_rate": aug_wr,
            })

        # 按增强胜率降序排列
        enriched.sort(key=lambda x: x["aug_win_rate"], reverse=True)

        # 输出
        print(f"=== {name} (胜率 {wr:.1f}%, Tier {tier}) ===")

        pick_count = 0
        for item in enriched:
            aug_wr = item["aug_win_rate"]
            rarity_cn = TIER_CN.get(item["rarity"], item["rarity"])

            if aug_wr >= PICK_THRESHOLD:
                tag = "[精选]"
                pick_count += 1
            else:
                tag = "[普通]"

            print(f"  {tag} {item['name']} ({rarity_cn}, 增强胜率 {aug_wr:.1f}%)")

            # 全局统计
            total_combos += 1
            if aug_wr >= 30:
                ge30_count += 1
            if aug_wr >= 40:
                ge40_count += 1
            if aug_wr >= 50:
                ge50_count += 1

        print(f"  精选占比: {pick_count}/{len(enriched)}")
        print()

    # ── 6. 全局统计 ──────────────────────────────────
    print("=" * 60)
    print("全局统计 (以上 5 位英雄的所有 transform 组合)")
    print("=" * 60)
    print(f"  总组合数:              {total_combos}")
    if total_combos > 0:
        print(f"  增强胜率 >= 30%:  {ge30_count:>3} 条  ({ge30_count / total_combos * 100:.1f}%)")
        print(f"  增强胜率 >= 40%:  {ge40_count:>3} 条  ({ge40_count / total_combos * 100:.1f}%)")
        print(f"  增强胜率 >= 50%:  {ge50_count:>3} 条  ({ge50_count / total_combos * 100:.1f}%)")
    else:
        print("  (无数据)")


if __name__ == "__main__":
    main()
