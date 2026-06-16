"""
更新 champions.json 的英雄档案
- 从 champion_recs.json 读取真实的 blitz.gg tier 数据
- 清理编造的统计数据（wr/pr/games/kda/build/tips）
- 保留正确的结构性数据（name/title/role）
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT, 'data')

def main():
    # 读取 champions.json
    champ_path = os.path.join(DATA_DIR, 'champions.json')
    with open(champ_path, 'r', encoding='utf-8') as f:
        champ_data = json.load(f)
    
    # 读取 champion_recs.json
    recs_path = os.path.join(DATA_DIR, 'champion_recs.json')
    with open(recs_path, 'r', encoding='utf-8') as f:
        recs_data = json.load(f)
    
    # champion_recs 中的名字 → champions.json 中的名字（已知差异）
    NAME_ALIASES = {
        '奥瑞利安索尔': '铸星龙王',
        '蒙多医生': '祖安狂人',
        '易大师': '无极剑圣',
    }
    
    # 从 champion_recs 反查每个英雄的 tier
    hero_tier = {}  # {champions.json 中文名: tier}
    for aug_id, recs in recs_data['data'].items():
        for r in recs:
            name = r['h']
            tier = r.get('champ_tier', 'unknown')
            # 转换名字
            mapped_name = NAME_ALIASES.get(name, name)
            if mapped_name not in hero_tier:
                hero_tier[mapped_name] = tier
    
    print(f"从 champion_recs.json 获取到 {len(hero_tier)} 位英雄的 tier 数据")
    
    # 统计变更
    tier_updated = 0
    stats_cleared = 0
    tier_map = {'S': 'S', 'A': 'A', 'B': 'B', 'C': 'C', 'D': 'D'}
    
    for champ in champ_data['champions']:
        name = champ['name']
        
        # 更新 tier
        if name in hero_tier:
            old_tier = champ.get('tier', 'unknown')
            new_tier = hero_tier[name]
            if old_tier != new_tier:
                champ['tier'] = new_tier
                tier_updated += 1
        
        # 清理编造统计数据（所有英雄统一处理）
        # wr/pr/games/kda 设为 null，build/tips 设为空
        changed = False
        for stat_key in ['wr', 'pr', 'games', 'kda']:
            if champ.get(stat_key) is not None:
                champ[stat_key] = None
                changed = True
        for str_key in ['build', 'tips']:
            if champ.get(str_key):
                champ[str_key] = ''
                changed = True
        if changed:
            stats_cleared += 1
    
    # 保存
    with open(champ_path, 'w', encoding='utf-8') as f:
        json.dump(champ_data, f, ensure_ascii=False, indent=2)
    
    # 验证
    print(f"\n更新完成:")
    print(f"  Tier 更新: {tier_updated} 位英雄")
    print(f"  统计清理: {stats_cleared} 位英雄")
    print(f"  总英雄数: {len(champ_data['champions'])}")
    
    # 打印 tier 分布
    tier_counts = {}
    for champ in champ_data['champions']:
        t = champ.get('tier', 'unknown')
        tier_counts[t] = tier_counts.get(t, 0) + 1
    print(f"\nTier 分布:")
    for t in ['S', 'A', 'B', 'C', 'D', 'unknown']:
        print(f"  {t}: {tier_counts.get(t, 0)}")
    
    print(f"\n已保存到: {champ_path}")


if __name__ == '__main__':
    main()
