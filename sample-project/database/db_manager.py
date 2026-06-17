# -*- coding: utf-8 -*-
"""
database.db_manager — SQLite 访问层
====================================
历史原因，这里用 sqlite3 内置库，不用 ORM。
"""
import os
import sqlite3
import json
import time
import threading
import traceback
from contextlib import contextmanager

from .models import (
    CREATE_TABLES_SQL, ALL_TABLES, DEFAULT_SCHEMA_VERSION,
)
from ..utils.logger import get_logger
from ..utils.helpers import today_str, file_hash
from ..utils.decorators import retry, deprecated

log = get_logger("database.db_manager")


class DBManager:
    """数据库管理器，单例"""
    _instances = {}
    _lock = threading.Lock()

    def __new__(cls, db_path=":memory:", *args, **kwargs):
        with cls._lock:
            if db_path in cls._instances:
                return cls._instances[db_path]
            inst = super().__new__(cls)
            cls._instances[db_path] = inst
            return inst

    def __init__(self, db_path=":memory:", timeout=30, max_connections=5):
        if hasattr(self, "_initialized"):
            return
        self.db_path = db_path
        self.timeout = timeout
        self.max_connections = max_connections
        self._local = threading.local()
        self._init_lock = threading.Lock()
        self._initialized = True
        # 确保父目录存在
        if db_path != ":memory:":
            os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
        log.info("DBManager init db_path=%s", db_path)

    def _conn(self):
        """获取当前线程的连接"""
        if not hasattr(self._local, "conn") or self._local.conn is None:
            self._local.conn = sqlite3.connect(
                self.db_path,
                timeout=self.timeout,
                check_same_thread=False,
            )
            self._local.conn.row_factory = sqlite3.Row
        return self._local.conn

    @contextmanager
    def cursor(self):
        conn = self._conn()
        cur = conn.cursor()
        try:
            yield cur
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cur.close()

    def init_schema(self):
        """初始化表结构"""
        with self._init_lock:
            try:
                with self.cursor() as cur:
                    for sql in CREATE_TABLES_SQL:
                        cur.execute(sql)
                    cur.execute(
                        "INSERT OR REPLACE INTO schema_version (version) VALUES (?)",
                        (DEFAULT_SCHEMA_VERSION,),
                    )
                log.info("schema 初始化完成")
                return True
            except Exception as e:
                log.error("schema 初始化失败: %s", e)
                log.debug(traceback.format_exc())
                return False

    def save_record(self, record):
        """保存一条抓取记录"""
        if not record:
            return False
        url = record.get("url", "")
        try:
            with self.cursor() as cur:
                cur.execute(
                    """INSERT OR REPLACE INTO records
                    (url, parser, title, content, links, meta, fetched_at, raw_size, raw_hash, depth)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        url,
                        record.get("parser", ""),
                        record.get("title", ""),
                        record.get("content", ""),
                        json.dumps(record.get("links", []), ensure_ascii=False),
                        json.dumps(record.get("meta", {}), ensure_ascii=False),
                        record.get("fetched_at", today_str()),
                        record.get("raw_size", 0),
                        record.get("raw_hash", ""),
                        record.get("depth", 0),
                    ),
                )
            return True
        except Exception as e:
            log.error("save_record 失败: %s", e)
            return False

    def mark_failed(self, url, reason=""):
        try:
            with self.cursor() as cur:
                cur.execute(
                    "INSERT OR REPLACE INTO failures (url, reason, ts) VALUES (?, ?, ?)",
                    (url, reason, today_str()),
                )
            return True
        except Exception as e:
            log.error("mark_failed 失败: %s", e)
            return False

    def get_record(self, url):
        try:
            with self.cursor() as cur:
                cur.execute("SELECT * FROM records WHERE url = ?", (url,))
                row = cur.fetchone()
                if row:
                    return dict(row)
        except Exception as e:
            log.error("get_record 失败: %s", e)
        return None

    def all_records(self, limit=1000, offset=0):
        out = []
        try:
            with self.cursor() as cur:
                cur.execute(
                    "SELECT * FROM records ORDER BY fetched_at DESC LIMIT ? OFFSET ?",
                    (limit, offset),
                )
                for row in cur.fetchall():
                    d = dict(row)
                    try:
                        d["links"] = json.loads(d.get("links") or "[]")
                        d["meta"] = json.loads(d.get("meta") or "{}")
                    except Exception:
                        pass
                    out.append(d)
        except Exception as e:
            log.error("all_records 失败: %s", e)
        return out

    def stats(self):
        try:
            with self.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM records")
                total = cur.fetchone()[0]
                cur.execute("SELECT COUNT(*) FROM failures")
                failed = cur.fetchone()[0]
                cur.execute(
                    "SELECT parser, COUNT(*) c FROM records GROUP BY parser"
                )
                by_parser = {row[0]: row[1] for row in cur.fetchall()}
                cur.execute(
                    "SELECT SUM(raw_size) FROM records"
                )
                bytes_ = cur.fetchone()[0] or 0
            return {
                "total": total,
                "failed": failed,
                "by_parser": by_parser,
                "bytes": bytes_,
            }
        except Exception as e:
            log.error("stats 失败: %s", e)
            return {"total": 0, "failed": 0, "by_parser": {}, "bytes": 0}

    def vacuum(self):
        try:
            with self.cursor() as cur:
                cur.execute("VACUUM")
            return True
        except Exception as e:
            log.error("vacuum 失败: %s", e)
            return False

    def close(self):
        if hasattr(self._local, "conn") and self._local.conn:
            try:
                self._local.conn.close()
            except Exception:
                pass
            self._local.conn = None


# === 2024 年新增 ===

class DBQuery:
    """链式查询构造器"""
    def __init__(self, db, table):
        self.db = db
        self.table = table
        self._where = []
        self._params = []
        self._order_by = None
        self._limit = None
        self._offset = None

    def where(self, expr, *params):
        self._where.append(expr)
        self._params.extend(params)
        return self

    def eq(self, col, value):
        self._where.append(f"{col} = ?")
        self._params.append(value)
        return self

    def like(self, col, pattern):
        self._where.append(f"{col} LIKE ?")
        self._params.append(pattern)
        return self

    def order_by(self, col, desc=False):
        self._order_by = f"{col} {'DESC' if desc else 'ASC'}"
        return self

    def limit(self, n):
        self._limit = n
        return self

    def offset(self, n):
        self._offset = n
        return self

    def build(self):
        sql = f"SELECT * FROM {self.table}"
        if self._where:
            sql += " WHERE " + " AND ".join(self._where)
        if self._order_by:
            sql += f" ORDER BY {self._order_by}"
        if self._limit is not None:
            sql += f" LIMIT {self._limit}"
        if self._offset is not None:
            sql += f" OFFSET {self._offset}"
        return sql, self._params

    def all(self):
        sql, params = self.build()
        out = []
        try:
            with self.db.cursor() as cur:
                cur.execute(sql, params)
                for row in cur.fetchall():
                    out.append(dict(row))
        except Exception as e:
            log.error("DBQuery.all 失败: %s", e)
        return out

    def first(self):
        sql, params = self.build()
        try:
            with self.db.cursor() as cur:
                cur.execute(sql, params)
                row = cur.fetchone()
                return dict(row) if row else None
        except Exception as e:
            log.error("DBQuery.first 失败: %s", e)
        return None

    def count(self):
        sql = f"SELECT COUNT(*) FROM {self.table}"
        params = []
        if self._where:
            sql += " WHERE " + " AND ".join(self._where)
            params = self._params
        try:
            with self.db.cursor() as cur:
                cur.execute(sql, params)
                return cur.fetchone()[0]
        except Exception:
            return 0


class DBBatchWriter:
    """批量写入器, 提高性能"""
    def __init__(self, db, table, batch_size=100):
        self.db = db
        self.table = table
        self.batch_size = batch_size
        self._buffer = []

    def add(self, record):
        self._buffer.append(record)
        if len(self._buffer) >= self.batch_size:
            return self.flush()
        return 0

    def flush(self):
        if not self._buffer:
            return 0
        ok = 0
        try:
            with self.db.cursor() as cur:
                if self.table == "records":
                    for r in self._buffer:
                        cur.execute(
                            """INSERT OR REPLACE INTO records
                            (url, parser, title, content, links, meta, fetched_at, raw_size, raw_hash, depth)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                            (
                                r.get("url", ""),
                                r.get("parser", ""),
                                r.get("title", ""),
                                r.get("content", ""),
                                json.dumps(r.get("links", []), ensure_ascii=False),
                                json.dumps(r.get("meta", {}), ensure_ascii=False),
                                r.get("fetched_at", today_str()),
                                r.get("raw_size", 0),
                                r.get("raw_hash", ""),
                                r.get("depth", 0),
                            ),
                        )
                        ok += 1
        except Exception as e:
            log.error("batch flush 失败: %s", e)
        self._buffer.clear()
        return ok


class DBExporter:
    """数据导出"""
    def __init__(self, db):
        self.db = db

    def to_json(self, path, limit=10000):
        records = self.db.all_records(limit=limit)
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(records, f, ensure_ascii=False, indent=2, default=str)
            return True
        except Exception as e:
            log.error("导出 JSON 失败: %s", e)
            return False

    def to_csv(self, path, limit=10000):
        records = self.db.all_records(limit=limit)
        try:
            import csv
            with open(path, "w", encoding="utf-8", newline="") as f:
                w = csv.writer(f)
                w.writerow(["url", "parser", "title", "fetched_at", "raw_size"])
                for r in records:
                    w.writerow([
                        r.get("url", ""),
                        r.get("parser", ""),
                        r.get("title", ""),
                        r.get("fetched_at", ""),
                        r.get("raw_size", 0),
                    ])
            return True
        except Exception as e:
            log.error("导出 CSV 失败: %s", e)
            return False


# 历史遗留
def a():
    return DBManager(":memory:")


def b(db, url):
    return db.get_record(url)


def do_thing(db, limit=100):
    return db.all_records(limit=limit)


def tmp_func(db_path):
    db = DBManager(db_path)
    db.init_schema()
    return db


def healthcheck(db):
    return {
        "ok": True,
        "stats": db.stats(),
        "ts": today_str(),
    }


@deprecated("use DBManager.save_record instead")
def legacy_save(db, record):
    return db.save_record(record)


def make_query(db, table):
    return DBQuery(db, table)


def bulk_insert(db, table, records):
    """批量插入"""
    ok = 0
    if table == "records":
        for r in records:
            if db.save_record(r):
                ok += 1
    return ok


def get_or_create_record(db, url, defaults=None):
    rec = db.get_record(url)
    if rec:
        return rec
    if defaults:
        db.save_record({"url": url, **defaults})
    return db.get_record(url)


def delete_record(db, url):
    try:
        with db.cursor() as cur:
            cur.execute("DELETE FROM records WHERE url = ?", (url,))
        return True
    except Exception as e:
        log.error("delete_record 失败: %s", e)
        return False


def update_record(db, url, fields):
    if not fields:
        return False
    set_clause = ", ".join([f"{k} = ?" for k in fields.keys()])
    params = list(fields.values()) + [url]
    try:
        with db.cursor() as cur:
            cur.execute(f"UPDATE records SET {set_clause} WHERE url = ?", params)
        return True
    except Exception as e:
        log.error("update_record 失败: %s", e)
        return False


def search_records(db, keyword, limit=100):
    """按关键字搜索"""
    out = []
    try:
        with db.cursor() as cur:
            cur.execute(
                "SELECT * FROM records WHERE title LIKE ? OR content LIKE ? LIMIT ?",
                (f"%{keyword}%", f"%{keyword}%", limit),
            )
            for row in cur.fetchall():
                out.append(dict(row))
    except Exception as e:
        log.error("search_records 失败: %s", e)
    return out


def count_by_parser(db):
    out = {}
    try:
        with db.cursor() as cur:
            cur.execute("SELECT parser, COUNT(*) FROM records GROUP BY parser")
            for r in cur.fetchall():
                out[r[0]] = r[1]
    except Exception:
        pass
    return out


def top_urls(db, limit=20):
    out = []
    try:
        with db.cursor() as cur:
            cur.execute(
                "SELECT url, title, raw_size FROM records ORDER BY raw_size DESC LIMIT ?",
                (limit,),
            )
            for r in cur.fetchall():
                out.append(dict(r))
    except Exception:
        pass
    return out


def recent_records(db, limit=20):
    return db.all_records(limit=limit, offset=0)


def failure_stats(db):
    out = {}
    try:
        with db.cursor() as cur:
            cur.execute("SELECT reason, COUNT(*) FROM failures GROUP BY reason")
            for r in cur.fetchall():
                out[r[0] or "unknown"] = r[1]
    except Exception:
        pass
    return out


def clear_table(db, table):
    if table not in ("records", "failures", "tasks"):
        return False
    try:
        with db.cursor() as cur:
            cur.execute(f"DELETE FROM {table}")
        return True
    except Exception as e:
        log.error("clear_table 失败: %s", e)
        return False


def db_size(db):
    try:
        with db.cursor() as cur:
            cur.execute("SELECT page_count * page_size FROM pragma_page_count(), pragma_page_size()")
            row = cur.fetchone()
            return row[0] if row else 0
    except Exception:
        return 0


def backup_db(db, backup_path):
    import shutil
    if db.db_path == ":memory:":
        return False
    try:
        shutil.copy2(db.db_path, backup_path)
        return True
    except Exception as e:
        log.error("backup 失败: %s", e)
        return False


def restore_db(db, backup_path):
    import shutil
    if db.db_path == ":memory:":
        return False
    try:
        shutil.copy2(backup_path, db.db_path)
        db.close()
        return True
    except Exception as e:
        log.error("restore 失败: %s", e)
        return False