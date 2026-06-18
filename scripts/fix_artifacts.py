"""Fix scraping artifacts where English prefixes remain alongside Chinese translations."""
import json, shutil

SRC = "data/champions.json"

# These are scraping artifacts that need cleanup
FIXES = {
    "Blade of 破败王者之刃": "破败王者之刃",
    "Dusk and Dawn": "黎明与黄昏",
    "Rite of Ruin": "毁灭仪式",
    "Diadem of Songs": "歌之冕",
}

SORTED = sorted(FIXES.items(), key=lambda x: -len(x[0]))

def main():
    with open(SRC, "r", encoding="utf-8") as f:
        data = json.load(f)

    count = 0
    for champ in data["champions"]:
        changed = False
        for field in ["build", "tips"]:
            val = champ.get(field, "") or ""
            new_val = val
            for old, new in SORTED:
                new_val = new_val.replace(old, new)
            if new_val != val:
                champ[field] = new_val
                changed = True
        if changed:
            count += 1

    with open(SRC, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=None, separators=(",", ":"))

    print(f"Fixed {count} champions")

    # Verify
    import re
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
