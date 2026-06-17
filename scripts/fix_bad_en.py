"""fix_bad_en.py - Clear navigation-text effect_en entries."""
import json, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
with open(os.path.join(ROOT, 'data', 'augments.json'), 'r', encoding='utf-8') as f:
    augs = json.load(f)
bad_phrases = ['Keep exploring', 'rarity augment in ARAM', 'rarity augment in the current']
cleared = 0
for a in augs:
    en = a.get('effect_en', '')
    if en and any(bp in en for bp in bad_phrases):
        a['effect_en'] = ''
        cleared += 1
        print(f'  Cleared: {a["id"]}')
with open(os.path.join(ROOT, 'data', 'augments.json'), 'w', encoding='utf-8') as f:
    json.dump(augs, f, ensure_ascii=False, indent=2)
print(f'Cleared {cleared} bad effect_en entries')
