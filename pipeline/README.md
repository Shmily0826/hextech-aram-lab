# 海克斯乱斗实验室 — 数据采集 Pipeline

本地数据采集与清洗管道，用于从 Reddit 等公开论坛收集 LOL ARAM Mayhem / 海克斯大乱斗相关讨论，提取潜在 Bug、避雷组合、质变组合，经 AI 总结后生成候选 JSON 文件供人工审核。

## 目录结构

```
pipeline/
  config/
    keywords.json        # 搜索关键词（中英文）
    sources.json         # 数据源配置（Reddit 子版块等）
    manual_links.json    # 手动收集的链接
  collectors/
    reddit_collector.py  # Reddit API 采集器（使用 PRAW）
    manual_links_collector.py  # 手动链接读取器
  processors/
    clean_text.py        # 文本清洗（去 HTML/Markdown/Bot）
    dedupe.py            # 去重（URL/ID/标题相似度）
    ai_extract.py        # AI 结构化提取（使用 OpenAI API）
  output/                # 输出目录（自动生成，不提交到版本库）
    raw_reddit_posts.jsonl
    manual_items.jsonl
    cleaned_items.jsonl
    candidate_bugs.json
    candidate_synergies.json
    rejected_candidates.json   # 被拒绝的候选（自动生成）
  run_pipeline.py        # 总入口脚本
  review_candidates.py   # 人工审核工具
```

## 环境配置

### 1. 安装依赖

```bash
pip install praw python-dotenv openai
```

### 2. 配置 .env

复制项目根目录的 `.env.example` 为 `.env`，填入你的 API 密钥：

```bash
cp .env.example .env
# 编辑 .env 填入：
# REDDIT_CLIENT_ID=...
# REDDIT_CLIENT_SECRET=...
# REDDIT_USER_AGENT=...
# OPENAI_API_KEY=...
```

**Reddit API 凭证获取方法：**
1. 访问 https://www.reddit.com/prefs/apps
2. 点击 "create another app..."
3. 选择 "script" 类型
4. redirect uri 填 `http://localhost:8080`
5. 创建后获取 client_id 和 client_secret

## 运行 Pipeline

### 从 Reddit 采集

```bash
python pipeline/run_pipeline.py --source reddit --days 7 --limit 50
```

### 处理手动链接

```bash
python pipeline/run_pipeline.py --source manual
```

### 全部数据源

```bash
python pipeline/run_pipeline.py --source all --days 7 --limit 50
```

### 跳过 AI 提取

```bash
python pipeline/run_pipeline.py --source reddit --days 7 --limit 50 --skip-ai
```

## 查看候选发现

运行 pipeline 后，在网站中点击"候选发现"标签页即可查看 AI 提取的候选数据。

如果未运行过 pipeline，页面会显示"暂无候选数据，请先运行 pipeline"。

## 数据合规说明

- Reddit 数据通过官方 PRAW API 采集，遵守 Reddit API Terms of Service
- 仅采集公开帖子和评论，不保存私人信息
- 作者信息仅保留公开昵称，可选匿名化
- AI 提取结果全部标记为 `needs_review: true`，需人工审核后方可使用
- AI 不会编造胜率、样本量或官方确认信息
- 所有候选数据 status 默认为 `investigating`

## 人工审核流程

### 推荐审核流程

1. 运行 pipeline 生成候选数据文件
2. 使用 `review_candidates.py` 命令行工具逐条审核
3. 审核通过的条目自动写入正式数据并触发校验
4. 审核拒绝的条目记录到 `rejected_candidates.json`
5. 定期重新运行 pipeline 获取新数据

### 运行审核工具

```bash
# 审核所有候选数据（Bug + 组合）
python pipeline/review_candidates.py

# 仅审核 Bug 候选
python pipeline/review_candidates.py --type bugs

# 仅审核组合候选
python pipeline/review_candidates.py --type synergies
```

### 操作说明

审核工具逐条展示候选数据的详细信息，包括标题、描述、涉及英雄/增强、证据链接等。对每条候选可以执行以下操作：

| 快捷键 | 操作 | 说明 |
|--------|------|------|
| `a` | approve | 审核通过，写入正式数据文件 |
| `r` | reject | 拒绝，记录到 rejected_candidates.json |
| `s` | skip | 跳过，保留在候选文件中下次审核 |
| `e` | edit | 编辑候选字段（标题、描述、状态、置信度等） |
| `v` | add evidence | 补充证据链接（类型/URL/摘要） |
| `q` | quit | 退出审核，已处理的条目已保存 |

### 审核通过后的处理

- **Bug 候选** → 写入 `data/issues.json`，字段自动映射（severity→sev, champions→heroes 等）
- **组合候选** → 写入 `data/synergies.json`，字段自动映射（rating_type→tier, trap_warning→avoid）
- 自动设置 `needs_review: false`，`updated_at` 为当前时间
- 如果 evidence 为空，自动添加 source_note 说明
- 每次写入后自动运行 `scripts/validate_data.py`，校验失败则自动回滚

### 空证据保护机制

当候选没有证据链接时用户仍选择 approve，审核工具会自动执行以下保护：

- `status` 强制设为 `investigating`（即使用户编辑为其他状态）
- `confidence` 若高于 60 则自动降至 60
- `source_note` 标注"该条目暂无外部证据链接，需继续验证"

这确保了无证据的条目不会被标记为已验证或高置信度。详细审核标准参见 [审核规范文档](../docs/review_guidelines.md)。

### 去重机制

- `issues.json`：如果已有相同 `title` 的条目，自动跳过
- `synergies.json`：如果已有相同 `hero + aug + tier` 的条目，自动跳过

### 注意事项

- AI 候选数据**不会**自动发布到正式数据库，必须经过人工审核
- 审核通过的条目默认 status 为 `investigating`，建议审核后视情况修改
- 无证据的 approve 会触发空证据保护（status 强制 investigating，confidence 封顶 60）
- 建议先使用 `v` 补充证据后再 approve，以保留原始 status 和 confidence
- 被拒绝的条目保留在 `rejected_candidates.json` 中供追溯

## 下一步：迁移到后端

当数据量增长或需要多人协作审核时，建议迁移到后端架构：

- **后端框架**: Python FastAPI（与现有 pipeline 代码兼容）
- **数据库**: PostgreSQL（结构化查询）或 MongoDB（灵活的 JSON 文档）
- **API 端点**: REST API 提供数据 CRUD + 审核接口
- **定时任务**: Celery/APScheduler 定期运行 pipeline
- **Riot API 集成**: 接入 Match-V5 API 获取真实对局数据验证候选组合
