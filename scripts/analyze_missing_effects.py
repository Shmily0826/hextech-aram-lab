"""
analyze_missing_effects.py
Find augments with effect_en but no Chinese effect, and other data gaps.
"""
import json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

with open(os.path.join(ROOT, 'data', 'augments.json'), encoding='utf-8') as f:
    augs = json.load(f)

# 1. Augments with effect_en but no effect (Chinese)
missing_cn = []
for a in augs:
    en = (a.get('effect_en') or '').strip()
    cn = (a.get('effect') or '').strip()
    if en and not cn:
        missing_cn.append(a)

print(f"=== 有英文效果但缺中文效果: {len(missing_cn)} 个 ===")
for a in missing_cn:
    en_preview = (a.get('effect_en') or '')[:60]
    print(f"  {a['name']} ({a.get('name_en','?')}) [{a.get('tier','?')}]")
    print(f"    EN: {en_preview}...")

# 2. Augments with no effect AND no effect_en
missing_both = []
for a in augs:
    en = (a.get('effect_en') or '').strip()
    cn = (a.get('effect') or '').strip()
    if not en and not cn:
        missing_both.append(a)

print(f"\n=== 中英文效果都缺失: {len(missing_both)} 个 ===")
for a in missing_both:
    print(f"  {a['name']} ({a.get('name_en','?')}) [{a.get('tier','?')}]")

# 3. Other data gaps
print(f"\n=== 其他数据漏洞 ===")
no_name_en = [a for a in augs if not a.get('name_en')]
no_tier = [a for a in augs if not a.get('tier')]
no_status = [a for a in augs if not a.get('status')]
no_tags = [a for a in augs if not a.get('tags') or len(a.get('tags',[])) == 0]
no_desc = [a for a in augs if not (a.get('desc') or '').strip()]
no_win_rate = [a for a in augs if a.get('win_rate') is None]

print(f"  缺 name_en: {len(no_name_en)}")
for a in no_name_en[:5]:
    print(f"    {a['name']} ({a.get('id','?')})")
print(f"  缺 tier: {len(no_tier)}")
for a in no_tier[:5]:
    print(f"    {a['name']}")
print(f"  缺 status: {len(no_status)}")
print(f"  缺 tags: {len(no_tags)}")
print(f"  缺 desc (玩法说明): {len(no_desc)}")
print(f"  缺 win_rate: {len(no_win_rate)}")
for a in no_win_rate[:5]:
    print(f"    {a['name']} ({a.get('name_en','?')}) [{a.get('tier','?')}]")

# 4. Summary
total = len(augs)
has_cn_effect = sum(1 for a in augs if (a.get('effect') or '').strip())
has_en_effect = sum(1 for a in augs if (a.get('effect_en') or '').strip())
print(f"\n=== 总览 ===")
print(f"  总计: {total} 增强")
print(f"  有中文效果: {has_cn_effect}")
print(f"  有英文效果: {has_en_effect}")
print(f"  缺中文效果: {len(missing_cn) + len(missing_both)}")
print(f"  两者都缺: {len(missing_both)}")
