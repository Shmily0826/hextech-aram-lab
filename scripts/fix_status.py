"""
fix_status.py
Fix status of augments incorrectly marked as removed.
Based on official Riot Patch 26.12 notes cross-reference.

10 confirmed active (LoL Wiki + not in official removal list):
- Earthwake, Icathian Fall, Transmute Gold, Guilty Pleasure,
  Devil on Your Shoulder, Final City Transit, It's Critical,
  Perseverance, Snowball Upgrade, Critical Healing (user confirmed in-game)

6 uncertain (not in official removals, not on wiki):
- OrbitalLaser, Slow Cooker, Tank It Or Leave It, Bolstered,
  Flash Forward, Solid As Rock
  -> Also changing to active since NOT in official removal list
"""
import json, os, shutil, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUG_PATH = os.path.join(ROOT, 'data', 'augments.json')
BACKUP_PATH = os.path.join(ROOT, 'pipeline', 'output', 'augments_backup_before_fix_status.json')

# 1. Backup
shutil.copy2(AUG_PATH, BACKUP_PATH)
print(f"备份 -> {BACKUP_PATH}")

# 2. Load
with open(AUG_PATH, encoding='utf-8') as f:
    augs = json.load(f)

# Official 26.12 removal list (40 augments from Riot patch notes)
OFFICIAL_REMOVED_EN = {
    'buff buddies', 'cerberus', 'cheating', 'crack open that egg',
    "crit 'n cast", 'demon\'s dance', 'executioner', 'feel the burn',
    'frost wraith', 'gash', 'grandma\'s chili oil', 'hat on a hat',
    'holy fire', 'i\'m a baby kitty where is mama', 'keystone conjurer',
    'laser heal', 'lightning strikes', 'poro blaster',
    'bounce of the poro king', 'rabble rousing', 'red envelopes',
    'repulsor', 'restless restoration', 'self destruct',
    'slow and steady', 'snowball roulette', 'speed demon',
    'the brutalizer', 'tormentor', 'trailblazer', 'trueshot prodigy',
    'twice thrice', 'upgrade cutlass', 'upgrade hubris',
    'upgrade: mikael\'s blessing', 'upgrade thornmail',
    'void rift', 'heads up cupcake!', 'weighted popoffs',
    'wind beneath blade',
    # Additional confirmed by official notes:
    'critical missile', 'critical rhythm', 'double tap',
    'droppybara', 'quantum computing', 'vampirism', 'vulnerability',
    'clown college',
}

# Normalize for comparison
def norm(s):
    import re
    return re.sub(r'[^a-z0-9]', '', (s or '').lower())

official_norm = {norm(n) for n in OFFICIAL_REMOVED_EN}

# 3. Fix status
changed = []
for a in augs:
    if a.get('status') != 'removed':
        continue
    
    name_en = (a.get('name_en') or '').strip()
    key = norm(name_en)
    
    if key not in official_norm:
        # NOT in official removal list -> should be active
        old_status = a['status']
        a['status'] = 'active'
        changed.append({
            'name': a['name'],
            'name_en': name_en,
            'tier': a.get('tier', '?'),
            'old': old_status,
            'new': 'active',
        })
        print(f"  {a['name']:20s} ({name_en:30s}) [{a.get('tier','?'):10s}] removed -> active")

print(f"\n修改 {len(changed)} 个海克斯状态: removed -> active")

# 4. Write
with open(AUG_PATH, 'w', encoding='utf-8') as f:
    json.dump(augs, f, ensure_ascii=False, indent=2)

# 5. Validate
try:
    with open(AUG_PATH, encoding='utf-8') as f:
        validate = json.load(f)
    assert len(validate) == len(augs), f"数量不匹配"
    
    active_count = sum(1 for a in validate if a.get('status') == 'active')
    removed_count = sum(1 for a in validate if a.get('status') == 'removed')
    
    print("验证通过 ✓")
except Exception as e:
    print(f"验证失败: {e}")
    print("回滚...")
    shutil.copy2(BACKUP_PATH, AUG_PATH)
    sys.exit(1)

# 6. Summary
print(f"\n=== 修复后统计 ===")
print(f"  总计: {len(validate)} 个海克斯")
print(f"  活跃: {active_count}")
print(f"  已移除: {removed_count}")

# 7. List remaining removed
remaining = [a for a in validate if a.get('status') == 'removed']
print(f"\n=== 仍然标记为已移除 ({len(remaining)} 个) ===")
for a in remaining:
    print(f"  {a['name']:20s} ({a.get('name_en','?'):30s}) [{a.get('tier','?')}]")
