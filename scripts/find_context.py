"""Find context of remaining English fragments."""
import json

with open("data/champions.json", "r", encoding="utf-8") as f:
    data = json.load(f)

fragments = ["Blade", "Dawn", "Dusk", "Diadem", "Rite", "Ruin", "Songs"]
for c in data["champions"]:
    build = c.get("build", "") or ""
    for frag in fragments:
        if frag in build:
            idx = build.index(frag)
            start = max(0, idx - 20)
            end = min(len(build), idx + len(frag) + 20)
            context = build[start:end]
            name = c["name"]
            print(f"{name}: ...{context}...")
