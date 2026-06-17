"""Debug: analyze raw HTML structure of blitz.gg champion page."""
import re

with open('pipeline/output/_debug_sion_raw.html', 'r', encoding='utf-8') as f:
    html = f.read()

print(f"HTML size: {len(html)} bytes")

# Check for embedded data patterns
patterns = {
    '__NEXT_DATA__': r'__NEXT_DATA__',
    '__NUXT': r'__NUXT',
    'window.__': r'window\.__',
    'application/json': r'application/json',
    'self.__next': r'self\.__next',
    'winRate': r'winRate',
    'win_rate': r'win_rate',
    'gamesPlayed': r'gamesPlayed',
    'playRate': r'playRate',
    'pickRate': r'pickRate',
    'totalGames': r'totalGames',
}

print("\n=== Pattern search ===")
for name, pattern in patterns.items():
    matches = re.findall(pattern, html, re.IGNORECASE)
    if matches:
        print(f"  {name}: {len(matches)} matches")
        # Show context around first match
        idx = html.lower().find(name.lower())
        if idx >= 0:
            context = html[max(0,idx-50):idx+100]
            context = context.replace('\n', ' ').replace('\r', '')
            print(f"    Context: ...{context}...")

# Check for large script blocks
print("\n=== Script tags ===")
scripts = re.findall(r'<script[^>]*>(.*?)</script>', html, re.DOTALL)
print(f"Total scripts: {len(scripts)}")
for i, s in enumerate(scripts):
    if len(s) > 1000:
        # Check if it contains interesting keywords
        has_data = any(kw in s.lower() for kw in ['winrate', 'win_rate', 'games', 'tier', 'augment'])
        preview = s[:200].replace('\n', ' ').replace('\r', '')
        print(f"  Script {i}: {len(s)} chars, has_relevant_data={has_data}")
        print(f"    Preview: {preview[:150]}...")

# Look for data in non-script tags
print("\n=== Text content search ===")
# Remove scripts and styles for text search
text_html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL)
text_html = re.sub(r'<style[^>]*>.*?</style>', '', text_html, flags=re.DOTALL)

# Search for numbers that could be win rates
pct_in_text = re.findall(r'(\d{2})\s*%', text_html)
print(f"Percentages in text: {len(pct_in_text)}")
for m in pct_in_text[:10]:
    idx = text_html.find(m + '%')
    context = text_html[max(0,idx-30):idx+30].replace('\n', ' ')
    print(f"  {m}% context: ...{context}...")

# Search for "Games" text
games_in_text = re.findall(r'(\d[\d,]*)\s*[Gg]ames', text_html)
print(f"\nGames in text: {len(games_in_text)}")
for m in games_in_text[:5]:
    idx = text_html.find(m)
    context = text_html[max(0,idx-30):idx+40].replace('\n', ' ')
    print(f"  {m} context: ...{context}...")

# Look for Sion-specific content
sion_refs = re.findall(r'Sion', text_html)
print(f"\nSion references in text: {len(sion_refs)}")

# Check for Playstyle section
playstyle = re.findall(r'[Pp]laystyle', text_html)
print(f"Playstyle references: {len(playstyle)}")
