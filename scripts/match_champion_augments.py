"""
匹配 blitz.gg 英雄增强推荐数据到 augments.json
构建"英雄→增强推荐"关联结构
"""
import json
import re
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT, 'data')
OUTPUT_DIR = os.path.join(ROOT, 'pipeline', 'output')

# --- 英雄英文名 → 中文名映射（从 heroes.json 读取） ---
def load_heroes_map():
    path = os.path.join(DATA_DIR, 'champions.json')
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    # championKeys: {中文名: EnglishName}
    cn_to_en = data.get('championKeys', {})
    en_to_cn = {v.lower(): k for k, v in cn_to_en.items()}
    # 补充显示名映射（处理 Dr. Mundo、Aurelion Sol 等有空格/点号的英雄）
    display_fallback = {
        'dr. mundo': '蒙多医生', 'dr mundo': '蒙多医生',
        'aurelion sol': '奥瑞利安索尔',
        'renata glasc': '炼金男爵',
        'wukong': '齐天大圣', 'monkeyking': '齐天大圣',
        'tahm kench': '河流之王', 'tahmkench': '河流之王',
        "cho'gath": '虚空恐惧', 'chogath': '虚空恐惧',
        "kai'sa": '卡莎', 'kaisa': '卡莎',
        "kog'maw": '深渊巨口', 'kogmaw': '深渊巨口',
        "rek'sai": '虚空遁地兽', 'reksai': '虚空遁地兽',
        "bel'veth": '虚空女皇', 'belveth': '虚空女皇',
        'miss fortune': '赏金猎人', 'missfortune': '赏金猎人',
        'twisted fate': '卡牌大师', 'twistedfate': '卡牌大师',
        'master yi': '易大师', 'masteryi': '易大师',
        'xin zhao': '德邦总管', 'xinzhao': '德邦总管',
        'lee sin': '盲僧', 'leesin': '盲僧',
        "vel'koz": '虚空之眼', 'velkoz': '虚空之眼',
        'jarvan iv': '德玛西亚皇子', 'jarvaniv': '德玛西亚皇子',
        "k'sante": '纳祖芒荣耀', 'ksante': '纳祖芒荣耀',
        "kha'zix": '虚空掠夺者', 'khazix': '虚空掠夺者',
        'leblanc': '诡术妖姬',
    }
    for k, v in display_fallback.items():
        if k.lower() not in en_to_cn:
            en_to_cn[k.lower()] = v
    return en_to_cn

# --- 增强英文名 → augments.json 条目映射 ---
def load_augments_map():
    path = os.path.join(DATA_DIR, 'augments.json')
    with open(path, 'r', encoding='utf-8') as f:
        augments = json.load(f)
    
    en_to_entry = {}
    id_to_entry = {}
    for a in augments:
        entry = {
            'id': a['id'],
            'name': a['name'],
            'name_en': a.get('name_en', ''),
            'tier': a.get('tier', 'unknown'),
        }
        id_to_entry[a['id']] = entry
        
        # 主英文名
        en = a.get('name_en', '').lower().strip()
        if en:
            en_to_entry[en] = entry
        
        # 别名
        for alias in a.get('aliases', []):
            alias_lower = alias.lower().strip()
            if alias_lower:
                en_to_entry[alias_lower] = entry
    
    return en_to_entry, id_to_entry, augments

def normalize_name(name):
    """标准化增强英文名用于匹配"""
    name = name.lower().strip()
    # 移除标点差异
    name = name.replace('\u2019', "'")  # 弯引号 → 直引号
    name = name.replace('\u2018', "'")
    name = re.sub(r'[^a-z0-9\s\':]', '', name)
    return name

# blitz.gg 名字 → 我们数据库的名字（已知差异）
NAME_OVERRIDES = {
    "icathia's fall": "icathian fall",
    "it's go time": "its go time",  # 可能不存在
    "bread and jam": "bread and jam",
    "bread and butter": "bread and butter",
    "bread and cheese": "bread and cheese",
    "light 'em up!": "light 'em up!",
}

def match_augment(blitz_name, en_to_entry):
    """尝试匹配 blitz.gg 增强名到我们的条目"""
    norm = normalize_name(blitz_name)
    
    # 检查已知名字差异
    if norm in NAME_OVERRIDES:
        override = NAME_OVERRIDES[norm]
        if override in en_to_entry:
            return en_to_entry[override], 'override'
    
    # 精确匹配
    if norm in en_to_entry:
        return en_to_entry[norm], 'exact'
    
    # 忽略空格/冒号/标点差异
    norm_stripped = re.sub(r'[\s\-\':!?.]+', '', norm)
    for key, entry in en_to_entry.items():
        key_stripped = re.sub(r'[\s\-\':!?.]+', '', key)
        if norm_stripped == key_stripped:
            return entry, 'fuzzy'
    
    # 部分匹配（至少5个字符）
    if len(norm) >= 5:
        for key, entry in en_to_entry.items():
            if len(key) >= 5 and (norm in key or key in norm):
                return entry, 'partial'
    
    return None, 'no_match'


def main():
    # 加载数据
    heroes_map = load_heroes_map()
    en_to_entry, id_to_entry, all_augments = load_augments_map()
    
    # 加载抓取的英雄数据
    sample_path = os.path.join(OUTPUT_DIR, 'blitz_champion_augments_sample.json')
    with open(sample_path, 'r', encoding='utf-8') as f:
        champions_data = json.load(f)
    
    results = []
    total_matched = 0
    total_unmatched = 0
    unmatched_list = []
    
    for champ_data in champions_data:
        if 'error' in champ_data:
            continue
            
        champ_en = champ_data['champion']
        champ_cn = heroes_map.get(champ_en.lower(), champ_en)
        
        champion_result = {
            'champion': champ_cn,
            'champion_en': champ_en,
            'tier': champ_data.get('tier', 'S'),
            'augments': [],
            'source': 'blitz.gg',
            'url': champ_data['url'],
        }
        
        for rarity in ['prismatic', 'gold', 'silver']:
            for aug in champ_data['augments'].get(rarity, []):
                blitz_name = aug['name']
                grade = aug['tier']  # S/A/B
                
                entry, match_type = match_augment(blitz_name, en_to_entry)
                
                rec = {
                    'blitz_name': blitz_name,
                    'rarity': rarity,
                    'grade': grade,
                    'matched': entry is not None,
                    'match_type': match_type,
                }
                
                if entry:
                    rec['augment_id'] = entry['id']
                    rec['augment_name'] = entry['name']
                    rec['augment_name_en'] = entry['name_en']
                    total_matched += 1
                else:
                    total_unmatched += 1
                    unmatched_list.append(f"{champ_en} > {blitz_name}")
                    
                champion_result['augments'].append(rec)
        
        results.append(champion_result)
    
    # 输出候选 JSON
    output = {
        'type': 'champion_augment_recommendations',
        'source': 'blitz.gg',
        'patch': '26.12',
        'champion_count': len(results),
        'stats': {
            'total_augments': total_matched + total_unmatched,
            'matched': total_matched,
            'unmatched': total_unmatched,
            'match_rate': f"{total_matched/(total_matched+total_unmatched)*100:.1f}%" if (total_matched + total_unmatched) > 0 else "0%"
        },
        'unmatched_augments': unmatched_list,
        'champions': results
    }
    
    output_path = os.path.join(OUTPUT_DIR, 'champion_augment_recommendations_sample.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    # 打印结果
    print(f"匹配完成: {total_matched}/{total_matched + total_unmatched} ({output['stats']['match_rate']})")
    
    if unmatched_list:
        print(f"\n未匹配的增强 ({len(unmatched_list)}):")
        for u in unmatched_list:
            print(f"  - {u}")
    
    print(f"\n已保存到: {output_path}")
    
    # 打印每个英雄的匹配详情
    for champ in results:
        print(f"\n{'='*50}")
        print(f"[{champ['champion']}] ({champ['champion_en']}) - {champ['tier']}级英雄")
        print(f"{'='*50}")
        
        for rarity in ['prismatic', 'gold', 'silver']:
            rarity_cn = {'prismatic': '棱彩', 'gold': '金色', 'silver': '银色'}[rarity]
            augs = [a for a in champ['augments'] if a['rarity'] == rarity]
            if not augs:
                continue
            print(f"\n  {rarity_cn}:")
            for a in augs:
                grade_mark = {'S': 'S', 'A': 'A', 'B': 'B'}[a['grade']]
                if a['matched']:
                    print(f"    [{grade_mark}] {a['augment_name']} ({a['augment_name_en']})")
                    print(f"         id={a['augment_id']}")
                else:
                    print(f"    [{grade_mark}] ??? ({a['blitz_name']}) [未匹配]")


if __name__ == '__main__':
    main()
