"""
AI 候选提取处理器 (AI Candidate Extraction Processor)

从 cleaned_items.jsonl 读取已清洗/去重的条目，使用 LLM (OpenAI API 或兼容接口)
提取结构化的候选 Bug 和协同效应(synergy)信息。

输入: pipeline/output/cleaned_items.jsonl
输出: pipeline/output/candidate_bugs.json
      pipeline/output/candidate_synergies.json
"""

import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# 导入实体名称标准化模块
from pipeline.processors.normalize_entities import (
    normalize_champion_name, normalize_champion_list,
    normalize_augment_name, normalize_augment_list,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 尝试加载 .env 文件中的环境变量（python-dotenv 可选依赖）
# ---------------------------------------------------------------------------
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # python-dotenv 未安装时，手动尝试读取 .env 文件
    _env_path = Path(__file__).resolve().parent.parent.parent / ".env"
    if _env_path.is_file():
        with open(_env_path, encoding="utf-8") as _f:
            for _line in _f:
                _line = _line.strip()
                if _line and not _line.startswith("#") and "=" in _line:
                    _key, _, _val = _line.partition("=")
                    os.environ.setdefault(_key.strip(), _val.strip().strip("'\""))

# ---------------------------------------------------------------------------
# OpenAI 库导入检查
# ---------------------------------------------------------------------------
try:
    from openai import OpenAI
except ImportError:
    print("[错误] 缺少 openai 库，请运行: pip install openai")
    sys.exit(1)

# ============================================================================
# AI 系统提示词 (System Prompt)
# ============================================================================
SYSTEM_PROMPT = """你是一个专业的游戏数据分析 AI，专门处理来自 Reddit、论坛、视频评论等来源的玩家反馈数据。
你的任务是对每条玩家反馈进行分类和结构化信息提取。

## 分类规则

将每条数据分类为以下类型之一：
- bug_report: 玩家报告了游戏中的 Bug（技能异常、数值错误、交互问题等）
- synergy_claim: 玩家声称某个英雄+强化符文组合特别强或特别弱
- trap_warning: 玩家警告某个看似强力但实际有陷阱/坑的组合
- general_discussion: 一般性讨论，不包含具体的 Bug 报告或协同效应声明
- irrelevant: 与游戏机制无关的内容（闲聊、 memes、赛事讨论等）

## 提取规则

**仅对 bug_report、synergy_claim、trap_warning 三种类型提取信息。**
对于 general_discussion 和 irrelevant，仅返回 {"classification": "<类型>", "skip": true}。

### 通用提取字段：
- champions: 涉及的英雄列表（数组）。如果不明确，使用 ["unknown"]
- augments: 涉及的强化符文列表（数组）。如果不明确，使用 ["unknown"]
- description: 简洁的中文描述，概括玩家反馈的核心内容
- trigger: 触发条件或场景描述（如"在3-2选择XX强化后使用XX技能"）
- severity: 严重程度 - "minor"(轻微), "major"(重要), "critical"(严重/影响游戏平衡)
- confidence: 置信度评分，严格按以下标准：
  - 30-50: 单一玩家反馈，无额外证据
  - 50-70: 多条评论/多个玩家提及相同问题
  - 70-85: 有视频、截图或可复现步骤
  - 85-95: 官方声明或开发者确认

### Bug Report 额外字段：
- title: 简短标题，概括 Bug 内容

### Synergy / Trap 额外字段：
- hero: 主要英雄名称（字符串，非数组）
- augment: 主要强化符文名称（字符串，非数组）
- rating_type: "transform"(质变/极强), "recommend"(推荐), "avoid"(避免/陷阱)

## 绝对禁止事项

1. **绝对不要编造数据** — 如果英雄或强化符文名称不明确，必须使用 "unknown"
2. **绝对不要输出胜率、样本量或验证结论** — 这些由后续流程处理
3. **绝对不要在 JSON 之外输出任何文字** — 你的完整输出必须是且仅是一个合法 JSON 对象
4. **不要猜测** — 只根据提供的文本内容提取信息

## 输出格式

对于 bug_report：
```json
{
  "classification": "bug_report",
  "skip": false,
  "title": "...",
  "champions": ["..."],
  "augments": ["..."],
  "description": "...",
  "trigger": "...",
  "severity": "minor|major|critical",
  "confidence": 40
}
```

对于 synergy_claim 或 trap_warning：
```json
{
  "classification": "synergy_claim|trap_warning",
  "skip": false,
  "hero": "...",
  "augment": "...",
  "rating_type": "transform|recommend|avoid",
  "champions": ["..."],
  "augments": ["..."],
  "description": "...",
  "trigger": "...",
  "severity": "minor|major|critical",
  "confidence": 40
}
```

对于 general_discussion 或 irrelevant：
```json
{
  "classification": "general_discussion|irrelevant",
  "skip": true
}
```"""

# ============================================================================
# 用户消息模板
# ============================================================================
USER_MESSAGE_TEMPLATE = """请分析以下玩家反馈数据并提取结构化信息：

---
来源: {source}
标题: {title}
内容:
{content}

链接: {url}
时间: {timestamp}
---

请严格按照系统提示中的规则进行分类和信息提取，只输出 JSON。"""


# ============================================================================
# 核心函数
# ============================================================================

def _get_default_model() -> str:
    """从环境变量获取默认模型名，fallback 到 deepseek-v4-flash。"""
    return os.environ.get("AI_MODEL", "deepseek-v4-flash").strip()


def _create_client() -> OpenAI:
    """创建 OpenAI 兼容客户端，从环境变量加载配置。"""
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        api_key = os.environ.get("AI_API_KEY", "").strip()
    base_url = os.environ.get("OPENAI_BASE_URL", "").strip()

    if not api_key:
        print("[错误] 未设置 OPENAI_API_KEY 或 AI_API_KEY 环境变量。")
        print("       请在项目根目录的 .env 文件中设置 AI_API_KEY，")
        print("       或者通过环境变量导出: export AI_API_KEY=sk-xxx")
        print("       如果使用兼容 API，同时设置 OPENAI_BASE_URL。")
        sys.exit(1)

    kwargs: Dict[str, Any] = {"api_key": api_key}
    if base_url:
        kwargs["base_url"] = base_url
        print(f"[信息] 使用自定义 API 地址: {base_url}")

    return OpenAI(**kwargs)


def _build_user_message(item: Dict[str, Any]) -> str:
    """根据 cleaned item 构造发送给 AI 的用户消息。"""
    return USER_MESSAGE_TEMPLATE.format(
        source=item.get("source", "unknown"),
        title=item.get("title", "(无标题)"),
        content=item.get("content", item.get("text", item.get("body", "(无内容)"))),
        url=item.get("url", item.get("permalink", "N/A")),
        timestamp=item.get("created_at", item.get("timestamp", "N/A")),
    )


def _call_ai(
    client: OpenAI,
    model: str,
    item: Dict[str, Any],
    max_retries: int = 3,
) -> Optional[Dict[str, Any]]:
    """
    调用 AI API 并解析返回的 JSON。
    失败时最多重试 max_retries 次，返回 None 表示彻底失败。
    """
    user_message = _build_user_message(item)

    for attempt in range(1, max_retries + 1):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_message},
                ],
                temperature=0.1,  # 低温度以保证输出稳定、遵循格式
                max_tokens=1024,
            )
            raw_text = response.choices[0].message.content.strip()

            # 去除可能的 markdown 代码块包裹
            if raw_text.startswith("```"):
                # 移除首行 ```json 或 ```
                first_newline = raw_text.index("\n") if "\n" in raw_text else 3
                raw_text = raw_text[first_newline + 1:]
                if raw_text.endswith("```"):
                    raw_text = raw_text[:-3]
                raw_text = raw_text.strip()

            parsed = json.loads(raw_text)
            return parsed

        except json.JSONDecodeError as e:
            print(f"  [警告] AI 返回了无效 JSON (尝试 {attempt}/{max_retries}): {e}")
            logger.warning("AI 返回无效 JSON (尝试 %d/%d): %s", attempt, max_retries, e)
            if attempt < max_retries:
                wait = 2 ** attempt
                print(f"         等待 {wait} 秒后重试...")
                time.sleep(wait)
        except Exception as e:
            print(f"  [错误] API 调用失败 (尝试 {attempt}/{max_retries}): {e}")
            logger.error("API 调用失败 (尝试 %d/%d): %s", attempt, max_retries, e)
            if attempt < max_retries:
                wait = 2 ** attempt
                print(f"         等待 {wait} 秒后重试...")
                time.sleep(wait)

    # 所有重试均失败
    print(f"  [跳过] 条目处理失败，已跳过: {item.get('title', item.get('url', '?'))[:60]}")
    return None


def _now_iso() -> str:
    """返回当前 UTC 时间的 ISO 8601 字符串。"""
    return datetime.now(timezone.utc).isoformat()


def _build_bug_candidate(item: Dict[str, Any], ai_result: Dict[str, Any], ts: str, idx: int) -> Dict[str, Any]:
    """将 AI 提取结果转为 candidate_bugs 格式。"""
    return {
        "candidate_id": f"bug_{ts}_{idx}",
        "type": "bug_report",
        "title": ai_result.get("title", ai_result.get("description", "未命名 Bug")[:80]),
        "champions": ai_result.get("champions", ["unknown"]),
        "augments": ai_result.get("augments", ["unknown"]),
        "description": ai_result.get("description", ""),
        "trigger": ai_result.get("trigger", ""),
        "evidence": [
            {
                "source": item.get("source", "unknown"),
                "url": item.get("url", item.get("permalink", "")),
                "summary": ai_result.get("description", ""),
            }
        ],
        "patch": item.get("patch", "unknown"),
        "severity": ai_result.get("severity", "major"),
        "status": "investigating",
        "confidence": ai_result.get("confidence", 40),
        "needs_review": True,
        "created_at": _now_iso(),
    }


def _build_synergy_candidate(item: Dict[str, Any], ai_result: Dict[str, Any], ts: str, idx: int) -> Dict[str, Any]:
    """将 AI 提取结果转为 candidate_synergies 格式。"""
    item_type = ai_result.get("classification", "synergy_claim")
    return {
        "candidate_id": f"syn_{ts}_{idx}",
        "type": item_type,
        "hero": ai_result.get("hero", "unknown"),
        "augment": ai_result.get("augment", "unknown"),
        "rating_type": ai_result.get("rating_type", "recommend"),
        "description": ai_result.get("description", ""),
        "trigger": ai_result.get("trigger", ""),
        "evidence": [
            {
                "source": item.get("source", "unknown"),
                "url": item.get("url", item.get("permalink", "")),
                "summary": ai_result.get("description", ""),
            }
        ],
        "patch": item.get("patch", "unknown"),
        "status": "investigating",
        "confidence": ai_result.get("confidence", 40),
        "needs_review": True,
        "created_at": _now_iso(),
    }


def _read_items(input_path: Path) -> List[Dict[str, Any]]:
    """逐行读取 JSONL 文件。"""
    items = []
    with open(input_path, encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                items.append(json.loads(line))
            except json.JSONDecodeError:
                print(f"  [警告] 第 {line_no} 行 JSON 解析失败，已跳过")
                logger.warning("JSONL 第 %d 行解析失败，已跳过", line_no)
    return items


# ============================================================================
# 主提取函数（公开 API）
# ============================================================================

def extract_candidates(
    input_path: Any,  # str | Path
    output_dir: Any,  # str | Path
    model: str = "",
    batch_size: int = 10,
    rate_limit_delay: float = 1.0,
    max_retries: int = 3,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    读取 cleaned_items.jsonl，调用 AI 提取候选 Bug 和协同效应。

    Args:
        input_path: 输入的 JSONL 文件路径
        output_dir: 输出目录路径
        model: 模型名称（默认从 AI_MODEL 环境变量读取，fallback deepseek-v4-flash）
        batch_size: 每批次处理的条目数（用于日志输出）
        rate_limit_delay: API 调用之间的等待秒数（限速）
        max_retries: API 失败时的最大重试次数

    Returns:
        (candidate_bugs, candidate_synergies) 元组
    """
    input_path = Path(input_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if not model:
        model = _get_default_model()

    # 检查输入文件
    if not input_path.is_file():
        print(f"[错误] 输入文件不存在: {input_path}")
        return [], []

    # 创建 OpenAI 客户端（API Key 缺失时会自动退出）
    client = _create_client()

    # 读取所有条目
    items = _read_items(input_path)
    total = len(items)
    if total == 0:
        print("[信息] 输入文件为空，无需处理。")
        return [], []

    print(f"[信息] 共读取 {total} 条记录，模型: {model}，批次大小: {batch_size}")
    print(f"[信息] API 调用间隔: {rate_limit_delay}s，最大重试: {max_retries} 次")
    print("-" * 60)

    # 用于生成 candidate_id 的时间戳
    run_ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")

    candidate_bugs: List[Dict[str, Any]] = []
    candidate_synergies: List[Dict[str, Any]] = []
    bug_idx = 0
    syn_idx = 0
    skipped_count = 0
    irrelevant_count = 0

    for i, item in enumerate(items):
        item_num = i + 1
        item_title = item.get("title", item.get("url", "(无标题)"))[:50]

        # 批次分隔日志
        if i % batch_size == 0:
            batch_no = i // batch_size + 1
            total_batches = (total + batch_size - 1) // batch_size
            print(f"\n[批次 {batch_no}/{total_batches}] 处理条目 {item_num}-{min(item_num + batch_size - 1, total)}")

        print(f"  [{item_num}/{total}] {item_title} ...", end=" ", flush=True)

        # 调用 AI
        ai_result = _call_ai(client, model, item, max_retries=max_retries)

        if ai_result is None:
            skipped_count += 1
            print("失败")
            # 限速：即使失败也等待，避免疯狂重试
            time.sleep(rate_limit_delay)
            continue

        classification = ai_result.get("classification", "irrelevant")
        should_skip = ai_result.get("skip", False)

        if should_skip or classification in ("general_discussion", "irrelevant"):
            irrelevant_count += 1
            print(f"跳过 ({classification})")
            time.sleep(rate_limit_delay)
            continue

        # 标准化英雄名称（英 → 中）
        if classification == "bug_report":
            raw_champions = ai_result.get("champions", ["unknown"])
            if isinstance(raw_champions, list):
                ai_result["champions"] = normalize_champion_list(raw_champions)
            else:
                ai_result["champions"] = [normalize_champion_name(str(raw_champions))]
        elif classification in ("synergy_claim", "trap_warning"):
            raw_hero = ai_result.get("hero", "unknown")
            ai_result["hero"] = normalize_champion_name(str(raw_hero))

        # 标准化增强名称（英 → 中）
        if classification == "bug_report":
            raw_augments = ai_result.get("augments", ["unknown"])
            if isinstance(raw_augments, list):
                ai_result["augments"] = normalize_augment_list(raw_augments)
            else:
                ai_result["augments"] = [normalize_augment_name(str(raw_augments))]
        elif classification in ("synergy_claim", "trap_warning"):
            raw_augment = ai_result.get("augment", "unknown")
            ai_result["augment"] = normalize_augment_name(str(raw_augment))
            # 同步标准化 augments 数组
            raw_augments = ai_result.get("augments", ["unknown"])
            if isinstance(raw_augments, list):
                ai_result["augments"] = normalize_augment_list(raw_augments)
            else:
                ai_result["augments"] = [normalize_augment_name(str(raw_augments))]

        # 根据分类构造候选项
        if classification == "bug_report":
            bug = _build_bug_candidate(item, ai_result, run_ts, bug_idx)
            candidate_bugs.append(bug)
            bug_idx += 1
            print(f"Bug (confidence={bug['confidence']})")
        elif classification in ("synergy_claim", "trap_warning"):
            syn = _build_synergy_candidate(item, ai_result, run_ts, syn_idx)
            candidate_synergies.append(syn)
            syn_idx += 1
            print(f"Synergy [{classification}] (confidence={syn['confidence']})")
        else:
            # 未知分类，当作跳过
            irrelevant_count += 1
            print(f"跳过 (未知分类: {classification})")

        # 限速：每次 API 调用后等待
        time.sleep(rate_limit_delay)

    # ---- 写入输出文件 ----
    bugs_path = output_dir / "candidate_bugs.json"
    syns_path = output_dir / "candidate_synergies.json"

    with open(bugs_path, "w", encoding="utf-8") as f:
        json.dump(candidate_bugs, f, ensure_ascii=False, indent=2)
    print(f"\n[输出] 候选 Bug: {len(candidate_bugs)} 条 -> {bugs_path}")

    with open(syns_path, "w", encoding="utf-8") as f:
        json.dump(candidate_synergies, f, ensure_ascii=False, indent=2)
    print(f"[输出] 候选协同/陷阱: {len(candidate_synergies)} 条 -> {syns_path}")

    # ---- 统计摘要 ----
    print("-" * 60)
    print(f"[统计] 总计: {total} | Bug: {len(candidate_bugs)} | "
          f"协同/陷阱: {len(candidate_synergies)} | "
          f"跳过(无关): {irrelevant_count} | 失败: {skipped_count}")
    logger.info(
        "提取完成: 总计 %d 条, Bug %d, 协同/陷阱 %d, 跳过 %d, 失败 %d",
        total, len(candidate_bugs), len(candidate_synergies), irrelevant_count, skipped_count,
    )

    return candidate_bugs, candidate_synergies


# ============================================================================
# 命令行入口
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="AI 候选提取处理器 - 从 cleaned_items.jsonl 提取结构化 Bug 和协同效应"
    )
    parser.add_argument(
        "--input",
        type=str,
        default=None,
        help="输入 JSONL 文件路径 (默认: pipeline/output/cleaned_items.jsonl)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="输出目录 (默认: pipeline/output/)",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="",
        help="模型名称 (默认从 AI_MODEL 环境变量读取，fallback: deepseek-v4-flash)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=10,
        help="每批次处理的条目数，用于日志分组 (默认: 10)",
    )
    parser.add_argument(
        "--rate-limit",
        type=float,
        default=1.0,
        help="API 调用之间的等待秒数，用于限速 (默认: 1.0)",
    )
    parser.add_argument(
        "--max-retries",
        type=int,
        default=3,
        help="API 调用失败时的最大重试次数 (默认: 3)",
    )

    args = parser.parse_args()

    # 推导默认路径（基于项目目录结构）
    project_root = Path(__file__).resolve().parent.parent.parent
    default_input = project_root / "pipeline" / "output" / "cleaned_items.jsonl"
    default_output = project_root / "pipeline" / "output"

    input_path = Path(args.input) if args.input else default_input
    output_dir = Path(args.output_dir) if args.output_dir else default_output

    print("=" * 60)
    print("  ARAM Insight - AI 候选提取处理器")
    print("=" * 60)
    print(f"  输入文件: {input_path}")
    print(f"  输出目录: {output_dir}")
    print(f"  模型:     {args.model}")
    print(f"  批次大小: {args.batch_size}")
    print(f"  限速延迟: {args.rate_limit}s")
    print(f"  最大重试: {args.max_retries}")
    print("=" * 60)

    extract_candidates(
        input_path=input_path,
        output_dir=output_dir,
        model=args.model,
        batch_size=args.batch_size,
        rate_limit_delay=args.rate_limit,
        max_retries=args.max_retries,
    )


if __name__ == "__main__":
    main()
