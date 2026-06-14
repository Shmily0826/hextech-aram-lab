#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
normalize_entities.py — 实体名称标准化模块

将 AI / Reddit 输出中的英文英雄名映射为当前正式数据使用的中文英雄名。

基于 data/champions.json 的 championKeys 构建映射：
  - DataDragonKey (Ziggs) → 中文名 (吉格斯)
  - 英文名 / 常见别名 (Kai'Sa) → 中文名 (卡莎)
  - 中文名 → 中文名 (直通)

用法：
    from pipeline.processors.normalize_entities import normalize_champion_name
    cn_name = normalize_champion_name("Ziggs")  # -> "吉格斯"

    from pipeline.processors.normalize_entities import normalize_augment_name
    cn_aug = normalize_augment_name("Chain Lightning")  # -> "连锁闪电"
"""

import json
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Windows 终端 UTF-8 兼容
# ---------------------------------------------------------------------------
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

# ---------------------------------------------------------------------------
# 路径配置
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent       # pipeline/processors/
PIPELINE_DIR = SCRIPT_DIR.parent                    # pipeline/
PROJECT_ROOT = PIPELINE_DIR.parent                  # aram-insight/
DATA_DIR = PROJECT_ROOT / "data"
CHAMPIONS_PATH = DATA_DIR / "champions.json"
AUGMENTS_PATH = DATA_DIR / "augments.json"

# ---------------------------------------------------------------------------
# 常见英文别名映射 (小写 → 项目中文名)
# 涵盖 Data Dragon key 变体、官方英文名、Reddit 常见称呼
# ---------------------------------------------------------------------------
_ALIAS_MAP: dict[str, str] = {
    # 已有 16 英雄的英文名 / 变体
    "kaisa": "卡莎",
    "kai'sa": "卡莎",
    "kai sa": "卡莎",
    "wukong": "亚索",          # 实际是 MonkeyKing, 但项目中无悟空
    "monkey king": "亚索",     # fallback
    "mf": "厄运小姐",
    "miss fortune": "厄运小姐",
    "tf": "崔斯特",
    "twisted fate": "崔斯特",
    "mundo": "蒙多",
    "dr mundo": "蒙多",
    "drmundo": "蒙多",
    "j4": "嘉文四世",
    "jarvan": "嘉文四世",
    "jarvan iv": "嘉文四世",
    "lee sin": "李青",
    "leesin": "李青",
    "yi": "易",
    "master yi": "易",
    "reksai": "雷克塞",
    "rek'sai": "雷克塞",
    "tahm kench": "塔姆",
    "tahmkench": "塔姆",
    "twistedfate": "崔斯特",
    "aurelion sol": "奥瑞利安索尔",
    "aurelionsol": "奥瑞利安索尔",
}


def _normalize_key(s: str) -> str:
    """将名称转为标准化查找键：小写、去除空格和撇号。"""
    return s.lower().replace("'", "").replace("'", "").replace(" ", "").replace("-", "")


class ChampionNormalizer:
    """英雄名称标准化器，基于 champions.json 构建映射。"""

    def __init__(self, champions_path: Path = CHAMPIONS_PATH):
        self._dd_key_to_cn: dict[str, str] = {}    # DataDragonKey -> 项目中文名
        self._cn_names: set[str] = set()             # 所有已知中文名
        self._norm_lookup: dict[str, str] = {}       # 标准化键 -> 项目中文名
        self._unknown_names: set[str] = set()        # 缓存无法匹配的名称

        self._load(champions_path)

    # ------------------------------------------------------------------
    # 内部方法
    # ------------------------------------------------------------------

    def _load(self, path: Path) -> None:
        """从 champions.json 加载映射数据。"""
        if not path.exists():
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, Exception):
            return

        champion_keys = data.get("championKeys", {})
        champions = data.get("champions", [])

        # DD Key -> 中文名
        for cn_name, dd_key in champion_keys.items():
            self._dd_key_to_cn[dd_key] = cn_name
            self._cn_names.add(cn_name)
            # 注册标准化键
            self._norm_lookup[_normalize_key(dd_key)] = cn_name
            self._norm_lookup[_normalize_key(cn_name)] = cn_name

        # 注册静态别名
        for alias, cn_name in _ALIAS_MAP.items():
            self._norm_lookup[_normalize_key(alias)] = cn_name

    def _register(self, norm: str, cn_name: str) -> None:
        """注册一个映射（仅当不冲突时）。"""
        if norm and norm not in self._norm_lookup:
            self._norm_lookup[norm] = cn_name

    # ------------------------------------------------------------------
    # 公开 API
    # ------------------------------------------------------------------

    def normalize(self, name: str) -> tuple[str, bool]:
        """
        标准化英雄名称。

        Returns:
            (chinese_name, known): 中文名和是否成功匹配
        """
        if not name or name == "unknown":
            return name, False

        # 1. 完全匹配中文名
        if name in self._cn_names:
            return name, True

        # 2. 完全匹配 DD Key
        if name in self._dd_key_to_cn:
            return self._dd_key_to_cn[name], True

        # 3. 标准化键查找
        norm = _normalize_key(name)
        if norm in self._norm_lookup:
            return self._norm_lookup[norm], True

        # 4. 无法匹配
        if name not in self._unknown_names:
            self._unknown_names.add(name)
            print(f"  [normalize] 无法匹配英雄名: '{name}'")
        return name, False

    def normalize_list(self, names: list) -> list:
        """批量标准化英雄名称列表。"""
        return [self.normalize(n)[0] for n in names]

    @property
    def known_count(self) -> int:
        """已知映射数量。"""
        return len(self._dd_key_to_cn)


# ---------------------------------------------------------------------------
# 模块级单例 + 便捷函数
# ---------------------------------------------------------------------------

_normalizer: ChampionNormalizer | None = None


def _get_normalizer() -> ChampionNormalizer:
    """获取或创建全局标准化器实例。"""
    global _normalizer
    if _normalizer is None:
        _normalizer = ChampionNormalizer()
    return _normalizer


def normalize_champion_name(name: str) -> str:
    """
    标准化单个英雄名称。

    如果匹配到已知英雄，返回项目使用的中文名；
    否则返回原始名称（调用方可通过 is_champion_known() 判断）。
    """
    return _get_normalizer().normalize(name)[0]


def is_champion_known(name: str) -> bool:
    """检查英雄名是否可被标准化匹配。"""
    return _get_normalizer().normalize(name)[1]


def normalize_champion_list(names: list) -> list:
    """批量标准化英雄名称列表。"""
    return _get_normalizer().normalize_list(names)


# ===========================================================================
# 增强名称标准化
# ===========================================================================

# ---------------------------------------------------------------------------
# 静态增强别名映射 (小写 → 项目中文名)
# 涵盖 augments.json 中未列出但社区常用的称呼
# ---------------------------------------------------------------------------
_AUGMENT_ALIAS_MAP: dict[str, str] = {
    # 社区常用缩写 / 变体
    "chain": "连锁闪电",
    "toxic": "毒性增幅",
    "amp": "毒性增幅",
    "waltz": "利刃华尔兹",
    "ap round": "穿甲弹头",
    "ap rounds": "穿甲弹头",
    "execute": "毁灭凝视",
    "ult cd": "终极冷却",
    "ult cooldown": "终极冷却",
    "shield heal": "全心为你",
    "mana": "法力涌泉",
    "mana regen": "法力涌泉",
    "as": "致命节奏",
    "attack speed": "致命节奏",
    "dodge": "你摸不到",
    "ad2ap": "物理转魔法",
    "ad to ap": "物理转魔法",
    "xp": "超强大脑",
    "xp boost": "超强大脑",
    "ult hunter": "终极猎手",
    "psi": "灵能护盾",
    "psi shield": "灵能护盾",
    "move charge": "回响",
    "pd": "幻影之舞",
}


class AugmentNormalizer:
    """增强名称标准化器，基于 augments.json 构建映射。"""

    def __init__(self, augments_path: Path = AUGMENTS_PATH):
        self._cn_names: set[str] = set()            # 所有已知中文名
        self._en_to_cn: dict[str, str] = {}         # name_en -> 中文名
        self._norm_lookup: dict[str, str] = {}       # 标准化键 -> 中文名
        self._unknown_names: set[str] = set()        # 缓存无法匹配的名称

        self._load(augments_path)

    # ------------------------------------------------------------------
    # 内部方法
    # ------------------------------------------------------------------

    def _load(self, path: Path) -> None:
        """从 augments.json 加载映射数据。"""
        if not path.exists():
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, Exception):
            return

        if not isinstance(data, list):
            return

        for entry in data:
            if not isinstance(entry, dict):
                continue

            cn_name = entry.get("name", "")
            name_en = entry.get("name_en", "")
            aliases = entry.get("aliases", [])

            if not cn_name:
                continue

            self._cn_names.add(cn_name)

            # 注册中文名
            self._norm_lookup[_normalize_key(cn_name)] = cn_name

            # 注册 name_en
            if name_en:
                self._en_to_cn[name_en] = cn_name
                self._norm_lookup[_normalize_key(name_en)] = cn_name

            # 注册 aliases
            if isinstance(aliases, list):
                for alias in aliases:
                    if isinstance(alias, str) and alias:
                        self._norm_lookup[_normalize_key(alias)] = cn_name

        # 注册静态别名（不覆盖已有映射）
        for alias, cn_name in _AUGMENT_ALIAS_MAP.items():
            norm = _normalize_key(alias)
            if norm not in self._norm_lookup:
                self._norm_lookup[norm] = cn_name

    # ------------------------------------------------------------------
    # 公开 API
    # ------------------------------------------------------------------

    def normalize(self, name: str) -> tuple[str, bool]:
        """
        标准化增强名称。

        Returns:
            (chinese_name, known): 中文名和是否成功匹配
        """
        if not name or name == "unknown":
            return name, False

        # 1. 完全匹配中文名
        if name in self._cn_names:
            return name, True

        # 2. 完全匹配 name_en
        if name in self._en_to_cn:
            return self._en_to_cn[name], True

        # 3. 标准化键查找
        norm = _normalize_key(name)
        if norm in self._norm_lookup:
            return self._norm_lookup[norm], True

        # 4. 无法匹配
        if name not in self._unknown_names:
            self._unknown_names.add(name)
            print(f"  [normalize] 无法匹配增强名: '{name}'")
        return name, False

    def normalize_list(self, names: list) -> list:
        """批量标准化增强名称列表。"""
        return [self.normalize(n)[0] for n in names]

    @property
    def known_count(self) -> int:
        """已知增强映射数量。"""
        return len(self._en_to_cn)


# ---------------------------------------------------------------------------
# 模块级单例 + 便捷函数（增强名称）
# ---------------------------------------------------------------------------

_augment_normalizer: AugmentNormalizer | None = None


def _get_augment_normalizer() -> AugmentNormalizer:
    """获取或创建全局增强标准化器实例。"""
    global _augment_normalizer
    if _augment_normalizer is None:
        _augment_normalizer = AugmentNormalizer()
    return _augment_normalizer


def normalize_augment_name(name: str) -> str:
    """
    标准化单个增强名称。

    如果匹配到已知增强，返回项目使用的中文名；
    否则返回原始名称（调用方可通过 is_augment_known() 判断）。
    """
    return _get_augment_normalizer().normalize(name)[0]


def is_augment_known(name: str) -> bool:
    """检查增强名是否可被标准化匹配。"""
    return _get_augment_normalizer().normalize(name)[1]


def normalize_augment_list(names: list) -> list:
    """批量标准化增强名称列表。"""
    return _get_augment_normalizer().normalize_list(names)


# ---------------------------------------------------------------------------
# 测试入口
# ---------------------------------------------------------------------------

def _run_tests() -> None:
    """运行内置测试用例。"""
    n = ChampionNormalizer()
    an = AugmentNormalizer()

    print("=" * 64)
    print("  normalize_entities.py — 名称标准化测试")
    print("=" * 64)
    print(f"  已加载 {n.known_count} 个英雄 DD Key 映射")
    print(f"  已加载 {an.known_count} 个增强 name_en 映射")
    print()

    # ------------------------------------------------------------------
    # 英雄名称测试
    # ------------------------------------------------------------------
    print("  --- 英雄名称测试 ---")
    champion_tests = [
        # (输入, 期望输出)
        ("Brand", "布兰德"),
        ("Ziggs", "吉格斯"),
        ("Kaisa", "卡莎"),
        ("Kai'Sa", "卡莎"),
        ("Karthus", "卡尔萨斯"),
        ("Viktor", "维克托"),
        ("Varus", "韦鲁斯"),
        ("Ahri", "阿狸"),
        ("Yasuo", "亚索"),
        ("Sylas", "塞拉斯"),
        ("Vayne", "薇恩"),
        ("Morgana", "莫甘娜"),
        # 中文名直通
        ("吉格斯", "吉格斯"),
        ("卡莎", "卡莎"),
        # 大小写不敏感
        ("BRAND", "布兰德"),
        ("ziggs", "吉格斯"),
        # 未知名称
        ("UnknownChampion", "UnknownChampion"),
    ]

    passed = 0
    failed = 0

    for inp, expected in champion_tests:
        result, known = n.normalize(inp)
        ok = result == expected
        status = "✓" if ok else "✗"
        known_tag = "" if known else " [unknown]"
        print(f"  {status} {inp:20s} -> {result:10s}{known_tag}", end="")
        if not ok:
            print(f"  (期望: {expected})")
            failed += 1
        else:
            print()
            passed += 1

    # ------------------------------------------------------------------
    # 增强名称测试
    # ------------------------------------------------------------------
    print()
    print("  --- 增强名称测试 ---")
    augment_tests = [
        # 需求中指定的测试用例
        ("Chain Lightning", "连锁闪电"),
        ("Toxic Amplifier", "毒性增幅"),
        ("Blade Waltz", "利刃华尔兹"),
        ("Ultimate Cooldown", "终极冷却"),
        # name_en 完整匹配
        ("Armor Piercing", "穿甲弹头"),
        ("Annihilation Gaze", "毁灭凝视"),
        ("Lethal Tempo", "致命节奏"),
        ("Big Brain", "超强大脑"),
        ("Ultimate Hunter", "终极猎手"),
        ("Psionic Shield", "灵能护盾"),
        ("Phantom Dance", "幻影之舞"),
        # aliases 匹配
        ("chain lightning", "连锁闪电"),
        ("toxic amp", "毒性增幅"),
        ("ult cooldown", "终极冷却"),
        ("ult hunter", "终极猎手"),
        ("psi shield", "灵能护盾"),
        ("phantom dance", "幻影之舞"),
        # 大小写不敏感
        ("CHAIN LIGHTNING", "连锁闪电"),
        ("blade waltz", "利刃华尔兹"),
        # 中文名直通
        ("连锁闪电", "连锁闪电"),
        ("毒性增幅", "毒性增幅"),
        ("终极冷却", "终极冷却"),
        # 静态别名
        ("pd", "幻影之舞"),
        ("ad to ap", "物理转魔法"),
        # 新增真实增强 (name = name_en, missing_zh)
        ("Adamant", "Adamant"),
        ("adamant", "Adamant"),
        ("Goredrink", "Goredrink"),
        ("goredrink", "Goredrink"),
        ("Deft", "Deft"),
        ("Erosion", "Erosion"),
        ("Homeguard", "Homeguard"),
        ("Executioner", "Executioner"),
        ("Dashing", "Dashing"),
        ("Celestial Body", "Celestial Body"),
        ("Get Excited", "Get Excited"),
        ("Dropkick", "Dropkick"),
        ("Don't Blink", "Don't Blink"),
        ("Can't Touch This", "Can't Touch This"),
        ("Back to Basics", "Back to Basics"),
        ("Biggest Snowball Ever", "Biggest Snowball Ever"),
        # 未知增强
        ("UnknownAugment", "UnknownAugment"),
    ]

    for inp, expected in augment_tests:
        result, known = an.normalize(inp)
        ok = result == expected
        status = "✓" if ok else "✗"
        known_tag = "" if known else " [unknown]"
        print(f"  {status} {inp:24s} -> {result:10s}{known_tag}", end="")
        if not ok:
            print(f"  (期望: {expected})")
            failed += 1
        else:
            print()
            passed += 1

    print()
    print(f"  结果: {passed} 通过, {failed} 失败")
    print("=" * 64)

    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    _run_tests()
