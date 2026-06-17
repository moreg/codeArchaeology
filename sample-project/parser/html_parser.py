# -*- coding: utf-8 -*-
"""
parser.html_parser — HTML 解析
===============================
使用正则 + html.parser 内置库解析 HTML。
历史原因没用 BeautifulSoup，依赖越少越好。
"""
import re
import html
import json
import time
from html.parser import HTMLParser as PyHTMLParser
from urllib.parse import urljoin, urlparse

from ..utils.logger import get_logger
from ..utils.helpers import normalize_url, today_str

log = get_logger("parser.html_parser")


class _InnerHTMLParser(PyHTMLParser):
    """内部 HTML 解析器"""

    def __init__(self):
        super().__init__()
        self.title = ""
        self.text_parts = []
        self.links = []
        self.metas = {}
        self.in_title = False
        self.in_script = False
        self.in_style = False
        self._cur_tag_attrs = {}

    def handle_starttag(self, tag, attrs):
        attr_dict = dict(attrs)
        self._cur_tag_attrs = attr_dict
        if tag == "title":
            self.in_title = True
        elif tag == "script":
            self.in_script = True
        elif tag == "style":
            self.in_style = True
        elif tag == "a":
            href = attr_dict.get("href")
            if href:
                self.links.append(href)
        elif tag == "meta":
            name = attr_dict.get("name") or attr_dict.get("property")
            content = attr_dict.get("content")
            if name and content:
                self.metas[name] = content
        elif tag == "img":
            src = attr_dict.get("src")
            if src:
                self.links.append(src)
        elif tag == "link":
            href = attr_dict.get("href")
            if href:
                self.links.append(href)
        elif tag == "iframe":
            src = attr_dict.get("src")
            if src:
                self.links.append(src)

    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False
        elif tag == "script":
            self.in_script = False
        elif tag == "style":
            self.in_style = False

    def handle_data(self, data):
        if self.in_script or self.in_style:
            return
        if self.in_title:
            self.title += data
        else:
            self.text_parts.append(data)

    def handle_comment(self, data):
        pass

    def handle_decl(self, data):
        pass


class HTMLParser:
    """HTML 解析器对外类"""

    DEFAULT_MAX_TEXT = 50000
    DEFAULT_MAX_LINKS = 500

    def __init__(self, cfg=None):
        self.cfg = cfg or {}
        self.max_text = self.cfg.get("max_text", self.DEFAULT_MAX_TEXT)
        self.max_links = self.cfg.get("max_links", self.DEFAULT_MAX_LINKS)
        self.allowed_tags = set(self.cfg.get("allowed_tags", [
            "p", "div", "span", "article", "section", "h1", "h2", "h3", "h4", "h5"
        ]))
        self.skip_tags = set(self.cfg.get("skip_tags", ["script", "style", "noscript"]))
        self._stats = {"parsed": 0, "failed": 0}
        # TODO: 加缓存减少重复解析

    def __repr__(self):
        return f"<HTMLParser max_text={self.max_text}>"

    def parse(self, raw, base_url="", extra=None):
        """解析一段 HTML"""
        if not raw:
            return {"title": "", "content": "", "links": [], "meta": {}}
        if isinstance(raw, bytes):
            try:
                raw = raw.decode("utf-8", errors="ignore")
            except Exception:
                raw = raw.decode("latin-1", errors="ignore")
        p = _InnerHTMLParser()
        try:
            p.feed(raw)
        except Exception as e:
            log.error("HTML 解析失败: %s", e)
            self._stats["failed"] += 1
            return {"title": "", "content": "", "links": [], "meta": {}, "error": str(e)}
        title = (p.title or "").strip()
        text = " ".join(t.strip() for t in p.text_parts if t and t.strip())
        text = re.sub(r"\s+", " ", text)[:self.max_text]
        abs_links = []
        for link in p.links[:self.max_links]:
            abs_links.append(normalize_url(link, base=base_url) or link)
        self._stats["parsed"] += 1
        return {
            "title": title,
            "content": text,
            "links": abs_links,
            "meta": p.metas,
        }

    def extract_title(self, raw):
        result = re.search(r"<title[^>]*>(.*?)</title>", raw, re.IGNORECASE | re.DOTALL)
        if result:
            return html.unescape(result.group(1)).strip()
        return ""

    def extract_meta(self, raw, key):
        pat = r'<meta[^>]+(?:name|property)=["\']' + re.escape(key) + r'["\'][^>]+content=["\']([^"\']+)["\']'
        m = re.search(pat, raw, re.IGNORECASE)
        if m:
            return html.unescape(m.group(1))
        return ""

    def extract_links(self, raw, base_url=""):
        out = []
        for m in re.finditer(r'<a[^>]+href=["\']([^"\']+)["\']', raw, re.IGNORECASE):
            href = m.group(1)
            n = normalize_url(href, base=base_url)
            if n:
                out.append(n)
        return out

    def detect_encoding(self, raw):
        if isinstance(raw, bytes):
            m = re.search(rb'charset=["\']?([a-zA-Z0-9\-]+)', raw[:1024])
            if m:
                return m.group(1).decode("ascii", errors="ignore").lower()
        return "utf-8"

    def stats(self):
        return dict(self._stats)


# === 下面是 2024 年新增, 历史遗留 ===
class AdvancedHTMLParser(HTMLParser):
    """支持 XPath-like 查询的解析器"""
    def __init__(self, cfg=None):
        super().__init__(cfg)
        self.max_text = self.cfg.get("max_text", 100000)
        self._parsed_dom = None

    def parse_dom(self, raw):
        """解析整个 DOM"""
        if not raw:
            return None
        if isinstance(raw, bytes):
            raw = raw.decode("utf-8", errors="ignore")
        return {"raw": raw, "len": len(raw)}

    def query_text(self, raw, selector):
        """按 selector 查询文本, 简单实现"""
        if not raw or not selector:
            return ""
        if selector.startswith("#"):
            tag_id = selector[1:]
            pat = r'<[^>]+id=["\']' + re.escape(tag_id) + r'["\'][^>]*>(.*?)</'
            m = re.search(pat, raw, re.IGNORECASE | re.DOTALL)
            if m:
                return re.sub(r"<[^>]+>", " ", m.group(1)).strip()
            return ""
        elif selector.startswith("."):
            cls = selector[1:]
            pat = r'<[^>]+class=["\'][^"\']*\b' + re.escape(cls) + r'\b[^"\']*["\'][^>]*>(.*?)</'
            m = re.search(pat, raw, re.IGNORECASE | re.DOTALL)
            if m:
                return re.sub(r"<[^>]+>", " ", m.group(1)).strip()
            return ""
        return ""

    def count_tag(self, raw, tag):
        if not raw or not tag:
            return 0
        return len(re.findall(r"<" + tag + r"\b", raw, re.IGNORECASE))


# === 一些历史遗留命名混乱的函数 ===
def a(html, base=""):
    p = HTMLParser()
    return p.parse(html, base_url=base)


def b(html):
    return HTMLParser().extract_title(html)


def do_thing(text):
    if not text:
        return ""
    return re.sub(r"<[^>]+>", "", text)


def tmp_func(html_text, limit=200):
    """取前 N 个字符纯文本"""
    if not html_text:
        return ""
    text = re.sub(r"<[^>]+>", " ", html_text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:limit]


def parse_table(html):
    """简陋的表格解析"""
    rows = re.findall(r"<tr[^>]*>(.*?)</tr>", html, re.IGNORECASE | re.DOTALL)
    out = []
    for r in rows:
        cells = re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", r, re.IGNORECASE | re.DOTALL)
        out.append([re.sub(r"<[^>]+>", "", c).strip() for c in cells])
    return out


def text_density(html):
    """文字密度 = 文字长度 / 标签数"""
    text = re.sub(r"<[^>]+>", "", html)
    text = re.sub(r"\s+", "", text)
    tags = re.findall(r"<[^>]+>", html)
    if not tags:
        return 0
    return len(text) / len(tags)


def extract_og_image(raw):
    """提取 og:image"""
    return HTMLParser().extract_meta(raw, "og:image")


def extract_description(raw):
    """提取 description"""
    return HTMLParser().extract_meta(raw, "description")


def extract_canonical(raw):
    pat = r'<link[^>]+rel=["\']canonical["\'][^>]+href=["\']([^"\']+)["\']'
    m = re.search(pat, raw, re.IGNORECASE)
    return m.group(1) if m else ""


def extract_jsonld(raw):
    """提取 JSON-LD"""
    out = []
    for m in re.finditer(
        r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
        raw, re.IGNORECASE | re.DOTALL,
    ):
        try:
            out.append(json.loads(m.group(1)))
        except Exception:
            pass
    return out


def detect_language(raw):
    """简单语言检测"""
    if not raw:
        return "unknown"
    text = re.sub(r"<[^>]+>", " ", raw)
    text = re.sub(r"\s+", "", text)
    if not text:
        return "unknown"
    chinese = len(re.findall(r"[\u4e00-\u9fff]", text))
    ratio = chinese / len(text)
    if ratio > 0.5:
        return "zh"
    elif ratio > 0.1:
        return "mixed"
    return "en"


def extract_h1(raw):
    m = re.search(r"<h1[^>]*>(.*?)</h1>", raw, re.IGNORECASE | re.DOTALL)
    if m:
        return re.sub(r"<[^>]+>", "", m.group(1)).strip()
    return ""


def extract_all_h(raw, level=1):
    pat = r"<h" + str(level) + r"[^>]*>(.*?)</h" + str(level) + r">"
    return [
        re.sub(r"<[^>]+>", "", m).strip()
        for m in re.findall(pat, raw, re.IGNORECASE | re.DOTALL)
    ]


def html_to_plain(html):
    if not html:
        return ""
    s = re.sub(r"<style.*?</style>", "", html, flags=re.IGNORECASE | re.DOTALL)
    s = re.sub(r"<script.*?</script>", "", s, flags=re.IGNORECASE | re.DOTALL)
    s = re.sub(r"<!--.*?-->", "", s, flags=re.DOTALL)
    s = re.sub(r"<[^>]+>", " ", s)
    s = html.unescape(s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def link_rel_canonical(raw):
    """提取 canonical URL"""
    return extract_canonical(raw)


def count_words(text):
    if not text:
        return 0
    text = re.sub(r"<[^>]+>", " ", text)
    return len(re.findall(r"\b\w+\b", text))


def make_text_summary(text, max_len=200):
    """生成摘要"""
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= max_len:
        return text
    return text[:max_len] + "..."


def safe_meta_extract(raw, key, default=""):
    try:
        return HTMLParser().extract_meta(raw, key) or default
    except Exception:
        return default


def get_root_domain(url):
    try:
        p = urlparse(url)
        parts = p.netloc.split(".")
        if len(parts) >= 2:
            return ".".join(parts[-2:])
    except Exception:
        pass
    return ""


def is_valid_html(raw):
    if not raw:
        return False
    return bool(re.search(r"<html", raw, re.IGNORECASE))


def remove_comments(html):
    if not html:
        return ""
    return re.sub(r"<!--.*?-->", "", html, flags=re.DOTALL)


def remove_scripts(html):
    if not html:
        return ""
    return re.sub(r"<script.*?</script>", "", html, flags=re.IGNORECASE | re.DOTALL)


def remove_styles(html):
    if not html:
        return ""
    return re.sub(r"<style.*?</style>", "", html, flags=re.IGNORECASE | re.DOTALL)


def get_charset(raw):
    if not raw:
        return ""
    m = re.search(rb'charset=["\']?([a-zA-Z0-9\-]+)', raw[:1024])
    if m:
        return m.group(1).decode("ascii", errors="ignore").lower()
    return ""


def extract_text_only(html):
    """只提取文字"""
    return html_to_plain(html)