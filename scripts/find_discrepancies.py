"""
find_discrepancies.py
Find augments where our status differs from arammayhem.com.
arammayhem.com: 190 active, 65 deleted, 255 total
Our data: 195 active, 64 removed, 259 total
"""
import json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

with open(os.path.join(ROOT, 'data', 'augments.json'), encoding='utf-8') as f:
    augs = json.load(f)

# The actual active list from arammayhem.com (190 augments, from the page that showed all)
# We need to fetch this properly. For now, let's see which of our "active" augments
# might not be on the site at all.

# Let's check: which of our removed augments DON'T have the "removed in 26.12" text?
# Those might be incorrectly marked.
removed = [a for a in augs if a.get('status') == 'removed']
print(f"=== 已移除海克斯详情 ({len(removed)} 个) ===\n")

# Group by whether they have effect text
has_effect = [a for a in removed if (a.get('effect') or '').strip()]
no_effect = [a for a in removed if not (a.get('effect') or '').strip()]

print(f"有效果描述的已移除: {len(has_effect)}")
for a in has_effect:
    print(f"  {a['name']:20s} ({a.get('name_en','?'):30s}) [{a.get('tier','?')}]")

print(f"\n无效果描述的已移除: {len(no_effect)}")
for a in no_effect[:10]:
    print(f"  {a['name']:20s} ({a.get('name_en','?'):30s}) [{a.get('tier','?')}]")
if len(no_effect) > 10:
    print(f"  ... 还有 {len(no_effect)-10} 个")

# Check our active augments that might not exist on arammayhem.com
# by checking which ones lack a source URL
active = [a for a in augs if a.get('status') == 'active']
print(f"\n=== 活跃海克斯来源分布 ({len(active)} 个) ===")
src_count = {}
for a in active:
    src = a.get('source', {})
    if isinstance(src, dict):
        stype = src.get('type', 'unknown')
    else:
        stype = str(src) if src else 'unknown'
    src_count[stype] = src_count.get(stype, 0) + 1
for s, c in sorted(src_count.items(), key=lambda x: -x[1]):
    print(f"  {s}: {c}")
