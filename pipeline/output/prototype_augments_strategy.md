# Prototype 增强策略报告

> 生成日期：2026-06-14
> 数据来源：`data/augments.json`、`data/synergies.json`、`data/issues.json`、`scripts/validate_data.py`

---

## 1. Prototype 增强清单

以下 13 个增强的 `source_status` 字段值为 `"prototype"`，表示它们不在 LoL Wiki ARAM:Mayhem 官方数据中，可能为早期占位数据。所有 13 个增强的 `status` 均为 `"active"`。

| # | ID | 中文名 | 英文名 | Tier | 稀有度 | 引用该增强的数据文件 |
|---|------|--------|--------|------|--------|----------------------|
| 1 | `chain_lightning` | 连锁闪电 | Chain Lightning | gold | gold | synergies.json, issues.json |
| 2 | `toxic_amplifier` | 毒性增幅 | Toxic Amplifier | gold | gold | synergies.json, issues.json |
| 3 | `armor_piercing` | 穿甲弹头 | Armor Piercing | gold | gold | synergies.json, issues.json |
| 4 | `annihilation_gaze` | 毁灭凝视 | Annihilation Gaze | prismatic | prism | synergies.json |
| 5 | `ultimate_cooldown` | 终极冷却 | Ultimate Cooldown | silver | silver | synergies.json |
| 6 | `mana_fountain` | 法力涌泉 | Mana Fountain | silver | silver | synergies.json |
| 7 | `lethal_tempo` | 致命节奏 | Lethal Tempo | silver | silver | synergies.json |
| 8 | `untouchable` | 你摸不到 | Untouchable | silver | silver | synergies.json |
| 9 | `physical_to_magical` | 物理转魔法 | Physical to Magical | silver | silver | synergies.json |
| 10 | `ultimate_hunter` | 终极猎手 | Ultimate Hunter | prismatic | prism | synergies.json, issues.json |
| 11 | `psionic_shield` | 灵能护盾 | Psionic Shield | silver | silver | （无引用） |
| 12 | `echo` | 回响 | Echo | prismatic | prism | （无引用） |
| 13 | `phantom_dance` | 幻影之舞 | Phantom Dance | gold | gold | （无引用） |

**备注：**
- 13 个增强中，10 个在 `synergies.json` 中被引用。
- 4 个增强在 `issues.json` 中被引用（连锁闪电、毒性增幅、穿甲弹头、终极猎手）。
- 3 个增强（灵能护盾、回响、幻影之舞）在任何其他数据文件中均无引用，属于"孤岛数据"。
- 所有 13 个增强的 `notes` 字段均包含相同说明：_"原型增强：该增强不在 LoL Wiki ARAM:Mayhem 数据中，可能为早期占位数据。保留供后续人工审核。"_

---

## 2. 交叉引用分析

### 2.1 各增强的详细引用情况

#### 连锁闪电 (`chain_lightning`)

**Synergies 引用（7 条）：**

| 英雄 | Tier | 状态 | Delta |
|------|------|------|-------|
| 吉格斯 | transform | **verified** | +6.4 |
| 布兰德 | transform | **verified** | +6.8 |
| 提莫 | bug | **disputed** | 0.0 |
| 亚索 | avoid | **verified** | -2.3 |
| 婕拉 | recommend | **verified** | +3.7 |
| 泽拉斯 | transform | **verified** | +5.5 |
| 凯南 | transform | **verified** | +4.8 |
| 吉格斯（社区投稿） | transform | investigating | N/A |

**Issues 引用（3 条）：**
- [major] 提莫 - R蘑菇不触发连锁闪电增强（status: investigating）
- [major] 亚索 - W风墙阻挡己方连锁闪电弹射（status: community）
- [major] Teemo mushroom traps do not trigger Chain Lightning（status: investigating）

**风险提示：** 有 6 条 synergy 标记为 `verified`，但增强本身为 prototype 状态，存在数据一致性风险。

---

#### 毒性增幅 (`toxic_amplifier`)

**Synergies 引用（3 条）：**

| 英雄 | Tier | 状态 | Delta |
|------|------|------|-------|
| 布兰德 | bug | **investigating** | +8.1 |
| 提莫 | transform | **verified** | +5.5 |
| 婕拉 | transform | **verified** | +5.8 |

**Issues 引用（2 条）：**
- [critical] 布兰德 - 毒性增幅叠加计算异常（status: investigating）
- [critical] Brand + Toxic Amplifier damage calculation uses multiplicative stacking（status: investigating）

**风险提示：** 2 条 synergy 为 `verified`，但存在 critical 级别的 bug issue。

---

#### 穿甲弹头 (`armor_piercing`)

**Synergies 引用（4 条）：**

| 英雄 | Tier | 状态 | Delta |
|------|------|------|-------|
| 吉格斯 | avoid | **verified** | -1.2 |
| 亚索 | bug | **disputed** | -0.5 |
| 婕拉 | avoid | **verified** | -1.8 |
| 莫甘娜 | avoid | **verified** | -1.0 |

**Issues 引用（1 条）：**
- [minor] 穿甲弹头对亚索Q技能疑似不生效（status: disputed）

**风险提示：** 3 条 synergy 为 `verified`，但该增强在所有 avoid 类 synergy 中均为负收益。

---

#### 毁灭凝视 (`annihilation_gaze`)

**Synergies 引用（3 条）：**

| 英雄 | Tier | 状态 | Delta |
|------|------|------|-------|
| 卡尔萨斯 | transform | **verified** | +7.2 |
| 吉格斯（组合引用） | — | — | — |
| 泽拉斯 | recommend | **verified** | +3.2 |

**Issues 引用：** 无

**风险提示：** 2 条 verified synergy，无已知 issue，数据质量相对较好。

---

#### 终极冷却 (`ultimate_cooldown`)

**Synergies 引用（2 条）：**

| 英雄 | Tier | 状态 | Delta |
|------|------|------|-------|
| 吉格斯 | recommend | **verified** | +3.7 |
| 卡尔萨斯 | recommend | **verified** | +3.4 |

**Issues 引用：** 无

**风险提示：** 全部 verified，无已知 issue。

---

#### 法力涌泉 (`mana_fountain`)

**Synergies 引用（1 条）：**

| 英雄 | Tier | 状态 | Delta |
|------|------|------|-------|
| 维克托 | recommend | **verified** | +2.5 |

**Issues 引用：** 无

---

#### 致命节奏 (`lethal_tempo`)

**Synergies 引用（1 条，间接引用）：**

| 英雄 | Tier | 状态 | Delta |
|------|------|------|-------|
| 韦鲁斯 | transform | **verified** | +5.2 |

> 注：韦鲁斯的 synergy combos 中引用了"韦鲁斯+致命节奏"，但致命节奏本身没有独立的 synergy 条目。

**Issues 引用：** 无

---

#### 你摸不到 (`untouchable`)

**Synergies 引用（1 条，间接引用）：**

| 英雄 | Tier | 状态 | Delta |
|------|------|------|-------|
| 卡莎 | avoid | **verified** | -1.5 |

> 注：亚索 synergy combos 中引用了"亚索+你摸不到"。

**Issues 引用：** 无

---

#### 物理转魔法 (`physical_to_magical`)

**Synergies 引用（1 条）：**

| 英雄 | Tier | 状态 | Delta |
|------|------|------|-------|
| 卡莎 | recommend | **verified** | +3.0 |

**Issues 引用：** 无

---

#### 终极猎手 (`ultimate_hunter`)

**Synergies 引用（3 条）：**

| 英雄 | Tier | 状态 | Delta |
|------|------|------|-------|
| 卡莎（组合引用） | — | — | — |
| 卡尔萨斯 | bug | **investigating** | 0.0 |
| 韦鲁斯 | recommend | **verified** | +3.8 |

**Issues 引用（1 条）：**
- [critical] 卡尔萨斯 - 终极猎手导致R技能CD异常（status: investigating）

**风险提示：** 1 条 verified synergy，但存在 critical 级别 bug。

---

#### 灵能护盾 (`psionic_shield`)

**Synergies 引用：** 无
**Issues 引用：** 无

**风险提示：** 完全无引用数据，属于"孤岛增强"，无法通过交叉引用验证其有效性。

---

#### 回响 (`echo`)

**Synergies 引用：** 无
**Issues 引用：** 无

**风险提示：** 完全无引用数据，属于"孤岛增强"。

---

#### 幻影之舞 (`phantom_dance`)

**Synergies 引用：** 无
**Issues 引用：** 无

**风险提示：** 完全无引用数据，属于"孤岛增强"。

---

### 2.2 Verified Synergy 与 Prototype 增强冲突汇总

以下 synergy 的 `status="verified"` 但所引用的增强 `source_status="prototype"`，存在语义矛盾：

| 增强 | Verified Synergy 数量 | 涉及英雄 |
|------|----------------------|----------|
| 连锁闪电 | 6 | 吉格斯、布兰德、亚索、婕拉、泽拉斯、凯南 |
| 毒性增幅 | 2 | 提莫、婕拉 |
| 穿甲弹头 | 3 | 吉格斯、婕拉、莫甘娜 |
| 毁灭凝视 | 2 | 卡尔萨斯、泽拉斯 |
| 终极冷却 | 2 | 吉格斯、卡尔萨斯 |
| 法力涌泉 | 1 | 维克托 |
| 物理转魔法 | 1 | 卡莎 |
| 终极猎手 | 1 | 韦鲁斯 |
| 你摸不到 | 1 | 卡莎 |

**共计 19 条 verified synergy 引用了 prototype 增强。**

---

## 3. 是否可以安全标记为 prototype

### 3.1 现状分析

当前 13 个增强的状态存在**双重矛盾**：

| 字段 | 值 | 含义 |
|------|------|------|
| `source_status` | `"prototype"` | 数据来源不可靠，可能为早期占位数据 |
| `status` | `"active"` | 增强当前在游戏中处于活跃可用状态 |

这两个字段的语义本不应冲突——`source_status` 描述的是**数据来源的可靠性**，`status` 描述的是**增强在游戏中的实际状态**。但问题在于：如果数据来源不可靠（prototype），那么 `status="active"` 这个判断本身也可能不准确。

### 3.2 风险评估

**可以安全保持 prototype 标记的增强（低风险）：**

以下 3 个增强无外部引用，修改其状态不会影响任何其他数据：
- 灵能护盾 (`psionic_shield`)
- 回响 (`echo`)
- 幻影之舞 (`phantom_dance`)

**需谨慎处理的增强（中风险）：**

以下增强虽然被标记为 prototype，但已有大量 verified synergy 数据支撑其存在：
- 连锁闪电 — 6 条 verified synergy + 3 条 issue
- 穿甲弹头 — 3 条 verified synergy + 1 条 issue
- 毁灭凝视 — 2 条 verified synergy，无 issue
- 终极冷却 — 2 条 verified synergy，无 issue
- 法力涌泉 — 1 条 verified synergy，无 issue
- 物理转魔法 — 1 条 verified synergy，无 issue

**高风险增强（有已知 bug 但仍活跃）：**
- 毒性增幅 — 存在 2 条 critical issue（布兰德叠加异常），但仍被标记为 active
- 终极猎手 — 存在 1 条 critical issue（卡尔萨斯 CD 异常），但仍被标记为 active

### 3.3 建议

保持 `source_status="prototype"` 标记是安全的，该字段不影响增强的可用性和前端展示。但应关注以下问题：

1. `source_status="prototype"` 应当被视为一个**待审核标记**，而非永久状态。
2. 对于已有大量 verified synergy 数据支撑的增强（如连锁闪电、毁灭凝视等），应考虑将 `source_status` 升级为 `"verified"` 或 `"community_verified"`。
3. 对于存在 critical issue 的增强（毒性增幅、终极猎手），应保留 `source_status="prototype"` 直到 bug 被确认或修复。

---

## 4. VALID_AUG_STATUSES 扩展建议

### 4.1 现状

在 `scripts/validate_data.py` 第 43 行，当前定义为：

```python
VALID_AUG_STATUSES = {"active", "removed", "unknown"}
```

该集合用于校验 `augments.json` 中每个增强的 `status` 字段（第 264 行）。

### 4.2 问题分析

当前所有 13 个 prototype 增强的 `status` 均为 `"active"`，因此**不会触发校验错误**。但这掩盖了真实情况——这些增强的数据来源尚未被确认。

当前 `VALID_AUG_STATUSES` 缺少对 `source_status` 字段的校验。`source_status` 是一个非校验字段，可以取任意值，这意味着 `"prototype"` 这个值目前不受校验脚本保护。

### 4.3 建议：扩展 VALID_AUG_STATUSES

**建议将 `"prototype"` 添加到 `VALID_AUG_STATUSES` 中。**

理由如下：

1. **语义准确性**：`status="active"` 表示增强在游戏中可用且数据可靠，但 prototype 增强的数据本身尚未被确认。添加 `"prototype"` 作为合法 status 值后，可以让这两个概念分离。
2. **前端区分**：如果 status 能准确反映 prototype 状态，前端可以据此展示不同的 UI 样式。
3. **数据治理**：明确的枚举值有助于后续批量查找和处理这些增强。

### 4.4 所需变更

如果需要实施此扩展，`scripts/validate_data.py` 需进行以下变更：

**变更 1（第 43 行）— 扩展枚举值：**

```python
# 修改前
VALID_AUG_STATUSES = {"active", "removed", "unknown"}

# 修改后
VALID_AUG_STATUSES = {"active", "removed", "unknown", "prototype"}
```

**变更 2（第 299-301 行附近）— 新增警告规则 W8：**

```python
# W8. status 为 prototype
if a.get("status") == "prototype":
    warn(f"[augments.json] 第 {i + 1} 条增强 '{a.get('name', '?')}' status 为 prototype，待人工审核")
```

**变更 3（可选）— 批量更新 augments.json：**

将 13 个 prototype 增强的 `status` 从 `"active"` 改为 `"prototype"`。注意：此项变更需同步更新前端筛选逻辑。

**变更 4（可选）— 新增 source_status 校验：**

在 `validate_augments` 函数中新增对 `source_status` 字段的枚举校验：

```python
VALID_SOURCE_STATUSES = {"verified", "prototype", "potentially_outdated", "community"}

# 在循环中添加
if "source_status" in a:
    check_enum(a["source_status"], VALID_SOURCE_STATUSES, "source_status", "增强", "augments.json", i)
```

---

## 5. 前端筛选建议

### 5.1 是否应添加 "Prototype" 筛选器/标签

**建议：添加。**

### 5.2 具体建议

**方案 A：添加 Prototype 徽章（推荐）**

在增强卡片上显示一个 "Prototype" 或 "原型" 的徽章/标签，以视觉方式区分这些增强与正式增强。

- **优点**：
  - 用户可以快速识别哪些增强数据可能不够准确
  - 不破坏现有筛选逻辑，仅作为辅助信息展示
  - 与现有的 tier 标签（transform / recommend / avoid / bug）不冲突
- **实现方式**：
  - 在增强卡片右上角显示橙色/黄色 "原型" 徽章
  - 鼠标悬停时显示 tooltip："该增强数据为原型状态，可能尚未完全验证"

**方案 B：添加筛选过滤器**

在增强列表页面添加 "Prototype" 作为筛选选项，允许用户选择是否显示原型增强。

- **优点**：
  - 追求数据准确性的用户可以隐藏原型增强
  - 数据完整性不受影响
- **缺点**：
  - 增加 UI 复杂度
  - 可能让用户产生"原型增强不可信"的误解，实际上部分原型增强已有大量验证数据

**方案 C：组合方案（最佳）**

同时采用方案 A + 方案 B：
1. 默认显示所有增强，原型增强带 "原型" 徽章
2. 在筛选栏中提供 "隐藏原型增强" 的开关
3. 在增强详情页中显示数据来源状态说明

### 5.3 UX 注意事项

1. **不要默认隐藏原型增强**：许多原型增强（如连锁闪电、毁灭凝视）已有大量 verified synergy 数据，隐藏它们会减少用户可用信息量。
2. **颜色选择**：建议使用橙色/琥珀色作为原型标记颜色，与绿色（active）和红色（removed）形成区分，传达"需注意但非不可用"的含义。
3. **数据透明度**：在原型增强的详情页中展示其 `source_status`、synergy 数量和 issue 数量，让用户自行判断数据可信度。
4. **孤岛增强特殊处理**：对于灵能护盾、回响、幻影之舞这 3 个无任何引用的增强，可在卡片上额外显示"待补充数据"的提示。

---

## 6. 总结建议

### 优先级汇总

| 优先级 | 建议项 | 影响范围 | 工作量 |
|--------|--------|----------|--------|
| **P0 - 紧急** | 处理毒性增幅的 2 条 critical issue（布兰德叠加异常） | 数据准确性 | 低 |
| **P0 - 紧急** | 处理终极猎手的 critical issue（卡尔萨斯 CD 异常） | 数据准确性 | 低 |
| **P1 - 高** | 将 `"prototype"` 添加到 `VALID_AUG_STATUSES` 中 | 校验脚本 | 低 |
| **P1 - 高** | 对 19 条 verified synergy + prototype 增强的矛盾进行标注 | 数据一致性 | 中 |
| **P2 - 中** | 前端添加 "原型" 徽章（方案 A） | 用户体验 | 中 |
| **P2 - 中** | 对 3 个孤岛增强（灵能护盾、回响、幻影之舞）补充 synergy 数据或标记为 "needs_review" | 数据完整性 | 中 |
| **P3 - 低** | 前端添加 Prototype 筛选过滤器（方案 B） | 用户体验 | 中 |
| **P3 - 低** | 新增 `source_status` 字段枚举校验 | 校验脚本 | 低 |
| **P3 - 低** | 批量将 13 个 prototype 增强的 `status` 从 `"active"` 改为 `"prototype"` | 数据一致性 | 低（但需同步前端） |

### 总体结论

1. **保持 `source_status="prototype"` 标记是安全的**，不需要修改任何 `data/*.json` 文件。该字段正确反映了这些增强的数据来源状态。

2. **核心矛盾不在于 prototype 标记本身，而在于 `status="active"` 与 `source_status="prototype"` 的语义模糊。** 当前校验脚本不校验 `source_status`，因此不会报错；但建议将 `"prototype"` 正式纳入 `VALID_AUG_STATUSES`，以便未来可以选择性地将 `status` 改为 `"prototype"` 进行更精确的分类。

3. **已有大量 verified synergy 支撑的增强**（如连锁闪电、毁灭凝视、终极冷却等 6 个），建议后续进行人工审核后，将 `source_status` 升级为 `"verified"`，从而解除 prototype 标记。

4. **3 个孤岛增强**（灵能护盾、回响、幻影之舞）由于没有任何 synergy 或 issue 引用，建议优先安排社区数据收集，或标记为 `"needs_review"` 以推动人工审核流程。

5. **前端应添加 Prototype 徽章**，让用户对数据来源可靠性有直观感知，但不应默认隐藏这些增强——它们的数据质量实际上参差不齐，部分已有较高可信度。
