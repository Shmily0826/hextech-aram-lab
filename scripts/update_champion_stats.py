"""
update_champion_stats.py
Update champions.json with win rate and game count from blitz.gg scrape.
"""
import json
import os
import shutil
from datetime import datetime

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, 'data')
OUTPUT_DIR = os.path.join(PROJECT_ROOT, 'pipeline', 'output')


def main():
    # Load scraped data
    with open(os.path.join(OUTPUT_DIR, 'blitz_hero_stats_scrape.json'), 'r', encoding='utf-8') as f:
        scrape = json.load(f)

    # Load champions.json
    champ_path = os.path.join(DATA_DIR, 'champions.json')
    backup_ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = os.path.join(OUTPUT_DIR, f'champions_backup_{backup_ts}.json')
    shutil.copy2(champ_path, backup_path)
    print(f'Backed up: {backup_path}')

    with open(champ_path, 'r', encoding='utf-8') as f:
        champs = json.load(f)

    champions = champs.get('champions', {})

    # Build CN name -> stats map from scrape
    stats_map = {}
    for entry in scrape['results']:
        cn_name = entry.get('cn_name', '')
        if cn_name and entry.get('weighted_win_rate') is not None:
            stats_map[cn_name] = {
                'win_rate': entry['weighted_win_rate'],
                'games': entry['total_games'],
                'builds': len(entry.get('builds', [])),
                'tier_blitz': entry.get('tier_blitz'),
            }

    print(f'Stats available for {len(stats_map)} champions')

    # Update champions (it's a list, not a dict)
    updated = 0
    not_found = []
    for champ_data in champions:
        cn_name = champ_data.get('name', '')
        if cn_name in stats_map:
            stats = stats_map[cn_name]
            champ_data['wr'] = stats['win_rate']
            champ_data['games'] = stats['games']
            # Keep existing tier if it's not unknown, otherwise use blitz tier
            if stats['tier_blitz'] and champ_data.get('tier') in (None, 'unknown'):
                tier_map = {'S': 'S', 'A': 'A', 'B': 'B', 'C': 'C', 'D': 'D'}
                champ_data['tier'] = tier_map.get(stats['tier_blitz'], champ_data.get('tier', 'unknown'))
            updated += 1
        else:
            not_found.append(cn_name)

    # Save
    with open(champ_path, 'w', encoding='utf-8') as f:
        json.dump(champs, f, ensure_ascii=False, indent=2)

    print(f'Updated {updated} champions')
    if not_found:
        print(f'Not found ({len(not_found)}): {not_found[:10]}')

    # Verify
    with open(champ_path, 'r', encoding='utf-8') as f:
        verify = json.load(f)
    v_champs = verify.get('champions', [])
    with_wr = sum(1 for c in v_champs if c.get('wr') is not None)
    with_games = sum(1 for c in v_champs if c.get('games') is not None)
    print(f'\nVerification: {len(v_champs)} total, {with_wr} with win_rate, {with_games} with games')


if __name__ == '__main__':
    main()
