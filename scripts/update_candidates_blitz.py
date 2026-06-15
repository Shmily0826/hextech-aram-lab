#!/usr/bin/env python3
"""
用 blitz.gg 中文数据更新增强导入候选。
1. 为现有候选补充中文效果描述
2. 添加 blitz.gg 上发现但候选中缺少的新增强
"""
import json, sys, os, io, copy

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CANDIDATES_PATH = os.path.join(PROJECT, "pipeline", "output", "augment_import_candidates.json")

# ===== blitz.gg 中文效果描述 (从页面直接提取) =====
BLITZ_EFFECTS_ZH = {
    # --- 棱彩 Prismatic ---
    "eureka": "获得相当于30%法术强度的技能急速。",
    "giant_slayer": "体型变小，获得移动速度，并基于敌方英雄体型大于你的程度获得额外伤害。",
    "goliath": "体型变大，获得35%生命值和15%适应之力。",
    "infernal_conduit": "技能对英雄施加灼烧效果，灼烧每跳减少基础技能冷却时间。灼烧可无限叠加。",
    "dropkick": "攻击可处决低生命值敌人，击退周围敌人并爆炸治疗自身。",
    "scopiest_weapons": "获得250攻击距离。",
    "final_form": "施放终极技能时获得50%最大生命值护盾、20%全能吸血和30%移动速度，持续10秒（20秒冷却）。",
    "dual_wield": "攻击发射箭矢，造成40%伤害并施加40%效能的命中特效。获得10%攻击速度。",
    "infinite_recursion": "获得60技能急速，每次参与击杀额外获得3技能急速。",
    "quest_wooglets_witchcap": "获得无用大棒。任务：持有灭世者的死亡之帽和中娅沙漏。奖励：转化为沃格勒特的巫师帽。",
    "ultimate_revolution": "施放终极技能后刷新其冷却时间（75秒冷却，阵亡时重置）。",
    "tap_dancer": "攻击提供10移动速度（5秒，可无限叠加）。基于总移动速度获得10%攻击速度。",
    "draw_your_sword": "变为近战，获得30%攻击力、25%攻击速度、30%生命值、25%移动速度和20%吸血。仅远程英雄可用。",
    "dashing": "冲刺/跳跃/闪烁技能获得175技能急速。",
    "biggest_snowball_ever": "雪球获得100技能急速，体积变大且可穿过小兵，命中后减速击飞并造成额外伤害。",
    "back_to_basics": "提升技能伤害/治疗/护盾/急速，但不能使用终极技能。",
    "courage_of_the_colossus": "定身或缚地敌方英雄后获得护盾（150-450 + 4%最大生命值），持续3秒（5秒冷却）。护盾可叠加。",
    "mystic_punch": "攻击命中时减少所有技能冷却时间1.25秒。",
    "fey_magic": "终极技能伤害将敌人变形为无害生物2秒，降低60移动速度并缴械（15秒冷却）。",
    "ultimate_awakening": "获得30终极技能急速。施放终极技能后刷新所有基础技能冷却并获得300基础技能急速，持续15秒（20秒冷却）。",
    "transmute_chaos": "获得2个完全随机的强化符文。",
    "fan_the_hammer": "攻击发射5个额外飞弹，造成随距离提升的伤害。",
    "ominous_pact": "技能消耗5%当前生命值。基于已损失生命值获得法强（最高75-150）、移动速度和全能吸血。",
    "can_t_touch_this": "施放终极技能后进入短时间免疫伤害状态。",
    "empowered_by_the_faithful": "为友军治疗/护盾积攒虔诚层数（上限50）。满层时释放冲击波造成伤害，并处决低血量敌人。",
    "omni_soul": "获得3个随机龙魂。",
    "stuck_in_here_with_me": "施放终极技能生成光环，持续2秒扩大。之后嘲讽范围内敌人2秒并获得50%伤害减免（30秒冷却）。+30终极技能急速。",
    "stats_on_stats_on_stats": "获得4个属性锻造器，下次选择强化符文时每个槽位额外一次刷新。更高几率出现金色和棱彩锻造器。",
    "symphony_of_war": "获得征服者和致命节奏基石符文。",
    "cruelty": "定身或缚地敌方英雄时召唤彗星，1秒后落地造成50-150（+40%法术强度）（+4%最大生命值）魔法伤害（6秒冷却）。",
    "mad_scientist": "获得时和每次重生时随机获得：坦克属性+增大体型 或 技能急速+移动速度+缩小体型。",
    "windspeakers_blessing": "治疗或护盾使目标获得30-60护甲和魔法抗性，持续3秒。",
    # Prismatic - 我们候选中没有的（新增）
    "high_roller": "附近敌人阵亡时有几率掉落属性锻造器。",
    "eat_the_path": "周期性识别附近敌方英雄破绽，命中造成真实伤害、回血并提供移速。",
    "multishot": "任务：用技能命中敌人若干次。奖励：发射额外飞弹。",
    "spell_splitting": "技能飞弹在命中/最大距离/再次施放时分裂为二。",
    "echoing_release": "施放技能时派出复制体再次施放同一技能。",
    "quickstep": "使用技能时朝鼠标指针方向冲刺。",
    "titan_resolve": "承受和造成伤害获得层数，每10层获得适应之力、双抗、体型和韧性。",
    "pandoras_box": "将所有已获得的强化符文变为随机棱彩阶符文。",
    "spirit_bomb": "治疗/护盾友军积攒炸弹层数，满层后投掷给最低血量友军。",
    "pincushion": "技能持续期间攻击施加标记，结束时爆炸造成伤害并提供移速。",
    "pandora_box": "将所有强化符文变为随机棱彩阶。",
    "clown_college": "获得欺诈魔术技能，阵亡时生成爆炸盒造成伤害和恐惧。",
    "droppybara": "召唤卡皮巴拉从天而降，造成30%最大生命值真实伤害。",
    "dimension_shift": "获得\"当黑暗来临\"召唤师技能，传送至另一位面。",
    "devil_on_shoulder": "与大魔王签订契约，汲取生命力但造成真实伤害并治疗残片。",
    "sneakerhead": "随机获得升级靴子，完成任务后可更换。",
    "jeweled_gauntlet": "技能可暴击，获得暴击几率。",
    "squishy_slappy_grab": "偶尔拉拽附近敌人进行下次攻击。",
    "quantum_computing": "周期性自动施放巨型斩击，减速敌人、造成最大生命值伤害并治疗自身。",
    "poro_stampede": "收集魄罗佳肴投喂魄罗，获得魄罗冲锋召唤师技能。",
    "earthwake": "冲刺/闪烁/传送留下0.75秒后爆炸的轨迹。",
    "blade_waltz": "获得利刃华尔兹作为召唤师技能。",
    "upgrade_mikaels": "获得100%攻速，对英雄攻击使米凯尔的祝福治疗效果提升250%。",
    "skip_the_basic": "技能急速仅作用于终极技能，效果增强50%，获得100技能急速。",
    "hellbent": "攻击和技能伤害提供层数，满层后下次阵亡时获得强化复活。",
    "surge_field": "施放终极技能生成地带，提供急速和移速，发射飞弹造成20%伤害。",
    "drop_bear": "阵亡时巨大提伯斯从天而降造成真实伤害。",
    "rite_of_ascension": "击杀后留下精华，攻击提供移速并重置基础技能冷却。",
    "chain_reaction": "被击退目标命中另一英雄则二者被击飞并受伤。",
    "ult_bot": "技能急速仅作用于终极技能，获得额外终极技能急速。",
    # --- 金色 Gold ---
    "upgrade_infinity_edge": "获得25%暴击几率和500金币。拥有无尽之刃时，暴击伤害获得随机额外暴击伤害加成。",
    "soul_eater": "定身敌方英雄时获得20最大生命值（可无限叠加，5秒冷却）。",
    "tank_engine": "击杀增大体型并提升5%最大生命值（可无限叠加）。阵亡损失65%层数。",
    "recursion": "获得60技能急速。",
    "scopier_weapons": "获得200攻击距离。",
    "its_killing_time": "施放终极技能后标记所有敌人，存储你对目标造成的40%伤害，5秒后引爆造成真实伤害（8秒冷却）。",
    "thread_the_needle": "获得18%护甲穿透和法术穿透。",
    "shrink_engine": "击杀变小并获得8技能急速和1%移动速度（可无限叠加）。阵亡损失65%层数。",
    "skilled_sniper": "非终极技能从700距离外命中敌方英雄，返还80%冷却时间（持续伤害技能为65%）。",
    "ethereal_weapon": "技能可施加命中特效（每目标1秒冷却）。",
    "transmute_prismatic": "获得1个随机棱彩阶强化符文（排除当前选择中的其他两个）。",
    "phenomenal_evil": "技能对英雄造成伤害时永久获得1法强（每秒最多触发一次）。若非法师第一符文，起始自带40层。",
    "quest_steel_your_heart": "任务：拥有心之钢并积累超过300层。奖励：心之钢层数效果乘以3。",
    "bread_and_butter": "对应技能获得100技能急速。",
    "magic_missile": "造成技能伤害时发射3个飞弹，每个造成基于飞行距离的最大生命值真实伤害（最高1%，6秒冷却）。",
    "sonata": "每10秒自动交替施放坚毅咏叹调（治疗/护盾光环）和迅捷奏鸣曲（移速光环）。",
    "nightstalking": "对敌方英雄造成伤害后3秒内击杀该目标，进入1.5秒隐身。",
    "stats_on_stats": "获得3个属性锻造器，更高几率出现金色和棱彩锻造器。",
    "with_haste": "获得相当于70%技能急速的移动速度。",
    "donation": "获得1750金币。",
    # Gold - 候选中已有的但补描述
    "big_brain": "获得相当于300%法术强度的护盾，持续至被摧毁。护盾在重生时和每70秒补充。",
    "bread_and_cheese": "E技能获得100技能急速。",
    "bread_and_jam": "W技能获得100技能急速。",
    "celestial_body": "获得1500生命值，但造成10%更少伤害。",
    "dawnbringers_resolve": "低于50%最大生命值时，3秒内恢复30%最大生命值（45秒冷却）。",
    "get_excited": "参与击杀后获得移动速度和攻击速度，持续4秒。",
    "growth_spurt": "获得\"生机迸发\"召唤师技能：突然增大体型，击飞附近敌人。",
    "marksmage": "攻击造成相当于75%法术强度的额外物理伤害。",
    "overflow": "法力消耗翻倍。基于最大法力值增加技能治疗、护盾和伤害。",
    # Gold - 新增（不在现有候选中）
    "archmage": "施放一个技能后返还另一个随机技能30%原冷却时间的费用。",
    "from_downtown": "任务：用技能狙击敌方英雄若干次。奖励：向被狙击的敌人发射流星。",
    "pursuit_of_haste": "任务：用技能命中敌方英雄若干次。奖励：获得该技能的技能急速。",
    "pursuit_of_power": "任务：用技能命中敌方英雄若干次。奖励：永久提升该技能伤害。",
    "lil_extra_help": "技能持续期间获得攻击距离和攻击速度。",
    "warlock_juicebox": "获得全能吸血。",
    "pressure_cooker": "每秒对附近敌方英雄施加灼烧（基于最大生命值缩放）。任务：提升灼烧规模和伤害。",
    "void_dash": "冲刺技能产生虚空地带，减速敌方英雄并造成魔法伤害。",
    "combusting_interest": "对英雄施加的灼烧和持续伤害会生成金币。",
    "sticky_fingers": "击杀时从敌方英雄偷取一件随机装备。",
    "storm_surge": "靠近友方英雄时获得移动速度。",
}

# ===== 新增增强候选 (blitz.gg 上有但我们的候选列表中没有) =====
NEW_CANDIDATES = [
    # 棱彩 - 新增
    {"id": "high_roller", "name": "掷骰狂人", "name_en": "High Roller", "tier": "prismatic"},
    {"id": "eat_the_path", "name": "吃过路兵", "name_en": "Eat the Path", "tier": "prismatic"},
    {"id": "multishot", "name": "多重射击", "name_en": "Multishot", "tier": "prismatic"},
    {"id": "spell_splitting", "name": "咒语裂变", "name_en": "Spell Splitting", "tier": "prismatic"},
    {"id": "echoing_release", "name": "回响施放", "name_en": "Echoing Release", "tier": "prismatic"},
    {"id": "quickstep", "name": "快步", "name_en": "Quickstep", "tier": "prismatic"},
    {"id": "titan_resolve", "name": "泰坦的坚决", "name_en": "Titan's Resolve", "tier": "prismatic"},
    {"id": "pandoras_box", "name": "潘朵拉的盒子", "name_en": "Pandora's Box", "tier": "prismatic"},
    {"id": "spirit_bomb", "name": "灵魄炸弹", "name_en": "Spirit Bomb", "tier": "prismatic"},
    {"id": "pincushion", "name": "针插垫", "name_en": "Pin Cushion", "tier": "prismatic"},
    {"id": "clown_college", "name": "小丑学院", "name_en": "Clown College", "tier": "prismatic"},
    {"id": "droppybara", "name": "卡皮巴拉空投", "name_en": "Droppybara", "tier": "prismatic"},
    {"id": "dimension_shift", "name": "位面转移", "name_en": "Dimension Shift", "tier": "prismatic"},
    {"id": "devil_on_shoulder", "name": "你肩上的恶魔", "name_en": "Devil on Your Shoulder", "tier": "prismatic"},
    {"id": "sneakerhead", "name": "王中王，靴中靴", "name_en": "Sneakerhead", "tier": "prismatic"},
    {"id": "jeweled_gauntlet", "name": "珠光护手", "name_en": "Jeweled Gauntlet", "tier": "prismatic"},
    {"id": "squishy_slappy_grab", "name": "软弹啪叽抓", "name_en": "Squishy Slappy Grab", "tier": "prismatic"},
    {"id": "quantum_computing", "name": "量子计算", "name_en": "Quantum Computing", "tier": "prismatic"},
    {"id": "poro_stampede", "name": "魄罗蛮冲", "name_en": "Poro Stampede", "tier": "prismatic"},
    {"id": "earthwake", "name": "大地苏醒", "name_en": "Earthwake", "tier": "prismatic"},
    {"id": "blade_waltz", "name": "利刃华尔兹", "name_en": "Blade Waltz", "tier": "prismatic"},
    {"id": "upgrade_mikaels", "name": "升级：花晓之剑", "name_en": "Upgrade Mikael's Blessing", "tier": "prismatic"},
    {"id": "skip_the_basic", "name": "大招工具人", "name_en": "Skip the Basic", "tier": "prismatic"},
    {"id": "hellbent", "name": "濒死悟道", "name_en": "Hellbent", "tier": "prismatic"},
    {"id": "surge_field", "name": "电涌力场", "name_en": "Surge Field", "tier": "prismatic"},
    {"id": "drop_bear", "name": "空投熊", "name_en": "Drop Bear", "tier": "prismatic"},
    {"id": "rite_of_ascension", "name": "飞升仪式", "name_en": "Rite of Ascension", "tier": "prismatic"},
    {"id": "chain_reaction", "name": "连锁反应", "name_en": "Chain Reaction", "tier": "prismatic"},
    # 金色 - 新增
    {"id": "archmage", "name": "大法师", "name_en": "Archmage", "tier": "gold"},
    {"id": "from_downtown", "name": "狙神飞星", "name_en": "From Downtown", "tier": "gold"},
    {"id": "pursuit_of_haste", "name": "急速之追求", "name_en": "Pursuit of Haste", "tier": "gold"},
    {"id": "pursuit_of_power", "name": "威能之追求", "name_en": "Pursuit of Power", "tier": "gold"},
    {"id": "lil_extra_help", "name": "小小的额外帮助", "name_en": "Lil' Extra Help", "tier": "gold"},
    {"id": "warlock_juicebox", "name": "术士果汁盒", "name_en": "Warlock Juicebox", "tier": "gold"},
    {"id": "pressure_cooker", "name": "高压锅", "name_en": "Pressure Cooker", "tier": "gold"},
    {"id": "void_dash", "name": "虚空冲刺", "name_en": "Void Dash", "tier": "gold"},
    {"id": "combusting_interest", "name": "燃烧利息", "name_en": "Combusting Interest", "tier": "gold"},
    {"id": "sticky_fingers", "name": "顺手牵羊", "name_en": "Sticky Fingers", "tier": "gold"},
    {"id": "storm_surge", "name": "风暴涌动", "name_en": "Storm Surge", "tier": "gold"},
]

def main():
    with open(CANDIDATES_PATH, "r", encoding="utf-8") as f:
        candidates = json.load(f)

    existing_ids = {c["id"] for c in candidates}
    updated_count = 0
    added_count = 0

    # 1. 更新现有候选的中文效果描述
    for c in candidates:
        cid = c["id"]
        if cid in BLITZ_EFFECTS_ZH:
            new_effect = BLITZ_EFFECTS_ZH[cid]
            if c.get("effect", "") != new_effect:
                c["effect"] = new_effect
                c["_source_blitz"] = True
                updated_count += 1

    # 2. 添加新发现的候选
    for nc in NEW_CANDIDATES:
        if nc["id"] not in existing_ids:
            effect_zh = BLITZ_EFFECTS_ZH.get(nc["id"], "")
            entry = {
                "id": nc["id"],
                "name": nc["name"],
                "name_en": nc["name_en"],
                "tier": nc["tier"],
                "status": "active",
                "effect": effect_zh,
                "effect_en": "",
                "source_status": "import_candidate",
                "source": {
                    "type": "blitz_gg",
                    "url": f"https://blitz.gg/zh-CN/lol/aram-mayhem-augments"
                },
                "_source_blitz": True
            }
            candidates.append(entry)
            added_count += 1

    # 3. 排序: 按 tier (prismatic > gold > silver) 然后按 id
    tier_order = {"prismatic": 0, "gold": 1, "silver": 2}
    candidates.sort(key=lambda c: (tier_order.get(c["tier"], 9), c["id"]))

    # 4. 写入
    with open(CANDIDATES_PATH, "w", encoding="utf-8") as f:
        json.dump(candidates, f, ensure_ascii=False, indent=2)

    print(f"[OK] 更新了 {updated_count} 个现有候选的中文效果描述")
    print(f"[OK] 新增了 {added_count} 个候选 (来自 blitz.gg)")
    print(f"[OK] 候选总数: {len(candidates)}")

    # 5. 统计
    by_tier = {}
    for c in candidates:
        t = c["tier"]
        by_tier[t] = by_tier.get(t, 0) + 1
    for t, n in sorted(by_tier.items()):
        print(f"     {t}: {n}")

    with_effect = sum(1 for c in candidates if c.get("effect", ""))
    print(f"[OK] 有中文效果描述: {with_effect}/{len(candidates)}")

if __name__ == "__main__":
    main()
