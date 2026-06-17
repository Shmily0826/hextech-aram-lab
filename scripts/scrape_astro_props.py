"""scrape_astro_props.py - Extract effect text from astro-island props JSON."""
import json, os, urllib.request, re, time, html as html_lib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
with open(os.path.join(ROOT, 'data', 'augments.json'), 'r', encoding='utf-8') as f:
    augs = json.load(f)

aug_map = {a['id']: a for a in augs}
active = [a for a in augs if a.get('status') == 'active']
targets = [a for a in active if '?' in a.get('effect', '')]

def clean_effect(raw):
    """Clean augment effect markup to plain text."""
    raw = html_lib.unescape(raw)
    raw = re.sub(r'\[stat:\w+\]', '', raw)
    raw = re.sub(r'\[/stat\]', '', raw)
    raw = re.sub(r'\[/?b\]', '', raw)
    raw = re.sub(r'<\w+>', '', raw)
    raw = re.sub(r'</\w+>', '', raw)
    raw = re.sub(r'\s+', ' ', raw).strip()
    return raw

def extract_from_page(html):
    """Extract description from astro-island props."""
    # Find the AugmentDescription component props
    pattern = r'component-url="[^"]*AugmentDescription[^"]*"[^>]*props="([^"]*)"'
    m = re.search(pattern, html)
    if m:
        props_escaped = html_lib.unescape(m.group(1))
        # Parse the description from props JSON
        desc_match = re.search(r'"description"\s*:\s*\[\s*\d+\s*,\s*"((?:[^"\\]|\\.)*)"', props_escaped)
        if desc_match:
            return clean_effect(desc_match.group(1))
    return None

results = {}

for a in targets:
    slug = a['id']
    cn_slug = slug.replace('_', '-')
    print(f'\n{slug} ({a["name"]})...')
    
    found_en = None
    found_cn = None
    
    # Try EN page
    url = f'https://arammayhem.com/augments/{cn_slug}'
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            page_html = resp.read().decode('utf-8')
        found_en = extract_from_page(page_html)
        if found_en:
            print(f'  EN: {found_en[:150]}')
        time.sleep(0.5)
    except Exception as e:
        if '404' not in str(e):
            print(f'  EN error: {e}')
    
    # Try CN page
    url_cn = f'https://arammayhem.com/zh-cn/augments/{cn_slug}'
    try:
        req = urllib.request.Request(url_cn, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            page_html = resp.read().decode('utf-8')
        found_cn = extract_from_page(page_html)
        if found_cn:
            print(f'  CN: {found_cn[:150]}')
        time.sleep(0.5)
    except Exception as e:
        if '404' not in str(e):
            print(f'  CN error: {e}')
    
    if found_en or found_cn:
        results[slug] = {'en': found_en, 'cn': found_cn}
    else:
        print(f'  Not found')

# Save raw results
out_path = os.path.join(ROOT, 'pipeline', 'output', 'astro_effects.json')
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print(f'\n{"="*60}')
print(f'Got astro effects for {len(results)}/{len(targets)} augments')

# Categorize
has_numbers = 0
still_q = 0
for slug, data in results.items():
    en = data.get('en', '') or ''
    cn = data.get('cn', '') or ''
    combined = en + ' ' + cn
    if re.search(r'\d', combined):
        has_numbers += 1
    else:
        still_q += 1

print(f'  With actual numbers: {has_numbers}')
print(f'  Without numbers: {still_q}')

# Show all results with numbers
print(f'\n{"="*60}')
print('Results with numbers:')
for slug, data in sorted(results.items()):
    en = data.get('en', '') or '-'
    cn = data.get('cn', '') or '-'
    cur_cn = aug_map[slug].get('effect', '')
    print(f'\n  {slug} ({aug_map[slug]["name"]})')
    print(f'    Current CN: {cur_cn[:100]}')
    print(f'    New EN:     {en[:150]}')
    print(f'    New CN:     {cn[:150]}')
