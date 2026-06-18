"""Remove null kda field from all champions and localize augment tags."""
import json, shutil

# ===== 1. Remove kda from champions =====
with open("data/champions.json", "r", encoding="utf-8") as f:
    cdata = json.load(f)

kda_removed = 0
for champ in cdata["champions"]:
    if "kda" in champ:
        del champ["kda"]
        kda_removed += 1

with open("data/champions.json", "w", encoding="utf-8") as f:
    json.dump(cdata, f, ensure_ascii=False, indent=None, separators=(",", ":"))
print(f"Removed kda from {kda_removed} champions")

# Also update openHero modal to not show KDA stat
# (handled in index.html edit separately)

# ===== 2. Localize augment tags =====
TAG_MAP = {
    "damage": "伤害",
    "heal": "治疗",
    "healing": "治疗",
    "movement": "机动",
    "speed": "速度",
    "tank": "坦克",
    "economy": "经济",
    "shield": "护盾",
    "attack": "攻击",
    "ability": "技能",
    "utility": "辅助",
    "defense": "防御",
    "sustain": "续航",
    "burst": "爆发",
    "crowd control": "控制",
    "cc": "控制",
    "assassin": "刺客",
    "mage": "法师",
    "marksman": "射手",
    "support": "辅助",
    "fighter": "战士",
    "gold": "金币",
    "health": "生命值",
    "mana": "法力值",
    "cooldown": "冷却",
    "attack speed": "攻速",
    "armor": "护甲",
    "magic resist": "魔抗",
    "lifesteal": "生命偷取",
    "spell vamp": "法术吸血",
    "crit": "暴击",
    "penetration": "穿透",
    "on-hit": "攻击特效",
    "wave clear": "清线",
    "objective": "目标",
    "siege": "推塔",
    "mobility": "机动性",
    "engage": "开团",
    "disengage": "反开",
    "peel": "保护",
    "poke": "消耗",
    "zone": "区域",
    "buff": "增益",
    "debuff": "减益",
    "quest": "任务",
    "unique": "独特",
    "rarity": "稀有",
    "adaptive": "自适应",
    "projectile": "飞弹",
    "attack damage": "攻击力",
    "ability power": "法术强度",
    "haste": "急速",
    "tenacity": "韧性",
    "omnivamp": "全能吸血",
    "execute": "斩杀",
    "revive": "复活",
    "summon": "召唤",
    "pet": "宠物",
    "transform": "变形",
    "empower": "强化",
    "clone": "克隆",
    "stealth": "隐身",
    "vision": "视野",
    "teleport": "传送",
    "knockup": "击飞",
    "knockback": "击退",
    "stun": "眩晕",
    "slow": "减速",
    "root": "禁锢",
    "silence": "沉默",
    "blind": "致盲",
    "fear": "恐惧",
    "charm": "魅惑",
    "taunt": "嘲讽",
    "polymorph": "变形术",
    "invulnerable": "无敌",
    "cleanse": "净化",
    "dash": "冲刺",
    "blink": "闪现",
    "barrier": "屏障",
}

with open("data/augments.json", "r", encoding="utf-8") as f:
    augs = json.load(f)

tag_count = 0
for aug in augs:
    tags = aug.get("tags", [])
    if not tags:
        continue
    new_tags = []
    for tag in tags:
        if isinstance(tag, str):
            lower_tag = tag.lower().strip()
            if lower_tag in TAG_MAP:
                new_tags.append(TAG_MAP[lower_tag])
                tag_count += 1
            else:
                new_tags.append(tag)  # Keep original if no mapping
        else:
            new_tags.append(tag)
    aug["tags"] = new_tags

with open("data/augments.json", "w", encoding="utf-8") as f:
    json.dump(augs, f, ensure_ascii=False, indent=None, separators=(",", ":"))
print(f"Localized {tag_count} augment tags")

# Check remaining English tags
remaining = set()
for aug in augs:
    for tag in aug.get("tags", []):
        if isinstance(tag, str) and any(c.isascii() and c.isalpha() for c in tag):
            remaining.add(tag)
if remaining:
    print(f"Remaining English tags: {sorted(remaining)}")
else:
    print("All tags localized!")
