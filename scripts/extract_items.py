"""Extract all unique item names from champion build strings."""
import json, re

with open("data/champions.json", "r", encoding="utf-8") as f:
    data = json.load(f)

items = set()
for champ in data["champions"]:
    build = champ.get("build", "") or ""
    tips = champ.get("tips", "") or ""
    # Extract item names from build strings
    # Patterns: "起始: X、Y、Z", "核心: X Y Z", "鞋子: X"
    # Items are capitalized English words, often 2-4 words
    # They appear after colons and between separators like 、
    
    # Split by Chinese labels to find item sections
    parts = re.split(r'(?:起始|鞋子|核心|技能|晚期)[:：]', build)
    for part in parts:
        # Split by Chinese separator
        segments = re.split(r'[，,|、\s]{2,}', part)
        for seg in segments:
            seg = seg.strip()
            # Match sequences of English words (item names)
            # Item names typically: Capitalized words with apostrophes and hyphens
            matches = re.findall(r"[A-Z][a-zA-Z'.]+(?:\s+[A-Z][a-zA-Z'.]+)*", seg)
            for m in matches:
                m = m.strip().rstrip('.')
                if len(m) > 3:  # Skip very short matches
                    items.add(m)

for item in sorted(items):
    print(item)

print(f"\nTotal unique items: {len(items)}")
