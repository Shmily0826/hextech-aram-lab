"""scrape_detailed_effects.py - Get full numerical effects from arammayhem.com EN pages."""
import json, os, urllib.request, re, time
from html.parser import HTMLParser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
with open(os.path.join(ROOT, 'data', 'augments.json'), 'r', encoding='utf-8') as f:
    augs = json.load(f)

aug_map = {a['id']: a for a in augs}
active = [a for a in augs if a.get('status') == 'active']

# Skip words for navigation text
SKIP_WORDS = [
    'Keep exploring', 'rarity augment in ARAM', 'rarity augment in the current',
    'Explore all', 'Check out', 'augments available', 'champions with'
]

# Targets: augments with ? in CN effect
targets = [a for a in active if '?' in a.get('effect', '')]
print(f'Targets: {len(targets)} augments with ? placeholders')

# Also check all augments for incomplete EN effects
for a in active:
    en = a.get('effect_en', '')
    if not en or len(en) < 10:
        if a not in targets:
            targets.append(a)

print(f'Total targets (incl missing EN): {len(targets)}')

results = {}

for a in targets:
    slug = a['id']
    url = f'https://arammayhem.com/augments/{slug}'
    print(f'\n{slug}...')
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            html = resp.read().decode('utf-8')
        
        # Strategy 1: Extract from JSON-LD or inline data
        # Look for the description in structured data
        desc_match = re.search(r'"description"\s*:\s*\[?\d+\s*,\s*"([^"]+)"', html)
        if desc_match:
            raw = desc_match.group(1)
            # Decode HTML entities
            raw = raw.replace('&quot;', '"').replace('&#39;', "'").replace('&amp;', '&')
            # Clean [stat:xxx]...[/stat] tags
            raw = re.sub(r'\[stat:\w+\]', '', raw)
            raw = re.sub(r'\[/stat\]', '', raw)
            raw = re.sub(r'\[/?b\]', '', raw)
            raw = re.sub(r'@(\w+)@', r'\1', raw)  # @VarName@ -> VarName
            raw = raw.strip()
            
            if any(sw.lower() in raw.lower() for sw in SKIP_WORDS):
                print(f'  JSON desc is nav text, skipping')
            elif len(raw) > 15:
                print(f'  JSON: {raw[:100]}')
                results[slug] = raw
                continue
        
        # Strategy 2: Extract from the effect description paragraph
        # Look for <p> tags in the main content area
        paras = re.findall(r'<p[^>]*>(.*?)</p>', html, re.DOTALL)
        best_para = ''
        for p in paras:
            clean = re.sub(r'<[^>]+>', '', p).strip()
            clean = clean.replace('&quot;', '"').replace('&#39;', "'").replace('&amp;', '&')
            # Skip navigation/guide text
            if any(sw.lower() in clean.lower() for sw in SKIP_WORDS):
                continue
            if any(kw in clean for kw in ['虚空裂隙前期', '装备出法穿', '打团千万别']):
                continue
            if len(clean) > len(best_para) and len(clean) > 20:
                best_para = clean
        
        if best_para:
            # Clean up remaining formatting
            best_para = re.sub(r'\[stat:\w+\]', '', best_para)
            best_para = re.sub(r'\[/stat\]', '', best_para)
            best_para = re.sub(r'\[/?b\]', '', best_para)
            print(f'  HTML: {best_para[:100]}')
            results[slug] = best_para
        else:
            print(f'  No effect text found')
        
        time.sleep(0.7)
    except Exception as e:
        print(f'  Error: {e}')

# Save results to pipeline/output
out_path = os.path.join(ROOT, 'pipeline', 'output', 'detailed_effects_en.json')
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print(f'\n=== Results ===')
print(f'Got effects for {len(results)}/{len(targets)} augments')
print(f'Saved to {out_path}')

# Show samples
for slug, eff in list(results.items())[:5]:
    print(f'\n  {slug}: {eff[:150]}')
