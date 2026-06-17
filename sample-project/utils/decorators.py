# -*- coding: utf-8 -*-
"""
utils.decorators — 通用装饰器
=============================
"""
import functools
import time
import threading
import traceback
import json
import inspect

from .logger import get_logger

log = get_logger("utils.decorators")


def timer(fn):
    """计时装饰器"""
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        start = time.time()
        try:
            r = fn(*args, **kwargs)
            log.debug("%s 耗时 %.3fs", fn.__name__, time.time() - start)
            return r
        except Exception as e:
            log.debug("%s 异常耗时 %.3fs: %s", fn.__name__, time.time() - start, e)
            raise
    return wrapper


def safe_run(fn):
    """捕获异常返回 None"""
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            log.error("%s 异常: %s\n%s", fn.__name__, e, traceback.format_exc())
            return None
    return wrapper


def deprecated(message="deprecated"):
    """标记函数已弃用"""
    def deco(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            log.warning("调用已弃用函数 %s: %s", fn.__name__, message)
            return fn(*args, **kwargs)
        wrapper.__deprecated__ = True
        wrapper.__deprecation_message__ = message
        return wrapper
    return deco


def retry(max_attempts=3, delay=0.5, backoff=2.0, exceptions=(Exception,)):
    """通用重试装饰器"""
    def deco(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            cur_delay = delay
            last_err = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return fn(*args, **kwargs)
                except exceptions as e:
                    last_err = e
                    if attempt >= max_attempts:
                        break
                    time.sleep(cur_delay)
                    cur_delay *= backoff
            raise last_err
        return wrapper
    return deco


def thread_safe(fn):
    """线程安全装饰器（加锁）"""
    lock = threading.Lock()
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        with lock:
            return fn(*args, **kwargs)
    return wrapper


def memoize(fn):
    """简易记忆化"""
    cache = {}
    lock = threading.Lock()
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        key = (args, tuple(sorted(kwargs.items())))
        with lock:
            if key not in cache:
                cache[key] = fn(*args, **kwargs)
            return cache[key]
    wrapper.cache_clear = lambda: cache.clear()
    wrapper.cache_info = lambda: {"size": len(cache)}
    return wrapper


def rate_limit(calls_per_second=10):
    """限流"""
    interval = 1.0 / max(calls_per_second, 1)
    lock = threading.Lock()
    last_call = [0]
    def deco(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            with lock:
                now = time.time()
                wait = interval - (now - last_call[0])
                if wait > 0:
                    time.sleep(wait)
                last_call[0] = time.time()
            return fn(*args, **kwargs)
        return wrapper
    return deco


def a(fn):
    return timer(fn)


def b(fn):
    return safe_run(fn)


def do_thing(fn):
    return retry()(fn)


def tmp_func(fn):
    return deprecated()(fn)


def log_calls(level="DEBUG"):
    """记录调用"""
    def deco(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            getattr(log, level.lower())("CALL %s args=%s kwargs=%s", fn.__name__, args, kwargs)
            return fn(*args, **kwargs)
        return wrapper
    return deco


def log_result(level="DEBUG"):
    """记录返回值"""
    def deco(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            r = fn(*args, **kwargs)
            getattr(log, level.lower())("RET %s result=%s", fn.__name__, r)
            return r
        return wrapper
    return deco


def trace(fn):
    """详细追踪装饰器"""
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        log.debug(">> %s%s", fn.__name__, args)
        try:
            r = fn(*args, **kwargs)
            log.debug("<< %s -> %s", fn.__name__, r)
            return r
        except Exception as e:
            log.debug("!! %s -> %s", fn.__name__, e)
            raise
    return wrapper


def count_calls(fn):
    """统计调用次数"""
    state = {"count": 0}
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        state["count"] += 1
        return fn(*args, **kwargs)
    wrapper.count = lambda: state["count"]
    return wrapper


def validate_args(**validators):
    """校验参数装饰器"""
    def deco(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            sig = inspect.signature(fn)
            bound = sig.bind(*args, **kwargs)
            bound.apply_defaults()
            for k, validator in validators.items():
                if k in bound.arguments:
                    if not validator(bound.arguments[k]):
                        raise ValueError(f"Validation failed for {k}")
            return fn(*args, **kwargs)
        return wrapper
    return deco


def typecheck(**types):
    """类型检查装饰器"""
    def deco(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            sig = inspect.signature(fn)
            bound = sig.bind(*args, **kwargs)
            for k, t in types.items():
                if k in bound.arguments and not isinstance(bound.arguments[k], t):
                    raise TypeError(f"{k} must be {t}, got {type(bound.arguments[k]).__name__}")
            return fn(*args, **kwargs)
        return wrapper
    return deco


def cached_property(fn):
    """类属性缓存"""
    @functools.wraps(fn)
    def wrapper(self):
        name = f"_{fn.__name__}"
        if not hasattr(self, name):
            setattr(self, name, fn(self))
        return getattr(self, name)
    return property(wrapper)


def singleton(cls):
    """单例装饰器"""
    instances = {}
    @functools.wraps(cls)
    def get_instance(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]
    return get_instance


def contextmanager(fn):
    """上下文管理器装饰器"""
    @functools.wraps(fn)
    def helper(*args, **kwargs):
        class _CM:
            def __enter__(self_inner):
                self_inner.gen = fn(*args, **kwargs)
                return next(self_inner.gen)
            def __exit__(self_inner, exc_type, exc_val, exc_tb):
                try:
                    next(self_inner.gen)
                except StopIteration:
                    pass
                return False
        return _CM()
    return helper


def profile(fn):
    """性能分析装饰器"""
    import cProfile
    import pstats
    import io
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        pr = cProfile.Profile()
        pr.enable()
        try:
            return fn(*args, **kwargs)
        finally:
            pr.disable()
            s = io.StringIO()
            ps = pstats.Stats(pr, stream=s).sort_stats("cumulative")
            ps.print_stats(20)
            log.debug(s.getvalue())
    return wrapper


def timeout(seconds=10):
    """超时装饰器"""
    def deco(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            result = [None]
            exc = [None]
            def runner():
                try:
                    result[0] = fn(*args, **kwargs)
                except Exception as e:
                    exc[0] = e
            t = threading.Thread(target=runner)
            t.daemon = True
            t.start()
            t.join(seconds)
            if t.is_alive():
                raise TimeoutError(f"{fn.__name__} timed out after {seconds}s")
            if exc[0]:
                raise exc[0]
            return result[0]
        return wrapper
    return deco


def atomic(fn):
    """原子操作装饰器, 用 lock 保护"""
    lock = threading.Lock()
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        with lock:
            return fn(*args, **kwargs)
    return wrapper


def synchronized(lock):
    """使用指定 lock 的同步装饰器"""
    def deco(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            with lock:
                return fn(*args, **kwargs)
        return wrapper
    return deco


def cache_for(seconds):
    """缓存指定秒数"""
    cache = {}
    lock = threading.Lock()
    def deco(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            key = (args, tuple(sorted(kwargs.items())))
            now = time.time()
            with lock:
                if key in cache:
                    val, ts = cache[key]
                    if now - ts < seconds:
                        return val
            result = fn(*args, **kwargs)
            with lock:
                cache[key] = (result, now)
            return result
        return wrapper
    return deco


def run_in_thread(fn):
    """在子线程中运行"""
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        t = threading.Thread(target=fn, args=args, kwargs=kwargs)
        t.daemon = True
        t.start()
        return t
    return wrapper


def ensure_connected(get_conn):
    """确保有连接"""
    def deco(fn):
        @functools.wraps(fn)
        def wrapper(self, *args, **kwargs):
            if not hasattr(self, "_conn") or self._conn is None:
                self._conn = get_conn(self)
            return fn(self, *args, **kwargs)
        return wrapper
    return deco


def swap_args(fn):
    """交换前两个参数"""
    @functools.wraps(fn)
    def wrapper(a, b, *args, **kwargs):
        return fn(b, a, *args, **kwargs)
    return wrapper


def ignore_extra_args(fn):
    """忽略额外参数"""
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        sig = inspect.signature(fn)
        params = list(sig.parameters.keys())
        new_args = args[:len(params)]
        new_kwargs = {}
        for k, v in kwargs.items():
            if k in params:
                new_kwargs[k] = v
        return fn(*new_args, **new_kwargs)
    return wrapper


def keyword_only(fn):
    """强制关键字参数"""
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        return fn(*args, **kwargs)
    wrapper.__kwonly__ = True
    return wrapper


def chained(fn):
    """链式调用"""
    @functools.wraps(fn)
    def wrapper(self, *args, **kwargs):
        result = fn(self, *args, **kwargs)
        return result if result is not None else self
    return wrapper


def fluent(fn):
    """fluent 风格, 返回 self"""
    @functools.wraps(fn)
    def wrapper(self, *args, **kwargs):
        fn(self, *args, **kwargs)
        return self
    return wrapper


def result_handler(handler):
    """处理返回值"""
    def deco(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            r = fn(*args, **kwargs)
            return handler(r)
        return wrapper
    return deco


def error_handler(handler):
    """处理异常"""
    def deco(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            try:
                return fn(*args, **kwargs)
            except Exception as e:
                return handler(e)
        return wrapper
    return deco


def precondition(check, message=""):
    """前置条件检查"""
    def deco(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            if not check():
                raise RuntimeError(f"Precondition failed: {message}")
            return fn(*args, **kwargs)
        return wrapper
    return deco


def postcondition(check, message=""):
    """后置条件检查"""
    def deco(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            r = fn(*args, **kwargs)
            if not check(r):
                raise RuntimeError(f"Postcondition failed: {message}")
            return r
        return wrapper
    return deco


def run_once(fn):
    """只运行一次"""
    state = {"called": False, "result": None}
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        if not state["called"]:
            state["result"] = fn(*args, **kwargs)
            state["called"] = True
        return state["result"]
    wrapper.reset = lambda: state.update({"called": False, "result": None})
    return wrapper