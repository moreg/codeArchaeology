# -*- coding: utf-8 -*-
"""
app.utils.logger — 简易日志
"""
import logging
import sys

_loggers = {}


def get_logger(name: str = "app"):
    if name in _loggers:
        return _loggers[name]
    logger = logging.getLogger(name)
    if not logger.handlers:
        h = logging.StreamHandler(sys.stdout)
        h.setFormatter(logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        ))
        logger.addHandler(h)
        logger.setLevel(logging.INFO)
    _loggers[name] = logger
    return logger