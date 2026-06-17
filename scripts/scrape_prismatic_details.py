"""scrape_prismatic_details.py - Get detailed numbers for prismatic augments from EN pages."""
import json, os, urllib.request, re, time, html as html_lib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
with open(os.path.join(ROOT, 'data', 'augments.json'), 'r', encoding='utf-8') as f:
    augs = json.load(f)

aug_map = {a['id']: a for a in augs}
active = [a for a in augs if a.get('status') == 'active']
prismatic = [a for a in active if a.get('tier') == 'prismatic']

# Targets: prismatic without numbers in CN
targets = [a for a in prismatic if not re.search(r'\d', a.get('effect', ''))]
print(f'Targets: {len(targets)} prismatic augments without numbers\n')

def extract_astro_desc(page_html):
    """Extract description from astro-island AugmentDescription component."""
    pattern = r'component-url="[^"]*AugmentDescription[^"]*"[^>]*props="([^"]*)"'
    m = re.search(pattern, page_html)
    if m:
        props = html_lib.unescape(m.group(1))
        desc = re.search(r'"description"\s*:\s*\[\s*\d+\s*,\s*"((?:[^"\\]|\\.)*)"', props)
        if desc:
            return html_lib.unescape(desc.group(1))
    return None

results = {}

for a in targets:
    slug = a['id'].replace('_', '-')
    url = f'https://arammayhem.com/augments/{slug}'
    print(f'{a["id"]} ({a["name"]})...')
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            page_html = resp.read().decode('utf-8')
        
        en_desc = extract_astro_desc(page_html)
        if en_desc:
            # Clean markup but keep numbers visible
            clean = en_desc
            clean = clean.replace('[br/]', ' ').replace('[br]', ' ')
            clean = re.sub(r'\[stat:\w+\]', '', clean)
            clean = re.sub(r'\[/stat\]', '', clean)
            clean = re.sub(r'\[/?b\]', '', clean)
            clean = re.sub(r"<font[^>]*>", '', clean)
            clean = clean.replace('</font>', '')
            clean = re.sub(r'<\w+>', '', clean)
            clean = re.sub(r'</\w+>', '', clean)
            clean = re.sub(r'\s+', ' ', clean).strip()
            
            results[a['id']] = {'en_raw': en_desc, 'en_clean': clean}
            has_nums = bool(re.search(r'\d', clean))
            marker = '🔢' if has_nums else '❌'
            print(f'  {marker} EN: {clean[:160]}')
        else:
            print(f'  ❌ No astro desc found')
        
        time.sleep(0.6)
    except Exception as e:
        print(f'  Error: {e}')

# Save
out_path = os.path.join(ROOT, 'pipeline', 'output', 'prismatic_details_en.json')
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

# Summary
with_nums = {k: v for k, v in results.items() if re.search(r'\d', v['en_clean'])}
print(f'\n{"="*60}')
print(f'Total scraped: {len(results)}/{len(targets)}')
print(f'With numbers: {len(with_nums)}')
print(f'Without numbers: {len(results) - len(with_nums)}')

print(f'\n=== WITH NUMBERS ===')
for slug, data in sorted(with_nums.items()):
    print(f'\n  {slug}:')
    print(f'    {data["en_clean"][:200]}')
