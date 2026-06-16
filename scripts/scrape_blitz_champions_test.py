"""
blitz.gg 英雄增强推荐数据抓取
从 blitz.gg ARAM Mayhem 英雄页面提取增强推荐列表（S/A/B等级）
"""
import urllib.request
import re
import json
import sys
import time
from html.parser import HTMLParser

# 全部 S 级英雄（blitz.gg URL 名）
S_TIER_CHAMPIONS = [
    'Sion', 'Sett', 'Kayle', 'Lillia', 'Rell', 'Gwen', 'Fiora',
    'Zaahen', 'Seraphine', 'DrMundo', 'Shyvana', 'Shen', 'Brand',
    'Jinx', 'Hwei', 'AurelionSol', 'Ekko', 'Malzahar', 'Galio',
    'Nasus', 'Graves', 'Vayne', 'Aphelios', 'Maokai',
]

# A 级英雄（全部33位）
A_TIER_CHAMPIONS = [
    'Sona', 'Illaoi', 'Heimerdinger', 'Viktor', 'Singed',
    'Jax', 'Aurora', 'MasterYi', 'TwistedFate', 'Kassadin', 'Zyra',
    'XinZhao', 'Ryze', 'MonkeyKing', 'Hecarim', 'Ornn', 'Yasuo',
    'Trundle', 'Soraka', 'Taric', 'Rumble', 'Leona', 'Karthus',
    'Zilean', 'Volibear', 'Briar', 'KogMaw', 'Kayn', 'Ahri',
    'Renata', 'Nautilus', 'Janna', 'Morgana',
]

# B 级英雄（全部54位）
B_TIER_CHAMPIONS = [
    'Caitlyn', 'Milio', 'Kled', 'TahmKench', 'Amumu',
    'Senna', 'Xayah', 'Sylas', 'Poppy', 'VelKoz',
    'Yone', 'Olaf', 'Mordekaiser', 'Alistar', 'Rammus',
    'Kalista', 'Syndra', 'Sejuani', 'Ambessa', 'Veigar',
    'Vladimir', 'RekSai', 'Ashe', 'MissFortune', 'Swain',
    'Skarner', 'Samira', 'Lux', 'Sivir', 'Azir',
    'Gangplank', 'Riven', 'Vex', 'Nami', 'Fiddlesticks',
    'Fizz', 'Yunara', 'Tryndamere', 'ChoGath', 'Teemo',
    'Ivern', 'Yuumi', 'Ziggs', 'Jhin', 'Vi',
    'Kindred', 'Warwick', 'Orianna', 'KaiSa', 'Annie',
    'Akshan', 'Urgot', 'Draven', 'Xerath',
]

# C 级英雄（全部35位）
C_TIER_CHAMPIONS = [
    'Udyr', 'Gragas', 'Mel', 'Rengar', 'Viego',
    'Nilah', 'Twitch', 'Pantheon', 'Varus', 'Diana',
    'Renekton', 'JarvanIV', 'Yorick', 'Tristana', 'Cassiopeia',
    'Smolder', 'Rakan', 'Corki', 'Malphite', 'Darius',
    'Karma', 'Katarina', 'Garen', 'Zac', 'Ezreal',
    'Nocturne', 'Talon', 'Zeri', 'Gnar', 'Lulu',
    'BelVeth', 'Lucian', 'Taliyah', 'Zed', 'Lissandra',
]

# D 级英雄（全部26位）
D_TIER_CHAMPIONS = [
    'Anivia', 'Elise', 'Evelynn', 'Braum', 'Zoe',
    'Pyke', 'Irelia', 'Nunu', 'Neeko', 'Naafiri',
    'Aatrox', 'Nidalee', 'Blitzcrank', 'Camille', 'Shaco',
    'Akali', 'Quinn', 'Jayce', 'Kennen', 'Khazix',
    'Qiyana', 'Thresh', 'KSante', 'Leblanc', 'Bard',
    'LeeSin',
]

# 英雄 → tier 映射
CHAMPION_TIER = {}
for c in S_TIER_CHAMPIONS:
    CHAMPION_TIER[c] = 'S'
for c in A_TIER_CHAMPIONS:
    CHAMPION_TIER[c] = 'A'
for c in B_TIER_CHAMPIONS:
    CHAMPION_TIER[c] = 'B'
for c in C_TIER_CHAMPIONS:
    CHAMPION_TIER[c] = 'C'
for c in D_TIER_CHAMPIONS:
    CHAMPION_TIER[c] = 'D'

# 合并要抓取的英雄列表
ALL_CHAMPIONS = S_TIER_CHAMPIONS + A_TIER_CHAMPIONS + B_TIER_CHAMPIONS + C_TIER_CHAMPIONS + D_TIER_CHAMPIONS

BASE_URL = 'https://blitz.gg/lol/champions/{}/aram-mayhem'

# URL 名 → 显示名映射（合并词的英雄名需要空格）
URL_TO_DISPLAY = {
    'DrMundo': "Dr. Mundo",
    'AurelionSol': "Aurelion Sol",
    'RenataGlasc': "Renata Glasc",
    'Renata': "Renata Glasc",
    'MonkeyKing': "Wukong",
    'TahmKench': "Tahm Kench",
    'ChoGath': "Cho'Gath",
    'KaiSa': "Kai'Sa",
    'KogMaw': "Kog'Maw",
    'RekSai': "Rek'Sai",
    'BelVeth': "Bel'Veth",
    'MissFortune': "Miss Fortune",
    'TwistedFate': "Twisted Fate",
    'MasterYi': "Master Yi",
    'XinZhao': "Xin Zhao",
    'VelKoz': "Vel'Koz",
    'JarvanIV': "Jarvan IV",
    'KSante': "K'Sante",
    'Khazix': "Kha'Zix",
    'LeeSin': "Lee Sin",
    'Leblanc': "LeBlanc",
}

# --- HTML 解析 ---

class AugmentPageParser(HTMLParser):
    """解析 blitz.gg 英雄页面的增强推荐数据"""
    
    def __init__(self):
        super().__init__()
        self.in_rarity_name = False
        self.current_rarity = None
        self.augments = []
        self._pending_augment = None
        self._depth_stack = []
        
    def handle_starttag(self, tag, attrs):
        attr_dict = dict(attrs)
        cls = attr_dict.get('class', '')
        alt = attr_dict.get('alt', '')
        
        # 检测稀有度名称
        if tag == 'span' and 'rarity-name' in cls:
            self.in_rarity_name = True
            
        # 检测增强图标
        if tag == 'img' and 'augment-img' in cls and alt and 'Tier' not in alt:
            self._pending_augment = {'name': alt, 'tier': None, 'rarity': self.current_rarity}
            
        # 检测等级图标 (tier-s.svg = S, tier-a.svg = A, 其他 = B)
        if tag == 'img' and alt.startswith('Tier') and self._pending_augment:
            tier_num = alt.replace('Tier ', '')
            tier_map = {'1': 'S', '2': 'A'}
            self._pending_augment['tier'] = tier_map.get(tier_num, 'B')
            
    def handle_endtag(self, tag):
        if tag == 'span' and self.in_rarity_name:
            self.in_rarity_name = False
            
    def handle_data(self, data):
        if self.in_rarity_name:
            text = data.strip()
            if 'Prismatic' in text:
                self.current_rarity = 'prismatic'
            elif 'Gold' in text:
                self.current_rarity = 'gold'
            elif 'Silver' in text:
                self.current_rarity = 'silver'
                
        # 当增强名字作为文本出现时（备用提取）
        # 某些增强名字可能在文本节点中
        
    def flush_augment(self):
        """将当前待处理的增强加入列表"""
        if self._pending_augment:
            self.augments.append(self._pending_augment)
            self._pending_augment = None


def extract_with_regex(html):
    """用正则表达式从 HTML 中提取增强推荐数据（更可靠）
    
    HTML 结构:
    <div class="rarity"><span class="rarity-name">Prismatic Augments</span>
      <div class="augments-grid">
        <div class="tooltip-trigger">
          <div class="augment">
            <div class="img-container">
              <img alt="增强名" class="augment-img" .../>
              <img alt="Tier 1" .../>  <!-- 1=S, 2=A, 3=B -->
            </div>
          </div>
        </div>
        ...
      </div>
    </div>
    """
    result = {'prismatic': [], 'gold': [], 'silver': []}
    
    # 步骤1: 按稀有度分割 HTML
    # 找到所有 rarity-name 及其位置（文本被 HTML 注释包裹）
    rarity_markers = list(re.finditer(
        r'<span[^>]*class="[^"]*rarity-name[^"]*"[^>]*>(.*?)</span>',
        html, re.DOTALL
    ))
    
    for i, marker in enumerate(rarity_markers):
        rarity_text = marker.group(1)
        start = marker.end()
        end = rarity_markers[i + 1].start() if i + 1 < len(rarity_markers) else len(html)
        section_html = html[start:end]
        
        # 确定稀有度（文本可能包含 HTML 注释如 <!--[2-->Prismatic Augments<!--]-->）
        if 'Prismatic' in rarity_text:
            rarity = 'prismatic'
        elif 'Gold' in rarity_text:
            rarity = 'gold'
        elif 'Silver' in rarity_text:
            rarity = 'silver'
        else:
            continue
        
        # 步骤2: 找到所有 tooltip-trigger 块
        # 每个块包含一个增强图标和一个等级图标
        trigger_blocks = re.split(r'<div class="tooltip-trigger"', section_html)
        
        for block in trigger_blocks[1:]:  # 跳过第一个（分割前的内容）
            # 取到闭合为止（大约 1500 字符足够）
            block_snippet = block[:1500]
            
            # 提取增强名: alt="XXX" class="augment-img" 或 alt="XXX" ... class="augment-img"
            augment_match = re.search(r'alt="([^"]+)"[^>]*?class="augment-img', block_snippet)
            if not augment_match:
                continue
            name = augment_match.group(1)
            
            # 提取等级: alt="Tier N"
            tier_match = re.search(r'alt="Tier\s*(\d+)"', block_snippet)
            if not tier_match:
                continue
            tier_num = tier_match.group(1)
            tier_map = {'1': 'S', '2': 'A'}
            tier = tier_map.get(tier_num, 'B')
            
            result[rarity].append({'name': name, 'tier': tier})
            
    return result


def fetch_champion(champion_name, champ_tier='S'):
    """抓取单个英雄的增强推荐数据"""
    url = BASE_URL.format(champion_name)
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml',
        'Accept-Language': 'en-US,en;q=0.9',
    }
    
    req = urllib.request.Request(url, headers=headers)
    
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            html = response.read().decode('utf-8')
    except Exception as e:
        return {'error': str(e), 'champion': URL_TO_DISPLAY.get(champion_name, champion_name)}
    
    # 用正则提取
    augments = extract_with_regex(html)
    
    # 统计
    total = sum(len(v) for v in augments.values())
    s_count = sum(1 for r in augments.values() for a in r if a['tier'] == 'S')
    a_count = sum(1 for r in augments.values() for a in r if a['tier'] == 'A')
    b_count = sum(1 for r in augments.values() for a in r if a['tier'] == 'B')
    
    return {
        'champion': URL_TO_DISPLAY.get(champion_name, champion_name),
        'champion_en': URL_TO_DISPLAY.get(champion_name, champion_name),
        'champion_url_name': champion_name,
        'tier': champ_tier,
        'url': url,
        'augments': augments,
        'stats': {
            'total': total,
            's_tier': s_count,
            'a_tier': a_count,
            'b_tier': b_count,
            'by_rarity': {r: len(v) for r, v in augments.items()}
        }
    }


def main():
    results = []
    success = 0
    fail = 0
    
    total_champs = len(ALL_CHAMPIONS)
    
    for i, champ in enumerate(ALL_CHAMPIONS, 1):
        tier = CHAMPION_TIER.get(champ, 'S')
        print(f"[{i}/{total_champs}] 正在抓取 {champ} ({tier}级) ...", flush=True)
        data = fetch_champion(champ, champ_tier=tier)
        results.append(data)
        
        if 'error' not in data:
            print(f"  OK {data['stats']['total']} augments "
                  f"(S:{data['stats']['s_tier']} A:{data['stats']['a_tier']} B:{data['stats']['b_tier']})",
                  flush=True)
            success += 1
        else:
            print(f"  FAIL: {data['error']}", flush=True)
            fail += 1
            
        time.sleep(1)  # 礼貌性延迟
    
    # 输出 JSON
    output_path = 'pipeline/output/blitz_champion_augments_sample.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\nSaved to {output_path}")
    print(f"Success: {success}, Failed: {fail}")
    
    # 打印摘要
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    
    for r in results:
        if 'error' in r:
            print(f"\n{r['champion']}: ERROR - {r['error']}")
            continue
            
        print(f"\n[{r['champion']}] ({r['stats']['total']} augments)")
        for rarity in ['prismatic', 'gold', 'silver']:
            aug_list = r['augments'][rarity]
            if not aug_list:
                continue
            rarity_label = {'prismatic': 'Prismatic', 'gold': 'Gold', 'silver': 'Silver'}[rarity]
            print(f"  {rarity_label} ({len(aug_list)}):")
            for a in aug_list:
                tier_mark = {'S': 'S', 'A': 'A', 'B': 'B'}[a['tier']]
                print(f"    [{tier_mark}] {a['name']}")


if __name__ == '__main__':
    main()
