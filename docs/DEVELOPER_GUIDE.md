# 海克斯乱斗实验室 — 开发者指南

> 本文档面向项目开发者，涵盖环境搭建、项目架构、数据流、常用命令、VSCode 配置以及当前进度。
> 最后更新：2026-06-15

---

## 1. 项目概述

海克斯乱斗实验室（Hex ARAM Lab）是一个围绕《英雄联盟》海克斯大乱斗模式的数据驱动静态网站。核心问题是回答"哪个增强能让哪个英雄产生质变"。

技术架构为 **纯前端 SPA（单文件 `index.html`）+ JSON 数据文件 + Python 数据处理管道**，无需后端服务器。前端通过 `fetch()` 加载 `data/*.json`，Python 管道负责从外部来源采集、清洗、提取结构化数据，经人工审核后写入正式数据文件。

---

## 2. 开发环境搭建

### 2.1 Python 环境

项目当前使用 **Python 3.14**（Windows），路径为：

```
C:\Users\Shmily\AppData\Local\Python\bin\python3.exe
```

> 建议使用虚拟环境隔离依赖。在 VSCode 终端中执行：

```bash
# 创建虚拟环境（可选但推荐）
python -m venv .venv

# 激活虚拟环境
.venv\Scripts\activate

# 安装依赖
pip install praw python-dotenv openai requests
```

已安装的依赖清单：

| 包名 | 版本 | 用途 |
|------|------|------|
| `praw` | 8.0.0 | Reddit API（PRAW），目前等待 API 审批 |
| `python-dotenv` | 1.2.2 | 加载 `.env` 环境变量 |
| `openai` | 2.41.1 | AI 结构化提取（使用 DeepSeek V4 Flash） |
| `requests` | 2.34.2 | HTTP 请求（部分脚本使用） |

> 管道中大部分脚本（爬虫、校验、审核工具）仅使用 Python 标准库，不依赖第三方包。

### 2.2 环境变量配置

复制 `.env.example` 为 `.env` 并填入 API 密钥：

```bash
cp .env.example .env
```

`.env` 中需要配置的变量：

```ini
# AI 提取用的 DeepSeek API（推荐）
AI_API_KEY=sk-your-key-here
OPENAI_BASE_URL=https://api.deepseek.com
AI_MODEL=deepseek-v4-flash

# Reddit API（等待审批中，暂不需要填写）
REDDIT_CLIENT_ID=
REDDIT_CLIENT_SECRET=
REDDIT_USER_AGENT=script:hextech-aram-lab:v0.1 by u/YOUR_USERNAME
```

### 2.3 VSCode 推荐配置

在项目根目录创建 `.vscode/settings.json`：

```json
{
  "python.defaultInterpreterPath": "C:\\Users\\Shmily\\AppData\\Local\\Python\\bin\\python3.exe",
  "files.encoding": "utf8",
  "editor.tabSize": 2,
  "editor.formatOnSave": true,
  "files.associations": {
    "*.jsonl": "json"
  },
  "python.analysis.extraPaths": [
    "pipeline",
    "scripts"
  ]
}
```

推荐安装的 VSCode 扩展：

| 扩展 | 用途 |
|------|------|
| Python (ms-python.python) | Python 语言支持、调试、Lint |
| JSON (ZainChen.json) | JSON 文件格式化和校验 |
| Live Server (ritwickdey.LiveServer) | 本地 HTTP 服务器预览前端 |
| GitLens | Git 变更追踪 |

### 2.4 启动前端预览

前端 `index.html` 使用 `fetch()` 加载 JSON 文件，需要 HTTP 协议（不能直接 `file://` 打开）：

```bash
# 方法 1：Python 内置服务器
python -m http.server 8000

# 方法 2：npx serve
npx serve .

# 方法 3：VSCode Live Server 扩展（右键 index.html → Open with Live Server）
```

然后访问 `http://localhost:8000`。

---

## 3. 项目架构

### 3.1 完整文件结构

```
aram-insight/
├── index.html                          # 前端 SPA（单文件，含 CSS/JS）
├── .env                                # 环境变量（不提交到 Git）
├── .env.example                        # 环境变量模板
├── .gitignore
├── README.md                           # 项目总体介绍
│
├── data/                               # ★ 正式数据文件（人工维护）
│   ├── champions.json                  #   英雄数据（172 位，含统计）
│   ├── champions.backup.json           #   英雄数据备份（自动生成）
│   ├── augments.json                   #   增强数据（40 个）
│   ├── synergies.json                  #   英雄×增强组合（36 条）
│   ├── reports.json                    #   社区投稿（8 篇）
│   ├── issues.json                     #   问题追踪（9 个）
│   └── changelog.json                  #   审核变更记录（自动追加）
│
├── pipeline/                           # ★ 数据采集管道
│   ├── run_pipeline.py                 #   管道总入口
│   ├── review_candidates.py            #   交互式候选审核工具
│   ├── approve_test.py                 #   审核功能测试
│   ├── config/
│   │   ├── keywords.json               #   搜索关键词（中英文）
│   │   ├── sources.json                #   数据源配置
│   │   └── manual_links.json           #   手动收集的链接（当前第3轮）
│   ├── collectors/
│   │   ├── reddit_collector.py         #   Reddit API 采集器（PRAW）
│   │   ├── manual_links_collector.py   #   手动链接读取器
│   │   └── tieba_collector.py          #   百度贴吧采集器（stdlib，dry-run）
│   ├── processors/
│   │   ├── clean_text.py               #   文本清洗（去 HTML/MD/Bot）
│   │   ├── dedupe.py                   #   去重（精确+模糊）
│   │   ├── ai_extract.py               #   AI 结构化提取（DeepSeek）
│   │   └── normalize_entities.py       #   实体归一化（英雄/增强名称）
│   ├── scripts/
│   │   └── gen_quality_todo.py         #   数据质量待办生成
│   └── output/                         #   管道输出（候选数据，不直接修改 data/）
│       ├── manual_items.jsonl          #     手动链接原始数据
│       ├── cleaned_items.jsonl         #     清洗后数据
│       ├── deduped_items.jsonl         #     去重后数据
│       ├── candidate_bugs.json         #     AI 提取的候选 Bug
│       ├── candidate_synergies.json    #     AI 提取的候选组合
│       ├── chinese_augment_candidates.json  # 中文增强候选（255条）
│       ├── wiki_augments_english.json  #     Wiki 英文增强数据（202条）
│       ├── arammayhem_augment_list.json #    arammayhem.com 中文列表
│       ├── augment_localization_report.md   # 增强本地化分析报告
│       ├── evidence_gap_report.json    #     证据缺口报告（45条）
│       └── ...
│
├── scripts/                            # ★ 独立工具脚本
│   ├── validate_data.py                #   数据校验（ERROR/WARNING）
│   ├── audit_trust_level.py            #   数据可信度审计
│   ├── sync_champions.py              #   全英雄同步（Data Dragon）
│   ├── sync_augments_from_wiki.py     #   增强同步（Wiki Module）
│   ├── fill_augment_fields.py          #   增强字段补全
│   ├── approve_candidate_dev_only.py   #   非交互式审核（安全模式）
│   ├── review_augment_localization.py  #   增强中文名审核工具
│   ├── scrape_arammayhem_zh.py        #   arammayhem.com 中文爬虫
│   ├── merge_chinese_augment_data.py   #   中英文增强数据交叉匹配
│   ├── generate_evidence_gap_report.py #   证据缺口报告生成器
│   ├── generate_localization_todo.py   #   本地化待办生成器
│   ├── generate_warnings_summary.py    #   校验警告摘要
│   ├── merge_selected_augments.py      #   批量导入增强
│   └── check_augment_list.py           #   增强列表快速检查
│
└── docs/
    ├── review_guidelines.md            #   审核规范文档
    └── DEVELOPER_GUIDE.md              #   本文档
```

### 3.2 数据流架构

```
外部来源                    管道处理                       正式数据
──────────               ──────────                    ──────────
Reddit API ──→ raw_reddit_posts.jsonl
                                       ↘
手动链接 ────→ manual_items.jsonl ──→ cleaned_items.jsonl
                                       ↓
百度贴吧 ────→ (tieba raw)          deduped_items.jsonl
                                       ↓
                                   ai_extract.py
                                   (DeepSeek V4 Flash)
                                       ↓
                              ┌─ candidate_bugs.json ──→ review ──→ issues.json
                              └─ candidate_synergies.json ──→ review ──→ synergies.json

arammayhem.com ──→ arammayhem_augment_list.json
                   chinese_augment_candidates.json ──→ review ──→ augments.json

LoL Wiki ──────→ wiki_augments_english.json ──→ (交叉匹配)

Data Dragon ──→ sync_champions.py ──→ champions.json
```

核心原则：**管道输出永远写入 `pipeline/output/`，只有经过人工审核后才写入 `data/` 正式文件。**

---

## 4. 数据文件说明

### 4.1 `data/augments.json` — 增强数据（40 条）

每条记录的关键字段：

```json
{
  "id": "chain_lightning",          // 唯一标识符（snake_case）
  "name": "连锁闪电",               // 显示名称（中文优先）
  "name_en": "Chain Lightning",     // 英文名称
  "tier": "gold",                   // 分级：silver / gold / prismatic
  "status": "active",               // 状态：active / removed / unknown
  "effect": "...",                   // 中文效果描述
  "effect_en": "...",                // 英文效果描述
  "source_status": "prototype",     // 数据来源状态
  "localization_status": "..."      // 本地化状态
}
```

**当前数据状态：**

- 16 个手工创建的原型增强（有完整中文数据+统计）
- 24 个从 Wiki 导入的增强（仅英文数据，缺少中文效果描述）
- 4 个已在 arammayhem.com 标记为已移除但仍为 active

### 4.2 `data/synergies.json` — 英雄×增强组合（36 条）

```json
{
  "hero": "吉格斯",                 // 英雄中文名
  "aug": "连锁闪电",                // 增强名称
  "tier": "transform",             // transform / recommend / avoid
  "status": "verified",            // verified / community / investigating / disputed
  "conf": 95,                      // 置信度 0-100
  "evidence": [...]                // 外部证据链接
}
```

**已知问题：** 33 条记录的 `source_note` 字段存在 Unicode 损坏（`/u5f53` 而非 `\u5f53`），27 条标记为 verified 但无证据。

### 4.3 `data/champions.json` — 英雄数据（172 位）

从 Riot Data Dragon 同步的全英雄基础数据，含胜率、出场率、KDA 等统计字段。

---

## 5. Python 脚本速查手册

### 5.1 管道主入口

| 命令 | 说明 |
|------|------|
| `python pipeline/run_pipeline.py --source reddit --days 7 --limit 50` | 从 Reddit 采集 |
| `python pipeline/run_pipeline.py --source manual` | 处理手动链接 |
| `python pipeline/run_pipeline.py --source tieba --kw "海克斯大乱斗"` | 贴吧采集（dry-run） |
| `python pipeline/run_pipeline.py --source all --days 7 --limit 50` | 全部来源 |
| `python pipeline/run_pipeline.py --source manual --dry-run` | 仅预览，不写候选 |

### 5.2 数据校验和审计

| 命令 | 说明 |
|------|------|
| `python scripts/validate_data.py` | 数据校验（0 error = 通过） |
| `python scripts/audit_trust_level.py` | 可信度审计（三级风险） |
| `python scripts/generate_evidence_gap_report.py` | 证据缺口分析 |
| `python scripts/generate_warnings_summary.py` | 校验警告汇总 |

### 5.3 数据采集工具

| 命令 | 说明 |
|------|------|
| `python scripts/scrape_arammayhem_zh.py --list-only` | 仅抓取中文增强列表 |
| `python scripts/scrape_arammayhem_zh.py --sample 10` | 抓取前10个详情页 |
| `python scripts/merge_chinese_augment_data.py` | 中英文数据交叉匹配 |
| `python scripts/sync_champions.py` | 从 Data Dragon 同步英雄 |
| `python scripts/sync_augments_from_wiki.py` | 从 Wiki 同步增强 |

### 5.4 审核工具

| 命令 | 说明 |
|------|------|
| `python pipeline/review_candidates.py` | 交互式审核候选 Bug/组合 |
| `python scripts/approve_candidate_dev_only.py` | 非交互式安全审核 |
| `python scripts/review_augment_localization.py` | 增强中文名审核 |
| `python scripts/review_augment_localization.py --dry-run` | 中文名审核预览 |

---

## 6. VSCode 开发工作流

### 6.1 日常开发循环

```
1. 修改代码/数据
   ↓
2. 运行校验：python scripts/validate_data.py
   ↓
3. 启动前端预览：python -m http.server 8000
   ↓
4. 浏览器访问 http://localhost:8000 查看效果
   ↓
5. git add / git commit
```

### 6.2 调试管道

在 VSCode 中调试 `run_pipeline.py`：

创建 `.vscode/launch.json`：

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Pipeline (manual)",
      "type": "python",
      "request": "launch",
      "program": "pipeline/run_pipeline.py",
      "args": ["--source", "manual", "--dry-run"],
      "cwd": "${workspaceFolder}",
      "envFile": "${workspaceFolder}/.env",
      "console": "integratedTerminal"
    },
    {
      "name": "Pipeline (tieba dry-run)",
      "type": "python",
      "request": "launch",
      "program": "pipeline/run_pipeline.py",
      "args": ["--source", "tieba", "--kw", "海克斯大乱斗", "--limit", "10", "--dry-run"],
      "cwd": "${workspaceFolder}",
      "envFile": "${workspaceFolder}/.env",
      "console": "integratedTerminal"
    },
    {
      "name": "Validate Data",
      "type": "python",
      "request": "launch",
      "program": "scripts/validate_data.py",
      "cwd": "${workspaceFolder}",
      "console": "integratedTerminal"
    },
    {
      "name": "Review Candidates",
      "type": "python",
      "request": "launch",
      "program": "pipeline/review_candidates.py",
      "cwd": "${workspaceFolder}",
      "envFile": "${workspaceFolder}/.env",
      "console": "integratedTerminal"
    }
  ]
}
```

### 6.3 常用 VSCode 快捷键

| 快捷键 | 用途 |
|--------|------|
| `Ctrl+`` | 打开集成终端 |
| `Ctrl+Shift+P` → "Python: Select Interpreter" | 切换 Python 解释器 |
| `Ctrl+Shift+B` | 运行构建任务 |
| `F5` | 启动调试（使用 launch.json 配置） |
| `Ctrl+Shift+M` | 打开问题面板（查看 JSON 校验错误） |

---

## 7. 数据安全规则

这些规则贯穿整个项目的所有脚本和操作流程，**必须严格遵守**：

### 7.1 数据写入保护

| 规则 | 说明 |
|------|------|
| 管道输出 → `pipeline/output/` | 所有采集/提取结果先写入输出目录 |
| 人工审核后才写入 `data/` | 必须通过审核工具 approve |
| 写入前自动备份 | 审核脚本会先备份目标 JSON 文件 |
| 写入后自动校验 | 校验失败自动回滚到备份 |
| 不直接编辑正式数据 | 禁止手动修改 `data/*.json`（除非通过脚本） |

### 7.2 禁止操作

- **不要删除现有增强** — 只能修改状态为 removed
- **不要让 AI 自由翻译中文名** — 使用 arammayhem.com 等官方来源
- **不要自动 approve** — 所有候选必须人工审核
- **不要修改 `data/synergies.json`、`data/issues.json`、`data/reports.json`** — 这些文件有复杂的关联关系
- **不要保存用户名或个人信息** — 仅采集公开数据
- **不要调用 Reddit API**（等待审批中）
- **不使用反爬/代理池/验证码绕过**

### 7.3 审核通过后的自动处理

每次 approve 后自动执行：

1. 备份目标 JSON 文件
2. 写入新数据
3. 运行 `validate_data.py`
4. 运行 `normalize_entities.py` 测试
5. 写入 `data/changelog.json` 审核记录
6. 如果校验失败，自动回滚到备份

---

## 8. 当前项目状态

### 8.1 Git 历史

```
b4d49b2  Add Chinese augment name crawler and localization data from arammayhem.com
547ab8e  Add localization review script, evidence gap report, and tieba collector
ae7fc52  Round 3 manual links validation and augment quality improvement
acdf035  Implement Reddit read-only collector with dry-run pipeline support
53b1414  Data quality convergence and second round manual pipeline verification
c1c0ada  Add real augment batch and validate manual AI pipeline
```

### 8.2 已完成的工作

| 模块 | 状态 | 说明 |
|------|------|------|
| 前端 SPA | ✅ 基础完成 | 质变组合、英雄档案、增强图鉴、投稿、问题追踪、候选发现 |
| 数据校验 | ✅ 完成 | 0 errors, 106 warnings |
| 手动链接管道 | ✅ 完成 | 3 轮采集（30 条手动链接） |
| Reddit 采集器 | ⏳ 等待 API | PRAW 代码已就绪，等待 Reddit 审批 |
| 贴吧采集器 | ⚠️ dry-run | stdlib 实现，实际请求返回 403 |
| AI 提取 | ✅ 完成 | DeepSeek V4 Flash，结构化提取 Bug/组合 |
| 中文增强爬虫 | ✅ 完成 | arammayhem.com 255 条中文名称 |
| 中文名审核工具 | ✅ 完成 | 交互式 CLI，支持 approve/edit/skip |
| 证据缺口分析 | ✅ 完成 | 45 条缺口已识别 |
| 增强本地化待办 | ✅ 完成 | 24 条待补充 |

### 8.3 待处理的关键问题

| 优先级 | 问题 | 影响 | 建议操作 |
|--------|------|------|----------|
| P0 | 24 个增强缺少中文效果描述 | 前端显示不完整 | 运行审核工具逐个补充 |
| P0 | 4 个增强应标记为 removed | 数据准确性 | 修改 `status` 字段 |
| P1 | 33 条 synergies 的 Unicode 损坏 | source_note 乱码 | 批量修复 `/u` → `\u` |
| P1 | 27 条 verified 但无证据 | 可信度虚高 | 降级为 investigating 或补充证据 |
| P1 | big_brain 效果描述完全错误 | 数据准确性 | 用 Wiki 数据替换 |
| P2 | 前端硬编码英文标签 | 用户体验 | 前端国际化 |
| P2 | 缺少原型过滤器 | 原型增强混入正式数据 | 前端增加 prototype 标签 |
| P3 | 约 158 个增强未收录 | 数据覆盖不全 | 从 arammayhem.com 批量导入 |
| P3 | Reddit API 等待审批 | 无法采集 Reddit 数据 | 等待审批后启用 |
| P3 | 几乎无测试覆盖 | 代码质量风险 | 添加单元测试 |

---

## 9. 快速上手指南

### 场景 A：我想查看当前数据质量

```bash
# 1. 数据校验
python scripts/validate_data.py

# 2. 可信度审计
python scripts/audit_trust_level.py

# 3. 证据缺口
python scripts/generate_evidence_gap_report.py
# 查看 pipeline/output/evidence_gap_report.json
```

### 场景 B：我想给增强补充中文名

```bash
# 1. 先预览有哪些增强需要中文名
python scripts/review_augment_localization.py --dry-run

# 2. 逐个审核（approve/edit/skip）
python scripts/review_augment_localization.py

# 3. 校验
python scripts/validate_data.py
```

### 场景 C：我想运行数据采集管道

```bash
# 1. 用手动链接测试（无需 API）
python pipeline/run_pipeline.py --source manual

# 2. 查看 AI 提取结果
# pipeline/output/candidate_bugs.json
# pipeline/output/candidate_synergies.json

# 3. 审核候选数据
python pipeline/review_candidates.py
```

### 场景 D：我想抓取更多中文增强数据

```bash
# 1. 抓取中文增强列表（仅列表页，约 2 秒）
python scripts/scrape_arammayhem_zh.py --list-only

# 2. 交叉匹配中英文数据
python scripts/merge_chinese_augment_data.py

# 3. 查看分析报告
# pipeline/output/augment_localization_report.md
```

### 场景 E：我想在前端看到效果

```bash
# 1. 启动本地服务器
python -m http.server 8000

# 2. 打开浏览器访问 http://localhost:8000
# 导航到各标签页查看数据展示
```

---

## 10. 故障排除

### 问题：`UnicodeEncodeError: 'charmap' codec`

Windows 终端默认编码不是 UTF-8。解决方案：

```bash
# 方法 1：设置环境变量
set PYTHONIOENCODING=utf-8
python your_script.py

# 方法 2：在脚本开头添加
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
```

### 问题：`fetch()` 加载 JSON 失败

直接双击 `index.html` 打开时，浏览器使用 `file://` 协议，不允许 `fetch()` 加载本地文件。必须通过 HTTP 服务器访问。

### 问题：贴吧采集器返回 403

这是预期行为。百度贴吧对简单 HTTP 请求有反爬机制。`tieba_collector.py` 会优雅降级，记录警告并返回空列表。如需真实采集贴吧数据，需使用浏览器自动化。

### 问题：AI 提取将大部分内容分类为 general_discussion

DeepSeek 模型对中文综合性攻略帖倾向于分类为 general_discussion（因为内容涵盖多个话题而非单一 Bug/组合）。这是已知限制，可通过优化 SYSTEM_PROMPT 或拆分子话题来改善。

### 问题：validate_data.py 报告 106 个 warnings

这是当前已知状态，主要是：已验证但缺少证据的条目、needs_review 标记的候选等。不影响数据可用性（exit code 0）。随着证据补充和审核推进，warning 数量会逐步减少。

---

## 11. 项目约定

### 11.1 命名规范

- 数据文件中的增强 `id`：`snake_case`（如 `chain_lightning`）
- 英雄名称：使用中文（如 `吉格斯`，不用 `Ziggs`）
- 增强名称：`name` 字段优先中文，`name_en` 字段存英文
- Python 脚本：`snake_case.py`
- JSON 字段：`snake_case`

### 11.2 分级体系

| 级别 | 英文 | 说明 |
|------|------|------|
| 银色 | Silver | 基础增强 |
| 金色 | Gold | 中等增强 |
| 棱彩 | Prismatic | 最高级增强 |

> 注意：`tier` 字段使用 `prismatic`，旧的 `rar` 字段使用 `prism`，两者共存于数据中。

### 11.3 状态枚举

| 状态 | 适用范围 | 说明 |
|------|----------|------|
| `active` | 增强 | 当前版本可用 |
| `removed` | 增强 | 已从游戏移除 |
| `unknown` | 增强 | 状态未知 |
| `verified` | 组合/问题 | 已交叉验证 |
| `community` | 组合/问题 | 社区验证中 |
| `investigating` | 组合/问题 | 调查中（默认） |
| `disputed` | 组合/问题 | 存在争议 |
| `fixed` | 问题 | 已修复 |

---

## 12. 下一步建议

如果你是刚接手这个项目的开发者，建议按以下顺序推进：

1. **先跑通全流程**：按"场景 A"运行校验和审计，了解数据现状
2. **启动前端预览**：`python -m http.server 8000`，浏览各页面
3. **审核一批中文名**：运行 `review_augment_localization.py --dry-run` 预览
4. **修复已知 Bug**：处理 4 个应标记为 removed 的增强
5. **补充证据**：为 verified 但无证据的组合补充来源链接
6. **等待 Reddit API**：审批通过后运行完整管道

详细的审核标准参见 [`docs/review_guidelines.md`](review_guidelines.md)。
