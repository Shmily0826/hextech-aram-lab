"""
check_all_gaps.py
Comprehensive check of all data quality gaps in augments.json
"""
import json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

with open(os.path.join(ROOT, 'data', 'augments.json'), encoding='utf-8') as f:
    augs = json.load(f)

active = [a for a in augs if a.get('status') == 'active']
removed = [a for a in augs if a.get('status') == 'removed']
other = [a for a in augs if a.get('status') not in ('active', 'removed')]

print(f"=== 总计: {len(augs)} 个海克斯 ===")
print(f"  active: {len(active)}")
print(f"  removed: {len(removed)}")
if other:
    print(f"  other: {len(other)}")

def check(subset, label):
    print(f"\n=== {label} ({len(subset)} 个) ===")
    
    no_effect = [a for a in subset if not (a.get('effect') or '').strip()]
    no_effect_en = [a for a in subset if not (a.get('effect_en') or '').strip()]
    no_both = [a for a in subset if not (a.get('effect') or '').strip() and not (a.get('effect_en') or '').strip()]
    has_en_no_cn = [a for a in subset if (a.get('effect_en') or '').strip() and not (a.get('effect') or '').strip()]
    no_tags = [a for a in subset if not a.get('tags') or len(a.get('tags', [])) == 0]
    no_win_rate = [a for a in subset if a.get('win_rate') is None]
    no_desc = [a for a in subset if not (a.get('desc') or '').strip()]
    no_name_en = [a for a in subset if not a.get('name_en')]
    
    print(f"  缺中文效果: {len(no_effect)}")
    print(f"  缺英文效果: {len(no_effect_en)}")
    print(f"  中英文都缺: {len(no_both)}")
    if no_both:
        for a in no_both[:5]:
            print(f"    {a['name']} ({a.get('name_en','?')})")
        if len(no_both) > 5:
            print(f"    ... 还有 {len(no_both)-5} 个")
    
    print(f"  有英文缺中文: {len(has_en_no_cn)}")
    if has_en_no_cn:
        for a in has_en_no_cn[:5]:
            print(f"    {a['name']} ({a.get('name_en','?')})")
    
    print(f"  缺标签(tags): {len(no_tags)}")
    print(f"  缺胜率: {len(no_win_rate)}")
    print(f"  缺玩法说明(desc): {len(no_desc)}")
    print(f"  缺英文名: {len(no_name_en)}")

check(active, "活跃海克斯")
check(removed, "已移除海克斯")

# Specifically check: are there any ACTIVE augments with missing effects?
active_no_effect = [a for a in active if not (a.get('effect') or '').strip()]
if active_no_effect:
    print(f"\n!!! 警告: {len(active_no_effect)} 个活跃海克斯缺少中文效果 !!!")
    for a in active_no_effect:
        print(f"  {a['name']} ({a.get('name_en','?')}) [{a.get('tier','?')}]")
        print(f"    effect_en: {(a.get('effect_en') or 'NONE')[:60]}")
