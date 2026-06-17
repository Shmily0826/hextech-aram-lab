"""scrape_remaining_cn.py - Get CN page data for the 12 remaining ? augments."""
import json, os, urllib.request, re, time, html as html_lib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
with open(os.path.join(ROOT, 'data', 'augments.json'), 'r', encoding='utf-8') as f:
    augs = json.load(f)

aug_map = {a['id']: a for a in augs}
active = [a for a in augs if a.get('status') == 'active']
remaining = [a for a in active if '?' in a.get('effect', '')]

def extract_astro_desc(page_html):
    """Extract from astro-island component."""
    pattern = r'component-url="[^"]*AugmentDescription[^"]*"[^>]*props="([^"]*)"'
    m = re.search(pattern, page_html)
    if m:
        props = html_lib.unescape(m.group(1))
        desc = re.search(r'"description"\s*:\s*\[\s*\d+\s*,\s*"((?:[^"\\]|\\.)*)"', props)
        if desc:
            return html_lib.unescape(desc.group(1))
    return None

print(f'Fetching CN pages for {len(remaining)} remaining augments...\n')

for a in remaining:
    slug = a['id'].replace('_', '-')
    url = f'https://arammayhem.com/zh-cn/augments/{slug}'
    print(f'{a["id"]} ({a["name"]})...')
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            page_html = resp.read().decode('utf-8')
        
        cn_desc = extract_astro_desc(page_html)
        if cn_desc:
            print(f'  CN raw: {cn_desc[:200]}')
        else:
            print(f'  CN: no astro desc found')
        
        time.sleep(0.5)
    except Exception as e:
        print(f'  Error: {e}')
