"""
check_item_names.py
Extract all unique item names from champions.json build strings
and check for potential mismatches with official Chinese LoL item names.
"""
import json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

with open(os.path.join(ROOT, 'data', 'champions.json'), encoding='utf-8') as f:
    data = json.load(f)

# Extract all item names from build strings
# Build format: "技能: ... | 起始: item1、item2 | 鞋子: item1、item2 | 核心: item1 item2 item3 (XX% 胜率)"
item_pattern = re.compile(r'[\u4e00-\u9fff\uff1a][\u4e00-\u9fff0-9a-zA-Z·：\-\']+(?:之[\u4e00-\u9fff]+)?')

all_items = set()
for c in data['champions']:
    build = c.get('build', '')
    if not build:
        continue
    # Split by sections
    for section in build.split('|'):
        section = section.strip()
        # Skip skill section
        if section.startswith('技能'):
            continue
        # Remove prefix like "起始:", "鞋子:", "核心:"
        if ':' in section:
            section = section.split(':', 1)[1].strip()
        # Remove win rate suffix like "(50.52% 胜率)"
        section = re.sub(r'\([\d.]+%\s*胜率\)', '', section)
        # Split by 、 and spaces
        items = re.split(r'[、\s]+', section.strip())
        for item in items:
            item = item.strip()
            if len(item) >= 2 and not item.startswith('('):
                all_items.add(item)

print(f"Found {len(all_items)} unique item names:\n")
for item in sorted(all_items):
    print(f"  {item}")

# Known suspicious items to flag
suspicious = {
    '傲慢': '狂妄 (Hubris)',
}

print(f"\n=== Suspicious items ===")
for s, correct in suspicious.items():
    if s in all_items:
        count = sum(1 for c in data['champions'] if s in c.get('build', ''))
        print(f"  '{s}' found in {count} champions -> should be '{correct}'")
    else:
        print(f"  '{s}' NOT found (already fixed?)")
