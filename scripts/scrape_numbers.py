"""scrape_numbers.py - Extract numerical effect descriptions from arammayhem.com EN pages."""
import json, os, urllib.request, re, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
with open(os.path.join(ROOT, 'data', 'augments.json'), 'r', encoding='utf-8') as f:
    augs = json.load(f)

aug_map = {a['id']: a for a in augs}
active = [a for a in augs if a.get('status') == 'active']
targets = [a for a in active if '?' in a.get('effect', '')]

SKIP_WORDS = [
    'Keep exploring', 'rarity augment in ARAM', 'rarity augment in the current',
    'Explore all', 'Check out', 'augments available', 'champions with',
    'Augments   Augment Sets', 'Combos    Updates', 'ARAM Mayhem is not endorsed',
    'Last updated', 'Best Champions', 'placed after stats', 'adsbygoogle',
    'Specifically Recommended', 'Submit Combo'
]

def clean_html(text):
    """Clean HTML tags and entities from text."""
    text = text.replace('&quot;', '"').replace('&#39;', "'").replace('&#x27;', "'").replace('&amp;', '&')
    text = re.sub(r'\[stat:\w+\]', '', text)
    text = re.sub(r'\[/stat\]', '', text)
    text = re.sub(r'\[/?b\]', '', text)
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'@\w+@', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def is_good_text(text):
    """Check if text is a real effect description, not navigation."""
    if len(text) < 15:
        return False
    if any(sw in text for sw in SKIP_WORDS):
        return False
    # Must contain some game-related words
    game_words = ['ability', 'damage', 'heal', 'shield', 'haste', 'speed', 'attack', 
                  'gain', 'critical', 'range', 'armor', 'magic', 'health', 'mana',
                  'cooldown', 'skill', 'cast', 'enemy', 'ally', 'champion', 'quest',
                  'your', 'grants', 'bonus', 'omnivamp', 'lifesteal', 'resist',
                  'task', 'reward', 'mark', 'dash', 'invulnerable']
    return any(w in text.lower() for w in game_words)

results = {}

for a in targets:
    slug = a['id']
    url = f'https://arammayhem.com/augments/{slug}'
    print(f'\n{slug} ({a["name"]})...')
    
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            html = resp.read().decode('utf-8')
        
        found_text = ''
        
        # Strategy 1: JSON description field  
        desc_match = re.search(r'"description"\s*:\s*\[?\d+\s*,\s*"((?:[^"\\]|\\.)*)"', html)
        if desc_match:
            raw = clean_html(desc_match.group(1))
            if is_good_text(raw):
                found_text = raw
                print(f'  [JSON] {raw[:120]}')
        
        # Strategy 2: Text fragments with game keywords (from "after heading" area)
        if not found_text:
            fragments = re.findall(r'>([^<]{10,300})<', html)
            candidates = []
            for frag in fragments:
                frag = clean_html(frag)
                if is_good_text(frag) and len(frag) > 15:
                    candidates.append(frag)
            
            if candidates:
                # Pick the longest one that looks like an effect
                candidates.sort(key=len, reverse=True)
                found_text = candidates[0]
                print(f'  [HTML] {found_text[:120]}')
        
        # Strategy 3: Look for effect text in span elements near the heading
        if not found_text:
            # Find content between h1 and the first h2 or grid section
            m = re.search(r'</h1>(.*?)(?:<h2|class="grid|<footer)', html, re.DOTALL)
            if m:
                section = m.group(1)
                texts = re.findall(r'<span[^>]*>([^<]{8,200})</span>', section)
                combined = ' '.join(clean_html(t) for t in texts if is_good_text(clean_html(t)))
                if combined:
                    found_text = combined
                    print(f'  [SPAN] {found_text[:120]}')
        
        if found_text:
            results[slug] = found_text
        else:
            print(f'  Not found')
        
        time.sleep(0.7)
    except Exception as e:
        print(f'  Error: {e}')

# Save raw results
out_path = os.path.join(ROOT, 'pipeline', 'output', 'detailed_effects_en.json')
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print(f'\n{"="*60}')
print(f'Got detailed EN effects for {len(results)}/{len(targets)} augments')
print(f'Saved to {out_path}')

# Show all results
print(f'\n{"="*60}')
print('All results:')
for slug, eff in sorted(results.items()):
    cn = aug_map[slug].get('effect', '')
    print(f'\n  {slug} ({aug_map[slug]["name"]})')
    print(f'    CN: {cn[:100]}')
    print(f'    EN: {eff[:150]}')
