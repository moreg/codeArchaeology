# -*- coding: utf-8 -*-
"""
crawler package
===============
爬虫核心: spider / url_manager / downloader
"""
from .spider import (
    Spider, SpiderPool, SpiderMetrics, SpiderRouter, SpiderContext,
    SpiderScheduler,
)
from .url_manager import (
    URLManager, URLFilter, URLNormalizer, URLFrontier,
    URLBloomFilter, URLStatistics,
)
from .downloader import (
    Downloader, AsyncDownloader, HTTPCache, RateLimiter, CookieJar,
)
from .main import (
    run_crawler, stop_flag, healthcheck,
    init_context, schedule_tasks, fetch_one,
)

__version__ = "0.4.0"
__all__ = [
    "Spider", "URLManager", "Downloader",
    "SpiderPool", "URLFilter", "URLNormalizer",
    "run_crawler", "stop_flag",
]