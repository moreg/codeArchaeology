# -*- coding: utf-8 -*-
"""
parser package
==============
解析 HTML/JSON/正文提取。
"""
from .html_parser import HTMLParser, AdvancedHTMLParser
from .json_parser import JSONParser, JSONSchemaValidator
from .content_extractor import (
    ContentExtractor, ReadabilityExtractor, MarkdownExtractor,
)

__version__ = "0.3.0"
__all__ = [
    "HTMLParser", "AdvancedHTMLParser",
    "JSONParser", "JSONSchemaValidator",
    "ContentExtractor", "ReadabilityExtractor", "MarkdownExtractor",
]