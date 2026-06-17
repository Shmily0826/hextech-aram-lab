"""Show the raw <a> tag for first champion to find pick rate location."""
import urllib.request, re

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
req = urllib.request.Request('https://arammayhem.com/champions', headers=HEADERS)
html = urllib.request.urlopen(req, timeout=30).read().decode('utf-8', errors='replace')

# Find the <a> tag for brand with everything between <a and >
m = re.search(r'<a\s[^>]*href="/build/brand/"[^>]*>', html)
if m:
    tag = m.group()
    print(f"Full opening <a> tag for brand ({len(tag)} chars):")
    print(repr(tag))
    print()
    print("Human readable:")
    print(tag)

# Also look for Pick Rate in a wider context - 200 chars before and after
idx = html.find('Pick Rate: 13.69%')
if idx >= 0:
    ctx = html[max(0,idx-200):idx+200]
    print(f"\n=== Context around 'Pick Rate: 13.69%' ===")
    print(repr(ctx))
