"""
scrape_blitz_hero_stats.py (v2)
Extract hero-level win rate and game count from blitz.gg ARAM Mayhem pages.
Parses embedded SvelteKit JSON blocks for precise build-level stats.
Computes weighted average win rate across all build types.
"""
import json
import os
import re
import time
import urllib.request
import urllib.error

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(PROJECT_ROOT, 'pipeline', 'output')
DATA_DIR = os.path.join(PROJECT_ROOT, 'data')

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
}

# All 172 champions
S_TIER = ['Sion','Sett','Kayle','Lillia','Rell','Gwen','Fiora','Zaahen','Seraphine','DrMundo',
          'Shyvana','Shen','Brand','Jinx','Hwei','AurelionSol','Ekko','Malzahar','Galio','Nasus',
          'Graves','Vayne','Aphelios','Maokai']
A_TIER = ['Sona','Illaoi','Heimerdinger','Viktor','Singed','Jax','Aurora','MasterYi','TwistedFate',
          'Kassadin','Zyra','XinZhao','Ryze','MonkeyKing','Hecarim','Ornn','Yasuo','Trundle',
          'Soraka','Taric','Rumble','Leona','Karthus','Zilean','Volibear','Briar','KogMaw','Kayn',
          'Ahri','Renata','Nautilus','Janna','Morgana']
B_TIER = ['Caitlyn','Milio','Kled','TahmKench','Amumu','Senna','Xayah','Sylas','Poppy','VelKoz',
          'Yone','Olaf','Mordekaiser','Alistar','Rammus','Kalista','Syndra','Sejuani','Ambessa',
          'Veigar','Vladimir','RekSai','Ashe','MissFortune','Swain','Skarner','Samira','Lux','Sivir',
          'Azir','Gangplank','Riven','Vex','Nami','Fiddlesticks','Fizz','Yunara','Tryndamere',
          'ChoGath','Teemo','Ivern','Yuumi','Ziggs','Jhin','Vi','Kindred','Warwick','Orianna',
          'KaiSa','Annie','Akshan','Urgot','Draven','Xerath']
C_TIER = ['Udyr','Gragas','Mel','Rengar','Viego','Nilah','Twitch','Pantheon','Varus','Diana',
          'Renekton','JarvanIV','Yorick','Tristana','Cassiopeia','Smolder','Rakan','Corki',
          'Malphite','Darius','Karma','Katarina','Garen','Zac','Ezreal','Nocturne','Talon',
          'Zeri','Gnar','Lulu','BelVeth','Lucian','Taliyah','Zed','Lissandra']
D_TIER = ['Anivia','Elise','Evelynn','Braum','Zoe','Pyke','Irelia','Nunu','Neeko','Naafiri',
          'Aatrox','Nidalee','Blitzcrank','Camille','Shaco','Akali','Quinn','Jayce','Kennen',
          'Khazix','Qiyana','Thresh','KSante','Leblanc','Bard','LeeSin']

ALL_CHAMPIONS = S_TIER + A_TIER + B_TIER + C_TIER + D_TIER

URL_TO_DISPLAY = {
    'DrMundo': 'Dr. Mundo', 'AurelionSol': 'Aurelion Sol',
    'Renata': 'Renata Glasc', 'MonkeyKing': 'Wukong',
    'TahmKench': 'Tahm Kench', 'ChoGath': "Cho'Gath",
    'KaiSa': "Kai'Sa", 'KogMaw': "Kog'Maw",
    'RekSai': "Rek'Sai", 'BelVeth': "Bel'Veth",
    'MissFortune': 'Miss Fortune', 'TwistedFate': 'Twisted Fate',
    'MasterYi': 'Master Yi', 'XinZhao': 'Xin Zhao',
    'VelKoz': "Vel'Koz", 'JarvanIV': 'Jarvan IV',
    'KSante': "K'Sante", 'Khazix': "Kha'Zix",
    'LeeSin': 'Lee Sin', 'Leblanc': 'LeBlanc',
}

NAME_ALIASES = {
    '奥瑞利安索尔': '铸星龙王',
    '蒙多医生': '祖安狂人',
    '易大师': '无极剑圣',
}


def fetch_page(url, retries=2):
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=30) as resp:
                return resp.read().decode('utf-8', errors='replace')
        except Exception as e:
            if attempt < retries:
                time.sleep(2)
            else:
                return None


def extract_build_stats(html):
    """Extract build-level stats from embedded SvelteKit JSON blocks.
    
    Looks for JSON blocks containing build_type_name, win_rate, games keys.
    Returns list of {build_type, games, win_rate} dicts.
    """
    builds = []
    
    # Extract all application/json script blocks
    json_blocks = re.findall(
        r'<script\s+type="application/json"[^>]*>(.*?)</script>',
        html, re.DOTALL
    )
    
    for block in json_blocks:
        try:
            data = json.loads(block)
            body = data.get('body', '')
            if not isinstance(body, str):
                continue
            if 'build_type_name' not in body:
                continue
            
            body_data = json.loads(body)
            if not isinstance(body_data, dict):
                continue
            
            items = body_data.get('data', [])
            if not isinstance(items, list):
                continue
            
            for item in items:
                if not isinstance(item, dict):
                    continue
                if 'build_type_name' in item and 'win_rate' in item and 'games' in item:
                    builds.append({
                        'build_type': item.get('build_type_name', ''),
                        'games': item['games'],
                        'win_rate': round(item['win_rate'] * 100, 2),
                    })
        except (json.JSONDecodeError, KeyError, TypeError):
            continue
    
    return builds


def extract_tier(html):
    """Extract champion tier from tier SVG image."""
    tier_match = re.search(r'tier-([a-z])\.svg', html)
    if tier_match:
        return tier_match.group(1).upper()
    return None


def extract_overall_stats(html):
    """Try to extract overall stats from the role-level JSON block."""
    json_blocks = re.findall(
        r'<script\s+type="application/json"[^>]*>(.*?)</script>',
        html, re.DOTALL
    )
    
    for block in json_blocks:
        try:
            data = json.loads(block)
            body = data.get('body', '')
            if not isinstance(body, str):
                continue
            if 'champion_role_tier' not in body:
                continue
            
            body_data = json.loads(body)
            items = body_data.get('data', [])
            if not isinstance(items, list):
                continue
            
            # Find the entry with most games (likely ARAM/main mode)
            best = None
            for item in items:
                if not isinstance(item, dict):
                    continue
                games = item.get('games', 0)
                if games > 100 and (best is None or games > best.get('games', 0)):
                    best = item
            
            if best:
                return {
                    'games': best['games'],
                    'win_rate': round(best.get('win_rate', 0) * 100, 2),
                    'pick_rate': round(best.get('pick_rate', 0) * 100, 2) if best.get('pick_rate') else None,
                }
        except (json.JSONDecodeError, KeyError, TypeError):
            continue
    
    return None


def load_champions_map():
    path = os.path.join(DATA_DIR, 'champions.json')
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    champ_keys = data.get('championKeys', {})
    id_to_cn = {v: k for k, v in champ_keys.items()}
    return id_to_cn


def main():
    print('=== Scraping Hero Stats from blitz.gg (v2) ===\n')
    
    id_to_cn = load_champions_map()
    results = []
    errors = []
    total = len(ALL_CHAMPIONS)
    
    for i, champ in enumerate(ALL_CHAMPIONS):
        display = URL_TO_DISPLAY.get(champ, champ)
        url = f'https://blitz.gg/lol/champions/{champ}/aram-mayhem'
        
        if (i + 1) % 20 == 0 or i == 0:
            print(f'  [{i+1}/{total}] {display}...')
        
        html = fetch_page(url)
        if not html:
            errors.append({'champion': champ, 'error': 'fetch failed'})
            continue
        
        builds = extract_build_stats(html)
        tier = extract_tier(html)
        overall = extract_overall_stats(html)
        
        # Compute weighted average from builds
        if builds:
            total_games = sum(b['games'] for b in builds)
            weighted_wr = sum(b['win_rate'] * b['games'] for b in builds) / total_games
        elif overall:
            total_games = overall['games']
            weighted_wr = overall['win_rate']
        else:
            total_games = 0
            weighted_wr = None
        
        cn_name = id_to_cn.get(champ, '')
        cn_name = NAME_ALIASES.get(cn_name, cn_name)
        
        entry = {
            'champion': champ,
            'display': display,
            'cn_name': cn_name,
            'tier_blitz': tier,
            'builds': builds,
            'total_games': total_games,
            'weighted_win_rate': round(weighted_wr, 2) if weighted_wr else None,
            'overall': overall,
        }
        results.append(entry)
        
        if weighted_wr is None:
            errors.append({'champion': champ, 'error': 'no stats extracted'})
        
        time.sleep(0.5)
    
    # Save
    output = {
        'source': 'blitz.gg',
        'scraped_at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        'total': total,
        'success': len(results),
        'with_stats': sum(1 for r in results if r['weighted_win_rate'] is not None),
        'errors': len(errors),
        'results': results,
        'error_details': errors,
    }
    
    output_file = os.path.join(OUTPUT_DIR, 'blitz_hero_stats_scrape.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f'\n=== Results ===')
    print(f'  Total: {total}, Success: {len(results)}, With stats: {output["with_stats"]}, Errors: {len(errors)}')
    print(f'  Saved: {output_file}')
    
    if errors:
        print(f'\n  Errors ({len(errors)}):')
        for e in errors[:5]:
            print(f'    {e["champion"]}: {e["error"]}')
    
    # Show top results
    with_stats = sorted(
        [r for r in results if r['weighted_win_rate']],
        key=lambda r: r['total_games'], reverse=True
    )
    print(f'\n  Top 10 by games:')
    for r in with_stats[:10]:
        print(f'    {r["display"]} ({r["cn_name"]}): WR={r["weighted_win_rate"]}% Games={r["total_games"]:,} Builds={len(r["builds"])}')


if __name__ == '__main__':
    main()
