"""
scrape_hero_pick_rates.py
Scrape champion win rate / pick rate from arammayhem.com/champions.
Pick rate is in the title attribute of <a> tags.
"""
import json
import os
import re
import time
import html as html_mod
import urllib.request
import urllib.error

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(PROJECT_ROOT, 'pipeline', 'output')
DATA_DIR = os.path.join(PROJECT_ROOT, 'data')

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
}

def fetch_page(url, retries=2):
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=30) as resp:
                return resp.read().decode('utf-8', errors='replace')
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
            if attempt < retries:
                print(f"  Retry {attempt+1}/{retries} for {url}: {e}")
                time.sleep(2)
            else:
                print(f"  FAILED: {url}: {e}")
                return None


def parse_champions(raw_html):
    """Parse champion entries. Pick rate is in the title attr of <a> tags."""
    entries = []
    
    # Match <a> tags with build links and title attributes
    # title contains: "Name\nRank: #N\nWin Rate: X%\nPick Rate: Y%"
    pattern = r'<a[^>]*href="/build/([a-z][a-z0-9-]+)/?"[^>]*title="([^"]*)"[^>]*>'
    
    for slug, title_raw in re.findall(pattern, raw_html, re.DOTALL):
        title = html_mod.unescape(title_raw)
        entry = {'slug': slug}
        
        # Parse title lines
        wr_m = re.search(r'Win Rate:\s*(\d+\.?\d*)%', title)
        pr_m = re.search(r'Pick Rate:\s*(\d+\.?\d*)%', title)
        rank_m = re.search(r'Rank:\s*#(\d+)', title)
        name_m = re.match(r'^(.+?)(?:\n|$)', title)
        
        if name_m:
            entry['name'] = name_m.group(1).strip()
        if wr_m:
            entry['win_rate'] = float(wr_m.group(1))
        if pr_m:
            entry['pick_rate'] = float(pr_m.group(1))
        if rank_m:
            entry['rank'] = int(rank_m.group(1))
        
        entries.append(entry)
    
    return entries


def parse_champions_cn(raw_html):
    """Parse CN champion entries for name mapping."""
    entries = []
    pattern = r'<a[^>]*href="/zh-cn/build/([a-z][a-z0-9-]+)/?"[^>]*title="([^"]*)"[^>]*>'
    
    for slug, title_raw in re.findall(pattern, raw_html, re.DOTALL):
        title = html_mod.unescape(title_raw)
        name_m = re.match(r'^(.+?)(?:\n|$)', title)
        name = name_m.group(1).strip() if name_m else ''
        entries.append({'slug': slug, 'name_cn': name})
    
    return entries


def main():
    print("=== Scraping Champion Pick Rates ===\n")
    
    # Fetch EN page
    print("Fetching EN champions page...")
    en_html = fetch_page("https://arammayhem.com/champions")
    en_entries = parse_champions(en_html) if en_html else []
    print(f"  Found {len(en_entries)} champions (EN)")
    
    time.sleep(1)
    
    # Fetch CN page for name mapping
    print("Fetching CN champions page...")
    cn_html = fetch_page("https://arammayhem.com/zh-cn/champions")
    cn_entries = parse_champions_cn(cn_html) if cn_html else []
    print(f"  Found {len(cn_entries)} champions (CN)")
    
    # Build slug -> data mapping
    slug_map = {}
    for e in en_entries:
        slug_map[e['slug']] = e
    for e in cn_entries:
        s = e['slug']
        if s in slug_map:
            slug_map[s]['name_cn'] = e.get('name_cn', '')
    
    # Save raw output
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_path = os.path.join(OUTPUT_DIR, 'hero_pick_rates.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(list(slug_map.values()), f, ensure_ascii=False, indent=2)
    print(f"\nRaw data saved to {output_path}")
    
    with_pr = sum(1 for e in slug_map.values() if 'pick_rate' in e)
    with_wr = sum(1 for e in slug_map.values() if 'win_rate' in e)
    print(f"With win rate: {with_wr}/{len(slug_map)}")
    print(f"With pick rate: {with_pr}/{len(slug_map)}")
    
    print("\nSample data:")
    for slug, e in list(slug_map.items())[:8]:
        nm = e.get('name', '?')
        cn = e.get('name_cn', '?')
        wr = e.get('win_rate', '?')
        pr = e.get('pick_rate', '?')
        print(f"  {slug}: {nm} ({cn}) WR={wr}% PR={pr}%")
    
    # Load champions.json and apply pick rates
    champ_path = os.path.join(DATA_DIR, 'champions.json')
    with open(champ_path, 'r', encoding='utf-8') as f:
        champ_data = json.load(f)
    
    champions = champ_data.get('champions', [])
    champ_keys = champ_data.get('championKeys', {})  # CN -> EN
    
    # Build EN name (lowercase, no spaces) -> CN name mapping
    en_norm_to_cn = {}
    for cn, en in champ_keys.items():
        key = en.lower().replace(' ', '').replace("'", '').replace('.', '')
        en_norm_to_cn[key] = cn
    
    updated_pr = 0
    updated_wr = 0
    
    for champ in champions:
        cn_name = champ.get('name', '')
        en_name = champ_keys.get(cn_name, '')
        en_key = en_name.lower().replace(' ', '').replace("'", '').replace('.', '')
        
        matched = None
        for slug, e in slug_map.items():
            slug_key = slug.replace('-', '')
            scraped_en = e.get('name', '').lower().replace(' ', '').replace("'", '').replace('.', '')
            scraped_cn = e.get('name_cn', '')
            
            if en_key == slug_key or en_key == scraped_en:
                matched = e
                break
            if cn_name and scraped_cn == cn_name:
                matched = e
                break
        
        if matched:
            if 'pick_rate' in matched and champ.get('pr') is None:
                champ['pr'] = matched['pick_rate']
                updated_pr += 1
            if 'win_rate' in matched:
                champ['wr'] = matched['win_rate']
                updated_wr += 1
    
    # Backup
    backup_path = os.path.join(OUTPUT_DIR, 'champions.backup.json')
    with open(backup_path, 'w', encoding='utf-8') as f:
        json.dump(champ_data, f, ensure_ascii=False, indent=2)
    print(f"\nBackup saved to {backup_path}")
    
    # Save updated data
    with open(champ_path, 'w', encoding='utf-8') as f:
        json.dump(champ_data, f, ensure_ascii=False, indent=2)
    
    print(f"\nUpdated pick rate: {updated_pr}/{len(champions)}")
    print(f"Updated win rate: {updated_wr}/{len(champions)}")
    
    # Verify
    has_pr = sum(1 for c in champions if c.get('pr') is not None)
    has_wr = sum(1 for c in champions if c.get('wr') is not None)
    print(f"\nFinal: {has_wr} with WR, {has_pr} with PR out of {len(champions)}")


if __name__ == '__main__':
    main()
