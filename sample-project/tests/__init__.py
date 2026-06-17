# -*- coding: utf-8 -*-
"""
tests package
=============
补充一些性能测试和回归测试。
"""
import unittest
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 一些常量
TEST_DB_PATH = ":memory:"
TEST_TIMEOUT = 5
TEST_SEEDS = ["https://test1.com", "https://test2.com"]


def setup_test_env():
    """设置测试环境"""
    os.environ["CRAWLER_DEBUG"] = "1"
    os.environ["CRAWLER_VERBOSE"] = "1"


def teardown_test_env():
    """清理测试环境"""
    for k in ("CRAWLER_DEBUG", "CRAWLER_VERBOSE"):
        os.environ.pop(k, None)


def run_all_tests():
    """运行所有测试"""
    setup_test_env()
    loader = unittest.TestLoader()
    start_dir = os.path.dirname(os.path.abspath(__file__))
    suite = loader.discover(start_dir, pattern="test_*.py")
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    teardown_test_env()
    return result


if __name__ == "__main__":
    run_all_tests()