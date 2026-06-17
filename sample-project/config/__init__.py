# -*- coding: utf-8 -*-
"""
config package
==============
配置加载与默认值。
"""
from .settings import (
    DEFAULT_DB_PATH, DEFAULT_OUTPUT_DIR, DEFAULT_LOG_DIR,
    DEFAULT_USER_AGENT, DEFAULT_TIMEOUT, DEFAULT_RETRY, DEFAULT_WORKERS,
    DEFAULT_SEEDS, EXT_TO_LANG, LANG_TO_TREE_SITTER,
    SCORE_THRESHOLDS, RATING_COLORS, RATING_LABELS,
    COLOR_MODES, CALL_TYPES,
    get_rating,
)
from .load_config import (
    parse_config, merge, validate_config, save_config,
    load_from_py, load_from_json, load_from_ini, load_from_yaml,
    load_from_toml, detect_format,
    DEFAULT_CONFIG,
)

__version__ = "0.2.0"
__all__ = [
    "parse_config", "merge", "validate_config", "save_config",
    "DEFAULT_DB_PATH", "DEFAULT_SEEDS", "EXT_TO_LANG",
    "get_rating",
]