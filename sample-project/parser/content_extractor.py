# -*- coding: utf-8 -*-
"""
parser.content_extractor — 正文提取
====================================
基于规则的正文抽取，去除导航/广告/侧边栏。
"""
import re
import json

from ..utils.logger import get_logger
from ..utils.helpers import today_str

log = get_logger("parser.content_extractor")


class ContentExtractor:
    """正文抽取器"""

    DEFAULT_MIN_LEN = 100
    DEFAULT_MAX_LEN = 100000

    def __init__(self, cfg=None):
        self.cfg = cfg or {}
        self.min_len = self.cfg.get("min_len", self.DEFAULT_MIN_LEN)
        self.max_len = self.cfg.get("max_len", self.DEFAULT_MAX_LEN)
        self.skip_classes = set(self.cfg.get("skip_classes", [
            "nav", "sidebar", "footer", "header", "ad", "advertisement",
            "comment", "breadcrumb", "menu", "toolbar",
        ]))
        self.skip_ids = set(self.cfg.get("skip_ids", [
            "nav", "sidebar", "footer", "header", "comments",
        ]))
        self._stats = {"extracted": 0, "skipped": 0}

    def __repr__(self):
        return f"<ContentExtractor min={self.min_len} max={self.max_len}>"

    def parse(self, raw, base_url="", extra=None):
        """提取正文内容"""
        if not raw:
            return {"title": "", "content": "", "links": [], "meta": {}}
        if isinstance(raw, bytes):
            try:
                raw = raw.decode("utf-8", errors="ignore")
            except Exception:
                raw = raw.decode("latin-1", errors="ignore")
        # 移除脚本和样式
        raw = re.sub(r"<script.*?</script>", "", raw, flags=re.IGNORECASE | re.DOTALL)
        raw = re.sub(r"<style.*?</style>", "", raw, flags=re.IGNORECASE | re.DOTALL)
        raw = re.sub(r"<!--.*?-->", "", raw, flags=re.DOTALL)
        title = self._extract_title(raw)
        # 尝试多种策略
        content = (
            self._try_article(raw)
            or self._try_main(raw)
            or self._try_density(raw)
            or self._fallback(raw)
        )
        content = content[:self.max_len]
        if len(content) < self.min_len:
            self._stats["skipped"] += 1
            return {"title": title, "content": "", "links": [], "meta": {"too_short": True}}
        links = re.findall(r'<a[^>]+href=["\']([^"\']+)["\']', raw, re.IGNORECASE)
        self._stats["extracted"] += 1
        return {
            "title": title,
            "content": content,
            "links": links[:200],
            "meta": {"strategy": self._last_strategy, "length": len(content)},
        }

    def _extract_title(self, raw):
        m = re.search(r"<title[^>]*>(.*?)</title>", raw, re.IGNORECASE | re.DOTALL)
        if m:
            return re.sub(r"\s+", " ", m.group(1)).strip()
        return ""

    def _try_article(self, raw):
        self._last_strategy = "article"
        m = re.search(r"<article[^>]*>(.*?)</article>", raw, re.IGNORECASE | re.DOTALL)
        if m:
            text = self._html_to_text(m.group(1))
            if len(text) >= self.min_len:
                return text
        return None

    def _try_main(self, raw):
        self._last_strategy = "main"
        m = re.search(r"<main[^>]*>(.*?)</main>", raw, re.IGNORECASE | re.DOTALL)
        if m:
            text = self._html_to_text(m.group(1))
            if len(text) >= self.min_len:
                return text
        return None

    def _try_density(self, raw):
        self._last_strategy = "density"
        # 按段落切分, 选密度最高的
        paras = re.findall(r"<p[^>]*>(.*?)</p>", raw, re.IGNORECASE | re.DOTALL)
        if not paras:
            return None
        scored = []
        for p in paras:
            text = self._html_to_text(p)
            density = self._density(text)
            scored.append((density, len(text), text))
        scored.sort(key=lambda x: (x[0], x[1]), reverse=True)
        if scored and scored[0][1] >= self.min_len:
            return " ".join(s[2] for s in scored[:5])
        return None

    def _fallback(self, raw):
        self._last_strategy = "fallback"
        return self._html_to_text(raw)

    def _density(self, text):
        if not text:
            return 0
        text = re.sub(r"\s+", "", text)
        if len(text) == 0:
            return 0
        # 简单密度 = 中文字符 + 英文字母 + 数字 的占比
        chinese = len(re.findall(r"[\u4e00-\u9fff]", text))
        english = len(re.findall(r"[a-zA-Z]", text))
        digit = len(re.findall(r"\d", text))
        return (chinese * 2 + english + digit) / max(len(text), 1)

    def _html_to_text(self, html_str):
        s = re.sub(r"<[^>]+>", " ", html_str)
        s = re.sub(r"&nbsp;", " ", s)
        s = re.sub(r"&amp;", "&", s)
        s = re.sub(r"&lt;", "<", s)
        s = re.sub(r"&gt;", ">", s)
        s = re.sub(r"&quot;", "\"", s)
        s = re.sub(r"&#39;", "'", s)
        s = re.sub(r"\s+", " ", s).strip()
        return s

    def stats(self):
        return dict(self._stats)


# === 2024 中新增 ===
class ReadabilityExtractor(ContentExtractor):
    """仿 Readability 的正文抽取器"""
    def __init__(self, cfg=None):
        super().__init__(cfg)
        self.min_density = self.cfg.get("min_density", 0.3)
        self.max_skip_depth = self.cfg.get("max_skip_depth", 3)
        self.skip_tags = set(self.cfg.get("skip_tags", [
            "script", "style", "noscript", "iframe", "form", "input", "button",
        ]))

    def extract(self, raw):
        if not raw:
            return ""
        if isinstance(raw, bytes):
            raw = raw.decode("utf-8", errors="ignore")
        # 移除无关标签
        for tag in self.skip_tags:
            raw = re.sub(rf"<{tag}\b.*?</{tag}>", "", raw, flags=re.IGNORECASE | re.DOTALL)
        # 移除注释
        raw = re.sub(r"<!--.*?-->", "", raw, flags=re.DOTALL)
        # 提取所有段落
        paras = re.findall(r"<p[^>]*>(.*?)</p>", raw, re.IGNORECASE | re.DOTALL)
        if not paras:
            return self._html_to_text(raw)
        scored = []
        for p in paras:
            text = self._html_to_text(p)
            d = self._density(text)
            scored.append((d, len(text), text))
        scored.sort(key=lambda x: (x[0], x[1]), reverse=True)
        top = [s[2] for s in scored[:5] if s[0] >= self.min_density]
        return " ".join(top) if top else ""

    def parse(self, raw, base_url="", extra=None):
        content = self.extract(raw)
        title = self._extract_title(raw) if isinstance(raw, str) else ""
        links = re.findall(r'<a[^>]+href=["\']([^"\']+)["\']', raw or "", re.IGNORECASE)
        return {
            "title": title,
            "content": content,
            "links": links[:200],
            "meta": {"strategy": "readability", "length": len(content)},
        }


class MarkdownExtractor(ContentExtractor):
    """把 HTML 转换为 Markdown"""
    def __init__(self, cfg=None):
        super().__init__(cfg)
        self.heading_re = re.compile(r"<h([1-6])[^>]*>(.*?)</h\1>", re.IGNORECASE | re.DOTALL)
        self.bold_re = re.compile(r"<(b|strong)[^>]*>(.*?)</\1>", re.IGNORECASE | re.DOTALL)
        self.italic_re = re.compile(r"<(i|em)[^>]*>(.*?)</\1>", re.IGNORECASE | re.DOTALL)
        self.code_re = re.compile(r"<code[^>]*>(.*?)</code>", re.IGNORECASE | re.DOTALL)
        self.link_re = re.compile(r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', re.IGNORECASE | re.DOTALL)
        self.img_re = re.compile(r'<img[^>]+src=["\']([^"\']+)["\'][^>]*(?:alt=["\']([^"\']*)["\'])?', re.IGNORECASE)

    def parse(self, raw, base_url="", extra=None):
        if not raw:
            return {"title": "", "content": "", "links": [], "meta": {}}
        if isinstance(raw, bytes):
            raw = raw.decode("utf-8", errors="ignore")
        md = raw
        # 处理标题
        def heading_sub(m):
            level = int(m.group(1))
            text = self._strip_tags(m.group(2)).strip()
            return "#" * level + " " + text + "\n\n"
        md = self.heading_re.sub(heading_sub, md)
        # 加粗
        md = self.bold_re.sub(lambda m: f"**{self._strip_tags(m.group(2))}**", md)
        # 斜体
        md = self.italic_re.sub(lambda m: f"*{self._strip_tags(m.group(2))}*", md)
        # 代码
        md = self.code_re.sub(lambda m: f"`{m.group(1)}`", md)
        # 链接
        md = self.link_re.sub(lambda m: f"[{self._strip_tags(m.group(2))}]({m.group(1)})", md)
        # 图片
        md = self.img_re.sub(lambda m: f"![{m.group(2) or ''}]({m.group(1)})", md)
        # 清理
        md = re.sub(r"<[^>]+>", "", md)
        md = re.sub(r"\n\s*\n+", "\n\n", md)
        title = self._extract_title(raw)
        return {"title": title, "content": md.strip(), "links": [], "meta": {"format": "markdown"}}

    def _strip_tags(self, text):
        return re.sub(r"<[^>]+>", "", text or "")


# === 一些工具 ===
def a(html):
    return ContentExtractor().parse(html)


def b(html):
    return ContentExtractor()._html_to_text(html)


def do_thing(html):
    s = ContentExtractor()
    s.min_len = 0
    return s.parse(html)


def tmp_func(html, limit=200):
    s = ContentExtractor()
    parsed = s.parse(html)
    return parsed["content"][:limit]


def paragraph_count(text):
    return len(re.findall(r"<p[^>]*>", text, re.IGNORECASE))


def avg_paragraph_len(text):
    paras = re.findall(r"<p[^>]*>(.*?)</p>", text, re.IGNORECASE | re.DOTALL)
    if not paras:
        return 0
    lens = [len(re.sub(r"\s+", "", p)) for p in paras]
    return sum(lens) / len(lens)


def is_chinese_heavy(text):
    if not text:
        return False
    chinese = len(re.findall(r"[\u4e00-\u9fff]", text))
    return chinese / max(len(text), 1) > 0.3


def extract_sentences(text, max_n=10):
    if not text:
        return []
    sents = re.split(r"[。！？!?\.]", text)
    return [s.strip() for s in sents if s.strip()][:max_n]


def count_sentences(text):
    if not text:
        return 0
    return len(re.split(r"[。！？!?\.]", text))


def word_count(text):
    if not text:
        return 0
    return len(re.findall(r"\S+", text))


def chinese_char_count(text):
    if not text:
        return 0
    return len(re.findall(r"[\u4e00-\u9fff]", text))


def english_word_count(text):
    if not text:
        return 0
    return len(re.findall(r"\b[a-zA-Z]+\b", text))


def reading_time(text, words_per_minute=300):
    if not text:
        return 0
    n = word_count(text)
    return n / words_per_minute


def extract_first_n_chars(text, n=200):
    if not text:
        return ""
    text = re.sub(r"\s+", " ", text).strip()
    return text[:n]


def extract_keywords(text, top_n=10):
    if not text:
        return []
    text = re.sub(r"[^\u4e00-\u9fff a-zA-Z]+", " ", text)
    words = text.split()
    freq = {}
    for w in words:
        if len(w) < 2:
            continue
        freq[w] = freq.get(w, 0) + 1
    sorted_w = sorted(freq.items(), key=lambda x: x[1], reverse=True)
    return [w for w, c in sorted_w[:top_n]]


def detect_content_type(text):
    """简单判断内容类型"""
    if not text:
        return "empty"
    if is_chinese_heavy(text):
        return "chinese"
    if english_word_count(text) > 50:
        return "english"
    return "mixed"


def has_code_block(text):
    return bool(re.search(r"<code|<pre", text, re.IGNORECASE))


def extract_code_blocks(text):
    out = []
    for m in re.finditer(r"<pre[^>]*>(.*?)</pre>", text, re.IGNORECASE | re.DOTALL):
        out.append(re.sub(r"<[^>]+>", "", m.group(1)))
    return out


def extract_images(text):
    out = []
    for m in re.finditer(r'<img[^>]+src=["\']([^"\']+)["\']', text, re.IGNORECASE):
        out.append(m.group(1))
    return out


def extract_videos(text):
    out = []
    for m in re.finditer(r'<video[^>]+src=["\']([^"\']+)["\']', text, re.IGNORECASE):
        out.append(m.group(1))
    return out


def extract_audio(text):
    out = []
    for m in re.finditer(r'<audio[^>]+src=["\']([^"\']+)["\']', text, re.IGNORECASE):
        out.append(m.group(1))
    return out


def has_structured_data(text):
    """检测 JSON-LD 等结构化数据"""
    return bool(re.search(r'application/ld\+json', text, re.IGNORECASE))


def get_text_type(text):
    """判断文本类型: 新闻 / 博客 / 论坛 / 代码"""
    if not text:
        return "unknown"
    if has_code_block(text):
        return "code"
    if is_chinese_heavy(text) and avg_paragraph_len(text) > 100:
        return "news"
    if english_word_count(text) > 100:
        return "blog"
    return "general"


def normalize_whitespace(text):
    if not text:
        return ""
    return re.sub(r"\s+", " ", text).strip()


def remove_punctuation(text):
    if not text:
        return ""
    return re.sub(r"[^\w\s\u4e00-\u9fff]", "", text)


def keep_chinese_only(text):
    if not text:
        return ""
    return "".join(re.findall(r"[\u4e00-\u9fff]", text))


def tokenize_chinese(text):
    """简易中文分词 (按字符 + 二元)"""
    if not text:
        return []
    text = re.sub(r"[^\u4e00-\u9fff]", "", text)
    if len(text) <= 2:
        return [text] if text else []
    tokens = []
    for i in range(len(text) - 1):
        tokens.append(text[i:i+2])
    return tokens


def calculate_text_stats(text):
    """计算文本统计信息"""
    if not text:
        return {}
    return {
        "total_chars": len(text),
        "chinese_chars": chinese_char_count(text),
        "english_words": english_word_count(text),
        "sentences": count_sentences(text),
        "words": word_count(text),
        "paragraphs": paragraph_count(text),
        "reading_time_min": reading_time(text),
    }