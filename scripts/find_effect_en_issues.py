"""Find augments with '?' placeholders in effect_en fields."""
import json

with open("data/augments.json", "r", encoding="utf-8") as f:
    augs = json.load(f)

print("=== Augments with ? in effect_en ===")
count = 0
for a in augs:
    eff_en = a.get("effect_en", "") or ""
    if "?" in eff_en and eff_en.strip():
        count += 1
        name = a.get("name", "?")
        name_en = a.get("name_en", "?")
        print(f"\n#{count} {name} ({name_en})")
        print(f"  effect_en: {eff_en[:120]}")
        eff = a.get("effect", "") or ""
        if eff:
            print(f"  effect:    {eff[:120]}")

print(f"\nTotal: {count}")
