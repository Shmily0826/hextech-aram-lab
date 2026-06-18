"""Normalize augments.json: remove redundant 'rar' field where 'tier' already exists.
26 augments have both rar=prism and tier=prismatic — keep tier, remove rar.
"""
import json, shutil

SRC = "data/augments.json"
BAK = "backups/augments.backup_before_normalize.json"

with open(SRC, "r", encoding="utf-8") as f:
    augs = json.load(f)

shutil.copy2(SRC, BAK)

count = 0
for aug in augs:
    if "rar" in aug and "tier" in aug:
        del aug["rar"]
        count += 1

with open(SRC, "w", encoding="utf-8") as f:
    json.dump(augs, f, ensure_ascii=False, indent=None, separators=(",", ":"))

print(f"Removed 'rar' field from {count} augments")

# Verify
with open(SRC, "r", encoding="utf-8") as f:
    verify = json.load(f)
has_rar = sum(1 for a in verify if "rar" in a)
print(f"Augments with 'rar' field remaining: {has_rar}")
