# -*- coding: utf-8 -*-
"""
config.settings — 默认配置
===========================
"""
import os
import time

DEFAULT_DB_PATH = os.environ.get(
    "CRAWLER_DB_PATH",
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "crawler.db"),
)
DEFAULT_OUTPUT_DIR = os.environ.get(
    "CRAWLER_OUTPUT_DIR",
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "output"),
)
DEFAULT_LOG_DIR = os.environ.get(
    "CRAWLER_LOG_DIR",
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs"),
)
DEFAULT_USER_AGENT = "Mozilla/5.0 (compatible; LegacySpider/1.0)"
DEFAULT_TIMEOUT = 30
DEFAULT_RETRY = 3
DEFAULT_WORKERS = 4
DEFAULT_PROXY = os.environ.get("CRAWLER_PROXY", None)

# 种子 URL
DEFAULT_SEEDS = [
    "https://example.com",
    "https://example.org",
    "https://example.net",
]

# 文件类型白名单
EXT_TO_LANG = {
    ".py": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".java": "java",
    ".go": "go",
    ".rb": "ruby",
    ".cpp": "cpp",
    ".c": "c",
    ".cs": "csharp",
    ".php": "php",
    ".swift": "swift",
    ".kt": "kotlin",
    ".rs": "rust",
}

LANG_TO_TREE_SITTER = {
    "python": "python",
    "javascript": "javascript",
    "typescript": "typescript",
    "java": "java",
    "go": "go",
    "ruby": "ruby",
}

LANGUAGE_LIST = ["python", "javascript", "typescript", "java", "go", "ruby"]

DEFAULT_MAX_DEPTH = 3
DEFAULT_MAX_PAGES = 500
DEFAULT_MAX_FILE_SIZE = 10 * 1024 * 1024
DEFAULT_MAX_DIR_SIZE = 100 * 1024 * 1024

# 评分默认阈值
SCORE_THRESHOLDS = {
    "excellent": 90,
    "good": 70,
    "fair": 50,
    "warning": 30,
    "danger": 0,
}

RATING_COLORS = {
    "excellent": "#10B981",
    "good": "#84CC16",
    "fair": "#EAB308",
    "warning": "#F97316",
    "danger": "#EF4444",
}

RATING_LABELS = {
    "excellent": "考古宝藏",
    "good": "略有灰尘",
    "fair": "需要清理",
    "warning": "屎山警告",
    "danger": "危险遗址",
}

# 颜色模式
COLOR_MODES = ["complexity", "frequency", "author", "test_coverage"]

# 调用类型
CALL_TYPES = ["direct", "indirect", "callback", "dataflow"]


def a():
    return DEFAULT_DB_PATH


def b():
    return DEFAULT_SEEDS


def do_thing():
    return EXT_TO_LANG


def tmp_func(name):
    return name in EXT_TO_LANG


def get_rating(score):
    if score >= SCORE_THRESHOLDS["excellent"]:
        return "excellent", RATING_COLORS["excellent"], RATING_LABELS["excellent"]
    elif score >= SCORE_THRESHOLDS["good"]:
        return "good", RATING_COLORS["good"], RATING_LABELS["good"]
    elif score >= SCORE_THRESHOLDS["fair"]:
        return "fair", RATING_COLORS["fair"], RATING_LABELS["fair"]
    elif score >= SCORE_THRESHOLDS["warning"]:
        return "warning", RATING_COLORS["warning"], RATING_LABELS["warning"]
    else:
        return "danger", RATING_COLORS["danger"], RATING_LABELS["danger"]


def get_lang_by_ext(ext):
    return EXT_TO_LANG.get(ext.lower())


def is_supported_lang(lang):
    return lang in LANG_TO_TREE_SITTER


def tree_sitter_name(lang):
    return LANG_TO_TREE_SITTER.get(lang)


def list_supported_langs():
    return list(LANG_TO_TREE_SITTER.keys())


def list_supported_exts():
    return list(EXT_TO_LANG.keys())


def make_default_config():
    return {
        "db_path": DEFAULT_DB_PATH,
        "output_dir": DEFAULT_OUTPUT_DIR,
        "log_dir": DEFAULT_LOG_DIR,
        "user_agent": DEFAULT_USER_AGENT,
        "timeout": DEFAULT_TIMEOUT,
        "retry": DEFAULT_RETRY,
        "workers": DEFAULT_WORKERS,
        "proxy": DEFAULT_PROXY,
        "max_depth": DEFAULT_MAX_DEPTH,
        "max_pages": DEFAULT_MAX_PAGES,
        "max_file_size": DEFAULT_MAX_FILE_SIZE,
        "seed_urls": list(DEFAULT_SEEDS),
    }


def healthcheck_settings():
    return {
        "ok": True,
        "db_path": DEFAULT_DB_PATH,
        "workers": DEFAULT_WORKERS,
        "ts": time.time(),
    }


def log_dir_path():
    return DEFAULT_LOG_DIR


def output_dir_path():
    return DEFAULT_OUTPUT_DIR


def data_dir_path():
    return os.path.dirname(DEFAULT_DB_PATH)


def make_dir_if_needed(path):
    if not path:
        return False
    try:
        os.makedirs(path, exist_ok=True)
        return True
    except Exception:
        return False


def all_dirs():
    return {
        "data": data_dir_path(),
        "output": output_dir_path(),
        "log": log_dir_path(),
    }


def ensure_all_dirs():
    for d in all_dirs().values():
        make_dir_if_needed(d)


def env_var_or_default(env_key, default):
    return os.environ.get(env_key, default)


def max_workers_for_env():
    return env_var_or_default("CRAWLER_MAX_WORKERS", str(DEFAULT_WORKERS))


def debug_mode():
    return os.environ.get("CRAWLER_DEBUG", "").lower() in ("1", "true", "yes")


def verbose_mode():
    return os.environ.get("CRAWLER_VERBOSE", "").lower() in ("1", "true", "yes")


def proxy_url():
    return DEFAULT_PROXY


def set_proxy(url):
    global DEFAULT_PROXY
    DEFAULT_PROXY = url


def user_agent():
    return DEFAULT_USER_AGENT


def custom_user_agent(name, version="1.0"):
    return f"{name}/{version} (compatible; LegacySpider)"


def spider_user_agent(spider_name):
    return custom_user_agent(spider_name)


def bot_user_agent(bot_name="crawler"):
    return f"{bot_name}/1.0 (+https://example.com/bot)"


def curl_user_agent():
    return "curl/7.68.0"


def chrome_user_agent():
    return "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"


def firefox_user_agent():
    return "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0"


def safari_user_agent():
    return "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15"