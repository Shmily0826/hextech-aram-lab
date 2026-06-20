"""
Cross-reference our removed augments against the OFFICIAL 26.12 patch notes.
Official source: https://www.leagueoflegends.com/en-ph/news/game-updates/league-of-legends-patch-26-12-notes/
"""
import json

# Official 26.12 REMOVED augments (39 total, from patch notes)
OFFICIAL_REMOVED_EN = [
    "Buff Buddies",
    "Cerberus",
    "Cheating",
    "Crack Open That Egg",
    "Demon's Dance",
    "Executioner",
    "Feel the Burn",
    "Frost Wraith",
    "Gash",
    "Grandma's Chili Oil",
    "Hat on a Hat",
    "Holy Fire",
    "I'm a Baby Kitty Where is Mama",
    "Keystone Conjurer",
    "Laser Heal",
    "Lightning Strikes",
    "Poro Blaster",
    "Bounce of the Poro King",
    "Rabble Rousing",
    "Red Envelopes",
    "Repulsor",
    "Restless Restoration",
    "Self Destruct",
    "Slow And Steady",
    "Snowball Roulette",
    "Speed Demon",
    "The Brutalizer",
    "Tormentor",
    "Trailblazer",
    "Trueshot Prodigy",
    "Twice Thrice",
    "Upgrade Cutlass",
    "Upgrade Hubris",
    "Upgrade Mikael's Blessing",
    "Upgrade Thornmail",
    "Void Rift",
    "Heads Up Cupcake!",
    "Weighted Popoffs",
    "Wind Beneath Blade",
]

# Normalize for matching
def norm(s):
    return s.lower().replace("'", "'").replace("'", "'").strip()

official_set = set(norm(x) for x in OFFICIAL_REMOVED_EN)
print(f"Official 26.12 removed: {len(official_set)} augments\n")

# Load our data
with open("data/augments.json", "r", encoding="utf-8") as f:
    augs = json.load(f)

our_removed = [a for a in augs if a["status"] == "removed"]
print(f"Our removed: {len(our_removed)} augments\n")

# Match our removed against official
matched_official = set()
should_be_active = []
confirmed_removed = []

for a in our_removed:
    en = norm(a.get("name_en", ""))
    if en in official_set:
        matched_official.add(en)
        confirmed_removed.append(a)
    else:
        should_be_active.append(a)

# Check if any official removals are missing from our data
unmatched_official = official_set - matched_official
if unmatched_official:
    print(f"=== Official removals NOT found in our removed list ({len(unmatched_official)}): ===")
    for name in sorted(unmatched_official):
        # Check if they exist in our data with a different name
        found = False
        for a in augs:
            if norm(a.get("name_en", "")) == name:
                print(f"  {name} -> found as {a['name']} (status={a['status']})")
                found = True
                break
        if not found:
            # Try fuzzy match
            for a in augs:
                a_en = norm(a.get("name_en", ""))
                if a_en and (a_en in name or name in a_en):
                    print(f"  {name} -> fuzzy match: {a['name']} / {a['name_en']} (status={a['status']})")
                    found = True
                    break
            if not found:
                print(f"  {name} -> NOT FOUND in our data at all")
    print()

print(f"=== Confirmed removed (in official 26.12 list): {len(confirmed_removed)} ===")
for a in sorted(confirmed_removed, key=lambda x: x.get("name_en", "")):
    print(f"  {a['name']} ({a['name_en']})")

print(f"\n=== Should be ACTIVE (NOT in official 26.12 removal list): {len(should_be_active)} ===")
for a in sorted(should_be_active, key=lambda x: x.get("name_en", "")):
    print(f"  {a['name']} ({a['name_en']}) id={a['id']}")
