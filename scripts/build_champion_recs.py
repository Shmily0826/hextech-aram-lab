"""
将 blitz.gg 英雄增强推荐数据转换为网站可用格式
- 输出 data/champion_recs.json (增强→推荐英雄映射)
"""
import json
import os
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INPUT = os.path.join(ROOT, 'pipeline', 'output', 'champion_augment_recommendations_sample.json')
OUTPUT = os.path.join(ROOT, 'data', 'champion_recs.json')

with open(INPUT, 'r', encoding='utf-8') as f:
    data = json.load(f)

# augment_id → [推荐英雄列表]
aug_recs = defaultdict(list)

for champ in data['champions']:
    champ_cn = champ['champion']
    champ_en = champ['champion_en']
    champ_tier = champ['tier']  # S/A/B/C
    
    for aug in champ['augments']:
        if not aug.get('matched'):
            continue
        aug_id = aug['augment_id']
        aug_recs[aug_id].append({
            'h': champ_cn,
            'h_en': champ_en,
            'rarity': aug['rarity'],
            'grade': aug['grade'],
            'champ_tier': champ_tier,
        })

# 每个增强按 grade 排序 (S > A > B)
grade_order = {'S': 0, 'A': 1, 'B': 2}
for aug_id in aug_recs:
    aug_recs[aug_id].sort(key=lambda x: (grade_order.get(x['grade'], 9), x['h']))

# 输出
output = {
    'type': 'augment_champion_recommendations',
    'source': 'blitz.gg',
    'patch': data.get('patch', '26.12'),
    'champion_count': data['champion_count'],
    'augment_count': len(aug_recs),
    'data': dict(aug_recs)
}

with open(OUTPUT, 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

# 统计
s_only = sum(1 for recs in aug_recs.values() if any(r['grade'] == 'S' for r in recs))
print(f"Output: {OUTPUT}")
print(f"Total augments with recommendations: {len(aug_recs)}")
print(f"Augments with S-grade recs: {s_only}")

# 打印 top 推荐（被最多S级英雄推荐的增强）
top = sorted(aug_recs.items(), key=lambda x: sum(1 for r in x[1] if r['grade'] == 'S'), reverse=True)
print(f"\nTop 10 augments (most S-grade champion recommendations):")
for aug_id, recs in top[:10]:
    s_count = sum(1 for r in recs if r['grade'] == 'S')
    names = [r['h'] for r in recs if r['grade'] == 'S']
    print(f"  {aug_id}: {s_count} S-tier heroes ({', '.join(names[:5])}{'...' if len(names) > 5 else ''})")
