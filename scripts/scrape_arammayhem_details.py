"""
scrape_arammayhem_details.py
Fetch individual augment detail pages from arammayhem.com.
Extract: effect description (CN + EN), champion recommendations, tier info.
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
    'Accept': 'text/html,application/xhtml+xml',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
}


def fetch_page(url, retries=2):
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=30) as resp:
                return resp.read().decode('utf-8', errors='replace')
        except Exception as e:
            if attempt < retries:
                time.sleep(2)
            else:
                return None


def extract_detail(html, slug):
    """Extract augment detail data from arammayhem.com page."""
    result = {
        'slug': slug,
        'effect_cn': None,
        'effect_en': None,
        'champions': [],
    }

    # Extract effect from paragraph tags
    # Pattern: the effect description is typically a short paragraph
    # like "施放一个技能会返还另一个随机技能的花费..."
    clean_html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL)
    clean_html = re.sub(r'<style[^>]*>.*?</style>', '', clean_html, flags=re.DOTALL)

    paras = re.findall(r'<p[^>]*>(.*?)</p>', clean_html, re.DOTALL)
    for p in paras:
        text = re.sub(r'<[^>]+>', '', p).strip()
        # Filter: skip navigation, meta, copyright, and too-short text
        if len(text) < 15 or len(text) > 300:
            continue
        skip_words = ['cookie', 'Cookie', 'privacy', '登录', '注册',
                      '继续查看', '选择强化符文', '不受 Riot', '保留所有权利',
                      '英雄联盟海克斯大乱斗攻略', '© 2026',
                      '版本中的', '稀有度强化符文', '强化符文   ',
                      '英雄联盟和 Riot']
        if any(sw in text for sw in skip_words):
            continue
        # This is likely the effect description
        result['effect_cn'] = text
        break

    return result


def main():
    print('=== Scraping Augment Details from arammayhem.com ===\n')

    # Load candidate data for slugs
    with open(os.path.join(OUTPUT_DIR, 'augment_change_candidates.json'), 'r', encoding='utf-8') as f:
        candidates = json.load(f)

    # Get all slugs: new augments + existing ones
    slugs_to_fetch = []

    # New augments
    for aug in candidates.get('to_add', []):
        url = aug.get('source', {}).get('url', '')
        slug_match = re.search(r'/augments/(.+)$', url)
        if slug_match:
            slugs_to_fetch.append({
                'slug': slug_match.group(1),
                'id': aug['id'],
                'name': aug['name'],
                'is_new': True,
            })

    # Also fetch existing augments that lack effect descriptions
    aug_path = os.path.join(PROJECT_ROOT, 'data', 'augments.json')
    with open(aug_path, 'r', encoding='utf-8') as f:
        local_augs = json.load(f)

    for aug in local_augs:
        if aug.get('status') == 'removed':
            continue
        if not aug.get('effect'):
            url = aug.get('source', {}).get('url', '')
            slug_match = re.search(r'/augments/(.+)$', url)
            if slug_match:
                slug = slug_match.group(1)
                # Avoid duplicates
                if not any(s['slug'] == slug for s in slugs_to_fetch):
                    slugs_to_fetch.append({
                        'slug': slug,
                        'id': aug['id'],
                        'name': aug['name'],
                        'is_new': False,
                    })

    print(f'Total slugs to fetch: {len(slugs_to_fetch)}')
    print(f'  New augments: {sum(1 for s in slugs_to_fetch if s["is_new"])}')
    print(f'  Existing (missing effect): {sum(1 for s in slugs_to_fetch if not s["is_new"])}')

    # Fetch
    results = []
    errors = []
    total = len(slugs_to_fetch)

    for i, item in enumerate(slugs_to_fetch):
        slug = item['slug']
        if (i + 1) % 20 == 0 or i == 0:
            print(f'  [{i+1}/{total}] {item["name"]}...')

        url = f'https://arammayhem.com/zh-cn/augments/{slug}'
        html = fetch_page(url)
        if not html:
            errors.append({'slug': slug, 'error': 'fetch failed'})
            continue

        detail = extract_detail(html, slug)
        detail['id'] = item['id']
        detail['name'] = item['name']
        detail['is_new'] = item['is_new']
        results.append(detail)

        time.sleep(0.3)

    # Save
    output = {
        'source': 'arammayhem.com',
        'scraped_at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        'total': total,
        'success': len(results),
        'with_effect': sum(1 for r in results if r.get('effect_cn')),
        'with_champions': sum(1 for r in results if r.get('champions')),
        'errors': len(errors),
        'results': results,
        'error_details': errors,
    }

    output_file = os.path.join(OUTPUT_DIR, 'arammayhem_details_scrape.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f'\n=== Results ===')
    print(f'  Total: {total}, Success: {len(results)}')
    print(f'  With effect: {output["with_effect"]}')
    print(f'  With champions: {output["with_champions"]}')
    print(f'  Errors: {len(errors)}')
    print(f'  Saved: {output_file}')

    # Sample
    with_effect = [r for r in results if r.get('effect_cn')]
    print(f'\n  Sample effects:')
    for r in with_effect[:5]:
        eff = r['effect_cn'][:80] if r['effect_cn'] else ''
        print(f'    {r["name"]}: {eff}')


if __name__ == '__main__':
    main()
