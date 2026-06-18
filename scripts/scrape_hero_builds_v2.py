"""
从 arammayhem.com 精准抓取英雄的出装建议和技巧
第二版：基于页面文本结构解析，而非 HTML regex
"""
import json, os, re, time, html as htmlmod
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SLUGS_FILE = os.path.join(ROOT, "pipeline", "output", "hero_pick_rates.json")
OUT_DIR = os.path.join(ROOT, "pipeline", "output")
OUT_FILE = os.path.join(OUT_DIR, "hero_builds_tips.json")

os.makedirs(OUT_DIR, exist_ok=True)

with open(SLUGS_FILE, "r", encoding="utf-8") as f:
    heroes = json.load(f)

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"


def fetch_page(slug):
    url = f"https://arammayhem.com/build/{slug}/"
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        return None


def strip_tags(s):
    """Remove all HTML tags and decode entities"""
    s = re.sub(r'<script[^>]*>.*?</script>', ' ', s, flags=re.DOTALL | re.IGNORECASE)
    s = re.sub(r'<style[^>]*>.*?</style>', ' ', s, flags=re.DOTALL | re.IGNORECASE)
    s = re.sub(r'<[^>]+>', ' ', s)
    s = htmlmod.unescape(s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s


def extract_json_ld(raw_html):
    """Extract JSON-LD description (contains tier tip)"""
    m = re.search(r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', raw_html, re.DOTALL)
    if m:
        try:
            data = json.loads(m.group(1))
            return data.get("description", "")
        except Exception:
            pass
    return ""


def parse_build_text(text):
    """Parse the structured text from the page to extract build sections"""
    result = {"skill_order": "", "start_items": [], "boots": [], "core_builds": [], "tips": ""}

    # Find "Skill Priority" section
    skill_m = re.search(r'Skill Priority.*?(Q[>WER]+|E[>QWR]+|W[>QER]+)\s*Pick Rate:\s*(\d+\.?\d*)%\s*Win Rate:\s*(\d+\.?\d*)%', text)
    if skill_m:
        result["skill_order"] = f"{skill_m.group(1)} ({skill_m.group(2)}% 选取)"

    # Find "Starting Items" section — items listed until "Boots"
    start_m = re.search(r'Starting Items\s+(.*?)\s+(?:Boots|Core)', text)
    if start_m:
        block = start_m.group(1)
        items = re.findall(r'([A-Z][a-zA-Z\' ]{2,30}?)\s+Pick Rate', block)
        result["start_items"] = items[:4]

    # Find "Boots" section
    boots_m = re.search(r'Boots\s+(.*?)\s+(?:Core Builds|Late-Game|Best Augments)', text)
    if boots_m:
        block = boots_m.group(1)
        items = re.findall(r'([A-Z][a-zA-Z\' ]{2,35}?)\s+Pick Rate', block)
        result["boots"] = [i.strip() for i in items if i.strip()][:2]

    # Find "Core Builds" section — top 2 builds
    core_m = re.search(r'Core Builds\s+(.*?)\s+(?:Late-Game|Best Augments)', text)
    if core_m:
        block = core_m.group(1)
        builds = re.findall(r'([A-Z][a-zA-Z\' ]+(?:\s+[A-Z][a-zA-Z\' ]+)*)\s+Pick Rate:\s*(\d+\.?\d*)%\s*Win Rate:\s*(\d+\.?\d*)%', block)
        result["core_builds"] = [{"items": b[0].strip(), "pr": b[1], "wr": b[2]} for b in builds[:3]]

    return result


def format_build(parsed, description):
    """Format parsed build data into a readable Chinese string"""
    parts = []
    if parsed["skill_order"]:
        parts.append(f"技能: {parsed['skill_order']}")
    if parsed["start_items"]:
        parts.append(f"起始: {'、'.join(parsed['start_items'])}")
    if parsed["boots"]:
        parts.append(f"鞋子: {'、'.join(parsed['boots'])}")
    if parsed["core_builds"]:
        top = parsed["core_builds"][0]
        parts.append(f"核心: {top['items']} ({top['wr']}% 胜率)")
    return ' | '.join(parts)


def format_tips(description, parsed):
    """Generate tips from page description and build data"""
    tips_parts = []
    if description:
        # Extract tier info from description
        tier_m = re.search(r'(\w+) is (\w+) tier.*?(\d+\.?\d*)%?\s*win rate', description)
        if tier_m:
            tips_parts.append(f"{tier_m.group(1)} 在 ARAM Mayhem 中为 {tier_m.group(2)} 级英雄，胜率 {tier_m.group(3)}%。")
        else:
            tips_parts.append(description.rstrip('.'))
    return ' '.join(tips_parts)


def process_hero(hero):
    slug = hero["slug"]
    name_cn = hero.get("name_cn", hero["name"])

    raw = fetch_page(slug)
    if raw is None:
        return {"slug": slug, "name_cn": name_cn, "status": "error", "build": "", "tips": ""}

    # Extract JSON-LD description for tips
    description = extract_json_ld(raw)

    # Strip HTML to get plain text
    text = strip_tags(raw)

    # Parse build sections
    parsed = parse_build_text(text)

    # Format outputs
    build_str = format_build(parsed, description)
    tips_str = format_tips(description, parsed)

    return {
        "slug": slug,
        "name_cn": name_cn,
        "name_en": hero["name"],
        "status": "ok",
        "build": build_str,
        "tips": tips_str,
        "skill_order": parsed["skill_order"],
        "start_items": parsed["start_items"],
        "boots": parsed["boots"],
        "core_builds": parsed["core_builds"],
    }


def main():
    print(f"[scrape] 开始抓取 {len(heroes)} 位英雄的出装和技巧...")
    results = []
    done = 0

    with ThreadPoolExecutor(max_workers=6) as pool:
        futures = {pool.submit(process_hero, h): h for h in heroes}
        for future in as_completed(futures):
            r = future.result()
            results.append(r)
            done += 1
            if done % 20 == 0:
                ok = sum(1 for x in results if x.get("build"))
                print(f"  [{done}/{len(heroes)}] 有出装: {ok}")
            time.sleep(0.3)

    # Sort by slug rank
    slug_rank = {h["slug"]: h.get("rank", 999) for h in heroes}
    results.sort(key=lambda x: slug_rank.get(x["slug"], 999))

    # Stats
    ok = sum(1 for r in results if r["status"] == "ok")
    with_build = sum(1 for r in results if r.get("build"))
    with_tips = sum(1 for r in results if r.get("tips"))

    print(f"\n[完成] 成功: {ok}/{len(results)}")
    print(f"[完成] 有出装: {with_build}, 有技巧: {with_tips}")

    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"[saved] {OUT_FILE}")

    # Samples
    print("\n=== 样例 (前5) ===")
    for r in results[:5]:
        print(f"\n{r['name_cn']} ({r['slug']}):")
        print(f"  build: {r.get('build', '')[:120]}")
        print(f"  tips: {r.get('tips', '')[:120]}")

    # Check empty ones
    empty = [r for r in results if not r.get("build")]
    if empty:
        print(f"\n=== 缺少出装 ({len(empty)}) ===")
        for r in empty[:10]:
            print(f"  {r['name_cn']} ({r['slug']}): status={r['status']}")


if __name__ == "__main__":
    main()
