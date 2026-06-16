"""
用 champion_recs.json 的真实数据重建 synergies.json
- 只保留 champion_recs 中确实存在的英雄-强化对
- 用推荐等级 S/A/B 作为可信度代理
- 去掉所有编造的胜率数字、玩家语录、证据等
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT, 'data')

# champion_recs 中的名字 → champions.json / synergies.json 中的名字
NAME_ALIASES = {
    '奥瑞利安索尔': '铸星龙王',
    '蒙多医生': '祖安狂人',
    '易大师': '无极剑圣',
}

# 推荐等级 → tier 映射
GRADE_TO_TIER = {
    'S': 'transform',  # S级 = 质变组合（最强推荐）
    'A': 'recommend',  # A级 = 推荐增强
    'B': 'recommend',  # B级 = 推荐增强
}

# 推荐等级 → 可信度代理
GRADE_TO_CONF = {
    'S': 90,
    'A': 70,
    'B': 50,
}


def main():
    # 读取 champion_recs.json
    recs_path = os.path.join(DATA_DIR, 'champion_recs.json')
    with open(recs_path, 'r', encoding='utf-8') as f:
        recs_data = json.load(f)

    # 读取 augments.json 获取强化中文名
    aug_path = os.path.join(DATA_DIR, 'augments.json')
    with open(aug_path, 'r', encoding='utf-8') as f:
        augments = json.load(f)
    aug_map = {a['id']: a['name'] for a in augments}

    # 遍历 champion_recs，生成 synergy 条目
    synergies = []
    heroes_seen = set()

    for aug_id, recs in recs_data['data'].items():
        aug_name = aug_map.get(aug_id, aug_id)
        for r in recs:
            hero_name = r['h']
            # 映射名字到 champions.json 用的名字
            hero_name = NAME_ALIASES.get(hero_name, hero_name)

            grade = r.get('grade', 'B')
            tier = GRADE_TO_TIER.get(grade, 'recommend')
            conf = GRADE_TO_CONF.get(grade, 50)

            synergies.append({
                'hero': hero_name,
                'aug': aug_name,
                'rar': r.get('rarity', 'silver'),
                'tier': tier,
                'conf': conf,
                'ver': recs_data.get('patch', '26.12'),
                'src': 'blitz_gg',
                'status': 'verified',
            })
            heroes_seen.add(hero_name)

    # 按英雄名、稀有度排序
    rar_order = {'prismatic': 0, 'gold': 1, 'silver': 2}
    tier_order = {'transform': 0, 'recommend': 1, 'avoid': 2, 'bug': 3}
    synergies.sort(key=lambda x: (x['hero'], tier_order.get(x['tier'], 9), rar_order.get(x['rar'], 9)))

    # 保存
    out_path = os.path.join(DATA_DIR, 'synergies.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(synergies, f, ensure_ascii=False, indent=2)

    # 统计
    transform_count = sum(1 for s in synergies if s['tier'] == 'transform')
    recommend_count = sum(1 for s in synergies if s['tier'] == 'recommend')

    print(f"重建完成: {len(synergies)} 条英雄-强化对")
    print(f"  质变组合 (S级): {transform_count}")
    print(f"  推荐增强 (A/B级): {recommend_count}")
    print(f"  覆盖英雄: {len(heroes_seen)}")
    print(f"  数据来源: blitz.gg (patch {recs_data.get('patch', '26.12')})")
    print(f"\n已保存到: {out_path}")


if __name__ == '__main__':
    main()
