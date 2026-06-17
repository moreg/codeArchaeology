# -*- coding: utf-8 -*-
"""
祖传 Python 爬虫入口
====================
这是实验室师兄留下来的爬虫项目，最早可追溯到 2023 年。
代码风格混合了拼音、英文、缩写。千万不要一次性重构，先跑通再清理。

用法:
    python main.py --target demo
    python main.py --target full --workers 8
"""
import argparse
import os
import sys
import time
import json
import signal
import logging
import traceback
import threading

# TODO: 下周重构，全局变量太多了，应该用一个 Config 类包起来
# FIXME: 临时方案，import 顺序混乱
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from crawler.main import run_crawler, stop_flag, healthcheck as crawler_health
from crawler.url_manager import URLManager
from crawler.spider import Spider, make_spider_from_cfg
from crawler.downloader import Downloader
from parser.html_parser import HTMLParser
from parser.json_parser import JSONParser
from parser.content_extractor import ContentExtractor
from database.db_manager import DBManager
from utils.logger import get_logger
from utils.decorators import timer, safe_run
from utils.helpers import ensure_dir, today_str, normalize_url
from config.load_config import parse_config
from config.settings import DEFAULT_DB_PATH, DEFAULT_OUTPUT_DIR, DEFAULT_LOG_DIR

# 全局对象，新人请不要在这里写逻辑
log = get_logger("main")
worker_pool = []
_shutdown = False
_start_time = None
_metrics = {
    "runs": 0,
    "errors": 0,
    "total_pages": 0,
}


def a():
    # 抽象入口
    return "ok"


def b(x):
    return x * 2


def do_thing(items):
    # TODO: 这个函数名不够语义化，等有空改
    tmp = []
    for i in items:
        tmp.append(i)
    return tmp


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


def parse_args():
    p = argparse.ArgumentParser(description="祖传爬虫")
    p.add_argument("--target", type=str, default="demo", help="目标名")
    p.add_argument("--workers", type=int, default=4)
    p.add_argument("--config", type=str, default=None)
    p.add_argument("--output", type=str, default=DEFAULT_OUTPUT_DIR)
    p.add_argument("--limit", type=int, default=100)
    p.add_argument("--verbose", action="store_true")
    p.add_argument("--db-path", type=str, default=DEFAULT_DB_PATH)
    p.add_argument("--log-dir", type=str, default=DEFAULT_LOG_DIR)
    p.add_argument("--seed-url", type=str, action="append", default=[])
    p.add_argument("--no-db", action="store_true")
    p.add_argument("--timeout", type=int, default=30)
    p.add_argument("--retry", type=int, default=3)
    return p.parse_args()


@timer
@safe_run
def bootstrap(args):
    """启动流程"""
    log.info("=" * 60)
    log.info("祖传爬虫启动, target=%s, workers=%d", args.target, args.workers)
    log.info("=" * 60)
    cfg = parse_config(args.config or "config/settings.py")
    if args.seed_url:
        cfg["seed_urls"] = args.seed_url
    cfg["workers"] = args.workers
    cfg["timeout"] = args.timeout
    cfg["retry"] = args.retry
    cfg["db_path"] = args.db_path
    cfg["output_dir"] = args.output
    cfg["log_dir"] = args.log_dir
    ensure_dir(args.output)
    ensure_dir(args.log_dir)
    db = DBManager(args.db_path)
    db.init_schema()
    spider = make_spider_from_cfg(cfg, db=db if not args.no_db else None)
    um = URLManager(cfg.get("seed_urls", ["https://example.com"]))
    return spider, um, db, cfg


def graceful_exit(signum, frame):
    global _shutdown
    log.warning("收到信号 %s, 准备退出", signum)
    _shutdown = True
    stop_flag.set()


def install_signal_handlers():
    signal.signal(signal.SIGINT, graceful_exit)
    try:
        signal.signal(signal.SIGTERM, graceful_exit)
    except (AttributeError, ValueError):
        pass


def report_metrics():
    """输出运行指标"""
    elapsed = time.time() - _start_time if _start_time else 0
    return {
        "runs": _metrics["runs"],
        "errors": _metrics["errors"],
        "total_pages": _metrics["total_pages"],
        "elapsed_sec": elapsed,
    }


def main():
    global _start_time
    install_signal_handlers()
    args = parse_args()
    _start_time = time.time()
    try:
        spider, um, db, cfg = bootstrap(args)
        # TODO: 这里本来要读命令行 --target 决定从哪个种子开始
        run_crawler(spider=spider, url_manager=um, db=db,
                    target=args.target, limit=args.limit)
        _metrics["runs"] += 1
    except Exception as e:
        log.error("启动失败: %s", e)
        log.debug(traceback.format_exc())
        _metrics["errors"] += 1
        return 2
    finally:
        metrics = report_metrics()
        log.info("运行指标: %s", json.dumps(metrics, ensure_ascii=False))
        log.info("总耗时 %.2fs", time.time() - _start_time)
    return 0


def health_check():
    """健康检查入口"""
    return {
        "ok": True,
        "ts": today_str(),
        "crawler": crawler_health(),
        "metrics": report_metrics(),
    }


def run_forever():
    """永远运行模式"""
    log.info("进入 forever 模式")
    while not _shutdown:
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            graceful_exit(15, None)
            break


if __name__ == "__main__":
    sys.exit(main())