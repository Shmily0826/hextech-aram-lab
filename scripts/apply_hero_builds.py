"""
将抓取的出装和技巧数据合并到 champions.json
从页面文本中提取 tier 信息作为 tips
"""
import json, os, shutil, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "champions.json")
BUILDS = os.path.join(ROOT, "pipeline", "output", "hero_builds_tips.json")
OUT_DIR = os.path.join(ROOT, "pipeline", "output")

# 备份
bak = os.path.join(OUT_DIR, "champions_backup_builds.json")
shutil.copy2(DATA, bak)
print(f"[backup] {DATA} -> {bak}")

# 加载
with open(DATA, "r", encoding="utf-8") as f:
    champ_data = json.load(f)

with open(BUILDS, "r", encoding="utf-8") as f:
    builds = json.load(f)

# 建立 slug -> build 映射
# 需要通过 name_cn 或 name_en 关联
# champions.json 里的 championKeys 是 {cn_name: en_key}
# builds 里的 slug 来自 arammayhem.com

ck = champ_data["championKeys"]
# 反向映射: en_key -> cn_name
en_to_cn = {v.lower(): k for k, v in ck.items()}

# 为每个 build 找到对应的 cn name
build_map = {}
for b in builds:
    slug = b["slug"]
    # 尝试直接匹配
    cn = b.get("name_cn", "")
    if not cn:
        cn = en_to_cn.get(slug, "")
    if cn:
        build_map[cn] = b

print(f"[match] 匹配到 {len(build_map)}/{len(champ_data['champions'])} 位英雄")

# 合并
updated = 0
no_match = []
for c in champ_data["champions"]:
    name = c["name"]
    b = build_map.get(name)
    if not b:
        no_match.append(name)
        continue

    # Build string - already good
    if b.get("build"):
        c["build"] = b["build"]
    
    # Tips - generate from tier info + core build
    tips_parts = []
    
    # Extract tier from the page text description
    # The page text usually has: "X is A tier in ARAM: Mayhem patch 26.12 with a 49.94% win rate"
    # We can use the champion's tier and wr from champions.json
    tier = c.get("tier", "unknown")
    wr = c.get("wr")
    pr = c.get("pr")
    tier_cn = {"S": "S级(顶尖)", "A": "A级(强势)", "B": "B级(平衡)", "C": "C级(偏弱)", "D": "D级(弱势)"}.get(tier, "")
    
    if tier_cn and wr:
        tips_parts.append(f"当前版本{tier_cn}英雄，胜率{wr}%，选取率{pr}%。")
    
    # Add core build info
    cores = b.get("core_builds", [])
    if cores:
        top = cores[0]
        tips_parts.append(f"核心出装: {top['items']}，胜率{top['wr']}%。")
    
    # Add skill order
    if b.get("skill_order"):
        tips_parts.append(f"主升{b['skill_order'].split('(')[0].strip()}。")
    
    c["tips"] = " ".join(tips_parts) if tips_parts else ""
    
    if c["build"] or c["tips"]:
        updated += 1

# 保存
with open(DATA, "w", encoding="utf-8") as f:
    json.dump(champ_data, f, ensure_ascii=False, indent=2)

print(f"[done] 已更新 {updated}/{len(champ_data['champions'])} 位英雄")
if no_match:
    print(f"[warn] 未匹配 ({len(no_match)}): {', '.join(no_match[:10])}")

# 验证
with_build = sum(1 for c in champ_data["champions"] if c.get("build"))
with_tips = sum(1 for c in champ_data["champions"] if c.get("tips"))
print(f"[verify] 有出装: {with_build}, 有技巧: {with_tips}")

# 展示几个样例
print("\n=== 样例 ===")
for c in champ_data["champions"]:
    if c["name"] in ("布兰德", "吉格斯", "卡莎", "亚索", "盖伦"):
        print(f"\n{c['name']}:")
        print(f"  build: {c.get('build','')[:150]}")
        print(f"  tips: {c.get('tips','')[:150]}")
