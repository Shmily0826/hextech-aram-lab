"""Compress champion_recs.json by stripping unused fields.
Removes h_en and champ_tier which aren't used by the frontend.
"""
import json, os, shutil

SRC = "data/champion_recs.json"
BAK = "data/champion_recs.backup.json"

def main():
    with open(SRC, "r", encoding="utf-8") as f:
        raw = json.load(f)

    orig_size = os.path.getsize(SRC)
    shutil.copy2(SRC, BAK)
    print(f"Backup saved to {BAK}")

    data = raw.get("data", {})
    print(f"Original: {len(data)} augment entries")

    # Strip unused fields
    for aug_id, recs in data.items():
        for rec in recs:
            rec.pop("h_en", None)
            rec.pop("champ_tier", None)

    raw["data"] = data

    with open(SRC, "w", encoding="utf-8") as f:
        json.dump(raw, f, ensure_ascii=False, separators=(",", ":"))

    new_size = os.path.getsize(SRC)
    reduction = (1 - new_size / orig_size) * 100
    print(f"Size: {orig_size:,} → {new_size:,} bytes ({reduction:.1f}% reduction)")

if __name__ == "__main__":
    main()
