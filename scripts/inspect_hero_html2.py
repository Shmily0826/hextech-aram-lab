"""Quick check for the title attribute pattern on champion links."""
import urllib.request, re

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
req = urllib.request.Request('https://arammayhem.com/champions', headers=HEADERS)
html = urllib.request.urlopen(req, timeout=30).read().decode('utf-8', errors='replace')

# Find <a> tags with build links and title attributes
pattern = r'<a\s+href="/build/([a-z][a-z0-9-]+)/?"\s+title="([^"]*)"'
matches = re.findall(pattern, html)
print(f"Champion links with title attribute: {len(matches)}")

if matches:
    for slug, title in matches[:5]:
        print(f"  {slug}: {title}")

# Alternative: title might come before href
pattern2 = r'<a\s+title="([^"]*)"\s+href="/build/([a-z][a-z0-9-]+)/?"'
matches2 = re.findall(pattern2, html)
print(f"\nAlt pattern (title before href): {len(matches2)}")
if matches2:
    for title, slug in matches2[:5]:
        print(f"  {slug}: {title}")

# Most flexible: find all <a ...build/SLUG... > with any attribute order
pattern3 = r'<a[^>]*href="/build/([a-z][a-z0-9-]+)/?"[^>]*>'
matches3 = re.findall(pattern3, html)
print(f"\nAll champion <a> tags: {len(matches3)}")

# Show first 3 full tags
for m in re.finditer(r'<a[^>]*href="/build/([a-z][a-z0-9-]+)/?"[^>]*>', html):
    tag = m.group()
    slug = m.group(1)
    if 'title=' in tag:
        title_match = re.search(r'title="([^"]*)"', tag)
        title = title_match.group(1) if title_match else '?'
        print(f"  {slug}: {title}")
    else:
        print(f"  {slug}: (no title attr) tag = {tag[:200]}")
    if slug == 'morgana':
        break
