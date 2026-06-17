# -*- coding: utf-8 -*-
"""test_call_graph.py"""
import pytest

from app.core.call_graph import CallGraphBuilder, build_call_graph, extract_imports


def test_empty_graph():
    builder = CallGraphBuilder()
    assert builder.graph.number_of_nodes() == 0
    assert builder.graph.number_of_edges() == 0


def test_add_function():
    builder = CallGraphBuilder()
    func = {
        "id": "f1",
        "name": "foo",
        "file_path": "/a.py",
        "start_line": 1,
        "end_line": 10,
    }
    builder.add_function(func)
    assert builder.graph.has_node("f1")


def test_add_edge():
    builder = CallGraphBuilder()
    builder.add_function({"id": "f1", "name": "foo", "file_path": "/a.py", "start_line": 1, "end_line": 5})
    builder.add_function({"id": "f2", "name": "bar", "file_path": "/a.py", "start_line": 6, "end_line": 10})
    builder.add_edge("f1", "f2", call_type="direct", call_count=1)
    assert builder.graph.has_edge("f1", "f2")


def test_edge_increments_count():
    builder = CallGraphBuilder()
    builder.add_function({"id": "f1", "name": "foo", "file_path": "/a.py", "start_line": 1, "end_line": 5})
    builder.add_function({"id": "f2", "name": "bar", "file_path": "/a.py", "start_line": 6, "end_line": 10})
    builder.add_edge("f1", "f2")
    builder.add_edge("f1", "f2")
    builder.add_edge("f1", "f2")
    data = builder.graph["f1"]["f2"]
    assert data["call_count"] == 3


def test_to_graph_dict():
    builder = CallGraphBuilder()
    builder.add_function({"id": "f1", "name": "foo", "file_path": "/a.py", "start_line": 1, "end_line": 5})
    builder.add_function({"id": "f2", "name": "bar", "file_path": "/a.py", "start_line": 6, "end_line": 10})
    builder.add_edge("f1", "f2")
    d = builder.to_graph_dict()
    assert "nodes" in d
    assert "edges" in d
    assert len(d["nodes"]) == 2
    assert len(d["edges"]) == 1


def test_to_cytoscape_json():
    builder = CallGraphBuilder()
    builder.add_function({"id": "f1", "name": "foo", "file_path": "/a.py", "start_line": 1, "end_line": 5})
    j = builder.to_cytoscape_json()
    assert "nodes" in j
    assert "edges" in j
    assert all("data" in n for n in j["nodes"])


def test_extract_imports_python():
    src = """
import os
import sys as system
from collections import defaultdict
from typing import List, Dict
"""
    imports = extract_imports(src, "python")
    assert len(imports) >= 3
    modules = [i["module"] for i in imports]
    assert "os" in modules


def test_extract_imports_js():
    src = """
import React from 'react';
import { useState, useEffect } from 'react';
"""
    imports = extract_imports(src, "javascript")
    assert len(imports) >= 1


def test_extract_imports_java():
    src = """
import java.util.List;
import static org.junit.Assert.*;
"""
    imports = extract_imports(src, "java")
    assert len(imports) >= 2


def test_build_call_graph_function():
    functions = [
        {"id": "f1", "name": "foo", "file_path": "/a.py", "start_line": 1, "end_line": 5, "calls": []},
        {"id": "f2", "name": "bar", "file_path": "/a.py", "start_line": 6, "end_line": 10, "calls": []},
    ]
    g = build_call_graph(functions)
    assert "nodes" in g
    assert "edges" in g


def test_get_stats():
    builder = CallGraphBuilder()
    builder.add_function({"id": "f1", "name": "a", "file_path": "/a.py", "start_line": 1, "end_line": 5})
    builder.add_function({"id": "f2", "name": "b", "file_path": "/a.py", "start_line": 6, "end_line": 10})
    builder.add_edge("f1", "f2")
    stats = builder.get_stats()
    assert stats["node_count"] == 2
    assert stats["edge_count"] == 1


def test_most_called():
    builder = CallGraphBuilder()
    builder.add_function({"id": "f1", "name": "a", "file_path": "/a.py", "start_line": 1, "end_line": 5})
    builder.add_function({"id": "f2", "name": "b", "file_path": "/a.py", "start_line": 6, "end_line": 10})
    builder.add_function({"id": "f3", "name": "c", "file_path": "/a.py", "start_line": 11, "end_line": 15})
    builder.add_edge("f1", "f2")
    builder.add_edge("f3", "f2")
    most = builder.most_called_functions(n=5)
    assert most[0][0] == "f2"
    assert most[0][1] == 2


def test_resolve_call():
    builder = CallGraphBuilder()
    builder.add_function({"id": "f1", "name": "helper", "file_path": "/b.py", "start_line": 1, "end_line": 5})
    builder.add_function({"id": "f2", "name": "main", "file_path": "/a.py", "start_line": 1, "end_line": 10})
    target = builder.resolve_call("/a.py", "helper")
    assert target == "f1"