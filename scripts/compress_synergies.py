"""Compress synergies.json by shortening field names.
Expected ~62% size reduction: 618KB → ~140KB
"""
import json, os, shutil

SRC = "data/synergies.json"
BAK = "data/synergies.backup_before_compress.json"

# Mapping: full → short
KEY_MAP = {
    "hero": "h",
    "aug": "a",
    "rar": "r",
    "tier": "t",
    "conf": "c",
    "ver": "v",
    "src": "s",
    "status": "st",
}

def main():
    with open(SRC, "r", encoding="utf-8") as f:
        data = json.load(f)

    print(f"Original: {len(data)} synergies")
    print(f"Original keys: {list(data[0].keys())}")

    # Backup
    shutil.copy2(SRC, BAK)
    print(f"Backup saved to {BAK}")

    # Compress
    compressed = []
    for item in data:
        new_item = {}
        for old_key, new_key in KEY_MAP.items():
            if old_key in item:
                new_item[new_key] = item[old_key]
        # Keep any unknown keys as-is
        for k, v in item.items():
            if k not in KEY_MAP:
                new_item[k] = v
        compressed.append(new_item)

    # Write compressed
    with open(SRC, "w", encoding="utf-8") as f:
        json.dump(compressed, f, ensure_ascii=False, separators=(",", ":"))

    orig_size = os.path.getsize(BAK)
    new_size = os.path.getsize(SRC)
    reduction = (1 - new_size / orig_size) * 100

    print(f"Compressed keys: {list(compressed[0].keys())}")
    print(f"Size: {orig_size:,} → {new_size:,} bytes ({reduction:.1f}% reduction)")
    print(f"Sample: {json.dumps(compressed[0], ensure_ascii=False)}")

if __name__ == "__main__":
    main()
