"""scrape_win_rates.py - Try to get win/pick rates for the 17 missing augments."""
import json, os, urllib.request, re, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
with open(os.path.join(ROOT, 'data', 'augments.json'), 'r', encoding='utf-8') as f:
    augs = json.load(f)

active = [a for a in augs if a.get('status') == 'active']
missing_wr = [a for a in active if not a.get('win_rate')]
print(f'Augments missing win_rate: {len(missing_wr)}')

aug_map = {a['id']: a for a in augs}
found = 0

for a in missing_wr:
    slug = a['id']
    url = f'https://arammayhem.com/augments/{slug}'
    print(f'\nFetching {slug}...')
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            html = resp.read().decode('utf-8')
        
        # Look for win rate patterns - typically "Win Rate" followed by a percentage
        # Try multiple patterns
        patterns = [
            r'Win\s*Rate[^0-9]*(\d{1,3}\.?\d*)\s*%',
            r'win.?rate[^0-9]*(\d{1,3}\.?\d*)\s*%',
            r'"winRate"\s*:\s*([\d.]+)',
            r'"win_rate"\s*:\s*([\d.]+)',
            r'([\d.]+)\s*%\s*Win',
            r'Pick\s*Rate[^0-9]*(\d{1,3}\.?\d*)\s*%',
        ]
        
        wr_match = None
        pr_match = None
        for pat in patterns:
            m = re.search(pat, html, re.IGNORECASE)
            if m:
                val = float(m.group(1))
                if 'pick' in pat.lower() or 'Pick' in pat:
                    if 0 < val <= 100:
                        pr_match = val
                else:
                    if 0 < val <= 100:
                        wr_match = val
                break
        
        if wr_match:
            aug_map[slug]['win_rate'] = round(wr_match / 100, 4) if wr_match > 1 else round(wr_match, 4)
            print(f'  Found win_rate: {wr_match}%')
            found += 1
        else:
            print(f'  No win_rate found on page')
        
        if pr_match:
            aug_map[slug]['pick_rate'] = round(pr_match / 100, 4) if pr_match > 1 else round(pr_match, 4)
            print(f'  Found pick_rate: {pr_match}%')
        
        time.sleep(0.8)  # Be polite
    except Exception as e:
        print(f'  Error: {e}')

# Save
with open(os.path.join(ROOT, 'data', 'augments.json'), 'w', encoding='utf-8') as f:
    json.dump(augs, f, ensure_ascii=False, indent=2)

print(f'\n=== Results ===')
print(f'Found win_rate for {found}/{len(missing_wr)} augments')

# Final check
active2 = [a for a in augs if a.get('status') == 'active']
has_wr = sum(1 for a in active2 if a.get('win_rate'))
print(f'win_rate coverage: {has_wr}/{len(active2)} ({100*has_wr//len(active2)}%)')

still_missing = [a['id'] for a in active2 if not a.get('win_rate')]
if still_missing:
    print(f'Still missing ({len(still_missing)}): {", ".join(still_missing)}')
