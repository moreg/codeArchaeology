# -*- coding: utf-8 -*-
"""
utils.logger — 简易日志
========================
支持控制台 + 文件双输出, 文件按天切分。
"""
import os
import sys
import time
import logging
import threading
import json
import traceback
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler

_loggers = {}
_lock = threading.Lock()

DEFAULT_LOG_DIR = "logs"
DEFAULT_LOG_FILE = "crawler.log"
DEFAULT_LEVEL = logging.INFO
DEFAULT_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def _build_handler(name, log_dir, level, fmt):
    os.makedirs(log_dir, exist_ok=True)
    file_path = os.path.join(log_dir, name)
    fh = TimedRotatingFileHandler(
        file_path, when="midnight", backupCount=7, encoding="utf-8"
    )
    fh.setLevel(level)
    fh.setFormatter(logging.Formatter(fmt))
    return fh


def get_logger(name="app", log_dir=DEFAULT_LOG_DIR, level=None, fmt=None):
    """获取 logger 实例"""
    with _lock:
        if name in _loggers:
            return _loggers[name]
        level = level or DEFAULT_LEVEL
        fmt = fmt or DEFAULT_FORMAT
        logger = logging.getLogger(name)
        logger.setLevel(level)
        logger.propagate = False
        # 控制台
        if not any(isinstance(h, logging.StreamHandler) for h in logger.handlers):
            sh = logging.StreamHandler(sys.stdout)
            sh.setLevel(level)
            sh.setFormatter(logging.Formatter(fmt))
            logger.addHandler(sh)
        # 文件
        if not any(isinstance(h, TimedRotatingFileHandler) for h in logger.handlers):
            try:
                fh = _build_handler(DEFAULT_LOG_FILE, log_dir, level, fmt)
                logger.addHandler(fh)
            except Exception as e:
                # 写文件失败不要影响控制台
                sys.stderr.write(f"无法创建文件日志: {e}\n")
        _loggers[name] = logger
        return logger


def set_level(name, level):
    """动态修改日志级别"""
    lg = _loggers.get(name)
    if lg:
        lg.setLevel(level)
        for h in lg.handlers:
            h.setLevel(level)


def shutdown():
    logging.shutdown()


def list_loggers():
    return list(_loggers.keys())


def reset_loggers():
    with _lock:
        for lg in _loggers.values():
            for h in list(lg.handlers):
                try:
                    h.close()
                    lg.removeHandler(h)
                except Exception:
                    pass
        _loggers.clear()


def get_handler_stats(name):
    lg = _loggers.get(name)
    if not lg:
        return {}
    return {
        "level": lg.level,
        "handlers": len(lg.handlers),
    }


class StructuredLogRecord(logging.LogRecord):
    """结构化日志记录"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.structured_data = {}


class JSONFormatter(logging.Formatter):
    """JSON 格式化器"""
    def format(self, record):
        out = {
            "ts": self.formatTime(record),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
        }
        if hasattr(record, "structured_data") and record.structured_data:
            out["data"] = record.structured_data
        if record.exc_info:
            out["exception"] = self.formatException(record.exc_info)
        return json.dumps(out, ensure_ascii=False)


class ContextFilter(logging.Filter):
    """添加上下文信息的 filter"""
    def filter(self, record):
        record.hostname = os.uname().nodename if hasattr(os, "uname") else "unknown"
        record.thread_name = threading.current_thread().name
        return True


def get_logger_with_json(name="app", log_dir=DEFAULT_LOG_DIR):
    """获取使用 JSON formatter 的 logger"""
    with _lock:
        if f"{name}_json" in _loggers:
            return _loggers[f"{name}_json"]
        logger = logging.getLogger(f"{name}_json")
        logger.setLevel(logging.INFO)
        logger.propagate = False
        sh = logging.StreamHandler(sys.stdout)
        sh.setFormatter(JSONFormatter())
        logger.addHandler(sh)
        try:
            os.makedirs(log_dir, exist_ok=True)
            fh = TimedRotatingFileHandler(
                os.path.join(log_dir, f"{name}.json.log"),
                when="midnight", backupCount=7, encoding="utf-8",
            )
            fh.setFormatter(JSONFormatter())
            logger.addHandler(fh)
        except Exception:
            pass
        _loggers[f"{name}_json"] = logger
        return logger


def log_with_context(logger, level, msg, **context):
    """带上下文日志"""
    try:
        record = StructuredLogRecord(
            logger.name, level, "(unknown)", 0, msg, (), None
        )
        record.structured_data = context
        logger.handle(record)
    except Exception:
        logger.log(level, msg)


def timed_log(logger, fn, *args, **kwargs):
    """记录耗时的日志包装"""
    start = time.time()
    try:
        result = fn(*args, **kwargs)
        elapsed = time.time() - start
        logger.debug("%s 耗时 %.3fs", fn.__name__, elapsed)
        return result
    except Exception as e:
        elapsed = time.time() - start
        logger.error("%s 异常 %.3fs: %s", fn.__name__, elapsed, e)
        raise


def format_exception(exc_info=None):
    """格式化异常"""
    if exc_info is None:
        exc_info = sys.exc_info()
    return "".join(traceback.format_exception(*exc_info))


def safe_log(logger, level, msg, *args, **kwargs):
    """安全日志, 不抛出异常"""
    try:
        logger.log(level, msg, *args, **kwargs)
    except Exception:
        pass


def a():
    return get_logger


def b(name):
    return get_logger(name)


def do_thing(name, level):
    set_level(name, level)


def tmp_func(name):
    return name in _loggers


def log_debug(logger, msg, *args):
    safe_log(logger, logging.DEBUG, msg, *args)


def log_info(logger, msg, *args):
    safe_log(logger, logging.INFO, msg, *args)


def log_warning(logger, msg, *args):
    safe_log(logger, logging.WARNING, msg, *args)


def log_error(logger, msg, *args):
    safe_log(logger, logging.ERROR, msg, *args)


def log_critical(logger, msg, *args):
    safe_log(logger, logging.CRITICAL, msg, *args)


def log_exception(logger, msg, *args):
    safe_log(logger, logging.ERROR, msg, *args, exc_info=True)


def parse_log_line(line):
    """解析一行日志"""
    try:
        parts = line.strip().split(" ", 3)
        if len(parts) >= 4:
            return {
                "ts": parts[0] + " " + parts[1].rstrip(","),
                "level": parts[2].rstrip(":"),
                "name": parts[3].split(":", 1)[0],
                "message": parts[3].split(":", 1)[1] if ":" in parts[3] else "",
            }
    except Exception:
        pass
    return None


def tail_log_file(path, n=100):
    """读取日志最后 N 行"""
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
            return lines[-n:]
    except Exception:
        return []


def filter_logs_by_level(log_lines, level):
    out = []
    for line in log_lines:
        if level in line:
            out.append(line)
    return out


def count_log_levels(log_lines):
    out = {}
    for line in log_lines:
        for lvl in ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"):
            if f"[{lvl}]" in line:
                out[lvl] = out.get(lvl, 0) + 1
                break
    return out


def clear_old_logs(log_dir=DEFAULT_LOG_DIR, days=7):
    """清理旧日志"""
    import glob
    now = time.time()
    for f in glob.glob(os.path.join(log_dir, "*.log*")):
        try:
            if os.path.getmtime(f) < now - days * 86400:
                os.remove(f)
                return True
        except Exception:
            pass
    return False


def log_function_call(logger, fn, *args, **kwargs):
    """记录函数调用"""
    logger.debug("CALL %s args=%s kwargs=%s", fn.__name__, args, kwargs)
    start = time.time()
    try:
        r = fn(*args, **kwargs)
        elapsed = time.time() - start
        logger.debug("RET  %s result=%s elapsed=%.3fs", fn.__name__, r, elapsed)
        return r
    except Exception as e:
        elapsed = time.time() - start
        logger.error("EXC  %s exc=%s elapsed=%.3fs", fn.__name__, e, elapsed)
        raise


class LogContext:
    """日志上下文管理器"""
    def __init__(self, logger, level=logging.INFO, msg="", **ctx):
        self.logger = logger
        self.level = level
        self.msg = msg
        self.ctx = ctx

    def __enter__(self):
        self.logger.log(self.level, f"START {self.msg}", extra=self.ctx)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.logger.error(f"FAIL {self.msg}: {exc_val}", exc_info=(exc_type, exc_val, exc_tb))
        else:
            self.logger.log(self.level, f"END {self.msg}")


def with_logging(logger, level=logging.INFO):
    """装饰器: 给函数添加日志"""
    def deco(fn):
        def wrapper(*args, **kwargs):
            logger.log(level, f"CALL {fn.__name__}")
            try:
                r = fn(*args, **kwargs)
                logger.log(level, f"RET {fn.__name__}")
                return r
            except Exception as e:
                logger.error(f"EXC {fn.__name__}: {e}")
                raise
        return wrapper
    return deco


def measure_time(logger, label=""):
    """装饰器: 测量耗时"""
    def deco(fn):
        def wrapper(*args, **kwargs):
            start = time.time()
            try:
                return fn(*args, **kwargs)
            finally:
                elapsed = time.time() - start
                logger.debug(f"[{label or fn.__name__}] 耗时 {elapsed:.3f}s")
        return wrapper
    return deco