"""
build_augment_candidates.py
Build a structured candidate file showing all augment changes needed:
  - New augments to ADD (from arammayhem.com, not in local)
  - Removed augments (in local, not on arammayhem.com)
  - Updated stats (win_rate, pick_rate for existing augments)
  - Tier discrepancies
"""
import json
import os
import time

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, 'data')
OUTPUT_DIR = os.path.join(PROJECT_ROOT, 'pipeline', 'output')


def main():
    # Load scraped data
    with open(os.path.join(OUTPUT_DIR, 'arammayhem_stats_scrape.json'), 'r', encoding='utf-8') as f:
        scrape = json.load(f)

    # Load local augments
    with open(os.path.join(DATA_DIR, 'augments.json'), 'r', encoding='utf-8') as f:
        local_augs = json.load(f)

    local_by_id = {a['id']: a for a in local_augs}
    local_by_slug = {}
    for a in local_augs:
        url = a.get('source', {}).get('url', '')
        if '/augments/' in url:
            slug = url.rsplit('/augments/', 1)[-1]
            local_by_slug[slug] = a

    matched = scrape['matched']
    unmatched_scraped = scrape['unmatched_scraped']
    unmatched_local = scrape['unmatched_local']

    # ---- Build candidate structure ----
    candidates = {
        'generated_at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        'source': 'arammayhem.com',
        'summary': {},
        'to_add': [],          # new augments to add
        'to_remove': [],       # augments to mark removed
        'to_update': [],       # stats/tier updates for existing
        'notes': [],           # observations and warnings
    }

    # --- 1. New augments to add ---
    for entry in unmatched_scraped:
        slug = entry['slug']
        new_id = slug.replace('-', '_')

        aug_candidate = {
            'id': new_id,
            'name': entry.get('name_cn', ''),
            'name_en': entry.get('name_en', ''),
            'tier': entry.get('tier', 'unknown'),
            'status': 'active',
            'source': {
                'type': 'arammayhem_com',
                'url': 'https://arammayhem.com/zh-cn/augments/' + slug,
            },
        }
        if entry.get('win_rate') is not None:
            aug_candidate['win_rate'] = entry['win_rate']
        if entry.get('pick_rate') is not None:
            aug_candidate['pick_rate'] = entry['pick_rate']
        if entry.get('rank') is not None:
            aug_candidate['site_rank'] = entry['rank']

        # Special cases
        if entry.get('name_cn') == '???':
            aug_candidate['notes'] = '未命名强化，wiki 上标记为 ???'
        if entry.get('win_rate') is None:
            aug_candidate['notes'] = aug_candidate.get('notes', '') + ' 新增强化，尚无胜率数据'

        candidates['to_add'].append(aug_candidate)

    # --- 2. Removed augments ---
    for entry in unmatched_local:
        aid = entry['id']
        local = local_by_id.get(aid, {})
        candidates['to_remove'].append({
            'id': aid,
            'name': local.get('name', entry.get('name', '?')),
            'name_en': local.get('name_en', entry.get('name_en', '?')),
            'tier': local.get('tier', entry.get('tier', '?')),
            'reason': '不在 arammayhem.com 当前列表中（可能已在 16.12 移除）',
        })

    # --- 3. Stats/tier updates for existing augments ---
    for entry in matched:
        aid = entry['local_id']
        local = local_by_id.get(aid, {})
        updates = {}

        # Check win rate
        scraped_wr = entry.get('win_rate')
        if scraped_wr is not None:
            updates['win_rate'] = scraped_wr

        # Check pick rate
        scraped_pr = entry.get('pick_rate')
        if scraped_pr is not None:
            updates['pick_rate'] = scraped_pr

        # Check tier discrepancy
        scraped_tier = entry.get('tier', 'unknown')
        local_tier = local.get('tier', 'unknown')
        if scraped_tier != local_tier and scraped_tier != 'unknown':
            updates['tier'] = scraped_tier
            updates['tier_old'] = local_tier
            candidates['notes'].append(
                '层级差异: ' + local.get('name', aid) + ' 本地=' + local_tier + ' 网站=' + scraped_tier
            )

        # Check rank
        if entry.get('rank') is not None:
            updates['site_rank'] = entry['rank']

        if updates:
            candidates['to_update'].append({
                'id': aid,
                'name': local.get('name', '?'),
                'updates': updates,
            })

    # --- 4. Summary ---
    candidates['summary'] = {
        'total_on_site': len(matched) + len(unmatched_scraped),
        'total_in_local': len(matched) + len(unmatched_local),
        'matched': len(matched),
        'to_add': len(candidates['to_add']),
        'to_remove': len(candidates['to_remove']),
        'to_update_stats': sum(1 for u in candidates['to_update'] if 'win_rate' in u['updates']),
        'to_update_tier': sum(1 for u in candidates['to_update'] if 'tier' in u['updates']),
    }

    # --- 5. Special observations ---
    # Check for name changes (same slug, different name)
    for entry in matched:
        aid = entry['local_id']
        local = local_by_id.get(aid, {})
        scraped_cn = entry.get('name_cn', '')
        local_cn = local.get('name', '')
        if scraped_cn and local_cn and scraped_cn != local_cn:
            candidates['notes'].append(
                '名称差异: ' + aid + ' 本地=' + local_cn + ' 网站=' + scraped_cn
            )

    # Save
    output_file = os.path.join(OUTPUT_DIR, 'augment_change_candidates.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(candidates, f, ensure_ascii=False, indent=2)

    print('=== Augment Change Candidates ===')
    print('Summary:')
    for k, v in candidates['summary'].items():
        print('  ' + str(k) + ': ' + str(v))
    print()
    print('To ADD: ' + str(len(candidates['to_add'])) + ' new augments')
    print('To REMOVE: ' + str(len(candidates['to_remove'])) + ' augments')
    print('To UPDATE: ' + str(len(candidates['to_update'])) + ' augments')
    print('Notes: ' + str(len(candidates['notes'])) + ' observations')
    print()
    print('Saved: ' + output_file)

    if candidates['notes']:
        print('\n--- Notes ---')
        for n in candidates['notes']:
            print('  ' + n)


if __name__ == '__main__':
    main()
