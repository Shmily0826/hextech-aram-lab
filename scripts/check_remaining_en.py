"""Check remaining untranslated English in build strings."""
import json, re

with open("data/champions.json", "r", encoding="utf-8") as f:
    data = json.load(f)

remaining = set()
for c in data["champions"]:
    build = c.get("build", "") or ""
    # Find English word sequences > 2 chars starting with capital
    matches = re.findall(r"[A-Z][a-zA-Z'.]{2,}", build)
    for m in matches:
        if m not in ("Q", "W", "E", "R"):
            remaining.add(m)

for r in sorted(remaining):
    print(r)
print(f"\nTotal: {len(remaining)}")
