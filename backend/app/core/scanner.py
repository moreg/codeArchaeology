# -*- coding: utf-8 -*-
"""
app.core.scanner — 项目目录扫描器
==================================
递归遍历项目目录, 按扩展名分类, 跳过特定目录。
"""
import os
import fnmatch
from pathlib import Path
from typing import List, Dict, Generator, Optional

from ..config import settings


EXT_TO_LANG = {
    ".py": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".mjs": "javascript",
    ".cjs": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".java": "java",
    ".kt": "kotlin",
    ".go": "go",
    ".rb": "ruby",
    ".c": "c",
    ".cpp": "cpp",
    ".cc": "cpp",
    ".h": "c",
    ".hpp": "cpp",
    ".cs": "csharp",
    ".php": "php",
    ".swift": "swift",
    ".rs": "rust",
}


class FileInfo:
    """文件信息"""
    def __init__(self, path: str, language: str, size: int = 0):
        self.path = path
        self.language = language
        self.size = size
        self.lines = 0

    def __repr__(self):
        return f"<FileInfo {self.path} lang={self.language} size={self.size}>"

    def to_dict(self):
        rel = self.path
        if os.path.isabs(self.path):
            try:
                rel = os.path.relpath(self.path)
            except ValueError:
                # Windows 跨盘符时 relpath 失败，退化为 basename
                rel = os.path.basename(self.path)
        return {
            "path": self.path,
            "relative_path": rel,
            "language": self.language,
            "size": self.size,
            "lines": self.lines,
        }


class Scanner:
    """项目扫描器"""

    def __init__(self, root_path: str, languages: Optional[List[str]] = None,
                 max_file_size: Optional[int] = None,
                 skip_dirs: Optional[List[str]] = None):
        self.root_path = os.path.abspath(root_path)
        self.languages = languages or list(EXT_TO_LANG.values())
        self.languages = set(self.languages)
        self.max_file_size = max_file_size or settings.MAX_FILE_SIZE
        self.skip_dirs = set(skip_dirs or settings.SKIP_DIRS)
        self._files: List[FileInfo] = []
        self._stats = {
            "total_files": 0,
            "total_lines": 0,
            "total_size": 0,
            "by_language": {},
            "skipped": 0,
        }

    @property
    def files(self) -> List[FileInfo]:
        return self._files

    @property
    def stats(self) -> dict:
        return dict(self._stats)

    def _should_skip_dir(self, dirname: str) -> bool:
        if dirname.startswith("."):
            return True
        if dirname in self.skip_dirs:
            return True
        return False

    def _get_language(self, ext: str) -> Optional[str]:
        lang = EXT_TO_LANG.get(ext.lower())
        if lang and lang in self.languages:
            return lang
        return None

    def _read_file_info(self, path: str) -> Optional[FileInfo]:
        """一次读取获取 size 和 lines"""
        try:
            with open(path, "rb") as f:
                content = f.read()
            size = len(content)
            if size > self.max_file_size:
                self._stats["skipped"] += 1
                return None
            lines = content.count(b"\n") + (1 if content and not content.endswith(b"\n") else 0)
            ext = os.path.splitext(path)[1]
            lang = self._get_language(ext)
            if not lang:
                return None
            fi = FileInfo(path, lang, size)
            fi.lines = lines
            return fi
        except Exception:
            return None

    def walk(self) -> Generator[FileInfo, None, None]:
        """递归遍历, yield FileInfo"""
        if not os.path.exists(self.root_path):
            return
        for root, dirs, files in os.walk(self.root_path):
            dirs[:] = [d for d in dirs if not self._should_skip_dir(d)]
            for filename in files:
                full_path = os.path.join(root, filename)
                ext = os.path.splitext(filename)[1]
                if not self._get_language(ext):
                    continue
                fi = self._read_file_info(full_path)
                if fi:
                    yield fi

    def scan(self) -> List[FileInfo]:
        """执行扫描"""
        self._files.clear()
        for fi in self.walk():
            self._files.append(fi)
            self._stats["total_files"] += 1
            self._stats["total_lines"] += fi.lines
            self._stats["total_size"] += fi.size
            by_lang = self._stats["by_language"]
            by_lang[fi.language] = by_lang.get(fi.language, 0) + 1
        return self._files

    def get_files_by_language(self, language: str) -> List[FileInfo]:
        return [f for f in self._files if f.language == language]

    def to_dict_list(self) -> List[dict]:
        return [f.to_dict() for f in self._files]


def scan_project(root_path: str, languages: Optional[List[str]] = None) -> dict:
    """便捷接口: 扫描整个项目并返回结果字典"""
    scanner = Scanner(root_path, languages)
    scanner.scan()
    return {
        "root": scanner.root_path,
        "files": scanner.to_dict_list(),
        "stats": scanner.stats,
    }