"""
update_en_effects.py
Fill in English effect descriptions for 19 removed augments that have real effect text.
Follows backup→write→validate→rollback pattern.
"""
import json, os, shutil, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUG_PATH = os.path.join(ROOT, 'data', 'augments.json')
BACKUP_PATH = os.path.join(ROOT, 'pipeline', 'output', 'augments_backup_before_en_effects.json')
CANDIDATES_PATH = os.path.join(ROOT, 'pipeline', 'output', 'en_effects_candidates.json')

# 1. Load candidates
with open(CANDIDATES_PATH, encoding='utf-8') as f:
    data = json.load(f)

candidates = data['candidates']
print(f"准备更新 {len(candidates)} 个海克斯的英文效果描述")

# 2. Backup
shutil.copy2(AUG_PATH, BACKUP_PATH)
print(f"备份 -> {BACKUP_PATH}")

# 3. Load augments
with open(AUG_PATH, encoding='utf-8') as f:
    augs = json.load(f)

# 4. Apply updates
updated = 0
for c in candidates:
    aug = next((a for a in augs if a.get('id') == c['id']), None)
    if not aug:
        print(f"  [跳过] 未找到: {c['id']}")
        continue
    
    old_en = (aug.get('effect_en') or '').strip()
    if old_en:
        print(f"  [跳过] 已有英文效果: {c['name']} ({c['name_en']})")
        continue
    
    aug['effect_en'] = c['effect_en']
    updated += 1
    print(f"  [更新] {c['name']} ({c['name_en']})")
    print(f"    -> {c['effect_en'][:80]}...")

print(f"\n实际更新: {updated} 个")

# 5. Write
with open(AUG_PATH, 'w', encoding='utf-8') as f:
    json.dump(augs, f, ensure_ascii=False, indent=2)
print(f"写入 -> {AUG_PATH}")

# 6. Validate
try:
    with open(AUG_PATH, encoding='utf-8') as f:
        validate = json.load(f)
    assert len(validate) == len(augs), f"数量不匹配: {len(validate)} vs {len(augs)}"
    
    # Verify each updated augment has effect_en
    for c in candidates:
        aug = next((a for a in validate if a.get('id') == c['id']), None)
        if aug:
            assert (aug.get('effect_en') or '').strip(), f"effect_en 仍为空: {c['id']}"
    
    print("验证通过 ✓")
except Exception as e:
    print(f"验证失败: {e}")
    print(f"回滚...")
    shutil.copy2(BACKUP_PATH, AUG_PATH)
    print(f"已回滚 ✓")
    sys.exit(1)

# 7. Summary
total_augs = len(validate)
has_effect = sum(1 for a in validate if (a.get('effect') or '').strip())
has_effect_en = sum(1 for a in validate if (a.get('effect_en') or '').strip())
missing_both = sum(1 for a in validate if not (a.get('effect') or '').strip() and not (a.get('effect_en') or '').strip())

print(f"\n=== 更新后统计 ===")
print(f"  总计: {total_augs} 个海克斯")
print(f"  有中文效果: {has_effect}")
print(f"  有英文效果: {has_effect_en}")
print(f"  中英文都缺: {missing_both}")
