"""
check_status.py
Check augments with status=removed — are they truly removed?
Cross-reference with arammayhem.com availability.
"""
import json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

with open(os.path.join(ROOT, 'data', 'augments.json'), encoding='utf-8') as f:
    augs = json.load(f)

removed = [a for a in augs if a.get('status') == 'removed']
active = [a for a in augs if a.get('status') == 'active']

print(f"=== 状态统计 ===")
print(f"  active: {len(active)}")
print(f"  removed: {len(removed)}")
print()

# Check: do removed augments have win_rate? (If they do, they might still be active)
removed_with_wr = [a for a in removed if a.get('win_rate') is not None]
print(f"=== 已移除但有胜率数据的: {len(removed_with_wr)} 个 ===")
for a in removed_with_wr:
    print(f"  {a['name']} ({a.get('name_en','?')}) [{a.get('tier','?')}] wr={a.get('win_rate')}")

# Check: do removed augments have tags? (Active ones usually have tags)
removed_with_tags = [a for a in removed if a.get('tags') and len(a.get('tags',[])) > 0]
print(f"\n=== 已移除但有标签的: {len(removed_with_tags)} 个 ===")
for a in removed_with_tags[:10]:
    print(f"  {a['name']} ({a.get('name_en','?')}) tags={a.get('tags',[])}")

# Check source field — if source has arammayhem.com Chinese page, the page might still exist
# meaning it's not actually removed
print(f"\n=== 已移除海克斯的source分布 ===")
src_types = {}
for a in removed:
    src = a.get('source', {})
    if isinstance(src, dict):
        url = src.get('url', '')
        stype = src.get('type', 'unknown')
    else:
        url = ''
        stype = str(src)
    src_types[stype] = src_types.get(stype, 0) + 1
for st, cnt in sorted(src_types.items()):
    print(f"  {st}: {cnt}")

# List all removed augments
print(f"\n=== 所有已移除海克斯 ({len(removed)}) ===")
for a in removed:
    src = a.get('source', {})
    src_url = src.get('url', '') if isinstance(src, dict) else ''
    has_effect_cn = bool((a.get('effect') or '').strip())
    has_effect_en = bool((a.get('effect_en') or '').strip())
    has_wr = a.get('win_rate') is not None
    has_tags = bool(a.get('tags') and len(a.get('tags',[])) > 0)
    flags = []
    if has_effect_cn: flags.append('中文效果')
    if has_effect_en: flags.append('英文效果')
    if has_wr: flags.append(f'胜率{a["win_rate"]}')
    if has_tags: flags.append('有标签')
    print(f"  {a['name']:20s} ({a.get('name_en','?'):30s}) [{a.get('tier','?'):10s}] {', '.join(flags) if flags else '(无数据)'}")

# Check: how many removed augments have Chinese effect text?
# If they have Chinese effects, they likely came from the original data source which
# may have had them as active at some point
removed_with_cn = [a for a in removed if (a.get('effect') or '').strip()]
print(f"\n=== 已移除但有中文效果描述的: {len(removed_with_cn)} 个 ===")
print("  这些可能实际上是活跃的，只是被错误标记为removed")
for a in removed_with_cn[:15]:
    print(f"  {a['name']} ({a.get('name_en','?')}) [{a.get('tier','?')}]")
    print(f"    effect: {(a.get('effect') or '')[:60]}...")
