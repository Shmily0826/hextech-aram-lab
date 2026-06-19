#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析 aram-insight 数据中可用于区分"质变组合"价值的信息。
目标：从 2817 条 transform 中筛选出"真正有价值"的组合。
"""

import json
from collections import Counter, defaultdict

DATA = r"D:\CODE\project\aram-insight\data"

# ──────────────────────────────────────────────
# 1. 读取数据
# ──────────────────────────────────────────────
with open(f"{DATA}/champions.json", "r", encoding="utf-8") as f:
    champs_data = json.load(f)
champions = champs_data["champions"]

with open(f"{DATA}/augments.json", "r", encoding="utf-8") as f:
    augments = json.load(f)

with open(f"{DATA}/synergies.json", "r", encoding="utf-8") as f:
    synergies = json.load(f)

with open(f"{DATA}/champion_recs.json", "r", encoding="utf-8") as f:
    recs_data = json.load(f)
recs = recs_data["data"]  # augment_id -> [{h, rarity, grade}]

# 建立索引
aug_by_name = {a["name"]: a for a in augments}
aug_by_id = {a["id"]: a for a in augments}
champ_by_name = {c["name"]: c for c in champions}

transforms = [s for s in synergies if s["t"] == "transform"]
recommends = [s for s in synergies if s["t"] == "recommend"]

print("=" * 70)
print("ARAM Insight - 质变组合价值分析")
print("=" * 70)

# ──────────────────────────────────────────────
# 2. Top 10 胜率英雄
# ──────────────────────────────────────────────
print("\n## 1. Top 10 胜率英雄")
print("-" * 50)
top_champs = sorted(champions, key=lambda x: x["wr"], reverse=True)[:10]
print(f"{'排名':<4} {'英雄':<10} {'胜率':>6} {'选取率':>6} {'Tier':<5} {'角色':<6}")
for i, c in enumerate(top_champs, 1):
    print(f"{i:<4} {c['name']:<10} {c['wr']:>6.2f}% {c['pr']:>6.2f}% {c.get('tier','N/A'):<5} {c.get('role','N/A'):<6}")

# ──────────────────────────────────────────────
# 3. Top 10 胜率增强
# ──────────────────────────────────────────────
print("\n## 2. Top 10 胜率增强")
print("-" * 50)
augs_with_wr = [a for a in augments if a.get("win_rate")]
top_augs = sorted(augs_with_wr, key=lambda x: x["win_rate"], reverse=True)[:10]
print(f"{'排名':<4} {'增强':<14} {'胜率':>6} {'选取率':>6} {'Tier':<10}")
for i, a in enumerate(top_augs, 1):
    print(f"{i:<4} {a['name']:<14} {a['win_rate']:>6.2f}% {a.get('pick_rate',0):>6.2f}% {a['tier']:<10}")

print("\n增强 Tier 分布:")
tier_dist = Counter(a["tier"] for a in augments)
for tier, cnt in sorted(tier_dist.items()):
    has_wr = sum(1 for a in augments if a["tier"] == tier and a.get("win_rate"))
    print(f"  {tier:<12} 总计: {cnt:>3}, 有胜率数据: {has_wr:>3}")

# ──────────────────────────────────────────────
# 4. Top 5 胜率英雄的 transform 组合
# ──────────────────────────────────────────────
print("\n## 3. Top 5 胜率英雄的 transform 组合分析")
print("-" * 50)

top5_names = [c["name"] for c in top_champs[:5]]

for champ_name in top5_names:
    champ = champ_by_name[champ_name]
    champ_transforms = [t for t in transforms if t["h"] == champ_name]

    print(f"\n### {champ_name} (胜率: {champ['wr']}%, Tier: {champ.get('tier','N/A')})")
    print(f"    Transform 数量: {len(champ_transforms)}")

    if not champ_transforms:
        print("    (无 transform 数据)")
        continue

    # 按 rarity 分组
    by_rarity = defaultdict(list)
    for t in champ_transforms:
        by_rarity[t["r"]].append(t)

    for rarity in ["prismatic", "gold", "silver"]:
        items = by_rarity.get(rarity, [])
        if not items:
            continue
        print(f"\n    [{rarity}] ({len(items)} 个):")

        # 对每个 transform，查找增强胜率 和 recs grade
        aug_infos = []
        for t in items:
            aug_name = t["a"]
            aug = aug_by_name.get(aug_name)
            wr = aug.get("win_rate") if aug else None
            pr = aug.get("pick_rate") if aug else None

            # 查找 champion_recs 中的 grade
            grade = None
            for aug_id, rec_list in recs.items():
                for rec in rec_list:
                    if rec["h"] == champ_name:
                        # 需要确认这个 aug_id 对应的 augment name
                        aug_obj = aug_by_id.get(aug_id)
                        if aug_obj and aug_obj["name"] == aug_name:
                            grade = rec["grade"]
                            break
                if grade:
                    break

            aug_infos.append({
                "name": aug_name,
                "wr": wr,
                "pr": pr,
                "grade": grade,
            })

        # 排序：有 grade 的优先，然后按胜率
        aug_infos.sort(key=lambda x: (
            0 if x["grade"] == "S" else 1 if x["grade"] == "A" else 2,
            -(x["wr"] or 0),
        ))

        for info in aug_infos:
            wr_str = f"wr={info['wr']:.1f}%" if info["wr"] else "wr=N/A"
            pr_str = f"pr={info['pr']:.1f}%" if info["pr"] else ""
            grade_str = f"Grade={info['grade']}" if info["grade"] else "Grade=--"
            print(f"      {info['name']:<14} {wr_str:>10} {pr_str:>10} {grade_str}")

# ──────────────────────────────────────────────
# 5. champion_recs.json 分析
# ──────────────────────────────────────────────
print("\n\n## 4. champion_recs.json 推荐等级分析")
print("-" * 50)

all_grades = []
for aug_id, rec_list in recs.items():
    for rec in rec_list:
        all_grades.append(rec["grade"])

grade_dist = Counter(all_grades)
print(f"推荐等级总分布: {dict(grade_dist)}")
print(f"总推荐条数: {len(all_grades)}")
print(f"覆盖增强数: {len(recs)}")
print(f"覆盖英雄数: {recs_data.get('champion_count', 'N/A')}")

# 构建反向索引: (champion, augment_name) -> grade
champ_aug_grade = {}
for aug_id, rec_list in recs.items():
    aug_obj = aug_by_id.get(aug_id)
    if not aug_obj:
        continue
    aug_name = aug_obj["name"]
    for rec in rec_list:
        champ_aug_grade[(rec["h"], aug_name)] = rec["grade"]

print(f"\n(champion, augment) grade 映射条数: {len(champ_aug_grade)}")

# 展示几个英雄的推荐
print("\n### 示例: 部分英雄在某增强下的推荐等级")
sample_augs = list(recs.keys())[:5]
for aug_id in sample_augs:
    aug_obj = aug_by_id.get(aug_id)
    aug_name = aug_obj["name"] if aug_obj else aug_id
    rec_list = recs[aug_id]
    s_count = sum(1 for r in rec_list if r["grade"] == "S")
    a_count = sum(1 for r in rec_list if r["grade"] == "A")
    print(f"  {aug_name}: {len(rec_list)} 英雄 (S={s_count}, A={a_count})")
    # 列出 S 级英雄（前5）
    s_champs = [r["h"] for r in rec_list if r["grade"] == "S"][:5]
    if s_champs:
        print(f"    S级英雄(前5): {', '.join(s_champs)}")

# ──────────────────────────────────────────────
# 6. 关键交叉分析: transform 与 recs 的匹配率
# ──────────────────────────────────────────────
print("\n\n## 5. Transform 与 Recs 交叉分析 (核心)")
print("-" * 50)

matched = 0
unmatched = 0
match_grades = Counter()
for t in transforms:
    key = (t["h"], t["a"])
    if key in champ_aug_grade:
        matched += 1
        match_grades[champ_aug_grade[key]] += 1
    else:
        unmatched += 1

print(f"Transform 总数: {len(transforms)}")
print(f"  在 recs 中有匹配: {matched} ({matched/len(transforms)*100:.1f}%)")
print(f"  在 recs 中无匹配: {unmatched} ({unmatched/len(transforms)*100:.1f}%)")
print(f"  匹配中的 grade 分布: {dict(match_grades)}")

# 进一步：看无匹配的 transform 特征
print("\n### 无匹配 transform 的 rarity 分布:")
unmatched_rarity = Counter()
for t in transforms:
    if (t["h"], t["a"]) not in champ_aug_grade:
        unmatched_rarity[t["r"]] += 1
for r, c in sorted(unmatched_rarity.items()):
    print(f"  {r}: {c}")

# ──────────────────────────────────────────────
# 7. 可用的价值区分维度汇总
# ──────────────────────────────────────────────
print("\n\n## 6. 可用于区分质变组合价值的维度汇总")
print("=" * 70)

# 维度 A: augment 胜率
has_wr_transforms = 0
for t in transforms:
    aug = aug_by_name.get(t["a"])
    if aug and aug.get("win_rate"):
        has_wr_transforms += 1
print(f"\n[A] 增强胜率 (augments.json win_rate)")
print(f"    有胜率数据的 transform: {has_wr_transforms}/{len(transforms)} ({has_wr_transforms/len(transforms)*100:.1f}%)")

# 胜率分布
wr_vals = []
for t in transforms:
    aug = aug_by_name.get(t["a"])
    if aug and aug.get("win_rate"):
        wr_vals.append(aug["win_rate"])
if wr_vals:
    wr_vals.sort()
    print(f"    胜率范围: {min(wr_vals):.2f}% - {max(wr_vals):.2f}%")
    print(f"    胜率中位数: {wr_vals[len(wr_vals)//2]:.2f}%")
    # 分段
    brackets = [(0, 10), (10, 20), (20, 30), (30, 40), (40, 50), (50, 100)]
    print(f"    胜率分段分布:")
    for lo, hi in brackets:
        cnt = sum(1 for w in wr_vals if lo <= w < hi)
        print(f"      [{lo:>2}%, {hi:>3}%): {cnt:>4} 条")

# 维度 B: recs grade
print(f"\n[B] 推荐等级 (champion_recs.json grade)")
print(f"    有 grade 的 transform: {matched}/{len(transforms)} ({matched/len(transforms)*100:.1f}%)")
print(f"    Grade 分布: {dict(match_grades)}")

# 维度 C: augment rarity
print(f"\n[C] 增强稀有度 (synergies.json r)")
rarity_dist = Counter(t["r"] for t in transforms)
for r, c in sorted(rarity_dist.items()):
    print(f"    {r}: {c} ({c/len(transforms)*100:.1f}%)")

# 维度 D: 英雄胜率
print(f"\n[D] 英雄胜率 (champions.json wr)")
champ_wr_map = {c["name"]: c["wr"] for c in champions}
t_champ_wrs = [champ_wr_map.get(t["h"], 0) for t in transforms]
t_champ_wrs_valid = [w for w in t_champ_wrs if w > 0]
if t_champ_wrs_valid:
    print(f"    英雄胜率范围: {min(t_champ_wrs_valid):.2f}% - {max(t_champ_wrs_valid):.2f}%")
    brackets2 = [(40, 45), (45, 48), (48, 50), (50, 52), (52, 55), (55, 60)]
    print(f"    英雄胜率分段分布:")
    for lo, hi in brackets2:
        cnt = sum(1 for w in t_champ_wrs_valid if lo <= w < hi)
        print(f"      [{lo:>2}%, {hi:>2}%): {cnt:>4} 条")

# 维度 E: 英雄 tier
print(f"\n[E] 英雄 Tier (champions.json tier)")
champ_tier_map = {c["name"]: c.get("tier", "N/A") for c in champions}
tier_dist_t = Counter(champ_tier_map.get(t["h"], "N/A") for t in transforms)
for tier, cnt in sorted(tier_dist_t.items()):
    print(f"    Tier {tier}: {cnt} ({cnt/len(transforms)*100:.1f}%)")

# ──────────────────────────────────────────────
# 8. 综合评分方案提议
# ──────────────────────────────────────────────
print("\n\n## 7. 综合评分方案示例")
print("=" * 70)
print("""
提出以下多维度打分方案，用于筛选"真正有价值"的质变组合:

  分数 = w1 * augment_win_rate_score
       + w2 * rec_grade_score
       + w3 * champion_win_rate_score
       + w4 * rarity_score

各维度评分规则:
  - augment_win_rate_score: 增强自身胜率 (0-100 分)
      >=40%: 100, >=30%: 80, >=20%: 60, >=10%: 40, <10%: 20, 无数据: 0
  - rec_grade_score: 推荐等级 (0-100 分)
      S: 100, A: 60, 无匹配: 0
  - champion_win_rate_score: 英雄胜率 (0-100 分)
      >=55%: 100, >=52%: 80, >=50%: 60, >=48%: 40, <48%: 20
  - rarity_score: 增强稀有度 (0-100 分)
      prismatic: 100, gold: 60, silver: 30

建议权重: w1=0.35, w2=0.35, w3=0.15, w4=0.15
""")

# 实际打分并排名
scored = []
for t in transforms:
    aug = aug_by_name.get(t["a"])
    aug_wr = aug.get("win_rate") if aug else None
    champ = champ_by_name.get(t["h"])
    champ_wr = champ.get("wr") if champ else None
    grade = champ_aug_grade.get((t["h"], t["a"]))

    # augment win rate score
    if aug_wr is not None:
        if aug_wr >= 40:
            awr_score = 100
        elif aug_wr >= 30:
            awr_score = 80
        elif aug_wr >= 20:
            awr_score = 60
        elif aug_wr >= 10:
            awr_score = 40
        else:
            awr_score = 20
    else:
        awr_score = 0

    # rec grade score
    if grade == "S":
        grade_score = 100
    elif grade == "A":
        grade_score = 60
    else:
        grade_score = 0

    # champion win rate score
    if champ_wr is not None:
        if champ_wr >= 55:
            cwr_score = 100
        elif champ_wr >= 52:
            cwr_score = 80
        elif champ_wr >= 50:
            cwr_score = 60
        elif champ_wr >= 48:
            cwr_score = 40
        else:
            cwr_score = 20
    else:
        cwr_score = 0

    # rarity score
    rarity_map = {"prismatic": 100, "gold": 60, "silver": 30}
    rar_score = rarity_map.get(t["r"], 0)

    total = 0.35 * awr_score + 0.35 * grade_score + 0.15 * cwr_score + 0.15 * rar_score

    scored.append({
        "champion": t["h"],
        "augment": t["a"],
        "rarity": t["r"],
        "aug_wr": aug_wr,
        "grade": grade,
        "champ_wr": champ_wr,
        "total": total,
    })

scored.sort(key=lambda x: x["total"], reverse=True)

# 分数分布
scores = [s["total"] for s in scored]
print(f"分数范围: {min(scores):.1f} - {max(scores):.1f}")
print(f"分数中位数: {sorted(scores)[len(scores)//2]:.1f}")
print(f"分数平均值: {sum(scores)/len(scores):.1f}")

score_brackets = [(80, 100), (60, 80), (40, 60), (20, 40), (0, 20)]
print("\n分数分段分布:")
for lo, hi in score_brackets:
    cnt = sum(1 for s in scores if lo <= s < hi + (1 if hi == 100 else 0))
    print(f"  [{lo:>2}, {hi:>3}]: {cnt:>4} 条 ({cnt/len(scored)*100:.1f}%)")

print("\n### Top 20 最有价值的质变组合:")
print(f"{'排名':<4} {'英雄':<10} {'增强':<14} {'稀有度':<10} {'增强WR':>7} {'Grade':>6} {'英雄WR':>7} {'总分':>6}")
for i, s in enumerate(scored[:20], 1):
    awr = f"{s['aug_wr']:.1f}%" if s['aug_wr'] else "N/A"
    gr = s['grade'] or "--"
    cwr = f"{s['champ_wr']:.2f}%" if s['champ_wr'] else "N/A"
    print(f"{i:<4} {s['champion']:<10} {s['augment']:<14} {s['rarity']:<10} {awr:>7} {gr:>6} {cwr:>7} {s['total']:>6.1f}")

print("\n### Bottom 10 最低价值的质变组合:")
for i, s in enumerate(scored[-10:], 1):
    awr = f"{s['aug_wr']:.1f}%" if s['aug_wr'] else "N/A"
    gr = s['grade'] or "--"
    cwr = f"{s['champ_wr']:.2f}%" if s['champ_wr'] else "N/A"
    print(f"{i:<4} {s['champion']:<10} {s['augment']:<14} {s['rarity']:<10} {awr:>7} {gr:>6} {cwr:>7} {s['total']:>6.1f}")

# ──────────────────────────────────────────────
# 9. 推荐筛选阈值
# ──────────────────────────────────────────────
print("\n\n## 8. 推荐筛选阈值")
print("=" * 70)

# 有 grade S 且 augment 胜率 >= 20%
elite = [s for s in scored if s["grade"] == "S" and s["aug_wr"] is not None and s["aug_wr"] >= 20]
print(f"\n[A级] Grade=S 且增强胜率>=20%: {len(elite)} 条")
for s in elite[:10]:
    print(f"    {s['champion']} + {s['augment']} ({s['rarity']}) wr={s['aug_wr']:.1f}%")

# 有 grade S 或 (grade A 且 augment 胜率>=30%)
high = [s for s in scored if (s["grade"] == "S") or (s["grade"] == "A" and s["aug_wr"] is not None and s["aug_wr"] >= 30)]
print(f"\n[B级] Grade=S 或 (Grade=A 且增强胜率>=30%): {len(high)} 条")

# 综合分数 >= 60
score_high = [s for s in scored if s["total"] >= 60]
print(f"\n[C级] 综合分数>=60: {len(score_high)} 条 ({len(score_high)/len(scored)*100:.1f}%)")

# 综合分数 >= 50
score_med = [s for s in scored if s["total"] >= 50]
print(f"\n[D级] 综合分数>=50: {len(score_med)} 条 ({len(score_med)/len(scored)*100:.1f}%)")

print("\n\n分析完成!")
