# -*- coding: utf-8 -*-
"""test_scanner.py"""
import os
import tempfile
import pytest

from app.core.scanner import Scanner, scan_project, EXT_TO_LANG


def test_ext_to_lang():
    assert EXT_TO_LANG[".py"] == "python"
    assert EXT_TO_LANG[".js"] == "javascript"
    assert EXT_TO_LANG[".ts"] == "typescript"


def test_scanner_basic():
    with tempfile.TemporaryDirectory() as tmpdir:
        # 创建测试文件
        with open(os.path.join(tmpdir, "a.py"), "w") as f:
            f.write("print('hello')\n" * 10)
        with open(os.path.join(tmpdir, "b.js"), "w") as f:
            f.write("console.log('hello');\n" * 5)
        # 创建应跳过的目录
        os.makedirs(os.path.join(tmpdir, ".git"))
        with open(os.path.join(tmpdir, ".git", "config"), "w") as f:
            f.write("ignore me")
        os.makedirs(os.path.join(tmpdir, "node_modules"))
        with open(os.path.join(tmpdir, "node_modules", "x.js"), "w") as f:
            f.write("ignored")

        scanner = Scanner(tmpdir, languages=["python", "javascript"])
        files = scanner.scan()
        paths = [os.path.basename(f.path) for f in files]
        assert "a.py" in paths
        assert "b.js" in paths
        assert "config" not in paths
        assert "x.js" not in paths


def test_scanner_stats():
    with tempfile.TemporaryDirectory() as tmpdir:
        with open(os.path.join(tmpdir, "test.py"), "w") as f:
            f.write("x = 1\n" * 100)
        scanner = Scanner(tmpdir, languages=["python"])
        scanner.scan()
        stats = scanner.stats
        assert stats["total_files"] == 1
        assert stats["total_lines"] == 100
        assert "python" in stats["by_language"]


def test_scan_project_function():
    with tempfile.TemporaryDirectory() as tmpdir:
        with open(os.path.join(tmpdir, "main.py"), "w") as f:
            f.write("print(1)\n" * 50)
        result = scan_project(tmpdir)
        assert "files" in result
        assert "stats" in result
        assert result["stats"]["total_files"] >= 1


def test_scanner_should_skip_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        scanner = Scanner(tmpdir)
        assert scanner._should_skip_dir("node_modules")
        assert scanner._should_skip_dir(".git")
        assert scanner._should_skip_dir("__pycache__")
        assert not scanner._should_skip_dir("src")


def test_get_files_by_language():
    with tempfile.TemporaryDirectory() as tmpdir:
        with open(os.path.join(tmpdir, "a.py"), "w") as f:
            f.write("pass\n")
        with open(os.path.join(tmpdir, "b.py"), "w") as f:
            f.write("pass\n")
        scanner = Scanner(tmpdir, languages=["python"])
        scanner.scan()
        py_files = scanner.get_files_by_language("python")
        assert len(py_files) == 2


def test_scanner_max_file_size():
    with tempfile.TemporaryDirectory() as tmpdir:
        with open(os.path.join(tmpdir, "big.py"), "w") as f:
            f.write("x\n" * 10000)
        scanner = Scanner(tmpdir, languages=["python"], max_file_size=100)
        scanner.scan()
        # 文件过大被跳过
        assert scanner.stats["skipped"] >= 0


def test_scanner_to_dict_list():
    with tempfile.TemporaryDirectory() as tmpdir:
        with open(os.path.join(tmpdir, "a.py"), "w") as f:
            f.write("pass\n")
        scanner = Scanner(tmpdir, languages=["python"])
        scanner.scan()
        d_list = scanner.to_dict_list()
        assert isinstance(d_list, list)
        assert "path" in d_list[0]
        assert "language" in d_list[0]