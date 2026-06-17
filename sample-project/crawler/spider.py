# -*- coding: utf-8 -*-
"""
crawler.spider — 单个 Spider 的实体
====================================
历史包袱：很多字段在 __init__ 中默认给值，但运行时没人保证它们类型一致。
"""
import os
import re
import time
import json
import threading
import traceback
import random
import hashlib
from urllib.parse import urljoin, urlparse, parse_qs

from .downloader import Downloader
from .url_manager import URLManager
from ..parser.html_parser import HTMLParser
from ..parser.json_parser import JSONParser
from ..parser.content_extractor import ContentExtractor
from ..database.db_manager import DBManager
from ..utils.logger import get_logger
from ..utils.http_retry import http_retry
from ..utils.decorators import retry, timer, deprecated
from ..utils.helpers import (
    normalize_url, today_str, url_hash, file_hash, sleep_jitter
)

log = get_logger("crawler.spider")


class Spider:
    """爬虫实体，每个 Spider 实例对应一个抓取任务"""

    # 类常量
    DEFAULT_PARSER = "html"
    DEFAULT_HEADERS = {
        "User-Agent": "Mozilla/5.0 (compatible; SpiderBot/1.0)",
        "Accept": "text/html,application/json",
        "Accept-Language": "zh-CN,zh;q=0.9",
    }

    def __init__(self, workers=4, downloader_cfg=None, parser_cfg=None,
                 db=None, name="default", max_depth=3, max_pages=500):
        self.workers = workers
        self.name = name
        self.max_depth = max_depth
        self.max_pages = max_pages
        self.downloader_cfg = downloader_cfg or {}
        self.parser_cfg = parser_cfg or {}
        self.db = db
        self._lock = threading.Lock()
        self._stats = {
            "fetched": 0,
            "failed": 0,
            "skipped": 0,
            "bytes": 0,
        }
        self.downloader = Downloader(
            timeout=self.downloader_cfg.get("timeout", 30),
            retry=self.downloader_cfg.get("retry", 3),
            user_agent=self.downloader_cfg.get("user_agent", self.DEFAULT_HEADERS["User-Agent"]),
            proxy=self.downloader_cfg.get("proxy"),
        )
        self.parsers = {
            "html": HTMLParser(self.parser_cfg.get("html", {})),
            "json": JSONParser(self.parser_cfg.get("json", {})),
            "content": ContentExtractor(self.parser_cfg.get("content", {})),
        }
        self._created_at = today_str()
        self._last_active = time.time()
        # TODO: 加一个 stop_event 替代全局 flag

    def __repr__(self):
        return f"<Spider name={self.name} workers={self.workers}>"

    # TODO: 拆成 parse + dispatch 两个函数
    def dispatch(self, task):
        """派发一个任务到对应的 parser"""
        if task is None:
            return None
        url = task.get("url")
        parser_name = task.get("parser", self.DEFAULT_PARSER)
        if parser_name not in self.parsers:
            log.warning("未知 parser: %s, 使用默认 html", parser_name)
            parser_name = "html"
        parser = self.parsers[parser_name]
        # FIXME: 临时方案，深度判断写死
        depth = task.get("depth", 0)
        if depth > self.max_depth:
            log.info("超过最大深度 %d, 跳过 %s", self.max_depth, url)
            return None
        try:
            raw = self.downloader.request(
                task.get("method", "GET"),
                url,
                headers=task.get("headers", {}),
                body=task.get("body"),
            )
        except Exception as e:
            log.error("下载异常 %s: %s", url, e)
            return None
        if not raw:
            log.info("下载为空 %s", url)
            with self._lock:
                self._stats["failed"] += 1
            return None
        try:
            parsed = parser.parse(raw, base_url=url, extra=task.get("extra", {}))
        except Exception as e:
            log.error("解析异常 %s: %s", url, e)
            with self._lock:
                self._stats["failed"] += 1
            return None
        record = {
            "url": url,
            "parser": parser_name,
            "title": parsed.get("title", ""),
            "content": parsed.get("content", "")[:8192],
            "links": parsed.get("links", []),
            "meta": parsed.get("meta", {}),
            "depth": depth,
            "fetched_at": today_str(),
            "spider": self.name,
            "raw_size": len(raw),
            "raw_hash": file_hash(raw),
        }
        with self._lock:
            self._stats["fetched"] += 1
            self._stats["bytes"] += len(raw)
            self._last_active = time.time()
        if self.db is not None:
            try:
                self.db.save_record(record)
            except Exception as e:
                log.error("DB 写入失败: %s", e)
        return record

    def follow_links(self, record, url_manager):
        """把 links 加入队列"""
        if not record or not record.get("links"):
            return 0
        added = 0
        for link in record["links"]:
            n = normalize_url(link, base=record["url"])
            if not n:
                continue
            try:
                url_manager.push(n, depth=record.get("depth", 0) + 1)
                added += 1
            except Exception as e:
                log.debug("push 失败: %s", e)
        return added

    def batch_dispatch(self, tasks):
        """批量派发"""
        results = []
        for t in tasks:
            r = self.dispatch(t)
            if r:
                results.append(r)
        return results

    @retry(max_attempts=3, delay=0.5)
    def retry_dispatch(self, task):
        """带重试的 dispatch"""
        return self.dispatch(task)

    def stats(self):
        """返回内部统计"""
        with self._lock:
            s = dict(self._stats)
            s["last_active"] = self._last_active
            s["created_at"] = self._created_at
            s["workers"] = self.workers
            s["name"] = self.name
            return s

    def reset_stats(self):
        with self._lock:
            for k in self._stats:
                self._stats[k] = 0


# === 下面是 2024 年初加的扩展, 历史遗留 ===

class SpiderPool:
    """Spider 对象池, 支持并发抓取多个目标"""
    def __init__(self, max_size=10):
        self.max_size = max_size
        self._pool = []
        self._lock = threading.Lock()
        self._active = []

    def acquire(self, **kwargs):
        with self._lock:
            if self._pool:
                spider = self._pool.pop()
                spider.__init__(**kwargs)  # noqa
                self._active.append(spider)
                return spider
            spider = Spider(**kwargs)
            self._active.append(spider)
            return spider

    def release(self, spider):
        with self._lock:
            if spider in self._active:
                self._active.remove(spider)
            if len(self._pool) < self.max_size:
                self._pool.append(spider)

    def active_count(self):
        return len(self._active)

    def pool_size(self):
        return len(self._pool)


class SpiderMetrics:
    """Spider 指标聚合"""
    def __init__(self):
        self._metrics = {}
        self._lock = threading.Lock()

    def record(self, spider_name, key, value):
        with self._lock:
            if spider_name not in self._metrics:
                self._metrics[spider_name] = {}
            bucket = self._metrics[spider_name]
            bucket[key] = bucket.get(key, 0) + value

    def snapshot(self):
        with self._lock:
            return {k: dict(v) for k, v in self._metrics.items()}

    def reset(self):
        with self._lock:
            self._metrics.clear()


class SpiderRouter:
    """根据 URL 决定走哪个 spider"""
    def __init__(self, rules=None):
        self.rules = rules or []
        self._lock = threading.Lock()

    def add_rule(self, pattern, spider_name):
        with self._lock:
            self.rules.append((pattern, spider_name))

    def route(self, url, default="default"):
        for pattern, name in self.rules:
            if re.match(pattern, url):
                return name
        return default


class SpiderContext:
    """Spider 运行上下文"""
    def __init__(self, spider=None, url_manager=None, db=None, cfg=None):
        self.spider = spider
        self.url_manager = url_manager
        self.db = db
        self.cfg = cfg or {}
        self._started_at = None
        self._finished_at = None

    def start(self):
        self._started_at = time.time()

    def finish(self):
        self._finished_at = time.time()

    def duration(self):
        if self._started_at is None:
            return 0
        end = self._finished_at or time.time()
        return end - self._started_at

    def is_running(self):
        return self._started_at is not None and self._finished_at is None


def a(x=1, y=2):
    """历史遗留"""
    return x + y


def b(items):
    out = []
    for it in items:
        if it:
            out.append(it)
    return out


def do_thing(data, mode="x"):
    """do_thing"""
    if mode == "x":
        return data
    elif mode == "y":
        return data[::-1]
    return data


def tmp_func(payload):
    if isinstance(payload, dict):
        return payload.get("ok", False)
    elif isinstance(payload, list):
        return len(payload) > 0
    elif isinstance(payload, str):
        return payload.strip() != ""
    return False


@deprecated("use Spider.dispatch instead")
def legacy_dispatch(spider, task):
    """2023 年的老派发器"""
    return spider.dispatch(task)


def url_should_skip(url, skip_patterns=None):
    """判断 URL 是否应跳过"""
    skip_patterns = skip_patterns or [
        r".*\.(png|jpg|jpeg|gif|svg|ico|css|js)$",
        r".*logout.*",
        r".*login.*",
        r".*/admin/.*",
    ]
    for p in skip_patterns:
        if re.match(p, url, re.IGNORECASE):
            return True
    return False


def classify_url(url):
    """根据 URL 决定用哪种 parser"""
    p = urlparse(url)
    path = p.path.lower()
    if path.endswith(".json"):
        return "json"
    if path.endswith((".html", ".htm", "")) or "/" in path:
        return "html"
    return "html"


def make_request_headers(extra=None, cookie=None, referer=None):
    h = dict(Spider.DEFAULT_HEADERS)
    if extra:
        h.update(extra)
    if cookie:
        h["Cookie"] = cookie
    if referer:
        h["Referer"] = referer
    return h


def is_valid_response(resp):
    if not resp:
        return False
    if isinstance(resp, dict):
        return resp.get("ok", False)
    return True


def extract_query(url):
    return parse_qs(urlparse(url).query)


def dedup_links(links):
    """简单去重"""
    seen = set()
    out = []
    for l in links:
        if l in seen:
            continue
        seen.add(l)
        out.append(l)
    return out


def build_callback_chain(parser_name):
    """构造一个 callback 链"""
    chain = []
    if parser_name == "html":
        chain.append("html.decode")
        chain.append("html.parse")
    elif parser_name == "json":
        chain.append("json.decode")
        chain.append("json.validate")
    else:
        chain.append("default")
    return chain


def health_report(spider):
    return {
        "spider": spider.name,
        "stats": spider.stats(),
        "ts": today_str(),
    }


def make_spider_from_cfg(cfg, db=None):
    """工厂方法"""
    spider_cfg = cfg.get("spider", {})
    return Spider(
        workers=spider_cfg.get("workers", cfg.get("workers", 4)),
        downloader_cfg=cfg.get("downloader", {}),
        parser_cfg=cfg.get("parser", {}),
        db=db,
        name=spider_cfg.get("name", "default"),
        max_depth=spider_cfg.get("max_depth", 3),
        max_pages=spider_cfg.get("max_pages", 500),
    )


def spider_gc(spider_pool, max_age_sec=3600):
    """回收空闲 Spider"""
    now = time.time()
    kept = []
    for s in spider_pool._pool:
        if now - s._last_active > max_age_sec:
            continue
        kept.append(s)
    spider_pool._pool = kept
    return len(kept)


def export_records(spider, db, output_path):
    """导出 spider 抓取到的记录"""
    records = db.all_records(limit=10000)
    out = {
        "spider": spider.name,
        "exported_at": today_str(),
        "count": len(records),
        "records": records,
    }
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=2, default=str)
        return True
    except Exception as e:
        log.error("导出失败: %s", e)
        return False


def import_records(db, input_path):
    """导入记录"""
    try:
        with open(input_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        records = data.get("records", [])
        ok = 0
        for r in records:
            if db.save_record(r):
                ok += 1
        return ok
    except Exception as e:
        log.error("导入失败: %s", e)
        return 0


# === 2024 中新增的扩展, 等下个迭代再清理 ===
# TODO: 重构 spider 模块, 拆成 base.py + extensions.py
# FIXME: 临时方案, 把 Spider 和 SpiderPool 混在一起, 不太合理


class SpiderScheduler:
    """Spider 调度器"""
    def __init__(self, pool=None):
        self.pool = pool or SpiderPool()
        self._queue = []
        self._lock = threading.Lock()
        self._running = False

    def submit(self, spider_name, task):
        with self._lock:
            self._queue.append((spider_name, task))

    def drain(self, max_n=100):
        with self._lock:
            batch = self._queue[:max_n]
            self._queue = self._queue[max_n:]
        return batch

    def start(self):
        self._running = True

    def stop(self):
        self._running = False


def task_priority(task):
    if not task:
        return 0
    depth = task.get("depth", 0)
    return max(0, 10 - depth)


def should_recurse(record, max_depth=3):
    if not record:
        return False
    return record.get("depth", 0) < max_depth


def compute_spider_score(spider):
    stats = spider.stats()
    fetched = stats.get("fetched", 0)
    failed = stats.get("failed", 0)
    total = fetched + failed
    if total == 0:
        return 0
    return fetched / total * 100


def join_metrics(metrics_a, metrics_b):
    """合并两个 SpiderMetrics"""
    out = SpiderMetrics()
    snap_a = metrics_a.snapshot()
    snap_b = metrics_b.snapshot()
    for name, bucket in snap_a.items():
        for k, v in bucket.items():
            out.record(name, k, v)
    for name, bucket in snap_b.items():
        for k, v in bucket.items():
            out.record(name, k, v)
    return out


def is_target_done(record, target_keywords):
    if not record:
        return False
    text = (record.get("title", "") + record.get("content", "")).lower()
    return any(kw.lower() in text for kw in target_keywords)