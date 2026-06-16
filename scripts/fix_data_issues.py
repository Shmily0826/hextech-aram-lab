"""
fix_data_issues.py
==================
Fix identified data issues:
  1. Cerberus: add Chinese name "地狱三头犬" and effect
  2. Executioner: add Chinese name "裁决使" and effect
  3. Adamant: merge into solid_as_rock (same augment), remove duplicate
  4. Guilty Pleasure: add Chinese name "恶趣味" and effect
  5. Batch fill patch_added for active augments missing it
  6. Auto-classify tags for entries missing them
"""

import json
import shutil
import sys
import os
import re
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

AUGMENTS_PATH = 'data/augments.json'
BACKUP_DIR = 'pipeline/output'
CURRENT_PATCH = '26.12'


def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write('\n')


# ── Chinese name + effect fixes for removed augments ──────
REMOVED_FIXES = {
    'cerberus': {
        'name': '地狱三头犬',
        'effect': '获得丛刃和强攻基石符文。',
        'effect_en': 'Gain the Hail of Blades and Press the Attack Keystone Runes.',
        'tags': ['rune', 'utility'],
    },
    'executioner': {
        'name': '裁决使',
        'effect': '对生命值低于30%的敌人们多造成10%伤害。在参与击杀后重置你的基础技能。',
        'effect_en': 'Deal 10% more damage to enemies below 30% Health. Reset your basic Abilities on takedown.',
        'tags': ['damage', 'execute'],
    },
    'guilty_pleasure': {
        'name': '恶趣味',
        'effect': '定身或缚地敌方英雄时对你进行治疗。',
        'effect_en': 'Immobilizing or Grounding enemy champions heals you.',
        'tags': ['heal', 'cc'],
    },
}

# ── Tag auto-classification rules ──────────────────────────
# Keywords in effect text → tags
TAG_RULES = [
    # Damage
    (['伤害', 'damage', 'magic damage', 'physical damage', 'bonus damage'], 'damage'),
    (['真实伤害', 'true damage'], 'true_damage'),
    (['攻击速度', 'attack speed'], 'attack_speed'),
    (['攻击力', 'attack damage'], 'ad'),
    (['法术强度', 'ability power'], 'ap'),
    (['暴击', 'critical'], 'crit'),
    (['穿甲', 'armor pen', 'lethality'], 'penetration'),
    (['法术穿透', 'magic pen'], 'magic_pen'),
    # Utility
    (['治疗', 'heal', 'health'], 'heal'),
    (['护盾', 'shield'], 'shield'),
    (['移动速度', 'move speed', 'movement speed'], 'movement'),
    (['减速', 'slow'], 'slow'),
    (['击飞', 'knock up'], 'knockup'),
    (['击退', 'knock back'], 'knockback'),
    (['定身', 'root', 'immobiliz'], 'cc'),
    (['缚地', 'ground'], 'cc'),
    (['眩晕', 'stun'], 'cc'),
    (['沉默', 'silence'], 'cc'),
    (['恐惧', 'fear'], 'cc'),
    # Defense
    (['护甲', 'armor'], 'tank'),
    (['魔法抗性', 'magic resist'], 'tank'),
    (['生命值', 'health', 'max health'], 'tank'),
    (['韧性', 'tenacity'], 'tenacity'),
    # Special
    (['符文', 'rune', 'keystone'], 'rune'),
    (['召唤师技能', 'summoner spell'], 'summoner'),
    (['雪球', 'snowball', 'mark'], 'snowball'),
    (['灼烧', 'burn'], 'burn'),
    (['金币', 'gold', 'coin'], 'economy'),
    (['魄罗', 'poro'], 'poro'),
]


def classify_tags(effect, effect_en):
    """Auto-classify tags based on effect text keywords."""
    text = (effect + ' ' + effect_en).lower()
    tags = set()
    for keywords, tag in TAG_RULES:
        for kw in keywords:
            if kw.lower() in text:
                tags.add(tag)
                break
    # Limit to max 4 tags
    if len(tags) > 4:
        # Prioritize: damage > heal > tank > cc > utility
        priority = ['damage', 'true_damage', 'heal', 'shield', 'tank', 'cc',
                     'knockup', 'knockback', 'slow', 'movement', 'attack_speed',
                     'ap', 'ad', 'crit', 'penetration', 'magic_pen', 'rune',
                     'summoner', 'burn', 'economy', 'poro', 'snowball', 'tenacity']
        tags = sorted(tags, key=lambda t: priority.index(t) if t in priority else 99)
        tags = set(tags[:4])
    return sorted(tags) if tags else []


def main():
    print("=" * 60)
    print("  Fix Data Issues")
    print("=" * 60)

    data = load_json(AUGMENTS_PATH)
    id_map = {e['id']: e for e in data}

    # Backup
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = os.path.join(BACKUP_DIR, f'augments_fixissues_{timestamp}.json')
    shutil.copy2(AUGMENTS_PATH, backup_path)
    print(f"  Backup: {backup_path}")

    # ── 1. Fix removed augments (Cerberus, Executioner, Guilty Pleasure) ──
    print(f"\n--- Fix removed augments ---")
    for aid, fixes in REMOVED_FIXES.items():
        if aid in id_map:
            e = id_map[aid]
            old_name = e['name']
            e['name'] = fixes['name']
            if not e.get('effect', '').strip():
                e['effect'] = fixes['effect']
            if not e.get('effect_en', '').strip():
                e['effect_en'] = fixes['effect_en']
            if not e.get('name_en', '') or e['name_en'] == old_name:
                e['name_en'] = old_name  # keep English name
            if not e.get('tags') or len(e.get('tags', [])) == 0:
                e['tags'] = fixes.get('tags', [])
            # Add old English name as alias
            aliases = e.get('aliases', [])
            if old_name.lower() not in [a.lower() for a in aliases]:
                aliases.append(old_name)
            e['aliases'] = aliases
            # Remove localization_status
            e.pop('localization_status', None)
            print(f"  {aid}: '{old_name}' -> '{fixes['name']}'")

    # ── 2. Merge adamant into solid_as_rock ──
    print(f"\n--- Merge adamant -> solid_as_rock ---")
    if 'adamant' in id_map and 'solid_as_rock' in id_map:
        adamant = id_map['adamant']
        sor = id_map['solid_as_rock']

        # Add adamant as alias to solid_as_rock
        aliases = sor.get('aliases', [])
        for a in ['adamant', 'Adamant']:
            if a.lower() not in [x.lower() for x in aliases]:
                aliases.append(a)
        sor['aliases'] = aliases

        # If adamant had patch_removed info, note it
        if adamant.get('patch_removed') and not sor.get('patch_removed'):
            # solid_as_rock is active, so don't set patch_removed
            pass

        # If solid_as_rock has empty effect_en, use adamant's
        if not sor.get('effect_en', '').strip() and adamant.get('effect_en', '').strip():
            sor['effect_en'] = adamant['effect_en']

        # Remove adamant entry
        data = [e for e in data if e['id'] != 'adamant']
        # Rebuild id_map
        id_map = {e['id']: e for e in data}
        print(f"  Merged adamant into solid_as_rock, removed adamant entry")
        print(f"  solid_as_rock aliases: {sor.get('aliases', [])}")

    # ── 3. Batch fill patch_added for active augments ──
    print(f"\n--- Batch fill patch_added ---")
    pa_filled = 0
    for e in data:
        if e.get('status') == 'active' and not e.get('patch_added', '').strip():
            e['patch_added'] = CURRENT_PATCH
            pa_filled += 1
    print(f"  Filled patch_added for {pa_filled} active augments -> '{CURRENT_PATCH}'")

    # ── 4. Auto-classify tags ──
    print(f"\n--- Auto-classify tags ---")
    tags_added = 0
    for e in data:
        if not e.get('tags') or len(e.get('tags', [])) == 0:
            effect = e.get('effect', '')
            effect_en = e.get('effect_en', '')
            new_tags = classify_tags(effect, effect_en)
            if new_tags:
                e['tags'] = new_tags
                tags_added += 1
    print(f"  Auto-classified tags for {tags_added} entries")

    # ── Save ──
    save_json(AUGMENTS_PATH, data)
    print(f"\n  Saved {len(data)} entries")

    # Verify no duplicate names
    names = {}
    for e in data:
        n = e['name']
        names.setdefault(n, []).append(e['id'])
    dupes = {n: ids for n, ids in names.items() if len(ids) > 1}
    if dupes:
        print(f"\n  WARNING: {len(dupes)} duplicate names remain:")
        for n, ids in dupes.items():
            print(f"    '{n}': {ids}")
    else:
        print(f"  No duplicate names.")

    # Verify no empty effects
    empty_eff = [e['id'] for e in data if not e.get('effect', '').strip()]
    if empty_eff:
        print(f"  Empty effects: {len(empty_eff)} ({empty_eff})")
    else:
        print(f"  All entries have effect descriptions.")

    # Count tags coverage
    with_tags = sum(1 for e in data if e.get('tags') and len(e['tags']) > 0)
    print(f"  Tags coverage: {with_tags}/{len(data)}")

    # Count patch_added coverage
    with_pa = sum(1 for e in data if e.get('patch_added'))
    print(f"  patch_added coverage: {with_pa}/{len(data)}")

    print(f"\n{'=' * 60}")


if __name__ == '__main__':
    main()
