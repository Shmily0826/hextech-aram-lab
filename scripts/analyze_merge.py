#!/usr/bin/env python3
"""分析 approved_augments.json 与现有 augments.json 的重叠情况。"""
import json, sys, os, io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

with open(os.path.join(PROJECT, "data", "approved_augments.json"), "r", encoding="utf-8") as f:
    approved = json.load(f)
with open(os.path.join(PROJECT, "data", "augments.json"), "r", encoding="utf-8") as f:
    existing = json.load(f)

approved_ids = {c["id"] for c in approved}
existing_ids = {c["id"] for c in existing}

overlap = approved_ids & existing_ids
new_ids = approved_ids - existing_ids

print(f"approved_augments.json: {len(approved)} 条")
print(f"augments.json (现有): {len(existing)} 条")
print(f"ID 重叠: {len(overlap)} 条")
print(f"全新增强: {len(new_ids)} 条")

print("\n=== 重叠的 ID ===")
for oid in sorted(overlap):
    a = next(c for c in approved if c["id"] == oid)
    e = next(c for c in existing if c["id"] == oid)
    name_a = a["name"]
    name_e = e["name"]
    flag = " <<< 名字不同!" if name_a != name_e else ""
    tier_a = a["tier"]
    tier_e = e["tier"]
    tier_flag = f" <<< 稀有度不同! ({tier_e} vs {tier_a})" if tier_a != tier_e else ""
    print(f"  {oid}")
    print(f"    现有: {name_e} ({tier_e})")
    print(f"    审批: {name_a} ({tier_a}){flag}{tier_flag}")

print(f"\n=== 全新增强 ({len(new_ids)} 条) ===")
by_tier = {}
for nid in sorted(new_ids):
    a = next(c for c in approved if c["id"] == nid)
    t = a["tier"]
    by_tier[t] = by_tier.get(t, 0) + 1

for t in ["prismatic", "gold", "silver"]:
    print(f"  {t}: {by_tier.get(t, 0)} 条")

# 检查 approved 里有没有重复 ID
id_counts = {}
for c in approved:
    id_counts[c["id"]] = id_counts.get(c["id"], 0) + 1
dupes = {k: v for k, v in id_counts.items() if v > 1}
if dupes:
    print(f"\n=== 重复 ID ({len(dupes)}) ===")
    for k, v in dupes.items():
        print(f"  {k}: {v} 次")
else:
    print("\n无重复 ID")

# 检查 name_en 为空的情况
empty_en = [c for c in approved if not c.get("name_en", "")]
if empty_en:
    print(f"\n=== name_en 为空 ({len(empty_en)}) ===")
    for c in empty_en:
        print(f"  {c['id']}: {c['name']}")
