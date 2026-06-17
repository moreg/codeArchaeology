# -*- coding: utf-8 -*-
"""
tests.test_extra — 一些额外测试
================================
"""
import os
import sys
import unittest
import time
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestIntegration(unittest.TestCase):
    def test_full_flow(self):
        from utils.helpers import normalize_url, file_hash, today_str
        from parser.html_parser import HTMLParser
        from database.db_manager import DBManager

        db = DBManager(":memory:")
        db.init_schema()
        p = HTMLParser()
        html = "<html><body><article><p>" + "word " * 100 + "</p></article></body></html>"
        result = p.parse(html, base_url="https://test.com/")
        self.assertGreater(len(result["content"]), 0)
        self.assertTrue(db.save_record({
            "url": "https://test.com/",
            "parser": "html",
            "title": result["title"],
            "content": result["content"][:1000],
            "links": result["links"],
            "meta": {},
        }))
        rec = db.get_record("https://test.com/")
        self.assertIsNotNone(rec)

    def test_url_pipeline(self):
        from crawler.url_manager import URLManager
        m = URLManager()
        for u in ["https://a.com", "https://b.com", "https://a.com/page"]:
            m.push(u, depth=1)
        self.assertEqual(m.seen_size(), 3)
        items = [m.next() for _ in range(3)]
        self.assertTrue(all(i is not None for i in items))


class TestPerformance(unittest.TestCase):
    def test_parser_speed(self):
        from parser.html_parser import HTMLParser
        p = HTMLParser()
        html = "<html><body>" + ("<p>x</p>" * 100) + "</body></html>"
        start = time.time()
        for _ in range(100):
            p.parse(html, base_url="https://x.com/")
        elapsed = time.time() - start
        self.assertLess(elapsed, 5.0, f"parser too slow: {elapsed}s")


class TestRegression(unittest.TestCase):
    def test_url_normalize_edge_cases(self):
        from utils.helpers import normalize_url
        # Various edge cases
        cases = [
            ("/path", "https://x.com", "https://x.com/path"),
            ("https://y.com/", "", "https://y.com/"),
            ("#hash", "https://x.com/page", "https://x.com/page"),
            ("", "", None),
        ]
        for href, base, expected in cases:
            self.assertEqual(normalize_url(href, base), expected)


if __name__ == "__main__":
    unittest.main()