#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
add_chinese_effects.py — 为 20 个 effect 为空的增强添加中文效果描述

读取 data/augments.json 和 pipeline/output/wiki_augments_english.json，
根据预写的中文翻译为指定增强填充 effect / desc 字段，并移除 localization_status。

用法：
    python scripts/add_chinese_effects.py
"""

import io
import json
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Windows 终端 UTF-8 兼容 — 使用 io.TextIOWrapper
# ---------------------------------------------------------------------------
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
else:
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

# ---------------------------------------------------------------------------
# 路径配置
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
DATA_DIR = PROJECT_ROOT / "data"
PIPELINE_OUTPUT = PROJECT_ROOT / "pipeline" / "output"

AUGMENTS_FILE = DATA_DIR / "augments.json"
WIKI_ENGLISH_FILE = PIPELINE_OUTPUT / "wiki_augments_english.json"
BACKUP_FILE = PIPELINE_OUTPUT / "augments_backup_before_effects.json"

# ---------------------------------------------------------------------------
# 预写的中文效果描述（基于游戏机制翻译）
# ---------------------------------------------------------------------------
CHINESE_EFFECTS: dict[str, str] = {
    "blunt_force": "攻击伤害提升20%。",
    "deft": "获得60%额外攻击速度。",
    "erosion": "每次对敌人造成伤害时，降低其护甲和魔抗1.5%，持续4秒，最多叠加20层，总计降低30%双抗。",
    "first_aid_kit": "获得20%治疗和护盾强度。",
    "goredrink": "获得15%全能吸血。",
    "homeguard": "获得100%额外移动速度。受到英雄伤害后该加成消失6秒。",
    "back_to_basics": "基础技能伤害提升35%，获得70技能急速，所有来源的治疗和护盾效果提升35%，但终极技能被永久封印。",
    "biggest_snowball_ever": (
        "将你的标记升级为巨型雪球，体积增大且可穿过非英雄单位。"
        "命中后爆炸造成200-350（+100%额外攻击力）（+60%法术强度）魔法伤害，"
        "击飞0.75秒并减速20%持续2秒。标记冷却缩减相当于100技能急速。"
    ),
    "circle_of_death": "你的治疗和自我恢复会对最近1000码内的敌方英雄造成等值70%的魔法伤害。",
    "get_excited": "击杀或参与击杀后获得100%额外移动速度和15%总攻击速度，持续4秒。",
    "goliath": "获得35%额外生命值、15自适应之力和50%体型增大。",
    "growth_spurt": (
        "替换一个召唤师技能为成长突增。增大自身体型，击飞400码内的敌人1秒。"
        "接下来7秒内获得300（+20%最大生命值）额外生命值和50%体型增大。"
    ),
    "bread_and_butter": "英雄的Q技能获得100技能急速。",
    "fan_the_hammer": (
        "每次对敌方英雄的普攻会在四个方向各发射5枚爆竹，"
        "每枚造成8-51（+14%额外攻击力）物理伤害（每方向5秒冷却）。"
    ),
    "celestial_body": "获得1500额外生命值，但伤害输出降低10%。",
    "dashing": "拥有冲刺或闪烁效果的技能获得175技能急速。",
    "dive_bomber": "死亡时爆炸，对500码内的敌人造成相当于目标20%最大生命值的真实伤害。",
    "dropkick": (
        "普攻和技能可处决生命值低于5%（+3.5%/100基础攻击力）（+2%/1000额外生命值）"
        "最大生命值的敌方英雄，并将其尸体击飞。"
        "尸体撞到敌方英雄或地形时爆炸，对附近敌人造成150-500"
        "（+100%额外护甲）（+100%额外魔抗）魔法伤害。"
    ),
    "don_t_blink": "每比目标多10点移动速度，造成的伤害提升1%。",
    "can_t_touch_this": "施放终极技能后获得2秒无敌（8秒冷却）。",
}


def load_json(filepath: Path) -> object:
    """加载 JSON 文件。"""
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(filepath: Path, data: object) -> None:
    """保存 JSON 文件（UTF-8，中文不转义，缩进 2）。"""
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")  # 尾部换行


def main() -> int:
    print("=" * 60)
    print("  添加中文效果描述 — add_chinese_effects.py")
    print("=" * 60)
    print()

    # -----------------------------------------------------------------------
    # 1. 读取数据
    # -----------------------------------------------------------------------
    print(f"[1/6] 读取 {AUGMENTS_FILE.relative_to(PROJECT_ROOT)} ...")
    augments = load_json(AUGMENTS_FILE)
    assert isinstance(augments, list), "augments.json 顶层应为数组"
    print(f"       共 {len(augments)} 条增强记录。")

    print(f"[2/6] 读取 {WIKI_ENGLISH_FILE.relative_to(PROJECT_ROOT)} ...")
    wiki_en = load_json(WIKI_ENGLISH_FILE)
    assert isinstance(wiki_en, list), "wiki_augments_english.json 顶层应为数组"
    # 构建 name -> description 索引（仅供参考 / 日志）
    wiki_desc_map: dict[str, str] = {}
    for entry in wiki_en:
        if isinstance(entry, dict) and "name" in entry:
            wiki_desc_map[entry["name"]] = entry.get("description", "")
    print(f"       共 {len(wiki_en)} 条 Wiki 英文记录。")

    # -----------------------------------------------------------------------
    # 2. 备份原始文件
    # -----------------------------------------------------------------------
    print(f"[3/6] 备份原始文件至 {BACKUP_FILE.relative_to(PROJECT_ROOT)} ...")
    BACKUP_FILE.parent.mkdir(parents=True, exist_ok=True)
    # 读取原始内容并原样写入备份（保留格式）
    with open(AUGMENTS_FILE, "r", encoding="utf-8") as src:
        raw = src.read()
    with open(BACKUP_FILE, "w", encoding="utf-8") as dst:
        dst.write(raw)
    print("       备份完成。")

    # -----------------------------------------------------------------------
    # 3. 遍历并更新增强
    # -----------------------------------------------------------------------
    print(f"[4/6] 更新 {len(CHINESE_EFFECTS)} 个增强的中文效果描述 ...")
    print()

    updated_count = 0
    skipped_ids: list[str] = []
    not_found_ids: list[str] = []

    # 先统计哪些 id 存在于数据中
    id_to_index: dict[str, int] = {}
    for i, aug in enumerate(augments):
        if isinstance(aug, dict) and "id" in aug:
            id_to_index[aug["id"]] = i

    # 检查所有目标 id 是否存在
    for target_id in CHINESE_EFFECTS:
        if target_id not in id_to_index:
            not_found_ids.append(target_id)

    if not_found_ids:
        print(f"  [警告] 以下 {len(not_found_ids)} 个 id 在 augments.json 中未找到：")
        for nid in not_found_ids:
            print(f"    - {nid}")
        print()

    # 执行更新
    for target_id, chinese_effect in CHINESE_EFFECTS.items():
        if target_id not in id_to_index:
            continue

        idx = id_to_index[target_id]
        aug = augments[idx]
        aug_name = aug.get("name", "?")
        aug_name_en = aug.get("name_en", "?")

        # 查找对应的 Wiki 英文描述（仅供参考日志）
        wiki_desc = wiki_desc_map.get(aug_name_en, "(未找到)")

        old_effect = aug.get("effect", "")
        old_desc = aug.get("desc", "")
        had_localization = "localization_status" in aug

        # 设置新的 effect 和 desc
        aug["effect"] = chinese_effect
        aug["desc"] = chinese_effect

        # 移除 localization_status
        if had_localization:
            del aug["localization_status"]

        augments[idx] = aug
        updated_count += 1

        # 打印变更详情
        print(f"  [{updated_count:2d}] {target_id}")
        print(f"       名称: {aug_name} ({aug_name_en})")
        if old_effect:
            print(f"       旧 effect: {old_effect[:60]}...")
        else:
            print(f"       旧 effect: (空)")
        print(f"       新 effect: {chinese_effect[:60]}{'...' if len(chinese_effect) > 60 else ''}")
        if had_localization:
            print(f"       已移除 localization_status")
        print()

    print(f"  共更新 {updated_count} 条，跳过 {len(skipped_ids)} 条，未找到 {len(not_found_ids)} 条。")
    print()

    # -----------------------------------------------------------------------
    # 4. 写回文件
    # -----------------------------------------------------------------------
    print(f"[5/6] 写回 {AUGMENTS_FILE.relative_to(PROJECT_ROOT)} ...")
    save_json(AUGMENTS_FILE, augments)
    print("       写入完成（ensure_ascii=False, indent=2）。")
    print()

    # -----------------------------------------------------------------------
    # 5. 运行校验
    # -----------------------------------------------------------------------
    print(f"[6/6] 运行 validate_data.py ...")
    print("-" * 60)

    validate_script = SCRIPT_DIR / "validate_data.py"
    if not validate_script.exists():
        print(f"  [错误] 找不到校验脚本: {validate_script}")
        return 1

    import subprocess
    result = subprocess.run(
        [sys.executable, str(validate_script)],
        cwd=str(PROJECT_ROOT),
        capture_output=False,
    )

    print("-" * 60)
    if result.returncode == 0:
        print("校验通过！")
    else:
        print(f"校验未通过（退出码 {result.returncode}），请检查上方输出。")

    print()
    print("=" * 60)
    print(f"  完成！已更新 {updated_count} 个增强的中文效果描述。")
    print(f"  备份位于: {BACKUP_FILE.relative_to(PROJECT_ROOT)}")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
