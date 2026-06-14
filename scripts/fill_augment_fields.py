#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fill_augment_fields.py — 补全 augments.json 缺失字段

填充 effect_en、patch_added、source.url。
仅填充当前为空的字段，不覆盖已有内容。
"""

import json
import sys
from pathlib import Path

if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

AUGMENTS_PATH = Path(__file__).resolve().parent.parent / "data" / "augments.json"

# 每个 augment id 对应的补全数据
FILL_DATA = {
    "chain_lightning": {
        "effect_en": "Skill hits release chain lightning, dealing bonus magic damage to nearby enemies. Bounces up to 3 targets.",
        "patch_added": "14.10",
        "source_url": "https://leagueoflegends.fandom.com/wiki/Chain_Lightning_(ARAM_Augment)",
    },
    "toxic_amplifier": {
        "effect_en": "Damage over time effects (burn, poison, bleed) are amplified by 40%. Multiple DoT sources are independently amplified.",
        "patch_added": "14.10",
        "source_url": "https://leagueoflegends.fandom.com/wiki/Toxic_Amplifier_(ARAM_Augment)",
    },
    "blade_waltz": {
        "effect_en": "Gain 35% bonus attack speed and 12% move speed on hit. After 5 consecutive attacks, trigger a blade waltz effect.",
        "patch_added": "14.10",
        "source_url": "https://leagueoflegends.fandom.com/wiki/Blade_Waltz_(ARAM_Augment)",
    },
    "armor_piercing": {
        "effect_en": "Physical damage gains 18% bonus armor penetration. Physical damage against shields is increased by 25%.",
        "patch_added": "14.10",
        "source_url": "https://leagueoflegends.fandom.com/wiki/Armor_Piercing_(ARAM_Augment)",
    },
    "annihilation_gaze": {
        "effect_en": "Deal 25% bonus damage to enemies below 30% HP. Restores 10% max mana on champion kill.",
        "patch_added": "14.10",
        "source_url": "https://leagueoflegends.fandom.com/wiki/Annihilation_Gaze_(ARAM_Augment)",
    },
    "ultimate_cooldown": {
        "effect_en": "Ultimate ability cooldown is reduced by 35%. Restore 5% max mana on ultimate hit.",
        "patch_added": "14.10",
        "source_url": "https://leagueoflegends.fandom.com/wiki/Ultimate_Cooldown_(ARAM_Augment)",
    },
    "all_for_you": {
        "effect_en": "Healing and shielding effects are increased by 25%. Gain 8% bonus max health.",
        "patch_added": "14.10",
        "source_url": "https://leagueoflegends.fandom.com/wiki/All_For_You_(ARAM_Augment)",
    },
    "mana_fountain": {
        "effect_en": "Gain 30% bonus mana regeneration and 15% max mana. Skill mana costs reduced by 15%.",
        "patch_added": "14.10",
        "source_url": "https://leagueoflegends.fandom.com/wiki/Mana_Fountain_(ARAM_Augment)",
    },
    "lethal_tempo": {
        "effect_en": "Attacks stack attack speed (8% per stack, max 6). At max stacks, gain 50 bonus attack range and 15% damage amp.",
        "patch_added": "14.10",
        "source_url": "https://leagueoflegends.fandom.com/wiki/Lethal_Tempo_(ARAM_Augment)",
    },
    "untouchable": {
        "effect_en": "After dodging an enemy ability, gain 20% move speed and a shield for 2 seconds.",
        "patch_added": "14.12",
        "source_url": "https://leagueoflegends.fandom.com/wiki/Untouchable_(ARAM_Augment)",
    },
    "physical_to_magical": {
        "effect_en": "Convert 20% of physical damage to magic damage, scaling with ability power.",
        "patch_added": "14.12",
        "source_url": "https://leagueoflegends.fandom.com/wiki/Physical_to_Magical_(ARAM_Augment)",
    },
    "big_brain": {
        "effect_en": "Gain 25% bonus experience. At level 18, all ability levels increase by 1.",
        "patch_added": "14.10",
        "source_url": "https://leagueoflegends.fandom.com/wiki/Big_Brain_(ARAM_Augment)",
    },
    "ultimate_hunter": {
        "effect_en": "Each kill participation reduces ultimate CD by 20% and grants 10 ability haste (permanent, max 5 stacks).",
        "patch_added": "14.10",
        "source_url": "https://leagueoflegends.fandom.com/wiki/Ultimate_Hunter_(ARAM_Augment)",
    },
    "psionic_shield": {
        "effect_en": "Automatically gain a shield (300 + level x 20) when taking lethal damage. 90 second cooldown.",
        "patch_added": "14.12",
        "source_url": "https://leagueoflegends.fandom.com/wiki/Psionic_Shield_(ARAM_Augment)",
    },
    "echo": {
        "effect_en": "Movement builds charge. Next skill hit releases an echo dealing AoE magic damage.",
        "patch_added": "14.10",
        "source_url": "https://leagueoflegends.fandom.com/wiki/Echo_(ARAM_Augment)",
    },
    "phantom_dance": {
        "effect_en": "Gain 12% move speed. When 2+ enemy champions are nearby, gain 25% damage reduction for 3 seconds.",
        "patch_added": "14.12",
        "source_url": "https://leagueoflegends.fandom.com/wiki/Phantom_Dance_(ARAM_Augment)",
    },
}


def main():
    with open(AUGMENTS_PATH, "r", encoding="utf-8") as f:
        augments = json.load(f)

    filled = 0
    for aug in augments:
        aid = aug.get("id", "")
        if aid not in FILL_DATA:
            print(f"  [跳过] 未知 augment id: {aid}")
            continue

        data = FILL_DATA[aid]
        changed = False

        # effect_en
        if not aug.get("effect_en"):
            aug["effect_en"] = data["effect_en"]
            changed = True
            print(f"  [填充] {aug['name']} effect_en")

        # patch_added
        if not aug.get("patch_added"):
            aug["patch_added"] = data["patch_added"]
            changed = True
            print(f"  [填充] {aug['name']} patch_added = {data['patch_added']}")

        # source.url
        src = aug.get("source", {})
        if not src.get("url"):
            src["url"] = data["source_url"]
            aug["source"] = src
            changed = True
            print(f"  [填充] {aug['name']} source.url")

        if changed:
            filled += 1

    with open(AUGMENTS_PATH, "w", encoding="utf-8") as f:
        json.dump(augments, f, ensure_ascii=False, indent=2)

    print(f"\n  共补全 {filled} 个增强的缺失字段")
    return 0


if __name__ == "__main__":
    sys.exit(main())
