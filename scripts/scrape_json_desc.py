"""scrape_json_desc.py - Extract effect text from JSON description field in page HTML."""
import json, os, urllib.request, re, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
with open(os.path.join(ROOT, 'data', 'augments.json'), 'r', encoding='utf-8') as f:
    augs = json.load(f)

aug_map = {a['id']: a for a in augs}
active = [a for a in augs if a.get('status') == 'active']
targets = [a for a in active if '?' in a.get('effect', '')]

NAV_TEXTS = ['Keep exploring', 'rarity augment in ARAM', 'rarity augment in the current',
             'When selecting augments', 'is particularly effective']

def clean_desc(raw):
    """Clean raw description from [stat:xxx][b]...[/b][/stat] markup."""
    raw = raw.replace('&quot;', '"').replace('&#39;', "'").replace('&#x27;', "'").replace('&amp;', '&')
    raw = raw.replace('\\n', ' ').replace('\\t', ' ')
    raw = re.sub(r'\[stat:\w+\]', '', raw)
    raw = re.sub(r'\[/stat\]', '', raw)
    raw = re.sub(r'\[/?b\]', '', raw)
    raw = re.sub(r'@\w+@', lambda m: m.group(0)[1:-1], raw)  # @VarName@ -> VarName
    raw = re.sub(r'\s+', ' ', raw).strip()
    return raw

results = {}

# Try both EN and CN pages for each
for a in targets:
    slug = a['id']
    print(f'\n{slug} ({a["name"]})...')
    
    found = False
    for lang, base_url in [('EN', 'https://arammayhem.com/augments/'), 
                            ('CN', 'https://arammayhem.com/zh-cn/augments/')]:
        if found:
            break
        url = base_url + slug
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=10) as resp:
                html = resp.read().decode('utf-8')
            
            # Find ALL description patterns in the HTML
            descs = []
            
            # Pattern 1: "description":[N,"text"]
            for m in re.finditer(r'"description"\s*:\s*\[\s*\d+\s*,\s*"((?:[^"\\]|\\.)*)"', html):
                raw = clean_desc(m.group(1))
                if len(raw) > 15 and not any(nt in raw for nt in NAV_TEXTS):
                    descs.append(raw)
            
            # Pattern 2: "description":"text" (direct)
            for m in re.finditer(r'"description"\s*:\s*"((?:[^"\\]|\\.)*)"', html):
                raw = clean_desc(m.group(1))
                if len(raw) > 15 and not any(nt in raw for nt in NAV_TEXTS):
                    descs.append(raw)
            
            # Pattern 3: Look for effect text in span.text-stat or specific containers
            for m in re.finditer(r'class="[^"]*(?:text-stat|effect-text|augment-desc)[^"]*"[^>]*>(.*?)</(?:span|p|div)', html, re.DOTALL):
                raw = re.sub(r'<[^>]+>', '', m.group(1)).strip()
                raw = clean_desc(raw)
                if len(raw) > 15:
                    descs.append(raw)
            
            if descs:
                # Pick longest unique description
                descs = list(set(descs))
                descs.sort(key=len, reverse=True)
                best = descs[0]
                results[slug] = {'text': best, 'lang': lang, 'all': descs[:3]}
                print(f'  [{lang}] {best[:150]}')
                found = True
            
            time.sleep(0.6)
        except Exception as e:
            if '404' not in str(e):
                print(f'  [{lang}] Error: {e}')
    
    if not found:
        print(f'  Not found on any page')

# Save
out_path = os.path.join(ROOT, 'pipeline', 'output', 'json_desc_effects.json')
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump({k: v['text'] for k, v in results.items()}, f, ensure_ascii=False, indent=2)

print(f'\n{"="*60}')
print(f'Got JSON descriptions for {len(results)}/{len(targets)} augments')

# Show which ones have actual numbers vs still have ?
with_nums = []
with_q = []
for slug, data in results.items():
    text = data['text']
    if '?' in text:
        with_q.append(slug)
    else:
        with_nums.append(slug)

print(f'  With actual numbers: {len(with_nums)}')
print(f'  Still has ?: {len(with_q)}')
