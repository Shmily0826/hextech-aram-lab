# 第三轮 Manual Links + 数据质量增强 — 综合报告

> 日期：2026-06-14
> 提交基线：`acdf035` (Reddit collector) → 本次新增提交

---

## 1. 第三轮 Manual Links 来源

本轮 10 条数据全部使用 **非 Reddit 来源**，覆盖中文社区和统计站：

| # | 来源 | 平台 | 内容方向 |
|---|------|------|----------|
| 1 | 百度贴吧 | tieba | 增强优先级排行实测（涉及 Adamant/Deft/Erosion/Executioner/Dashing 等） |
| 2 | 百度贴吧 | tieba | Cerberus 双基石符文触发 Bug 反馈 |
| 3 | 百度贴吧 | tieba | 英雄专精向增强组合推荐攻略 |
| 4 | NGA | nga | 增强符文隐藏机制深度解析（Biggest Snowball Ever/Circle of Death/Fan the Hammer） |
| 5 | NGA | nga | Guilty Pleasure + Dive Bomber 冷门增强实测数据 |
| 6 | NGA | nga | Don't Blink 移速差增伤机制研究 |
| 7 | 腾讯官方 | riot_official | 海克斯大乱斗增强符文官方中文名称介绍 |
| 8 | LoL Wiki | lol_wiki | ARAM Mayhem 主页面总览 + 补丁信息 |
| 9 | OP.GG | stats_site | 增强胜率排行榜（10 万场数据） |
| 10 | arammayhem.com | stats_site | 增强+英雄组合胜率数据 + Bug 标注 |

---

## 2. Pipeline 抽取统计

| 指标 | 数量 |
|------|------|
| collected (manual_items.jsonl) | 10 |
| cleaned (cleaned_items.jsonl) | 10 |
| deduped (deduped_items.jsonl) | 10（0 条重复） |
| general_discussion | 8 |
| bug_report | 2 |
| synergy_claim | 0 |
| trap_warning | 0 |
| unknown augments | 3（Hail of Blades, Press the Attack — 符文名非增强名；Cerberus 归一化失败） |
| evidence 完整率 | 2/2 bug candidates 有 source_url + summary |
| AI 调用耗时 | ~1 分 17 秒（10 条 × 1s 限速 + 重试） |

### 来源清洗效果评估

| 来源 | 清洗效果 | 说明 |
|------|----------|------|
| 百度贴吧 | 良好 | 纯文本内容，无 HTML 残留，中文分词正常 |
| NGA | 良好 | 结构化清晰，无广告干扰 |
| 腾讯官方 | 中等 | 内容较短但信息密度高，官方术语准确 |
| LoL Wiki | 中等 | 英文长文本，AI 正确分类为 general_discussion |
| 统计站 | 良好 | 数据型文本，AI 成功提取了 Brand+Toxic Amplifier 的 Bug 信号 |

### AI 分类偏向分析

本轮 AI 将 80% 的内容分类为 `general_discussion`，原因：
- 贴吧攻略帖和 NGA 解析帖本质是"综合讨论"而非单一 Bug/Synergy 报告
- AI 系统提示词对 general_discussion 的定义过于宽泛
- **建议后续优化**：在 SYSTEM_PROMPT 中增加"如果一条文本包含多个具体 synergy 或 bug 声明，应拆分为多个提取"的规则

---

## 3. 人工审核结果

| 候选 ID | 类型 | 审核结果 | 原因 |
|---------|------|----------|------|
| bug_20260614102703_0 | Cerberus Bug | **Skip** | 英雄字段归一化为 "Cerberus"（错误——Cerberus 是增强名），增强字段为符文名（Hail of Blades / Press the Attack），AI 提取结构错误 |
| bug_20260614102703_1 | Brand + 毒性增幅 | **Skip（已知重复）** | 数据正确（布兰德 + 毒性增幅），但 data/issues.json 第 1、7 条已记录同一问题。本轮作为第三方来源（arammayhem.com）交叉验证，确认 Bug 可信度 |

**Approve: 0 | Skip: 2 | Reject: 0**

> 注：Cerberus Bug 的归一化失败暴露了 AI 提取器对"增强名 vs 英雄名"混淆的问题。建议在 SYSTEM_PROMPT 中明确区分：Cerberus 是增强符文名，不是英雄名。

---

## 4. validate_data.py 结果

- **Errors: 0**（全部校验通过）
- **Warnings: 106**
  - effect 为空: 24 条
  - patch_added 为空: 24 条
  - evidence 为空: 54 条（synergies + reports）
  - 其他: 4 条

与上一轮的 145 条 warnings 对比减少了 39 条，主要因为部分 warnings 分类合并。

---

## 5. audit_trust_level.py 结果

| 风险等级 | 数量 | 说明 |
|----------|------|------|
| 高风险 | 29 | 主要是 status=verified 但 evidence 为空的 synergy 条目 |
| 中风险 | 4 | issues.json 中有 confirm 但无 evidence |
| 低风险 | 4 | reports.json 中有数据性声明但无 evidence |
| **合计** | **37** | |

核心问题仍是 27 条原始 synergy 条目的 evidence 为空（历史遗留数据）。

---

## 6. normalize_entities.py 测试结果

**58 通过，0 失败**

- 英雄名归一化：17 个测试用例全部通过
- 增强名归一化：41 个测试用例全部通过
- 未知名称正确标记为 unknown

---

## 7. 前端 Console 验证

- HTTP Server: `localhost:8765`
- 页面加载：正常
- **Console Errors: 0**
- 数据渲染：正常（40 增强 + 34 协同 + 9 Issues）

---

## 8. 中文来源 Collector 可行性评估

| 来源 | 是否适合开发 Collector | 原因 |
|------|------------------------|------|
| **百度贴吧** | 中等推荐 | 无官方 API，需要爬取 HTML。帖子内容质量不稳定，广告和无关评论多。但中文数据丰富，可获取增强中文名称 |
| **NGA** | 低推荐 | 无公开 API，需要登录态。帖子质量高但反爬严格，HTML 结构复杂。建议保持 manual_links 方式 |
| **腾讯官方** | 低推荐 | 官方新闻更新频率低，且大部分内容为活动推广而非游戏机制数据。增强名称可从官方页面获取 |

**最适合做 Collector 的中文来源**：百度贴吧（海克斯大乱斗吧）。理由：
1. 无需登录即可读取帖子
2. 内容更新频繁
3. 有大量玩家实测和 Bug 反馈
4. 可自动化采集标题 + 正文 + 高赞评论

---

## 9. tieba_collector 建议

**推荐开发，但优先级低于 Reddit。**

理由：
- Reddit API 申请仍在等待中，tieba 可作为中文数据补充
- 贴吧帖子结构简单，爬取难度中等
- 但需要注意：贴吧没有官方 API，爬取稳定性依赖于页面结构不变
- 建议先实现一个最小可用版本（标题 + 正文 + 前 5 条回复），再逐步完善

开发前需要的准备：
1. 确认贴吧反爬策略（Cookie 要求、请求频率限制）
2. 设计 clean_text 处理器支持贴吧特有的 HTML 结构
3. 不保存发帖人 UID、头像、个人主页

---

## 10. nga_collector 建议

**不推荐当前阶段开发。**

理由：
- NGA 需要登录态才能查看完整帖子
- 反爬机制严格（验证码、IP 限速）
- 维护成本高，HTML 结构频繁变动
- 建议保持 manual_links 手动收集方式，精选高质量帖子

---

## 11. Reddit API 等待期间可做的下一步

按优先级排序：

1. **处理 24 个增强中文翻译**（augment_wiki_quality_todo.json 已生成 24 条建议）
   - 人工审核 suggested_zh_name，对照腾讯官方确认
   - 优先处理 10 个 silver 增强（使用频率最高）

2. **修复 AI 提取器的增强名/英雄名混淆问题**
   - Cerberus Bug 暴露了 SYSTEM_PROMPT 的缺陷
   - 建议在提示词中增加"增强符文名 vs 英雄名"的区分规则

3. **补充 evidence 数据**（37 条高风险的核心问题）
   - 为 27 条原始 synergy 条目补充 source_url
   - 为 5 条 issues 补充复现证据链接

4. **扩展 VALID_AUG_STATUSES**（prototype 策略报告已输出建议）
   - 添加 "prototype" 到枚举
   - 更新 validate_data.py 的相关警告规则

5. **Reddit API 通过后直接运行 dry-run**
   - 所有基础设施已就绪（8/9 检查通过）
   - 仅需修复 standalone collector CLI 的 --dry-run 支持（非关键）

---

## 附：产出文件清单

| 文件 | 状态 | 说明 |
|------|------|------|
| `pipeline/config/manual_links.json` | 已更新 | 第三轮 10 条非 Reddit 来源 |
| `pipeline/output/manual_items.jsonl` | 已生成 | 10 条 validated records |
| `pipeline/output/cleaned_items.jsonl` | 已生成 | 10 条 cleaned |
| `pipeline/output/deduped_items.jsonl` | 已生成 | 10 条（0 重复） |
| `pipeline/output/candidate_bugs.json` | 已生成 | 2 条 Bug 候选（均 skip） |
| `pipeline/output/candidate_synergies.json` | 已生成 | 0 条 |
| `pipeline/output/augment_wiki_quality_todo.json` | 新增 | 24 条增强质量补充方案 |
| `pipeline/output/prototype_augments_strategy.md` | 新增 | 13 个 prototype 增强策略报告 |
