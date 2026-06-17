# -*- coding: utf-8 -*-
"""
parser.json_parser — JSON 解析器
=================================
解析 JSON 响应，提取字段。
"""
import json
import re
import time
import copy

from ..utils.logger import get_logger
from ..utils.helpers import today_str, normalize_url

log = get_logger("parser.json_parser")


class JSONParser:
    """JSON 解析器"""

    DEFAULT_MAX_DEPTH = 20
    DEFAULT_MAX_KEYS = 10000

    def __init__(self, cfg=None):
        self.cfg = cfg or {}
        self.max_depth = self.cfg.get("max_depth", self.DEFAULT_MAX_DEPTH)
        self.max_keys = self.cfg.get("max_keys", self.DEFAULT_MAX_KEYS)
        self.field_mapping = self.cfg.get("field_mapping", {
            "title": ["title", "name", "subject"],
            "content": ["content", "body", "text", "description"],
            "links": ["links", "url", "urls", "items"],
        })
        self._stats = {"parsed": 0, "failed": 0}

    def __repr__(self):
        return f"<JSONParser max_depth={self.max_depth}>"

    def parse(self, raw, base_url="", extra=None):
        """解析 JSON"""
        if not raw:
            return {"title": "", "content": "", "links": [], "meta": {}}
        if isinstance(raw, bytes):
            try:
                raw = raw.decode("utf-8", errors="ignore")
            except Exception:
                raw = raw.decode("latin-1", errors="ignore")
        try:
            data = json.loads(raw)
        except Exception as e:
            log.error("JSON 解析失败: %s", e)
            self._stats["failed"] += 1
            return {"title": "", "content": "", "links": [], "meta": {}, "error": str(e)}
        # 检查深度/键数量
        try:
            depth = self._depth(data, 0)
            keys = self._count_keys(data)
            if depth > self.max_depth or keys > self.max_keys:
                log.warning("数据过大 depth=%d keys=%d", depth, keys)
        except RecursionError:
            log.error("递归爆栈")
            return {"title": "", "content": "", "links": [], "meta": {}}
        title = self._extract_field(data, self.field_mapping["title"])
        content = self._extract_field(data, self.field_mapping["content"])
        links = self._extract_list(data, self.field_mapping["links"])
        abs_links = []
        for l in links:
            if isinstance(l, str):
                n = normalize_url(l, base=base_url) or l
                abs_links.append(n)
        self._stats["parsed"] += 1
        return {
            "title": str(title)[:512] if title else "",
            "content": str(content)[:8192] if content else "",
            "links": abs_links,
            "meta": {"depth": depth, "keys": keys},
        }

    def _extract_field(self, data, candidates):
        for c in candidates:
            v = self._dig(data, c)
            if v is not None:
                return v
        return ""

    def _extract_list(self, data, candidates):
        for c in candidates:
            v = self._dig(data, c)
            if isinstance(v, list):
                return v
            if isinstance(v, str):
                return [v]
        return []

    def _dig(self, data, key):
        """递归查找 key"""
        if isinstance(data, dict):
            if key in data:
                return data[key]
            for k, v in data.items():
                r = self._dig(v, key)
                if r is not None:
                    return r
        elif isinstance(data, list):
            for item in data:
                r = self._dig(item, key)
                if r is not None:
                    return r
        return None

    def _depth(self, data, d):
        if d > self.max_depth:
            return d
        if isinstance(data, dict):
            if not data:
                return d
            return max(self._depth(v, d + 1) for v in data.values())
        if isinstance(data, list):
            if not data:
                return d
            return max(self._depth(v, d + 1) for v in data)
        return d

    def _count_keys(self, data):
        cnt = 0
        def walk(x):
            nonlocal cnt
            if cnt > self.max_keys:
                return
            if isinstance(x, dict):
                cnt += len(x)
                for v in x.values():
                    walk(v)
            elif isinstance(x, list):
                for v in x:
                    walk(v)
        walk(data)
        return cnt

    def stats(self):
        return dict(self._stats)


class JSONSchemaValidator:
    """简单的 JSON Schema 校验器"""
    def __init__(self, schema=None):
        self.schema = schema or {}

    def validate(self, data):
        """校验 data 是否符合 schema"""
        if not isinstance(self.schema, dict):
            return True
        return self._validate_node(data, self.schema)

    def _validate_node(self, data, schema):
        if "type" in schema:
            t = schema["type"]
            if t == "object" and not isinstance(data, dict):
                return False
            if t == "array" and not isinstance(data, list):
                return False
            if t == "string" and not isinstance(data, str):
                return False
            if t == "number" and not isinstance(data, (int, float)):
                return False
            if t == "boolean" and not isinstance(data, bool):
                return False
            if t == "null" and data is not None:
                return False
        if "required" in schema and isinstance(data, dict):
            for k in schema["required"]:
                if k not in data:
                    return False
        if "properties" in schema and isinstance(data, dict):
            for k, sub_schema in schema["properties"].items():
                if k in data:
                    if not self._validate_node(data[k], sub_schema):
                        return False
        return True


# 历史遗留函数
def a(text):
    try:
        return json.loads(text)
    except Exception:
        return None


def b(text, path):
    """用 a.b.c 路径取值"""
    try:
        cur = json.loads(text)
        for p in path.split("."):
            if isinstance(cur, dict):
                cur = cur.get(p)
            elif isinstance(cur, list) and p.isdigit():
                cur = cur[int(p)]
            else:
                return None
        return cur
    except Exception:
        return None


def do_thing(data, key):
    return JSONParser()._dig(data, key)


def tmp_func(text):
    try:
        return json.loads(text) is not None
    except Exception:
        return False


def flatten(data, prefix=""):
    """展平嵌套字典"""
    out = {}
    if isinstance(data, dict):
        for k, v in data.items():
            new_key = f"{prefix}.{k}" if prefix else k
            if isinstance(v, (dict, list)):
                out.update(flatten(v, new_key))
            else:
                out[new_key] = v
    elif isinstance(data, list):
        for i, v in enumerate(data):
            out.update(flatten(v, f"{prefix}[{i}]"))
    return out


def safe_loads(text, default=None):
    try:
        return json.loads(text)
    except Exception:
        return default


def healthcheck():
    return {"ok": True, "ts": today_str()}


def merge_json(a, b):
    """递归合并两个 JSON"""
    if not isinstance(a, dict):
        return b
    if not isinstance(b, dict):
        return a
    out = copy.deepcopy(a)
    for k, v in b.items():
        if k in out:
            out[k] = merge_json(out[k], v)
        else:
            out[k] = v
    return out


def pluck(items, key):
    """从 list of dict 中提取某个字段"""
    out = []
    for it in items:
        if isinstance(it, dict) and key in it:
            out.append(it[key])
    return out


def group_by(items, key):
    """按 key 分组"""
    out = {}
    for it in items:
        if isinstance(it, dict) and key in it:
            k = it[key]
            if k not in out:
                out[k] = []
            out[k].append(it)
    return out


def filter_keys(data, allowed_keys):
    """只保留白名单 keys"""
    if not isinstance(data, dict):
        return {}
    return {k: v for k, v in data.items() if k in allowed_keys}


def remove_keys(data, banned_keys):
    """移除黑名单 keys"""
    if not isinstance(data, dict):
        return {}
    return {k: v for k, v in data.items() if k not in banned_keys}


def deep_get(data, path, default=None):
    """a.b.c 路径取值"""
    cur = data
    for p in path.split("."):
        if isinstance(cur, dict):
            cur = cur.get(p, default)
        elif isinstance(cur, list) and p.isdigit():
            cur = cur[int(p)] if int(p) < len(cur) else default
        else:
            return default
    return cur


def deep_set(data, path, value):
    """a.b.c 路径赋值"""
    parts = path.split(".")
    cur = data
    for p in parts[:-1]:
        if p not in cur or not isinstance(cur[p], dict):
            cur[p] = {}
        cur = cur[p]
    cur[parts[-1]] = value
    return data


def to_json_string(obj, indent=None):
    return json.dumps(obj, ensure_ascii=False, indent=indent, default=str)


def from_json_string(text, default=None):
    try:
        return json.loads(text)
    except Exception:
        return default


def is_json_object(text):
    if not text:
        return False
    try:
        o = json.loads(text)
        return isinstance(o, dict)
    except Exception:
        return False


def is_json_array(text):
    if not text:
        return False
    try:
        o = json.loads(text)
        return isinstance(o, list)
    except Exception:
        return False


def count_items(data):
    """统计元素数量"""
    if isinstance(data, list):
        return len(data)
    elif isinstance(data, dict):
        return len(data)
    return 0


def to_one_line(text):
    """折叠成一行"""
    try:
        o = json.loads(text)
        return json.dumps(o, ensure_ascii=False, separators=(",", ":"))
    except Exception:
        return text


def pretty(text, indent=2):
    """美化"""
    try:
        o = json.loads(text)
        return json.dumps(o, ensure_ascii=False, indent=indent)
    except Exception:
        return text