#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
reddit_collector.py — Read-only Reddit 帖子/评论采集器

⚠️ 安全约束：
  - 仅使用 PRAW read-only 模式（不发帖、评论、投票、私信）
  - 不保存 Reddit 用户名或个人信息
  - 不修改 data/*.json 正式文件
  - 输出仅写入 pipeline/output/ 目录

用法：
    # CLI 独立运行
    python pipeline/collectors/reddit_collector.py --subreddit ARAM --query "ARAM Mayhem" --limit 10

    # 通过 run_pipeline.py
    python pipeline/run_pipeline.py --source reddit --subreddit ARAM --query "ARAM Mayhem" --limit 10 --dry-run
"""

import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional

# Windows UTF-8
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 路径
# ---------------------------------------------------------------------------
COLLECTOR_DIR = Path(__file__).resolve().parent          # pipeline/collectors/
PIPELINE_DIR = COLLECTOR_DIR.parent                       # pipeline/
PROJECT_ROOT = PIPELINE_DIR.parent                        # project root
DEFAULT_OUTPUT = PIPELINE_DIR / "output" / "raw_reddit_posts.jsonl"


# ---------------------------------------------------------------------------
# 环境加载
# ---------------------------------------------------------------------------
def _load_env():
    """从 .env 加载环境变量。"""
    try:
        from dotenv import load_dotenv
        load_dotenv(dotenv_path=str(PROJECT_ROOT / ".env"))
    except ImportError:
        logger.warning("python-dotenv 未安装，仅使用系统环境变量。")


# ---------------------------------------------------------------------------
# Reddit 客户端（read-only）
# ---------------------------------------------------------------------------
def get_reddit_client():
    """
    创建 PRAW read-only Reddit 客户端。

    需要环境变量：
      REDDIT_CLIENT_ID
      REDDIT_CLIENT_SECRET
      REDDIT_USER_AGENT
    """
    _load_env()

    client_id = os.getenv("REDDIT_CLIENT_ID", "").strip()
    client_secret = os.getenv("REDDIT_CLIENT_SECRET", "").strip()
    user_agent = os.getenv("REDDIT_USER_AGENT", "").strip()

    if not all([client_id, client_secret, user_agent]):
        raise RuntimeError(
            "Reddit API 凭证未配置。\n"
            "请在 .env 中设置: REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT\n"
            "参考 .env.example 获取凭证步骤。"
        )

    # 拒绝占位符
    placeholders = {"your_client_id_here", "your_client_secret_here", ""}
    if client_id.lower() in placeholders or client_secret.lower() in placeholders:
        raise RuntimeError(
            "Reddit API 凭证仍为占位符值，请在 .env 中填入真实凭证。"
        )

    try:
        import praw
    except ImportError:
        raise RuntimeError("praw 未安装。请运行: pip install praw")

    reddit = praw.Reddit(
        client_id=client_id,
        client_secret=client_secret,
        user_agent=user_agent,
        ratelimit_seconds=60,
    )

    # 验证 read-only 模式
    if not reddit.read_only:
        raise RuntimeError(
            "PRAW 客户端不是 read-only 模式！"
            "请确认未提供 username/password（script 应用只使用 client_id + secret）。"
        )

    logger.info("Reddit read-only 客户端初始化成功。")
    return reddit


# ---------------------------------------------------------------------------
# 采集逻辑
# ---------------------------------------------------------------------------
def collect_top_comments(post, max_comments: int) -> List[Dict[str, Any]]:
    """
    收集帖子的热门评论（不保存 author）。

    Returns:
        [{body, score, created_utc}, ...]
    """
    comments_data = []
    try:
        post.comments.replace_more(limit=0)  # 不展开 MoreComments
        for i, comment in enumerate(post.comments):
            if i >= max_comments:
                break
            # 跳过 PRAW 特殊对象（MoreComments 等）
            if not hasattr(comment, "body"):
                continue
            comments_data.append({
                "body": comment.body,
                "score": comment.score,
                "created_utc": datetime.fromtimestamp(
                    comment.created_utc, tz=timezone.utc
                ).isoformat(),
            })
    except Exception as e:
        logger.warning("收集帖子 %s 的评论时出错: %s", post.id, e)
    return comments_data


def search_reddit(
    subreddit_name: str,
    query: str,
    limit: int = 10,
    comments_limit: int = 20,
    time_filter: str = "week",
) -> List[Dict[str, Any]]:
    """
    在指定 subreddit 搜索帖子并收集评论。

    Args:
        subreddit_name: subreddit 名称（如 "ARAM"）
        query: 搜索关键词（如 "ARAM Mayhem"）
        limit: 最多返回多少帖子（默认 10，最大 10）
        comments_limit: 每个帖子最多收集多少条评论（默认 20，最大 20）
        time_filter: 时间过滤 ("hour", "day", "week", "month", "year", "all")

    Returns:
        raw item 列表，每条符合 pipeline 标准格式
    """
    # 安全限制
    limit = min(limit, 10)
    comments_limit = min(comments_limit, 20)

    reddit = get_reddit_client()

    logger.info("搜索 r/%s: query='%s' limit=%d time_filter=%s",
                subreddit_name, query, limit, time_filter)

    items = []
    try:
        subreddit = reddit.subreddit(subreddit_name)
        search_results = subreddit.search(
            query,
            sort="relevance",
            time_filter=time_filter,
            limit=limit,
        )

        for post in search_results:
            # 构建 text: selftext 或 title（如果 selftext 为空）
            text = post.selftext.strip() if post.selftext else ""
            if not text:
                text = post.title

            # 收集评论
            comments = collect_top_comments(post, comments_limit) if comments_limit > 0 else []

            # 构建 source_metadata
            source_metadata = {
                "num_comments": post.num_comments,
                "upvote_ratio": getattr(post, "upvote_ratio", None),
                "is_self": post.is_self,
                "link_flair_text": getattr(post, "link_flair_text", None),
                "domain": getattr(post, "domain", ""),
                "search_query": query,
                "time_filter": time_filter,
            }

            item = {
                "id": post.id,
                "source_type": "reddit",
                "subreddit": str(post.subreddit),
                "title": post.title,
                "text": text,
                "url": post.url,
                "permalink": f"https://www.reddit.com{post.permalink}",
                "score": post.score,
                "created_utc": datetime.fromtimestamp(
                    post.created_utc, tz=timezone.utc
                ).isoformat(),
                "collected_at": datetime.now(timezone.utc).isoformat(),
                "comments": comments,
                "source_metadata": source_metadata,
            }

            items.append(item)
            logger.info("  收集帖子: [%s] %s (score=%d, comments=%d/%d)",
                        post.id, post.title[:60], post.score,
                        len(comments), post.num_comments)

    except Exception as e:
        logger.error("搜索 r/%s 时出错: %s", subreddit_name, e, exc_info=True)

    logger.info("搜索完成: 共 %d 条帖子, %d 条评论",
                len(items), sum(len(i["comments"]) for i in items))
    return items


# ---------------------------------------------------------------------------
# 输出
# ---------------------------------------------------------------------------
def save_to_jsonl(items: List[Dict[str, Any]], output_path: Path) -> None:
    """保存 raw items 到 JSONL 文件。"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        for item in items:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
    logger.info("已保存 %d 条到 %s", len(items), output_path)


# ---------------------------------------------------------------------------
# Pipeline 兼容接口
# ---------------------------------------------------------------------------
def collect_reddit(
    days: int = 7,
    limit: int = 10,
    subreddits: Optional[List[str]] = None,
    max_comments: int = 20,
    query: str = "ARAM Mayhem",
    time_filter: str = "",
    output_path: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Pipeline 兼容接口 — 被 run_pipeline.py 的 step_collect_reddit() 调用。

    Args:
        days: 时间范围（转换为 time_filter）
        limit: 每个 subreddit 最大帖子数（上限 10）
        subreddits: subreddit 列表
        max_comments: 每帖最大评论数（上限 20）
        query: 搜索关键词
        time_filter: 时间过滤（优先于 days）
        output_path: 输出路径（None 则用默认值）

    Returns:
        raw items 列表
    """
    # days → time_filter 映射
    if not time_filter:
        if days <= 1:
            time_filter = "day"
        elif days <= 7:
            time_filter = "week"
        elif days <= 30:
            time_filter = "month"
        else:
            time_filter = "year"

    if subreddits is None:
        subreddits = ["ARAM"]

    all_items = []
    for sub in subreddits:
        items = search_reddit(
            subreddit_name=sub,
            query=query,
            limit=limit,
            comments_limit=max_comments,
            time_filter=time_filter,
        )
        all_items.extend(items)

    # 保存
    out = Path(output_path) if output_path else DEFAULT_OUTPUT
    save_to_jsonl(all_items, out)

    return all_items


# ---------------------------------------------------------------------------
# CLI 入口
# ---------------------------------------------------------------------------
def main():
    import argparse

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    parser = argparse.ArgumentParser(
        description="Reddit Read-only Collector — ARAM Mayhem 帖子采集（仅读取）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python pipeline/collectors/reddit_collector.py --subreddit ARAM --query "ARAM Mayhem" --limit 10
  python pipeline/collectors/reddit_collector.py --subreddit leagueoflegends --query "augment bug" --limit 5 --comments-limit 10 --time-filter month
        """,
    )
    parser.add_argument("--subreddit", default="ARAM",
                        help="搜索的 subreddit（默认: ARAM）")
    parser.add_argument("--query", default="ARAM Mayhem",
                        help="搜索关键词（默认: 'ARAM Mayhem'）")
    parser.add_argument("--limit", type=int, default=10,
                        help="最多返回帖子数（默认 10，上限 10）")
    parser.add_argument("--comments-limit", type=int, default=20,
                        help="每帖最多评论数（默认 20，上限 20）")
    parser.add_argument("--time-filter", default="week",
                        choices=["hour", "day", "week", "month", "year", "all"],
                        help="时间过滤（默认: week）")
    parser.add_argument("--output", default=None,
                        help="输出文件路径（默认: pipeline/output/raw_reddit_posts.jsonl）")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="显示详细日志")

    args = parser.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    output_path = Path(args.output) if args.output else DEFAULT_OUTPUT

    try:
        items = search_reddit(
            subreddit_name=args.subreddit,
            query=args.query,
            limit=args.limit,
            comments_limit=args.comments_limit,
            time_filter=args.time_filter,
        )
        save_to_jsonl(items, output_path)

        print(f"\n采集完成:")
        print(f"  帖子数  : {len(items)}")
        print(f"  评论数  : {sum(len(i['comments']) for i in items)}")
        print(f"  输出文件: {output_path}")

    except RuntimeError as e:
        print(f"\n错误: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n用户中断。")
        sys.exit(0)
    except Exception as e:
        logger.error("采集失败: %s", e, exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
