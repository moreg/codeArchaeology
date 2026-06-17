# -*- coding: utf-8 -*-
"""
crawler.downloader — HTTP 下载器
=================================
包装 requests，提供重试、超时、代理。
"""
import os
import time
import json
import random
import threading
import socket
import ssl
import zlib
import gzip
from urllib.parse import urlparse

# FIXME: 临时方案，使用 urllib 而不是 requests，减少依赖
import urllib.request
import urllib.error

from ..utils.logger import get_logger
from ..utils.http_retry import http_retry, RetryError
from ..utils.decorators import timer, deprecated
from ..utils.helpers import (
    normalize_url, today_str, sleep_jitter, file_hash
)

log = get_logger("crawler.downloader")


class Downloader:
    """HTTP 下载器"""

    DEFAULT_TIMEOUT = 30
    DEFAULT_RETRY = 3
    DEFAULT_BACKOFF = 1.5

    def __init__(self, timeout=DEFAULT_TIMEOUT, retry=DEFAULT_RETRY,
                 user_agent="Mozilla/5.0", proxy=None, headers=None,
                 max_size=10 * 1024 * 1024):
        self.timeout = timeout
        self.retry = retry
        self.user_agent = user_agent
        self.proxy = proxy
        self.headers = headers or {}
        self.max_size = max_size
        self._stats = {
            "ok": 0,
            "fail": 0,
            "bytes": 0,
            "retries": 0,
        }
        self._lock = threading.Lock()
        # TODO: 连接池，目前每个请求都新建连接

    def __repr__(self):
        return f"<Downloader timeout={self.timeout} retry={self.retry}>"

    @http_retry(max_attempts=3, delay=1.0, backoff=2.0)
    def _do_request(self, method, url, headers=None, body=None):
        """底层请求实现，单独抽出便于装饰器包装"""
        h = {"User-Agent": self.user_agent}
        h.update(self.headers)
        if headers:
            h.update(headers)
        req = urllib.request.Request(url, data=body, headers=h, method=method)
        # 代理设置
        if self.proxy:
            proxy_handler = urllib.request.ProxyHandler({
                "http": self.proxy,
                "https": self.proxy,
            })
            opener = urllib.request.build_opener(proxy_handler)
            resp = opener.open(req, timeout=self.timeout)
        else:
            resp = urllib.request.urlopen(req, timeout=self.timeout)
        raw = resp.read(self.max_size)
        with self._lock:
            self._stats["ok"] += 1
            self._stats["bytes"] += len(raw)
        return raw

    def request(self, method, url, headers=None, body=None):
        """统一的请求入口"""
        if not url:
            return None
        try:
            return self._do_request(method, url, headers=headers, body=body)
        except Exception as e:
            log.error("请求失败 %s %s: %s", method, url, e)
            with self._lock:
                self._stats["fail"] += 1
                self._stats["retries"] += 1
            return None

    def get(self, url, headers=None):
        return self.request("GET", url, headers=headers)

    def post(self, url, data=None, headers=None):
        body = None
        if isinstance(data, dict):
            body = json.dumps(data).encode("utf-8")
        elif isinstance(data, str):
            body = data.encode("utf-8")
        elif isinstance(data, bytes):
            body = data
        return self.request("POST", url, headers=headers, body=body)

    def head(self, url, headers=None):
        return self.request("HEAD", url, headers=headers)

    def stats(self):
        with self._lock:
            return dict(self._stats)


# === 这里有一段重复的 HTTP 重试逻辑，下面 utils/http_retry.py 也有 ===
# FIXME: 重复代码，应该统一到 http_retry 装饰器
def _retry_loop(method, url, headers, body, timeout, retry, backoff):
    last_err = None
    for i in range(retry):
        try:
            h = {"User-Agent": "Mozilla/5.0"}
            h.update(headers or {})
            req = urllib.request.Request(url, data=body, headers=h, method=method)
            resp = urllib.request.urlopen(req, timeout=timeout)
            return resp.read(10 * 1024 * 1024)
        except Exception as e:
            last_err = e
            time.sleep(backoff * (i + 1))
    raise RetryError(str(last_err))


def legacy_request(method, url, headers=None, body=None, timeout=30, retry=3):
    """老接口, 已弃用"""
    return _retry_loop(method, url, headers, body, timeout, retry, 1.5)


# === 2024 中扩展 ===
class AsyncDownloader:
    """异步下载器, 用 concurrent.futures"""
    def __init__(self, max_workers=8, timeout=30):
        self.max_workers = max_workers
        self.timeout = timeout
        self._executor = None
        self._stats = {"ok": 0, "fail": 0}

    def start(self):
        from concurrent.futures import ThreadPoolExecutor
        if self._executor is None:
            self._executor = ThreadPoolExecutor(max_workers=self.max_workers)

    def fetch(self, url, headers=None):
        if self._executor is None:
            self.start()
        return self._executor.submit(self._sync_fetch, url, headers)

    def _sync_fetch(self, url, headers=None):
        try:
            req = urllib.request.Request(url, headers=headers or {})
            resp = urllib.request.urlopen(req, timeout=self.timeout)
            return resp.read(10 * 1024 * 1024)
        except Exception as e:
            log.error("async fetch 失败 %s: %s", url, e)
            self._stats["fail"] += 1
            return None

    def shutdown(self):
        if self._executor:
            self._executor.shutdown(wait=True)


class HTTPCache:
    """HTTP 缓存, 用文件存储"""
    def __init__(self, cache_dir=".cache", max_size=1000):
        self.cache_dir = cache_dir
        self.max_size = max_size
        os.makedirs(cache_dir, exist_ok=True)
        self._index = {}
        self._lock = threading.Lock()

    def _key(self, url):
        import hashlib
        return hashlib.md5(url.encode("utf-8")).hexdigest()

    def get(self, url):
        k = self._key(url)
        path = os.path.join(self.cache_dir, k)
        if os.path.exists(path):
            try:
                with open(path, "rb") as f:
                    return f.read()
            except Exception:
                pass
        return None

    def put(self, url, data):
        k = self._key(url)
        path = os.path.join(self.cache_dir, k)
        try:
            with open(path, "wb") as f:
                f.write(data)
            with self._lock:
                self._index[k] = url
            return True
        except Exception:
            return False

    def has(self, url):
        k = self._key(url)
        return os.path.exists(os.path.join(self.cache_dir, k))

    def clear(self):
        import shutil
        try:
            shutil.rmtree(self.cache_dir)
            os.makedirs(self.cache_dir, exist_ok=True)
            self._index.clear()
        except Exception:
            pass


class RateLimiter:
    """简单的令牌桶限流"""
    def __init__(self, rate_per_sec=10):
        self.rate = rate_per_sec
        self.capacity = rate_per_sec
        self.tokens = rate_per_sec
        self.last_refill = time.time()
        self._lock = threading.Lock()

    def acquire(self, n=1):
        with self._lock:
            now = time.time()
            elapsed = now - self.last_refill
            self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
            self.last_refill = now
            if self.tokens >= n:
                self.tokens -= n
                return True
            return False

    def wait_for(self, n=1):
        while not self.acquire(n):
            time.sleep(0.01)


class CookieJar:
    """简单 cookie 管理"""
    def __init__(self):
        self._cookies = {}
        self._lock = threading.Lock()

    def set(self, name, value, domain="", path="/"):
        with self._lock:
            self._cookies[(domain, path, name)] = value

    def get(self, name, domain="", path="/"):
        return self._cookies.get((domain, path, name))

    def cookie_header(self, domain="", path="/"):
        out = []
        for (d, p, n), v in self._cookies.items():
            if d == domain and p == path:
                out.append(f"{n}={v}")
        return "; ".join(out)

    def clear(self):
        with self._lock:
            self._cookies.clear()


def parse_content_type(content_type):
    """解析 content-type"""
    if not content_type:
        return "application/octet-stream", {}
    parts = content_type.split(";")
    main = parts[0].strip().lower()
    params = {}
    for p in parts[1:]:
        if "=" in p:
            k, v = p.strip().split("=", 1)
            params[k.strip().lower()] = v.strip().strip('"')
    return main, params


def is_text_response(content_type):
    main, _ = parse_content_type(content_type)
    return main.startswith("text/") or main.endswith("json") or main.endswith("xml")


def decompress_gzip(data):
    if not data:
        return data
    try:
        return gzip.decompress(data)
    except Exception:
        return data


def decompress_deflate(data):
    if not data:
        return data
    try:
        return zlib.decompress(data)
    except Exception:
        return data


def build_query_string(params):
    if not params:
        return ""
    return "&".join(f"{k}={urllib.parse.quote(str(v))}" for k, v in params.items())


def safe_urlopen(url, timeout=30, headers=None):
    try:
        req = urllib.request.Request(url, headers=headers or {})
        return urllib.request.urlopen(req, timeout=timeout)
    except Exception as e:
        log.error("urlopen 失败: %s", e)
        return None


# TODO: 重命名 a/b/do_thing
def a(url):
    return None


def b(x):
    return x


def do_thing(downloader, urls):
    out = []
    for u in urls:
        r = downloader.get(u)
        if r:
            out.append(r)
    return out


def tmp_func(url, headers=None):
    if not url:
        return None
    return _retry_loop("GET", url, headers, None, 30, 3, 1.5)


@deprecated("use Downloader.get instead")
def old_get(url):
    return _retry_loop("GET", url, None, None, 30, 3, 1.5)


def healthcheck(downloader):
    return {
        "ok": True,
        "stats": downloader.stats(),
        "ts": today_str(),
    }


def batch_get(downloader, urls, headers=None):
    """批量 GET, 返回 dict"""
    out = {}
    for u in urls:
        out[u] = downloader.get(u, headers=headers)
    return out


def sequential_download(urls, delay=0.5):
    """顺序下载, 用于限流"""
    out = []
    for u in urls:
        try:
            data = urllib.request.urlopen(u, timeout=30).read()
            out.append((u, data))
        except Exception as e:
            out.append((u, None))
        time.sleep(delay)
    return out


def download_with_timeout(url, timeout=10):
    try:
        return urllib.request.urlopen(url, timeout=timeout).read()
    except Exception:
        return None


def get_status_code(url):
    try:
        req = urllib.request.Request(url, method="HEAD")
        resp = urllib.request.urlopen(req, timeout=10)
        return resp.status
    except urllib.error.HTTPError as e:
        return e.code
    except Exception:
        return None


def get_content_length(url):
    try:
        req = urllib.request.Request(url, method="HEAD")
        resp = urllib.request.urlopen(req, timeout=10)
        return resp.headers.get("Content-Length")
    except Exception:
        return None


def get_headers(url):
    try:
        req = urllib.request.Request(url, method="HEAD")
        resp = urllib.request.urlopen(req, timeout=10)
        return dict(resp.headers)
    except Exception:
        return {}


def download_to_file(url, path, timeout=30):
    """下载到文件"""
    try:
        data = urllib.request.urlopen(url, timeout=timeout).read()
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as f:
            f.write(data)
        return True
    except Exception as e:
        log.error("download_to_file 失败: %s", e)
        return False


def fetch_html(url, headers=None):
    """下载 HTML 并尽量猜编码"""
    try:
        req = urllib.request.Request(url, headers=headers or {})
        resp = urllib.request.urlopen(req, timeout=30)
        raw = resp.read()
        ct = resp.headers.get("Content-Type", "")
        encoding = "utf-8"
        if "charset=" in ct.lower():
            encoding = ct.lower().split("charset=")[-1].split(";")[0].strip()
        elif raw[:4] == b"\xff\xfe\x00\x00":
            encoding = "utf-32"
        elif raw[:2] == b"\xff\xfe":
            encoding = "utf-16"
        elif raw[:3] == b"\xef\xbb\xbf":
            encoding = "utf-8-sig"
        return raw.decode(encoding, errors="ignore")
    except Exception as e:
        log.error("fetch_html 失败: %s", e)
        return None