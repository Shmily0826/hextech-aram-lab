# ARAM Augment Chinese Localization Report

**Generated:** 2026-06-15
**Data Sources:** `data/augments.json` (40 augments), `pipeline/output/chinese_augment_candidates.json` (255 entries from arammayhem.com)

---

## 1. Chinese Name Coverage

| Category | Count | Percentage |
|----------|------:|-----------:|
| Have Chinese name (Chinese characters in `name` field) | 16 | 40% |
| English-only name (no Chinese in `name` field) | 24 | 60% |

**Of the 24 English-only augments:**

| Sub-category | Count |
|--------------|------:|
| Chinese name available on arammayhem.com (active) | 20 |
| Chinese name available on arammayhem.com (marked as removed) | 4 |
| Not found on arammayhem.com at all | 0 |

All 24 English-only augments (sourced from the Wiki Module) have matches on arammayhem.com.

**Breakdown by data source:**

- All 16 Chinese-named augments originate from `source.type: "manual"` (hand-authored prototype data).
- All 24 English-only augments originate from `source.type: "lol_wiki_module"` (imported from the LoL Wiki Module).

---

## 2. Name Comparison Table

Legend for Status column:
- **Match**: Chinese name in our data matches arammayhem.com
- **No CN**: English-only name in our data; Chinese name available on arammayhem.com
- **N/A**: Not found on arammayhem.com (neither active nor removed)
- **Removed**: Found on arammayhem.com but marked as removed ("已移除")

### Augments with Chinese Names (16)

| # | id | name_en | Current `name` | arammayhem.com Chinese | Status |
|---|----|---------|----------------|----------------------|--------|
| 1 | chain_lightning | Chain Lightning | 连锁闪电 | -- | N/A |
| 2 | toxic_amplifier | Toxic Amplifier | 毒性增幅 | -- | N/A |
| 3 | blade_waltz | Blade Waltz | 利刃华尔兹 | 利刃华尔兹 | Match |
| 4 | armor_piercing | Armor Piercing | 穿甲弹头 | -- | N/A |
| 5 | annihilation_gaze | Annihilation Gaze | 毁灭凝视 | -- | N/A |
| 6 | ultimate_cooldown | Ultimate Cooldown | 终极冷却 | -- | N/A |
| 7 | all_for_you | All For You | 全心为你 | 全心为你 | Match |
| 8 | mana_fountain | Mana Fountain | 法力涌泉 | -- | N/A |
| 9 | lethal_tempo | Lethal Tempo | 致命节奏 | -- | N/A |
| 10 | untouchable | Untouchable | 你摸不到 | -- | N/A |
| 11 | physical_to_magical | Physical to Magical | 物理转魔法 | 物理转魔法 (slug: adapt) | Match |
| 12 | big_brain | Big Brain | 超强大脑 | 超强大脑 | Match |
| 13 | ultimate_hunter | Ultimate Hunter | 终极猎手 | -- | N/A |
| 14 | psionic_shield | Psionic Shield | 灵能护盾 | -- | N/A |
| 15 | echo | Echo | 回响 | -- | N/A |
| 16 | phantom_dance | Phantom Dance | 幻影之舞 | -- | N/A |

**Summary:** Of the 16 Chinese-named augments, 4 match arammayhem.com exactly. The remaining 12 are not present on arammayhem.com (they are prototype augments that may not exist in the current live game).

### Augments with English-Only Names (24)

| # | id | name_en | Current `name` | arammayhem.com Chinese | Status |
|---|----|---------|----------------|----------------------|--------|
| 17 | adamant | Adamant | Adamant | 坚若磐石 (已移除) | Removed |
| 18 | blunt_force | Blunt Force | Blunt Force | 大力 | No CN |
| 19 | deft | Deft | Deft | 灵巧 | No CN |
| 20 | erosion | Erosion | Erosion | 侵蚀 | No CN |
| 21 | first_aid_kit | First-Aid Kit | First-Aid Kit | 急救用具 | No CN |
| 22 | goredrink | Goredrink | Goredrink | 渴血 | No CN |
| 23 | homeguard | Homeguard | Homeguard | 家园卫士 | No CN |
| 24 | guilty_pleasure | Guilty Pleasure | Guilty Pleasure | 恶趣味 (已移除) | Removed |
| 25 | back_to_basics | Back to Basics | Back to Basics | 回归基本功 | No CN |
| 26 | biggest_snowball_ever | Biggest Snowball Ever | Biggest Snowball Ever | 史上最大雪球 | No CN |
| 27 | circle_of_death | Circle of Death | Circle of Death | 死亡之环 | No CN |
| 28 | get_excited | Get Excited | Get Excited | 罪恶快感 | No CN |
| 29 | goliath | Goliath | Goliath | 歌利亚巨人 | No CN |
| 30 | growth_spurt | Growth Spurt | Growth Spurt | 生机迸发 | No CN |
| 31 | bread_and_butter | Bread And Butter | Bread And Butter | 面包和黄油 | No CN |
| 32 | fan_the_hammer | Fan the Hammer | Fan the Hammer | 连拨击锤 | No CN |
| 33 | celestial_body | Celestial Body | Celestial Body | 星界躯体 | No CN |
| 34 | cerberus | Cerberus | Cerberus | 地狱三头犬 (已移除) | Removed |
| 35 | dashing | Dashing | Dashing | 全凭身法 | No CN |
| 36 | dive_bomber | Dive Bomber | Dive Bomber | 俯冲轰炸 | No CN |
| 37 | dropkick | Dropkick | Dropkick | 飞身踢 | No CN |
| 38 | executioner | Executioner | Executioner | 裁决使 (已移除) | Removed |
| 39 | don_t_blink | Don't Blink | Don't Blink | 唯快不破 | No CN |
| 40 | can_t_touch_this | Can't Touch This | Can't Touch This | 你摸不到 | No CN |

**Summary:** Of the 24 English-only augments, 20 have Chinese translations available from arammayhem.com (active) and 4 are marked as removed on arammayhem.com.

---

## 3. Tier Analysis

### Tier Conflicts Between arammayhem.com and the Wiki

There are **25 total tier conflicts** across all 255 entries in the candidates file, where `tier_arammayhem` differs from `tier_wiki`.

**Pattern:** In every case, arammayhem.com assigns a **lower tier** (Silver/Gold) while the Wiki assigns **Prismatic**. This suggests a systematic data discrepancy -- possibly the Wiki reflects an older tier assignment, or arammayhem.com reflects a recent rebalance.

| # | Slug | arammayhem.com Tier | Wiki Tier | Chinese Name |
|---|------|---------------------|-----------|-------------|
| 1 | pursuit-of-haste | Gold | Prismatic | 急速之追求 |
| 2 | pursuit-of-power | Silver | Prismatic | 威能之追求 |
| 3 | archmage | Gold | Prismatic | 大法师 |
| 4 | stackosaurusrex | Silver | Prismatic | 叠角龙 |
| 5 | pressure-cooker | Gold | Prismatic | 高压锅 |
| 6 | warlock-juicebox | Gold | Prismatic | 术士果汁盒 |
| 7 | forged-by-the-master | Silver | Prismatic | 大师铸就 |
| 8 | combusting-interest | Gold | Prismatic | 炽燃利息 |
| 9 | wee-woo-wee-woo | Gold | Prismatic | 喂呜喂呜 |
| 10 | siphon | Silver | Gold | 虹吸 |
| 11 | trusty-weapon | Silver | Prismatic | 可靠武器 |
| 12 | lil-extra-help | Gold | Prismatic | 小小的额外帮助 |
| 13 | void-dash | Gold | Prismatic | 虚空冲刺 |
| 14 | stay-resolute | Silver | Prismatic | 保持坚定 |
| 15 | bonk | Gold | Prismatic | 邦！ |
| 16 | yowch-my-coins | Gold | Prismatic | 哎哟，我的硬币！ |
| 17 | from-downtown | Gold | Prismatic | 狙神飞星 |
| 18 | overextender | Gold | Prismatic | 过量延伸者 |
| 19 | terraind | Gold | Prismatic | 地形专家 |
| 20 | shark-bait | Gold | Prismatic | 鲨鱼诱饵 |
| 21 | pat-on-the-back | Gold | Prismatic | 轻拍背部 |
| 22 | its-go-time | Silver | Prismatic | 前进时间到 |
| 23 | dont-change-the-channel | Silver | Prismatic | 别停止引导 |
| 24 | mercys-strike | Gold | Prismatic | 仁慈打击 |
| 25 | double-defense | Silver | Prismatic | 双重防御 |

**Note:** None of the 25 tier-conflicting augments are currently in our `augments.json` database. For our existing 40 augments, tiers are consistent between our data, the Wiki, and arammayhem.com (where applicable).

**Additional tier conflicts found in removed augments section (not counted above):**
- `red-envelopes`: Gold (arammayhem) vs Prismatic (Wiki)
- `nature-is-healing`: Gold vs Prismatic
- `rejuvenation`: Gold vs Prismatic
- `endless-decimation`: Gold vs Prismatic
- `snowblast`: Gold vs Prismatic
- `tooth-fairy`: Gold vs Prismatic
- `trailblazer`: Gold vs Prismatic
- `upgrade-cutlass`: Silver vs Prismatic
- `hide-on-bush`: Gold vs Prismatic
- `support-main`: Silver vs Prismatic
- `snowday`: Silver vs Prismatic
- `our-healing`: Gold vs Prismatic
- `mountainsoul`: Silver vs Prismatic
- `porcupine`: Gold vs Prismatic
- `shark-tempest`: Gold vs Prismatic

This brings the **grand total to approximately 40 tier conflicts** across all 255 entries (active + removed).

---

## 4. New Augments Summary

### Coverage Gap

| Metric | Count |
|--------|------:|
| Total augments on arammayhem.com | 255 |
| Augments on arammayhem.com marked as removed | ~73 |
| Active augments on arammayhem.com | ~182 |
| Augments in our database | 40 |
| Our augments found on arammayhem.com (active) | 24 |
| Our augments found on arammayhem.com (removed) | 4 |
| Our augments NOT on arammayhem.com | 12 |
| **Active augments on arammayhem.com NOT in our database** | **~158** |

### New Augments on arammayhem.com by Tier (Active, Not in Our Data)

| Tier | Count | Examples |
|------|------:|----------|
| Silver | ~53 | 重量级打击手, 逃跑计划, 暗影疾奔, 万用瞄准镜, 属性！, 海洋龙魂 |
| Gold | ~55 | 质变：棱彩阶, 坦克引擎, 大法师, 捐赠, 循环往复, 魔法飞弹 |
| Prismatic | ~55 | 掷骰狂人, 亮出你的剑, 无限循环往复, 尤里卡, 双刀流, 科学狂人 |

### Our 12 Augments Not on arammayhem.com (Active)

These prototype augments have no corresponding entry on arammayhem.com:

| id | name | tier | Notes |
|----|------|------|-------|
| chain_lightning | 连锁闪电 | gold | Prototype, source_status: prototype |
| toxic_amplifier | 毒性增幅 | gold | Prototype, source_status: prototype |
| armor_piercing | 穿甲弹头 | gold | Prototype, source_status: prototype |
| annihilation_gaze | 毁灭凝视 | prismatic | Prototype, source_status: prototype |
| ultimate_cooldown | 终极冷却 | silver | Prototype, source_status: prototype |
| mana_fountain | 法力涌泉 | silver | Prototype, source_status: prototype |
| lethal_tempo | 致命节奏 | silver | Prototype, source_status: prototype |
| untouchable | 你摸不到 | silver | Prototype, source_status: prototype |
| ultimate_hunter | 终极猎手 | prismatic | Prototype, source_status: prototype |
| psionic_shield | 灵能护盾 | silver | Prototype, source_status: prototype |
| echo | 回响 | prismatic | Prototype, source_status: prototype |
| phantom_dance | 幻影之舞 | gold | Prototype, source_status: prototype |

**Key finding:** All 12 missing augments are manual prototypes that were never on arammayhem.com. They may be early placeholder data that should be reviewed for removal or replacement with real game data.

---

## 5. Data Quality Notes

### Critical Effect Description Mismatch

**big_brain (超强大脑):** There is a significant discrepancy in the effect description:

| Source | Effect |
|--------|--------|
| Our data | "获得额外25%经验值。18级后所有技能等级+1。" (Gain 25% bonus XP, +1 skill level at 18) |
| arammayhem.com / Wiki | "Gain a shield that absorbs damage equal to 300% AP and lasts until destroyed. Shield is replenished upon respawn and every 70 seconds." |

The Chinese name "超强大脑" (Big Brain) matches, but the **effect descriptions are completely different**. Our data may contain outdated or incorrect effect information that needs to be replaced with the Wiki-sourced description.

### English Name vs. arammayhem.com Name Mismatch

| Our id | Our name_en | arammayhem slug | arammayhem name_en | Notes |
|--------|------------|-----------------|-------------------|-------|
| physical_to_magical | Physical to Magical | adapt | ADAPt | Different augment name entirely; same Chinese translation "物理转魔法" |
| untouchable | Untouchable | cant-touch-this | Can't Touch This | Different augment; similar Chinese: "你摸不到" vs "你摸不到" |
| siphon | -- | siphon | Soul Siphon | The slug "siphon" maps to Wiki's "Soul Siphon"; different from our augments |

### Augments Marked as Removed on arammayhem.com

The following 4 augments in our database are confirmed as **removed** on arammayhem.com (Chinese name includes "已移除"):

| id | Our name | arammayhem Chinese | Implication |
|----|----------|-------------------|-------------|
| adamant | Adamant | 坚若磐石已移除 | Should be marked inactive |
| guilty_pleasure | Guilty Pleasure | 恶趣味已移除 | Should be marked inactive |
| cerberus | Cerberus | 地狱三头犬已移除 | Should be marked inactive |
| executioner | Executioner | 裁决使已移除 | Should be marked inactive |

### Missing Chinese Effect Descriptions

All 24 Wiki-imported augments have empty `effect` (Chinese) and `desc` (Chinese) fields. Only `effect_en` is populated. These will need Chinese effect descriptions regardless of name localization.

### Source Status Observations

- 15 of our 40 augments have `source_status: "prototype"` -- these are hand-authored data not validated against any live source.
- 24 augments have `source_status: "potentially_outdated"` -- imported from the Wiki Module but not verified against arammayhem.com or recent patches.
- 1 augment (blade_waltz) has no explicit `source_status` but was verified against the Wiki.

---

## 6. Recommendations

### Priority 1: Apply Available Chinese Names (Quick Win)

The following 20 augments have English-only names in our data but have verified Chinese names available from arammayhem.com. These can be applied immediately:

| id | Suggested Chinese Name |
|----|----------------------|
| blunt_force | 大力 |
| deft | 灵巧 |
| erosion | 侵蚀 |
| first_aid_kit | 急救用具 |
| goredrink | 渴血 |
| homeguard | 家园卫士 |
| back_to_basics | 回归基本功 |
| biggest_snowball_ever | 史上最大雪球 |
| circle_of_death | 死亡之环 |
| get_excited | 罪恶快感 |
| goliath | 歌利亚巨人 |
| growth_spurt | 生机迸发 |
| bread_and_butter | 面包和黄油 |
| fan_the_hammer | 连拨击锤 |
| celestial_body | 星界躯体 |
| dashing | 全凭身法 |
| dive_bomber | 俯冲轰炸 |
| dropkick | 飞身踢 |
| don_t_blink | 唯快不破 |
| can_t_touch_this | 你摸不到 |

### Priority 2: Mark Removed Augments

Set `status: "removed"` for the 4 augments confirmed as removed on arammayhem.com:
- `adamant`
- `guilty_pleasure`
- `cerberus`
- `executioner`

### Priority 3: Fix Big Brain Effect Description

Replace the incorrect effect description for `big_brain` with the Wiki-sourced version. The current "experience/level" effect appears to be fabricated prototype data.

### Priority 4: Audit and Remove Prototype Augments

12 prototype augments are not found on arammayhem.com at all. These should be individually reviewed:
- If they were placeholder data: remove them from the database.
- If they represent real but renamed augments: update the id/name to match the current game data.
- If they were removed from the game in a past patch: set `status: "removed"` and add `patch_removed`.

### Priority 5: Resolve Tier Data Source

The 25+ tier conflicts between arammayhem.com and the Wiki should be investigated. Decide on a canonical tier source:
- If arammayhem.com reflects the current live game: use it as the tier authority.
- If the Wiki is more up-to-date: keep Wiki tiers.
- Consider adding a `tier_conflict` field to flag disputed tiers in our data.

### Priority 6: Expand Database with New Augments

Approximately 158 active augments exist on arammayhem.com that are not in our database. To expand coverage:
1. Import all active augments from `chinese_augment_candidates.json` where `in_current_data: false` and the augment is not removed.
2. Use the Chinese names and tier data from arammayhem.com.
3. Use the English descriptions from the Wiki match (where `wiki_matched: true`).
4. Prioritize high-popularity augments (lower `rank_on_site` values indicate higher popularity).

---

*End of report.*
