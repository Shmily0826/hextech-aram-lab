"""
fix_name_mismatches.py
Fix English name mismatches between our data and arammayhem.com.
These are translation differences, not data errors.
"""
import json, os, shutil, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUG_PATH = os.path.join(ROOT, 'data', 'augments.json')
BACKUP_PATH = os.path.join(ROOT, 'pipeline', 'output', 'augments_backup_before_fix_names.json')

# Name corrections: our name_en -> arammayhem.com name_en
NAME_CORRECTIONS = {
    'Merciful Strike': "Mercy's Strike",
    'Nature Heals': 'Nature is Healing',
    'Echoing Release': 'Echo Cast',
    "Wee Oo Wee Oo": 'Wee Woo Wee Woo',
    'Greedy Grasp': 'Ravenous Bind',
    'Bang': 'BONK!',
    'Ouch My Coins': 'Yowch, My Coins!',
    "Don't Stop Channeling": "Don't Change the Channel",
    'Time To Advance': "It's Go Time",
    'Stackasaurus': 'Stackosaurus Rex',
    'Reliable Weapon': 'Trusty Weapon',
    'Bush Hide': 'Hide on Bush',
    'Endless Rampage': 'Endless Decimation',
    'Terrain Expert': "Terrain'd",
    'Master Crafted': 'Forged By The Master',
    'Ice Burst': 'Snowblast',
    'Stay Firm': 'Stay Resolute',
    'Burst Of Vitality': 'Growth Spurt',
}

# Status fixes for unmatched augments that ARE in arammayhem.com's deleted list
STATUS_TO_REMOVED = {
    'Solid As Rock',       # Deleted on arammayhem
    'Veil Of Protection',  # Deleted on arammayhem
    'Bolstered',           # Deleted on arammayhem
}

# 1. Backup
shutil.copy2(AUG_PATH, BACKUP_PATH)
print(f"备份 -> {BACKUP_PATH}")

# 2. Load
with open(AUG_PATH, encoding='utf-8') as f:
    augs = json.load(f)

# 3. Fix names
name_changes = []
for a in augs:
    old_en = (a.get('name_en') or '').strip()
    if old_en in NAME_CORRECTIONS:
        new_en = NAME_CORRECTIONS[old_en]
        a['name_en'] = new_en
        name_changes.append(f"  {a['name']}: '{old_en}' -> '{new_en}'")

print(f"\n=== 英文名修正: {len(name_changes)} 个 ===")
for c in name_changes:
    print(c)

# 4. Fix status for ones in deleted list
status_changes = []
for a in augs:
    name_en = (a.get('name_en') or '').strip()
    if name_en in STATUS_TO_REMOVED and a.get('status') != 'removed':
        old_status = a['status']
        a['status'] = 'removed'
        status_changes.append(f"  {a['name']} ({name_en}): {old_status} -> removed")

print(f"\n=== 状态修正: {len(status_changes)} 个 ===")
for c in status_changes:
    print(c)

# 5. Write
with open(AUG_PATH, 'w', encoding='utf-8') as f:
    json.dump(augs, f, ensure_ascii=False, indent=2)

# 6. Validate
with open(AUG_PATH, encoding='utf-8') as f:
    validate = json.load(f)

active_count = sum(1 for a in validate if a.get('status') == 'active')
removed_count = sum(1 for a in validate if a.get('status') == 'removed')

print(f"\n=== 最终统计 ===")
print(f"  总计: {len(validate)} 个海克斯")
print(f"  活跃: {active_count} (arammayhem: 190)")
print(f"  已移除: {removed_count} (arammayhem: 65)")

# 7. Check remaining unmatched
def norm(s):
    return re.sub(r'[^a-z0-9]', '', (s or '').lower())

ARAM_ALL_NORM = set()
for n in """Tank Engine, Upgrade Infinity Edge, Quest Steel Your Heart, Heavy Hitter,
Infinite Recursion, Pressure Cooker, Warlock Juicebox, Phenomenal Evil, Draw Your Sword, Dropkick,
Void Immolation, Scopier Weapons, Goliath, Magic Missile, Eureka, Combusting Interest,
Transmute Prismatic, Infernal Conduit, Goredrink, Upgrade Immolate, Spirit Bomb, Ethereal Weapon,
Blunt Force, Giant Slayer, Deft, Dual Wield, Celestial Body, Pursuit of Haste, Ocean Soul,
Stackosaurus Rex, Back To Basics, ADAPt, Twin Fire, High Roller, Windspeaker's Blessing,
Skilled Sniper, Wee Woo Wee Woo, Upgrade Collector, Mystic Punch, Quest Wooglets Witchcap,
Shrink Engine, Ice Cold, Shadow Runner, Slap Around, Donation, Witchful Thinking, Growth Spurt,
Sonata, Forged By The Master, Escape Plan, Mind to Matter, Lil Extra Help, Archmage,
Stats on Stats, With Haste, Siphon, escAPADe, Outlaws Grit, Mad Scientist, Stay Resolute,
Marksmage, Tap Dancer, From Downtown, Recursion, Scoped Weapons, Soul Eater, BONK,
Swift and Safe, Scopiest Weapons, From Beginning To End, Final Form, Upgrade Zhonyas,
Get Excited, Big Brain, Homeguard, Dawnbringers Resolve, Upgrade Sheen, Light em Up,
Terraind, Purist Caster, Leg Day, Tooth Fairy, Overflow, DropBear, Spin To Win, Erosion,
FireFox, King Me, Fan The Hammer, Hand of Baron, Typhoon, Trusty Weapon, Sonic Boom,
FirstAid Kit, Omni Soul, Overextender, Biggest Snowball Ever, Ravenous Bind, Dont Blink,
Quest Support Main, All For You, Its Go Time, Bread And Butter, Bread and Cheese, Minionmancer,
En Passant, Yowch My Coins, Transmute Chaos, Dashing, Dont Change the Channel, Goldrend,
Apex Inventor, Master of Duality, Thread the Needle, Its Killing Time, Cruelty, Flashbang,
Void Dash, Mercys Strike, Quest Urfs Champion, Hextech Soul, Double Defense,
Ultimate Awakening, Bread And Jam, Courage of the Colossus, Ominous Pact,
Empowered By The Faithful, Stats, Flash 2, Ok Boomerang, Firebrand,
Stats on Stats on Stats, Infernal Soul, Overloaded, Adaptive Ward, Nightstalking,
Endless Decimation, Divine Intervention, Searing Dawn, Ultimate Revolution, Shark Bait,
Ultimate Unstoppable, Spiritual Purification, Symphony of War, Nature is Healing,
Circle of Death, Dive Bomber, MountainSoul, Fey Magic, Poltergeist, Tripleshot, Juiced,
Impassable, Blade Waltz, Hellbent, Spellsplit, Empyrean Promise, Shrink Ray, Echo Cast,
Protein Shake, Porcupine, Kill Secured, PandorasBox, Stuck In Here With Me, Shark Tempest,
Hide on Bush, Triggered Inferno, Our Healing, Titans Resolve, Cant Touch This,
Snowday, Rite of Ascension, Prom Queen, Multishot, Pinball, Terror, Mighty Shield,
Snowblast, Spin Me Right Round, Surge Field, Quickstep, Holy Snowball, Pin Cushion,
Glass Cannon, Chain Reaction, Dimension Shift, Poro Stampede, One Trick Pony,
Rejuvenation, Squishy Slappy Grab,
Adamant, Bounce of the Poro King, Buff Buddies, Cerberus, Cheating,
Clown College, Crack Open That Egg, Crit n Cast, Critical Healing, Critical Missile,
Critical Rhythm, Demon's Dance, Devil on Your Shoulder, Double Tap, Droppybara,
Earthwake, Executioner, Feel the Burn, Final City Transit, Frost Wraith, Gash,
Grandma's Chili Oil, Guilty Pleasure, Hat on a Hat, Heads Up Cupcake, Holy Fire,
I'm a Baby Kitty Where is Mama, Icathian Fall, It's Critical, Jeweled Gauntlet,
Keystone Conjurer, Laser Heal, Lightning Strikes, OrbitalLaser, Pat On The Back,
Perseverance, Poro Blaster, Pursuit of Power, Quantum Computing, Rabble Rousing,
Red Envelopes, Repulsor, Restless Restoration, Self Destruct, Slow And Steady,
Slow Cooker, Snowball Roulette, Snowball Upgrade, Soul Siphon, Speed Demon,
Tank It Or Leave It, The Brutalizer, Tormentor, Trailblazer, Transmute Gold,
TrueshotProdigy, Twice Thrice, Upgrade Cutlass, Upgrade Hubris, Upgrade Mikael's Blessing,
Upgrade Thornmail, Vampirism, Void Rift, Vulnerability, Weighted Popoffs,
Wind Beneath Blade, Zealot""".split(','):
    ARAM_ALL_NORM.add(norm(n.strip()))

USER_OVERRIDES = {norm(n) for n in ['Earthwake', 'Icathian Fall', 'Transmute Gold']}

still_unmatched = []
for a in validate:
    key = norm(a.get('name_en', ''))
    if key not in ARAM_ALL_NORM and key not in USER_OVERRIDES:
        still_unmatched.append(f"  {a['name']} ({a.get('name_en','?')}) [{a.get('tier','?')}] status={a.get('status')}")

if still_unmatched:
    print(f"\n=== 仍未匹配arammayhem.com: {len(still_unmatched)} 个 ===")
    for u in still_unmatched:
        print(u)
