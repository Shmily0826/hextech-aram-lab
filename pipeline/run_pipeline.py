#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
run_pipeline.py - ARAM Insight 数据处理流水线主入口

用法示例:
    python pipeline/run_pipeline.py --source reddit --days 7 --limit 50
    python pipeline/run_pipeline.py --source manual
    python pipeline/run_pipeline.py --source reddit --days 7 --limit 50 --skip-ai
    python pipeline/run_pipeline.py --source all --days 14 --limit 100
"""

import argparse
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import List

# Windows 终端 UTF-8 兼容
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

# ---------------------------------------------------------------------------
# 路径计算 —— 基于脚本自身所在位置，而非工作目录
# ---------------------------------------------------------------------------
# __file__ 位于 pipeline/run_pipeline.py，因此 parent 就是 pipeline/
PIPELINE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = PIPELINE_DIR.parent
OUTPUT_DIR = PIPELINE_DIR / "output"

# 确保 pipeline/ 及其父目录（项目根）在 sys.path 中，以便直接 import
# collectors.xxx / processors.xxx 等子包
for _p in (str(PIPELINE_DIR), str(PROJECT_ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

# ---------------------------------------------------------------------------
# 加载 .env 环境变量（必须在 import 各 collector 之前完成，
# 因为 reddit_collector 模块级别就调用了 load_dotenv / os.getenv）
# ---------------------------------------------------------------------------
try:
    from dotenv import load_dotenv
    _env_file = PROJECT_ROOT / ".env"
    load_dotenv(dotenv_path=str(_env_file))
except ImportError:
    print("[警告] 未安装 python-dotenv，跳过 .env 加载。请运行: pip install python-dotenv")

# ---------------------------------------------------------------------------
# 日志配置
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# ===========================================================================
# 工具函数
# ===========================================================================

def _file_size_str(filepath: Path) -> str:
    """返回人类可读的文件大小字符串。"""
    if not filepath.exists():
        return "文件不存在"
    size = filepath.stat().st_size
    if size < 1024:
        return f"{size} B"
    elif size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"
    else:
        return f"{size / (1024 * 1024):.1f} MB"


def _print_summary(generated_files: List[Path]) -> None:
    """打印生成文件汇总报告。"""
    print("\n" + "=" * 60)
    print("流水线执行完毕！生成文件汇总：")
    print("=" * 60)
    if not generated_files:
        print("  （未生成任何输出文件）")
    for f in generated_files:
        status = _file_size_str(f) if f.exists() else "文件不存在"
        print(f"  {f.name:40s}  {status}")
    print("=" * 60)


def _step_label(current: int, total: int) -> str:
    """生成步骤标签，例如 [1/4]。"""
    return f"[{current}/{total}]"


# ===========================================================================
# 各步骤封装
# ===========================================================================

def step_collect_reddit(days: int, limit: int) -> List[dict]:
    """步骤：从 Reddit 采集帖子数据。"""
    from collectors.reddit_collector import collect_reddit
    posts = collect_reddit(days=days, limit=limit)
    logger.info("Reddit 采集完成：共 %d 条帖子", len(posts))
    return posts


def step_collect_manual() -> List[dict]:
    """步骤：读取手动收集的链接/摘录。"""
    from collectors.manual_links_collector import collect_manual
    items = collect_manual()
    logger.info("手动数据读取完成：共 %d 条", len(items))
    return items


def step_clean_text(input_paths: List[str], output_path: str) -> str:
    """步骤：清洗原始文本，返回输出文件的绝对路径。"""
    from processors.clean_text import clean_all
    result_path = clean_all(input_paths=input_paths, output_path=output_path)
    logger.info("文本清洗完成：%s", result_path)
    return result_path


def step_dedupe(input_path: str, output_path: str) -> str:
    """步骤：去重处理，返回输出文件的绝对路径。"""
    from processors.dedupe import dedupe_all
    result_path = dedupe_all(input_path=input_path, output_path=output_path)
    logger.info("去重处理完成：%s", result_path)
    return result_path


def step_ai_extract(input_path: str, output_dir: str) -> List[Path]:
    """
    步骤：AI 智能提取候选 Bug 与 Synergy。

    返回生成的输出文件 Path 列表。
    如果 processors.ai_extract 模块尚未实现，则安全跳过。
    """
    try:
        from processors.ai_extract import extract_candidates  # type: ignore[import-untyped]
    except ImportError:
        logger.warning(
            "processors.ai_extract 模块尚未实现，跳过 AI 提取步骤。\n"
            "         请在 pipeline/processors/ai_extract.py 中实现 extract_candidates(input_path, output_dir) 函数。"
        )
        return []

    try:
        result = extract_candidates(input_path, output_dir)
    except Exception as exc:
        logger.error("AI 提取过程中发生错误: %s", exc, exc_info=True)
        return []

    # extract_candidates 返回 (candidate_bugs, candidate_synergies) 元组
    # 或文件路径字符串、Path、列表、dict（兼容旧版本）
    generated: List[Path] = []

    if isinstance(result, tuple) and len(result) == 2:
        # 标准返回: (bugs_list, syns_list) — 文件已由 extract_candidates 写入
        bugs_path = Path(output_dir) / "candidate_bugs.json"
        syns_path = Path(output_dir) / "candidate_synergies.json"
        if bugs_path.exists():
            generated.append(bugs_path)
        if syns_path.exists():
            generated.append(syns_path)
    elif isinstance(result, (str, Path)):
        generated.append(Path(result))
    elif isinstance(result, list):
        for item in result:
            generated.append(Path(item))
    elif isinstance(result, dict):
        for v in result.values():
            if v:
                generated.append(Path(v))

    return generated


# ===========================================================================
# 输出文件路径常量（均在 pipeline/output/ 下）
# ===========================================================================
RAW_REDDIT_PATH   = str(OUTPUT_DIR / "raw_reddit_posts.jsonl")
RAW_MANUAL_PATH   = str(OUTPUT_DIR / "manual_items.jsonl")
CLEANED_PATH      = str(OUTPUT_DIR / "cleaned_items.jsonl")
DEDUPED_PATH      = str(OUTPUT_DIR / "deduped_items.jsonl")


# ===========================================================================
# 流水线编排
# ===========================================================================

def _build_input_paths(do_reddit: bool, do_manual: bool) -> List[str]:
    """根据启用的数据来源，构建清洗阶段的输入文件路径列表。"""
    paths: List[str] = []
    if do_reddit:
        paths.append(RAW_REDDIT_PATH)
    if do_manual:
        paths.append(RAW_MANUAL_PATH)
    return paths


def run_pipeline(
    source: str,
    days: int = 7,
    limit: int = 50,
    skip_ai: bool = False,
) -> int:
    """
    运行完整的数据处理流水线。

    Args:
        source:  数据来源 —— "reddit" | "manual" | "all"
        days:    Reddit 搜索时间范围（天）
        limit:   每个 subreddit 最大帖子数
        skip_ai: 是否跳过 AI 提取步骤

    Returns:
        0 表示成功，1 表示失败
    """
    start_time = datetime.now()
    generated_files: List[Path] = []

    do_reddit = source in ("reddit", "all")
    do_manual = source in ("manual", "all")
    is_combined = source == "all"

    # 计算总步骤数，用于进度显示
    # 采集阶段算 1 步（all 模式下 Reddit + Manual 各算 1 步），清洗 1 步，去重 1 步，AI 1 步
    collect_steps = 2 if is_combined else 1
    total_steps = collect_steps + 2 + (0 if skip_ai else 1)
    current_step = 0

    print(f"\n{'=' * 60}")
    print(f"ARAM Insight 数据处理流水线")
    print(f"数据来源: {source}  |  跳过 AI: {'是' if skip_ai else '否'}")
    if do_reddit:
        print(f"Reddit 参数: --days {days} --limit {limit}")
    print(f"{'=' * 60}\n")

    try:
        # --------------------------------------------------------------
        # 采集阶段
        # --------------------------------------------------------------
        if is_combined:
            # ---- Reddit 采集 ----
            current_step += 1
            print(f"{_step_label(current_step, total_steps)} 正在采集 Reddit 数据...")
            try:
                reddit_posts = step_collect_reddit(days=days, limit=limit)
                generated_files.append(OUTPUT_DIR / "raw_reddit_posts.jsonl")
            except Exception as e:
                logger.error("Reddit 采集失败: %s", e, exc_info=True)
                print(f"\n[错误] Reddit 采集失败: {e}")
                print("将仅使用手动数据继续执行后续步骤...\n")
                reddit_posts = []

            # ---- 手动数据读取 ----
            current_step += 1
            print(f"{_step_label(current_step, total_steps)} 正在读取手动收集的数据...")
            try:
                manual_items = step_collect_manual()
                generated_files.append(OUTPUT_DIR / "manual_items.jsonl")
            except Exception as e:
                logger.error("手动数据读取失败: %s", e, exc_info=True)
                print(f"\n[错误] 手动数据读取失败: {e}")
                print("将仅使用 Reddit 数据继续执行后续步骤...\n")
                manual_items = []

            # 检查是否有任何数据被采集到
            if not reddit_posts and not manual_items:
                print("\n[错误] 所有数据来源均未采集到有效数据，流水线中止。")
                return 1

        elif do_reddit:
            current_step += 1
            print(f"{_step_label(current_step, total_steps)} 正在采集 Reddit 数据...")
            step_collect_reddit(days=days, limit=limit)
            generated_files.append(OUTPUT_DIR / "raw_reddit_posts.jsonl")

        elif do_manual:
            current_step += 1
            print(f"{_step_label(current_step, total_steps)} 正在读取手动收集的数据...")
            step_collect_manual()
            generated_files.append(OUTPUT_DIR / "manual_items.jsonl")

        # --------------------------------------------------------------
        # 清洗阶段
        # --------------------------------------------------------------
        current_step += 1
        print(f"{_step_label(current_step, total_steps)} 正在清洗文本数据...")
        input_paths = _build_input_paths(do_reddit, do_manual)
        cleaned_path = step_clean_text(input_paths=input_paths, output_path=CLEANED_PATH)
        generated_files.append(Path(CLEANED_PATH))

        # --------------------------------------------------------------
        # 去重阶段
        # --------------------------------------------------------------
        current_step += 1
        print(f"{_step_label(current_step, total_steps)} 正在进行数据去重...")
        deduped_path = step_dedupe(input_path=cleaned_path, output_path=DEDUPED_PATH)
        generated_files.append(Path(DEDUPED_PATH))

        # --------------------------------------------------------------
        # AI 提取阶段（可选）
        # --------------------------------------------------------------
        if not skip_ai:
            current_step += 1
            print(f"{_step_label(current_step, total_steps)} 正在执行 AI 智能提取...")
            ai_files = step_ai_extract(deduped_path, str(OUTPUT_DIR))
            generated_files.extend(ai_files)
        else:
            print("\n  [跳过] 已启用 --skip-ai，跳过 AI 提取步骤。")

        # --------------------------------------------------------------
        # 完成汇总
        # --------------------------------------------------------------
        elapsed = datetime.now() - start_time
        minutes = int(elapsed.total_seconds()) // 60
        seconds = int(elapsed.total_seconds()) % 60
        time_str = f"{minutes}分{seconds}秒" if minutes > 0 else f"{seconds}秒"

        # 只保留实际存在的文件
        existing_files = [f for f in generated_files if f.exists()]
        _print_summary(existing_files)
        print(f"总耗时: {time_str}\n")

        return 0

    except KeyboardInterrupt:
        print("\n\n[中断] 用户手动终止流水线。")
        return 1
    except Exception as e:
        logger.error("流水线执行失败: %s", e, exc_info=True)
        print(f"\n[错误] 流水线执行失败: {e}")
        return 1


# ===========================================================================
# CLI 入口
# ===========================================================================

def build_parser() -> argparse.ArgumentParser:
    """构建命令行参数解析器。"""
    parser = argparse.ArgumentParser(
        description="ARAM Insight 数据处理流水线 - 采集、清洗、去重、AI 提取",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
示例:
  python pipeline/run_pipeline.py --source reddit --days 7 --limit 50
  python pipeline/run_pipeline.py --source manual
  python pipeline/run_pipeline.py --source reddit --days 7 --limit 50 --skip-ai
  python pipeline/run_pipeline.py --source all --days 14 --limit 100
        """,
    )

    parser.add_argument(
        "--source",
        required=True,
        choices=["reddit", "manual", "all"],
        help="数据来源: reddit（Reddit 采集）、manual（手动链接）、all（两者都运行）",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="Reddit 搜索最近几天的帖子（默认: 7，仅 --source reddit/all 时生效）",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=50,
        help="每个 subreddit 最多采集多少帖子（默认: 50，仅 --source reddit/all 时生效）",
    )
    parser.add_argument(
        "--skip-ai",
        action="store_true",
        default=False,
        help="跳过 AI 智能提取步骤（Step 4）",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        default=False,
        help="显示详细调试日志",
    )

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    # 设置日志级别
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # 确保输出目录存在
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    return run_pipeline(
        source=args.source,
        days=args.days,
        limit=args.limit,
        skip_ai=args.skip_ai,
    )


if __name__ == "__main__":
    sys.exit(main())
