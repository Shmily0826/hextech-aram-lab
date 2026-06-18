"""Fix remaining untranslated items and augment names."""
import json, re, shutil

SRC = "data/champions.json"

# Additional translations missed in first pass
EXTRA_MAP = {
    "Bloodthirster": "饮血剑",
    "Riftmaker": "峡谷制造者",
    "Rod of Ages": "时光之杖",
    "Spear of Shojin": "朔极之矛",
    "Edge of Night": "夜之锋刃",
    "Blade of the Ruined King": "破败王者之刃",
    "Shurelya's Battlesong": "舒瑞莉亚的战歌",
    "The Protean": "千变者",
    # ARAM Mayhem augment/item names
    "Dawn and Dusk": "黎明与黄昏",
}

SORTED = sorted(EXTRA_MAP.items(), key=lambda x: -len(x[0]))

def main():
    with open(SRC, "r", encoding="utf-8") as f:
        data = json.load(f)

    count = 0
    for champ in data["champions"]:
        old_build = champ.get("build", "") or ""
        old_tips = champ.get("tips", "") or ""
        new_build = old_build
        new_tips = old_tips
        for en, cn in SORTED:
            new_build = new_build.replace(en, cn)
            new_tips = new_tips.replace(en, cn)
        if new_build != old_build or new_tips != old_tips:
            count += 1
        champ["build"] = new_build
        champ["tips"] = new_tips

    with open(SRC, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=None, separators=(",", ":"))

    print(f"Fixed {count} champions")

    # Re-check remaining English
    remaining = set()
    for c in data["champions"]:
        build = c.get("build", "") or ""
        matches = re.findall(r"[A-Z][a-zA-Z'.]{2,}", build)
        for m in matches:
            if m not in ("Q", "W", "E", "R"):
                remaining.add(m)
    if remaining:
        print(f"Still remaining: {sorted(remaining)}")
    else:
        print("All English text translated!")

if __name__ == "__main__":
    main()
