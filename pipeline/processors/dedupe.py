"""
dedupe.py - 数据去重处理器

功能：
  1. 读取 cleaned_items.jsonl（由 clean_text.py 输出）
  2. 按 URL 和 id 进行精确去重
  3. 对标题进行规范化（小写 + 去空白 + 去标点）后，使用 difflib.SequenceMatcher 做模糊匹配（阈值 0.8）
  4. 重复条目保留 score 更高的一条
  5. 输出去重后的 cleaned_items.jsonl（默认覆盖原文件）
  6. 记录去重统计日志（精确去重数 + 模糊去重数）
"""

import argparse
import json
import logging
import re
import string
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# ============================================================
# 常量
# ============================================================

# 标题模糊匹配相似度阈值（0.0 ~ 1.0）
TITLE_SIMILARITY_THRESHOLD = 0.8

# 低于此长度的标题不参与模糊匹配（避免过短标题产生误判）
MIN_TITLE_LENGTH_FOR_FUZZY = 3

# 预编译：用于标题规范化的标点字符集（包含中英文常见标点）
# string.punctuation 覆盖 ASCII 标点；额外补充中文标点
_PUNCTUATION_EXTRA = "。，！？；：""''【】《》（）、·…—"
_RE_PUNCTUATION = re.compile(
    r"[" + re.escape(string.punctuation + _PUNCTUATION_EXTRA) + r"]+"
)
# 多余空白
_RE_WHITESPACE = re.compile(r"\s+")


# ============================================================
# 工具函数
# ============================================================


def normalize_title(title: str) -> str:
    """
    规范化标题，用于模糊匹配比较。

    处理步骤：
      1. 转为小写（含 Unicode 大小写折叠）
      2. 去除所有标点字符
      3. 合并多余空白并去除首尾空白

    Args:
        title: 原始标题字符串

    Returns:
        规范化后的纯文本标题
    """
    if not title:
        return ""
    # Unicode 大小写折叠（比 .lower() 更彻底，可处理特殊字符如 ß→ss）
    t = title.casefold()
    # 去除标点
    t = _RE_PUNCTUATION.sub("", t)
    # 合并空白
    t = _RE_WHITESPACE.sub(" ", t).strip()
    return t


def _score_of(item: Dict[str, Any]) -> int:
    """安全获取条目的 score 字段，缺失或非法值返回 0。"""
    try:
        return int(item.get("score", 0))
    except (TypeError, ValueError):
        return 0


# ============================================================
# JSONL 读写
# ============================================================


def read_jsonl(path: str) -> List[Dict[str, Any]]:
    """读取 JSONL 文件，返回解析成功的所有条目列表。"""
    items = []
    skipped = 0
    with open(path, "r", encoding="utf-8") as f:
        for lineno, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                items.append(json.loads(line))
            except json.JSONDecodeError as exc:
                logger.warning("跳过无效 JSON（第 %d 行）: %s", lineno, exc)
                skipped += 1
    if skipped:
        logger.info("共跳过 %d 条无效 JSON 记录", skipped)
    return items


def write_jsonl(items: List[Dict[str, Any]], path: str) -> None:
    """将条目列表写入 JSONL 文件（覆盖写入），自动创建父目录。"""
    output_p = Path(path)
    output_p.parent.mkdir(parents=True, exist_ok=True)
    with open(output_p, "w", encoding="utf-8") as f:
        for item in items:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")


# ============================================================
# 核心去重逻辑
# ============================================================


def dedupe_all(
    input_path: str = "pipeline/output/cleaned_items.jsonl",
    output_path: Optional[str] = None,
) -> str:
    """
    对 cleaned_items.jsonl 进行去重处理。

    去重策略（两轮）：

    第一轮 - 精确去重：
      对每条记录的 url（非空时）和 id 建立索引，若出现完全相同的值，
      保留 score 较高的条目。

    第二轮 - 模糊去重：
      对所有保留条目的标题进行规范化后，使用 difflib.SequenceMatcher
      两两比较相似度（阈值 >= 0.8），相似则保留 score 更高的条目。

    Args:
        input_path:  输入 JSONL 文件路径（默认 pipeline/output/cleaned_items.jsonl）
        output_path: 输出 JSONL 文件路径（默认覆盖 input_path）

    Returns:
        输出文件的绝对路径字符串
    """
    if output_path is None:
        output_path = input_path

    # ------------------------------------------------------------------
    # 1. 读取全部条目
    # ------------------------------------------------------------------
    items = read_jsonl(input_path)
    total = len(items)
    logger.info("读取完成：%s → 共 %d 条记录", input_path, total)

    if total == 0:
        write_jsonl([], output_path)
        logger.info("无数据需要处理，已写入空文件: %s", output_path)
        return str(Path(output_path).resolve())

    # ------------------------------------------------------------------
    # 2. 第一轮：按 URL 和 ID 精确去重
    #    - 分别维护 url_index 和 id_index，值均为 {key: items列表中的整数索引}
    #    - 遇到重复 key 时，比较 score，保留高分条目
    # ------------------------------------------------------------------
    url_index: Dict[str, int] = {}  # url → result 列表中的位置
    id_index: Dict[str, int] = {}   # id  → result 列表中的位置
    deduped_by_exact: List[Dict[str, Any]] = []
    exact_dupes = 0

    for item in items:
        item_url: str = (item.get("url") or "").strip()
        item_id: str = str(item.get("id", "")).strip()
        score = _score_of(item)

        is_dup = False
        replace_idx: Optional[int] = None  # 需要被替换的 result 列表索引

        # 检查 URL 精确匹配
        if item_url:
            existing = url_index.get(item_url)
            if existing is not None:
                is_dup = True
                if score > _score_of(deduped_by_exact[existing]):
                    replace_idx = existing

        # 检查 ID 精确匹配（仅在 URL 未触发替换时检查，避免重复逻辑）
        if item_id and not is_dup:
            existing = id_index.get(item_id)
            if existing is not None:
                is_dup = True
                if score > _score_of(deduped_by_exact[existing]):
                    replace_idx = existing

        if is_dup:
            exact_dupes += 1
            if replace_idx is not None:
                # 新条目 score 更高，替换旧条目（需更新索引指向新位置）
                old_item = deduped_by_exact[replace_idx]
                old_url = (old_item.get("url") or "").strip()
                old_id = str(old_item.get("id", "")).strip()

                # 删除旧条目的索引映射
                if old_url and url_index.get(old_url) == replace_idx:
                    del url_index[old_url]
                if old_id and id_index.get(old_id) == replace_idx:
                    del id_index[old_id]

                # 放入新条目并重建索引
                deduped_by_exact[replace_idx] = item
                if item_url:
                    url_index[item_url] = replace_idx
                if item_id:
                    id_index[item_id] = replace_idx

                logger.debug(
                    "精确去重（替换）: [%s] 替换 [%s]，新 score=%d > 旧 score=%d",
                    item.get("id", "?"), old_item.get("id", "?"),
                    score, _score_of(old_item),
                )
        else:
            # 非重复，追加到结果列表
            idx = len(deduped_by_exact)
            deduped_by_exact.append(item)
            if item_url:
                url_index[item_url] = idx
            if item_id:
                id_index[item_id] = idx

    logger.info(
        "第一轮（精确去重）完成：%d → %d 条（移除 %d 条重复）",
        total, len(deduped_by_exact), exact_dupes,
    )

    # ------------------------------------------------------------------
    # 3. 第二轮：按规范化标题做模糊去重（SequenceMatcher）
    #    - 将每条保留条目的 normalized_title 与已保留列表逐一比较
    #    - 相似度 >= 阈值时视为重复，保留 score 更高的条目
    #    - 时间复杂度 O(n^2)，对于万级数据量仍然可接受
    # ------------------------------------------------------------------
    final_result: List[Dict[str, Any]] = []
    final_norm_titles: List[str] = []  # 与 final_result 索引一一对应
    fuzzy_dupes = 0

    for item in deduped_by_exact:
        raw_title = item.get("title", "")
        norm_title = normalize_title(raw_title)
        score = _score_of(item)

        # 标题过短则跳过模糊比较（避免误判）
        if len(norm_title) < MIN_TITLE_LENGTH_FOR_FUZZY:
            final_result.append(item)
            final_norm_titles.append(norm_title)
            continue

        # 与已保留的条目逐一比较
        is_fuzzy_dup = False
        replace_final_idx: Optional[int] = None

        for j, existing_norm in enumerate(final_norm_titles):
            # 跳过短标题的比较
            if len(existing_norm) < MIN_TITLE_LENGTH_FOR_FUZZY:
                continue

            ratio = SequenceMatcher(None, norm_title, existing_norm).ratio()
            if ratio >= TITLE_SIMILARITY_THRESHOLD:
                is_fuzzy_dup = True
                if score > _score_of(final_result[j]):
                    replace_final_idx = j
                # 找到一条重复即可停止（避免多次替换）
                break

        if is_fuzzy_dup:
            fuzzy_dupes += 1
            if replace_final_idx is not None:
                old = final_result[replace_final_idx]
                final_result[replace_final_idx] = item
                final_norm_titles[replace_final_idx] = norm_title
                logger.debug(
                    "模糊去重（替换）: \"%s\" 替换 \"%s\"（score %d > %d）",
                    raw_title[:40], old.get("title", "")[:40],
                    score, _score_of(old),
                )
            else:
                logger.debug(
                    "模糊去重（丢弃）: \"%s\"（score=%d，低于已有条目）",
                    raw_title[:40], score,
                )
        else:
            final_result.append(item)
            final_norm_titles.append(norm_title)

    logger.info(
        "第二轮（模糊去重）完成：%d → %d 条（移除 %d 条相似标题重复）",
        len(deduped_by_exact), len(final_result), fuzzy_dupes,
    )

    # ------------------------------------------------------------------
    # 4. 写入输出文件
    # ------------------------------------------------------------------
    write_jsonl(final_result, output_path)

    kept = len(final_result)
    total_removed = total - kept

    logger.info("=" * 60)
    logger.info("去重统计汇总：")
    logger.info("  原始记录数     : %d", total)
    logger.info("  精确去重移除   : %d 条（URL/ID 完全相同）", exact_dupes)
    logger.info("  模糊去重移除   : %d 条（标题相似度 >= %.1f%%）",
                fuzzy_dupes, TITLE_SIMILARITY_THRESHOLD * 100)
    logger.info("  总移除数       : %d 条", total_removed)
    logger.info("  最终保留       : %d 条", kept)
    logger.info("  输出文件       : %s", Path(output_path).resolve())
    logger.info("=" * 60)

    return str(Path(output_path).resolve())


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
        description="对 cleaned_items.jsonl 进行精确去重（URL/ID）和模糊去重（标题相似度）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "示例用法:\n"
            "  python dedupe.py\n"
            "  python dedupe.py --input cleaned_items.jsonl\n"
            "  python dedupe.py --input cleaned_items.jsonl --output deduped_items.jsonl\n"
        ),
    )
    parser.add_argument(
        "--input",
        default="pipeline/output/cleaned_items.jsonl",
        metavar="FILE",
        help="输入 JSONL 文件路径（默认: pipeline/output/cleaned_items.jsonl）",
    )
    parser.add_argument(
        "--output",
        default=None,
        metavar="FILE",
        help="输出 JSONL 文件路径（默认: 覆盖输入文件）",
    )

    args = parser.parse_args()
    dedupe_all(args.input, args.output)


if __name__ == "__main__":
    main()
