"""
scrape_missing_effects.py
Scrape Chinese effect descriptions from arammayhem.com for the 54 missing augments.
"""
import json, os, re, time, urllib.request, urllib.error

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

with open(os.path.join(ROOT, 'data', 'augments.json'), encoding='utf-8') as f:
    augs = json.load(f)

# Find augments missing both effect and effect_en
missing = []
for a in augs:
    en = (a.get('effect_en') or '').strip()
    cn = (a.get('effect') or '').strip()
    if not en and not cn:
        missing.append(a)

print(f"Found {len(missing)} augments missing effects")

# Build slug from aug id (replace _ with -)
def id_to_slug(aug_id):
    return aug_id.replace('_', '-')

# Scrape each from arammayhem.com Chinese page
results = []
for i, a in enumerate(missing):
    slug = id_to_slug(a['id'])
    url = f'https://arammayhem.com/zh-cn/augments/{slug}'
    print(f"\n[{i+1}/{len(missing)}] {a['name']} -> {url}")
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode('utf-8', errors='replace')
        
        # Try to find effect text in the page
        # Look for effect description patterns
        # Pattern 1: Look for text near "效果" heading
        effect_match = re.search(r'效果[^<]*</[^>]+>\s*<[^>]+>([^<]+)', html)
        if effect_match:
            effect_text = effect_match.group(1).strip()
            if len(effect_text) > 10:
                print(f"  Found effect: {effect_text[:80]}...")
                results.append({'id': a['id'], 'name': a['name'], 'effect': effect_text})
                continue
        
        # Pattern 2: Look for paragraph text after augment name
        # Try meta description
        meta_match = re.search(r'<meta[^>]*name="description"[^>]*content="([^"]+)"', html)
        if meta_match:
            meta_text = meta_match.group(1).strip()
            if len(meta_text) > 20 and a['name'] in meta_text:
                print(f"  Found meta: {meta_text[:80]}...")
                results.append({'id': a['id'], 'name': a['name'], 'effect': meta_text, 'source': 'meta'})
                continue
        
        # Pattern 3: Look for any substantial Chinese text block
        # Find all <p> or <div> with Chinese text
        text_blocks = re.findall(r'<(?:p|div|span)[^>]*>([^<]{20,})</(?:p|div|span)>', html)
        cn_blocks = [t.strip() for t in text_blocks if re.search(r'[\u4e00-\u9fff]{3,}', t)]
        if cn_blocks:
            # Filter out navigation/UI text
            good = [t for t in cn_blocks if '增强' not in t[:5] and '海克斯' not in t[:5] and '首页' not in t]
            if good:
                print(f"  Found text block: {good[0][:80]}...")
                results.append({'id': a['id'], 'name': a['name'], 'effect': good[0], 'source': 'text_block'})
                continue
        
        # Pattern 4: Try to get page text content
        # Strip all HTML tags
        clean = re.sub(r'<[^>]+>', ' ', html)
        clean = re.sub(r'\s+', ' ', clean)
        # Find Chinese text segments
        cn_segments = re.findall(r'[\u4e00-\u9fff\uff08\uff09，。、；：""''！？\d\.\+%s\-]{15,}', clean)
        if cn_segments:
            # Look for effect-like text (mentions numbers, seconds, damage, etc.)
            effect_like = [s for s in cn_segments if any(kw in s for kw in ['秒', '伤害', '治疗', '护盾', '生命', '攻击', '法术', '冷却', '速度', '效果', '持续', '获得', '提供'])]
            if effect_like:
                print(f"  Found effect-like: {effect_like[0][:80]}...")
                results.append({'id': a['id'], 'name': a['name'], 'effect': effect_like[0], 'source': 'effect_like'})
                continue
        
        print(f"  NOT FOUND")
        results.append({'id': a['id'], 'name': a['name'], 'effect': None})
        
    except Exception as e:
        print(f"  ERROR: {e}")
        results.append({'id': a['id'], 'name': a['name'], 'effect': None, 'error': str(e)})
    
    time.sleep(0.5)  # Be polite

# Summary
found = [r for r in results if r.get('effect')]
not_found = [r for r in results if not r.get('effect')]
print(f"\n=== Results ===")
print(f"Found: {len(found)}")
print(f"Not found: {len(not_found)}")
for r in not_found:
    print(f"  {r['name']} ({r['id']})")

# Save results
output_path = os.path.join(ROOT, 'pipeline', 'output', 'missing_effects_scrape.json')
os.makedirs(os.path.dirname(output_path), exist_ok=True)
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
print(f"\nSaved to {output_path}")
