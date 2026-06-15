#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_validate.py — 海克斯乱斗实验室 基础数据测试

使用 Python 内置 unittest 模块，校验 data/ 目录下 JSON 数据文件的
完整性和 validate_data.py 脚本的退出码。

用法：
    python tests/test_validate.py
"""

import io
import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

# ---------------------------------------------------------------------------
# Windows 终端 UTF-8 兼容（使用 io.TextIOWrapper）
# ---------------------------------------------------------------------------
if sys.platform == "win32":
    try:
        sys.stdout = io.TextIOWrapper(
            sys.stdout.buffer, encoding="utf-8", errors="replace"
        )
        sys.stderr = io.TextIOWrapper(
            sys.stderr.buffer, encoding="utf-8", errors="replace"
        )
    except Exception:
        pass

# ---------------------------------------------------------------------------
# 路径配置
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
DATA_DIR = PROJECT_ROOT / "data"
VALIDATE_SCRIPT = PROJECT_ROOT / "scripts" / "validate_data.py"

# Python 可执行文件路径
PYTHON_EXE = r"C:\Users\Shmily\AppData\Local\Python\bin\python3.exe"
if not Path(PYTHON_EXE).exists():
    # 回退到当前 Python 解释器
    PYTHON_EXE = sys.executable


class TestValidateScript(unittest.TestCase):
    """测试 validate_data.py 脚本退出码。"""

    def test_validate_exits_with_zero(self) -> None:
        """validate_data.py 在当前数据上应以退出码 0 结束。"""
        result = subprocess.run(
            [PYTHON_EXE, str(VALIDATE_SCRIPT)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            cwd=str(PROJECT_ROOT),
            timeout=60,
        )
        self.assertEqual(
            result.returncode,
            0,
            f"validate_data.py 退出码非零 ({result.returncode})。\n"
            f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}",
        )


class TestJSONValidity(unittest.TestCase):
    """测试 data/ 目录下所有 JSON 文件的解析合法性。"""

    def _json_files(self) -> list[Path]:
        """返回 data/ 目录下所有 .json 文件路径。"""
        return sorted(DATA_DIR.glob("*.json"))

    def test_all_json_files_are_valid(self) -> None:
        """data/ 下每个 .json 文件都应能被 json.load() 正确解析。"""
        json_files = self._json_files()
        self.assertGreater(len(json_files), 0, "data/ 目录下没有找到任何 JSON 文件")
        for filepath in json_files:
            with self.subTest(file=filepath.name):
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        json.load(f)
                except json.JSONDecodeError as e:
                    self.fail(f"JSON 解析失败: {filepath.name} — {e}")
                except Exception as e:
                    self.fail(f"读取失败: {filepath.name} — {e}")


class TestChampionsJSON(unittest.TestCase):
    """测试 champions.json 的结构完整性。"""

    @classmethod
    def setUpClass(cls) -> None:
        cls.filepath = DATA_DIR / "champions.json"
        if not cls.filepath.exists():
            raise unittest.SkipTest(f"文件不存在: {cls.filepath}")
        with open(cls.filepath, "r", encoding="utf-8") as f:
            cls.data = json.load(f)

    def test_has_champion_keys_field(self) -> None:
        """champions.json 应包含顶层字段 championKeys。"""
        self.assertIn(
            "championKeys",
            self.data,
            "champions.json 缺少顶层字段: championKeys",
        )

    def test_champion_keys_is_dict(self) -> None:
        """championKeys 应为字典类型。"""
        self.assertIsInstance(
            self.data.get("championKeys"),
            dict,
            "championKeys 应为 object/dict",
        )

    def test_has_champions_field(self) -> None:
        """champions.json 应包含顶层字段 champions。"""
        self.assertIn(
            "champions",
            self.data,
            "champions.json 缺少顶层字段: champions",
        )

    def test_champions_is_list(self) -> None:
        """champions 应为数组。"""
        self.assertIsInstance(
            self.data.get("champions"),
            list,
            "champions 应为数组",
        )


class TestAugmentsJSON(unittest.TestCase):
    """测试 augments.json 各条目的必需字段。"""

    REQUIRED_FIELDS = {"id", "name", "tier", "status"}

    @classmethod
    def setUpClass(cls) -> None:
        cls.filepath = DATA_DIR / "augments.json"
        if not cls.filepath.exists():
            raise unittest.SkipTest(f"文件不存在: {cls.filepath}")
        with open(cls.filepath, "r", encoding="utf-8") as f:
            cls.data = json.load(f)

    def test_top_level_is_list(self) -> None:
        """augments.json 顶层应为数组。"""
        self.assertIsInstance(
            self.data,
            list,
            f"augments.json 顶层应为数组，实际为 {type(self.data).__name__}",
        )

    def test_entries_have_required_fields(self) -> None:
        """每条增强记录都应包含 id, name, tier, status 字段。"""
        self.assertGreater(len(self.data), 0, "augments.json 为空数组")
        for i, entry in enumerate(self.data):
            if not isinstance(entry, dict):
                self.fail(f"第 {i + 1} 条应为 object，实际为 {type(entry).__name__}")
            missing = self.REQUIRED_FIELDS - set(entry.keys())
            self.assertFalse(
                missing,
                f"第 {i + 1} 条增强缺少字段: {', '.join(sorted(missing))}",
            )

    def test_id_field_non_empty(self) -> None:
        """每条增强的 id 字段不应为空字符串。"""
        for i, entry in enumerate(self.data):
            if not isinstance(entry, dict):
                continue
            aug_id = entry.get("id")
            if aug_id is not None:
                self.assertTrue(
                    isinstance(aug_id, str) and aug_id.strip(),
                    f"第 {i + 1} 条增强的 id 为空或类型错误",
                )

    def test_name_field_non_empty(self) -> None:
        """每条增强的 name 字段不应为空字符串。"""
        for i, entry in enumerate(self.data):
            if not isinstance(entry, dict):
                continue
            name = entry.get("name")
            if name is not None:
                self.assertTrue(
                    isinstance(name, str) and name.strip(),
                    f"第 {i + 1} 条增强的 name 为空或类型错误",
                )


if __name__ == "__main__":
    unittest.main(verbosity=2)
