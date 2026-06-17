# -*- coding: utf-8 -*-
"""test_scoring.py"""
import pytest

from app.core.scoring import (
    score_complexity, score_duplication, score_comment,
    score_author_centrality, score_test_coverage,
    get_rating, find_hot_spots, ScoringEngine, compute_total_score,
)


def test_score_complexity_empty():
    assert score_complexity([]) == 100.0


def test_score_complexity_low():
    funcs = [{"complexity": 5}] * 5
    assert score_complexity(funcs) == 100.0


def test_score_complexity_high():
    funcs = [{"complexity": 70}] * 5
    s = score_complexity(funcs)
    assert s < 50


def test_score_complexity_medium():
    funcs = [{"complexity": 15}] * 5
    s = score_complexity(funcs)
    assert 0 < s < 100


def test_score_duplication_empty():
    assert score_duplication({}) == 100.0


def test_score_duplication_high():
    dup = "x" * 200
    sources = {"a": dup, "b": dup, "c": dup}
    s = score_duplication(sources)
    assert s < 100


def test_score_duplication_unique():
    sources = {
        "a": "def f1():\n    pass\n" * 5,
        "b": "def f2():\n    pass\n" * 5,
    }
    s = score_duplication(sources)
    assert s >= 90


def test_score_comment_empty():
    assert score_comment({}) == 0.0


def test_score_comment_high():
    sources = {"a": "# comment\n" * 50 + "pass\n" * 50}
    s = score_comment(sources)
    assert s == 50.0


def test_score_comment_low():
    sources = {"a": "pass\n" * 100}
    s = score_comment(sources)
    assert s == 0.0


def test_score_author_centrality_single():
    s = score_author_centrality({"alice": 100})
    # 单个作者基尼系数 = 0
    assert s == 100.0


def test_score_author_centrality_balanced():
    s = score_author_centrality({"a": 10, "b": 10, "c": 10})
    # 均衡分布
    assert s >= 90


def test_score_author_centrality_skewed():
    s = score_author_centrality({"alice": 100, "bob": 1})
    # 极度不均衡（100:1 的基尼系数 ~0.49，反向得分 < 55）
    assert s < 55


def test_score_author_centrality_empty():
    assert score_author_centrality({}) == 0.0


def test_score_test_coverage_full():
    import tempfile
    import os
    with tempfile.TemporaryDirectory() as tmp:
        f1 = os.path.join(tmp, "main.py")
        f2 = os.path.join(tmp, "test_main.py")
        with open(f1, "w") as f:
            f.write("x = 1\n" * 100)
        with open(f2, "w") as f:
            f.write("y = 2\n" * 50)
        s = score_test_coverage([f1, f2], [f2])
        assert s > 0


def test_score_test_coverage_empty():
    assert score_test_coverage([], []) == 0.0


def test_get_rating():
    assert get_rating(95)[0] == "excellent"
    assert get_rating(80)[0] == "good"
    assert get_rating(60)[0] == "fair"
    assert get_rating(40)[0] == "warning"
    assert get_rating(10)[0] == "danger"


def test_compute_total_score():
    dims = {"a": 80, "b": 60, "c": 40}
    weights = {"a": 0.5, "b": 0.3, "c": 0.2}
    total = compute_total_score(dims, weights)
    assert total == 66.0


def test_compute_total_score_default():
    dims = {"a": 60, "b": 80}
    total = compute_total_score(dims)
    assert total == 70.0


def test_find_hot_spots_empty():
    spots = find_hot_spots([])
    assert spots == []


def test_find_hot_spots_extreme():
    funcs = [{"name": "x", "file_path": "/a.py", "complexity": 67, "line_count": 100}]
    spots = find_hot_spots(funcs)
    assert len(spots) == 1
    assert spots[0]["severity"] == "extreme"
    assert spots[0]["severity_color"] == "#F44336"


def test_find_hot_spots_high():
    funcs = [{"name": "x", "file_path": "/a.py", "complexity": 35, "line_count": 50}]
    spots = find_hot_spots(funcs)
    assert spots[0]["severity"] == "high"


def test_find_hot_spots_low():
    funcs = [{"name": "x", "file_path": "/a.py", "complexity": 5, "line_count": 10}]
    spots = find_hot_spots(funcs)
    assert spots[0]["severity"] == "low"


def test_scoring_engine_full():
    engine = ScoringEngine()
    ctx = {
        "functions": [{"complexity": 5, "name": "f", "file_path": "/a.py",
                       "start_line": 1, "end_line": 5, "line_count": 5}],
        "source_by_file": {"a.py": "# comment\npass\n"},
        "authors": {"alice": 10, "bob": 10},
        "all_files": [],
        "test_files": [],
    }
    result = engine.score(ctx)
    assert "total_score" in result
    assert "rating" in result
    assert "rating_color" in result
    assert "dimensions" in result
    assert "hot_spots" in result
    assert all(k in result["dimensions"] for k in
               ["complexity", "duplication", "comment", "author_centrality", "test_coverage"])


def test_scoring_engine_custom_weights():
    engine = ScoringEngine(weights={
        "complexity": 0.5,
        "duplication": 0.5,
        "comment": 0.0,
        "author_centrality": 0.0,
        "test_coverage": 0.0,
    })
    ctx = {
        "functions": [{"complexity": 5, "name": "f", "file_path": "/a.py",
                       "start_line": 1, "end_line": 5, "line_count": 5}],
        "source_by_file": {},
        "authors": {},
        "all_files": [],
        "test_files": [],
    }
    result = engine.score(ctx)
    assert "total_score" in result