"""
fix_status_v2.py
Use arammayhem.com's complete JS-rendered list (190 active + 65 deleted) 
as the authoritative source, plus user overrides.

User confirmed active (despite arammayhem.com saying Deleted):
- Earthwake (大地苏醒)
- Icathian Fall (艾卡西亚的陷落)  
- Transmute Gold (质变：黄金阶)
"""
import json, os, re, shutil, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUG_PATH = os.path.join(ROOT, 'data', 'augments.json')
BACKUP_PATH = os.path.join(ROOT, 'pipeline', 'output', 'augments_backup_before_fix_status_v2.json')

# arammayhem.com active augments (190, from browser JS rendering, June 19 2026)
ARAM_ACTIVE = """Tank Engine, Upgrade Infinity Edge, Quest Steel Your Heart, Heavy Hitter,
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
Rejuvenation, Squishy Slappy Grab"""

# arammayhem.com deleted augments (65)
ARAM_DELETED = """Adamant, Bounce of the Poro King, Buff Buddies, Cerberus, Cheating,
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
Wind Beneath Blade, Zealot"""

# User overrides: these are STILL ACTIVE despite arammayhem.com saying Deleted
USER_ACTIVE_OVERRIDES = {'earthwake', 'icathianfall', 'transmutegold'}

def norm(s):
    return re.sub(r'[^a-z0-9]', '', (s or '').lower())

active_norm = {norm(n) for n in ARAM_ACTIVE.split(',') if n.strip()}
deleted_norm = {norm(n) for n in ARAM_DELETED.split(',') if n.strip()}

print(f"arammayhem.com: {len(active_norm)} active, {len(deleted_norm)} deleted")

# 1. Backup
shutil.copy2(AUG_PATH, BACKUP_PATH)
print(f"备份 -> {BACKUP_PATH}\n")

# 2. Load
with open(AUG_PATH, encoding='utf-8') as f:
    augs = json.load(f)

# 3. Fix status based on arammayhem.com + user overrides
changed_to_active = []
changed_to_removed = []
no_match = []

for a in augs:
    name_en = (a.get('name_en') or '').strip()
    key = norm(name_en)
    current = a.get('status', 'unknown')
    
    # Check user override first
    if key in USER_ACTIVE_OVERRIDES:
        if current != 'active':
            a['status'] = 'active'
            changed_to_active.append(f"  {a['name']} ({name_en}) [{a.get('tier','?')}] -> active (用户确认)")
        continue
    
    # Check arammayhem active list
    if key in active_norm:
        if current != 'active':
            a['status'] = 'active'
            changed_to_active.append(f"  {a['name']} ({name_en}) [{a.get('tier','?')}] -> active")
        continue
    
    # Check arammayhem deleted list
    if key in deleted_norm:
        if current != 'removed':
            a['status'] = 'removed'
            changed_to_removed.append(f"  {a['name']} ({name_en}) [{a.get('tier','?')}] -> removed")
        continue
    
    # Try fuzzy match
    found = False
    for ak in active_norm:
        if key and ak and len(key) > 5 and (key in ak or ak in key):
            if current != 'active':
                a['status'] = 'active'
                changed_to_active.append(f"  {a['name']} ({name_en}) [{a.get('tier','?')}] -> active (模糊匹配)")
            found = True
            break
    if found:
        continue
    
    for dk in deleted_norm:
        if key and dk and len(key) > 5 and (key in dk or dk in key):
            if current != 'removed':
                a['status'] = 'removed'
                changed_to_removed.append(f"  {a['name']} ({name_en}) [{a.get('tier','?')}] -> removed (模糊匹配)")
            found = True
            break
    if found:
        continue
    
    no_match.append(f"  {a['name']} ({name_en}) [{a.get('tier','?')}] status={current} (无匹配)")

print(f"=== 改为 active: {len(changed_to_active)} 个 ===")
for c in changed_to_active:
    print(c)

print(f"\n=== 改为 removed: {len(changed_to_removed)} 个 ===")
for c in changed_to_removed:
    print(c)

print(f"\n=== 无匹配: {len(no_match)} 个 ===")
for c in no_match:
    print(c)

# 4. Write
with open(AUG_PATH, 'w', encoding='utf-8') as f:
    json.dump(augs, f, ensure_ascii=False, indent=2)

# 5. Validate
with open(AUG_PATH, encoding='utf-8') as f:
    validate = json.load(f)

active_count = sum(1 for a in validate if a.get('status') == 'active')
removed_count = sum(1 for a in validate if a.get('status') == 'removed')

print(f"\n=== 修复后统计 ===")
print(f"  总计: {len(validate)} 个海克斯")
print(f"  活跃: {active_count}")
print(f"  已移除: {removed_count}")
print(f"  arammayhem.com: 190 active + 65 deleted = 255")
