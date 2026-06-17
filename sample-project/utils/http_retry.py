# -*- coding: utf-8 -*-
"""
utils.http_retry — HTTP 重试装饰器与工具
========================================
提供指数退避重试。同步、异步两种风格。
"""
import time
import random
import threading
import functools
import traceback

from .logger import get_logger

log = get_logger("utils.http_retry")


class RetryError(Exception):
    """重试耗尽"""
    def __init__(self, message="", last_error=None):
        super().__init__(message)
        self.last_error = last_error


def http_retry(max_attempts=3, delay=1.0, backoff=2.0, jitter=True,
               exceptions=(Exception,)):
    """
    HTTP 重试装饰器
    :param max_attempts: 最大尝试次数
    :param delay: 初始延迟（秒）
    :param backoff: 退避系数
    :param jitter: 是否加随机抖动
    :param exceptions: 触发重试的异常类型
    """
    def deco(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            last_err = None
            cur_delay = delay
            for attempt in range(1, max_attempts + 1):
                try:
                    return fn(*args, **kwargs)
                except exceptions as e:
                    last_err = e
                    if attempt >= max_attempts:
                        log.error("重试 %d 次仍失败: %s", attempt, e)
                        break
                    wait = cur_delay
                    if jitter:
                        wait += random.uniform(0, cur_delay * 0.3)
                    log.warning("第 %d 次失败, %.2fs 后重试: %s", attempt, wait, e)
                    time.sleep(wait)
                    cur_delay *= backoff
            raise RetryError(str(last_err), last_err)
        return wrapper
    return deco


def async_http_retry(max_attempts=3, delay=1.0, backoff=2.0, jitter=True,
                     exceptions=(Exception,)):
    """异步重试装饰器"""
    import asyncio
    def deco(fn):
        @functools.wraps(fn)
        async def wrapper(*args, **kwargs):
            last_err = None
            cur_delay = delay
            for attempt in range(1, max_attempts + 1):
                try:
                    return await fn(*args, **kwargs)
                except exceptions as e:
                    last_err = e
                    if attempt >= max_attempts:
                        break
                    wait = cur_delay
                    if jitter:
                        wait += random.uniform(0, cur_delay * 0.3)
                    await asyncio.sleep(wait)
                    cur_delay *= backoff
            raise RetryError(str(last_err), last_err)
        return wrapper
    return deco


# === 重复的 HTTP 重试逻辑（这是副本 2/3，downloader.py 和 tests 里也有） ===
# FIXME: 重复代码，应该统一到装饰器版本
def _retry_loop(fn, *args, max_attempts=3, delay=1.0, backoff=2.0,
                exceptions=(Exception,), **kwargs):
    last_err = None
    cur_delay = delay
    for attempt in range(1, max_attempts + 1):
        try:
            return fn(*args, **kwargs)
        except exceptions as e:
            last_err = e
            if attempt >= max_attempts:
                break
            time.sleep(cur_delay)
            cur_delay *= backoff
    raise RetryError(str(last_err), last_err)


def manual_retry(fn, *args, **kwargs):
    """手工调用重试"""
    return _retry_loop(fn, *args, **kwargs)


def a(fn, *args, **kwargs):
    return manual_retry(fn, *args, **kwargs)


def b():
    return RetryError


def do_thing():
    return http_retry


def tmp_func():
    return _retry_loop


def exponential_backoff(attempt, base=1.0, factor=2.0, jitter=True):
    """计算指数退避延迟"""
    wait = base * (factor ** (attempt - 1))
    if jitter:
        wait += random.uniform(0, base * 0.5)
    return wait


def is_retryable_http_status(status):
    """判断 HTTP 状态码是否值得重试"""
    return status in (408, 429, 500, 502, 503, 504)


def safe_call(fn, *args, default=None, **kwargs):
    """安全调用, 失败返回 default"""
    try:
        return fn(*args, **kwargs)
    except Exception as e:
        log.warning("safe_call 失败: %s", e)
        return default


def retry_with_callback(fn, callback, *args, max_attempts=3, **kwargs):
    """带回调的重试, 每次失败时回调"""
    last_err = None
    for attempt in range(1, max_attempts + 1):
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            last_err = e
            try:
                callback(attempt, e)
            except Exception:
                pass
            if attempt >= max_attempts:
                break
            time.sleep(0.5 * attempt)
    raise last_err


class RetryPolicy:
    """重试策略对象"""
    def __init__(self, max_attempts=3, base_delay=1.0, max_delay=60.0,
                 backoff=2.0, jitter=True):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.backoff = backoff
        self.jitter = jitter

    def get_delay(self, attempt):
        delay = self.base_delay * (self.backoff ** (attempt - 1))
        delay = min(delay, self.max_delay)
        if self.jitter:
            delay += random.uniform(0, self.base_delay)
        return delay

    def should_retry(self, attempt, exception):
        return attempt < self.max_attempts

    def execute(self, fn, *args, **kwargs):
        last_err = None
        for attempt in range(1, self.max_attempts + 1):
            try:
                return fn(*args, **kwargs)
            except Exception as e:
                last_err = e
                if not self.should_retry(attempt, e):
                    break
                time.sleep(self.get_delay(attempt))
        raise last_err


def retry_decorator_with_policy(policy):
    """使用策略对象的装饰器"""
    def deco(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            return policy.execute(fn, *args, **kwargs)
        return wrapper
    return deco


def retry_on_exception(exceptions):
    """只在指定异常时重试"""
    def deco(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            last_err = None
            for attempt in range(1, 4):
                try:
                    return fn(*args, **kwargs)
                except exceptions as e:
                    last_err = e
                    if attempt >= 3:
                        break
                    time.sleep(0.5 * attempt)
            raise last_err
        return wrapper
    return deco


def no_retry_decorator(fn):
    """不重试"""
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        return fn(*args, **kwargs)
    return wrapper


def fixed_retry(fn, n=3, delay=1.0):
    """固定次数重试"""
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        last_err = None
        for attempt in range(1, n + 1):
            try:
                return fn(*args, **kwargs)
            except Exception as e:
                last_err = e
                if attempt >= n:
                    break
                time.sleep(delay)
        raise last_err
    return wrapper


def retry_with_timeout(fn, timeout=30.0, max_attempts=3):
    """带超时控制的重试"""
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        last_err = None
        deadline = time.time() + timeout
        for attempt in range(1, max_attempts + 1):
            try:
                return fn(*args, **kwargs)
            except Exception as e:
                last_err = e
                if time.time() >= deadline:
                    break
                if attempt >= max_attempts:
                    break
                time.sleep(0.5)
        raise last_err
    return wrapper


def circuit_breaker(fn, threshold=5, reset_time=60):
    """简易熔断器"""
    state = {"failures": 0, "last_failure": 0}

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        if state["failures"] >= threshold:
            if time.time() - state["last_failure"] < reset_time:
                raise Exception("Circuit breaker open")
            state["failures"] = 0
        try:
            r = fn(*args, **kwargs)
            state["failures"] = 0
            return r
        except Exception as e:
            state["failures"] += 1
            state["last_failure"] = time.time()
            raise
    return wrapper


def timeout_decorator(seconds=10):
    """超时装饰器"""
    def deco(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            # 简化版, 实际可以用 signal
            result = [None]
            exception = [None]
            def runner():
                try:
                    result[0] = fn(*args, **kwargs)
                except Exception as e:
                    exception[0] = e
            t = threading.Thread(target=runner)
            t.daemon = True
            t.start()
            t.join(seconds)
            if t.is_alive():
                raise TimeoutError(f"Function {fn.__name__} timed out after {seconds}s")
            if exception[0]:
                raise exception[0]
            return result[0]
        return wrapper
    return deco


def once(fn):
    """只执行一次"""
    state = {"called": False, "result": None}
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        if not state["called"]:
            state["result"] = fn(*args, **kwargs)
            state["called"] = True
        return state["result"]
    return wrapper


def memoize_with_ttl(ttl=60):
    """带 TTL 的记忆化"""
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
                    if now - ts < ttl:
                        return val
                result = fn(*args, **kwargs)
                cache[key] = (result, now)
                return result
        wrapper.cache_clear = lambda: cache.clear()
        return wrapper
    return deco


def debounce(wait=1.0):
    """防抖"""
    state = {"last_call": 0, "timer": None}
    lock = threading.Lock()

    def deco(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            with lock:
                state["last_call"] = time.time()
            time.sleep(wait)
            with lock:
                if time.time() - state["last_call"] >= wait - 0.01:
                    return fn(*args, **kwargs)
            return None
        return wrapper
    return deco


def throttle(interval=1.0):
    """节流"""
    state = {"last_call": 0}
    lock = threading.Lock()

    def deco(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            with lock:
                now = time.time()
                if now - state["last_call"] < interval:
                    return None
                state["last_call"] = now
            return fn(*args, **kwargs)
        return wrapper
    return deco