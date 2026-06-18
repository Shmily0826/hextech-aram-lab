"""Fix 16 augments with '?' placeholders in effect_en.
Two types of ?: 
1. Represents 'chosen ability' (所选技能)
2. Represents a numeric value that was stripped during translation
"""
import json, shutil

SRC = "data/augments.json"
BAK = "data/augments.backup_before_fix_en.json"

# Manual corrections: augment name_en → corrected effect_en
# Derived by comparing with the Chinese effect field
FIXES = {
    "Triple Shot": "Your chosen ability targets 2 additional enemies in front of you.",
    "Spell Splitting": "Your chosen ability missile splits into two on hit, at max Range, or when Recast.",
    "Echoing Release": "Casting your chosen ability sends a clone toward your mouse position and recasts it.",
    "Overload": "Using another Ability resets the cooldown of your chosen ability.",
    "Pin Cushion": "Attacks during your chosen ability apply Marks that explode at the end of its duration, dealing damage and granting Move Speed.",
    "Merciful Strike": "After using your chosen ability, your next basic attack gains attack range, attack speed and deals bonus max Health magic damage.",
    "Terrain Expert": "Your chosen ability deals damage in an area around it.",
    "Nature Heals": "Standing in Brush regenerates 2% max Health per second.",
    "Greedy Grasp": "Immobilizing or Grounding enemy champions with your chosen ability deals extra damage and heals you.",
    "Bang!": "Attacks and Abilities empowered by your chosen ability deal additional damage to the target and nearby enemies.",
    "Stay Firm": "When your chosen ability damages enemy champions, gain 10 Armor and Magic Resistance.",
    "Time To Advance": "Activating your chosen ability grants you Movement Speed for its duration.",
    "Reliable Weapon": "Striking enemy champions with your chosen ability forges a bond of Friendship. Each stack of Friendship grants 5-15 bonus damage based on your level.",
    "Master Crafted": "Increase your Item and Augment damage by 12%.",
    "Adaptive Defense": "Striking an enemy champion with your chosen ability grants you 8 Armor or Magic Resist based on their damage type for 6 seconds. This effect can stack up to 5 times.",
    "Bolstered": "Shields granted from your chosen ability are stronger and scaling with target's missing Health.",
}

def main():
    with open(SRC, "r", encoding="utf-8") as f:
        augs = json.load(f)

    shutil.copy2(SRC, BAK)
    print(f"Backup saved to {BAK}")

    count = 0
    for aug in augs:
        name_en = aug.get("name_en", "")
        if name_en in FIXES:
            old = aug.get("effect_en", "")
            new = FIXES[name_en]
            if old != new:
                aug["effect_en"] = new
                count += 1
                print(f"  ✓ {aug['name']} ({name_en}): '{old[:50]}...' → '{new[:50]}...'")

    with open(SRC, "w", encoding="utf-8") as f:
        json.dump(augs, f, ensure_ascii=False, indent=None, separators=(",", ":"))

    print(f"\nFixed {count} augments")

    # Verify no ? remains
    with open(SRC, "r", encoding="utf-8") as f:
        verify = json.load(f)
    remaining = [a for a in verify if "?" in (a.get("effect_en", "") or "") and a.get("effect_en", "").strip()]
    if remaining:
        print(f"\nWARNING: {len(remaining)} augments still have ? in effect_en")
    else:
        print("All ? placeholders fixed!")

if __name__ == "__main__":
    main()
