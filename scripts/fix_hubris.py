"""
fix_hubris.py
Fix item name: 傲慢 → 狂妄 (Hubris)
Follows backup→write→validate→rollback pattern.
"""
import json, os, shutil
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUG_PATH = os.path.join(ROOT, 'data', 'champions.json')
BACKUP_DIR = os.path.join(ROOT, 'backups')

def main():
    # Backup
    os.makedirs(BACKUP_DIR, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
    backup_path = os.path.join(BACKUP_DIR, f'champions_backup_{ts}.json')
    shutil.copy2(AUG_PATH, backup_path)
    print(f"Backup: {backup_path}")

    # Load
    with open(AUG_PATH, encoding='utf-8') as f:
        data = json.load(f)

    # Fix: replace 傲慢 with 狂妄 in build and tips strings
    fixes = {
        '傲慢': '狂妄',
    }

    count = 0
    for champ in data['champions']:
        for field in ['build', 'tips']:
            original = champ.get(field, '')
            if not original:
                continue
            modified = original
            for wrong, correct in fixes.items():
                if wrong in modified:
                    modified = modified.replace(wrong, correct)
            if modified != original:
                champ[field] = modified
                count += 1
                print(f"  Fixed {champ['name']}.{field}")

    # Validate
    with open(AUG_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    # Verify no remaining 傲慢
    with open(AUG_PATH, encoding='utf-8') as f:
        verify = f.read()
    if '傲慢' in verify:
        print("ERROR: Still found '傲慢' after fix! Rolling back...")
        shutil.copy2(backup_path, AUG_PATH)
        return
    if len(data['champions']) != 172:
        print(f"ERROR: Expected 172 champions, got {len(data['champions'])}! Rolling back...")
        shutil.copy2(backup_path, AUG_PATH)
        return

    print(f"\nFixed {count} fields across champions. Verification passed.")

if __name__ == '__main__':
    main()
