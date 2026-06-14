#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Reddit Collector - 从 Reddit 收集与 ARAM Mayhem 相关的帖子
使用 PRAW (Python Reddit API Wrapper) 访问 Reddit API
"""

import os
import sys
import json
import argparse
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional

try:
    import praw
    from praw.models import Submission, Comment
except ImportError:
    print("错误: 未安装 praw 库")
    print("请运行: pip install praw")
    sys.exit(1)

try:
    from dotenv import load_dotenv
except ImportError:
    print("错误: 未安装 python-dotenv 库")
    print("请运行: pip install python-dotenv")
    sys.exit(1)

# 加载 .env 文件
load_dotenv()

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


def load_config():
    """加载配置文件"""
    config_dir = Path(__file__).parent.parent / "config"

    keywords_file = config_dir / "keywords.json"
    sources_file = config_dir / "sources.json"

    if not keywords_file.exists():
        logger.error(f"关键词配置文件不存在: {keywords_file}")
        sys.exit(1)

    if not sources_file.exists():
        logger.error(f"数据源配置文件不存在: {sources_file}")
        sys.exit(1)

    with open(keywords_file, 'r', encoding='utf-8') as f:
        keywords_config = json.load(f)

    with open(sources_file, 'r', encoding='utf-8') as f:
        sources_config = json.load(f)

    return keywords_config, sources_config


def get_reddit_client() -> praw.Reddit:
    """创建 Reddit API 客户端"""
    client_id = os.getenv('REDDIT_CLIENT_ID')
    client_secret = os.getenv('REDDIT_CLIENT_SECRET')
    user_agent = os.getenv('REDDIT_USER_AGENT')

    if not all([client_id, client_secret, user_agent]):
        print("\n" + "="*60)
        print("错误: Reddit API 凭证未配置")
        print("="*60)
        print("\n请在项目根目录创建或编辑 .env 文件，添加以下配置：\n")
        print("REDDIT_CLIENT_ID=your_client_id")
        print("REDDIT_CLIENT_SECRET=your_client_secret")
        print("REDDIT_USER_AGENT=your_user_agent")
        print("\n如何获取 Reddit API 凭证：")
        print("1. 访问 https://www.reddit.com/prefs/apps")
        print("2. 点击 'create another app...'")
        print("3. 选择 'script' 类型")
        print("4. 填写应用名称和 redirect uri (例如: http://localhost:8080)")
        print("5. 创建后复制 client_id 和 client_secret")
        print("6. user_agent 格式: '<platform>:<app_id>:<version> (by /u/<username>)'")
        print("\n示例: 'python:aram-insight:v1.0 (by /u/yourusername)'")
        print("="*60 + "\n")
        sys.exit(1)

    logger.info("正在初始化 Reddit 客户端...")

    return praw.Reddit(
        client_id=client_id,
        client_secret=client_secret,
        user_agent=user_agent,
        # PRAW 内置速率限制处理
        ratelimit_seconds=60
    )


def search_reddit_posts(
    reddit: praw.Reddit,
    subreddits: List[str],
    keywords: List[str],
    days: int,
    limit: int,
    max_comments: int
) -> List[Dict[str, Any]]:
    """
    搜索 Reddit 帖子

    Args:
        reddit: PRAW Reddit 客户端
        subreddits: 要搜索的 subreddit 列表
        keywords: 关键词列表
        days: 搜索最近几天的帖子
        limit: 每个 subreddit 最多返回多少帖子
        max_comments: 每个帖子最多收集多少条评论

    Returns:
        收集到的帖子列表
    """
    collected_posts = []
    time_filter = 'week' if days <= 7 else 'month' if days <= 30 else 'year'

    logger.info(f"开始搜索 Reddit 帖子")
    logger.info(f"搜索范围: {len(subreddits)} 个 subreddit")
    logger.info(f"关键词数量: {len(keywords)}")
    logger.info(f"时间范围: 最近 {days} 天")

    for subreddit_name in subreddits:
        logger.info(f"\n正在搜索 r/{subreddit_name}...")

        try:
            subreddit = reddit.subreddit(subreddit_name)

            # 搜索每个关键词
            for keyword in keywords:
                logger.debug(f"搜索关键词: '{keyword}'")

                try:
                    # 使用 search API，按相关性排序
                    search_results = subreddit.search(
                        keyword,
                        sort='relevance',
                        time_filter=time_filter,
                        limit=limit
                    )

                    for post in search_results:
                        # 检查是否在时间范围内
                        post_date = datetime.utcfromtimestamp(post.created_utc)
                        cutoff_date = datetime.utcnow() - timedelta(days=days)

                        if post_date < cutoff_date:
                            logger.debug(f"跳过过期帖子: {post.id}")
                            continue

                        # 收集帖子数据
                        post_data = {
                            'post_id': post.id,
                            'title': post.title,
                            'selftext': post.selftext,
                            'score': post.score,
                            'num_comments': post.num_comments,
                            'created_utc': datetime.fromtimestamp(
                                post.created_utc
                            ).isoformat(),
                            'url': post.url,
                            'subreddit': str(post.subreddit),
                            'matched_keywords': [keyword],
                            'collected_at': datetime.now().isoformat()
                        }

                        # 收集评论（如果需要）
                        if max_comments > 0:
                            comments = collect_top_comments(post, max_comments)
                            post_data['top_comments'] = comments

                        collected_posts.append(post_data)
                        logger.debug(f"收集到帖子: {post.id} - {post.title[:50]}")

                except Exception as e:
                    logger.warning(f"搜索关键词 '{keyword}' 时出错: {e}")
                    continue

        except Exception as e:
            logger.error(f"搜索 subreddit r/{subreddit_name} 时出错: {e}")
            continue

    # 去重：合并相同帖子的关键词
    unique_posts = {}
    for post in collected_posts:
        post_id = post['post_id']
        if post_id not in unique_posts:
            unique_posts[post_id] = post
        else:
            # 合并关键词
            existing_keywords = unique_posts[post_id]['matched_keywords']
            new_keywords = post['matched_keywords']
            unique_posts[post_id]['matched_keywords'] = list(
                set(existing_keywords + new_keywords)
            )

    result = list(unique_posts.values())
    logger.info(f"\n共收集到 {len(result)} 个不重复的帖子")

    return result


def collect_top_comments(post: Submission, max_comments: int) -> List[Dict[str, Any]]:
    """
    收集帖子的热门评论

    Args:
        post: Reddit 帖子对象
        max_comments: 最多收集多少条评论

    Returns:
        评论列表
    """
    comments_data = []

    try:
        # 按热度排序评论
        post.comments.sort('best')

        for i, comment in enumerate(post.comments):
            if i >= max_comments:
                break

            # 跳过被删除的评论
            if not isinstance(comment, Comment):
                continue

            comment_data = {
                'comment_id': comment.id,
                'author': str(comment.author) if comment.author else '[deleted]',
                'body': comment.body,
                'score': comment.score,
                'created_utc': datetime.fromtimestamp(
                    comment.created_utc
                ).isoformat()
            }

            comments_data.append(comment_data)

    except Exception as e:
        logger.warning(f"收集帖子 {post.id} 的评论时出错: {e}")

    return comments_data


def save_to_jsonl(posts: List[Dict[str, Any]], output_file: Path):
    """
    保存数据到 JSONL 文件

    Args:
        posts: 帖子数据列表
        output_file: 输出文件路径
    """
    output_file.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"\n正在保存数据到 {output_file}...")

    with open(output_file, 'w', encoding='utf-8') as f:
        for post in posts:
            json_line = json.dumps(post, ensure_ascii=False)
            f.write(json_line + '\n')

    logger.info(f"已保存 {len(posts)} 条记录")


def collect_reddit(
    days: int = 7,
    limit: int = 50,
    subreddits: Optional[List[str]] = None,
    max_comments: int = 5
) -> List[Dict[str, Any]]:
    """
    主收集函数 - 可作为模块导入使用

    Args:
        days: 搜索最近几天的帖子
        limit: 每个 subreddit 最多返回多少帖子
        subreddits: 要搜索的 subreddit 列表，None 则使用配置中的默认值
        max_comments: 每个帖子最多收集多少条评论

    Returns:
        收集到的帖子列表
    """
    # 加载配置
    keywords_config, sources_config = load_config()

    # 合并中英文关键词
    keywords = (
        keywords_config.get('english', []) +
        keywords_config.get('chinese', [])
    )

    # 确定要搜索的 subreddit
    if subreddits is None:
        reddit_config = sources_config.get('reddit', {})
        subreddits = reddit_config.get('subreddits', ['leagueoflegends'])

    # 如果命令行指定了 "all"，使用配置中的所有 subreddit
    if len(subreddits) == 1 and subreddits[0].lower() == 'all':
        reddit_config = sources_config.get('reddit', {})
        subreddits = reddit_config.get('subreddits', ['leagueoflegends'])

    # 创建 Reddit 客户端
    reddit = get_reddit_client()

    # 搜索帖子
    posts = search_reddit_posts(
        reddit=reddit,
        subreddits=subreddits,
        keywords=keywords,
        days=days,
        limit=limit,
        max_comments=max_comments
    )

    # 保存到文件
    output_file = Path(__file__).parent.parent / "output" / "raw_reddit_posts.jsonl"
    save_to_jsonl(posts, output_file)

    return posts


def main():
    """主函数 - CLI 入口"""
    parser = argparse.ArgumentParser(
        description='Reddit Collector - 从 Reddit 收集 ARAM Mayhem 相关帖子',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python reddit_collector.py --days 7 --limit 50
  python reddit_collector.py --subreddit leagueoflegends ARAM
  python reddit_collector.py --subreddit all --no-comments
        """
    )

    parser.add_argument(
        '--days',
        type=int,
        default=7,
        help='搜索最近几天的帖子 (默认: 7)'
    )

    parser.add_argument(
        '--limit',
        type=int,
        default=50,
        help='每个 subreddit 最多返回多少帖子 (默认: 50)'
    )

    parser.add_argument(
        '--subreddit',
        nargs='+',
        default=None,
        help='指定要搜索的 subreddit，可以指定多个，或使用 "all" 表示配置中的所有 subreddit'
    )

    parser.add_argument(
        '--no-comments',
        action='store_true',
        help='不收集评论'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='显示详细日志'
    )

    args = parser.parse_args()

    # 设置日志级别
    if args.verbose:
        logger.setLevel(logging.DEBUG)

    # 确定最大评论数
    max_comments = 0 if args.no_comments else 5

    try:
        posts = collect_reddit(
            days=args.days,
            limit=args.limit,
            subreddits=args.subreddit,
            max_comments=max_comments
        )

        print(f"\n✓ 收集完成！共收集到 {len(posts)} 个帖子")
        print(f"✓ 数据已保存到: pipeline/output/raw_reddit_posts.jsonl")

    except KeyboardInterrupt:
        print("\n\n用户中断操作")
        sys.exit(0)
    except Exception as e:
        logger.error(f"发生错误: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
