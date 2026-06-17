"""fix_source_format.py - Normalize source field to object format for new augments."""
import json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
aug_path = os.path.join(ROOT, 'data', 'augments.json')

with open(aug_path, 'r', encoding='utf-8') as f:
    augs = json.load(f)

# Load candidates for URL lookup
cand_path = os.path.join(ROOT, 'pipeline', 'output', 'augment_change_candidates.json')
with open(cand_path, 'r', encoding='utf-8') as f:
    cands = json.load(f)

url_map = {}
for item in cands.get('to_add', []):
    url_map[item['id']] = item.get('source', {}).get('url', '')

fixed = 0
for a in augs:
    if isinstance(a.get('source'), str):
        aid = a['id']
        url = url_map.get(aid, f'https://arammayhem.com/zh-cn/augments/{aid.replace("_", "-")}')
        a['source'] = {
            'type': a['source'],
            'url': url
        }
        fixed += 1

with open(aug_path, 'w', encoding='utf-8') as f:
    json.dump(augs, f, ensure_ascii=False, indent=2)

print(f'Fixed source format for {fixed} augments')
