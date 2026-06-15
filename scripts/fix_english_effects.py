#!/usr/bin/env python3
"""手动修补剩余缺失的英文效果描述。"""
import json, sys, os, io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(PROJECT, "pipeline", "output", "augment_import_candidates.json")

with open(PATH, "r", encoding="utf-8") as f:
    cands = json.load(f)

# 从英文 3.txt 和 4.txt 直接提取的英文描述
FIXES = {
    "dashing": "Your dash, leap, blink, or teleport Abilities gain 175 Ability Haste.",
    "dropkick": "Your Attacks execute low Health enemy champions, Knocking Back and causing an explosion while healing you.",
    "drop_bear": "On death, a giant Tibbers with all your augments falls from the sky and damages nearby enemies.",
    "devil_on_shoulder": "Forge a pact with The Little Devil himself. He drains your life over time but rewards by applying bonus true damage against champions and creating healing remnants for you to acquire.",
    "droppybara": "Gain Droppybara as a Summoner Spell. After a delay, call down a capybara that deals 30% max Health true damage.",
    "sneakerhead": "Immediate: Gain a random pair of upgraded boots. Requirement: Complete its quest to swap for another. Reward: Jarvan I's Boot.",
    "upgrade_mikaels": "Gain 100% Attack Speed. Increase Sword of Blossoming Dawn's healing to 250% when you attack enemy champions.",
    "pressure_cooker": "Every second, apply a stacking Burn to nearby enemy champions, scaling with your max Health. QUEST: Deal Burn damage to enemy Champions. REWARD: Size and damage increase per Quest Level.",
    "shark_bait": "A few seconds after death, a shark chomps all nearby enemies. You can move after death to aim the shark attack.",
    "shark_storm": "Sharks circle your Snowball, slowing and damaging nearby enemies. When your Snowball hits a Champion, they become trapped in a shark storm!",
    "soul_siphon_new": "Heal for 12% of damage done by Critical Strikes. Gain 25% Crit chance.",
    "sticky_fingers": "Steal a random item from an enemy champion upon takedown.",
    "storm_surge": "Gain Movement Speed when near allied champions.",
    "upgrade_snowball": "Gain 50 Ability Haste on Snowball. Hitting an enemy creates a snowfall that deals AoE damage and Slows nearby enemies. If you don't have one, gain a Snowball.",
    "double_strike": "Your ability applies On-Hit effects an additional time.",
    "homeguard": "Gain 100% Movement Speed, disabled for 6 seconds after taking damage.",
}

count = 0
for c in cands:
    cid = c["id"]
    if cid in FIXES and not c.get("effect_en", ""):
        c["effect_en"] = FIXES[cid]
        count += 1
        print(f"  + {c['name']} ({cid})")

with open(PATH, "w", encoding="utf-8") as f:
    json.dump(cands, f, ensure_ascii=False, indent=2)

with_en = sum(1 for c in cands if c.get("effect_en", ""))
with_zh = sum(1 for c in cands if c.get("effect", ""))
still_empty = sum(1 for c in cands if not c.get("effect_en", ""))
print(f"\n修补了 {count} 个英文描述")
print(f"总计: {len(cands)} 个候选")
print(f"  有中文描述: {with_zh}")
print(f"  有英文描述: {with_en}")
if still_empty:
    print(f"  仍缺少英文描述: {still_empty}")
    for c in cands:
        if not c.get("effect_en", ""):
            print(f"    - {c['name']} ({c['id']})")
