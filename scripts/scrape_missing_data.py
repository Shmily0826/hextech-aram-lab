"""scrape_missing_data.py
Scrape missing effect_en from arammayhem.com English pages,
then auto-generate tags based on effect text for augments missing tags.
"""
import json, os, re, time
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(ROOT, 'pipeline', 'output')

# --- Step 1: Scrape English effect descriptions ---
def fetch_en_effects(missing_ids):
    """Fetch English effect descriptions from arammayhem.com/en/augments/{slug}"""
    results = {}
    for aid in missing_ids:
        slug = aid.replace('_', '-')
        url = f'https://arammayhem.com/augments/{slug}'
        print(f'  Fetching EN: {url}')
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=15) as resp:
                html = resp.read().decode('utf-8', errors='replace')
            # Extract paragraphs
            paragraphs = re.findall(r'<p[^>]*>(.*?)</p>', html, re.DOTALL)
            skip_words = [
                'cookie', 'Cookie', 'privacy', 'Login', 'Sign up',
                'Continue reading', 'not endorsed by Riot', 'All rights reserved',
                'League of Legends and Riot', 'ARAM Mayhem',
                'is a augment in', 'rarity augment in the current',
                'win rate of', 'pick rate of', '© 2026',
                'Keep exploring', 'champions, items, sets',
                'is a silver rarity', 'is a gold rarity', 'is a prismatic rarity',
                'rarity augment in ARAM',
            ]
            effect = ''
            for p in paragraphs:
                text = re.sub(r'<[^>]+>', '', p).strip()
                if len(text) < 15:
                    continue
                if any(sw.lower() in text.lower() for sw in skip_words):
                    continue
                if 'launched in patch' in text.lower() or 'removed in patch' in text.lower():
                    continue
                effect = text
                break
            if effect:
                results[aid] = effect
                print(f'    OK: {effect[:60]}...')
            else:
                print(f'    SKIP: no valid effect text found')
        except Exception as e:
            print(f'    ERROR: {e}')
        time.sleep(0.5)
    return results


# --- Step 2: Auto-generate tags from effect text ---
TAG_KEYWORDS = {
    '治疗': ['治疗', '回复', 'heal', 'restore'],
    '护盾': ['护盾', 'shield'],
    '攻击速度': ['攻击速度', '攻速', 'attack speed'],
    '技能急速': ['技能急速', 'ability haste', 'haste'],
    '暴击': ['暴击', 'critical', 'crit'],
    '移动速度': ['移动速度', '移速', 'movement speed', 'move speed'],
    '法力': ['法力', 'mana'],
    '生命值': ['生命值', 'health', 'max health'],
    '法术强度': ['法术强度', 'ability power', 'AP'],
    '攻击力': ['攻击力', 'attack damage', 'AD'],
    '护甲': ['护甲', 'armor'],
    '魔抗': ['魔抗', '魔法抗性', 'magic resist'],
    '灼烧': ['灼烧', 'burn', 'damage over time'],
    '减速': ['减速', 'slow'],
    '冲刺': ['冲刺', 'dash', 'leap'],
    '召唤物': ['召唤', 'summon', 'pet'],
    '雪球': ['雪球', 'snowball', 'mark'],
    '任务': ['任务', 'quest'],
    '终极技能': ['终极技能', 'ultimate', 'ult'],
    '装备升级': ['升级', 'upgrade'],
    '金币': ['金币', 'gold', 'coin'],
    '体型': ['体型', 'size'],
    '全能吸血': ['全能吸血', 'omnivamp'],
    '生命偷取': ['生命偷取', 'lifesteal'],
    '穿透': ['穿透', 'penetration', 'pen'],
    '飞弹': ['飞弹', 'missile', 'projectile'],
    '复活': ['复活', 'revive', 'resurrect'],
}

def generate_tags(effect, effect_en):
    """Generate tags based on effect text keywords."""
    text = (effect or '') + ' ' + (effect_en or '')
    tags = []
    for tag, keywords in TAG_KEYWORDS.items():
        for kw in keywords:
            if kw.lower() in text.lower():
                tags.append(tag)
                break
    return tags


def main():
    with open(os.path.join(ROOT, 'data', 'augments.json'), 'r', encoding='utf-8') as f:
        augs = json.load(f)

    active = [a for a in augs if a.get('status') == 'active']

    # Find missing effect_en
    missing_en = [a['id'] for a in active if not a.get('effect_en')]
    print(f'=== Missing effect_en: {len(missing_en)} ===')
    for aid in missing_en:
        a = next(x for x in augs if x['id'] == aid)
        print(f'  {aid}: {a["name"]}')

    # Scrape English effects
    if missing_en:
        print(f'\nFetching English effects from arammayhem.com...')
        en_effects = fetch_en_effects(missing_en)
        print(f'\nGot {len(en_effects)} English effects')

        # Apply
        updated_en = 0
        for aid, en_text in en_effects.items():
            for a in augs:
                if a['id'] == aid:
                    a['effect_en'] = en_text
                    updated_en += 1
                    break
        print(f'Applied {updated_en} English effects')
    else:
        print('No missing effect_en!')

    # Generate tags for missing
    print(f'\n=== Auto-generating tags ===')
    tagged = 0
    for a in augs:
        if a.get('status') != 'active':
            continue
        if not a.get('tags'):
            new_tags = generate_tags(a.get('effect', ''), a.get('effect_en', ''))
            if new_tags:
                a['tags'] = new_tags
                tagged += 1
                print(f'  {a["id"]}: {a["name"]} -> {new_tags}')
    print(f'Generated tags for {tagged} augments')

    # Save
    with open(os.path.join(ROOT, 'data', 'augments.json'), 'w', encoding='utf-8') as f:
        json.dump(augs, f, ensure_ascii=False, indent=2)

    # Summary
    active2 = [a for a in augs if a.get('status') == 'active']
    has_eff = sum(1 for a in active2 if a.get('effect'))
    has_en = sum(1 for a in active2 if a.get('effect_en'))
    has_wr = sum(1 for a in active2 if a.get('win_rate'))
    has_tags = sum(1 for a in active2 if a.get('tags'))
    print(f'\n=== Final Summary ===')
    print(f'Active: {len(active2)}')
    print(f'Effect: {has_eff}/{len(active2)}')
    print(f'Effect_en: {has_en}/{len(active2)}')
    print(f'Win_rate: {has_wr}/{len(active2)}')
    print(f'Tags: {has_tags}/{len(active2)}')


if __name__ == '__main__':
    main()
