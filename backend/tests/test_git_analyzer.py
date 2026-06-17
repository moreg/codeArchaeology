# -*- coding: utf-8 -*-
"""test_git_analyzer.py"""
import os
import gc
import tempfile
import subprocess
import pytest

from app.core.git_analyzer import GitAnalyzer, analyze_git


def _init_repo_with_commit(path):
    """初始化一个临时 git 仓库并创建一个 commit"""
    subprocess.run(["git", "init"], cwd=path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=path, check=True)
    with open(os.path.join(path, "README.md"), "w") as f:
        f.write("# Test\n")
    subprocess.run(["git", "add", "README.md"], cwd=path, check=True)
    subprocess.run(["git", "commit", "-m", "initial commit"], cwd=path, check=True, capture_output=True)


def _make_analyzer(path):
    """创建并返回 GitAnalyzer 句柄，由调用方负责 close()"""
    return GitAnalyzer(path)


def test_invalid_repo():
    with tempfile.TemporaryDirectory() as tmp:
        ga = _make_analyzer(tmp)
        try:
            assert not ga.is_valid_repo()
        finally:
            ga.close()


def test_valid_repo():
    with tempfile.TemporaryDirectory() as tmp:
        _init_repo_with_commit(tmp)
        ga = _make_analyzer(tmp)
        try:
            assert ga.is_valid_repo()
        finally:
            ga.close()


def test_get_commits():
    with tempfile.TemporaryDirectory() as tmp:
        _init_repo_with_commit(tmp)
        ga = _make_analyzer(tmp)
        try:
            commits = ga.get_commits()
            assert len(commits) >= 1
            assert "hash" in commits[0]
            assert "author" in commits[0]
            assert "message" in commits[0]
        finally:
            ga.close()


def test_get_shortlog():
    with tempfile.TemporaryDirectory() as tmp:
        _init_repo_with_commit(tmp)
        ga = _make_analyzer(tmp)
        try:
            s = ga.get_shortlog()
            assert "Test User" in s
            assert s["Test User"] >= 1
        finally:
            ga.close()


def test_get_authors():
    with tempfile.TemporaryDirectory() as tmp:
        _init_repo_with_commit(tmp)
        ga = _make_analyzer(tmp)
        try:
            authors = ga.get_authors()
            assert "Test User" in authors
            assert authors["Test User"]["commit_count"] >= 1
        finally:
            ga.close()


def test_analyze_git_function():
    with tempfile.TemporaryDirectory() as tmp:
        _init_repo_with_commit(tmp)
        result = analyze_git(tmp)
        assert result["ok"] is True
        assert result["commit_count"] >= 1


def test_get_file_modify_count():
    with tempfile.TemporaryDirectory() as tmp:
        _init_repo_with_commit(tmp)
        ga = _make_analyzer(tmp)
        try:
            n = ga.get_file_modify_count(os.path.join(tmp, "README.md"))
            assert n >= 1
        finally:
            ga.close()


def test_get_file_last_modified():
    with tempfile.TemporaryDirectory() as tmp:
        _init_repo_with_commit(tmp)
        ga = _make_analyzer(tmp)
        try:
            info = ga.get_file_last_modified(os.path.join(tmp, "README.md"))
            assert info is not None
            assert "author" in info
        finally:
            ga.close()


def test_get_file_history():
    with tempfile.TemporaryDirectory() as tmp:
        _init_repo_with_commit(tmp)
        # 再次修改
        with open(os.path.join(tmp, "README.md"), "w") as f:
            f.write("# Updated\n")
        subprocess.run(["git", "add", "README.md"], cwd=tmp, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "update"], cwd=tmp, check=True, capture_output=True)
        ga = _make_analyzer(tmp)
        try:
            history = ga.get_file_history(os.path.join(tmp, "README.md"))
            assert len(history) >= 2
        finally:
            ga.close()


def test_get_summary():
    with tempfile.TemporaryDirectory() as tmp:
        _init_repo_with_commit(tmp)
        ga = _make_analyzer(tmp)
        try:
            s = ga.get_summary()
            assert s["ok"] is True
            assert "commit_count" in s
            assert "author_count" in s
        finally:
            ga.close()