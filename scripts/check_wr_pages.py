"""check_wr_pages.py - Debug win rate pages for jeweled_gauntlet and soul_siphon."""
import urllib.request, re

SLUGS = ['jeweled_gauntlet', 'soul_siphon']

for slug in SLUGS:
    url = f'https://arammayhem.com/augments/{slug}'
    print(f'\n=== {slug} ({url}) ===')
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            html = resp.read().decode('utf-8')
        
        # Search for percentage patterns in context
        for m in re.finditer(r'(\d{1,3}\.?\d*)\s*%', html):
            start = max(0, m.start() - 60)
            end = min(len(html), m.end() + 20)
            ctx = html[start:end].replace('\n', ' ').strip()
            print(f'  Found: ...{ctx}...')
        
        # Also search for win_rate in JSON data
        for m in re.finditer(r'"winRate"[\s:]+[\d.]+', html):
            ctx = html[m.start():m.end()+20].strip()
            print(f'  JSON: {ctx}')
        for m in re.finditer(r'"pickRate"[\s:]+[\d.]+', html):
            ctx = html[m.start():m.end()+20].strip()
            print(f'  JSON: {ctx}')
    except Exception as e:
        print(f'  Error: {e}')
