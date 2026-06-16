"""
补充 8 个缺失增强到 augments.json
数据来源：blitz.gg 中文/英文页面
"""
import json
import os
import shutil
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUGMENTS_PATH = os.path.join(ROOT, 'data', 'augments.json')
BACKUP_PATH = os.path.join(ROOT, 'pipeline', 'output',
                           f'augments_backup_{date.today().isoformat()}_add8.json')

# 8 个新增增强
NEW_AUGMENTS = [
    {
        "id": "its_go_time",
        "name": "前进时间到",
        "name_en": "It's Go Time",
        "aliases": ["it's go time", "its go time", "go time"],
        "tier": "silver",
        "status": "active",
        "effect": "激活召唤师技能时，在其持续期间获得移动速度。",
        "effect_en": "Activating a Summoner Spell grants you Movement Speed for its duration.",
        "tags": ["utility", "movement"],
        "patch_added": "26.12",
        "patch_removed": None,
        "source": {
            "type": "blitz.gg",
            "url": "https://blitz.gg/lol/aram-mayhem-augments",
            "verified_at": date.today().isoformat()
        },
        "notes": ""
    },
    {
        "id": "rejuvenation",
        "name": "活力焕发",
        "name_en": "Rejuvenation",
        "aliases": ["rejuvenation"],
        "tier": "gold",
        "status": "active",
        "effect": "使用召唤师技能时回复生命值。",
        "effect_en": "Using a Summoner Spell restores Health.",
        "tags": ["heal", "utility"],
        "patch_added": "26.12",
        "patch_removed": None,
        "source": {
            "type": "blitz.gg",
            "url": "https://blitz.gg/lol/aram-mayhem-augments",
            "verified_at": date.today().isoformat()
        },
        "notes": ""
    },
    {
        "id": "trusty_weapon",
        "name": "可靠武器",
        "name_en": "Trusty Weapon",
        "aliases": ["trusty weapon"],
        "tier": "silver",
        "status": "active",
        "effect": "用攻击技能打击敌方英雄时会铸造一条友谊纽带。该技能基于友谊等级获得临时提升伤害。",
        "effect_en": "Striking enemy champions with an attack forges a bond of Friendship. The attack gains temporarily increased damage based on your level of Friendship.",
        "tags": ["damage"],
        "patch_added": "26.12",
        "patch_removed": None,
        "source": {
            "type": "blitz.gg",
            "url": "https://blitz.gg/lol/aram-mayhem-augments",
            "verified_at": date.today().isoformat()
        },
        "notes": ""
    },
    {
        "id": "en_passant",
        "name": "吃过路兵",
        "name_en": "En Passant",
        "aliases": ["en passant"],
        "tier": "prismatic",
        "status": "active",
        "effect": "周期性地识别出敌方英雄身上的破绽。用攻击或技能命中时，会造成最大生命值真实伤害、回复生命值并提供移动速度。这些效果可以叠加。",
        "effect_en": "Periodically identify Vitals on enemy champions. Hitting them with Attacks or Abilities deals max Health true damage, restores Health, and grants Movement Speed. These effects can stack.",
        "tags": ["damage", "heal", "movement"],
        "patch_added": "26.12",
        "patch_removed": None,
        "source": {
            "type": "blitz.gg",
            "url": "https://blitz.gg/lol/aram-mayhem-augments",
            "verified_at": date.today().isoformat()
        },
        "notes": "名字来源于国际象棋术语（吃过路兵）"
    },
    {
        "id": "wee_woo_wee_woo",
        "name": "喂呜喂呜",
        "name_en": "Wee Woo Wee Woo",
        "aliases": ["wee woo wee woo", "wee woo"],
        "tier": "gold",
        "status": "active",
        "effect": "在朝着低生命值的友军移动时，获得移动速度。你的治疗和护盾获得提升，基于目标的低生命值程度。",
        "effect_en": "When moving towards allies with low Health, gain Movement Speed. Your Healing and Shielding are greater based on how low your target's Health is.",
        "tags": ["heal", "shield", "movement", "support"],
        "patch_added": "26.12",
        "patch_removed": None,
        "source": {
            "type": "blitz.gg",
            "url": "https://blitz.gg/lol/aram-mayhem-augments",
            "verified_at": date.today().isoformat()
        },
        "notes": "名字模拟警笛声，配合辅助型玩法"
    },
    {
        "id": "echo_cast",
        "name": "回响施放",
        "name_en": "Echo Cast",
        "aliases": ["echo cast"],
        "tier": "prismatic",
        "status": "active",
        "effect": "施放技能时会朝鼠标位置派出一个复制体并再次施放该技能。",
        "effect_en": "Casting your ability sends a clone toward your mouse position and recasts it.",
        "tags": ["utility"],
        "patch_added": "26.12",
        "patch_removed": None,
        "source": {
            "type": "blitz.gg",
            "url": "https://blitz.gg/lol/aram-mayhem-augments",
            "verified_at": date.today().isoformat()
        },
        "notes": ""
    },
    {
        "id": "ravenous_bind",
        "name": "贪欲束缚",
        "name_en": "Ravenous Bind",
        "aliases": ["ravenous bind"],
        "tier": "gold",
        "status": "active",
        "effect": "用技能定身或缚地敌方英雄时造成额外伤害并治疗你。",
        "effect_en": "Immobilizing or Grounding enemy champions with an ability deals extra damage and heals you.",
        "tags": ["damage", "heal", "cc"],
        "patch_added": "26.12",
        "patch_removed": None,
        "source": {
            "type": "blitz.gg",
            "url": "https://blitz.gg/lol/aram-mayhem-augments",
            "verified_at": date.today().isoformat()
        },
        "notes": ""
    },
    {
        "id": "minionmancer",
        "name": "仆从大师",
        "name_en": "Minionmancer",
        "aliases": ["minionmancer"],
        "tier": "gold",
        "status": "active",
        "effect": "你的召唤物获得40%体型提升、生命值和伤害。",
        "effect_en": "Your summons gain 40% increased size, health, and damage.",
        "tags": ["damage", "utility"],
        "patch_added": "26.12",
        "patch_removed": None,
        "source": {
            "type": "blitz.gg",
            "url": "https://blitz.gg/lol/aram-mayhem-augments",
            "verified_at": date.today().isoformat()
        },
        "notes": ""
    }
]


def main():
    # 1. 备份
    shutil.copy2(AUGMENTS_PATH, BACKUP_PATH)
    print(f"Backup: {BACKUP_PATH}")

    # 2. 加载现有数据
    with open(AUGMENTS_PATH, 'r', encoding='utf-8') as f:
        augments = json.load(f)
    
    existing_ids = {a['id'] for a in augments}
    existing_names_en = {a.get('name_en', '').lower() for a in augments}
    
    added = 0
    for new_aug in NEW_AUGMENTS:
        if new_aug['id'] in existing_ids:
            print(f"  SKIP (id exists): {new_aug['id']}")
            continue
        if new_aug['name_en'].lower() in existing_names_en:
            print(f"  SKIP (name exists): {new_aug['name_en']}")
            continue
        
        augments.append(new_aug)
        added += 1
        print(f"  ADD: {new_aug['name']} ({new_aug['name_en']}) [{new_aug['tier']}]")
    
    # 3. 排序：按 tier(prismatic > gold > silver) 再按 name
    tier_order = {'prismatic': 0, 'gold': 1, 'silver': 2, 'unknown': 3}
    augments.sort(key=lambda a: (tier_order.get(a.get('tier', 'unknown'), 3),
                                  a.get('name', '')))
    
    # 4. 写回
    with open(AUGMENTS_PATH, 'w', encoding='utf-8') as f:
        json.dump(augments, f, ensure_ascii=False, indent=2)
    
    print(f"\nAdded {added} augments. Total: {len(augments)}")


if __name__ == '__main__':
    main()
