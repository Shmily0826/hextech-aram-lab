"""fix_patch_added.py - Clear patch_added for historical removed augments."""
import json, os, shutil
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
aug_path = os.path.join(ROOT, 'data', 'augments.json')
out_dir = os.path.join(ROOT, 'pipeline', 'output')

with open(aug_path, 'r', encoding='utf-8') as f:
    augs = json.load(f)

# Backup
ts = datetime.now().strftime('%Y%m%d_%H%M%S')
shutil.copy2(aug_path, os.path.join(out_dir, f'augments_backup_{ts}.json'))

fixed = 0
for a in augs:
    if a.get('status') == 'removed' and a.get('patch_added') == '26.12':
        a['patch_added'] = ''
        fixed += 1

with open(aug_path, 'w', encoding='utf-8') as f:
    json.dump(augs, f, ensure_ascii=False, indent=2)

print(f'Cleared patch_added for {fixed} historical removed augments')
