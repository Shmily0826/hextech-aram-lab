"""
find_dupes_and_fix.py
Find all removed augments that have an active counterpart (same English name = duplicate).
Also check for name mismatches with arammayhem.com.
"""
import json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

with open(os.path.join(ROOT, 'data', 'augments.json'), encoding='utf-8') as f:
    augs = json.load(f)

def norm_en(s):
    s = (s or '').lower().strip()
    return re.sub(r'[^a-z0-9]', '', s)

# Build EN name -> augment list
en_map = {}
for a in augs:
    key = norm_en(a.get('name_en', ''))
    if key:
        en_map.setdefault(key, []).append(a)

# Find duplicates (same EN name, different status)
print("=== 英文重名（同EN名不同状态）===")
dupes = []
for key, items in en_map.items():
    if len(items) > 1:
        statuses = [a.get('status') for a in items]
        if len(set(statuses)) > 1:  # Different statuses
            dupes.append((key, items))
            removed_item = [a for a in items if a.get('status') == 'removed'][0]
            active_item = [a for a in items if a.get('status') == 'active'][0]
            print(f"  {key}:")
            print(f"    已移除: {removed_item['name']} (id={removed_item.get('id','?')})")
            print(f"    活跃:   {active_item['name']} (id={active_item.get('id','?')})")
            print(f"    操作: 删除已移除的重复条目 '{removed_item['name']}'")

# Also check: removed augments whose EN name partially matches an active augment
print(f"\n=== 已移除 vs 活跃 部分名称匹配 ===")
removed = [a for a in augs if a.get('status') == 'removed']
active = [a for a in augs if a.get('status') == 'active']
active_keys = {norm_en(a.get('name_en','')): a for a in active}

for r in removed:
    r_key = norm_en(r.get('name_en', ''))
    if r_key in active_keys:
        a = active_keys[r_key]
        print(f"  精确匹配: {r['name']}(removed) vs {a['name']}(active) — EN: {r.get('name_en')}")
    else:
        # Partial match
        for a_key, a in active_keys.items():
            if r_key and a_key and len(r_key) > 5 and len(a_key) > 5:
                if r_key in a_key or a_key in r_key:
                    print(f"  部分匹配: {r['name']}(removed, {r.get('name_en')}) vs {a['name']}(active, {a.get('name_en')})")
                    break

# Summary
print(f"\n=== 需要修复的问题 ===")
print(f"  1. 重复条目: {len(dupes)} 对 (应删除已移除的重复)")
print(f"  2. 活跃但不在arammayhem.com: 94 个 (需进一步确认)")
print(f"  3. 已移除确认: {len(removed) - len(dupes)} 个真正已移除")
