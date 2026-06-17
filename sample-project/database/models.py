# -*- coding: utf-8 -*-
"""
database.models — 表结构定义
============================
"""
import json
import time

DEFAULT_SCHEMA_VERSION = 4

CREATE_TABLES_SQL = [
    """CREATE TABLE IF NOT EXISTS records (
        url TEXT PRIMARY KEY,
        parser TEXT,
        title TEXT,
        content TEXT,
        links TEXT,
        meta TEXT,
        fetched_at TEXT,
        raw_size INTEGER,
        raw_hash TEXT,
        depth INTEGER DEFAULT 0
    )""",
    """CREATE TABLE IF NOT EXISTS failures (
        url TEXT PRIMARY KEY,
        reason TEXT,
        ts TEXT
    )""",
    """CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        url TEXT,
        target TEXT,
        status TEXT,
        created_at TEXT,
        updated_at TEXT
    )""",
    """CREATE TABLE IF NOT EXISTS authors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE,
        name TEXT,
        created_at TEXT
    )""",
    """CREATE TABLE IF NOT EXISTS git_commits (
        hash TEXT PRIMARY KEY,
        author TEXT,
        email TEXT,
        message TEXT,
        committed_at TEXT,
        files_changed INTEGER
    )""",
    """CREATE TABLE IF NOT EXISTS git_blame (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        file_path TEXT,
        line_no INTEGER,
        author TEXT,
        commit_hash TEXT,
        line_content TEXT
    )""",
    """CREATE TABLE IF NOT EXISTS scan_results (
        id TEXT PRIMARY KEY,
        project_path TEXT,
        status TEXT,
        progress INTEGER,
        total INTEGER,
        started_at TEXT,
        finished_at TEXT
    )""",
    """CREATE TABLE IF NOT EXISTS analysis_results (
        id TEXT PRIMARY KEY,
        scan_id TEXT,
        node_id TEXT,
        kind TEXT,
        result TEXT,
        generated_at TEXT
    )""",
    """CREATE TABLE IF NOT EXISTS schema_version (
        version INTEGER PRIMARY KEY
    )""",
    "CREATE INDEX IF NOT EXISTS idx_records_fetched ON records(fetched_at)",
    "CREATE INDEX IF NOT EXISTS idx_records_parser ON records(parser)",
    "CREATE INDEX IF NOT EXISTS idx_failures_ts ON failures(ts)",
    "CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)",
    "CREATE INDEX IF NOT EXISTS idx_blame_file ON git_blame(file_path)",
    "CREATE INDEX IF NOT EXISTS idx_analysis_scan ON analysis_results(scan_id)",
]

ALL_TABLES = [
    "records", "failures", "tasks", "authors", "git_commits",
    "git_blame", "scan_results", "analysis_results",
    "schema_version",
]


class Record:
    """Record 模型"""

    def __init__(self, url, parser, title="", content="", links=None,
                 meta=None, fetched_at="", raw_size=0, raw_hash="", depth=0):
        self.url = url
        self.parser = parser
        self.title = title
        self.content = content
        self.links = links or []
        self.meta = meta or {}
        self.fetched_at = fetched_at
        self.raw_size = raw_size
        self.raw_hash = raw_hash
        self.depth = depth

    def to_dict(self):
        return {
            "url": self.url,
            "parser": self.parser,
            "title": self.title,
            "content": self.content,
            "links": self.links,
            "meta": self.meta,
            "fetched_at": self.fetched_at,
            "raw_size": self.raw_size,
            "raw_hash": self.raw_hash,
            "depth": self.depth,
        }

    @classmethod
    def from_dict(cls, d):
        return cls(
            url=d.get("url", ""),
            parser=d.get("parser", ""),
            title=d.get("title", ""),
            content=d.get("content", ""),
            links=d.get("links", []),
            meta=d.get("meta", {}),
            fetched_at=d.get("fetched_at", ""),
            raw_size=d.get("raw_size", 0),
            raw_hash=d.get("raw_hash", ""),
            depth=d.get("depth", 0),
        )

    def __repr__(self):
        return f"<Record {self.url} parser={self.parser}>"

    def __eq__(self, other):
        return isinstance(other, Record) and self.url == other.url

    def __hash__(self):
        return hash(self.url)


class Failure:
    def __init__(self, url, reason="", ts=""):
        self.url = url
        self.reason = reason
        self.ts = ts

    def to_dict(self):
        return {"url": self.url, "reason": self.reason, "ts": self.ts}

    @classmethod
    def from_dict(cls, d):
        return cls(d.get("url", ""), d.get("reason", ""), d.get("ts", ""))


class Task:
    def __init__(self, id=None, url="", target="", status="pending",
                 created_at="", updated_at=""):
        self.id = id
        self.url = url
        self.target = target
        self.status = status
        self.created_at = created_at
        self.updated_at = updated_at

    def to_dict(self):
        return {
            "id": self.id,
            "url": self.url,
            "target": self.target,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, d):
        return cls(
            id=d.get("id"),
            url=d.get("url", ""),
            target=d.get("target", ""),
            status=d.get("status", "pending"),
            created_at=d.get("created_at", ""),
            updated_at=d.get("updated_at", ""),
        )


class Author:
    def __init__(self, id=None, email="", name="", created_at=""):
        self.id = id
        self.email = email
        self.name = name
        self.created_at = created_at

    def to_dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "name": self.name,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, d):
        return cls(
            id=d.get("id"),
            email=d.get("email", ""),
            name=d.get("name", ""),
            created_at=d.get("created_at", ""),
        )


class GitCommit:
    def __init__(self, hash, author="", email="", message="",
                 committed_at="", files_changed=0):
        self.hash = hash
        self.author = author
        self.email = email
        self.message = message
        self.committed_at = committed_at
        self.files_changed = files_changed

    def to_dict(self):
        return {
            "hash": self.hash,
            "author": self.author,
            "email": self.email,
            "message": self.message,
            "committed_at": self.committed_at,
            "files_changed": self.files_changed,
        }

    @classmethod
    def from_dict(cls, d):
        return cls(
            hash=d.get("hash", ""),
            author=d.get("author", ""),
            email=d.get("email", ""),
            message=d.get("message", ""),
            committed_at=d.get("committed_at", ""),
            files_changed=d.get("files_changed", 0),
        )


class GitBlame:
    def __init__(self, file_path, line_no, author="", commit_hash="",
                 line_content=""):
        self.file_path = file_path
        self.line_no = line_no
        self.author = author
        self.commit_hash = commit_hash
        self.line_content = line_content

    def to_dict(self):
        return {
            "file_path": self.file_path,
            "line_no": self.line_no,
            "author": self.author,
            "commit_hash": self.commit_hash,
            "line_content": self.line_content,
        }

    @classmethod
    def from_dict(cls, d):
        return cls(
            file_path=d.get("file_path", ""),
            line_no=d.get("line_no", 0),
            author=d.get("author", ""),
            commit_hash=d.get("commit_hash", ""),
            line_content=d.get("line_content", ""),
        )


class ScanResult:
    def __init__(self, id, project_path="", status="pending", progress=0,
                 total=0, started_at="", finished_at=""):
        self.id = id
        self.project_path = project_path
        self.status = status
        self.progress = progress
        self.total = total
        self.started_at = started_at
        self.finished_at = finished_at

    def to_dict(self):
        return {
            "id": self.id,
            "project_path": self.project_path,
            "status": self.status,
            "progress": self.progress,
            "total": self.total,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
        }


class AnalysisResult:
    def __init__(self, id, scan_id="", node_id="", kind="",
                 result=None, generated_at=""):
        self.id = id
        self.scan_id = scan_id
        self.node_id = node_id
        self.kind = kind
        self.result = result
        self.generated_at = generated_at

    def to_dict(self):
        return {
            "id": self.id,
            "scan_id": self.scan_id,
            "node_id": self.node_id,
            "kind": self.kind,
            "result": self.result,
            "generated_at": self.generated_at,
        }


def a():
    return Record("", "")


def b(d):
    return Record.from_dict(d)


def do_thing(r):
    return r.to_dict()


def tmp_func(rec):
    return isinstance(rec, Record) and bool(rec.url)


def model_to_dict(obj):
    if hasattr(obj, "to_dict"):
        return obj.to_dict()
    return dict(obj)


def dict_to_model(d, cls):
    if hasattr(cls, "from_dict"):
        return cls.from_dict(d)
    return cls(**d)


def validate_record(record):
    if not isinstance(record, dict):
        return False
    return bool(record.get("url"))


def validate_commit(commit):
    if not isinstance(commit, dict):
        return False
    return bool(commit.get("hash"))


def validate_blame(blame):
    if not isinstance(blame, dict):
        return False
    return bool(blame.get("file_path")) and blame.get("line_no") is not None


# === 模型工厂 ===
class ModelFactory:
    """根据 kind 返回对应的 model 类"""
    @staticmethod
    def get(kind):
        return {
            "record": Record,
            "failure": Failure,
            "task": Task,
            "author": Author,
            "commit": GitCommit,
            "blame": GitBlame,
            "scan": ScanResult,
            "analysis": AnalysisResult,
        }.get(kind)


def make_model(kind, **kwargs):
    cls = ModelFactory.get(kind)
    if cls is None:
        return None
    return cls(**kwargs)


def dump_records(records):
    return [r.to_dict() if hasattr(r, "to_dict") else r for r in records]


def load_records(dicts):
    return [Record.from_dict(d) for d in dicts]


def dump_commits(commits):
    return [c.to_dict() if hasattr(c, "to_dict") else c for c in commits]


def load_commits(dicts):
    return [GitCommit.from_dict(d) for d in dicts]


def sort_by_field(items, field, desc=False):
    return sorted(items, key=lambda x: x.get(field, "") if isinstance(x, dict) else getattr(x, field, ""), reverse=desc)


def filter_records_by_date(records, since=None, until=None):
    """按日期过滤"""
    out = []
    for r in records:
        d = r.get("fetched_at", "") if isinstance(r, dict) else getattr(r, "fetched_at", "")
        if since and d < since:
            continue
        if until and d > until:
            continue
        out.append(r)
    return out


def records_by_parser(records):
    """按 parser 分组"""
    out = {}
    for r in records:
        p = r.get("parser", "") if isinstance(r, dict) else getattr(r, "parser", "")
        if p not in out:
            out[p] = []
        out[p].append(r)
    return out


def records_by_author(records):
    """按 author 分组"""
    out = {}
    for r in records:
        a = r.get("author", "") if isinstance(r, dict) else getattr(r, "author", "")
        if a not in out:
            out[a] = []
        out[a].append(r)
    return out


def merge_models(*lists):
    out = []
    seen = set()
    for lst in lists:
        for item in lst:
            key = None
            if isinstance(item, dict):
                key = item.get("url") or item.get("hash") or id(item)
            else:
                key = getattr(item, "url", None) or getattr(item, "hash", None) or id(item)
            if key in seen:
                continue
            seen.add(key)
            out.append(item)
    return out


def chunk_models(items, size=100):
    return [items[i:i+size] for i in range(0, len(items), size)]


# === 模型字段定义 ===
RECORD_FIELDS = [
    "url", "parser", "title", "content", "links", "meta",
    "fetched_at", "raw_size", "raw_hash", "depth",
]

COMMIT_FIELDS = [
    "hash", "author", "email", "message", "committed_at", "files_changed",
]

BLAME_FIELDS = [
    "file_path", "line_no", "author", "commit_hash", "line_content",
]

TASK_FIELDS = [
    "id", "url", "target", "status", "created_at", "updated_at",
]

AUTHOR_FIELDS = [
    "id", "email", "name", "created_at",
]


def get_field_names(model_name):
    return {
        "record": RECORD_FIELDS,
        "commit": COMMIT_FIELDS,
        "blame": BLAME_FIELDS,
        "task": TASK_FIELDS,
        "author": AUTHOR_FIELDS,
    }.get(model_name, [])


# === 模型序列化 ===
def serialize(obj):
    """序列化单个对象"""
    if obj is None:
        return None
    if isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, (list, tuple)):
        return [serialize(x) for x in obj]
    if isinstance(obj, dict):
        return {k: serialize(v) for k, v in obj.items()}
    if hasattr(obj, "to_dict"):
        return serialize(obj.to_dict())
    return str(obj)


def deserialize(data, cls=None):
    """反序列化"""
    if data is None:
        return None
    if cls is not None and hasattr(cls, "from_dict"):
        return cls.from_dict(data)
    return data