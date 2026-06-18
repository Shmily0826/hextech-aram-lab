"""Extract all unique Chinese item names from champion build strings.
Also extract the raw build strings for manual review.
"""
import json, re

with open("data/champions.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# Collect all unique Chinese item-like strings from build fields
# Items appear after labels like "起始:", "鞋子:", "核心:", "晚期:"
items_in_starting = set()
items_in_boots = set()
items_in_core = set()
items_in_late = set()
all_items = set()

for champ in data["champions"]:
    build = champ.get("build", "") or ""
    
    # Parse sections
    sections = re.split(r'\|', build)
    for sec in sections:
        sec = sec.strip()
        if sec.startswith("起始:") or sec.startswith("起始："):
            items_part = re.sub(r'^起始[:：]\s*', '', sec)
            for item in re.split(r'[、,，\s]+', items_part):
                item = item.strip()
                if item and len(item) > 1:
                    items_in_starting.add(item)
                    all_items.add(item)
        elif sec.startswith("鞋子:") or sec.startswith("鞋子："):
            items_part = re.sub(r'^鞋子[:：]\s*', '', sec)
            for item in re.split(r'[、,，\s]+', items_part):
                item = item.strip()
                if item and len(item) > 1:
                    items_in_boots.add(item)
                    all_items.add(item)
        elif sec.startswith("核心:") or sec.startswith("核心："):
            items_part = re.sub(r'^核心[:：]\s*', '', sec)
            # Core builds: items separated by spaces, with (XX% 胜率) at end
            items_part = re.sub(r'\(.*?\)', '', items_part).strip()
            for item in re.split(r'[、,，\s]+', items_part):
                item = item.strip()
                if item and len(item) > 1:
                    items_in_core.add(item)
                    all_items.add(item)
        elif sec.startswith("晚期:") or sec.startswith("晚期："):
            items_part = re.sub(r'^晚期[:：]\s*', '', sec)
            items_part = re.sub(r'\(.*?\)', '', items_part).strip()
            for item in re.split(r'[、,，\s]+', items_part):
                item = item.strip()
                if item and len(item) > 1:
                    items_in_late.add(item)
                    all_items.add(item)

print("=== ALL UNIQUE ITEMS ===")
for item in sorted(all_items):
    print(f"  {item}")
print(f"\nTotal unique items: {len(all_items)}")

print("\n=== BOOTS ===")
for item in sorted(items_in_boots):
    print(f"  {item}")

print("\n=== STARTING ITEMS ===")
for item in sorted(items_in_starting):
    print(f"  {item}")
