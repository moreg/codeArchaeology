# -*- coding: utf-8 -*-
"""
utils.helpers — 杂项工具
========================
"""
import os
import re
import time
import random
import hashlib
import datetime
import socket
import json
import base64
import html
import urllib.parse
from urllib.parse import urlparse, urljoin, urlunparse, urldefrag


def today_str(fmt="%Y-%m-%d %H:%M:%S"):
    return datetime.datetime.now().strftime(fmt)


def iso_now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def timestamp_ms():
    return int(time.time() * 1000)


def normalize_url(url, base=""):
    """把 URL 转成绝对路径"""
    if not url:
        return None
    url = url.strip()
    if not url:
        return None
    # 跳过 data:, javascript:, mailto: 等
    if re.match(r"^(javascript|data|mailto|tel|about):", url, re.IGNORECASE):
        return None
    if base:
        url = urljoin(base, url)
    url, _ = urldefrag(url)
    return url


def url_hash(url):
    """仅用于 URL 去重 key，不可用作安全签名（MD5 已被攻破）"""
    if not url:
        return ""
    return hashlib.md5(url.encode("utf-8")).hexdigest()


def file_hash(content):
    """仅用于内容指纹/去重，不可用作安全签名（SHA-1 已被攻破）"""
    if isinstance(content, str):
        content = content.encode("utf-8")
    if not content:
        return ""
    return hashlib.sha1(content).hexdigest()


def md5(text):
    """仅用于去重/缓存键，不可用作安全签名"""
    if text is None:
        return ""
    return hashlib.md5(str(text).encode("utf-8")).hexdigest()


def sha1(text):
    """仅用于去重/缓存键，不可用作安全签名"""
    if text is None:
        return ""
    return hashlib.sha1(str(text).encode("utf-8")).hexdigest()


def sha256(text):
    """用于一般性指纹/缓存键（仍非密码学安全用途）"""
    if text is None:
        return ""
    return hashlib.sha256(str(text).encode("utf-8")).hexdigest()


def sleep_jitter(min_s=0.1, max_s=0.5):
    """带随机抖动的 sleep"""
    time.sleep(random.uniform(min_s, max_s))


def ensure_dir(path):
    if not path:
        return False
    try:
        os.makedirs(path, exist_ok=True)
        return True
    except Exception:
        return False


def is_probably_html(content_type):
    return content_type and "html" in content_type.lower()


def safe_int(v, default=0):
    try:
        return int(v)
    except Exception:
        return default


def safe_float(v, default=0.0):
    try:
        return float(v)
    except Exception:
        return default


def truncate(s, max_len=100, suffix="..."):
    if not s:
        return ""
    if len(s) <= max_len:
        return s
    return s[: max_len - len(suffix)] + suffix


def chunked(seq, size):
    """把序列切分"""
    return [seq[i:i + size] for i in range(0, len(seq), size)]


def flatten(seq):
    """拍平一层"""
    out = []
    for item in seq:
        if isinstance(item, (list, tuple)):
            out.extend(item)
        else:
            out.append(item)
    return out


def unique(seq, key=None):
    """去重，保持顺序"""
    seen = set()
    out = []
    for it in seq:
        k = key(it) if key else it
        if k in seen:
            continue
        seen.add(k)
        out.append(it)
    return out


def hostname():
    return socket.gethostname()


def uptime(start_ts):
    return time.time() - start_ts


def to_json(obj, indent=None):
    return json.dumps(obj, ensure_ascii=False, indent=indent, default=str)


def from_json(text, default=None):
    try:
        return json.loads(text)
    except Exception:
        return default


def a(x):
    return x


def b(x):
    return x


def do_thing(items):
    return list(items)


def tmp_func(x, default=None):
    return x if x is not None else default


def clamp(value, lo, hi):
    return max(lo, min(hi, value))


def lerp(a, b, t):
    return a + (b - a) * t


def rand_str(length=8, chars=None):
    chars = chars or "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    return "".join(random.choice(chars) for _ in range(length))


def short_hash(content, length=8):
    return md5(content)[:length]


def percent(num, denom):
    if not denom:
        return 0
    return num / denom * 100


def human_bytes(n):
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024:
            return f"{n:.1f}{unit}"
        n /= 1024
    return f"{n:.1f}PB"


def human_duration(seconds):
    if seconds < 60:
        return f"{seconds:.1f}s"
    if seconds < 3600:
        return f"{seconds/60:.1f}m"
    return f"{seconds/3600:.1f}h"


def human_number(n):
    if n < 1000:
        return str(n)
    if n < 1_000_000:
        return f"{n/1000:.1f}K"
    if n < 1_000_000_000:
        return f"{n/1_000_000:.1f}M"
    return f"{n/1_000_000_000:.1f}B"


def parse_duration(text):
    """解析 1h30m 之类的字符串"""
    if not text:
        return 0
    total = 0
    m = re.search(r"(\d+)h", text)
    if m:
        total += int(m.group(1)) * 3600
    m = re.search(r"(\d+)m", text)
    if m:
        total += int(m.group(1)) * 60
    m = re.search(r"(\d+)s", text)
    if m:
        total += int(m.group(1))
    return total


def slugify(text):
    if not text:
        return ""
    s = re.sub(r"[\s_]+", "-", text.lower())
    s = re.sub(r"[^a-z0-9\-]", "", s)
    return s.strip("-")


def camel_to_snake(name):
    s1 = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


def snake_to_camel(name):
    parts = name.split("_")
    return parts[0] + "".join(p.title() for p in parts[1:])


def get_nested(data, keys, default=None):
    """按 keys 列表取嵌套值"""
    cur = data
    for k in keys:
        if isinstance(cur, dict):
            cur = cur.get(k, default)
        elif isinstance(cur, list) and isinstance(k, int) and k < len(cur):
            cur = cur[k]
        else:
            return default
    return cur


def set_nested(data, keys, value):
    """按 keys 列表设置嵌套值"""
    cur = data
    for k in keys[:-1]:
        if k not in cur or not isinstance(cur[k], dict):
            cur[k] = {}
        cur = cur[k]
    cur[keys[-1]] = value
    return data


def is_iterable(obj):
    return hasattr(obj, "__iter__") and not isinstance(obj, (str, bytes))


def first_or_none(seq, predicate=None):
    if predicate is None:
        return next(iter(seq), None)
    for it in seq:
        if predicate(it):
            return it
    return None


def count_by(seq, key=None):
    out = {}
    for it in seq:
        k = key(it) if key else it
        out[k] = out.get(k, 0) + 1
    return out


def group_by(items, key):
    out = {}
    for it in items:
        k = key(it) if callable(key) else it.get(key)
        if k not in out:
            out[k] = []
        out[k].append(it)
    return out


def sum_by(items, key):
    total = 0
    for it in items:
        v = key(it) if callable(key) else it.get(key, 0)
        if v is not None:
            total += v
    return total


def avg_by(items, key):
    s = sum_by(items, key)
    n = len(list(items))
    return s / n if n else 0


def max_by(items, key):
    return max(items, key=key) if items else None


def min_by(items, key):
    return min(items, key=key) if items else None


def sort_by(items, key, desc=False):
    return sorted(items, key=key, reverse=desc)


def take(items, n):
    return list(items)[:n]


def skip(items, n):
    return list(items)[n:]


def head(items):
    return next(iter(items), None)


def tail(items):
    items = list(items)
    return items[-1] if items else None


def any_match(items, predicate):
    return any(predicate(it) for it in items)


def all_match(items, predicate):
    return all(predicate(it) for it in items)


def none_match(items, predicate):
    return all(not predicate(it) for it in items)


def filter_items(items, predicate):
    return [it for it in items if predicate(it)]


def reject_items(items, predicate):
    return [it for it in items if not predicate(it)]


def partition(items, predicate):
    yes = []
    no = []
    for it in items:
        if predicate(it):
            yes.append(it)
        else:
            no.append(it)
    return yes, no


def safe_get(d, *keys, default=None):
    cur = d
    for k in keys:
        if isinstance(cur, dict):
            cur = cur.get(k, default)
        else:
            return default
    return cur


def merge_dict(a, b):
    out = dict(a)
    out.update(b)
    return out


def merge_deep(a, b):
    out = dict(a)
    for k, v in b.items():
        if k in out and isinstance(out[k], dict) and isinstance(v, dict):
            out[k] = merge_deep(out[k], v)
        else:
            out[k] = v
    return out


def pick(d, keys):
    return {k: d[k] for k in keys if k in d}


def omit(d, keys):
    return {k: v for k, v in d.items() if k not in keys}


def rename_keys(d, mapping):
    return {mapping.get(k, k): v for k, v in d.items()}


def invert_dict(d):
    return {v: k for k, v in d.items()}


def keys_sorted(d):
    return sorted(d.keys())


def values_sorted(d):
    return [d[k] for k in sorted(d.keys())]


def is_empty(obj):
    if obj is None:
        return True
    if isinstance(obj, (str, list, dict, tuple, set)):
        return len(obj) == 0
    return False


def non_empty(obj):
    return not is_empty(obj)


def ensure_str(obj, default=""):
    if obj is None:
        return default
    return str(obj)


def ensure_list(obj, default=None):
    if obj is None:
        return default if default is not None else []
    if isinstance(obj, list):
        return obj
    if isinstance(obj, (tuple, set)):
        return list(obj)
    return [obj]


def ensure_dict(obj, default=None):
    if obj is None:
        return default if default is not None else {}
    if isinstance(obj, dict):
        return obj
    return {}


def encode_base64(text):
    if isinstance(text, str):
        text = text.encode("utf-8")
    return base64.b64encode(text).decode("ascii")


def decode_base64(text):
    return base64.b64decode(text).decode("utf-8", errors="ignore")


def escape_html(text):
    if text is None:
        return ""
    return html.escape(str(text))


def unescape_html(text):
    if text is None:
        return ""
    return html.unescape(str(text))


def url_quote(text):
    return urllib.parse.quote(str(text), safe="")


def url_unquote(text):
    return urllib.parse.unquote(text)


def parse_url(url):
    return urlparse(url)


def build_url(scheme, netloc, path="", params="", query="", fragment=""):
    return urlunparse((scheme, netloc, path, params, query, fragment))


def domain_of(url):
    try:
        return urlparse(url).netloc
    except Exception:
        return ""


def path_of(url):
    try:
        return urlparse(url).path
    except Exception:
        return ""


def scheme_of(url):
    try:
        return urlparse(url).scheme
    except Exception:
        return ""


def strip_query(url):
    try:
        p = urlparse(url)
        return urlunparse((p.scheme, p.netloc, p.path, "", "", ""))
    except Exception:
        return url


def replace_query(url, **kwargs):
    try:
        p = urlparse(url)
        q = dict(urllib.parse.parse_qsl(p.query))
        q.update(kwargs)
        return urlunparse((p.scheme, p.netloc, p.path, p.params, urllib.parse.urlencode(q), p.fragment))
    except Exception:
        return url


def make_path(*parts):
    return os.path.join(*parts)


def abspath(p):
    return os.path.abspath(p)


def basename(p):
    return os.path.basename(p)


def dirname(p):
    return os.path.dirname(p)


def exists(p):
    return os.path.exists(p)


def is_file(p):
    return os.path.isfile(p)


def is_dir(p):
    return os.path.isdir(p)


def file_size(p):
    try:
        return os.path.getsize(p)
    except Exception:
        return 0


def read_file(p, encoding="utf-8"):
    try:
        with open(p, "r", encoding=encoding) as f:
            return f.read()
    except Exception:
        return None


def write_file(p, content, encoding="utf-8"):
    try:
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding=encoding) as f:
            f.write(content)
        return True
    except Exception:
        return False


def append_file(p, content, encoding="utf-8"):
    try:
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "a", encoding=encoding) as f:
            f.write(content)
        return True
    except Exception:
        return False


def list_files(dir_path, pattern=None, recursive=False):
    out = []
    if not os.path.exists(dir_path):
        return out
    if recursive:
        for root, _, files in os.walk(dir_path):
            for f in files:
                if pattern is None or re.match(pattern, f):
                    out.append(os.path.join(root, f))
    else:
        for f in os.listdir(dir_path):
            p = os.path.join(dir_path, f)
            if os.path.isfile(p):
                if pattern is None or re.match(pattern, f):
                    out.append(p)
    return out


def list_dirs(dir_path, recursive=False):
    out = []
    if not os.path.exists(dir_path):
        return out
    if recursive:
        for root, dirs, _ in os.walk(dir_path):
            for d in dirs:
                out.append(os.path.join(root, d))
    else:
        for d in os.listdir(dir_path):
            p = os.path.join(dir_path, d)
            if os.path.isdir(p):
                out.append(p)
    return out


def file_ext(p):
    _, ext = os.path.splitext(p)
    return ext.lower()


def filename_no_ext(p):
    name, _ = os.path.splitext(os.path.basename(p))
    return name


def remove_file(p):
    try:
        os.remove(p)
        return True
    except Exception:
        return False


def remove_dir(p):
    import shutil
    try:
        shutil.rmtree(p)
        return True
    except Exception:
        return False


def copy_file(src, dst):
    import shutil
    try:
        shutil.copy2(src, dst)
        return True
    except Exception:
        return False


def move_file(src, dst):
    try:
        os.rename(src, dst)
        return True
    except Exception:
        import shutil
        try:
            shutil.move(src, dst)
            return True
        except Exception:
            return False


def touch(p):
    try:
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "a"):
            os.utime(p, None)
        return True
    except Exception:
        return False


def getenv(key, default=""):
    import os as _os
    return _os.environ.get(key, default)


def setenv(key, value):
    import os as _os
    _os.environ[key] = str(value)


def tempdir():
    import tempfile
    return tempfile.mkdtemp()


def tempdir_in(base):
    import tempfile
    return tempfile.mkdtemp(dir=base)