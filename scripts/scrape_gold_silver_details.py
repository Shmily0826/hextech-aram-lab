"""scrape_gold_silver_details.py - Get detailed numbers for gold/silver augments."""
import json, os, urllib.request, re, time, html as html_lib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
with open(os.path.join(ROOT, 'data', 'augments.json'), 'r', encoding='utf-8') as f:
    augs = json.load(f)

aug_map = {a['id']: a for a in augs}
active = [a for a in augs if a.get('status') == 'active']

# Gold and silver without numbers in CN effect
targets = [a for a in active 
           if a.get('tier') in ('gold', 'silver') 
           and not re.search(r'\d', a.get('effect', ''))]

gold_targets = [a for a in targets if a['tier'] == 'gold']
silver_targets = [a for a in targets if a['tier'] == 'silver']

print(f'Gold without numbers: {len(gold_targets)}/{sum(1 for a in active if a["tier"]=="gold")}')
print(f'Silver without numbers: {len(silver_targets)}/{sum(1 for a in active if a["tier"]=="silver")}')
print(f'Total targets: {len(targets)}\n')

def extract_astro_desc(page_html):
    pattern = r'component-url="[^"]*AugmentDescription[^"]*"[^>]*props="([^"]*)"'
    m = re.search(pattern, page_html)
    if m:
        props = html_lib.unescape(m.group(1))
        desc = re.search(r'"description"\s*:\s*\[\s*\d+\s*,\s*"((?:[^"\\]|\\.)*)"', props)
        if desc:
            return html_lib.unescape(desc.group(1))
    return None

def clean_markup(text):
    if not text:
        return ''
    text = text.replace('[br/]', ' ').replace('[br]', ' ')
    text = re.sub(r'\[stat:\w+\]', '', text)
    text = re.sub(r'\[/stat\]', '', text)
    text = re.sub(r'\[/?b\]', '', text)
    text = re.sub(r"<font[^>]*>", '', text)
    text = text.replace('</font>', '')
    text = re.sub(r'<\w+>', '', text)
    text = re.sub(r'</\w+>', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

results = {}

for a in targets:
    slug = a['id'].replace('_', '-')
    url = f'https://arammayhem.com/augments/{slug}'
    tier_tag = a['tier'].upper()
    print(f'[{tier_tag}] {a["id"]} ({a["name"]})...')
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            page_html = resp.read().decode('utf-8')
        
        en_desc = extract_astro_desc(page_html)
        if en_desc:
            clean = clean_markup(en_desc)
            has_nums = bool(re.search(r'\d', clean))
            marker = '+' if has_nums else '-'
            results[a['id']] = {'en_raw': en_desc, 'en_clean': clean, 'has_nums': has_nums, 'tier': a['tier']}
            print(f'  {marker} {clean[:140]}')
        else:
            print(f'  x No astro desc')
        
        time.sleep(0.5)
    except Exception as e:
        err = '404' if '404' in str(e) else str(e)[:50]
        print(f'  x {err}')

# Save raw
out_path = os.path.join(ROOT, 'pipeline', 'output', 'gold_silver_details_en.json')
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

# Summary
with_nums = {k: v for k, v in results.items() if v['has_nums']}
without_nums = {k: v for k, v in results.items() if not v['has_nums']}

print(f'\n{"="*60}')
print(f'Total scraped: {len(results)}/{len(targets)}')
print(f'With numbers: {len(with_nums)}')
print(f'Without numbers: {len(without_nums)}')
print(f'Not found (404 etc): {len(targets) - len(results)}')

# Show all with numbers
print(f'\n=== WITH NUMBERS ===\n')
for slug, data in sorted(with_nums.items()):
    t = data['tier'].upper()
    print(f'[{t}] {slug} ({aug_map[slug]["name"]})')
    print(f'    {data["en_clean"][:200]}')
    print()
