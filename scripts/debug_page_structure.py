"""debug_page_structure.py - Show HTML structure around effect text for a sample augment."""
import urllib.request, re

SLUGS = ['jeweled_gauntlet', 'scoped_weapons', 'bread_and_cheese', 'warlock_juicebox']

for slug in SLUGS:
    url = f'https://arammayhem.com/augments/{slug}'
    print(f'\n{"="*60}')
    print(f'=== {slug} ===')
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            html = resp.read().decode('utf-8')
        
        # Find all text that could be the effect
        # Look for the description section
        # Try finding the main content area
        
        # Strategy 1: Look for text-muted-foreground class (common for descriptions)
        matches = re.findall(r'text-muted-foreground[^>]*>(.*?)</(?:p|div|span)', html, re.DOTALL)
        if matches:
            print('  [text-muted-foreground]:')
            for m in matches[:3]:
                clean = re.sub(r'<[^>]+>', '', m).strip()
                if len(clean) > 10:
                    print(f'    {clean[:200]}')
        
        # Strategy 2: Look for specific description container
        matches = re.findall(r'class="[^"]*description[^"]*"[^>]*>(.*?)</(?:p|div|span)', html, re.DOTALL)
        if matches:
            print('  [description class]:')
            for m in matches[:3]:
                clean = re.sub(r'<[^>]+>', '', m).strip()
                if len(clean) > 10:
                    print(f'    {clean[:200]}')
        
        # Strategy 3: Search for "Your" or common effect-starting words
        for pat in [r'>([^<]*(?:Your|Gain|Task|Casting|After)[^<]*(?:damage|healing|attack|ability|skill|shield|haste|speed|crit)[^<]*)<']:
            matches = re.findall(pat, html, re.IGNORECASE)
            if matches:
                print(f'  [effect-like text]:')
                seen = set()
                for m in matches[:5]:
                    m = m.strip()
                    if m not in seen and len(m) > 20:
                        seen.add(m)
                        print(f'    {m[:200]}')
        
        # Strategy 4: Look for the JSON data in __NEXT_DATA__ or similar
        next_data = re.search(r'<script[^>]*id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.DOTALL)
        if next_data:
            nd = next_data.group(1)[:500]
            print(f'  [__NEXT_DATA__ snippet]: {nd[:300]}')
        
        # Strategy 5: Look for inline script with augment data
        for m in re.finditer(r'(?:augmentData|augment_data|AUGMENT)\s*[:=]\s*(\{[^}]{50,500}\})', html):
            print(f'  [inline data]: {m.group(1)[:200]}')
        
        # Strategy 6: Look for the rendered effect in a specific span/div
        # Find the section right after the augment name
        name_section = re.search(r'<h[12][^>]*>[^<]*</h[12]>\s*(.*?)(?:<h[12]|<div class="grid|<footer)', html, re.DOTALL)
        if name_section:
            content = name_section.group(1)
            # Find all text in this area
            texts = re.findall(r'>([^<]{15,})<', content)
            print(f'  [after heading texts]:')
            for t in texts[:5]:
                t = t.strip()
                if t and not any(sw in t for sw in ['Augments', 'Augment Sets', 'Combos', 'Updates', 'Patch Notes']):
                    print(f'    {t[:200]}')
        
        import time
        time.sleep(0.5)
    except Exception as e:
        print(f'  Error: {e}')
