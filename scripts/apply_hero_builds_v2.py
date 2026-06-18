"""
将抓取的出装和技巧数据合并到 champions.json (v2)
修复英文名格式不匹配的映射问题
"""
import json, os, shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "champions.json")
BUILDS = os.path.join(ROOT, "pipeline", "output", "hero_builds_tips.json")
OUT_DIR = os.path.join(ROOT, "pipeline", "output")

# 手动修正: arammayhem slug -> championKeys 中的英文 key
SLUG_TO_KEY = {
    "drmundo": "DrMundo",
    "xinzhao": "XinZhao",
    "aurelionsol": "AurelionSol",
    "missfortune": "MissFortune",
    "twistedfate": "TwistedFate",
    "masteryi": "MasterYi",
    "tahmkench": "TahmKench",
    "kaisa": "Kaisa",
    "velkoz": "Velkoz",
    "jarvaniv": "JarvanIV",
    "chogath": "Chogath",
    "kogmaw": "KogMaw",
    "renata": "Renata",
    "monkeyking": "MonkeyKing",
    "khazix": "Khazix",
    "leesin": "LeeSin",
    "nunu": "Nunu",   # Nunu -> Nunu (same in both)
    "belveth": "Belveth",
    "reksai": "RekSai",
    "ksante": "KSante",
}

# 备份
bak = os.path.join(OUT_DIR, "champions_backup_builds.json")
shutil.copy2(DATA, bak)
print(f"[backup] {DATA} -> {bak}")

# 加载
with open(DATA, "r", encoding="utf-8") as f:
    champ_data = json.load(f)

with open(BUILDS, "r", encoding="utf-8") as f:
    builds = json.load(f)

ck = champ_data["championKeys"]  # {cn_name: en_key}

# en_key -> cn_name
en_to_cn = {v: k for k, v in ck.items()}
# lowercase en_key -> cn_name
en_lower_to_cn = {v.lower(): k for k, v in ck.items()}

# Build slug -> cn_name mapping
build_by_cn = {}
for b in builds:
    slug = b["slug"]
    
    # 1. Try manual mapping
    en_key = SLUG_TO_KEY.get(slug)
    if en_key and en_key in en_to_cn:
        cn = en_to_cn[en_key]
        build_by_cn[cn] = b
        continue
    
    # 2. Try slug as lowercase en_key
    cn = en_lower_to_cn.get(slug)
    if cn:
        build_by_cn[cn] = b
        continue
    
    # 3. Try partial match
    found = False
    for ek, cn_name in en_to_cn.items():
        if ek.lower().replace(" ", "") == slug.replace(" ", ""):
            build_by_cn[cn_name] = b
            found = True
            break
    
    if not found:
        print(f"  [warn] 无法匹配 slug={slug}")

print(f"[match] 匹配到 {len(build_by_cn)}/{len(champ_data['champions'])} 位英雄")

# 合并
updated = 0
no_match = []
for c in champ_data["champions"]:
    name = c["name"]
    b = build_by_cn.get(name)
    if not b:
        no_match.append(name)
        continue

    # Build string
    if b.get("build"):
        c["build"] = b["build"]
    
    # Tips - generate from tier + stats + core build
    tips_parts = []
    tier = c.get("tier", "unknown")
    wr = c.get("wr")
    pr = c.get("pr")
    tier_cn = {"S": "S级(顶尖)", "A": "A级(强势)", "B": "B级(平衡)", "C": "C级(偏弱)", "D": "D级(弱势)"}.get(tier, "")
    
    if tier_cn and wr:
        tips_parts.append(f"当前版本{tier_cn}英雄，胜率{wr}%，选取率{pr}%。")
    
    cores = b.get("core_builds", [])
    if cores:
        top = cores[0]
        tips_parts.append(f"核心出装: {top['items']}，胜率{top['wr']}%。")
    
    if b.get("skill_order"):
        skill = b["skill_order"].split("(")[0].strip()
        tips_parts.append(f"主升{skill}。")
    
    c["tips"] = " ".join(tips_parts) if tips_parts else ""
    
    if c["build"] or c["tips"]:
        updated += 1

# 保存
with open(DATA, "w", encoding="utf-8") as f:
    json.dump(champ_data, f, ensure_ascii=False, indent=2)

print(f"[done] 已更新 {updated}/{len(champ_data['champions'])} 位英雄")
if no_match:
    print(f"[warn] 未匹配 ({len(no_match)}): {', '.join(no_match)}")

# 验证
with_build = sum(1 for c in champ_data["champions"] if c.get("build"))
with_tips = sum(1 for c in champ_data["champions"] if c.get("tips"))
print(f"[verify] 有出装: {with_build}, 有技巧: {with_tips}")

# 样例
print("\n=== 样例 ===")
for c in champ_data["champions"]:
    if c["name"] in ("布兰德", "吉格斯", "卡莎", "亚索", "齐天大圣", "祖安狂人", "赏金猎人"):
        print(f"\n{c['name']}:")
        print(f"  build: {c.get('build', '')[:160]}")
        print(f"  tips:  {c.get('tips', '')[:160]}")
