"""Inspect champion page HTML to find pick rate location."""
import urllib.request, re

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
req = urllib.request.Request('https://arammayhem.com/champions', headers=HEADERS)
html = urllib.request.urlopen(req, timeout=30).read().decode('utf-8', errors='replace')

# Find "Pick" context - show surrounding HTML
print("=== Contexts around 'Pick Rate' ===")
for m in re.finditer(r'.{0,100}Pick.{0,100}', html):
    ctx = m.group()
    if 'Rate' in ctx or 'rate' in ctx:
        print(ctx[:200])
        print("---")
        break  # Just show first one

# Find actual champion links (with real slugs, not just "/build/")
champ_links = re.findall(r'<a\s+href="/build/([a-z][a-z0-9-]+)/?"[^>]*>(.*?)</a>', html, re.DOTALL)
print(f"\nChampion links with real slugs: {len(champ_links)}")

if champ_links:
    slug, inner = champ_links[0]
    print(f"\n=== First champion card: {slug} ===")
    print(f"Inner HTML length: {len(inner)}")
    print(f"Inner HTML (first 500):\n{inner[:500]}")
    
    # Get text content
    text = re.sub(r'<[^>]+>', ' ', inner)
    print(f"\nText: {text.strip()[:300]}")
    pcts = re.findall(r'(\d+\.?\d*)%', text)
    print(f"\nPercentages in text: {pcts}")

# Also look for a broader section - find champion entries by looking at a bigger context
# Maybe the champion data is in a larger container
print("\n=== Looking for champion data containers ===")
# Look for astro-island components
astro_matches = re.findall(r'<astro-island[^>]*>', html)
print(f"astro-island tags: {len(astro_matches)}")

# Look for data attributes or JSON data
json_data = re.findall(r'props="([^"]{100,})"', html)
print(f"Props attributes > 100 chars: {len(json_data)}")
if json_data:
    # Decode HTML entities and show first
    import html as html_mod
    decoded = html_mod.unescape(json_data[0])
    print(f"\nFirst props (decoded, first 500 chars):\n{decoded[:500]}")

# Try looking at broader pattern - maybe each champion is in a section or div
# Look for win rate percentage patterns near champion names
print("\n=== Searching for WR/PR pattern ===")
# Try pattern: number% followed by more text then another number%
wr_pr_pattern = re.findall(r'(\d+\.\d+)%.*?(\d+\.\d+)%', html[:50000], re.DOTALL)
if wr_pr_pattern:
    print(f"Found {len(wr_pr_pattern)} WR/PR pairs in first 50000 chars")
    for wr, pr in wr_pr_pattern[:3]:
        print(f"  WR={wr}% PR={pr}%")
else:
    print("No WR/PR pairs found in first 50000 chars")

# Check if Pick Rate is a label followed by value
pick_pattern = re.findall(r'Pick\s*Rate[:\s]*(\d+\.?\d*)%', html, re.IGNORECASE)
print(f"\n'Pick Rate: X%' pattern matches: {len(pick_pattern)}")
if pick_pattern:
    print(f"First 5: {pick_pattern[:5]}")
