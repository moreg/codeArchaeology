# -*- coding: utf-8 -*-
"""test_parser.py"""
import os
import tempfile
import pytest

from app.core.parser import CodeParser, parse_file, compute_complexity, FunctionInfo


def test_function_info_basic():
    fi = FunctionInfo(name="foo", file_path="/a.py", start_line=1, end_line=10)
    assert fi.name == "foo"
    assert fi.line_count == 10
    assert fi.complexity == 1
    assert fi.id.startswith("func_")


def test_parser_python_simple():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "test.py")
        with open(path, "w") as f:
            f.write('''
def hello():
    """doc"""
    return "hello"

def world(x):
    if x:
        return x
    return None
''')
        result = parse_file(path)
        assert "functions" in result
        names = [f["name"] for f in result["functions"]]
        assert "hello" in names
        assert "world" in names


def test_parser_with_class():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "test.py")
        with open(path, "w") as f:
            f.write('''
class MyClass:
    def method1(self):
        return 1
    def method2(self, x):
        if x > 0:
            return x
        return 0
''')
        result = parse_file(path)
        names = [f["name"] for f in result["functions"]]
        assert "method1" in names
        assert "method2" in names


def test_complexity_calculation():
    parser = CodeParser("python")
    src = """
def complex_func(x):
    if x > 0:
        return x
    elif x < 0:
        return -x
    else:
        return 0
"""
    cc = parser._compute_complexity(parser.parse_source(src).root_node)
    assert cc > 1


def test_compute_complexity():
    src = """
def f(x):
    if x:
        for i in range(10):
            while True:
                break
"""
    cc = compute_complexity(src)
    assert cc > 3


def test_parser_invalid_file():
    result = parse_file("/nonexistent/path/file.py")
    assert "functions" in result
    assert "error" in result or len(result["functions"]) == 0


def test_parser_handles_empty():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "empty.py")
        with open(path, "w") as f:
            f.write("")
        result = parse_file(path)
        assert result["functions"] == []


def test_function_to_dict():
    fi = FunctionInfo(
        name="test_func",
        file_path="/a.py",
        start_line=1,
        end_line=5,
        language="python",
        class_name="MyClass",
    )
    fi.complexity = 5
    fi.calls = ["foo", "bar"]
    fi.parameters = ["x", "y"]
    d = fi.to_dict()
    assert d["name"] == "test_func"
    assert d["class_name"] == "MyClass"
    assert d["complexity"] == 5
    assert d["calls"] == ["foo", "bar"]
    assert d["line_count"] == 5