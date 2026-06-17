# -*- coding: utf-8 -*-
"""
database package
================
数据库访问层, 支持 SQLite/PostgreSQL。
"""
from .models import (
    Record, Failure, Task, Author, GitCommit, GitBlame,
    ScanResult, AnalysisResult,
    CREATE_TABLES_SQL, ALL_TABLES, DEFAULT_SCHEMA_VERSION,
)
from .db_manager import (
    DBManager, DBQuery, DBBatchWriter, DBExporter,
)
from .migrations import (
    MIGRATIONS, migrate, get_current_version, set_version,
)

__version__ = "0.3.0"
__all__ = [
    "Record", "Failure", "Task", "Author", "GitCommit", "GitBlame",
    "ScanResult", "AnalysisResult",
    "DBManager", "DBQuery", "DBBatchWriter", "DBExporter",
    "MIGRATIONS", "migrate",
]