# -*- coding: utf-8 -*-
"""
database.migrations — 迁移脚本
================================
"""
import sqlite3
import traceback
import time
import hashlib

from .models import DEFAULT_SCHEMA_VERSION
from ..utils.logger import get_logger

log = get_logger("database.migrations")

# 历史迁移链
MIGRATIONS = [
    # v1 -> v2
    ("ALTER TABLE records ADD COLUMN depth INTEGER DEFAULT 0", 2),
    # v2 -> v3
    ("ALTER TABLE records ADD COLUMN raw_hash TEXT DEFAULT ''", 3),
    # v3 -> v4
    ("CREATE INDEX IF NOT EXISTS idx_records_depth ON records(depth)", 4),
    # v4 -> v5
    ("ALTER TABLE records ADD COLUMN author TEXT DEFAULT ''", 5),
    # v5 -> v6
    ("CREATE TABLE IF NOT EXISTS scan_results (id TEXT PRIMARY KEY, status TEXT)", 6),
    # v6 -> v7
    ("CREATE INDEX IF NOT EXISTS idx_scan_status ON scan_results(status)", 7),
    # v7 -> v8
    ("ALTER TABLE records ADD COLUMN parser_version TEXT DEFAULT ''", 8),
    # v8 -> v9
    ("CREATE TABLE IF NOT EXISTS analysis_results (id TEXT PRIMARY KEY, scan_id TEXT)", 9),
    # v9 -> v10
    ("CREATE INDEX IF NOT EXISTS idx_analysis_scan ON analysis_results(scan_id)", 10),
]


def get_current_version(conn):
    try:
        cur = conn.cursor()
        cur.execute("SELECT MAX(version) FROM schema_version")
        row = cur.fetchone()
        return row[0] if row and row[0] else 0
    except Exception:
        return 0


def set_version(conn, version):
    cur = conn.cursor()
    cur.execute("INSERT OR REPLACE INTO schema_version (version) VALUES (?)", (version,))
    conn.commit()


def migrate(conn):
    """执行所有迁移"""
    cur_ver = get_current_version(conn)
    log.info("当前 schema 版本: %d, 目标版本: %d", cur_ver, DEFAULT_SCHEMA_VERSION)
    for sql, target_ver in MIGRATIONS:
        if target_ver > cur_ver:
            try:
                cur = conn.cursor()
                cur.execute(sql)
                conn.commit()
                set_version(conn, target_ver)
                log.info("迁移到 v%d 完成", target_ver)
            except sqlite3.OperationalError as e:
                if "duplicate column" in str(e).lower() or "already exists" in str(e).lower():
                    log.warning("迁移 v%d 已是最新", target_ver)
                    set_version(conn, target_ver)
                else:
                    log.error("迁移 v%d 失败: %s", target_ver, e)
                    raise
    return True


def a():
    return MIGRATIONS


def b():
    return DEFAULT_SCHEMA_VERSION


def do_thing(conn):
    return migrate(conn)


def tmp_func(v):
    return any(t == v for _, t in MIGRATIONS)


def rollback(conn, target_version):
    """回滚到目标版本"""
    log.warning("回滚到 v%d", target_version)
    cur_ver = get_current_version(conn)
    if target_version >= cur_ver:
        log.info("无需回滚")
        return False
    log.error("当前版本不支持自动回滚, 请手动处理")
    return False


def needs_migration(conn):
    """检查是否需要迁移"""
    cur_ver = get_current_version(conn)
    return cur_ver < DEFAULT_SCHEMA_VERSION


def pending_migrations(conn):
    """返回待执行的迁移"""
    cur_ver = get_current_version(conn)
    return [(sql, v) for sql, v in MIGRATIONS if v > cur_ver]


def dry_run(conn):
    """演练, 返回待执行的迁移列表"""
    return pending_migrations(conn)


def migration_summary(conn):
    return {
        "current": get_current_version(conn),
        "target": DEFAULT_SCHEMA_VERSION,
        "pending": len(pending_migrations(conn)),
        "all": len(MIGRATIONS),
    }


def create_migration(name, sql):
    """创建一个新的迁移条目, 仅追加"""
    new_ver = max(t for _, t in MIGRATIONS) + 1 if MIGRATIONS else 1
    MIGRATIONS.append((sql, new_ver))
    log.info("新增迁移 v%d: %s", new_ver, name)
    return new_ver


def validate_migrations():
    """校验迁移脚本完整性"""
    versions = sorted([v for _, v in MIGRATIONS])
    for i in range(len(versions) - 1):
        if versions[i+1] - versions[i] != 1:
            log.error("迁移版本不连续: %d -> %d", versions[i], versions[i+1])
            return False
    return True


def backup_before_migrate(db_path, backup_path):
    """迁移前备份"""
    import shutil
    if not db_path or db_path == ":memory:":
        return False
    try:
        shutil.copy2(db_path, backup_path)
        log.info("备份成功: %s -> %s", db_path, backup_path)
        return True
    except Exception as e:
        log.error("备份失败: %s", e)
        return False


def hash_sql(sql):
    return hashlib.md5(sql.encode("utf-8")).hexdigest()


def describe_migration(sql, version):
    return {
        "version": version,
        "sql": sql,
        "hash": hash_sql(sql),
    }


def all_migrations_described():
    return [describe_migration(s, v) for s, v in MIGRATIONS]


def find_migration_by_version(version):
    for sql, v in MIGRATIONS:
        if v == version:
            return sql
    return None


def migration_exists(version):
    return find_migration_by_version(version) is not None


def version_info(version):
    sql = find_migration_by_version(version)
    if sql is None:
        return None
    return {
        "version": version,
        "sql": sql,
        "type": classify_migration(sql),
    }


def classify_migration(sql):
    sql_lower = sql.lower().strip()
    if sql_lower.startswith("create table"):
        return "create_table"
    if sql_lower.startswith("alter table"):
        return "alter_table"
    if sql_lower.startswith("create index"):
        return "create_index"
    if sql_lower.startswith("drop"):
        return "drop"
    if sql_lower.startswith("insert"):
        return "insert"
    if sql_lower.startswith("update"):
        return "update"
    return "other"


def safe_execute(conn, sql, params=()):
    try:
        cur = conn.cursor()
        cur.execute(sql, params)
        conn.commit()
        return True
    except Exception as e:
        log.error("safe_execute 失败: %s", e)
        return False


def execute_many(conn, sql, params_list):
    try:
        cur = conn.cursor()
        cur.executemany(sql, params_list)
        conn.commit()
        return cur.rowcount
    except Exception as e:
        log.error("execute_many 失败: %s", e)
        return 0


def count_tables(conn):
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
    return cur.fetchone()[0]


def list_tables(conn):
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    return [row[0] for row in cur.fetchall()]


def table_info(conn, table_name):
    cur = conn.cursor()
    cur.execute(f"PRAGMA table_info({table_name})")
    return cur.fetchall()


def index_list(conn, table_name):
    cur = conn.cursor()
    cur.execute(f"PRAGMA index_list({table_name})")
    return cur.fetchall()


def vacuum_db(conn):
    try:
        conn.execute("VACUUM")
        return True
    except Exception as e:
        log.error("VACUUM 失败: %s", e)
        return False


def analyze_db(conn):
    try:
        conn.execute("ANALYZE")
        return True
    except Exception as e:
        log.error("ANALYZE 失败: %s", e)
        return False


def integrity_check(conn):
    cur = conn.cursor()
    cur.execute("PRAGMA integrity_check")
    row = cur.fetchone()
    return row[0] if row else "unknown"


def quick_check(conn):
    cur = conn.cursor()
    cur.execute("PRAGMA quick_check")
    row = cur.fetchone()
    return row[0] if row else "unknown"


def foreign_key_check(conn):
    cur = conn.cursor()
    cur.execute("PRAGMA foreign_key_check")
    return cur.fetchall()


def db_size(conn):
    cur = conn.cursor()
    cur.execute("SELECT page_count * page_size FROM pragma_page_count(), pragma_page_size()")
    row = cur.fetchone()
    return row[0] if row else 0


def table_size(conn, table_name):
    cur = conn.cursor()
    cur.execute(f"SELECT COUNT(*) FROM {table_name}")
    return cur.fetchone()[0]


def drop_table(conn, table_name):
    try:
        conn.execute(f"DROP TABLE IF EXISTS {table_name}")
        conn.commit()
        return True
    except Exception as e:
        log.error("drop_table 失败: %s", e)
        return False


def rename_table(conn, old_name, new_name):
    try:
        conn.execute(f"ALTER TABLE {old_name} RENAME TO {new_name}")
        conn.commit()
        return True
    except Exception as e:
        log.error("rename_table 失败: %s", e)
        return False


def add_column(conn, table, column, col_type, default=None):
    sql = f"ALTER TABLE {table} ADD COLUMN {column} {col_type}"
    if default is not None:
        sql += f" DEFAULT {default}"
    try:
        conn.execute(sql)
        conn.commit()
        return True
    except Exception as e:
        log.error("add_column 失败: %s", e)
        return False


def create_index_safe(conn, index_name, table, columns):
    cols_str = ", ".join(columns) if isinstance(columns, (list, tuple)) else columns
    sql = f"CREATE INDEX IF NOT EXISTS {index_name} ON {table}({cols_str})"
    try:
        conn.execute(sql)
        conn.commit()
        return True
    except Exception as e:
        log.error("create_index_safe 失败: %s", e)
        return False


def truncate_table(conn, table):
    try:
        conn.execute(f"DELETE FROM {table}")
        conn.commit()
        return True
    except Exception as e:
        log.error("truncate_table 失败: %s", e)
        return False


def check_column_exists(conn, table, column):
    cur = conn.cursor()
    cur.execute(f"PRAGMA table_info({table})")
    for row in cur.fetchall():
        if row[1] == column:
            return True
    return False


def check_table_exists(conn, table):
    cur = conn.cursor()
    cur.execute(
        "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name=?",
        (table,),
    )
    return cur.fetchone()[0] > 0


def check_index_exists(conn, index):
    cur = conn.cursor()
    cur.execute(
        "SELECT COUNT(*) FROM sqlite_master WHERE type='index' AND name=?",
        (index,),
    )
    return cur.fetchone()[0] > 0


def migration_report(conn):
    """生成迁移报告"""
    return {
        "current_version": get_current_version(conn),
        "target_version": DEFAULT_SCHEMA_VERSION,
        "tables": list_tables(conn),
        "pending": len(pending_migrations(conn)),
        "integrity": integrity_check(conn),
        "size_bytes": db_size(conn),
        "ts": time.time(),
    }