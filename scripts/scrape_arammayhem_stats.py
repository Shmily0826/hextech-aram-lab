"""
scrape_arammayhem_stats.py
Scrape augment win rate / pick rate data from arammayhem.com.
Fetches both Chinese and English pages to get CN names + EN slugs.
Outputs candidate data to pipeline/output/ for review.
"""
import json
import os
import re
import time
import urllib.request
import urllib.error

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(PROJECT_ROOT, 'pipeline', 'output')

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
}

def fetch_page(url, retries=2):
    """Fetch a page with retries."""
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=30) as resp:
                return resp.read().decode('utf-8', errors='replace')
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
            if attempt < retries:
                print(f"  Retry {attempt+1}/{retries} for {url}: {e}")
                time.sleep(2)
            else:
                print(f"  FAILED: {url}: {e}")
                return None


def parse_augment_list(html, lang='zh'):
    """Parse augment entries from the HTML.
    
    Each entry is an <a> tag linking to /zh-cn/augments/{slug} or /augments/{slug}.
    Contains: image with alt text (augment name), tier info, win rate, pick rate.
    """
    entries = []
    
    # Pattern for augment links: <a href="/(zh-cn/)?augments/SLUG">
    if lang == 'zh':
        link_pattern = r'<a\s+href="/zh-cn/augments/([^"]+)"[^>]*>(.*?)</a>'
    else:
        link_pattern = r'<a\s+href="/augments/([^"]+)"[^>]*>(.*?)</a>'
    
    for slug, inner_html in re.findall(link_pattern, html, re.DOTALL):
        entry = {'slug': slug}
        
        # Extract augment name from image alt text: ![Name](...)
        name_match = re.search(r'alt="([^"]+)"', inner_html)
        if name_match:
            entry['name'] = name_match.group(1)
        
        # Extract image src for augment icon
        img_match = re.search(r'src="([^"]*augment[^"]*)"', inner_html, re.IGNORECASE)
        if img_match:
            entry['image_url'] = img_match.group(1)
        
        # Extract tier from text content or image alt
        # Tiers: 银/Silver, 金/Gold, 棱彩/Prismatic
        text_content = re.sub(r'<[^>]+>', ' ', inner_html)
        
        if '棱彩' in text_content or 'Prismatic' in text_content or 'prismatic' in slug.lower():
            entry['tier'] = 'prismatic'
        elif '金' in text_content or 'Gold' in text_content:
            entry['tier'] = 'gold'
        elif '银' in text_content or 'Silver' in text_content:
            entry['tier'] = 'silver'
        
        # Extract percentages: patterns like "69.86%" or "67.38%"
        percents = re.findall(r'(\d+\.?\d*)%', text_content)
        if len(percents) >= 2:
            entry['pick_rate'] = float(percents[0])  # page order: pick_rate first
            entry['win_rate'] = float(percents[1])   # then win_rate
        elif len(percents) == 1:
            entry['win_rate'] = float(percents[0])
        
        # Extract "新" (new) marker if present
        if '新' in text_content[:10]:
            entry['is_new'] = True
        
        # Extract rank number
        rank_match = re.search(r'^(\d+)', text_content.strip())
        if rank_match:
            entry['rank'] = int(rank_match.group(1))
        
        entries.append(entry)
    
    return entries


def merge_cn_en(cn_entries, en_entries):
    """Merge Chinese and English entries by slug."""
    en_map = {e['slug']: e for e in en_entries}
    merged = []
    
    for cn in cn_entries:
        slug = cn['slug']
        en = en_map.get(slug, {})
        
        entry = {
            'slug': slug,
            'name_cn': cn.get('name', ''),
            'name_en': en.get('name', ''),
            'tier': cn.get('tier') or en.get('tier', 'unknown'),
            'win_rate': cn.get('win_rate') or en.get('win_rate'),
            'pick_rate': cn.get('pick_rate') or en.get('pick_rate'),
            'rank': cn.get('rank') or en.get('rank'),
            'is_new': cn.get('is_new', False) or en.get('is_new', False),
            'image_url': cn.get('image_url') or en.get('image_url', ''),
        }
        merged.append(entry)
    
    return merged


def cross_reference_with_local(merged_entries):
    """Cross-reference scraped data with local augments.json."""
    local_path = os.path.join(PROJECT_ROOT, 'data', 'augments.json')
    with open(local_path, 'r', encoding='utf-8') as f:
        local_augs = json.load(f)
    
    # Build lookup maps
    local_by_id = {a['id']: a for a in local_augs}
    local_by_name = {a['name']: a for a in local_augs}
    local_by_name_en = {a.get('name_en', ''): a for a in local_augs if a.get('name_en')}
    local_by_slug = {}
    for a in local_augs:
        src = a.get('source', {})
        url = src.get('url', '')
        # Extract slug from URL like https://arammayhem.com/zh-cn/augments/slug
        slug_match = re.search(r'/augments/([^/]+)$', url)
        if slug_match:
            local_by_slug[slug_match.group(1)] = a
    
    matched = []
    unmatched_scraped = []
    unmatched_local = set(local_by_id.keys())
    
    for entry in merged_entries:
        slug = entry['slug']
        local = None
        
        # Try matching by slug
        if slug in local_by_slug:
            local = local_by_slug[slug]
        # Try matching by English name
        elif entry['name_en'] in local_by_name_en:
            local = local_by_name_en[entry['name_en']]
        # Try matching by Chinese name
        elif entry['name_cn'] in local_by_name:
            local = local_by_name[entry['name_cn']]
        
        if local:
            entry['local_id'] = local['id']
            entry['match_method'] = 'slug' if slug in local_by_slug else ('name_en' if entry['name_en'] in local_by_name_en else 'name_cn')
            matched.append(entry)
            unmatched_local.discard(local['id'])
        else:
            unmatched_scraped.append(entry)
    
    # Check local augments not found in scrape
    unmatched_local_entries = [local_by_id[aid] for aid in sorted(unmatched_local)]
    
    return matched, unmatched_scraped, unmatched_local_entries


def main():
    print("=== Scraping arammayhem.com Augment Stats ===\n")
    
    # Step 1: Fetch Chinese page
    print("--- Step 1: Fetching Chinese augment list ---")
    cn_url = 'https://arammayhem.com/zh-cn/augments'
    cn_html = fetch_page(cn_url)
    if not cn_html:
        print("FATAL: Could not fetch Chinese page")
        return
    
    cn_entries = parse_augment_list(cn_html, lang='zh')
    print(f"  Parsed {len(cn_entries)} entries from Chinese page")
    
    time.sleep(1)  # Be polite
    
    # Step 2: Fetch English page
    print("\n--- Step 2: Fetching English augment list ---")
    en_url = 'https://arammayhem.com/augments'
    en_html = fetch_page(en_url)
    if not en_html:
        print("WARNING: Could not fetch English page, using Chinese data only")
        en_entries = []
    else:
        en_entries = parse_augment_list(en_html, lang='en')
        print(f"  Parsed {len(en_entries)} entries from English page")
    
    # Step 3: Merge CN + EN data
    print("\n--- Step 3: Merging CN + EN data ---")
    if en_entries:
        merged = merge_cn_en(cn_entries, en_entries)
    else:
        merged = [{'slug': e['slug'], 'name_cn': e.get('name',''), 'name_en': '',
                    'tier': e.get('tier','unknown'), 'win_rate': e.get('win_rate'),
                    'pick_rate': e.get('pick_rate'), 'rank': e.get('rank'),
                    'is_new': e.get('is_new', False), 'image_url': e.get('image_url','')}
                   for e in cn_entries]
    print(f"  Merged: {len(merged)} entries")
    
    # Step 4: Cross-reference with local data
    print("\n--- Step 4: Cross-referencing with local augments.json ---")
    matched, unmatched_scraped, unmatched_local = cross_reference_with_local(merged)
    print(f"  Matched: {len(matched)}")
    print(f"  In scrape but NOT in local: {len(unmatched_scraped)}")
    print(f"  In local but NOT in scrape: {len(unmatched_local)}")
    
    # Step 5: Output results
    print("\n--- Step 5: Outputting results ---")
    
    # Full scraped data
    output_file = os.path.join(OUTPUT_DIR, 'arammayhem_stats_scrape.json')
    output_data = {
        'source': 'arammayhem.com',
        'scraped_at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        'total_scraped': len(merged),
        'total_matched': len(matched),
        'total_unmatched_scraped': len(unmatched_scraped),
        'total_unmatched_local': len(unmatched_local),
        'matched': matched,
        'unmatched_scraped': unmatched_scraped,
        'unmatched_local': [{'id': a['id'], 'name': a['name'], 'name_en': a.get('name_en',''), 'tier': a.get('tier','')} for a in unmatched_local],
    }
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    print(f"  Saved: {output_file}")
    
    # Summary
    print("\n=== Summary ===")
    print(f"  Total augments on arammayhem.com: {len(merged)}")
    print(f"  Total augments in local augments.json: {len(matched) + len(unmatched_local)}")
    
    if unmatched_scraped:
        print(f"\n  --- {len(unmatched_scraped)} NEW augments (in scrape, not local) ---")
        for e in unmatched_scraped[:20]:
            name = e.get('name_cn') or e.get('name_en') or e['slug']
            tier = e.get('tier', '?')
            wr = e.get('win_rate', '?')
            print(f"    {e.get('rank','?')}. {name} ({tier}) WR={wr}%")
    
    if unmatched_local:
        print(f"\n  --- {len(unmatched_local)} REMOVED augments (in local, not in scrape) ---")
        for a in unmatched_local[:20]:
            name = a.get('name', '?')
            aid = a.get('id', '?')
            tier = a.get('tier', '?')
            print(f"    {aid}: {name} ({tier})")
    
    # Tier distribution of scraped data
    tier_dist = {}
    for e in merged:
        t = e.get('tier', 'unknown')
        tier_dist[t] = tier_dist.get(t, 0) + 1
    print(f"\n  Tier distribution (scraped): {tier_dist}")
    
    # New augments count
    new_count = sum(1 for e in merged if e.get('is_new'))
    print(f"  New augments (marked 新): {new_count}")


if __name__ == '__main__':
    main()
