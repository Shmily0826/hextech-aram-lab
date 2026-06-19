"""
fix_items_v3.py
Fix item names: 恶意→残疫, 终点站→无终恨意
"""
import json, os, shutil
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'data', 'champions.json')
BACKUP_DIR = os.path.join(ROOT, 'backups')

FIXES = {
    '恶意': '残疫',
    '终点站': '无终恨意',
}

def main():
    os.makedirs(BACKUP_DIR, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
    backup = os.path.join(BACKUP_DIR, f'champions_backup_{ts}.json')
    shutil.copy2(PATH, backup)
    print(f"Backup: {backup}")

    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)

    count = 0
    for champ in data['champions']:
        for field in ['build', 'tips']:
            original = champ.get(field, '')
            if not original:
                continue
            modified = original
            for wrong, correct in FIXES.items():
                if wrong in modified:
                    modified = modified.replace(wrong, correct)
            if modified != original:
                champ[field] = modified
                count += 1
                print(f"  {champ['name']}.{field}")

    with open(PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    # Verify
    with open(PATH, encoding='utf-8') as f:
        text = f.read()
    for wrong in FIXES:
        if wrong in text:
            print(f"ERROR: '{wrong}' still found! Rolling back...")
            shutil.copy2(backup, PATH)
            return
    if len(data['champions']) != 172:
        print(f"ERROR: champion count wrong! Rolling back...")
        shutil.copy2(backup, PATH)
        return

    print(f"\nFixed {count} fields. Verification passed.")

if __name__ == '__main__':
    main()
