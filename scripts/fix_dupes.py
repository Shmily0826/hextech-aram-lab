"""
fix_dupes.py
Remove duplicate removed augment entries that have active counterparts.
Follows backup→write→validate→rollback pattern.
"""
import json, os, shutil, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUG_PATH = os.path.join(ROOT, 'data', 'augments.json')
BACKUP_PATH = os.path.join(ROOT, 'pipeline', 'output', 'augments_backup_before_fix_dupes.json')

# 1. Backup
shutil.copy2(AUG_PATH, BACKUP_PATH)
print(f"备份 -> {BACKUP_PATH}")

# 2. Load
with open(AUG_PATH, encoding='utf-8') as f:
    augs = json.load(f)

original_count = len(augs)

# 3. Find and remove duplicates
# "碰不到我" (removed, id=can_t_touch_this) is a duplicate of "你摸不到" (active, id=cant_touch_this)
# Both are "Can't Touch This" — remove the removed one since the active one is the correct entry

import re
def norm_en(s):
    return re.sub(r'[^a-z0-9]', '', (s or '').lower().strip())

en_map = {}
for a in augs:
    key = norm_en(a.get('name_en', ''))
    if key:
        en_map.setdefault(key, []).append(a)

to_remove = []
for key, items in en_map.items():
    if len(items) > 1:
        statuses = {a.get('status') for a in items}
        if 'removed' in statuses and 'active' in statuses:
            removed_items = [a for a in items if a.get('status') == 'removed']
            for r in removed_items:
                to_remove.append(r)
                print(f"  删除重复: {r['name']} (id={r.get('id')}, status=removed)")
                print(f"    保留活跃版本: {next(a['name'] for a in items if a.get('status') == 'active')}")

# Remove duplicates
for r in to_remove:
    augs.remove(r)

print(f"\n删除 {len(to_remove)} 个重复条目")
print(f"原始数量: {original_count}, 新数量: {len(augs)}")

# 4. Write
with open(AUG_PATH, 'w', encoding='utf-8') as f:
    json.dump(augs, f, ensure_ascii=False, indent=2)

# 5. Validate
try:
    with open(AUG_PATH, encoding='utf-8') as f:
        validate = json.load(f)
    assert len(validate) == original_count - len(to_remove), f"数量不匹配"
    
    # Verify no more duplicates
    en_check = {}
    for a in validate:
        key = norm_en(a.get('name_en', ''))
        if key:
            en_check.setdefault(key, []).append(a)
    dupes_remaining = sum(1 for k, v in en_check.items() if len(v) > 1 and len({a.get('status') for a in v}) > 1)
    assert dupes_remaining == 0, f"仍有 {dupes_remaining} 个重复"
    
    print("验证通过 ✓")
except Exception as e:
    print(f"验证失败: {e}")
    print("回滚...")
    shutil.copy2(BACKUP_PATH, AUG_PATH)
    sys.exit(1)

# 6. Summary
active_count = sum(1 for a in validate if a.get('status') == 'active')
removed_count = sum(1 for a in validate if a.get('status') == 'removed')
print(f"\n=== 修复后统计 ===")
print(f"  总计: {len(validate)} 个海克斯")
print(f"  活跃: {active_count}")
print(f"  已移除: {removed_count}")
