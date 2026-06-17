import json
with open("data/champions.json","r",encoding="utf-8") as f:
    d = json.load(f)
heroes = d.get("champions", [])
has_pr = sum(1 for h in heroes if h.get("pr") is not None)
has_wr = sum(1 for h in heroes if h.get("wr") is not None)
print(f"Total: {len(heroes)}, WR: {has_wr}, PR: {has_pr}")
for h in heroes[:8]:
    nm = h.get("name","?")
    wr = h.get("wr")
    pr = h.get("pr")
    print(f"  {nm}: WR={wr}%, PR={pr}%")
