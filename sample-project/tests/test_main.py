# -*- coding: utf-8 -*-
"""
tests.test_main — 基础测试
===========================
覆盖率约 20%, 故意不全, 反映老项目的真实状况。
"""
import os
import sys
import unittest
import time
import json
import re

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.helpers import (
    normalize_url, today_str, file_hash, sleep_jitter, safe_int,
    url_hash, md5, sha1, sha256, truncate, chunked, flatten, unique,
    ensure_dir, safe_float, is_probably_html, hostname, uptime, to_json, from_json,
    clamp, lerp, percent, parse_duration, slugify, camel_to_snake,
    snake_to_camel, group_by, sort_by, take, skip, filter_items,
)
from utils.decorators import timer, safe_run, retry, thread_safe
from utils.http_retry import http_retry, RetryError, exponential_backoff, safe_call
from utils.logger import get_logger, list_loggers
from parser.html_parser import HTMLParser, AdvancedHTMLParser
from parser.json_parser import JSONParser, JSONSchemaValidator
from parser.content_extractor import ContentExtractor, ReadabilityExtractor, MarkdownExtractor
from database.db_manager import DBManager, DBQuery
from database.models import (
    Record, Failure, Task, Author, GitCommit, GitBlame,
    ScanResult, AnalysisResult,
)
from config.load_config import (
    parse_config, merge, validate_config, save_config,
    get_nested_value, set_nested_value,
)
from config.settings import (
    DEFAULT_DB_PATH, EXT_TO_LANG, get_rating,
    list_supported_langs, list_supported_exts,
)
from crawler.url_manager import URLManager, URLFilter
from crawler.downloader import Downloader, parse_content_type


class TestHelpers(unittest.TestCase):
    def test_normalize_url(self):
        self.assertEqual(
            normalize_url("/a/b", base="https://x.com/c"),
            "https://x.com/a/b",
        )
        self.assertIsNone(normalize_url("javascript:alert(1)"))
        self.assertIsNone(normalize_url(""))

    def test_today_str(self):
        s = today_str()
        self.assertIsInstance(s, str)
        self.assertGreater(len(s), 0)

    def test_file_hash(self):
        self.assertEqual(file_hash("abc"), file_hash(b"abc"))
        self.assertEqual(file_hash(""), "")

    def test_safe_int(self):
        self.assertEqual(safe_int("42"), 42)
        self.assertEqual(safe_int("abc", default=1), 1)
        self.assertEqual(safe_int(None), 0)

    def test_safe_float(self):
        self.assertEqual(safe_float("3.14"), 3.14)
        self.assertEqual(safe_float("abc", default=1.0), 1.0)
        self.assertEqual(safe_float(None), 0.0)

    def test_url_hash(self):
        self.assertEqual(url_hash("https://a.com"), url_hash("https://a.com"))
        self.assertNotEqual(url_hash("a"), url_hash("b"))
        self.assertEqual(url_hash(""), "")

    def test_md5_sha(self):
        self.assertEqual(len(md5("x")), 32)
        self.assertEqual(len(sha1("x")), 40)
        self.assertEqual(len(sha256("x")), 64)

    def test_truncate(self):
        self.assertEqual(truncate("hello world", 5), "he...")
        self.assertEqual(truncate("", 5), "")

    def test_chunked(self):
        self.assertEqual(chunked([1,2,3,4,5], 2), [[1,2],[3,4],[5]])

    def test_flatten(self):
        self.assertEqual(flatten([[1,2],[3,[4]]]), [1,2,3,[4]])

    def test_unique(self):
        self.assertEqual(unique([1,2,2,3]), [1,2,3])
        self.assertEqual(unique(["a","b","a"]), ["a","b"])

    def test_ensure_dir(self):
        d = "/tmp/_test_ensure_dir"
        self.assertTrue(ensure_dir(d))
        try:
            os.rmdir(d)
        except Exception:
            pass

    def test_clamp(self):
        self.assertEqual(clamp(5, 0, 10), 5)
        self.assertEqual(clamp(-1, 0, 10), 0)
        self.assertEqual(clamp(20, 0, 10), 10)

    def test_lerp(self):
        self.assertEqual(lerp(0, 10, 0.5), 5)

    def test_percent(self):
        self.assertEqual(percent(50, 100), 50)
        self.assertEqual(percent(1, 0), 0)

    def test_parse_duration(self):
        self.assertEqual(parse_duration("1h30m"), 5400)
        self.assertEqual(parse_duration("2m"), 120)
        self.assertEqual(parse_duration(""), 0)

    def test_slugify(self):
        self.assertEqual(slugify("Hello World"), "hello-world")
        self.assertEqual(slugify(""), "")

    def test_camel_snake(self):
        self.assertEqual(camel_to_snake("HelloWorld"), "hello_world")
        self.assertEqual(snake_to_camel("hello_world"), "helloWorld")

    def test_group_by(self):
        result = group_by([{"a": 1}, {"a": 2}, {"a": 1}], "a")
        self.assertEqual(len(result[1]), 2)
        self.assertEqual(len(result[2]), 1)


class TestDecorators(unittest.TestCase):
    def test_timer(self):
        @timer
        def f():
            return 1
        self.assertEqual(f(), 1)

    def test_safe_run(self):
        @safe_run
        def boom():
            raise RuntimeError("x")
        self.assertIsNone(boom())

    def test_retry(self):
        calls = [0]
        @retry(max_attempts=2, delay=0)
        def f():
            calls[0] += 1
            if calls[0] < 2:
                raise ValueError("again")
            return "ok"
        self.assertEqual(f(), "ok")

    def test_thread_safe(self):
        counter = [0]
        @thread_safe
        def inc():
            counter[0] += 1
            return counter[0]
        inc()
        inc()
        self.assertEqual(counter[0], 2)


class TestRetry(unittest.TestCase):
    def test_exponential_backoff(self):
        d1 = exponential_backoff(1, base=1.0, factor=2.0, jitter=False)
        d2 = exponential_backoff(2, base=1.0, factor=2.0, jitter=False)
        d3 = exponential_backoff(3, base=1.0, factor=2.0, jitter=False)
        self.assertEqual(d1, 1.0)
        self.assertEqual(d2, 2.0)
        self.assertEqual(d3, 4.0)

    def test_safe_call(self):
        def boom():
            raise RuntimeError()
        self.assertIsNone(safe_call(boom, default="x"))

    def test_http_retry(self):
        @http_retry(max_attempts=2, delay=0)
        def f():
            raise ValueError("test")
        with self.assertRaises(RetryError):
            f()


class TestHTMLParser(unittest.TestCase):
    def setUp(self):
        self.p = HTMLParser()

    def test_parse_simple(self):
        html = "<html><head><title>T</title></head><body><a href='/x'>x</a><p>hello</p></body></html>"
        r = self.p.parse(html, base_url="https://a.com/")
        self.assertEqual(r["title"], "T")
        self.assertIn("hello", r["content"])
        self.assertIn("https://a.com/x", r["links"])

    def test_extract_title(self):
        self.assertEqual(self.p.extract_title("<title>Hi</title>"), "Hi")

    def test_extract_links(self):
        html = '<a href="/a">a</a><a href="https://b.com/b">b</a>'
        links = self.p.extract_links(html, base_url="https://x.com/")
        self.assertIn("https://x.com/a", links)
        self.assertIn("https://b.com/b", links)

    def test_extract_meta(self):
        html = '<html><head><meta name="description" content="abc"></head></html>'
        self.assertEqual(self.p.extract_meta(html, "description"), "abc")

    def test_advanced_parser(self):
        p = AdvancedHTMLParser()
        html = '<div id="content">Hello</div><p>World</p>'
        text = p.query_text(html, "#content")
        self.assertIn("Hello", text)


class TestJSONParser(unittest.TestCase):
    def setUp(self):
        self.p = JSONParser()

    def test_parse(self):
        raw = '{"title": "hello", "content": "world", "items": ["a", "b"]}'
        r = self.p.parse(raw)
        self.assertEqual(r["title"], "hello")
        self.assertEqual(r["content"], "world")
        self.assertEqual(len(r["links"]), 2)

    def test_invalid(self):
        r = self.p.parse("not json")
        self.assertIn("error", r)

    def test_nested(self):
        raw = '{"a": {"b": {"title": "deep"}}}'
        r = self.p.parse(raw)
        self.assertEqual(r["title"], "deep")

    def test_schema_validator(self):
        validator = JSONSchemaValidator({"type": "object", "required": ["name"]})
        self.assertTrue(validator.validate({"name": "x"}))
        self.assertFalse(validator.validate({}))


class TestContentExtractor(unittest.TestCase):
    def test_basic(self):
        html = "<html><body><article><p>Hello world!</p><p>This is a test.</p></article></body></html>"
        e = ContentExtractor(min_len=10)
        r = e.parse(html)
        self.assertIn("Hello", r["content"])

    def test_short_content(self):
        html = "<html><body><article><p>Hi</p></article></body></html>"
        e = ContentExtractor(min_len=100)
        r = e.parse(html)
        self.assertEqual(r["content"], "")

    def test_readability(self):
        e = ReadabilityExtractor()
        r = e.extract("<article><p>" + "word " * 200 + "</p></article>")
        self.assertGreater(len(r), 0)

    def test_markdown(self):
        e = MarkdownExtractor()
        r = e.parse("<h1>Title</h1><p>Body</p>")
        self.assertIn("Title", r["content"])


class TestDB(unittest.TestCase):
    def setUp(self):
        self.db = DBManager(":memory:")
        self.db.init_schema()

    def test_save_and_get(self):
        self.db.save_record({
            "url": "https://a.com",
            "parser": "html",
            "title": "T",
            "content": "C",
            "links": ["https://b.com"],
            "meta": {},
        })
        rec = self.db.get_record("https://a.com")
        self.assertIsNotNone(rec)
        self.assertEqual(rec["title"], "T")

    def test_stats(self):
        s = self.db.stats()
        self.assertIn("total", s)

    def test_mark_failed(self):
        self.db.mark_failed("https://x.com", "timeout")
        s = self.db.stats()
        self.assertEqual(s["failed"], 1)

    def test_query(self):
        self.db.save_record({"url": "https://a.com", "parser": "html", "title": "T"})
        q = DBQuery(self.db, "records").eq("parser", "html")
        results = q.all()
        self.assertEqual(len(results), 1)


class TestModels(unittest.TestCase):
    def test_record(self):
        r = Record(url="https://a.com", parser="html", title="T")
        d = r.to_dict()
        self.assertEqual(d["url"], "https://a.com")
        r2 = Record.from_dict(d)
        self.assertEqual(r.url, r2.url)

    def test_failure(self):
        f = Failure("https://x", "timeout")
        self.assertEqual(f.reason, "timeout")

    def test_task(self):
        t = Task(url="https://x", target="demo")
        self.assertEqual(t.status, "pending")


class TestConfig(unittest.TestCase):
    def test_default(self):
        cfg = parse_config()
        self.assertIn("db_path", cfg)
        self.assertIn("downloader", cfg)

    def test_override(self):
        cfg = parse_config(override={"workers": 99})
        self.assertEqual(cfg["workers"], 99)

    def test_merge(self):
        a = {"x": 1, "y": {"a": 1}}
        b = {"y": {"b": 2}}
        self.assertEqual(merge(a, b), {"x": 1, "y": {"a": 1, "b": 2}})

    def test_validate(self):
        cfg = parse_config()
        errors = validate_config(cfg)
        self.assertEqual(len(errors), 0)

    def test_nested_get_set(self):
        cfg = {"a": {"b": 1}}
        self.assertEqual(get_nested_value(cfg, "a.b"), 1)
        set_nested_value(cfg, "a.c", 2)
        self.assertEqual(cfg["a"]["c"], 2)

    def test_settings_rating(self):
        rating, color, label = get_rating(95)
        self.assertEqual(rating, "excellent")
        rating, color, label = get_rating(25)
        self.assertEqual(rating, "danger")

    def test_langs(self):
        self.assertIn("python", list_supported_langs())
        self.assertIn(".py", list_supported_exts())


class TestURLManager(unittest.TestCase):
    def test_basic(self):
        m = URLManager(seed_urls=["https://a.com", "https://b.com"])
        self.assertEqual(m.seen_size(), 2)
        item = m.next()
        self.assertIsNotNone(item)
        self.assertEqual(item["depth"], 0)

    def test_dedup(self):
        m = URLManager(seed_urls=["https://a.com"])
        m.push("https://a.com")
        self.assertEqual(m.seen_size(), 1)

    def test_filter(self):
        f = URLFilter(allow=[r".*example.*"], deny=[r".*\.png$"])
        self.assertTrue(f.check("https://example.com/page"))
        self.assertFalse(f.check("https://other.com"))
        self.assertFalse(f.check("https://example.com/logo.png"))


class TestDownloader(unittest.TestCase):
    def test_content_type(self):
        main, params = parse_content_type("text/html; charset=utf-8")
        self.assertEqual(main, "text/html")
        self.assertEqual(params["charset"], "utf-8")

    def test_downloader_init(self):
        d = Downloader(timeout=10, retry=2)
        self.assertEqual(d.timeout, 10)
        self.assertEqual(d.retry, 2)


class TestIntegration(unittest.TestCase):
    def test_end_to_end(self):
        db = DBManager(":memory:")
        db.init_schema()
        html = "<html><body><article><p>" + "x" * 200 + "</p></article></body></html>"
        e = ContentExtractor(min_len=50)
        r = e.parse(html)
        self.assertGreater(len(r["content"]), 0)


if __name__ == "__main__":
    unittest.main()