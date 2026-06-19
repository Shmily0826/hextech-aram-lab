"""
check_removed_augs.py
Check the 54 removed augments: do they have effect_en? What data do they have?
"""
import json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

with open(os.path.join(ROOT, 'data', 'augments.json'), encoding='utf-8') as f:
    augs = json.load(f)

# Load scrape results
with open(os.path.join(ROOT, 'pipeline', 'output', 'missing_effects_scrape.json'), encoding='utf-8') as f:
    scrape = json.load(f)

scrape_ids = {s['id'] for s in scrape}

# Find the 54 augments missing both effects
missing_both = [a for a in augs if not (a.get('effect') or '').strip() and not (a.get('effect_en') or '').strip()]

print(f"=== 中英文效果都缺失的海克斯: {len(missing_both)} 个 ===\n")

# Group by status
by_status = {}
for a in missing_both:
    st = a.get('status', 'unknown')
    by_status.setdefault(st, []).append(a)

for st, items in sorted(by_status.items()):
    print(f"--- status={st}: {len(items)} 个 ---")
    for a in items[:5]:
        print(f"  {a['name']} ({a.get('name_en','?')}) [{a.get('tier','?')}]")
        print(f"    id={a.get('id','?')}, tags={a.get('tags',[])}")
        print(f"    effect={repr(a.get('effect',''))}, effect_en={repr(a.get('effect_en',''))}")
    if len(items) > 5:
        print(f"  ... 还有 {len(items)-5} 个")
    print()

# Check if scrape found any useful text (not just "已移除" meta)
print(f"=== 抓取结果分析 ===")
useful = []
meta_only = []
for s in scrape:
    eff = s.get('effect', '')
    if '已在' in eff and '移除' in eff:
        meta_only.append(s)
    else:
        useful.append(s)

print(f"  只有'已移除'meta描述: {len(meta_only)} 个")
print(f"  可能有用的效果文本: {len(useful)} 个")
for u in useful:
    print(f"  -> {u['name']}: {u.get('effect','')[:80]}")
