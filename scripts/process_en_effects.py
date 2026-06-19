"""
process_en_effects.py
Process scraped English effects, classify them, clean BBCode,
and output candidates for augments.json update.
"""
import json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

with open(os.path.join(ROOT, 'pipeline', 'output', 'en_effects_scrape.json'), encoding='utf-8') as f:
    scrape = json.load(f)

with open(os.path.join(ROOT, 'data', 'augments.json'), encoding='utf-8') as f:
    augs = json.load(f)

# Boilerplate patterns that indicate non-effect text
BOILERPLATE = [
    r'keep exploring .+ through champions',
    r'last updated\s*·',
]

# Strategy tip indicators (not actual effect descriptions)
STRATEGY_INDICATORS = [
    r'build around',
    r'core items?:',
    r'pair with',
    r'pair\s+with',
    r'use .+ to',
    r'stack .+ synerg',
    r'forge:',
    r'exploits? a special',
    r'converts? .+ to .+ without',
    r'massive(ly)? boosts',
    r'perfect for',
    r'insane damage',
    r'huge sustain',
    r'melts? squish',
    r'triple-mixed',
    r'huge ms and',
    r'endless tank',
    r'spicy enough',
    r'chili oil build',
    r'back to basics',
]

def clean_bbcode(text):
    """Remove BBCode tags like [b], [/b], [i], [/i]"""
    text = re.sub(r'\[/?[bi]\]', '', text)
    # Fix encoding artifacts
    text = text.replace('\xc3\xa2\xc2\xc2', '—')
    text = text.replace('â', '—')
    # Remove HTML comments
    text = re.sub(r'<!--.*?-->', '', text)
    return text.strip()

def is_boilerplate(text):
    lower = text.lower()
    for pat in BOILERPLATE:
        if re.search(pat, lower):
            return True
    return False

def is_strategy_tip(text):
    lower = text.lower()
    for pat in STRATEGY_INDICATORS:
        if re.search(pat, lower):
            return True
    return False

def is_real_effect(text):
    """Heuristic: real effects describe game mechanics directly"""
    if is_boilerplate(text):
        return False
    if len(text) < 15:
        return False
    # Real effects typically start with action verbs or describe grants
    lower = text.lower()
    effect_starts = [
        'your ', 'grants ', 'gain ', 'replaces ', 'replace ',
        'upon ', 'whenever ', 'automatically', 'hitting ',
        'critical strikes', 'you summon', 'upgrades both',
    ]
    for start in effect_starts:
        if lower.startswith(start):
            return True
    return False

# Classify each result
real_effects = []
strategy_tips = []
boilerplate = []

for r in scrape['results']:
    text = r.get('effect_en', '')
    cleaned = clean_bbcode(text)
    
    if is_boilerplate(cleaned):
        boilerplate.append({**r, 'effect_en_cleaned': cleaned, 'reason': 'boilerplate'})
    elif is_real_effect(cleaned):
        real_effects.append({**r, 'effect_en_cleaned': cleaned})
    elif is_strategy_tip(cleaned):
        strategy_tips.append({**r, 'effect_en_cleaned': cleaned, 'reason': 'strategy_tip'})
    else:
        # Ambiguous - check more carefully
        # If it describes any game mechanic at all, treat as partial effect
        if any(kw in cleaned.lower() for kw in ['damage', 'cooldown', 'second', 'radius', 'health', '%']):
            strategy_tips.append({**r, 'effect_en_cleaned': cleaned, 'reason': 'mixed_strategy'})
        else:
            boilerplate.append({**r, 'effect_en_cleaned': cleaned, 'reason': 'unclear'})

print(f"=== 分类结果 ===")
print(f"  真实效果描述: {len(real_effects)} 个")
print(f"  攻略/策略文本: {len(strategy_tips)} 个")
print(f"  样板/无效文本: {len(boilerplate)} 个")

print(f"\n--- 真实效果 ({len(real_effects)}) ---")
for e in real_effects:
    print(f"  {e['name']} ({e['name_en']})")
    print(f"    {e['effect_en_cleaned'][:100]}...")

print(f"\n--- 攻略文本 ({len(strategy_tips)}) ---")
for e in strategy_tips:
    print(f"  {e['name']} ({e['name_en']}): {e['reason']}")
    print(f"    {e['effect_en_cleaned'][:80]}...")

print(f"\n--- 无效文本 ({len(boilerplate)}) ---")
for e in boilerplate:
    print(f"  {e['name']} ({e['name_en']}): {e['reason']}")

# Output candidates: only real effects
candidates = []
for e in real_effects:
    aug_id = e['id']
    # Find in augments.json
    aug = next((a for a in augs if a.get('id') == aug_id), None)
    if aug:
        candidates.append({
            'id': aug_id,
            'name': e['name'],
            'name_en': e['name_en'],
            'effect_en': e['effect_en_cleaned'],
            'current_effect': aug.get('effect', ''),
            'current_effect_en': aug.get('effect_en', ''),
            'status': aug.get('status', ''),
        })

out_path = os.path.join(ROOT, 'pipeline', 'output', 'en_effects_candidates.json')
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump({
        'description': 'English effect candidates for removed augments - real effect descriptions only',
        'total_scraped': len(scrape['results']),
        'real_effects': len(real_effects),
        'strategy_tips': len(strategy_tips),
        'boilerplate': len(boilerplate),
        'candidates': candidates,
    }, f, ensure_ascii=False, indent=2)

print(f"\n=== 输出候选: {len(candidates)} 个真实效果描述 ===")
print(f"  -> {out_path}")
