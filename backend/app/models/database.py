# -*- coding: utf-8 -*-
"""
app.models.database — SQLAlchemy 数据库初始化
==============================================
"""
import threading
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from contextlib import contextmanager
import os

from ..config import settings
from ..utils.logger import get_logger

log = get_logger("models.database")


def _ensure_sqlite_dir(url: str):
    if not url.startswith("sqlite:///"):
        return
    path = url.replace("sqlite:///", "", 1)
    if path == ":memory:":
        return
    d = os.path.dirname(os.path.abspath(path))
    if d:
        os.makedirs(d, exist_ok=True)


_ensure_sqlite_dir(settings.DATABASE_URL)

_is_sqlite = settings.DATABASE_URL.startswith("sqlite")

engine = create_engine(
    settings.DATABASE_URL,
    # SQLite 跨线程访问需要关闭 thread 检查；同时启用 WAL 提升并发
    connect_args={"check_same_thread": False, "timeout": 30} if _is_sqlite else {},
    pool_pre_ping=True,
)


if _is_sqlite:
    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, connection_record):
        """在每个新连接上开启 WAL + busy_timeout，缓解多线程写竞争"""
        try:
            cur = dbapi_connection.cursor()
            cur.execute("PRAGMA journal_mode=WAL")
            cur.execute("PRAGMA synchronous=NORMAL")
            cur.execute("PRAGMA busy_timeout=30000")
            cur.execute("PRAGMA foreign_keys=ON")
            cur.close()
        except Exception as e:
            log.warning("设置 SQLite PRAGMA 失败: %s", e)


# 跨线程访问 SQLite 时的全局写锁：SQLAlchemy Session 本身不是线程安全的
# 此锁确保任意时刻只有一个线程在写串行化 session 写操作
_write_lock = threading.Lock()


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """FastAPI 依赖注入"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def db_session():
    """上下文管理器：SQLite 下加写锁，避免 'database is locked'"""
    if _is_sqlite:
        with _write_lock:
            db = SessionLocal()
            try:
                yield db
                db.commit()
            except Exception:
                db.rollback()
                raise
            finally:
                db.close()
    else:
        db = SessionLocal()
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()


def init_db():
    """初始化所有表"""
    try:
        from . import project, file, function, call_relation
        from . import git_commit, git_blame, score, analysis_result
        Base.metadata.create_all(bind=engine)
        log.info("数据库表已创建")
        return True
    except Exception as e:
        log.error("数据库初始化失败: %s", e)
        return False