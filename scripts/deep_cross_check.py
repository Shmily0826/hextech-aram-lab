"""
deep_cross_check.py
Deep cross-reference using English names to find true status mismatches.
Also detect potential duplicates (same English name, different Chinese name).
"""
import json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

with open(os.path.join(ROOT, 'data', 'augments.json'), encoding='utf-8') as f:
    augs = json.load(f)

# Active English names from arammayhem.com (actual fetch, no manual additions)
ARAM_EN = [n.strip() for n in """Tank Engine, Upgrade Infinity Edge, Quest Steel Your Heart, Heavy Hitter, 
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
En Passant, Yowch, My Coins, Transmute Chaos, Dashing, Dont Change the Channel, Goldrend, 
Apex Inventor""".split(',') if n.strip()]

def norm_en(s):
    """Normalize English name for comparison"""
    s = s.lower().strip()
    s = re.sub(r'[^a-z0-9]', '', s)
    return s

aram_set = {norm_en(n): n for n in ARAM_EN}
print(f"arammayhem.com 活跃: {len(aram_set)} 个\n")

# 1. Check for duplicates (same English name, different status)
en_to_augs = {}
for a in augs:
    en = (a.get('name_en') or '').strip()
    if en:
        key = norm_en(en)
        en_to_augs.setdefault(key, []).append(a)

print("=== 英文重名检查 (可能的重复) ===")
dups = {k: v for k, v in en_to_augs.items() if len(v) > 1}
for k, items in dups.items():
    statuses = [a.get('status','?') for a in items]
    names = [f"{a['name']}({a.get('status','?')})" for a in items]
    print(f"  {k}: {', '.join(names)}")

# 2. Check removed augments against arammayhem active list using EN names
print(f"\n=== 已移除海克斯 vs arammayhem.com 活跃列表 ===")
removed = [a for a in augs if a.get('status') == 'removed']
for a in removed:
    en = (a.get('name_en') or '').strip()
    key = norm_en(en)
    if key in aram_set:
        print(f"  [!] {a['name']} ({en}) [{a.get('tier','?')}] - 在arammayhem活跃列表中!")
        print(f"      arammayhem名称: {aram_set[key]}")
    else:
        # Try fuzzy: check if one is substring of other
        for aram_key, aramname in aram_set.items():
            if key and aram_key and len(key) > 5 and len(aram_key) > 5:
                if key in aram_key or aram_key in key:
                    print(f"  [~] {a['name']} ({en}) [{a.get('tier','?')}] - 模糊匹配: {aramname}")
                    break

# 3. Check our active augments against arammayhem
print(f"\n=== 我们的活跃海克斯不在 arammayhem.com 上 ===")
our_active = [a for a in augs if a.get('status') == 'active']
not_on_site = []
for a in our_active:
    en = (a.get('name_en') or '').strip()
    key = norm_en(en)
    if key in aram_set:
        continue  # Found
    # Try fuzzy
    found = False
    for aramkey in aram_set:
        if key and aramkey and len(key) > 5 and len(aramkey) > 5:
            if key in aramkey or aramkey in key:
                found = True
                break
    if not found:
        not_on_site.append(a)

print(f"  共 {len(not_on_site)} 个活跃海克斯不在 arammayhem.com")
print(f"  (可能是 arammayhem.com 未收录，或名称差异)")

# 4. Key question: how many of our 195 active are on arammayhem?
on_site = len(our_active) - len(not_on_site)
print(f"\n=== 总结 ===")
print(f"  我们的活跃: {len(our_active)}")
print(f"  在 arammayhem.com: {on_site} ({on_site*100//len(our_active)}%)")
print(f"  不在 arammayhem.com: {len(not_on_site)} ({len(not_on_site)*100//len(our_active)}%)")
print(f"  我们的已移除: {len(removed)}")
print(f"  arammayhem.com 活跃: {len(aram_set)}")

# 5. Check: the 81 "active but not on site" — are they from blitz.gg?
print(f"\n=== 不在arammayhem的活跃海克斯来源 ===")
src_count = {}
for a in not_on_site:
    src = a.get('source', {})
    if isinstance(src, dict):
        stype = src.get('type', 'unknown')
    else:
        stype = str(src) if src else 'unknown'
    src_count[stype] = src_count.get(stype, 0) + 1
for s, c in sorted(src_count.items(), key=lambda x: -x[1]):
    print(f"  {s}: {c}")
