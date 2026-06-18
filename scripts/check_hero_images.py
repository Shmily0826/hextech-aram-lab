"""检查哪些英雄的 ddragon 头像无法加载"""
import json, urllib.request, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "champions.json")

with open(DATA, "r", encoding="utf-8") as f:
    data = json.load(f)

ck = data["championKeys"]
PATCH = "15.12.1"
BASE = f"https://ddragon.leagueoflegends.com/cdn/{PATCH}/img/champion"

failed = []
ok = 0

for cn_name, en_key in ck.items():
    url = f"{BASE}/{en_key}.png"
    try:
        req = urllib.request.Request(url, method="HEAD")
        req.add_header("User-Agent", "Mozilla/5.0")
        with urllib.request.urlopen(req, timeout=5) as resp:
            if resp.status == 200:
                ok += 1
            else:
                failed.append((cn_name, en_key, resp.status))
    except Exception as e:
        failed.append((cn_name, en_key, str(e)[:60]))

print(f"[结果] OK: {ok}, FAILED: {len(failed)}")
for cn, en, err in failed:
    print(f"  {cn} ({en}): {err}")
