import json
ck = json.load(open('data/champions.json','r',encoding='utf-8'))['championKeys']
builds = json.load(open('pipeline/output/hero_builds_tips.json','r',encoding='utf-8'))
en_to_cn = {v.lower(): k for k, v in ck.items()}

# Check which slugs don't match
for b in builds:
    slug = b['slug']
    name_cn = b.get('name_cn', '?')
    if slug not in en_to_cn:
        matches = [k for k in en_to_cn if k.startswith(slug[:4])]
        print(f"  slug={slug}  name_cn={name_cn}  close_matches={matches}")
    
# Also check by name_cn
cn_names = {c for c in [b.get('name_cn','') for b in builds] if c}
champ_names = set(ck.keys())
missing = cn_names - champ_names
extra = champ_names - cn_names
print(f"\nbuilds has {len(cn_names)} cn_names, champions has {len(champ_names)}")
print(f"In builds but not in champions: {missing}")
print(f"In champions but not in builds: {list(extra)[:10]}")
