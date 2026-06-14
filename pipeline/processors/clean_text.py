"""
clean_text.py - 原始文本清洗处理器

功能：
  1. 读取 pipeline/output/raw_reddit_posts.jsonl 和/或 pipeline/output/manual_items.jsonl
  2. 清洗文本：去除 HTML 标签、多余空白、Markdown 格式、Reddit 引用符号（>）、Bot 评论
  3. 保留文本中的 URL
  4. 将帖子标题 + selftext + 热门评论合并为单一 "text" 字段，供 AI 分析使用
  5. 输出 pipeline/output/cleaned_items.jsonl
"""

import argparse
import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# ============================================================
# 常量定义
# ============================================================

# 已知 Reddit Bot 用户名（不区分大小写匹配）
KNOWN_BOTS = frozenset([
    "automoderator",
    "remindmebot",
    "autotldr",
    "haikusbot",
    "sneakpeakbot",
    "wikibot",
    "redditbotsinfo",
    "botdefence",
    "niceaccounts",
    "substatsbot",
    "redditrepostsleuth",
    "colorizationbot",
    "tiny_smile_bot",
    "lenscloud_bot",
    "anti-evilbot",
    "good_hate_bot",
    "b0trank",
    "reddit-wiki-bot",
    "video_descriptionbot",
    "profanity_gauge_bot",
    "clickbait_sentinel",
])

# 预编译正则表达式（模块级别，避免重复编译）

# HTML 标签：<br>, <p>, <div ...>, etc.
RE_HTML_TAG = re.compile(r"<[^>]+>")

# Markdown 图片：![alt](url) → 保留 url
RE_MD_IMAGE = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")

# Markdown 链接：[text](url) → 保留 text 和 url
RE_MD_LINK = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")

# 独立 URL（不在 Markdown 语法内的）
RE_STANDALONE_URL = re.compile(
    r"(?<!\()(?:https?://|www\.)[^\s<>\"')\]]+",
    re.IGNORECASE,
)

# Reddit 引用行（行首 > 符号，可嵌套 >>>）
RE_REDDIT_QUOTE = re.compile(r"^(?:>{1,}\s?)+", re.MULTILINE)

# Markdown 粗体/斜体：***text***, **text**, *text*, ___text___, __text__, _text_
# 注意：按照从最长标记到最短标记的顺序替换，防止部分替换
RE_MD_BOLD_ITALIC = re.compile(r"\*{3}(.+?)\*{3}|_{3}(.+?)_{3}")
RE_MD_BOLD = re.compile(r"\*{2}(.+?)\*{2}|_{2}(.+?)_{2}")
RE_MD_ITALIC = re.compile(r"\*(.+?)\*|_(.+?)_")

# Markdown 内联代码块：```...``` 或 `...`
RE_MD_CODE_BLOCK = re.compile(r"```[\s\S]*?```")
RE_MD_INLINE_CODE = re.compile(r"`(.+?)`")

# Markdown 水平分割线
RE_MD_HORIZONTAL_RULE = re.compile(r"^[-*_]{3,}\s*$", re.MULTILINE)

# Markdown 标题标记
RE_MD_HEADER = re.compile(r"^#{1,6}\s*", re.MULTILINE)

# Markdown 无序列表项标记
RE_MD_LIST_ITEM = re.compile(r"^[\s]*[-*+]\s+", re.MULTILINE)

# 多余空白：连续空格、连续换行
RE_EXCESS_SPACES = re.compile(r"[ \t]{2,}")
RE_EXCESS_NEWLINES = re.compile(r"\n{3,}")

# Reddit 编辑标记
RE_EDIT_MARKER = re.compile(
    r"(?i)^\s*(?:edit|update|edit\s*\d*|update\s*\d*)[:\-.]?\s*",
    re.MULTILINE,
)

# 无意义占位符文本（Reddit 用于删除/移除的帖子）
REMOVED_PLACEHOLDERS = frozenset(["[removed]", "[deleted]", "[gone]", ""])


# ============================================================
# 文本清洗工具函数
# ============================================================


def extract_and_preserve_urls(text: str) -> str:
    """
    提取 Markdown 链接/图片语法中的 URL，将其替换为纯 URL 文本，
    确保后续去除 Markdown 格式时不会丢失链接。

    示例：
        [点击这里](https://example.com) → 点击这里 https://example.com
        ![img](https://imgur.com/a.jpg) → https://imgur.com/a.jpg
    """
    # Markdown 图片：![alt](url) → url（图片 alt 文本通常无意义，直接保留 url）
    text = RE_MD_IMAGE.sub(r"\1", text)

    # Markdown 链接：[text](url) → text url
    def _link_replacer(m: re.Match) -> str:
        link_text = m.group(1).strip()
        url = m.group(2).strip()
        if link_text and link_text != url:
            return f"{link_text} {url}"
        return url

    text = RE_MD_LINK.sub(_link_replacer, text)
    return text


def remove_html_tags(text: str) -> str:
    """去除所有 HTML 标签，保留标签内文本内容。"""
    text = RE_HTML_TAG.sub(" ", text)
    # 还原常见 HTML 实体
    text = text.replace("&amp;", "&")
    text = text.replace("&lt;", "<")
    text = text.replace("&gt;", ">")
    text = text.replace("&quot;", '"')
    text = text.replace("&#x27;", "'")
    text = text.replace("&nbsp;", " ")
    return text


def remove_markdown_artifacts(text: str) -> str:
    """
    去除 Markdown 格式标记（粗体、斜体、代码块、标题、列表等），
    保留纯文本内容。注意：此函数应在 extract_and_preserve_urls 之后调用，
    以避免链接 URL 被误删。
    """
    # 代码块（先处理，防止内部内容被其他规则干扰）
    text = RE_MD_CODE_BLOCK.sub("", text)
    text = RE_MD_INLINE_CODE.sub(r"\1", text)

    # 粗体+斜体（***text*** 或 ___text___）
    text = RE_MD_BOLD_ITALIC.sub(
        lambda m: m.group(1) or m.group(2) or "", text
    )
    # 粗体
    text = RE_MD_BOLD.sub(
        lambda m: m.group(1) or m.group(2) or "", text
    )
    # 斜体
    text = RE_MD_ITALIC.sub(
        lambda m: m.group(1) or m.group(2) or "", text
    )

    # 水平分割线
    text = RE_MD_HORIZONTAL_RULE.sub("", text)

    # 标题标记
    text = RE_MD_HEADER.sub("", text)

    # 列表项标记
    text = RE_MD_LIST_ITEM.sub("", text)

    # Reddit 引用符号（> 开头的行）
    text = RE_REDDIT_QUOTE.sub("", text)

    # Reddit 编辑标记（Edit:, Update: 等）
    text = RE_EDIT_MARKER.sub("", text)

    return text


def normalize_whitespace(text: str) -> str:
    """折叠多余空白字符：多个空格→单空格，多个换行→双换行，去除首尾空白。"""
    text = RE_EXCESS_SPACES.sub(" ", text)
    text = RE_EXCESS_NEWLINES.sub("\n\n", text)
    return text.strip()


def clean_single_text(text: Optional[str]) -> str:
    """
    对单段文本执行完整清洗流水线：
      URL 保留 → HTML 去除 → Markdown 去除 → 空白规范化

    Args:
        text: 原始文本，可为 None

    Returns:
        清洗后的纯文本字符串；输入为 None 或空时返回空字符串
    """
    if not text:
        return ""
    text = str(text)
    text = extract_and_preserve_urls(text)
    text = remove_html_tags(text)
    text = remove_markdown_artifacts(text)
    text = normalize_whitespace(text)
    return text


# ============================================================
# Bot 检测
# ============================================================


def is_bot_comment(comment: Dict[str, Any]) -> bool:
    """
    判断一条评论是否来自已知 Bot。
    判断依据：author 字段在 KNOWN_BOTS 列表中（不区分大小写）。
    """
    author = str(comment.get("author", "")).lower()
    if author in KNOWN_BOTS:
        return True
    # 额外检查：body 中包含典型 bot 触发语（如 "I am a bot"）
    body = str(comment.get("body", "")).lower()
    if author.endswith("bot") and "i am a bot" in body:
        return True
    return False


# ============================================================
# 评论提取
# ============================================================


def _extract_comments_recursive(thing: Any, collected: List[Dict]) -> None:
    """
    递归遍历 Reddit 评论树（支持嵌套 replies 结构），
    将所有评论节点收集到 collected 列表中。
    """
    if isinstance(thing, dict):
        # 标准 Reddit "listing" 结构
        if thing.get("kind") == "Listing" and "data" in thing:
            for child in thing["data"].get("children", []):
                _extract_comments_recursive(child, collected)
        # 单条评论节点（kind == "t1"）
        elif thing.get("kind") == "t1":
            data = thing.get("data", {})
            if data:
                collected.append(data)
                # 递归处理 replies（可能是 Listing 或空字符串）
                replies = data.get("replies")
                if isinstance(replies, dict):
                    _extract_comments_recursive(replies, collected)
        # 扁平列表结构（无 kind 字段，直接有 body/author 字段）
        elif "body" in thing or "author" in thing:
            collected.append(thing)
    elif isinstance(thing, list):
        for item in thing:
            _extract_comments_recursive(item, collected)


def extract_top_comments(post: Dict[str, Any], max_comments: int = 10) -> List[str]:
    """
    从 Reddit 帖子数据中提取热门评论（排除 Bot 评论）。

    支持的评论数据格式：
      - post["comments"]（标准 Reddit API 返回的 Listing 结构）
      - post["top_comments"]（预处理后的扁平列表）
      - post["comments_list"]（自定义扁平列表）

    Args:
        post: 帖子原始数据字典
        max_comments: 最多保留的评论数量

    Returns:
        清洗后的评论文本列表
    """
    raw_comments: List[Dict] = []

    # 优先使用预处理的扁平列表
    if "top_comments" in post:
        raw_comments = post["top_comments"]
    elif "comments_list" in post:
        raw_comments = post["comments_list"]
    elif "comments" in post:
        # 递归解析 Reddit 标准评论树
        _extract_comments_recursive(post["comments"], raw_comments)

    clean_comments = []
    for comment in raw_comments:
        if not isinstance(comment, dict):
            continue
        if is_bot_comment(comment):
            continue
        body = comment.get("body") or comment.get("text") or comment.get("selftext") or ""
        cleaned = clean_single_text(body)
        if cleaned and cleaned.lower() not in REMOVED_PLACEHOLDERS:
            clean_comments.append(cleaned)
        if len(clean_comments) >= max_comments:
            break

    return clean_comments


# ============================================================
# 单条数据处理
# ============================================================


def _get_reddit_id(post: Dict[str, Any]) -> str:
    """从帖子数据中提取 Reddit 帖子 ID（无前缀）。"""
    # name 字段通常是完整 ID，如 "t3_abc123"
    name = post.get("name", "")
    if name.startswith("t3_"):
        return name[3:]
    return str(post.get("id", ""))


def process_reddit_post(post: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    处理一条 Reddit 帖子，生成清洗后的标准化输出记录。

    返回格式：
        {
            "id": "reddit_<post_id>",
            "source": "reddit",
            "platform": "reddit",
            "url": "...",
            "title": "...",
            "text": "<merged clean text>",
            "score": <int>,
            "num_comments": <int>,
            "created_utc": <float>,
            "matched_keywords": [...]
        }
    """
    post_id = _get_reddit_id(post)
    if not post_id:
        logger.warning("跳过无 ID 的 Reddit 帖子: %s", post.get("title", "?")[:50])
        return None

    # 提取 URL（Reddit 帖子的 url 字段可能是外链或帖子自身 permalink）
    raw_url = post.get("url", "")
    permalink = post.get("permalink", "")
    if raw_url and not raw_url.startswith("https://www.reddit.com"):
        url = raw_url
    elif permalink:
        url = f"https://www.reddit.com{permalink}" if permalink.startswith("/") else permalink
    else:
        url = raw_url

    # 清洗标题
    title = clean_single_text(post.get("title", ""))

    # 清洗正文（selftext）
    selftext_raw = post.get("selftext", "")
    selftext = clean_single_text(selftext_raw)
    # 过滤掉已删除/移除的占位符
    if selftext.lower() in REMOVED_PLACEHOLDERS:
        selftext = ""

    # 提取并清洗热门评论
    top_comments = extract_top_comments(post)

    # 合并为单一 text 字段：标题 + 正文 + 评论
    # 用双换行分隔各段，便于 AI 模型理解段落结构
    text_parts = [p for p in [title, selftext] if p]
    text_parts.extend(top_comments)
    merged_text = "\n\n".join(text_parts)

    return {
        "id": f"reddit_{post_id}",
        "source": "reddit",
        "platform": "reddit",
        "url": url,
        "title": title,
        "text": merged_text,
        "score": int(post.get("score", 0)),
        "num_comments": int(post.get("num_comments", 0)),
        "created_utc": float(post.get("created_utc", 0)),
        "matched_keywords": post.get("matched_keywords", []),
    }


def process_manual_item(item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    处理一条手动录入的数据项，生成清洗后的标准化输出记录。

    返回格式与 process_reddit_post 一致，id 前缀为 "manual_"。
    """
    item_id = str(item.get("id", ""))
    if not item_id:
        logger.warning("跳过无 ID 的手动条目: %s", item.get("title", "?")[:50])
        return None

    # 清洗标题和正文
    title = clean_single_text(item.get("title", ""))
    body = clean_single_text(
        item.get("text") or item.get("body") or item.get("content") or ""
    )

    # 合并文本
    merged_parts = [p for p in [title, body] if p]
    merged_text = "\n\n".join(merged_parts)

    return {
        "id": f"manual_{item_id}",
        "source": "manual",
        "platform": item.get("platform", "manual"),
        "url": item.get("url", ""),
        "title": title,
        "text": merged_text,
        "score": int(item.get("score", 0)),
        "num_comments": int(item.get("num_comments", 0)),
        "created_utc": float(item.get("created_utc", 0)),
        "matched_keywords": item.get("matched_keywords", []),
    }


# ============================================================
# 主处理流程
# ============================================================


def _detect_source_type(filepath: str) -> str:
    """根据文件名推断数据来源类型。"""
    name = Path(filepath).stem.lower()
    if "reddit" in name:
        return "reddit"
    if "manual" in name:
        return "manual"
    return "unknown"


def clean_all(
    input_paths: List[str],
    output_path: str = "pipeline/output/cleaned_items.jsonl",
) -> str:
    """
    主清洗入口：读取一个或多个原始 JSONL 文件，清洗后输出为单一 JSONL 文件。

    Args:
        input_paths: 原始 JSONL 文件路径列表
        output_path: 清洗后的输出文件路径

    Returns:
        输出文件的绝对路径
    """
    output_p = Path(output_path)
    output_p.parent.mkdir(parents=True, exist_ok=True)

    total_in = 0   # 读取总条数
    total_out = 0  # 有效输出条数

    with open(output_p, "w", encoding="utf-8") as fout:
        for fpath in input_paths:
            source_type = _detect_source_type(fpath)
            file_in = 0
            file_out = 0

            try:
                with open(fpath, "r", encoding="utf-8") as fin:
                    for lineno, raw_line in enumerate(fin, start=1):
                        raw_line = raw_line.strip()
                        if not raw_line:
                            continue
                        total_in += 1
                        file_in += 1

                        # 解析 JSON
                        try:
                            data = json.loads(raw_line)
                        except json.JSONDecodeError as exc:
                            logger.warning(
                                "跳过无效 JSON（文件 %s，第 %d 行）: %s",
                                fpath, lineno, exc,
                            )
                            continue

                        # 根据来源类型选择处理函数
                        if source_type == "reddit":
                            result = process_reddit_post(data)
                        elif source_type == "manual":
                            result = process_manual_item(data)
                        else:
                            # 未知来源：根据数据内容自动判断
                            if "selftext" in data or "subreddit" in data:
                                result = process_reddit_post(data)
                            else:
                                result = process_manual_item(data)

                        if result and result.get("text"):
                            fout.write(json.dumps(result, ensure_ascii=False) + "\n")
                            total_out += 1
                            file_out += 1

            except FileNotFoundError:
                logger.error("输入文件不存在，跳过: %s", fpath)
            except Exception as exc:
                logger.error("处理文件 %s 时发生异常: %s", fpath, exc, exc_info=True)

            logger.info(
                "文件 %-40s | 来源: %-8s | 读取: %d | 输出: %d",
                Path(fpath).name, source_type, file_in, file_out,
            )

    logger.info(
        "清洗完成：共读取 %d 条 → 有效输出 %d 条 → %s",
        total_in, total_out, output_p.resolve(),
    )
    return str(output_p.resolve())


# ============================================================
# CLI 入口
# ============================================================


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    parser = argparse.ArgumentParser(
        description="清洗原始 JSONL 数据，合并文本字段，输出标准化 cleaned_items.jsonl",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "示例用法:\n"
            "  python clean_text.py --input raw_reddit_posts.jsonl manual_items.jsonl\n"
            "  python clean_text.py --input raw.jsonl --output cleaned.jsonl\n"
        ),
    )
    parser.add_argument(
        "--input",
        nargs="+",
        required=True,
        metavar="FILE",
        help="一个或多个原始 JSONL 输入文件路径",
    )
    parser.add_argument(
        "--output",
        default="pipeline/output/cleaned_items.jsonl",
        metavar="FILE",
        help="清洗后的输出 JSONL 文件路径（默认: pipeline/output/cleaned_items.jsonl）",
    )

    args = parser.parse_args()
    clean_all(args.input, args.output)


if __name__ == "__main__":
    main()
