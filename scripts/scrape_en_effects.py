"""
scrape_en_effects.py
Scrape English effect descriptions from arammayhem.com for 54 removed augments.
Outputs candidates to pipeline/output/en_effects_scrape.json
"""
import json, os, time, re

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    import subprocess, sys
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'requests', 'beautifulsoup4'])
    import requests
    from bs4 import BeautifulSoup

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

with open(os.path.join(ROOT, 'data', 'augments.json'), encoding='utf-8') as f:
    augs = json.load(f)

# Find augments missing both effects
missing = [a for a in augs if not (a.get('effect') or '').strip() and not (a.get('effect_en') or '').strip()]

print(f"Found {len(missing)} augments missing both effects")

results = []
errors = []

for i, a in enumerate(missing):
    aug_id = a.get('id', '')
    name = a.get('name', '')
    name_en = a.get('name_en', '')
    
    # Convert id to URL slug format
    # The id is already in slug format from arammayhem.com
    url = f"https://arammayhem.com/augments/{aug_id}"
    
    print(f"[{i+1}/{len(missing)}] {name} ({name_en}) -> {url}")
    
    try:
        resp = requests.get(url, timeout=15, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        if resp.status_code != 200:
            print(f"  HTTP {resp.status_code}")
            errors.append({'id': aug_id, 'name': name, 'error': f'HTTP {resp.status_code}'})
            time.sleep(0.5)
            continue
        
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # Try to find the effect text - look for the main content area
        # arammayhem.com typically has effect text in a specific section
        effect_text = ''
        
        # Method 1: Look for paragraphs in main content
        main = soup.find('main') or soup.find('article') or soup
        paragraphs = main.find_all('p')
        
        for p in paragraphs:
            text = p.get_text(strip=True)
            # Skip meta/removed descriptions
            if 'removed' in text.lower() and 'aram mayhem' in text.lower():
                continue
            if len(text) > 30 and ('grant' in text.lower() or 'gain' in text.lower() or 
                                     'deal' in text.lower() or 'heal' in text.lower() or
                                     'cast' in text.lower() or 'your' in text.lower() or
                                     'enemy' in text.lower() or 'bonus' in text.lower() or
                                     'damage' in text.lower() or 'shield' in text.lower()):
                effect_text = text
                break
        
        # Method 2: If no paragraph found, look for any text block
        if not effect_text:
            for p in paragraphs:
                text = p.get_text(strip=True)
                if 'removed' in text.lower() and 'aram mayhem' in text.lower():
                    continue
                if len(text) > 20 and not text.startswith('http'):
                    effect_text = text
                    break
        
        if effect_text:
            print(f"  FOUND: {effect_text[:80]}...")
            results.append({
                'id': aug_id,
                'name': name,
                'name_en': name_en,
                'effect_en': effect_text,
                'source': 'arammayhem.com/en'
            })
        else:
            print(f"  NO EFFECT TEXT FOUND")
            errors.append({'id': aug_id, 'name': name, 'error': 'No effect text found on page'})
        
    except Exception as e:
        print(f"  ERROR: {e}")
        errors.append({'id': aug_id, 'name': name, 'error': str(e)})
    
    time.sleep(0.5)  # Rate limiting

# Save results
output = {
    'scraped_at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
    'total_requested': len(missing),
    'found': len(results),
    'errors': len(errors),
    'results': results,
    'error_details': errors
}

out_path = os.path.join(ROOT, 'pipeline', 'output', 'en_effects_scrape.json')
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f"\n=== 完成 ===")
print(f"  成功获取英文效果: {len(results)} 个")
print(f"  失败/未找到: {len(errors)} 个")
print(f"  输出: {out_path}")
