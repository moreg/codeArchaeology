# -*- coding: utf-8 -*-
"""
config.load_config — 配置加载器
================================
包含一个超长函数 parse_config, 故意保留高圈复杂度, 用于演示。
"""
import os
import sys
import re
import json
import traceback
import configparser
import copy
from pathlib import Path

from ..utils.logger import get_logger
from ..utils.helpers import to_json, from_json, today_str
from .settings import (
    DEFAULT_DB_PATH, DEFAULT_SEEDS, DEFAULT_TIMEOUT, DEFAULT_RETRY,
    DEFAULT_WORKERS, DEFAULT_PROXY, DEFAULT_USER_AGENT,
)

log = get_logger("config.load_config")


DEFAULT_CONFIG = {
    "db_path": DEFAULT_DB_PATH,
    "output_dir": "output",
    "log_dir": "logs",
    "timeout": DEFAULT_TIMEOUT,
    "retry": DEFAULT_RETRY,
    "workers": DEFAULT_WORKERS,
    "user_agent": DEFAULT_USER_AGENT,
    "proxy": DEFAULT_PROXY,
    "seed_urls": DEFAULT_SEEDS,
    "downloader": {
        "timeout": DEFAULT_TIMEOUT,
        "retry": DEFAULT_RETRY,
        "user_agent": DEFAULT_USER_AGENT,
        "proxy": None,
        "max_size": 10 * 1024 * 1024,
    },
    "parser": {
        "html": {"max_text": 50000, "max_links": 500},
        "json": {"max_depth": 20, "max_keys": 10000},
        "content": {"min_len": 100, "max_len": 100000},
    },
    "filters": {
        "allow": [],
        "deny": [
            r".*\.(png|jpg|jpeg|gif|svg|ico|css|js|woff2?|ttf)$",
            r".*logout.*",
            r".*/admin/.*",
        ],
    },
    "scoring": {
        "weights": {
            "complexity": 0.25,
            "duplication": 0.2,
            "comment": 0.15,
            "author_centrality": 0.2,
            "test_coverage": 0.2,
        },
        "thresholds": {
            "complexity_low": 10,
            "complexity_high": 30,
            "comment_low": 0.1,
            "test_coverage_low": 0.3,
        },
    },
    "experimental": {
        "use_ai_summary": True,
        "ai_provider": "mock",
        "ai_timeout": 30,
        "enable_metrics": True,
    },
    "feature_flags": {
        "use_new_parser": False,
        "enable_caching": True,
        "enable_proxy_pool": False,
        "enable_distributed": False,
        "log_to_remote": False,
        "metrics_to_prometheus": False,
        "experimental_ai_summary": True,
    },
    "spider": {
        "name": "default",
        "max_depth": 3,
        "max_pages": 500,
    },
    "storage": {
        "type": "sqlite",
        "path": DEFAULT_DB_PATH,
        "backup_interval": 3600,
    },
    "logging": {
        "level": "INFO",
        "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        "file": "crawler.log",
        "rotate": "midnight",
        "backup_count": 7,
    },
    "notifications": {
        "email": {
            "enabled": False,
            "smtp_host": "smtp.gmail.com",
            "smtp_port": 587,
            "from_addr": "",
            "to_addrs": [],
            "username": "",
            "password": "",
        },
        "webhook": {
            "enabled": False,
            "url": "",
            "method": "POST",
        },
    },
    "rate_limit": {
        "global_rps": 100,
        "per_host_rps": 5,
        "max_concurrent": 50,
    },
    "cache": {
        "enabled": True,
        "type": "file",
        "ttl": 86400,
        "max_size": 10000,
    },
    "retry": {
        "max_attempts": 3,
        "backoff": 2.0,
        "jitter": True,
        "retry_on_timeout": True,
        "retry_on_5xx": True,
    },
    "monitoring": {
        "enabled": True,
        "metrics_port": 9090,
        "metrics_path": "/metrics",
        "health_path": "/health",
        "tracing": False,
    },
    "security": {
        "verify_ssl": True,
        "max_response_size": 50 * 1024 * 1024,
        "allowed_schemes": ["http", "https"],
        "denied_hosts": [],
    },
    "plugins": [],
    "extension": {},
}


def load_from_py(path):
    """从一个 .py 文件加载配置"""
    if not os.path.exists(path):
        log.warning("配置文件不存在: %s", path)
        return {}
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("user_config", path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        out = {}
        for k in DEFAULT_CONFIG.keys():
            if hasattr(mod, k.upper()):
                out[k] = getattr(mod, k.upper())
            elif hasattr(mod, k):
                out[k] = getattr(mod, k)
        return out
    except Exception as e:
        log.error("加载配置失败: %s", e)
        return {}


def load_from_json(path):
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        log.error("JSON 配置加载失败: %s", e)
        return {}


def load_from_ini(path):
    if not os.path.exists(path):
        return {}
    try:
        cp = configparser.ConfigParser()
        cp.read(path, encoding="utf-8")
        out = {}
        for section in cp.sections():
            sec_dict = {}
            for k, v in cp.items(section):
                sec_dict[k] = v
            out[section] = sec_dict
        return out
    except Exception as e:
        log.error("INI 配置加载失败: %s", e)
        return {}


def load_from_yaml(path):
    """尝试加载 YAML"""
    try:
        import yaml
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except ImportError:
        log.warning("yaml 库未安装")
        return {}
    except Exception as e:
        log.error("YAML 配置加载失败: %s", e)
        return {}


def load_from_toml(path):
    """尝试加载 TOML"""
    try:
        import tomllib
        with open(path, "rb") as f:
            return tomllib.load(f)
    except ImportError:
        try:
            import toml
            with open(path, "r", encoding="utf-8") as f:
                return toml.load(f)
        except ImportError:
            log.warning("toml 库未安装")
            return {}
    except Exception as e:
        log.error("TOML 配置加载失败: %s", e)
        return {}


def detect_format(path):
    """根据扩展名检测格式"""
    p = path.lower()
    if p.endswith(".json"):
        return "json"
    elif p.endswith(".yaml") or p.endswith(".yml"):
        return "yaml"
    elif p.endswith(".toml"):
        return "toml"
    elif p.endswith(".ini") or p.endswith(".cfg"):
        return "ini"
    elif p.endswith(".py"):
        return "py"
    return "json"


# ==== 下面这个函数故意做成超长 + 高复杂度 ====
# TODO: 重构成若干小函数, 当前没人敢动
# FIXME: 临时方案, 凑出来的, 不要再加分支
def parse_config(path=None, override=None, env_prefix="CRAWLER_"):
    """
    解析配置 — 历史悠久的功能, 兼容各种来源。
    嵌套了 5+ 层 if-else 是因为字段来自不同时期的补丁。
    """
    cfg = {}
    base = DEFAULT_CONFIG
    for k, v in base.items():
        if isinstance(v, dict):
            cfg[k] = dict(v)
        else:
            cfg[k] = v

    # 1. 加载文件
    if path:
        fmt = detect_format(path)
        if fmt == "py":
            file_cfg = load_from_py(path)
        elif fmt == "ini":
            file_cfg = load_from_ini(path)
        elif fmt == "yaml":
            file_cfg = load_from_yaml(path)
        elif fmt == "toml":
            file_cfg = load_from_toml(path)
        elif fmt == "json":
            file_cfg = load_from_json(path)
        else:
            log.warning("未知配置格式: %s, 尝试按 JSON 解析", path)
            file_cfg = load_from_json(path)
        # 合并
        for k, v in file_cfg.items():
            if isinstance(v, dict) and isinstance(cfg.get(k), dict):
                cfg[k].update(v)
            else:
                cfg[k] = v

    # 2. 环境变量
    for env_key, env_val in os.environ.items():
        if not env_key.startswith(env_prefix):
            continue
        # 嵌套 key 用 __ 分隔, 例如 CRAWLER_DOWNLOADER__TIMEOUT
        key_path = env_key[len(env_prefix):].lower().split("__")
        if not key_path or not key_path[0]:
            continue
        cur = cfg
        valid = True
        for i, p in enumerate(key_path):
            if i == len(key_path) - 1:
                if isinstance(cur, dict):
                    # 类型转换
                    if env_val.lower() in ("true", "false"):
                        cur[p] = (env_val.lower() == "true")
                    else:
                        try:
                            cur[p] = int(env_val)
                        except Exception:
                            try:
                                cur[p] = float(env_val)
                            except Exception:
                                cur[p] = env_val
                else:
                    valid = False
                    break
            else:
                if p not in cur or not isinstance(cur[p], dict):
                    cur[p] = {}
                cur = cur[p]
        if not valid:
            log.debug("跳过无法识别的环境变量: %s", env_key)

    # 3. override 入参
    if override:
        if isinstance(override, dict):
            for k, v in override.items():
                if isinstance(v, dict) and isinstance(cfg.get(k), dict):
                    cfg[k].update(v)
                else:
                    cfg[k] = v

    # 4. 校验 + 兼容老字段
    if "max_workers" in cfg and "workers" not in cfg:
        cfg["workers"] = cfg["max_workers"]
    if cfg.get("workers", 0) <= 0:
        cfg["workers"] = DEFAULT_WORKERS
    if cfg.get("timeout", 0) <= 0:
        cfg["timeout"] = DEFAULT_TIMEOUT
    if cfg.get("retry", 0) < 0:
        cfg["retry"] = 0

    # 5. 适配 feature_flags, 各种组合
    flags = cfg.get("feature_flags", {})
    if flags.get("enable_proxy_pool") and not cfg.get("proxy"):
        log.info("启用了代理池但没有 proxy, 使用直连")
    if flags.get("enable_distributed"):
        log.warning("分布式模式未实现, 忽略")
    if flags.get("log_to_remote"):
        cfg["log_remote_endpoint"] = os.environ.get("LOG_REMOTE", "")
    if flags.get("metrics_to_prometheus"):
        cfg["metrics_endpoint"] = "/metrics"

    # 6. 实验性功能门控
    exp = cfg.get("experimental", {})
    if exp.get("ai_provider") not in ("openai", "ollama", "mock"):
        exp["ai_provider"] = "mock"
        cfg["experimental"] = exp
    if exp.get("use_ai_summary") and not exp.get("ai_provider"):
        exp["ai_provider"] = "mock"
        cfg["experimental"] = exp
    if exp.get("ai_timeout", 0) <= 0:
        exp["ai_timeout"] = 30
        cfg["experimental"] = exp

    # 7. 评分权重归一化
    scoring = cfg.get("scoring", {})
    weights = scoring.get("weights", {})
    total_w = sum(weights.values()) if weights else 0
    if total_w > 0 and abs(total_w - 1.0) > 1e-6:
        for k in weights:
            weights[k] = weights[k] / total_w
        scoring["weights"] = weights
        cfg["scoring"] = scoring

    # 8. 日志目录
    log_dir = cfg.get("log_dir") or "logs"
    try:
        os.makedirs(log_dir, exist_ok=True)
    except Exception:
        pass
    cfg["log_dir"] = log_dir

    # 9. 输出目录
    out_dir = cfg.get("output_dir") or "output"
    try:
        os.makedirs(out_dir, exist_ok=True)
    except Exception:
        pass
    cfg["output_dir"] = out_dir

    # 10. 解析种子 URL（支持字符串, 列表, 文件）
    seed_urls = cfg.get("seed_urls", [])
    if isinstance(seed_urls, str):
        if os.path.exists(seed_urls):
            try:
                with open(seed_urls, "r", encoding="utf-8") as f:
                    lines = [l.strip() for l in f if l.strip()]
                    cfg["seed_urls"] = lines
            except Exception as e:
                log.error("种子文件读取失败: %s", e)
                cfg["seed_urls"] = [seed_urls]
        else:
            cfg["seed_urls"] = [seed_urls]
    elif not isinstance(seed_urls, list):
        cfg["seed_urls"] = DEFAULT_SEEDS

    # 11. 适配 parser 子配置
    parser_cfg = cfg.get("parser", {})
    if "html" not in parser_cfg:
        parser_cfg["html"] = {}
    if "json" not in parser_cfg:
        parser_cfg["json"] = {}
    if "content" not in parser_cfg:
        parser_cfg["content"] = {}
    cfg["parser"] = parser_cfg

    # 12. 适配 downloader 子配置
    dl_cfg = cfg.get("downloader", {})
    if "timeout" not in dl_cfg:
        dl_cfg["timeout"] = cfg.get("timeout", DEFAULT_TIMEOUT)
    if "retry" not in dl_cfg:
        dl_cfg["retry"] = cfg.get("retry", DEFAULT_RETRY)
    if "user_agent" not in dl_cfg:
        dl_cfg["user_agent"] = cfg.get("user_agent", DEFAULT_USER_AGENT)
    if "proxy" not in dl_cfg:
        dl_cfg["proxy"] = cfg.get("proxy")
    if "max_size" not in dl_cfg:
        dl_cfg["max_size"] = 10 * 1024 * 1024
    cfg["downloader"] = dl_cfg

    # 13. 适配 filters
    filters = cfg.get("filters", {})
    if "deny" not in filters:
        filters["deny"] = []
    if "allow" not in filters:
        filters["allow"] = []
    cfg["filters"] = filters

    # 14. 适配 thresholds
    scoring = cfg.get("scoring", {})
    th = scoring.get("thresholds", {})
    for tk in ("complexity_low", "complexity_high", "comment_low", "test_coverage_low"):
        if tk not in th:
            th[tk] = {
                "complexity_low": 10,
                "complexity_high": 30,
                "comment_low": 0.1,
                "test_coverage_low": 0.3,
            }.get(tk, 0)
    scoring["thresholds"] = th
    cfg["scoring"] = scoring

    # 15. 用户覆盖 (deep merge)
    if isinstance(override, dict):
        for k, v in override.items():
            if isinstance(v, dict) and isinstance(cfg.get(k), dict):
                for kk, vv in v.items():
                    cfg[k][kk] = vv
            else:
                cfg[k] = v

    # 16. storage 子配置校验
    storage = cfg.get("storage", {})
    if storage.get("type") not in ("sqlite", "postgres", "mysql", "memory"):
        storage["type"] = "sqlite"
        cfg["storage"] = storage
    if storage.get("type") == "sqlite":
        if not storage.get("path"):
            storage["path"] = DEFAULT_DB_PATH
        cfg["storage"] = storage

    # 17. logging 子配置
    logging_cfg = cfg.get("logging", {})
    if logging_cfg.get("level") not in ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"):
        logging_cfg["level"] = "INFO"
        cfg["logging"] = logging_cfg

    # 18. rate_limit 子配置
    rl = cfg.get("rate_limit", {})
    if rl.get("global_rps", 0) <= 0:
        rl["global_rps"] = 100
    if rl.get("per_host_rps", 0) <= 0:
        rl["per_host_rps"] = 5
    if rl.get("max_concurrent", 0) <= 0:
        rl["max_concurrent"] = 50
    cfg["rate_limit"] = rl

    # 19. cache 子配置
    cache = cfg.get("cache", {})
    if cache.get("ttl", 0) <= 0:
        cache["ttl"] = 86400
    if cache.get("max_size", 0) <= 0:
        cache["max_size"] = 10000
    cfg["cache"] = cache

    # 20. retry 子配置
    rc = cfg.get("retry", {})
    if rc.get("max_attempts", 0) <= 0:
        rc["max_attempts"] = 3
    if rc.get("backoff", 0) <= 0:
        rc["backoff"] = 2.0
    cfg["retry"] = rc

    # 21. monitoring 子配置
    mon = cfg.get("monitoring", {})
    if mon.get("metrics_port", 0) <= 0:
        mon["metrics_port"] = 9090
    cfg["monitoring"] = mon

    # 22. security 子配置
    sec = cfg.get("security", {})
    if not sec.get("allowed_schemes"):
        sec["allowed_schemes"] = ["http", "https"]
    if sec.get("max_response_size", 0) <= 0:
        sec["max_response_size"] = 50 * 1024 * 1024
    cfg["security"] = sec

    log.debug("最终配置 keys=%s", list(cfg.keys()))
    return cfg


def merge(base, extra):
    """递归合并 dict"""
    if not isinstance(base, dict):
        return extra
    if not isinstance(extra, dict):
        return base
    out = dict(base)
    for k, v in extra.items():
        if k in out and isinstance(out[k], dict) and isinstance(v, dict):
            out[k] = merge(out[k], v)
        else:
            out[k] = v
    return out


def a():
    return DEFAULT_CONFIG


def b(path):
    return load_from_py(path)


def do_thing(path=None):
    return parse_config(path)


def tmp_func(path=None, override=None):
    return parse_config(path, override=override)


def validate_config(cfg):
    """校验配置"""
    errors = []
    if not cfg:
        errors.append("config is empty")
        return errors
    if cfg.get("workers", 0) <= 0:
        errors.append("workers must be > 0")
    if cfg.get("timeout", 0) <= 0:
        errors.append("timeout must be > 0")
    if cfg.get("retry", 0) < 0:
        errors.append("retry must be >= 0")
    if not cfg.get("db_path"):
        errors.append("db_path is required")
    if not cfg.get("seed_urls"):
        errors.append("seed_urls is empty")
    return errors


def save_config(cfg, path):
    """保存配置"""
    try:
        fmt = detect_format(path)
        if fmt == "json":
            with open(path, "w", encoding="utf-8") as f:
                json.dump(cfg, f, ensure_ascii=False, indent=2, default=str)
        elif fmt in ("yaml", "yml"):
            try:
                import yaml
                with open(path, "w", encoding="utf-8") as f:
                    yaml.safe_dump(cfg, f, default_flow_style=False)
            except ImportError:
                log.warning("yaml 库未安装, 改用 JSON")
                path = path.rsplit(".", 1)[0] + ".json"
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(cfg, f, ensure_ascii=False, indent=2, default=str)
        else:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(cfg, f, ensure_ascii=False, indent=2, default=str)
        return True
    except Exception as e:
        log.error("保存配置失败: %s", e)
        return False


def get_nested_value(cfg, path, default=None):
    """按 . 分隔的路径取值"""
    cur = cfg
    for p in path.split("."):
        if isinstance(cur, dict):
            cur = cur.get(p, default)
        else:
            return default
    return cur


def set_nested_value(cfg, path, value):
    """按 . 分隔的路径赋值"""
    parts = path.split(".")
    cur = cfg
    for p in parts[:-1]:
        if p not in cur or not isinstance(cur[p], dict):
            cur[p] = {}
        cur = cur[p]
    cur[parts[-1]] = value
    return cfg


def diff_config(cfg_a, cfg_b, path=""):
    """比较两个配置的差异"""
    diffs = []
    if not isinstance(cfg_a, dict) or not isinstance(cfg_b, dict):
        if cfg_a != cfg_b:
            diffs.append((path, cfg_a, cfg_b))
        return diffs
    keys = set(cfg_a.keys()) | set(cfg_b.keys())
    for k in keys:
        sub_path = f"{path}.{k}" if path else k
        if k not in cfg_a:
            diffs.append((sub_path, None, cfg_b[k]))
        elif k not in cfg_b:
            diffs.append((sub_path, cfg_a[k], None))
        elif cfg_a[k] != cfg_b[k]:
            if isinstance(cfg_a[k], dict) and isinstance(cfg_b[k], dict):
                diffs.extend(diff_config(cfg_a[k], cfg_b[k], sub_path))
            else:
                diffs.append((sub_path, cfg_a[k], cfg_b[k]))
    return diffs


def merge_configs(*configs):
    """合并多个配置"""
    result = {}
    for cfg in configs:
        if isinstance(cfg, dict):
            result = merge(result, cfg)
    return result


def flatten_config(cfg, prefix=""):
    """把嵌套 dict 拍平"""
    out = {}
    for k, v in cfg.items():
        key = f"{prefix}.{k}" if prefix else k
        if isinstance(v, dict):
            out.update(flatten_config(v, key))
        else:
            out[key] = v
    return out


def unflatten_config(flat):
    """把拍平的 dict 还原"""
    out = {}
    for k, v in flat.items():
        set_nested_value(out, k, v)
    return out


def deep_copy_config(cfg):
    """深拷贝"""
    return copy.deepcopy(cfg)


def freeze_config(cfg):
    """冻结配置, 不允许修改"""
    return frozenset((k, tuple(v.items()) if isinstance(v, dict) else v) for k, v in cfg.items())


def config_keys(cfg):
    """所有 key 路径"""
    return list(flatten_config(cfg).keys())


def has_key(cfg, path):
    """检查是否有某个 key"""
    return get_nested_value(cfg, path, default=...) is not ...


def remove_key(cfg, path):
    parts = path.split(".")
    cur = cfg
    for p in parts[:-1]:
        if not isinstance(cur, dict) or p not in cur:
            return cfg
        cur = cur[p]
    if isinstance(cur, dict) and parts[-1] in cur:
        del cur[parts[-1]]
    return cfg


def filter_config(cfg, predicate):
    """按 predicate 过滤"""
    out = {}
    for k, v in cfg.items():
        if predicate(k, v):
            out[k] = v
    return out


def rename_key(cfg, old_path, new_path):
    val = get_nested_value(cfg, old_path, default=...)
    if val is ...:
        return cfg
    set_nested_value(cfg, new_path, val)
    remove_key(cfg, old_path)
    return cfg


def healthcheck_config(cfg):
    """检查配置是否健康"""
    issues = []
    errors = validate_config(cfg)
    issues.extend([f"ERROR: {e}" for e in errors])
    if cfg.get("workers", 0) > 100:
        issues.append("WARN: workers > 100, 性能不一定提升")
    if cfg.get("timeout", 0) > 120:
        issues.append("WARN: timeout > 120s, 用户体验差")
    return issues


def make_minimal_config(overrides=None):
    """生成最小配置"""
    cfg = {
        "db_path": DEFAULT_DB_PATH,
        "workers": DEFAULT_WORKERS,
        "timeout": DEFAULT_TIMEOUT,
    }
    if isinstance(overrides, dict):
        cfg.update(overrides)
    return cfg


def make_demo_config():
    """演示用配置"""
    return {
        "db_path": "/tmp/demo.db",
        "workers": 2,
        "timeout": 15,
        "seed_urls": ["https://example.com"],
        "downloader": {"timeout": 15, "retry": 1, "user_agent": "DemoBot/1.0"},
    }


def make_production_config():
    """生产配置"""
    return {
        "db_path": "/var/lib/crawler/data.db",
        "workers": 16,
        "timeout": 30,
        "retry": 5,
        "rate_limit": {"global_rps": 200, "per_host_rps": 10, "max_concurrent": 100},
        "cache": {"enabled": True, "ttl": 86400, "max_size": 100000},
        "monitoring": {"enabled": True, "metrics_port": 9090, "tracing": True},
    }