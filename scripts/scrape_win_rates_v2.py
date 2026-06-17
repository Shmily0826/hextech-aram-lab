"""scrape_win_rates_v2.py - Parse table rows for win/pick rates from arammayhem.com."""
import json, os, urllib.request, re, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
with open(os.path.join(ROOT, 'data', 'augments.json'), 'r', encoding='utf-8') as f:
    augs = json.load(f)

aug_map = {a['id']: a for a in augs}
active = [a for a in augs if a.get('status') == 'active']

# Fix the 2 that got bad values first
for slug in ['jeweled_gauntlet', 'soul_siphon']:
    if slug in aug_map:
        aug_map[slug].pop('win_rate', None)
        aug_map[slug].pop('pick_rate', None)

# Also retry those + the 15 still missing
missing_wr = [a for a in active if not a.get('win_rate')]
print(f'Trying {len(missing_wr)} augments missing win_rate')

found_count = 0

for a in missing_wr:
    slug = a['id']
    url = f'https://arammayhem.com/augments/{slug}'
    print(f'\n{slug}...')
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            html = resp.read().decode('utf-8')
        
        # Find the first table row with rank, win_rate%, pick_rate%
        # Pattern: #N</td> <td>XX.XX%</td> <td>XX.XX%</td>
        m = re.search(
            r'#\d+</td>\s*<td[^>]*>(\d{1,3}\.\d+)%</td>\s*<td[^>]*>(\d{1,3}\.\d+)%</td>',
            html
        )
        if m:
            wr = float(m.group(1))
            pr = float(m.group(2))
            if 0 < wr <= 100 and 0 < pr <= 100:
                aug_map[slug]['win_rate'] = round(wr / 100, 4)
                aug_map[slug]['pick_rate'] = round(pr / 100, 4)
                print(f'  WR={wr}%, PR={pr}%')
                found_count += 1
            else:
                print(f'  Values out of range: wr={wr}, pr={pr}')
        else:
            # Try alternative: maybe the page doesn't have a table (low-rank or new augment)
            print(f'  No table row found')
        
        time.sleep(0.8)
    except Exception as e:
        print(f'  Error: {e}')

# Save
with open(os.path.join(ROOT, 'data', 'augments.json'), 'w', encoding='utf-8') as f:
    json.dump(augs, f, ensure_ascii=False, indent=2)

# Final stats
active2 = [a for a in augs if a.get('status') == 'active']
has_wr = sum(1 for a in active2 if a.get('win_rate'))
has_pr = sum(1 for a in active2 if a.get('pick_rate'))
print(f'\n=== Results ===')
print(f'Found: {found_count}/{len(missing_wr)}')
print(f'win_rate: {has_wr}/{len(active2)} ({100*has_wr//len(active2)}%)')
print(f'pick_rate: {has_pr}/{len(active2)} ({100*has_pr//len(active2)}%)')

still = [a['id'] for a in active2 if not a.get('win_rate')]
if still:
    print(f'Still missing ({len(still)}): {", ".join(still)}')
