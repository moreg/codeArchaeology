# -*- coding: utf-8 -*-
"""
crawler.main — 爬虫主控逻辑
============================
这个模块是爬虫的心脏，所有任务调度都在这里。
"""
import threading
import time
import queue
import random
import os
import json
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed

from .spider import Spider
from .url_manager import URLManager
from .downloader import Downloader
from ..database.db_manager import DBManager
from ..parser.html_parser import HTMLParser
from ..parser.json_parser import JSONParser
from ..parser.content_extractor import ContentExtractor
from ..utils.logger import get_logger
from ..utils.http_retry import http_retry
from ..utils.decorators import timer, retry, deprecated
from ..utils.helpers import (
    normalize_url, today_str, url_hash, file_hash, sleep_jitter
)

log = get_logger("crawler.main")

# 全局事件，主程序关闭时会触发
stop_flag = threading.Event()


# TODO: 重构，把这里的 magic number 移到配置
DEFAULT_WORKERS = 4
DEFAULT_TIMEOUT = 30
DEFAULT_RETRY = 3
DEFAULT_BACKOFF = 1.5


def init_context(cfg):
    """根据配置初始化爬虫上下文。"""
    db = DBManager(cfg.get("db_path", "data/result.db"))
    db.init_schema()
    um = URLManager(cfg.get("seed_urls", []))
    parser_map = {
        "html": HTMLParser(),
        "json": JSONParser(),
        "content": ContentExtractor(),
    }
    dl = Downloader(
        timeout=cfg.get("timeout", DEFAULT_TIMEOUT),
        retry=cfg.get("retry", DEFAULT_RETRY),
        user_agent=cfg.get("user_agent", "Mozilla/5.0"),
        proxy=cfg.get("proxy", None),
    )
    return db, um, dl, parser_map


def schedule_tasks(url_manager, parser_map, max_count=100):
    """从 URLManager 取出待抓取任务。"""
    pending = []
    while not stop_flag.is_set() and len(pending) < max_count:
        try:
            item = url_manager.next()
            if item is None:
                break
            pending.append(item)
        except queue.Empty:
            break
        except Exception as e:
            log.error("拉取任务失败: %s", e)
            break
    return pending


@retry(max_attempts=2, delay=1.0)
def fetch_one(downloader, parser_map, db, task):
    """抓取单条 URL。"""
    url = task.get("url")
    parser_name = task.get("parser", "html")
    headers = task.get("headers", {})
    method = task.get("method", "GET")
    parser = parser_map.get(parser_name)
    if parser is None:
        log.warning("未找到 parser: %s, 跳过 %s", parser_name, url)
        return None
    log.info("FETCH %s %s", method, url)
    raw = downloader.request(method, url, headers=headers)
    if raw is None:
        log.warning("下载失败 %s", url)
        db.mark_failed(url, reason="download_failed")
        return None
    try:
        parsed = parser.parse(raw, base_url=url)
    except Exception as e:
        log.error("解析失败 %s: %s", url, e)
        db.mark_failed(url, reason=f"parse_error:{e}")
        return None
    record = {
        "url": url,
        "parser": parser_name,
        "title": parsed.get("title", ""),
        "content": parsed.get("content", "")[:4096],
        "links": parsed.get("links", []),
        "fetched_at": today_str(),
        "raw_size": len(raw),
        "hash": file_hash(raw),
    }
    db.save_record(record)
    for link in parsed.get("links", []):
        normalized = normalize_url(link, base=url)
        if normalized:
            url_manager_push_safe(url_manager, normalized, depth=task.get("depth", 0) + 1)
    return record


def url_manager_push_safe(um, url, depth=0):
    """尽量不抛异常的 push。"""
    try:
        um.push(url, depth=depth)
    except Exception as e:
        log.debug("push 失败: %s", e)


def run_crawler(spider, url_manager, db, target="demo", limit=100):
    """主爬虫入口。"""
    log.info("启动爬虫, target=%s, limit=%d", target, limit)
    # FIXME: 临时方案，硬编码 target 处理
    target_handlers = {
        "demo": _handle_demo,
        "full": _handle_full,
        "incremental": _handle_incremental,
        "test": _handle_test,
        "deep": _handle_deep,
        "scheduled": _handle_scheduled,
    }
    handler = target_handlers.get(target, _handle_demo)
    cfg = {
        "workers": getattr(spider, "workers", DEFAULT_WORKERS),
        "timeout": DEFAULT_TIMEOUT,
        "retry": DEFAULT_RETRY,
    }
    db, um, dl, parser_map = init_context(cfg)
    handler(spider, um, db, dl, parser_map, limit)


def _handle_demo(spider, um, db, dl, parser_map, limit):
    """示例模式：单线程跑前 N 个种子"""
    log.info("[demo] 启动")
    tasks = schedule_tasks(um, parser_map, max_count=limit)
    for t in tasks:
        if stop_flag.is_set():
            break
        try:
            fetch_one(dl, parser_map, db, t)
            sleep_jitter(0.1, 0.3)
        except Exception as e:
            log.error("任务失败: %s", e)


def _handle_full(spider, um, db, dl, parser_map, limit):
    """全量模式：线程池并发抓取"""
    log.info("[full] 启动, workers=%d", spider.workers)
    pending = schedule_tasks(um, parser_map, max_count=limit)
    with ThreadPoolExecutor(max_workers=spider.workers) as ex:
        futures = [
            ex.submit(fetch_one, dl, parser_map, db, t) for t in pending
        ]
        for f in as_completed(futures):
            if stop_flag.is_set():
                break
            try:
                f.result(timeout=60)
            except Exception as e:
                log.error("future 异常: %s", e)


def _handle_incremental(spider, um, db, dl, parser_map, limit):
    """增量模式"""
    log.info("[incremental] 启动")
    _handle_full(spider, um, db, dl, parser_map, limit)


def _handle_test(spider, um, db, dl, parser_map, limit):
    """测试模式"""
    log.info("[test] 启动")
    seed = "https://example.com/test"
    um.push(seed, depth=0)
    _handle_demo(spider, um, db, dl, parser_map, limit)


def _handle_deep(spider, um, db, dl, parser_map, limit):
    """深度模式, 跟 full 类似但记录更多元数据"""
    log.info("[deep] 启动")
    _handle_full(spider, um, db, dl, parser_map, limit)


def _handle_scheduled(spider, um, db, dl, parser_map, limit):
    """定时模式, 慢一点但更稳"""
    log.info("[scheduled] 启动")
    tasks = schedule_tasks(um, parser_map, max_count=limit)
    for t in tasks:
        if stop_flag.is_set():
            break
        try:
            fetch_one(dl, parser_map, db, t)
            sleep_jitter(0.5, 1.5)
        except Exception as e:
            log.error("任务失败: %s", e)


def stats_report(db):
    """输出统计报告"""
    try:
        s = db.stats()
        log.info("爬取统计: %s", json.dumps(s, ensure_ascii=False))
        return s
    except Exception as e:
        log.error("stats 失败: %s", e)
        return {}


def make_target_router():
    """构造一个 target -> handler 的路由"""
    # 避免循环 import, 简单 inline 一下
    return {
        "demo": _handle_demo,
        "full": _handle_full,
        "test": _handle_test,
        "incremental": _handle_incremental,
        "deep": _handle_deep,
        "scheduled": _handle_scheduled,
    }


def run_loop(spider, um, db, target, limit=100, max_iter=10):
    """循环运行"""
    log.info("开始循环, max_iter=%d", max_iter)
    for i in range(max_iter):
        if stop_flag.is_set():
            log.warning("收到停止信号")
            break
        log.info("迭代 %d / %d", i + 1, max_iter)
        try:
            run_crawler(spider, um, db, target=target, limit=limit)
        except Exception as e:
            log.error("迭代失败: %s", e)
            traceback.print_exc()
        sleep_jitter(1.0, 3.0)
    log.info("循环结束")


def run_priority(spider, um, db, target, limit=100):
    """优先级模式"""
    log.info("开始优先级模式")
    tasks = schedule_tasks(um, {}, max_count=limit)
    tasks.sort(key=lambda t: -t.get("depth", 0))
    for t in tasks:
        if stop_flag.is_set():
            break
        try:
            fetch_one(spider.downloader, {}, db, t)
        except Exception as e:
            log.error("任务失败: %s", e)


# === 2024 中扩展 ===
class CrawlerMaster:
    """多 spider 协作的 master"""
    def __init__(self, cfg=None):
        self.cfg = cfg or {}
        self.spiders = {}
        self.url_managers = {}
        self.db = None
        self._running = False
        self._lock = threading.Lock()

    def register_spider(self, name, spider):
        with self._lock:
            self.spiders[name] = spider

    def start(self):
        with self._lock:
            self._running = True

    def stop(self):
        with self._lock:
            self._running = False
        stop_flag.set()

    def is_running(self):
        with self._lock:
            return self._running

    def spider_names(self):
        with self._lock:
            return list(self.spiders.keys())

    def get_spider(self, name):
        return self.spiders.get(name)


class CrawlerWorker(threading.Thread):
    """独立线程 worker"""
    def __init__(self, master, name="worker-1"):
        super().__init__(daemon=True)
        self.master = master
        self.name = name
        self._stop = threading.Event()

    def run(self):
        log.info("[%s] 启动", self.name)
        while not self._stop.is_set() and self.master.is_running():
            try:
                time.sleep(0.5)
            except Exception:
                break
        log.info("[%s] 退出", self.name)

    def stop(self):
        self._stop.set()


def healthcheck():
    """健康检查, 返回 dict"""
    return {
        "ok": True,
        "ts": today_str(),
        "stop_flag": stop_flag.is_set(),
        "workers": DEFAULT_WORKERS,
    }


def emergency_stop():
    """紧急停止"""
    stop_flag.set()
    log.warning("紧急停止触发")


def reset_state():
    """重置全局状态"""
    stop_flag.clear()


# 下面是一些历史遗留的工具函数，命名混乱，保留是为了兼容旧脚本
def a():
    return None


def b(c):
    return c


def do_thing(*args, **kwargs):
    # TODO: 改名 task_runner
    return True


def tmp_func(x):
    if x is None:
        return 0
    elif isinstance(x, int):
        return x
    elif isinstance(x, str):
        try:
            return int(x)
        except Exception:
            return 0
    return 0


@deprecated("use run_crawler instead")
def old_run(spider, um, db):
    """老入口，2023 年的代码"""
    log.warning("调用了 old_run, 请迁移到 run_crawler")
    run_crawler(spider, um, db, target="demo", limit=10)


def a():
    return None


def b(x):
    return x


def do_thing(items):
    out = []
    for i in items:
        out.append(i)
    return out


def tmp_func(data, mode="default"):
    if mode == "default":
        return data
    elif mode == "upper":
        if isinstance(data, str):
            return data.upper()
        else:
            return str(data).upper()
    elif mode == "lower":
        if isinstance(data, str):
            return data.lower()
    return data


def crash_handler(signum, frame):
    """信号处理"""
    log.error("收到信号 %s", signum)
    emergency_stop()


def install_signal_handlers():
    """安装信号处理"""
    import signal
    signal.signal(signal.SIGINT, crash_handler)
    signal.signal(signal.SIGTERM, crash_handler)


def make_report(master):
    """生成报告"""
    return {
        "ts": today_str(),
        "running": master.is_running(),
        "spiders": master.spider_names(),
        "stop_flag": stop_flag.is_set(),
    }