"""Fix remaining English augment tags."""
import json

EXTRA_TAGS = {
    "ad": "AD",
    "ap": "AP",
    "attack_speed": "攻速",
    "burn": "灼烧",
    "leveling": "成长",
    "magic_pen": "法穿",
    "poro": "魄罗",
    "rune": "符文",
    "snowball": "雪球",
    "summoner": "召唤师",
    "true_damage": "真实伤害",
}

with open("data/augments.json", "r", encoding="utf-8") as f:
    augs = json.load(f)

count = 0
for aug in augs:
    tags = aug.get("tags", [])
    new_tags = []
    for tag in tags:
        if isinstance(tag, str) and tag.lower() in {k.lower(): k for k in EXTRA_TAGS}:
            new_tags.append(EXTRA_TAGS[tag])
            count += 1
        else:
            new_tags.append(tag)
    aug["tags"] = new_tags

with open("data/augments.json", "w", encoding="utf-8") as f:
    json.dump(augs, f, ensure_ascii=False, indent=None, separators=(",", ":"))

print(f"Fixed {count} more tags")

# Verify
remaining = set()
for aug in augs:
    for tag in aug.get("tags", []):
        if isinstance(tag, str) and any(c.isascii() and c.isalpha() for c in tag):
            if tag not in ("AD", "AP"):  # These are standard abbreviations
                remaining.add(tag)
if remaining:
    print(f"Still remaining: {sorted(remaining)}")
else:
    print("All tags localized!")
