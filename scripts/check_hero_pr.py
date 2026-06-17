import json
with open("data/champions.json","r",encoding="utf-8") as f:
    d = json.load(f)
heroes = d.get("champions", [])
total = len(heroes)
has_wr = sum(1 for h in heroes if h.get("wr") is not None)
has_pr = sum(1 for h in heroes if h.get("pr") is not None)
has_pick = sum(1 for h in heroes if h.get("pick_rate") is not None)
print(f"Total heroes: {total}")
print(f"Has wr (win rate): {has_wr}")
print(f"Has pr (pick rate): {has_pr}")
print(f"Has pick_rate: {has_pick}")
for h in heroes[:5]:
    nm = h.get("name","?")
    wr = h.get("wr")
    pr = h.get("pr")
    pk = h.get("pick_rate")
    print(f"  {nm}: wr={wr}, pr={pr}, pick_rate={pk}")
# Show all keys of first hero
if heroes:
    print(f"\nFirst hero keys: {list(heroes[0].keys())}")
