# -*- coding: utf-8 -*-
"""
utils.extras — 杂项扩充
========================
"""
import re
import os
import json
import time
import threading
import hashlib
import datetime
import urllib.parse

from .logger import get_logger

log = get_logger("utils.extras")


def a(x):
    return x


def b(x):
    return x * 2


def do_thing(items):
    out = []
    for i in items:
        if i:
            out.append(i)
    return out


def tmp_func(x, mode="default"):
    if mode == "default":
        return x
    if mode == "upper":
        return str(x).upper()
    if mode == "lower":
        return str(x).lower()
    return x


# === 一些老的字符串处理 ===
def trim(s, chars=" \t\n\r"):
    if not s:
        return ""
    return s.strip(chars)


def ltrim(s, chars=" \t\n\r"):
    if not s:
        return ""
    return s.lstrip(chars)


def rtrim(s, chars=" \t\n\r"):
    if not s:
        return ""
    return s.rstrip(chars)


def starts_with(s, prefix):
    if not s:
        return False
    return s.startswith(prefix)


def ends_with(s, suffix):
    if not s:
        return False
    return s.endswith(suffix)


def contains(s, sub):
    if not s:
        return False
    return sub in s


def split_lines(s):
    if not s:
        return []
    return s.splitlines()


def split_words(s):
    if not s:
        return []
    return s.split()


def join_lines(lines):
    return "\n".join(lines)


def join_words(words, sep=" "):
    return sep.join(words)


def replace_all(s, old, new):
    if not s:
        return ""
    return s.replace(old, new)


def remove_substring(s, sub):
    return replace_all(s, sub, "")


def count_substring(s, sub):
    if not s:
        return 0
    return s.count(sub)


def pad_left(s, width, fill=" "):
    if not s:
        s = ""
    return s.rjust(width, fill)


def pad_right(s, width, fill=" "):
    if not s:
        s = ""
    return s.ljust(width, fill)


def pad_center(s, width, fill=" "):
    if not s:
        s = ""
    return s.center(width, fill)


def truncate_string(s, n, suffix="..."):
    if not s:
        return ""
    if len(s) <= n:
        return s
    return s[:n - len(suffix)] + suffix


def is_blank(s):
    return not s or not s.strip()


def is_empty(s):
    return s is None or s == ""


def is_not_empty(s):
    return not is_empty(s)


# === 数字相关 ===
def to_int(s, default=0):
    try:
        return int(s)
    except Exception:
        return default


def to_float(s, default=0.0):
    try:
        return float(s)
    except Exception:
        return default


def is_int(s):
    if s is None:
        return False
    try:
        int(s)
        return True
    except Exception:
        return False


def is_float(s):
    if s is None:
        return False
    try:
        float(s)
        return True
    except Exception:
        return False


def is_number(s):
    return is_int(s) or is_float(s)


def clamp_value(v, lo, hi):
    return max(lo, min(hi, v))


def in_range(v, lo, hi):
    return lo <= v <= hi


def round_to(v, decimals=2):
    return round(v, decimals)


# === 时间相关 ===
def now_ts():
    return time.time()


def now_ms():
    return int(time.time() * 1000)


def format_ts(ts, fmt="%Y-%m-%d %H:%M:%S"):
    return datetime.datetime.fromtimestamp(ts).strftime(fmt)


def parse_ts(s, fmt="%Y-%m-%d %H:%M:%S"):
    try:
        return datetime.datetime.strptime(s, fmt).timestamp()
    except Exception:
        return 0


def elapsed_str(seconds):
    """格式化为可读字符串"""
    if seconds < 1:
        return f"{int(seconds * 1000)}ms"
    if seconds < 60:
        return f"{seconds:.1f}s"
    if seconds < 3600:
        return f"{int(seconds / 60)}m{int(seconds % 60)}s"
    if seconds < 86400:
        return f"{int(seconds / 3600)}h{int((seconds % 3600) / 60)}m"
    return f"{int(seconds / 86400)}d{int((seconds % 86400) / 3600)}h"


def sleep_ms(ms):
    time.sleep(ms / 1000.0)


# === 哈希相关 ===
def hash_md5(text):
    return hashlib.md5(str(text).encode("utf-8")).hexdigest()


def hash_sha1(text):
    return hashlib.sha1(str(text).encode("utf-8")).hexdigest()


def hash_sha256(text):
    return hashlib.sha256(str(text).encode("utf-8")).hexdigest()


def hash_blake2b(text):
    return hashlib.blake2b(str(text).encode("utf-8")).hexdigest()


def verify_hash(text, expected, algo="md5"):
    actual = {
        "md5": hash_md5,
        "sha1": hash_sha1,
        "sha256": hash_sha256,
    }.get(algo, hash_md5)(text)
    return actual == expected


# === 路径相关 ===
def path_join(*parts):
    return os.path.join(*parts)


def path_split(p):
    return os.path.split(p)


def path_basename(p):
    return os.path.basename(p)


def path_dirname(p):
    return os.path.dirname(p)


def path_ext(p):
    _, ext = os.path.splitext(p)
    return ext


def path_no_ext(p):
    name, _ = os.path.splitext(p)
    return name


def path_exists(p):
    return os.path.exists(p)


def path_isfile(p):
    return os.path.isfile(p)


def path_isdir(p):
    return os.path.isdir(p)


def path_size(p):
    try:
        return os.path.getsize(p)
    except Exception:
        return 0


# === URL 相关 ===
def url_scheme(url):
    try:
        return urllib.parse.urlparse(url).scheme
    except Exception:
        return ""


def url_netloc(url):
    try:
        return urllib.parse.urlparse(url).netloc
    except Exception:
        return ""


def url_path(url):
    try:
        return urllib.parse.urlparse(url).path
    except Exception:
        return ""


def url_query(url):
    try:
        return urllib.parse.urlparse(url).query
    except Exception:
        return ""


def url_fragment(url):
    try:
        return urllib.parse.urlparse(url).fragment
    except Exception:
        return ""


def url_params(url):
    try:
        return dict(urllib.parse.parse_qsl(urllib.parse.urlparse(url).query))
    except Exception:
        return {}


def url_build(scheme="", netloc="", path="", params="", query="", fragment=""):
    return urllib.parse.urlunparse((scheme, netloc, path, params, query, fragment))


# === 集合操作 ===
def list_intersection(a, b):
    return list(set(a) & set(b))


def list_union(a, b):
    return list(set(a) | set(b))


def list_difference(a, b):
    return list(set(a) - set(b))


def list_symmetric_difference(a, b):
    return list(set(a) ^ set(b))


def list_subset(a, b):
    return set(a).issubset(set(b))


def list_superset(a, b):
    return set(a).issuperset(set(b))


def list_disjoint(a, b):
    return set(a).isdisjoint(set(b))


def list_remove_duplicates(seq, key=None):
    """保持顺序去重"""
    seen = set()
    out = []
    for item in seq:
        k = key(item) if key else item
        if k in seen:
            continue
        seen.add(k)
        out.append(item)
    return out


def list_group_by(seq, key):
    out = {}
    for item in seq:
        k = key(item) if callable(key) else item.get(key)
        out.setdefault(k, []).append(item)
    return out


def list_chunk(seq, size):
    return [seq[i:i + size] for i in range(0, len(seq), size)]


def list_flatten(seq, depth=None):
    out = []
    for item in seq:
        if isinstance(item, (list, tuple)):
            if depth is None or depth > 0:
                out.extend(list_flatten(item, depth - 1 if depth else None))
            else:
                out.append(item)
        else:
            out.append(item)
    return out


def list_compact(seq):
    return [x for x in seq if x is not None and x != ""]


def list_intersection_by(seq, key):
    keys = [key(x) for x in seq]
    return list(set(keys))


# === 字典操作 ===
def dict_get(d, *keys, default=None):
    cur = d
    for k in keys:
        if isinstance(cur, dict):
            cur = cur.get(k, default)
        else:
            return default
    return cur


def dict_set(d, *keys_and_value):
    """dict_set(d, 'a', 'b', 1) 等价于 d['a']['b'] = 1"""
    if len(keys_and_value) < 2:
        raise ValueError("至少需要 key 和 value")
    keys = keys_and_value[:-1]
    value = keys_and_value[-1]
    cur = d
    for k in keys[:-1]:
        if k not in cur or not isinstance(cur[k], dict):
            cur[k] = {}
        cur = cur[k]
    cur[keys[-1]] = value
    return d


def dict_pick(d, keys):
    return {k: d[k] for k in keys if k in d}


def dict_omit(d, keys):
    return {k: v for k, v in d.items() if k not in keys}


def dict_invert(d):
    return {v: k for k, v in d.items()}


def dict_merge(a, b):
    out = dict(a)
    out.update(b)
    return out


def dict_merge_deep(a, b):
    out = dict(a)
    for k, v in b.items():
        if k in out and isinstance(out[k], dict) and isinstance(v, dict):
            out[k] = dict_merge_deep(out[k], v)
        else:
            out[k] = v
    return out


def dict_flatten(d, prefix=""):
    out = {}
    for k, v in d.items():
        key = f"{prefix}.{k}" if prefix else k
        if isinstance(v, dict):
            out.update(dict_flatten(v, key))
        else:
            out[key] = v
    return out


def dict_unflatten(flat):
    out = {}
    for k, v in flat.items():
        dict_set(out, *k.split("."), v)
    return out


def dict_filter(d, predicate):
    return {k: v for k, v in d.items() if predicate(k, v)}


def dict_map_values(d, mapper):
    return {k: mapper(v) for k, v in d.items()}


def dict_map_keys(d, mapper):
    return {mapper(k): v for k, v in d.items()}


def dict_keys_sorted(d, reverse=False):
    return sorted(d.keys(), reverse=reverse)


def dict_values_sorted_by_key(d, reverse=False):
    return [d[k] for k in sorted(d.keys(), reverse=reverse)]


def dict_items_sorted_by_key(d, reverse=False):
    return sorted(d.items(), reverse=reverse)


# === 验证 ===
def is_email(s):
    if not s:
        return False
    return bool(re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", s))


def is_url(s):
    if not s:
        return False
    return bool(re.match(r"^https?://", s))


def is_phone(s):
    if not s:
        return False
    return bool(re.match(r"^1[3-9]\d{9}$", s))


def is_ipv4(s):
    if not s:
        return False
    parts = s.split(".")
    if len(parts) != 4:
        return False
    try:
        return all(0 <= int(p) <= 255 for p in parts)
    except Exception:
        return False


def is_chinese_only(s):
    if not s:
        return False
    return bool(re.match(r"^[\u4e00-\u9fff]+$", s))


def has_chinese(s):
    if not s:
        return False
    return bool(re.search(r"[\u4e00-\u9fff]", s))


def is_pure_english(s):
    if not s:
        return False
    return bool(re.match(r"^[a-zA-Z\s]+$", s))


# === 文件操作 ===
def read_text(path, encoding="utf-8"):
    try:
        with open(path, "r", encoding=encoding) as f:
            return f.read()
    except Exception:
        return None


def write_text(path, content, encoding="utf-8"):
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding=encoding) as f:
            f.write(content)
        return True
    except Exception:
        return False


def append_text(path, content, encoding="utf-8"):
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "a", encoding=encoding) as f:
            f.write(content)
        return True
    except Exception:
        return False


def file_exists(path):
    return os.path.isfile(path)


def list_dir_files(path, ext=None):
    if not os.path.isdir(path):
        return []
    out = []
    for f in os.listdir(path):
        full = os.path.join(path, f)
        if os.path.isfile(full):
            if ext is None or full.endswith(ext):
                out.append(full)
    return out


def ensure_path(path):
    if not path:
        return False
    try:
        os.makedirs(path, exist_ok=True)
        return True
    except Exception:
        return False


# === 随机 ===
def random_string(length=8):
    import random
    import string
    chars = string.ascii_letters + string.digits
    return "".join(random.choice(chars) for _ in range(length))


def random_int(lo, hi):
    import random
    return random.randint(lo, hi)


def random_float(lo, hi):
    import random
    return random.uniform(lo, hi)


def random_choice(seq):
    import random
    if not seq:
        return None
    return random.choice(seq)


def random_sample(seq, k):
    import random
    return random.sample(seq, min(k, len(seq)))


def shuffle(seq):
    import random
    s = list(seq)
    random.shuffle(s)
    return s


# === 日期 ===
def today(fmt="%Y-%m-%d"):
    return datetime.date.today().strftime(fmt)


def yesterday(fmt="%Y-%m-%d"):
    return (datetime.date.today() - datetime.timedelta(days=1)).strftime(fmt)


def tomorrow(fmt="%Y-%m-%d"):
    return (datetime.date.today() + datetime.timedelta(days=1)).strftime(fmt)


def now_datetime():
    return datetime.datetime.now()


def utc_now():
    return datetime.datetime.now(datetime.timezone.utc)


def date_diff(d1, d2):
    """按天算 diff"""
    try:
        a = datetime.datetime.strptime(d1, "%Y-%m-%d")
        b = datetime.datetime.strptime(d2, "%Y-%m-%d")
        return (a - b).days
    except Exception:
        return 0


def add_days(date_str, days, fmt="%Y-%m-%d"):
    try:
        d = datetime.datetime.strptime(date_str, fmt)
        return (d + datetime.timedelta(days=days)).strftime(fmt)
    except Exception:
        return date_str


# === 一些 helper class ===
class Counter:
    def __init__(self):
        self._data = {}
        self._lock = threading.Lock()

    def inc(self, key, n=1):
        with self._lock:
            self._data[key] = self._data.get(key, 0) + n

    def get(self, key, default=0):
        with self._lock:
            return self._data.get(key, default)

    def all(self):
        with self._lock:
            return dict(self._data)

    def reset(self):
        with self._lock:
            self._data.clear()

    def total(self):
        with self._lock:
            return sum(self._data.values())


class StopWatch:
    def __init__(self):
        self._start = None
        self._stop = None

    def start(self):
        self._start = time.time()
        return self

    def stop(self):
        self._stop = time.time()
        return self

    def elapsed(self):
        if self._start is None:
            return 0
        end = self._stop or time.time()
        return end - self._start

    def elapsed_ms(self):
        return int(self.elapsed() * 1000)


class Bag:
    def __init__(self):
        self._items = []
        self._lock = threading.Lock()

    def add(self, item):
        with self._lock:
            self._items.append(item)

    def remove(self, item):
        with self._lock:
            try:
                self._items.remove(item)
                return True
            except ValueError:
                return False

    def all(self):
        with self._lock:
            return list(self._items)

    def size(self):
        with self._lock:
            return len(self._items)

    def clear(self):
        with self._lock:
            self._items.clear()

    def contains(self, item):
        with self._lock:
            return item in self._items


class RingBuffer:
    def __init__(self, capacity=100):
        self.capacity = capacity
        self._data = []
        self._idx = 0

    def push(self, item):
        if len(self._data) < self.capacity:
            self._data.append(item)
        else:
            self._data[self._idx] = item
            self._idx = (self._idx + 1) % self.capacity

    def all(self):
        if len(self._data) < self.capacity:
            return list(self._data)
        return self._data[self._idx:] + self._data[:self._idx]

    def size(self):
        return len(self._data)

    def clear(self):
        self._data.clear()
        self._idx = 0