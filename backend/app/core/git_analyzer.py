# -*- coding: utf-8 -*-
"""
app.core.git_analyzer — Git 分析器
===================================
用 GitPython 提取 blame、log、shortlog、文件耦合度。
"""
import os
from typing import List, Dict, Optional, Any

from ..utils.logger import get_logger

log = get_logger("core.git_analyzer")

try:
    import git
    from git import Repo, Actor
    HAS_GIT = True
except ImportError:
    HAS_GIT = False
    Repo = None


class GitAnalyzer:
    """Git 分析器"""

    def __init__(self, repo_path: str):
        self.repo_path = os.path.abspath(repo_path)
        self.repo: Optional[Any] = None
        if HAS_GIT:
            try:
                self.repo = Repo(self.repo_path)
            except Exception as e:
                log.error("打开 repo 失败: %s", e)
                self.repo = None

    def close(self) -> None:
        """显式关闭底层 Repo 句柄，释放 .git 目录的文件锁（Windows 上需要）"""
        if self.repo is not None:
            try:
                # gitpython 0.3+ 提供 close()
                if hasattr(self.repo, "close"):
                    self.repo.close()
            except Exception as e:
                log.warning("关闭 repo 失败: %s", e)
            self.repo = None

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass

    def is_valid_repo(self) -> bool:
        return self.repo is not None

    def get_commits(self, max_count: int = 500, branch: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取 commit 列表"""
        if not self.repo:
            return []
        out = []
        try:
            kwargs = {"max_count": max_count}
            if branch:
                kwargs["rev"] = branch
            for c in self.repo.iter_commits(**kwargs):
                out.append({
                    "hash": c.hexsha[:7],
                    "short_hash": c.hexsha[:7],
                    "full_hash": c.hexsha,
                    "author": c.author.name if c.author else "unknown",
                    "email": c.author.email if c.author else "",
                    "message": c.message.strip() if c.message else "",
                    "committed_at": c.committed_datetime.isoformat() if c.committed_datetime else "",
                    "authored_at": c.authored_datetime.isoformat() if c.authored_datetime else "",
                    "files_changed": len(c.stats.files) if c.stats else 0,
                })
        except Exception as e:
            log.error("get_commits 失败: %s", e)
        return out

    def get_authors(self) -> Dict[str, Dict[str, Any]]:
        """获取作者统计"""
        if not self.repo:
            return {}
        out = {}
        try:
            for c in self.repo.iter_commits():
                name = c.author.name if c.author else "unknown"
                if name not in out:
                    out[name] = {
                        "name": name,
                        "email": c.author.email if c.author else "",
                        "commit_count": 0,
                        "first_commit": c.committed_datetime.isoformat() if c.committed_datetime else "",
                        "last_commit": c.committed_datetime.isoformat() if c.committed_datetime else "",
                    }
                out[name]["commit_count"] += 1
                if c.committed_datetime:
                    iso = c.committed_datetime.isoformat()
                    if iso < out[name]["first_commit"]:
                        out[name]["first_commit"] = iso
                    if iso > out[name]["last_commit"]:
                        out[name]["last_commit"] = iso
        except Exception as e:
            log.error("get_authors 失败: %s", e)
        return out

    def get_blame(self, file_path: str) -> List[Dict[str, Any]]:
        """获取文件的 blame 信息"""
        if not self.repo:
            return []
        out = []
        try:
            rel_path = os.path.relpath(file_path, self.repo_path)
            blame = self.repo.blame(rel_path, incremental=False)
            # blame 返回 (commit, lines) 列表
            for commit, lines in blame:
                for line in lines:
                    out.append({
                        "commit_hash": commit.hexsha[:7],
                        "full_commit_hash": commit.hexsha,
                        "author": commit.author.name if commit.author else "unknown",
                        "email": commit.author.email if commit.author else "",
                        "committed_at": commit.committed_datetime.isoformat() if commit.committed_datetime else "",
                        "message": commit.message.strip()[:80] if commit.message else "",
                        "line": line.decode("utf-8", errors="ignore").rstrip("\n"),
                    })
        except Exception as e:
            log.error("get_blame 失败: %s", e)
        return out

    def get_file_blame_by_line(self, file_path: str) -> Dict[int, Dict[str, Any]]:
        """按行号返回 blame"""
        out = {}
        try:
            blame_data = self.get_blame(file_path)
            for i, item in enumerate(blame_data, 1):
                out[i] = item
        except Exception:
            pass
        return out

    def get_file_history(self, file_path: str, max_count: int = 50) -> List[Dict[str, Any]]:
        """获取文件修改历史"""
        if not self.repo:
            return []
        out = []
        try:
            rel_path = os.path.relpath(file_path, self.repo_path)
            commits = list(self.repo.iter_commits(paths=rel_path, max_count=max_count))
            for c in commits:
                out.append({
                    "hash": c.hexsha[:7],
                    "full_hash": c.hexsha,
                    "author": c.author.name if c.author else "unknown",
                    "email": c.author.email if c.author else "",
                    "message": c.message.strip() if c.message else "",
                    "committed_at": c.committed_datetime.isoformat() if c.committed_datetime else "",
                    "files_changed": len(c.stats.files) if c.stats else 0,
                })
        except Exception as e:
            log.error("get_file_history 失败: %s", e)
        return out

    def get_file_modify_count(self, file_path: str) -> int:
        """获取文件被修改的次数"""
        if not self.repo:
            return 0
        try:
            rel_path = os.path.relpath(file_path, self.repo_path)
            count = 0
            for _ in self.repo.iter_commits(paths=rel_path):
                count += 1
            return count
        except Exception:
            return 0

    def get_file_coupling(self, file_path: str, top_n: int = 10) -> List[Dict[str, Any]]:
        """找出经常和 file_path 一起修改的文件"""
        if not self.repo:
            return []
        try:
            rel_path = os.path.relpath(file_path, self.repo_path)
            coupling: Dict[str, int] = {}
            for c in self.repo.iter_commits(paths=rel_path):
                files = list(c.stats.files.keys()) if c.stats else []
                for f in files:
                    if f != rel_path:
                        coupling[f] = coupling.get(f, 0) + 1
            sorted_coupling = sorted(coupling.items(), key=lambda x: x[1], reverse=True)
            return [{"file": k, "co_change_count": v} for k, v in sorted_coupling[:top_n]]
        except Exception:
            return []

    def get_shortlog(self) -> Dict[str, int]:
        """按作者统计 commit 数"""
        if not self.repo:
            return {}
        out = {}
        try:
            for c in self.repo.iter_commits():
                name = c.author.name if c.author else "unknown"
                out[name] = out.get(name, 0) + 1
        except Exception:
            pass
        return out

    def get_file_last_modified(self, file_path: str) -> Optional[Dict[str, Any]]:
        """获取文件最后修改信息"""
        if not self.repo:
            return None
        try:
            rel_path = os.path.relpath(file_path, self.repo_path)
            commits = list(self.repo.iter_commits(paths=rel_path, max_count=1))
            if not commits:
                return None
            c = commits[0]
            return {
                "hash": c.hexsha[:7],
                "author": c.author.name if c.author else "unknown",
                "email": c.author.email if c.author else "",
                "committed_at": c.committed_datetime.isoformat() if c.committed_datetime else "",
                "message": c.message.strip() if c.message else "",
            }
        except Exception:
            return None

    def get_function_blame(self, file_path: str, start_line: int, end_line: int) -> Dict[str, Any]:
        """获取某个函数范围的 blame 汇总"""
        blame = self.get_blame(file_path)
        if not blame:
            return {"author": "unknown", "commit_hash": "", "lines": []}
        authors = {}
        commits = set()
        for i, item in enumerate(blame, 1):
            if start_line <= i <= end_line:
                authors[item["author"]] = authors.get(item["author"], 0) + 1
                commits.add(item["commit_hash"])
        if not authors:
            return {"author": "unknown", "commit_hash": "", "lines": []}
        main_author = max(authors.items(), key=lambda x: x[1])[0]
        # 取最早 commit
        first_commit = ""
        if blame and start_line <= 1 <= end_line:
            first_commit = blame[start_line - 1]["commit_hash"] if start_line - 1 < len(blame) else ""
        return {
            "author": main_author,
            "commit_hash": first_commit,
            "authors": authors,
            "commits": list(commits),
            "lines_count": sum(authors.values()),
        }

    def get_summary(self) -> Dict[str, Any]:
        """仓库总览"""
        if not self.repo:
            return {"ok": False}
        try:
            commits = self.get_commits(max_count=10000)
            authors = self.get_authors()
            return {
                "ok": True,
                "commit_count": len(commits),
                "author_count": len(authors),
                "authors": authors,
                "first_commit": commits[-1]["committed_at"] if commits else "",
                "last_commit": commits[0]["committed_at"] if commits else "",
                "branches": [b.name for b in self.repo.branches],
            }
        except Exception as e:
            return {"ok": False, "error": str(e)}


def analyze_git(repo_path: str) -> Dict[str, Any]:
    """便捷接口"""
    analyzer = GitAnalyzer(repo_path)
    return analyzer.get_summary()