# 海克斯乱斗实验室

## 项目简介

海克斯乱斗实验室是一个专注于《英雄联盟》海克斯大乱斗模式的 **英雄 × 增强质变组合数据库**。核心理念不是做一个普通的数据统计站，而是回答每个玩家最关心的问题：**"哪个增强能让哪个英雄产生质变？"**

项目围绕"质变组合"展开所有功能，包括英雄增强协同分析、避雷指南、疑似Bug追踪、以及结构化的玩家投稿系统。所有数据字段都带有版本号、来源、置信度和状态等元数据。

## 技术栈

| 技术 | 说明 |
|------|------|
| HTML / CSS / JavaScript | 纯前端 SPA，数据通过 fetch() 加载 JSON |
| Chart.js 4.4.1 | 数据可视化图表（CDN） |
| Python + PRAW | Reddit 数据采集管道 |
| OpenAI API | AI 结构化提取候选 Bug/组合 |
| Data Dragon | 英雄头像等静态资源 |
| Riot Games API (Match-V5) | 对局数据来源（计划接入） |
| Community Dragon | 增强数据（cherry-augments.json） |

## 功能模块

### 质变组合（核心）
英雄 × 增强协同矩阵，每条数据标注：质变/推荐/避雷/疑似Bug 四个等级。支持搜索、筛选、排序，以及可展开的玩家实测详情。

### 英雄档案
16个英雄的完整档案，展示每个英雄的质变、推荐、避雷、疑似Bug组合分布。点击英雄进入详情弹窗。

### 增强图鉴
16个增强的完整图鉴，展示最佳适配英雄、不推荐英雄、触发机制详解、以及玩家实测结果。

### 玩家投稿
结构化投稿系统，玩家可以选择英雄+增强+类型+评分来提交自己的发现。

### 问题追踪
当前版本已知Bug的结构化追踪，包含涉及英雄/增强、规避建议、关联投稿等信息。

### 候选发现（新增）
AI 从公开论坛自动提取的候选 Bug 和组合数据，标注"未审核，不对外发布"。用于人工审核后将有效数据手动迁入正式数据库。

## 数据元数据标准

每条数据均包含以下元数据：
- **版本号** — 数据来源的游戏版本
- **来源** — 数据分析 / 社区投稿 / 人工标注
- **置信度** — 0-100% 的可靠性评估
- **状态** — 已验证 / 社区验证中 / 争议 / 调查中

## 项目结构

```
aram-insight/
├── index.html                    # 主应用（SPA）
├── data/                         # 正式数据文件
│   ├── champions.json            # 英雄数据（16位）
│   ├── augments.json             # 增强数据（16个）
│   ├── synergies.json            # 英雄×增强组合（31条）
│   ├── reports.json              # 社区投稿（8篇）
│   ├── issues.json               # 问题追踪（6个）
│   └── changelog.json            # 审核变更记录（自动生成）
├── pipeline/                     # 数据采集与清洗管道
│   ├── config/
│   │   ├── keywords.json         # 搜索关键词（中英文）
│   │   ├── sources.json          # 数据源配置
│   │   └── manual_links.json     # 手动收集的链接
│   ├── collectors/
│   │   ├── reddit_collector.py   # Reddit API 采集器
│   │   └── manual_links_collector.py  # 手动链接读取
│   ├── processors/
│   │   ├── clean_text.py         # 文本清洗
│   │   ├── dedupe.py             # 去重
│   │   └── ai_extract.py         # AI 结构化提取
│   ├── output/                   # Pipeline 输出（自动生成）
│   │   ├── raw_reddit_posts.jsonl
│   │   ├── cleaned_items.jsonl
│   │   ├── candidate_bugs.json
│   │   ├── candidate_synergies.json
│   │   └── rejected_candidates.json
│   ├── run_pipeline.py           # 总入口脚本
│   ├── review_candidates.py      # 人工审核工具
│   └── README.md                 # Pipeline 详细文档
├── .env.example                  # 环境变量模板
├── .gitignore
├── scripts/
│   ├── validate_data.py          # 数据校验脚本
│   ├── audit_trust_level.py      # 数据可信度审计报告
│   └── sync_champions.py         # 全英雄同步（Data Dragon）
├── docs/
│   └── review_guidelines.md      # 审核规范文档
└── README.md
```

## 快速开始

### 查看网站

```bash
# 使用本地 HTTP 服务器（fetch() 需要 HTTP 协议）
py -m http.server 8000
# 或
npx serve .
# 然后访问 http://localhost:8000
```

### 数据校验

修改 `data/*.json` 后，建议运行校验脚本确保数据完整性：

```bash
python scripts/validate_data.py
```

校验内容包括：文件存在性、JSON 合法性、必需字段完整性、枚举值合法性、跨文件引用一致性（英雄/增强名称是否存在）。

### 同步全英雄

从 Riot Data Dragon 获取最新版本的全英雄基础数据，与现有 `champions.json` 合并：

```bash
python scripts/sync_champions.py
```

已有英雄的所有字段（wr/pr/games/kda/build/tips）不会被覆盖。新增英雄使用默认结构：tier 为 `unknown`，统计数据为 `null`，前端会显示"暂无真实统计"和"未评级"。写入前自动备份为 `data/champions.backup.json`，写入后自动运行 `validate_data.py` 校验。

### 配置 Pipeline 环境

1. 安装 Python 依赖：

```bash
pip install praw python-dotenv openai
```

2. 复制环境变量模板并填入 API 密钥：

```bash
cp .env.example .env
# 编辑 .env 填入：
# REDDIT_CLIENT_ID — Reddit 应用 ID
# REDDIT_CLIENT_SECRET — Reddit 应用密钥
# REDDIT_USER_AGENT — 用户代理字符串
# OPENAI_API_KEY — OpenAI API 密钥
```

**Reddit API 凭证获取：** 访问 https://www.reddit.com/prefs/apps → 创建 script 类型应用。

### 运行 Pipeline

```bash
# 从 Reddit 采集最近 7 天的帖子
python pipeline/run_pipeline.py --source reddit --days 7 --limit 50

# 处理手动收集的链接
python pipeline/run_pipeline.py --source manual

# 采集所有数据源
python pipeline/run_pipeline.py --source all --days 7 --limit 50

# 跳过 AI 提取步骤
python pipeline/run_pipeline.py --source reddit --days 7 --limit 50 --skip-ai
```

### 查看候选发现

运行 pipeline 后，在网站中点击"候选发现"标签页即可查看 AI 提取的候选数据。所有候选数据均标记为 `needs_review: true`，需人工审核。

### 人工审核候选数据

使用命令行工具逐条审核 AI 提取的候选数据，审核通过后自动写入正式数据文件：

```bash
# 审核所有候选（Bug + 组合）
python pipeline/review_candidates.py

# 仅审核 Bug 候选
python pipeline/review_candidates.py --type bugs

# 仅审核组合候选
python pipeline/review_candidates.py --type synergies
```

每条候选支持六种操作：approve（通过）、reject（拒绝）、skip（跳过）、edit（编辑）、add evidence（补充证据）、quit（退出）。审核通过后自动运行 `validate_data.py` 校验，校验失败自动回滚。无证据的 approve 会强制 status 为 investigating 并将 confidence 封顶 60。详细说明参见 `pipeline/README.md`，审核标准参见 [审核规范](docs/review_guidelines.md)。

### 审核变更记录

每次 approve 成功后，审核工具会自动向 `data/changelog.json` 追加一条记录，包含审核日期、类型（bug/synergy）、标题、英雄、增强、状态、来源和证据数量。网站的"候选发现"页面会自动展示最近 5 条审核记录，便于追溯数据变更历史。changelog 为可选文件，校验脚本仅在其存在时检查格式合法性。

### 小规模 Reddit 测试流程

首次使用时，建议按以下步骤进行一次完整的端到端小规模测试：

1. **配置环境变量**：复制 `.env.example` 为 `.env`，填入 Reddit API 和 OpenAI API 凭证。
2. **运行 Reddit pipeline**（小范围采集）：
   ```bash
   python pipeline/run_pipeline.py --source reddit --days 3 --limit 10
   ```
3. **打开网站**：访问"候选发现"标签页，查看 AI 提取的候选 Bug 和组合数据。
4. **人工审核**：
   ```bash
   python pipeline/review_candidates.py
   ```
   逐条审核，对有效数据执行 approve，无效数据执行 reject。approve 后自动运行 `validate_data.py` 校验。
5. **数据校验**：审核完成后手动确认数据完整性：
   ```bash
   python scripts/validate_data.py
   ```

采集结果仅写入 `pipeline/output/` 目录下的候选文件，不会自动修改 `data/` 下的正式数据文件。只有经过 `review_candidates.py` 人工 approve 后，数据才会写入正式文件。

### 数据可信度审计

对现有数据文件进行只读可信度扫描，识别缺少证据支撑的高可信度声明：

```bash
python scripts/audit_trust_level.py
```

脚本会扫描 `data/synergies.json`、`data/issues.json`、`data/reports.json`，按三级风险分类输出：

| 风险等级 | 触发条件 |
|---------|---------|
| 高风险 | synergies: status=verified 无证据；issues: severity=critical 无证据 |
| 中风险 | synergies: src=data 且 sample>0 无证据；issues: confirm>0 无证据 |
| 低风险 | reports: 描述含数据性关键词（实测/胜率/样本等）无证据 |

脚本为只读模式，不修改任何数据文件。同一数据条目触发多条规则时自动去重合并，保留最高风险等级。建议在每次批量审核或数据变更后运行一次，优先处理高风险条目。

## 数据合规说明

- Reddit 数据通过官方 PRAW API 采集，遵守 Reddit API Terms of Service
- 仅采集公开帖子和评论，不保存私人信息
- 作者信息仅保留公开昵称，可选匿名化
- AI 提取结果全部标记为 `needs_review: true`，需人工审核后方可使用
- AI 不会编造胜率、样本量或官方确认信息
- 所有候选数据 status 默认为 `investigating`
- 不使用浏览器反爬、代理池、验证码绕过等技术

## 数据可信度说明

本项目的所有数据均附带可信度元信息，帮助使用者判断数据的可靠程度。以下是关键概念的解释：

**verified ≠ Riot 官方确认。** 状态为 `verified`（已验证）仅代表该条数据在本项目内部经过了交叉比对或人工复核，并不等同于 Riot Games 的官方认证。游戏机制可能随版本更新发生变化，已验证的数据也可能过期。

**evidence 为空 = 待补充证据。** 当一条数据的 `evidence` 字段为空数组时，表示该条目尚未关联外部证据链接（如 Reddit 讨论帖、数据截图、Riot 官方说明等）。这不代表数据本身有误，只是可信度评估尚有提升空间。

**AI 提取 / 社区投稿数据需人工审核。** 通过 pipeline 自动生成的候选数据（`pipeline/output/` 下的文件）以及标记为 `src: "community"` 的数据，均需要人工审核后方可迁入正式数据库。AI 提取的数据 `needs_review` 字段为 `true`，校验脚本会以 warning（而非 error）的形式提醒审核。

**证据链接将逐步补充。** 当前 MVP 阶段以示例数据和人工整理数据为主。随着 pipeline 采集和人工审核的推进，各条数据的 `evidence` 字段将逐步填入来源链接，提升整体数据可信度。

校验脚本 `scripts/validate_data.py` 同时支持 error 和 warning 两级提示：error 会导致退出码 1（数据不可用），warning 仅作为信息提醒（如"已验证但缺少证据"），不影响退出码。

## 人工审核流程

1. 运行 pipeline 生成 `candidate_bugs.json` 和 `candidate_synergies.json`
2. 在网站"候选发现"页面浏览候选条目
3. 对每个条目判断：
   - **确认有效** → 手动移入 `data/issues.json` 或 `data/synergies.json`，修改 status 和 needs_review
   - **需要更多信息** → 保持现状，补充证据后重新评估
   - **无效/误报** → 从候选文件中删除
4. 定期重新运行 pipeline 获取新数据

## 计划功能

- [ ] 接入 Riot API 数据管道，实现真实对局数据采集和聚合
- [ ] 自动计算英雄×增强组合的胜率变化
- [ ] 用户账号系统
- [ ] 增强组合推荐引擎
- [ ] 版本更新自动检测和通知
- [ ] 后端迁移（FastAPI + PostgreSQL）

## 下一步：后端迁移建议

当数据量增长或需要多人协作审核时，建议迁移到后端架构：

- **后端框架**: Python FastAPI（与现有 pipeline 代码兼容）
- **数据库**: PostgreSQL（结构化查询 + JSONB 字段）
- **API 端点**: REST API 提供数据 CRUD + 审核接口
- **定时任务**: Celery/APScheduler 定期运行 pipeline
- **Riot API 集成**: 接入 Match-V5 API 获取真实对局数据验证候选组合

## 许可证

MIT License

## 免责声明

海克斯乱斗实验室并非由 Riot Games 认可或赞助。本项目中使用的《英雄联盟》相关素材和数据均归 Riot Games 所有。
