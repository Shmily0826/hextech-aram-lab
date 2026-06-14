#!/usr/bin/env python3
"""
Generate augment_wiki_quality_todo.json - an augment data quality improvement plan.

Reads data/augments.json and identifies augments with missing data
(effect="", patch_added="", localization_status="missing_zh"), then
creates entries with AI-suggested Chinese translations.
"""

import json
import os

# Paths
BASE_DIR = r"D:\CODE\project\aram-insight"
AUGMENTS_PATH = os.path.join(BASE_DIR, "data", "augments.json")
OUTPUT_DIR = os.path.join(BASE_DIR, "pipeline", "output")
OUTPUT_PATH = os.path.join(OUTPUT_DIR, "augment_wiki_quality_todo.json")

# AI-suggested translations: { augment_id: (suggested_zh_name, suggested_effect_zh, confidence) }
# Based on English name + effect meaning. All marked as needs_human_review=True.
AI_TRANSLATIONS = {
    "adamant": (
        "坚不可摧",
        "定身或禁锢敌方英雄时，获得10点额外护甲和魔法抗性，持续10秒，最多叠加10次，共100点额外双抗，后续触发时刷新（每次施法5秒冷却）。",
        "medium"
    ),
    "blunt_force": (
        "钝击",
        "攻击力提升20%。",
        "medium"
    ),
    "deft": (
        "灵巧",
        "获得60%额外攻击速度。",
        "medium"
    ),
    "erosion": (
        "侵蚀",
        "每次对敌人造成伤害时，使其护甲和魔法抗性降低1.5%，持续4秒，最多叠加20次，共降低30%双抗。",
        "medium"
    ),
    "first_aid_kit": (
        "急救包",
        "获得20%治疗与护盾强度。",
        "medium"
    ),
    "goredrink": (
        "嗜血",
        "获得15%全能吸血。",
        "medium"
    ),
    "homeguard": (
        "家园卫士",
        "获得100%额外移动速度。受到英雄伤害后此加成失效6秒。",
        "medium"
    ),
    "guilty_pleasure": (
        "罪恶快感",
        "定身或禁锢敌方英雄时，为你治疗30至250点生命值（每次施法5秒冷却）。",
        "medium"
    ),
    "back_to_basics": (
        "回归本源",
        "你的基础技能伤害提升35%，获得70点技能急速和35%来自所有来源的治疗与护盾增强，但你的终极技能将被永久锁定。",
        "medium"
    ),
    "biggest_snowball_ever": (
        "史上最大雪球",
        "将你的标记升级为一个巨大的雪球，增大命中半径并可以穿过非英雄单位。雪球命中目标后爆炸，对附近所有敌人造成魔法伤害（+100%额外攻击力）（+60%法术强度），击飞0.75秒并减速20%持续2秒。此外，你的标记冷却时间缩减相当于100点技能急速。如果未装备标记，系统将提示你用标记替换一个召唤师技能。被雪球命中的非英雄单位会被眩晕1.25秒。",
        "low"
    ),
    "circle_of_death": (
        "死亡之环",
        "你的治疗和健康回复效果会使你对1000码内最近的敌方英雄造成该数值70%的魔法伤害。",
        "medium"
    ),
    "get_excited": (
        "兴奋起来",
        "参与击杀英雄后，获得攻击速度和15%总攻击速度，持续4秒。",
        "medium"
    ),
    "goliath": (
        "巨人",
        "获得35%额外生命值、15%自适应之力和50%体型增大。",
        "medium"
    ),
    "growth_spurt": (
        "急速生长",
        "将一个召唤师技能替换为急速生长。",
        "low"
    ),
    "bread_and_butter": (
        "看家本领",
        "你的英雄第一个基础技能（Q）获得100点技能急速。",
        "medium"
    ),
    "fan_the_hammer": (
        "扇形锤击",
        "对攻击范围内的敌方英雄进行普攻时，在每个十字方向上的下一次普攻额外发射5发鞭炮，每发造成物理伤害（+14%额外攻击力），每个方向5秒冷却。鞭炮伤害随飞行距离增加。每发鞭炮可以暴击并附带20%攻击特效。",
        "low"
    ),
    "celestial_body": (
        "星界之躯",
        "获得1500点额外生命值，但你的伤害输出降低10%。",
        "medium"
    ),
    "cerberus": (
        "地狱三头犬",
        "获得丛刃和强攻两个基石符文。",
        "medium"
    ),
    "dashing": (
        "冲刺",
        "拥有冲刺或闪现效果的技能获得175点技能急速。",
        "medium"
    ),
    "dive_bomber": (
        "俯冲轰炸机",
        "死亡时爆炸，对500码内的敌人造成相当于目标最大生命值20%的真实伤害。",
        "medium"
    ),
    "dropkick": (
        "飞身踢",
        "你的普攻和技能对低于一定生命值百分比（+每1000额外生命值增加2%）的敌方英雄执行，使其尸体沿直线飞出。尸体撞击敌方英雄或地形后爆炸，对附近敌人造成魔法伤害（+100%额外护甲）（+100%额外魔抗）。成功执行后为你恢复生命值（+25%额外生命值）。执行也可由爆炸触发且无视护盾。",
        "low"
    ),
    "executioner": (
        "刽子手",
        "对生命值低于最大生命值30%的敌人造成10%额外伤害。参与击杀英雄后重置所有基础技能的冷却时间。",
        "medium"
    ),
    "don_t_blink": (
        "别眨眼",
        "你的移动速度每比目标高10点，造成的伤害提升1%。",
        "medium"
    ),
    "can_t_touch_this": (
        "碰不到我",
        "施放终极技能后获得2秒无敌效果（8秒冷却）。",
        "medium"
    ),
}


def main():
    # Load augments data
    with open(AUGMENTS_PATH, "r", encoding="utf-8") as f:
        augments = json.load(f)

    # Filter augments with missing data
    todo_entries = []

    for aug in augments:
        effect = aug.get("effect", "")
        patch_added = aug.get("patch_added", "")
        localization_status = aug.get("localization_status", "")

        # Check if any of the missing data conditions are met
        has_missing = (
            effect == ""
            or patch_added == ""
            or localization_status == "missing_zh"
        )

        if not has_missing:
            continue

        aug_id = aug["id"]
        name_en = aug.get("name_en", aug.get("name", ""))
        current_name = aug.get("name", name_en)
        tier = aug.get("tier", "")
        effect_en = aug.get("effect_en", "")
        current_effect = aug.get("effect", "")
        source_url = aug.get("source", {}).get("url", "")

        # Get AI suggestion if available
        if aug_id in AI_TRANSLATIONS:
            suggested_zh_name, suggested_effect_zh, confidence = AI_TRANSLATIONS[aug_id]
        else:
            # Fallback: use English name as suggested name, mark low confidence
            suggested_zh_name = name_en
            suggested_effect_zh = f"[待翻译] {effect_en}"
            confidence = "low"

        # Determine missing fields for the entry
        missing_fields = []
        if effect == "":
            missing_fields.append("effect")
        if patch_added == "":
            missing_fields.append("patch_added")
        if localization_status == "missing_zh":
            missing_fields.append("localization_status")

        entry = {
            "id": aug_id,
            "name_en": name_en,
            "current_name": current_name,
            "tier": tier,
            "effect_en": effect_en,
            "current_effect": current_effect,
            "suggested_zh_name": suggested_zh_name,
            "suggested_effect_zh": suggested_effect_zh,
            "source_url": source_url,
            "confidence": confidence,
            "needs_human_review": True,
            "missing_fields": missing_fields,
        }

        todo_entries.append(entry)

    # Ensure output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Write output
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(todo_entries, f, ensure_ascii=False, indent=2)

    print(f"Generated {len(todo_entries)} entries in {OUTPUT_PATH}")
    for e in todo_entries:
        print(f"  [{e['tier']:>10}] {e['id']:30} -> {e['suggested_zh_name']}  (confidence: {e['confidence']}, missing: {e['missing_fields']})")


if __name__ == "__main__":
    main()
