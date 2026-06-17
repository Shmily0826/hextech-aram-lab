"""find_alt_slugs.py - Try alternative URLs for 404 augments."""
import json, os, urllib.request, re, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
with open(os.path.join(ROOT, 'data', 'augments.json'), 'r', encoding='utf-8') as f:
    augs = json.load(f)

aug_map = {a['id']: a for a in augs}

# 404 augments - try different slug variations
FOUR_OH_FOUR = ['upgrade_mikaels', 'drop_bear', 'ice_burst', 'endless_rampage', 'nature_heals', 'solid_as_rock']

def try_url(url):
    """Returns (status_code, html_snippet) or (None, error)."""
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            html = resp.read().decode('utf-8')
            return resp.status, html
    except urllib.error.HTTPError as e:
        return e.code, None
    except Exception as e:
        return None, str(e)

def extract_wr(html):
    m = re.search(
        r'#\d+</td>\s*<td[^>]*>(\d{1,3}\.\d+)%</td>\s*<td[^>]*>(\d{1,3}\.\d+)%</td>',
        html
    )
    if m:
        return float(m.group(1)), float(m.group(2))
    return None, None

for slug in FOUR_OH_FOUR:
    aug = aug_map.get(slug)
    if not aug:
        continue
    
    # Get name variants
    name = aug.get('name', '')
    name_en = aug.get('name_en', '')
    
    # Generate slug candidates
    candidates = []
    # dash version
    candidates.append(slug.replace('_', '-'))
    # from name_en
    if name_en:
        s = name_en.lower().replace(' ', '-').replace("'", '').replace(':', '')
        s = re.sub(r'[^a-z0-9-]', '', s)
        if s and s not in candidates:
            candidates.append(s)
    # Try CN slug
    if name:
        candidates.append(name)
    
    # Also check if source URL has the slug
    src = aug.get('source', {})
    if isinstance(src, dict) and src.get('url'):
        src_url = src['url']
        m = re.search(r'/augments/([^/?]+)', src_url)
        if m:
            s = m.group(1)
            if s not in candidates:
                candidates.append(s)
    
    print(f'\n{slug} (name={name}, name_en={name_en})')
    print(f'  Candidates: {candidates}')
    
    found = False
    for c in candidates:
        for base in ['https://arammayhem.com/augments/', 'https://arammayhem.com/zh-cn/augments/']:
            url = base + c
            status, html = try_url(url)
            if status == 200 and html:
                wr, pr = extract_wr(html)
                if wr:
                    print(f'  FOUND at {url}: WR={wr}%, PR={pr}%')
                    aug_map[slug]['win_rate'] = round(wr / 100, 4)
                    aug_map[slug]['pick_rate'] = round(pr / 100, 4)
                    found = True
                    break
                else:
                    print(f'  Page exists at {url} but no table data')
            time.sleep(0.5)
        if found:
            break
    
    if not found:
        print(f'  Not found on any variant')

# Also try the "no table" ones with CN pages
NO_TABLE = ['spirit_bomb', 'squishy_slappy_grab', 'poro_stampede', 'rejuvenation', 'tooth_fairy']
for slug in NO_TABLE:
    aug = aug_map.get(slug)
    if not aug:
        continue
    # Try CN page
    cn_url = f'https://arammayhem.com/zh-cn/augments/{slug.replace("_", "-")}'
    status, html = try_url(cn_url)
    if status == 200 and html:
        wr, pr = extract_wr(html)
        if wr:
            print(f'\n{slug} CN page: WR={wr}%, PR={pr}%')
            aug_map[slug]['win_rate'] = round(wr / 100, 4)
            aug_map[slug]['pick_rate'] = round(pr / 100, 4)
        else:
            print(f'\n{slug} CN page exists but no table')
    time.sleep(0.5)

# Save
with open(os.path.join(ROOT, 'data', 'augments.json'), 'w', encoding='utf-8') as f:
    json.dump(augs, f, ensure_ascii=False, indent=2)

# Final stats
active = [a for a in augs if a.get('status') == 'active']
has_wr = sum(1 for a in active if a.get('win_rate'))
print(f'\n=== Final: win_rate {has_wr}/{len(active)} ({100*has_wr//len(active)}%) ===')
still = [a['id'] for a in active if not a.get('win_rate')]
if still:
    print(f'Still missing ({len(still)}): {", ".join(still)}')
