"""Debug: extract embedded JSON data from blitz.gg champion page."""
import re
import json

with open('pipeline/output/_debug_sion_raw.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Extract all application/json script blocks
json_blocks = re.findall(
    r'<script\s+type="application/json"[^>]*>(.*?)</script>',
    html, re.DOTALL
)
print(f"Found {len(json_blocks)} JSON blocks\n")

for i, block in enumerate(json_blocks):
    try:
        data = json.loads(block)
        # Check for relevant keys
        body = data.get('body', '')
        if isinstance(body, str) and 'win_rate' in body:
            # Parse the body JSON
            body_data = json.loads(body)
            print(f"Block {i}: has win_rate data")
            
            if isinstance(body_data, dict) and 'data' in body_data:
                inner = body_data['data']
                if isinstance(inner, list):
                    print(f"  data is list with {len(inner)} items")
                    for item in inner[:3]:
                        if isinstance(item, dict):
                            keys = list(item.keys())
                            print(f"  Keys: {keys[:15]}")
                            # Show relevant fields
                            for k in ['champion_id', 'games', 'win_rate', 'tier', 'total_num_games',
                                      'champion_win_rate', 'champion_ban_rate', 'ban_num_games']:
                                if k in item:
                                    print(f"    {k}: {item[k]}")
                elif isinstance(inner, dict):
                    print(f"  data is dict with keys: {list(inner.keys())[:10]}")
        elif isinstance(body, str) and ('champion' in body.lower() or 'games' in body.lower()):
            print(f"Block {i}: has champion/games data ({len(body)} chars)")
            if len(body) < 500:
                print(f"  Content: {body[:300]}")
    except json.JSONDecodeError:
        if 'win_rate' in block or 'games' in block:
            print(f"Block {i}: JSON parse error but has relevant keywords ({len(block)} chars)")

# Also extract winrate spans from HTML
print("\n=== HTML winrate spans ===")
wr_spans = re.findall(
    r'<span\s+class="winrate[^"]*"[^>]*>(\d+%)</span>',
    html
)
print(f"Found {len(wr_spans)} winrate spans:")
for w in wr_spans:
    print(f"  {w}")

# Extract games spans
games_spans = re.findall(
    r'<span\s+class="games[^"]*"[^>]*>([^<]+)</span>',
    html
)
print(f"\nFound {len(games_spans)} games spans:")
for g in games_spans:
    print(f"  {g}")

# Look for the Playstyle section context
print("\n=== Playstyle section context ===")
ps_idx = html.find('Playstyle')
if ps_idx >= 0:
    section = html[ps_idx:ps_idx+2000]
    # Extract all visible text
    text = re.sub(r'<[^>]+>', ' | ', section)
    text = re.sub(r'\s+', ' ', text)
    print(f"Playstyle section text: {text[:500]}")
