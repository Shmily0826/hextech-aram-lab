"""dump_html_section.py - Dump the relevant HTML section of an augment page."""
import urllib.request, re, time

SLUGS = ['scoped-weapons', 'ok-boomerang', 'bread-and-cheese', 'warlock-juicebox']

for slug in SLUGS:
    url = f'https://arammayhem.com/augments/{slug}'
    print(f'\n{"="*70}')
    print(f'=== {slug} ===')
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            html = resp.read().decode('utf-8')
        
        # Find the section between the H1 and the first stats/table section
        # Look for the augment description area
        h1_match = re.search(r'<h1[^>]*>(.*?)</h1>', html, re.DOTALL)
        if h1_match:
            h1_pos = h1_match.end()
            # Get the next 3000 chars after h1
            section = html[h1_pos:h1_pos+3000]
            
            # Find all <p> and <span> elements with effect-like text
            elements = re.findall(r'<(?:p|span|div)[^>]*>(.*?)</(?:p|span|div)>', section, re.DOTALL)
            for el in elements:
                clean = re.sub(r'<[^>]+>', '', el).strip()
                if clean and len(clean) > 5:
                    print(f'  <element> {clean[:200]}')
            
            # Also show the raw HTML (truncated) for structure analysis
            # Look for "text-muted" or effect containers
            effect_section = re.search(r'(text-muted-foreground[^>]*>.*?</(?:p|div)>)', section, re.DOTALL)
            if effect_section:
                print(f'\n  [RAW effect section]:')
                print(f'  {effect_section.group(1)[:400]}')
        
        time.sleep(0.5)
    except Exception as e:
        print(f'  Error: {e}')
