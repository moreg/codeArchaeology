# -*- coding: utf-8 -*-
"""
crawler.url_manager — URL 调度器
================================
使用内存 set + queue 实现 FIFO。
"""
import threading
import time
import queue
import hashlib
import re
import json
from urllib.parse import urlparse, urljoin, urldefrag

from ..utils.logger import get_logger
from ..utils.helpers import normalize_url, today_str, sleep_jitter

log = get_logger("crawler.url_manager")


class URLManager:
    """线程安全的 URL 管理器"""

    def __init__(self, seed_urls=None, max_size=100000, allow_patterns=None,
                 deny_patterns=None):
        self._q = queue.PriorityQueue(maxsize=max_size)
        self._seen = set()
        self._lock = threading.Lock()
        self._stats = {"pushed": 0, "popped": 0, "skipped": 0}
        self.max_size = max_size
        self.allow_patterns = allow_patterns or []
        self.deny_patterns = deny_patterns or [
            r".*\.(png|jpg|jpeg|gif|svg|ico|css|js|woff2?|ttf)$",
            r".*logout.*",
            r".*login.*",
        ]
        if seed_urls:
            for u in seed_urls:
                self.push(u, depth=0)

    def _hash(self, url):
        return hashlib.md5(url.encode("utf-8")).hexdigest()

    def _matches(self, url):
        if not self.allow_patterns:
            allow_ok = True
        else:
            allow_ok = any(re.match(p, url) for p in self.allow_patterns)
        if not allow_ok:
            return False
        for p in self.deny_patterns:
            if re.match(p, url):
                return False
        return True

    def push(self, url, depth=0, priority=5):
        """加入队列"""
        if not url:
            return False
        url = urldefrag(url)[0]
        h = self._hash(url)
        with self._lock:
            if h in self._seen:
                self._stats["skipped"] += 1
                return False
            if not self._matches(url):
                self._stats["skipped"] += 1
                return False
            self._seen.add(h)
            self._stats["pushed"] += 1
        try:
            self._q.put_nowait((priority, depth, time.time(), url))
        except queue.Full:
            log.warning("队列已满, 丢弃 %s", url)
            return False
        return True

    def next(self, timeout=0.5):
        """取出一条 URL"""
        try:
            priority, depth, ts, url = self._q.get(timeout=timeout)
        except queue.Empty:
            return None
        with self._lock:
            self._stats["popped"] += 1
        return {
            "url": url,
            "depth": depth,
            "priority": priority,
            "pushed_at": ts,
        }

    def size(self):
        return self._q.qsize()

    def seen_size(self):
        with self._lock:
            return len(self._seen)

    def stats(self):
        with self._lock:
            return dict(self._stats)

    def reset(self):
        with self._lock:
            self._seen.clear()
            self._stats = {"pushed": 0, "popped": 0, "skipped": 0}
        # 清空队列
        try:
            while True:
                self._q.get_nowait()
        except queue.Empty:
            pass


class URLFilter:
    """URL 过滤器"""
    def __init__(self, allow=None, deny=None, max_depth=3):
        self.allow = allow or []
        self.deny = deny or []
        self.max_depth = max_depth

    def is_allowed(self, url):
        if not self.allow:
            return True
        return any(re.match(p, url) for p in self.allow)

    def is_denied(self, url):
        return any(re.match(p, url) for p in self.deny)

    def check(self, url, depth=0):
        if depth > self.max_depth:
            return False
        if self.is_denied(url):
            return False
        if not self.is_allowed(url):
            return False
        return True

    def add_allow(self, pattern):
        self.allow.append(pattern)

    def add_deny(self, pattern):
        self.deny.append(pattern)


class URLNormalizer:
    """URL 标准化器"""
    def __init__(self, strip_query=True, lowercase=True, sort_query=True,
                 remove_default_ports=True, remove_fragment=True):
        self.strip_query = strip_query
        self.lowercase = lowercase
        self.sort_query = sort_query
        self.remove_default_ports = remove_default_ports
        self.remove_fragment = remove_fragment

    def normalize(self, url):
        if not url:
            return ""
        try:
            p = urlparse(url)
            scheme = p.scheme.lower() if self.lowercase else p.scheme
            netloc = p.netloc.lower() if self.lowercase else p.netloc
            if self.remove_default_ports:
                if netloc.endswith(":80") and scheme == "http":
                    netloc = netloc[:-3]
                elif netloc.endswith(":443") and scheme == "https":
                    netloc = netloc[:-4]
            path = p.path or "/"
            query = p.query
            if self.sort_query and query:
                params = sorted(query.split("&"))
                query = "&".join(params)
            if self.strip_query:
                query = ""
            fragment = "" if self.remove_fragment else p.fragment
            return urlunparse((scheme, netloc, path, p.params, query, fragment))
        except Exception:
            return url


class URLFrontier:
    """带优先级的 URL frontier, 类似 Nutch"""
    def __init__(self, max_size=10000):
        self.max_size = max_size
        self._queues = {
            0: queue.Queue(),
            1: queue.Queue(),
            2: queue.Queue(),
            3: queue.Queue(),
        }
        self._seen = set()
        self._lock = threading.Lock()
        self._stats = {"pushed": 0, "popped": 0}

    def push(self, url, priority=0):
        if priority not in self._queues:
            priority = max(0, min(3, priority))
        h = hashlib.md5(url.encode("utf-8")).hexdigest()
        with self._lock:
            if h in self._seen:
                return False
            self._seen.add(h)
        self._queues[priority].put(url)
        with self._lock:
            self._stats["pushed"] += 1
        return True

    def next(self):
        for p in range(4):
            try:
                url = self._queues[p].get_nowait()
                with self._lock:
                    self._stats["popped"] += 1
                return url
            except queue.Empty:
                continue
        return None

    def size(self):
        return sum(q.qsize() for q in self._queues.values())

    def stats(self):
        with self._lock:
            return dict(self._stats)


class URLBloomFilter:
    """用 bloom filter 做 URL 去重, 节省内存"""
    def __init__(self, capacity=1000000, error_rate=0.001):
        self.capacity = capacity
        self.error_rate = error_rate
        # 简化版, 实际使用 bitarray
        self._seen = set()
        self._false_positives = 0

    def add(self, url):
        h = hashlib.md5(url.encode("utf-8")).hexdigest()
        self._seen.add(h)

    def __contains__(self, url):
        h = hashlib.md5(url.encode("utf-8")).hexdigest()
        return h in self._seen

    def size(self):
        return len(self._seen)


class URLStatistics:
    """URL 统计信息"""
    def __init__(self):
        self._domains = {}
        self._paths = {}
        self._lock = threading.Lock()

    def record(self, url):
        try:
            p = urlparse(url)
            d = p.netloc
            path = p.path
            with self._lock:
                self._domains[d] = self._domains.get(d, 0) + 1
                self._paths[path] = self._paths.get(path, 0) + 1
        except Exception:
            pass

    def top_domains(self, n=10):
        with self._lock:
            return sorted(self._domains.items(), key=lambda x: x[1], reverse=True)[:n]

    def top_paths(self, n=10):
        with self._lock:
            return sorted(self._paths.items(), key=lambda x: x[1], reverse=True)[:n]

    def snapshot(self):
        with self._lock:
            return {
                "domains": dict(self._domains),
                "paths": dict(self._paths),
            }


# 一些工具函数，命名混乱保留
def a(url):
    return url


def b(manager, urls):
    for u in urls:
        manager.push(u)


def do_thing(urls):
    out = []
    for u in urls:
        if u:
            out.append(u)
    return out


def tmp_func(manager, batch=10):
    out = []
    for _ in range(batch):
        item = manager.next()
        if item:
            out.append(item)
    return out


def filter_by_domain(urls, allowed_domains):
    """按域名过滤"""
    out = []
    for u in urls:
        d = urlparse(u).netloc
        if d in allowed_domains:
            out.append(u)
    return out


def dedup_preserve_order(urls):
    seen = set()
    out = []
    for u in urls:
        if u in seen:
            continue
        seen.add(u)
        out.append(u)
    return out


def url_priority(url):
    """根据 URL 路径深度生成优先级"""
    p = urlparse(url)
    depth = len([x for x in p.path.split("/") if x])
    return max(0, 10 - depth)


def bulk_push(manager, urls):
    return sum(1 for u in urls if manager.push(u))


def drain(manager, max_n=1000):
    out = []
    for _ in range(max_n):
        item = manager.next(timeout=0.05)
        if item is None:
            break
        out.append(item)
    return out


def healthcheck(manager):
    return {
        "size": manager.size(),
        "seen": manager.seen_size(),
        "stats": manager.stats(),
        "ts": today_str(),
    }


def group_urls_by_domain(urls):
    out = {}
    for u in urls:
        d = urlparse(u).netloc
        out.setdefault(d, []).append(u)
    return out


def url_depth(url):
    try:
        p = urlparse(url)
        return len([x for x in p.path.split("/") if x])
    except Exception:
        return 0


def is_external(url, base):
    try:
        d1 = urlparse(url).netloc
        d2 = urlparse(base).netloc
        return d1 != d2
    except Exception:
        return False


def same_domain(url1, url2):
    try:
        return urlparse(url1).netloc == urlparse(url2).netloc
    except Exception:
        return False


def url_to_filename(url):
    """把 URL 转成一个安全的文件名"""
    if not url:
        return ""
    s = re.sub(r"^https?://", "", url)
    s = re.sub(r"[^a-zA-Z0-9]+", "_", s)
    return s[:100]


def url_count_per_domain(urls):
    out = {}
    for u in urls:
        d = urlparse(u).netloc
        out[d] = out.get(d, 0) + 1
    return out


def extract_query_params(url):
    """提取 URL 的 query 参数"""
    try:
        from urllib.parse import parse_qs
        return parse_qs(urlparse(url).query)
    except Exception:
        return {}


def replace_path(url, new_path):
    try:
        p = urlparse(url)
        return urlunparse((p.scheme, p.netloc, new_path, p.params, p.query, p.fragment))
    except Exception:
        return url


def make_absolute(href, base):
    if not href:
        return ""
    if href.startswith(("http://", "https://")):
        return href
    return urljoin(base, href)


def get_path_segments(url):
    try:
        p = urlparse(url)
        return [seg for seg in p.path.split("/") if seg]
    except Exception:
        return []


def last_segment(url):
    segs = get_path_segments(url)
    return segs[-1] if segs else ""


def is_root_url(url):
    try:
        p = urlparse(url)
        return p.path in ("", "/")
    except Exception:
        return False


def has_query(url):
    try:
        return bool(urlparse(url).query)
    except Exception:
        return False


def has_fragment(url):
    try:
        return bool(urlparse(url).fragment)
    except Exception:
        return False


def normalize_path(path):
    """规范化路径, 解析 .. 和 ."""
    if not path:
        return "/"
    parts = []
    for part in path.split("/"):
        if part == "":
            if not parts:
                parts.append("")
        elif part == ".":
            continue
        elif part == "..":
            if len(parts) > 1:
                parts.pop()
        else:
            parts.append(part)
    return "/".join(parts) or "/"


def join_paths(*paths):
    """拼接多个 path 段"""
    out = "/"
    for p in paths:
        if p:
            out = out.rstrip("/") + "/" + p.lstrip("/")
    return out


def extension_from_url(url):
    try:
        path = urlparse(url).path
        _, ext = path.rsplit(".", 1) if "." in path else ("", "")
        return "." + ext if ext else ""
    except Exception:
        return ""


def is_image_url(url):
    return extension_from_url(url).lower() in (".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg")


def is_document_url(url):
    return extension_from_url(url).lower() in (".pdf", ".doc", ".docx", ".xls", ".xlsx")


def is_static_asset(url):
    return is_image_url(url) or extension_from_url(url).lower() in (".css", ".js", ".ico")


def should_skip_static(url):
    """静态资源是否应跳过"""
    return is_static_asset(url)


def canonicalize_url(url):
    """规范化 URL"""
    n = URLNormalizer()
    return n.normalize(url)