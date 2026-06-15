#!/usr/bin/env python3
"""Quick check script for augment list data."""
import io, json, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

with open("pipeline/output/arammayhem_augment_list.json", "r", encoding="utf-8") as f:
    data = json.load(f)

print(f"Total augments: {len(data)}")
print(f"\n--- First 15 ---")
for d in data[:15]:
    rank = d.get("rank", "?")
    tier = d.get("tier", "?")
    name = d.get("name_zh", "?")
    slug = d.get("slug", "?")
    print(f"  {rank:>3}. [{tier:>10}] {name}  ({slug})")

print(f"\n--- Entries with '质变' ---")
for d in data:
    if "质变" in d.get("name_zh", ""):
        rank = d.get("rank", "?")
        tier = d.get("tier", "?")
        name = d.get("name_zh", "?")
        slug = d.get("slug", "?")
        print(f"  {rank:>3}. [{tier:>10}] {name}  ({slug})")

# Count by tier
tiers = {}
for d in data:
    t = d.get("tier", "unknown")
    tiers[t] = tiers.get(t, 0) + 1
print(f"\n--- Tier distribution ---")
for t, c in sorted(tiers.items()):
    print(f"  {t}: {c}")

# Check for empty names
empty = [d for d in data if not d.get("name_zh", "").strip()]
if empty:
    print(f"\n--- WARNING: {len(empty)} entries with empty names ---")
    for d in empty[:5]:
        print(f"  slug: {d.get('slug', '?')}")
