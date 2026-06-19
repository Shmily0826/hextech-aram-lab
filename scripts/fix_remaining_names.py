"""
fix_remaining_names.py
Fix the remaining English name mismatches.
"""
import json, os, shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUG_PATH = os.path.join(ROOT, 'data', 'augments.json')

with open(AUG_PATH, encoding='utf-8') as f:
    augs = json.load(f)

MORE_CORRECTIONS = {
    'Spell Splitting': 'Spellsplit',
    'Overload': 'Overloaded',
    'Support Main': 'Quest Support Main',
    'Adaptive Defense': 'Adaptive Ward',
    'Shark Storm': 'Shark Tempest',
    # Flash Forward: not on arammayhem at all - likely from another source, keep as-is
    # Eat the Path: not on arammayhem - keep as-is
}

changes = []
for a in augs:
    old_en = (a.get('name_en') or '').strip()
    if old_en in MORE_CORRECTIONS:
        a['name_en'] = MORE_CORRECTIONS[old_en]
        changes.append(f"  {a['name']}: '{old_en}' -> '{a['name_en']}'")

print(f"修正 {len(changes)} 个英文名:")
for c in changes:
    print(c)

with open(AUG_PATH, 'w', encoding='utf-8') as f:
    json.dump(augs, f, ensure_ascii=False, indent=2)

# Final count
active = sum(1 for a in augs if a.get('status') == 'active')
removed = sum(1 for a in augs if a.get('status') == 'removed')
print(f"\n最终: {len(augs)} 个, {active} 活跃, {removed} 已移除")
print(f"arammayhem: 190 活跃, 65 删除")
