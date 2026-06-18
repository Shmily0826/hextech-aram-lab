import json
ck = json.load(open('data/champions.json','r',encoding='utf-8'))['championKeys']
builds = json.load(open('pipeline/output/hero_builds_tips.json','r',encoding='utf-8'))
slugs = json.load(open('pipeline/output/hero_pick_rates.json','r',encoding='utf-8'))

# Build slug -> en_key mapping from hero_pick_rates (slug + name fields)
slug_to_en = {}
for s in slugs:
    slug_to_en[s['slug']] = s['name']  # e.g., "brand" -> "Brand"

# en_key (from championKeys) -> cn_name
en_to_cn = {}
for cn, en in ck.items():
    en_to_cn[en.lower()] = cn

# Now build slug -> cn_name
slug_to_cn = {}
for slug, en_name in slug_to_en.items():
    cn = en_to_cn.get(en_name.lower(), "")
    if cn:
        slug_to_cn[slug] = cn

# Check coverage
print(f"slug_to_cn: {len(slug_to_cn)}/{len(builds)}")

# Which slugs still don't match?
for b in builds:
    if b['slug'] not in slug_to_cn:
        print(f"  UNMATCHED slug={b['slug']} en_name={slug_to_en.get(b['slug'],'?')}")

# Now check which champion names are covered
matched_cn = set(slug_to_cn.values())
all_cn = set(ck.keys())
print(f"\nChampions matched: {len(matched_cn)}/{len(all_cn)}")
missing = all_cn - matched_cn
if missing:
    print(f"Missing: {missing}")
