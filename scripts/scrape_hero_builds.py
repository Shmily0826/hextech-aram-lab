"""
从 arammayhem.com 抓取所有英雄的出装建议和技巧
输出到 pipeline/output/hero_builds_tips.json
"""
import json, os, re, time, urllib.request, html
from concurrent.futures import ThreadPoolExecutor, as_completed

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SLUGS_FILE = os.path.join(ROOT, "pipeline", "output", "hero_pick_rates.json")
OUT_DIR = os.path.join(ROOT, "pipeline", "output")
OUT_FILE = os.path.join(OUT_DIR, "hero_builds_tips.json")

os.makedirs(OUT_DIR, exist_ok=True)

with open(SLUGS_FILE, "r", encoding="utf-8") as f:
    heroes = json.load(f)

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}


def fetch_page(slug):
    """Fetch a single champion build page"""
    url = f"https://arammayhem.com/build/{slug}/"
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        return None


def extract_text(html_str, pattern, group=1):
    """Extract text from HTML using regex"""
    m = re.search(pattern, html_str, re.IGNORECASE | re.DOTALL)
    if m:
        return html.unescape(m.group(group)).strip()
    return ""


def parse_champion_page(html_str, slug):
    """Parse build and tips data from champion page HTML"""
    result = {"slug": slug, "build_parts": [], "tips": "", "augments": []}

    if not html_str:
        return result

    # Extract skill order (e.g., "Q>E>W")
    skill_match = re.search(r'(Skill[^<]*?|Ability\s+Order[^<]*?)([QWER]\s*[>›]\s*[QWER]\s*[>›]\s*[QWER])', html_str)
    if skill_match:
        result["skill_order"] = skill_match.group(2).replace(" ", "")

    # Extract starting items
    start_items = re.findall(r'(?:Starting|Start)[^<]*?(?:items?|Items?)', html_str, re.IGNORECASE)

    # Look for item names in the page - they appear in specific patterns
    # Items are typically in spans/divs with specific classes
    items = []

    # Extract items from structured sections
    # Look for common item sections: "Core Build", "Starting Items", "Boots"
    sections = re.findall(r'<(?:h[2-4]|div[^>]*class="[^"]*(?:section|build|item)[^"]*")[^>]*>(.*?)</(?:h[2-4]|div)>', html_str, re.IGNORECASE | re.DOTALL)

    # More targeted: look for specific item patterns in the page text
    # Items on arammayhem are usually listed with their names
    page_text = re.sub(r'<[^>]+>', ' ', html_str)
    page_text = re.sub(r'\s+', ' ', page_text)

    # Extract build description - usually contains item names and order
    # Pattern: "Start X, Y. Core A, B, C."
    build_text = ""

    # Look for the build/build guide section
    build_patterns = [
        r'(?:Starting Items?|Start)[:\s]*([^<\n]+)',
        r'(?:Core(?:\s+Build)?|Full Build)[:\s]*([^<\n]+)',
        r'(?:Boots?)[:\s]*([^<\n]+)',
    ]

    for pat in build_patterns:
        m = re.search(pat, html_str, re.IGNORECASE)
        if m:
            result["build_parts"].append(m.group(1).strip())

    # Extract tips/advice
    tip_patterns = [
        r'(?:Tips?|Strategy|Advice|Pro\s*Tip|Gameplay)[:\s]*["""]?([^"""\n<]+(?:<[^>]+>[^"""\n<]+)*)',
        r'(?:arammayhem\.com\s*(?:says|recommends))[:\s]*([^<]+)',
    ]

    for pat in tip_patterns:
        m = re.search(pat, html_str, re.IGNORECASE)
        if m:
            tip = re.sub(r'<[^>]+>', '', m.group(1)).strip()
            if len(tip) > 10:
                result["tips"] = tip
                break

    # Extract best augments with win rates
    aug_matches = re.findall(r'((?:augment|perk)[^<]*?(?:[\w\s\'-]{3,30}))[^<]*?(\d+\.?\d*)%', html_str, re.IGNORECASE)
    for aug_name, aug_wr in aug_matches:
        aug_name = aug_name.strip()
        if len(aug_name) > 3 and aug_name.lower() not in ('pick rate', 'win rate'):
            result["augments"].append({"name": aug_name, "wr": float(aug_wr)})

    return result


def process_hero(hero):
    """Process a single hero: fetch + parse"""
    slug = hero["slug"]
    name_cn = hero.get("name_cn", hero["name"])

    html_str = fetch_page(slug)
    if html_str is None:
        return {"slug": slug, "name_cn": name_cn, "status": "error", "build": "", "tips": ""}

    data = parse_champion_page(html_str, slug)

    # Build a readable build string
    build_str = ""
    if data["build_parts"]:
        build_str = " | ".join(data["build_parts"])
    if data.get("skill_order"):
        build_str = f"技能顺序: {data['skill_order']}" + (f" | {build_str}" if build_str else "")

    return {
        "slug": slug,
        "name_cn": name_cn,
        "name_en": hero["name"],
        "status": "ok",
        "build": build_str,
        "tips": data["tips"],
        "skill_order": data.get("skill_order", ""),
        "build_parts": data["build_parts"],
        "augments": data["augments"],
        "html_len": len(html_str),
    }


def main():
    print(f"[scrape] 开始抓取 {len(heroes)} 位英雄的出装和技巧...")
    results = []
    done = 0

    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = {pool.submit(process_hero, h): h for h in heroes}
        for future in as_completed(futures):
            result = future.result()
            results.append(result)
            done += 1
            if done % 20 == 0:
                print(f"  [{done}/{len(heroes)}] ...")
            time.sleep(0.2)  # rate limiting

    # Sort by rank
    slug_rank = {h["slug"]: h.get("rank", 999) for h in heroes}
    results.sort(key=lambda x: slug_rank.get(x["slug"], 999))

    # Summary
    ok = sum(1 for r in results if r["status"] == "ok")
    with_build = sum(1 for r in results if r.get("build"))
    with_tips = sum(1 for r in results if r.get("tips"))

    print(f"\n[完成] 成功: {ok}/{len(results)}")
    print(f"[完成] 有出装: {with_build}, 有技巧: {with_tips}")

    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"[saved] {OUT_FILE}")

    # Show samples
    print("\n=== 样例 ===")
    for r in results[:5]:
        print(f"\n{r['name_cn']} ({r['slug']}):")
        if r.get("build"):
            print(f"  build: {r['build'][:100]}")
        if r.get("tips"):
            print(f"  tips: {r['tips'][:100]}")
        if not r.get("build") and not r.get("tips"):
            print(f"  [empty] html_len={r.get('html_len',0)}")


if __name__ == "__main__":
    main()
