#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tieba_collector.py — Baidu Tieba 帖子采集器 (dry-run, 仅读取公开页面)

安全约束:
  - 不登录、不使用 Cookie、不进行任何身份验证
  - 不保存用户名、UID、头像、个人主页等信息
  - 仅读取公开可访问的百度贴吧列表页和帖子页
  - 页面结构变化或访问受限时优雅失败
  - 输出仅写入 pipeline/output/ 目录，绝不写入 data/*.json

用法:
    # CLI 独立运行
    python pipeline/collectors/tieba_collector.py --kw "海克斯大乱斗" --limit 10 --output pipeline/output/tieba_raw.jsonl

    # 通过 run_pipeline.py
    python pipeline/run_pipeline.py --source tieba --kw "海克斯大乱斗" --limit 10 --dry-run
"""

import json
import logging
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Dict, List, Optional

# Windows UTF-8
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 路径
# ---------------------------------------------------------------------------
COLLECTOR_DIR = Path(__file__).resolve().parent  # pipeline/collectors/
PIPELINE_DIR = COLLECTOR_DIR.parent  # pipeline/
PROJECT_ROOT = PIPELINE_DIR.parent  # project root
DEFAULT_OUTPUT = PIPELINE_DIR / "output" / "tieba_raw.jsonl"

# ---------------------------------------------------------------------------
# 常量
# ---------------------------------------------------------------------------
USER_AGENT = "aram-insight-pipeline/1.0"
REQUEST_TIMEOUT = 30  # 秒
REQUEST_DELAY = 2  # 秒
MAX_LIMIT = 10


# ===========================================================================
# HTML 解析辅助
# ===========================================================================

class _TiebaListParser(HTMLParser):
    """
    解析百度贴吧论坛列表页 (https://tieba.baidu.com/f?kw=...) 的帖子列表。

    目标结构:
      <li class="j_thread_list ..." data-field='{"id":12345,...}'>
        ...
        <a ... class="j_th_tit ..." href="/p/12345" title="帖子标题">帖子标题</a>
        ...
        <span class="threadlist_detail">
          <div class="threadlist_text">
            <span class="threadlist_abs ...">摘要文本</span>
          </div>
        </span>
        ...
      </li>

    由于页面结构可能随时间变化，解析器采用宽松匹配策略:
    - 优先从 data-field 属性提取帖子 ID
    - 从 class="j_th_tit" 的 <a> 标签提取标题和链接
    - 从 class 含 "threadlist_abs" 的元素提取摘要
    """

    def __init__(self):
        super().__init__()
        self.posts: List[Dict[str, Any]] = []
        # 当前解析状态
        self._in_thread_item = False
        self._in_title_link = False
        self._in_summary = False
        self._current: Dict[str, Any] = {}
        self._text_buf = ""

    def handle_starttag(self, tag: str, attrs: List[tuple]):
        attr_dict = dict(attrs)
        cls = attr_dict.get("class", "")

        # 检测帖子列表项
        if tag == "li" and "j_thread_list" in cls:
            self._in_thread_item = True
            self._current = {}
            # 尝试从 data-field 提取帖子 ID
            data_field = attr_dict.get("data-field", "")
            if data_field:
                try:
                    field_data = json.loads(data_field)
                    if isinstance(field_data, dict) and "id" in field_data:
                        self._current["_tid"] = str(field_data["id"])
                    # 回复数
                    if "reply_num" in field_data:
                        try:
                            self._current["_reply_count"] = int(field_data["reply_num"])
                        except (ValueError, TypeError):
                            pass
                except (json.JSONDecodeError, ValueError):
                    pass

        if not self._in_thread_item:
            return

        # 标题链接: <a class="j_th_tit ..." href="/p/12345" title="...">
        if tag == "a" and "j_th_tit" in cls:
            self._in_title_link = True
            self._text_buf = ""
            href = attr_dict.get("href", "")
            title = attr_dict.get("title", "")
            if href:
                self._current["_href"] = href
            if title:
                self._current["_title_attr"] = title

        # 摘要: <span class="threadlist_abs ...">
        if tag == "span" and "threadlist_abs" in cls:
            self._in_summary = True
            self._text_buf = ""

        # 也尝试 threadlist_text 包裹的 div 内文本
        if tag == "div" and "threadlist_text" in cls:
            pass  # 仅作为容器，不直接处理

    def handle_data(self, data: str):
        if self._in_title_link:
            self._text_buf += data
        elif self._in_summary:
            self._text_buf += data

    def handle_endtag(self, tag: str):
        if tag == "a" and self._in_title_link:
            self._in_title_link = False
            title_text = self._text_buf.strip()
            # 优先使用 title 属性（完整标题），回退到链接文本
            self._current["_title"] = self._current.get("_title_attr", "") or title_text
            self._text_buf = ""

        if tag == "span" and self._in_summary:
            self._in_summary = False
            self._current["_summary"] = self._text_buf.strip()
            self._text_buf = ""

        if tag == "li" and self._in_thread_item:
            self._in_thread_item = False
            # 只保存有标题或链接的帖子
            if self._current.get("_title") or self._current.get("_href"):
                self.posts.append(dict(self._current))
            self._current = {}


class _TiebaPostParser(HTMLParser):
    """
    解析百度贴吧帖子详情页 (https://tieba.baidu.com/p/XXXX) 的楼主正文。

    目标结构 (宽松匹配):
      <div class="d_post_content j_d_post_content ...">帖子正文 HTML</div>

    仅提取第一个匹配的帖子内容（即楼主首楼正文）。
    忽略所有用户名、头像、等级等个人信息。
    """

    def __init__(self):
        super().__init__()
        self.body_text: str = ""
        self._in_content = False
        self._depth = 0
        self._text_buf = ""

    def handle_starttag(self, tag: str, attrs: List[tuple]):
        attr_dict = dict(attrs)
        cls = attr_dict.get("class", "")

        # 检测楼主正文区域
        if not self._in_content and "d_post_content" in cls:
            self._in_content = True
            self._depth = 1
            self._text_buf = ""
            return

        if self._in_content:
            self._depth += 1
            # 将 <br> 转为换行
            if tag == "br":
                self._text_buf += "\n"

    def handle_data(self, data: str):
        if self._in_content:
            self._text_buf += data

    def handle_endtag(self, tag: str):
        if self._in_content:
            self._depth -= 1
            if self._depth <= 0:
                self._in_content = False
                self.body_text = self._text_buf.strip()
                self._text_buf = ""


# ===========================================================================
# HTTP 请求
# ===========================================================================

def _fetch_url(url: str) -> Optional[str]:
    """
    使用 urllib 发起 GET 请求，返回响应文本。

    返回 None 表示请求失败（已记录日志）。
    """
    logger.debug("请求: %s", url)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
            # 检测编码
            charset = "utf-8"
            content_type = resp.headers.get("Content-Type", "")
            if "charset=" in content_type:
                charset = content_type.split("charset=")[-1].split(";")[0].strip()
            raw = resp.read()
            return raw.decode(charset, errors="replace")
    except urllib.error.HTTPError as e:
        logger.warning("HTTP 错误 %d: %s — %s", e.code, e.reason, url)
        return None
    except urllib.error.URLError as e:
        logger.warning("URL 错误: %s — %s", e.reason, url)
        return None
    except Exception as e:
        logger.warning("请求失败: %s — %s", e, url)
        return None


# ===========================================================================
# 采集逻辑
# ===========================================================================

def _extract_thread_id(href: str) -> Optional[str]:
    """从帖子链接中提取帖子 ID (tid)。

    支持的格式:
      /p/12345
      /p/12345?pid=678
      https://tieba.baidu.com/p/12345
    """
    match = re.search(r"/p/(\d+)", href)
    return match.group(1) if match else None


def _build_source_url(href: str) -> str:
    """将相对链接转为完整 URL。"""
    if href.startswith("http"):
        return href
    return "https://tieba.baidu.com" + href


def fetch_tieba_list(keyword: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    从百度贴吧论坛列表页获取帖子列表。

    Args:
        keyword: 贴吧名称 / 搜索关键词
        limit: 最多返回帖子数 (上限 10)

    Returns:
        帖子基本信息列表 (标题、链接、摘要、回复数)
    """
    limit = min(limit, MAX_LIMIT)
    kw_encoded = urllib.parse.quote(keyword, safe="")

    # 使用论坛列表页
    url = f"https://tieba.baidu.com/f?kw={kw_encoded}&ie=utf-8"
    logger.info("正在获取贴吧列表: %s (关键词: %s)", url, keyword)

    html = _fetch_url(url)
    if html is None:
        logger.warning("无法获取贴吧列表页，返回空列表。")
        return []

    # 检测是否被重定向到验证页面或搜索页面
    if "<title>" in html and ("百度安全验证" in html or "验证码" in html):
        logger.warning("百度贴吧返回安全验证页面，无法继续采集。返回空列表。")
        return []

    parser = _TiebaListParser()
    try:
        parser.feed(html)
    except Exception as e:
        logger.warning("解析贴吧列表页 HTML 时出错: %s", e)
        return []

    raw_posts = parser.posts[:limit]
    logger.info("从列表页解析到 %d 条帖子 (共解析 %d 条)", len(raw_posts), len(parser.posts))

    items = []
    for post in raw_posts:
        href = post.get("_href", "")
        tid = post.get("_tid") or _extract_thread_id(href)
        title = post.get("_title", "")
        summary = post.get("_summary", "")
        reply_count = post.get("_reply_count", 0)

        if not tid:
            logger.debug("跳过无法提取 tid 的帖子: %s", href)
            continue

        source_url = f"https://tieba.baidu.com/p/{tid}"
        item: Dict[str, Any] = {
            "id": f"tieba_post_{tid}",
            "source_type": "tieba",
            "source_url": source_url,
            "source_title": title,
            "text": summary or title,  # 先放摘要，后续可能替换为正文
            "collected_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "metadata": {
                "keyword": keyword,
                "reply_count": reply_count,
                "has_detail": False,
            },
        }
        items.append(item)
        logger.debug("  列表项: [%s] %s (回复: %d)", tid, title[:50], reply_count)

    return items


def fetch_post_detail(item: Dict[str, Any]) -> Dict[str, Any]:
    """
    尝试获取帖子详情页的楼主正文，并更新 item["text"]。

    如果获取失败，保留原有的摘要文本，不修改 item。
    """
    source_url = item.get("source_url", "")
    if not source_url:
        return item

    logger.debug("正在获取帖子详情: %s", source_url)
    html = _fetch_url(source_url)
    if html is None:
        logger.debug("无法获取帖子详情: %s", source_url)
        return item

    # 检测安全验证
    if "百度安全验证" in html or "验证码" in html:
        logger.warning("帖子详情页返回安全验证: %s", source_url)
        return item

    parser = _TiebaPostParser()
    try:
        parser.feed(html)
    except Exception as e:
        logger.debug("解析帖子详情 HTML 出错: %s — %s", source_url, e)
        return item

    body = parser.body_text.strip()
    if body:
        item["text"] = body
        item["metadata"]["has_detail"] = True
        logger.debug("  帖子正文: %d 字符", len(body))
    else:
        logger.debug("  未能提取到正文，保留摘要。")

    return item


def collect_tieba_posts(
    keyword: str = "海克斯大乱斗",
    limit: int = 10,
    fetch_detail: bool = True,
) -> List[Dict[str, Any]]:
    """
    完整的贴吧采集流程:
      1. 获取列表页帖子
      2. 逐个获取帖子详情 (可选)
      3. 返回标准化 item 列表

    Args:
        keyword: 搜索关键词 / 贴吧名称
        limit: 最大帖子数 (上限 10)
        fetch_detail: 是否获取帖子详情

    Returns:
        标准化 item 列表
    """
    limit = min(limit, MAX_LIMIT)

    # Step 1: 列表页
    items = fetch_tieba_list(keyword, limit)

    if not items:
        logger.info("列表页未获取到任何帖子。")
        return []

    # Step 2: 逐个获取详情
    if fetch_detail:
        for i, item in enumerate(items):
            if i > 0:
                time.sleep(REQUEST_DELAY)
            items[i] = fetch_post_detail(item)

    logger.info("采集完成: 共 %d 条帖子 (keyword=%s)", len(items), keyword)
    return items


# ===========================================================================
# 输出
# ===========================================================================

def save_to_jsonl(items: List[Dict[str, Any]], output_path: Path) -> None:
    """保存 items 到 JSONL 文件。"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        for item in items:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
    logger.info("已保存 %d 条到 %s", len(items), output_path)


# ===========================================================================
# Pipeline 兼容接口
# ===========================================================================

def collect_tieba(
    keyword: str = "海克斯大乱斗",
    limit: int = 10,
    output_path: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Pipeline 兼容接口 — 被 run_pipeline.py 的 step_collect_tieba() 调用。

    Args:
        keyword: 搜索关键词 / 贴吧名称
        limit: 最大帖子数 (上限 10)
        output_path: 输出路径 (None 则用默认值)

    Returns:
        标准化 item 列表
    """
    limit = min(limit, MAX_LIMIT)
    items = collect_tieba_posts(keyword=keyword, limit=limit, fetch_detail=True)

    out = Path(output_path) if output_path else DEFAULT_OUTPUT
    if items:
        save_to_jsonl(items, out)
    else:
        logger.warning("无有效数据，跳过写入。")

    return items


# ===========================================================================
# CLI 入口
# ===========================================================================

def main():
    import argparse

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    parser = argparse.ArgumentParser(
        description="Baidu Tieba Collector — 百度贴吧帖子采集 (仅读取公开页面, dry-run)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
示例:
  python pipeline/collectors/tieba_collector.py --kw "海克斯大乱斗" --limit 10
  python pipeline/collectors/tieba_collector.py --kw "海克斯大乱斗" --limit 5 --output pipeline/output/tieba_test.jsonl
  python pipeline/collectors/tieba_collector.py --kw "海克斯大乱斗" --limit 10 --verbose

安全约束:
  - 不登录、不使用 Cookie
  - 不保存任何用户个人信息 (用户名/UID/头像)
  - 仅读取公开可访问的页面
  - 输出仅写入 pipeline/output/
        """,
    )
    parser.add_argument(
        "--kw",
        default="海克斯大乱斗",
        help="搜索关键词 / 贴吧名称 (默认: 海克斯大乱斗)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="最多返回帖子数 (默认: 10, 上限: 10)",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="输出文件路径 (默认: pipeline/output/tieba_raw.jsonl)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="显示详细调试日志",
    )

    args = parser.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    output_path = Path(args.output) if args.output else DEFAULT_OUTPUT

    try:
        items = collect_tieba_posts(
            keyword=args.kw,
            limit=args.limit,
            fetch_detail=True,
        )
        save_to_jsonl(items, output_path)

        print(f"\n采集完成:")
        print(f"  帖子数  : {len(items)}")
        detail_count = sum(1 for i in items if i.get("metadata", {}).get("has_detail"))
        print(f"  有正文  : {detail_count}")
        print(f"  输出文件: {output_path}")

    except KeyboardInterrupt:
        print("\n用户中断。")
        sys.exit(0)
    except Exception as e:
        logger.error("采集失败: %s", e, exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
