#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sync_champions.py — 从 Riot Data Dragon 同步全英雄基础数据

扫描 Data Dragon 获取全英雄列表，与现有 data/champions.json 合并。
已有英雄保留所有字段不覆盖，新增英雄使用前端兼容的默认结构。

本脚本不会编造任何胜率、样本量或评级数据。

用法：
    python scripts/sync_champions.py
"""

import json
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

# ---------------------------------------------------------------------------
# Windows 终端 UTF-8 兼容
# ---------------------------------------------------------------------------
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

# ---------------------------------------------------------------------------
# 路径配置
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
DATA_DIR = PROJECT_ROOT / "data"

CHAMPIONS_PATH = DATA_DIR / "champions.json"
BACKUP_PATH = DATA_DIR / "champions.backup.json"

# Data Dragon URLs
DDRAGON_VERSION_URL = "https://ddragon.leagueoflegends.com/api/versions.json"
DDRAGON_CHAMPION_URL = "https://ddragon.leagueoflegends.com/cdn/{version}/data/zh_CN/champion.json"

# ---------------------------------------------------------------------------
# 角色映射 (Data Dragon tag → 中文角色名)
# ---------------------------------------------------------------------------
ROLE_MAP = {
    "Mage": "法师",
    "Marksman": "射手",
    "Fighter": "战士",
    "Tank": "坦克",
    "Support": "辅助",
    "Assassin": "刺客",
}


# ---------------------------------------------------------------------------
# 工具函数
# ---------------------------------------------------------------------------

def load_json(path: Path) -> dict | list | None:
    """加载 JSON 文件，失败返回 None。"""
    if not path.exists():
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, Exception) as e:
        print(f"  ✗ 无法读取 {path}: {e}")
        return None


def fetch_json(url: str) -> dict | list | None:
    """从 URL 获取 JSON 数据，失败返回 None。"""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "aram-insight-sync/1.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.URLError as e:
        print(f"  ✗ 网络请求失败: {e}")
        print("    请确认网络连接正常后重试。")
        return None
    except Exception as e:
        print(f"  ✗ 请求异常: {e}")
        return None


def map_role(tags) -> str:
    """将 Data Dragon tags 映射为中文角色名。"""
    if isinstance(tags, list):
        tag_list = tags
    elif isinstance(tags, str):
        tag_list = [t.strip() for t in tags.split(",")]
    else:
        return "未知"

    for tag in tag_list:
        if tag in ROLE_MAP:
            return ROLE_MAP[tag]
    return "未知"


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------

def main() -> int:
    print("=" * 64)
    print("  海克斯乱斗实验室 — 全英雄同步")
    print("=" * 64)

    # ---- 1. 获取 Data Dragon 最新版本 ----
    print("\n  [1/5] 获取 Data Dragon 最新版本号...")
    versions = fetch_json(DDRAGON_VERSION_URL)
    if not versions or not isinstance(versions, list) or len(versions) == 0:
        print("\n  ✗ 无法获取 Data Dragon 版本列表。")
        print("    请确认网络连接正常。现有 champions.json 未受影响。")
        return 1

    version = versions[0]
    print(f"    最新版本: {version}")

    # ---- 2. 获取全英雄列表 (zh_CN locale) ----
    print(f"\n  [2/5] 获取全英雄数据 (zh_CN)...")
    url = DDRAGON_CHAMPION_URL.format(version=version)
    dd_data = fetch_json(url)
    if not dd_data or "data" not in dd_data:
        print("\n  ✗ 无法获取 Data Dragon 英雄列表。")
        print("    请确认网络连接正常。现有 champions.json 未受影响。")
        return 1

    dd_champions = dd_data["data"]
    print(f"    Data Dragon 共 {len(dd_champions)} 个英雄")

    # ---- 3. 读取现有 champions.json ----
    print(f"\n  [3/5] 读取现有 champions.json...")
    existing = load_json(CHAMPIONS_PATH)
    if existing is None:
        # 文件不存在时使用初始结构
        existing = {"championKeys": {}, "champions": []}
        print("    文件不存在，将创建新文件")

    current_champions = existing.get("champions", [])
    current_keys = existing.get("championKeys", {})

    # 以 name 为键建立索引
    existing_by_name = {c.get("name"): c for c in current_champions if isinstance(c, dict)}
    # 以 Data Dragon key 为键建立索引（用于匹配已有英雄）
    known_dd_keys = set(current_keys.values())
    existing_count = len(current_champions)
    print(f"    现有英雄: {existing_count} 个")

    # ---- 4. 合并 ----
    print(f"\n  [4/5] 合并英雄数据...")

    added = 0
    updated_keys = 0

    for dd_key, champ_data in dd_champions.items():
        cn_name = champ_data.get("name", dd_key)
        cn_title = champ_data.get("title", "")
        en_name = champ_data.get("id", dd_key)
        tags = champ_data.get("tags", [])
        role = map_role(tags)

        # 通过 Data Dragon key 匹配已有英雄（因为中文名可能与 DD 不同）
        if dd_key in known_dd_keys:
            # 已有英雄：确认 championKeys 映射完整
            # 查找对应的中文名
            existing_cn = None
            for name, key in current_keys.items():
                if key == dd_key:
                    existing_cn = name
                    break
            # 如果中文名不在 champions 列表中（异常情况），补充映射
            if existing_cn and existing_cn not in existing_by_name:
                current_keys[existing_cn] = dd_key
                updated_keys += 1
            continue

        # 新增英雄
        new_hero = {
            "name": cn_name,
            "title": cn_title,
            "role": role,
            "tier": "unknown",
            "wr": None,
            "pr": None,
            "games": None,
            "kda": None,
            "build": "",
            "tips": "暂无海克斯大乱斗专属说明。"
        }

        current_champions.append(new_hero)
        current_keys[cn_name] = dd_key
        existing_by_name[cn_name] = new_hero
        added += 1
        print(f"    + {cn_name} ({en_name}, {role})")

    kept = existing_count
    total = len(current_champions)

    if added == 0 and updated_keys == 0:
        print("    所有英雄已存在，无需新增。")
    else:
        if updated_keys > 0:
            print(f"    补充了 {updated_keys} 个 championKeys 映射")

    print(f"\n    新增: {added} 个")
    print(f"    保留: {kept} 个")
    print(f"    合计: {total} 个")

    # ---- 5. 备份 + 写入 + 校验 ----
    print(f"\n  [5/5] 写入数据...")

    # 备份
    if CHAMPIONS_PATH.exists():
        shutil.copy2(CHAMPIONS_PATH, BACKUP_PATH)
        print(f"    备份 → {BACKUP_PATH.relative_to(PROJECT_ROOT)}")

    # 写入
    output = {
        "championKeys": current_keys,
        "champions": current_champions,
    }

    with open(CHAMPIONS_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"    写入 → {CHAMPIONS_PATH.relative_to(PROJECT_ROOT)}")

    # 自动校验
    print(f"\n  自动运行 validate_data.py...")
    validate_script = SCRIPT_DIR / "validate_data.py"
    if validate_script.exists():
        try:
            result = subprocess.run(
                [sys.executable, str(validate_script)],
                capture_output=True, text=True, encoding="utf-8"
            )
            print(result.stdout)
            if result.returncode != 0:
                print("  ⚠ 校验发现错误，请检查上方输出。")
                print(f"    如需回滚，可将 {BACKUP_PATH.relative_to(PROJECT_ROOT)} 重命名为 champions.json")
                return 1
        except Exception as e:
            print(f"  ⚠ 无法运行校验脚本: {e}")
    else:
        print("    validate_data.py 不存在，跳过校验")

    # 汇总
    print("=" * 64)
    print("  同步完成")
    print("=" * 64)
    print(f"  Data Dragon 版本 : {version}")
    print(f"  新增英雄        : {added} 个")
    print(f"  保留已有        : {kept} 个")
    print(f"  英雄总数        : {total} 个")
    if BACKUP_PATH.exists():
        print(f"  备份文件        : {BACKUP_PATH.relative_to(PROJECT_ROOT)}")
    print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
