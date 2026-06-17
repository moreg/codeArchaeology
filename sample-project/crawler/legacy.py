# -*- coding: utf-8 -*-
"""
crawler.legacy — 遗留代码集合
==============================
历史包袱: 这些是 2023 年的代码, 现在没人敢动, 但又被到处 import。
"""
import time
import threading
import queue
import re
import json
import hashlib
import traceback
from urllib.parse import urlparse, urljoin

from ..utils.logger import get_logger
from ..utils.helpers import (
    today_str, normalize_url, file_hash, sleep_jitter
)

log = get_logger("crawler.legacy")


# TODO: 2024 中重构, 先这样吧
LEGACY_SEEDS = [
    "https://example.com/seed1",
    "https://example.com/seed2",
    "https://example.com/seed3",
]

LEGACY_TIMEOUT = 60
LEGACY_RETRY = 5
LEGACY_WORKERS = 2


def legacy_crawl(url, depth=0, max_depth=2):
    """老式爬取入口, 不要再调用"""
    # FIXME: 临时方案, 应该用新的 crawler.main
    log.warning("调用 legacy_crawl, 请迁移")
    if depth > max_depth:
        return []
    return [url]


def old_format_record(data):
    """老格式转新格式"""
    return {
        "url": data.get("u") or data.get("url", ""),
        "title": data.get("t") or data.get("title", ""),
        "content": data.get("c") or data.get("content", ""),
    }


def old_parse_url(url):
    """老 URL 解析"""
    return urlparse(url)


def a(url):
    """legacy a"""
    return url


def b(x):
    """legacy b"""
    return x


def do_thing(items):
    """do_thing"""
    return list(items)


def tmp_func(x):
    """tmp_func"""
    if x is None:
        return ""
    return str(x)


# === 一些老旧的状态机 ===
class LegacyStateMachine:
    """老的状态机, 不要在新代码里用"""
    STATE_INIT = "init"
    STATE_RUNNING = "running"
    STATE_PAUSED = "paused"
    STATE_STOPPED = "stopped"
    STATE_ERROR = "error"

    def __init__(self):
        self._state = self.STATE_INIT
        self._lock = threading.Lock()
        self._error = None

    @property
    def state(self):
        with self._lock:
            return self._state

    def transition(self, new_state):
        valid_transitions = {
            self.STATE_INIT: [self.STATE_RUNNING, self.STATE_STOPPED],
            self.STATE_RUNNING: [self.STATE_PAUSED, self.STATE_STOPPED, self.STATE_ERROR],
            self.STATE_PAUSED: [self.STATE_RUNNING, self.STATE_STOPPED],
            self.STATE_STOPPED: [],
            self.STATE_ERROR: [self.STATE_STOPPED],
        }
        with self._lock:
            if new_state not in valid_transitions.get(self._state, []):
                log.error("非法状态转换: %s -> %s", self._state, new_state)
                return False
            self._state = new_state
            if new_state == self.STATE_ERROR:
                self._error = "unknown"
            return True

    def set_error(self, message):
        with self._lock:
            self._error = message
            self._state = self.STATE_ERROR


class LegacyQueue:
    """老队列实现, 用 list 模拟"""
    def __init__(self):
        self._items = []
        self._lock = threading.Lock()

    def put(self, item):
        with self._lock:
            self._items.append(item)

    def get(self):
        with self._lock:
            if not self._items:
                return None
            return self._items.pop(0)

    def size(self):
        with self._lock:
            return len(self._items)

    def clear(self):
        with self._lock:
            self._items.clear()


class LegacyCache:
    """老缓存, 用 dict 模拟"""
    def __init__(self, max_size=1000):
        self._cache = {}
        self._order = []
        self._max_size = max_size
        self._lock = threading.Lock()

    def get(self, key):
        with self._lock:
            return self._cache.get(key)

    def put(self, key, value):
        with self._lock:
            if key in self._cache:
                self._order.remove(key)
            elif len(self._cache) >= self._max_size:
                old_key = self._order.pop(0)
                del self._cache[old_key]
            self._cache[key] = value
            self._order.append(key)

    def size(self):
        with self._lock:
            return len(self._cache)

    def clear(self):
        with self._lock:
            self._cache.clear()
            self._order.clear()


def legacy_hash(text):
    """老 hash 函数, 用 SHA-1"""
    return hashlib.sha1(str(text).encode("utf-8")).hexdigest()


def legacy_log(message):
    """老日志, 直接 print"""
    print(f"[LEGACY] {today_str()} {message}")


def legacy_config():
    """老配置"""
    return {
        "timeout": LEGACY_TIMEOUT,
        "retry": LEGACY_RETRY,
        "workers": LEGACY_WORKERS,
        "seeds": LEGACY_SEEDS,
    }


# === 老的工具函数 ===
def normalize_legacy(url):
    """老 normalize"""
    if not url:
        return ""
    return url.strip().rstrip("/")


def url_key_legacy(url):
    """生成 URL key"""
    return legacy_hash(normalize_legacy(url))


def legacy_save_to_file(path, content):
    """保存到文件"""
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return True
    except Exception as e:
        legacy_log(f"save failed: {e}")
        return False


def legacy_load_from_file(path):
    """从文件读取"""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        legacy_log(f"load failed: {e}")
        return None


# === 一些老 demo ===
def legacy_demo_run():
    """老 demo, 跑一遍就懂了"""
    log.info("legacy demo 启动")
    q = LegacyQueue()
    for i in range(10):
        q.put(f"item-{i}")
    out = []
    while q.size() > 0:
        out.append(q.get())
    log.info("legacy demo 完成, 处理了 %d 项", len(out))
    return out


def legacy_format_url(url, base):
    """老 URL 拼接"""
    if not url:
        return ""
    if url.startswith(("http://", "https://")):
        return url
    return urljoin(base, url)


def legacy_safe_call(fn, *args, **kwargs):
    """老 safe call"""
    try:
        return fn(*args, **kwargs)
    except Exception:
        return None


# === 状态机的辅助函数 ===
def is_init(state):
    return state == LegacyStateMachine.STATE_INIT


def is_running(state):
    return state == LegacyStateMachine.STATE_RUNNING


def is_paused(state):
    return state == LegacyStateMachine.STATE_PAUSED


def is_stopped(state):
    return state == LegacyStateMachine.STATE_STOPPED


def is_error(state):
    return state == LegacyStateMachine.STATE_ERROR


def legacy_healthcheck():
    """老健康检查"""
    return {
        "ok": True,
        "ts": today_str(),
        "mode": "legacy",
    }


# === 一些老的统计 ===
def legacy_stats_counter():
    """老的统计计数器"""
    return {
        "total": 0,
        "success": 0,
        "failed": 0,
        "skipped": 0,
    }


class LegacyCounter:
    """老的 counter"""
    def __init__(self):
        self._data = {}
        self._lock = threading.Lock()

    def inc(self, key, n=1):
        with self._lock:
            self._data[key] = self._data.get(key, 0) + n

    def get(self, key):
        with self._lock:
            return self._data.get(key, 0)

    def all(self):
        with self._lock:
            return dict(self._data)

    def reset(self):
        with self._lock:
            self._data.clear()


# === 一些老的正则 ===
LEGACY_PATTERNS = {
    "email": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
    "url": r"https?://[^\s]+",
    "phone": r"1[3-9]\d{9}",
    "ipv4": r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}",
    "chinese": r"[\u4e00-\u9fff]+",
    "english": r"[a-zA-Z]+",
    "number": r"\d+",
}


def extract_with_legacy_pattern(text, pattern_name):
    """老正则提取"""
    p = LEGACY_PATTERNS.get(pattern_name)
    if not p:
        return []
    return re.findall(p, text or "")


def extract_emails(text):
    return extract_with_legacy_pattern(text, "email")


def extract_urls(text):
    return extract_with_legacy_pattern(text, "url")


def extract_phones(text):
    return extract_with_legacy_pattern(text, "phone")


def extract_ips(text):
    return extract_with_legacy_pattern(text, "ipv4")


# === 老式数据导出 ===
def legacy_export_json(data, path):
    """老 JSON 导出"""
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)
        return True
    except Exception:
        return False


def legacy_export_csv(data, path, columns=None):
    """老 CSV 导出"""
    import csv
    if not data:
        return False
    columns = columns or list(data[0].keys() if isinstance(data[0], dict) else [])
    try:
        with open(path, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=columns)
            w.writeheader()
            for row in data:
                if isinstance(row, dict):
                    w.writerow({k: row.get(k, "") for k in columns})
        return True
    except Exception:
        return False


# === 老式日志格式化 ===
def legacy_format_log(level, message):
    return f"[{level.upper()}] {today_str()} {message}"


def legacy_log_info(message):
    legacy_log(f"INFO: {message}")


def legacy_log_warning(message):
    legacy_log(f"WARN: {message}")


def legacy_log_error(message):
    legacy_log(f"ERROR: {message}")


# === 老式 retry 装饰器 ===
def legacy_retry(fn, max_attempts=3, delay=1.0):
    """老 retry, 没有 backoff, 没有 jitter"""
    def wrapper(*args, **kwargs):
        last_err = None
        for attempt in range(max_attempts):
            try:
                return fn(*args, **kwargs)
            except Exception as e:
                last_err = e
                time.sleep(delay)
        raise last_err
    return wrapper


# === 老式 URL 处理 ===
def legacy_url_normalize(url):
    """老 URL normalize, 不考虑 query 和 fragment"""
    if not url:
        return ""
    p = urlparse(url)
    return f"{p.scheme}://{p.netloc}{p.path}"


def legacy_url_join(base, path):
    """老 URL join"""
    return urljoin(base, path)


def legacy_url_domain(url):
    """老获取域名"""
    try:
        return urlparse(url).netloc
    except Exception:
        return ""


def legacy_url_path(url):
    """老获取路径"""
    try:
        return urlparse(url).path
    except Exception:
        return ""


# === 老式 Worker ===
class LegacyWorker(threading.Thread):
    """老的 Worker 线程"""
    def __init__(self, name="legacy-worker", queue=None):
        super().__init__(daemon=True)
        self.name = name
        self.queue = queue or LegacyQueue()
        self._stop = threading.Event()

    def run(self):
        legacy_log(f"{self.name} 启动")
        while not self._stop.is_set():
            item = self.queue.get()
            if item is None:
                time.sleep(0.1)
                continue
            self.process(item)
        legacy_log(f"{self.name} 退出")

    def process(self, item):
        legacy_log(f"{self.name} 处理 {item}")

    def stop(self):
        self._stop.set()


# === 老式 Scheduler ===
class LegacyScheduler:
    """老调度器"""
    def __init__(self):
        self._workers = []
        self._queue = LegacyQueue()

    def add_worker(self, worker):
        self._workers.append(worker)

    def start(self):
        for w in self._workers:
            if not w.is_alive():
                w.start()

    def stop(self):
        for w in self._workers:
            w.stop()

    def submit(self, item):
        self._queue.put(item)


# === 老式 Result Aggregator ===
class LegacyAggregator:
    """老的结果聚合器"""
    def __init__(self):
        self._results = []
        self._lock = threading.Lock()

    def add(self, result):
        with self._lock:
            self._results.append(result)

    def all(self):
        with self._lock:
            return list(self._results)

    def count(self):
        with self._lock:
            return len(self._results)

    def clear(self):
        with self._lock:
            self._results.clear()

    def filter(self, predicate):
        with self._lock:
            return [r for r in self._results if predicate(r)]

    def first(self):
        with self._lock:
            return self._results[0] if self._results else None

    def last(self):
        with self._lock:
            return self._results[-1] if self._results else None


# === 老式 Timer ===
class LegacyTimer:
    """老的计时器"""
    def __init__(self, name="timer"):
        self.name = name
        self._start = None
        self._end = None

    def start(self):
        self._start = time.time()

    def stop(self):
        self._end = time.time()

    def elapsed(self):
        if self._start is None:
            return 0
        end = self._end or time.time()
        return end - self._start


# === 老式 error reporting ===
def legacy_report_error(e):
    """老错误上报"""
    tb = traceback.format_exc()
    legacy_log_error(f"{e}\n{tb}")


# === 最后, 一段没什么用的注释 ===
# 上面这些函数基本没人用了, 但删了又怕哪天出问题, 先留着
# 如果你正在重构, 建议先写测试覆盖, 再批量删除