# -*- coding: utf-8 -*-
"""
app.core.parser — 基于 tree-sitter 的多语言解析
================================================
- 提取函数定义、类定义、import、call
- 计算圈复杂度 (CC)
- 提取函数的元数据: 文件路径, 起始行, 结束行, 行数
"""
import os
import importlib
from typing import List, Dict, Optional, Any

from .scanner import EXT_TO_LANG
from ..utils.logger import get_logger

log = get_logger("core.parser")

try:
    import tree_sitter_python
    from tree_sitter import Language, Parser
    HAS_TREE_SITTER = True
except Exception:
    HAS_TREE_SITTER = False
    tree_sitter_python = None


LANG_MODULES = {
    "python": "tree_sitter_python",
    "javascript": "tree_sitter_javascript",
    "typescript": "tree_sitter_typescript",
    "java": "tree_sitter_java",
}


FUNCTION_NODE_TYPES = {
    "python": ["function_definition"],
    "javascript": ["function_declaration", "function_expression", "arrow_function", "method_definition"],
    "typescript": ["function_declaration", "function_expression", "arrow_function", "method_definition"],
    "java": ["method_declaration", "constructor_declaration"],
}

CLASS_NODE_TYPES = {
    "python": ["class_definition"],
    "javascript": ["class_declaration"],
    "typescript": ["class_declaration"],
    "java": ["class_declaration"],
}

CALL_NODE_TYPES = {
    "python": ["call"],
    "javascript": ["call_expression"],
    "typescript": ["call_expression"],
    "java": ["method_invocation"],
}

IMPORT_NODE_TYPES = {
    "python": ["import_statement", "import_from_statement"],
    "javascript": ["import_statement"],
    "typescript": ["import_statement"],
    "java": ["import_declaration"],
}

# 用于圈复杂度计算的分支节点类型
BRANCH_TYPES = {
    "if_statement", "for_statement", "while_statement", "do_statement",
    "case_statement", "switch_statement", "try_statement", "except_clause",
    "with_statement", "elif_clause", "else_clause",
    "conditional_expression", "and", "or", "not",
    "list_comprehension", "set_comprehension", "dictionary_comprehension",
    "generator_expression",
}


class FunctionInfo:
    """函数信息"""
    def __init__(self, name: str, file_path: str, start_line: int, end_line: int,
                 language: str = "python", class_name: Optional[str] = None):
        self.name = name
        self.file_path = file_path
        self.start_line = start_line
        self.end_line = end_line
        self.language = language
        self.class_name = class_name
        self.complexity = 1
        self.calls: List[str] = []
        self.parameters: List[str] = []

    @property
    def line_count(self) -> int:
        return max(0, self.end_line - self.start_line + 1)

    @property
    def id(self) -> str:
        return f"func_{self.file_path.replace(os.sep, '_').replace('.', '_')}_{self.start_line}_{self.name}"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "file_path": self.file_path,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "line_count": self.line_count,
            "language": self.language,
            "class_name": self.class_name,
            "complexity": self.complexity,
            "calls": self.calls,
            "parameters": self.parameters,
        }


class ClassInfo:
    """类信息"""
    def __init__(self, name: str, file_path: str, start_line: int, end_line: int,
                 language: str = "python"):
        self.name = name
        self.file_path = file_path
        self.start_line = start_line
        self.end_line = end_line
        self.language = language
        self.methods: List[FunctionInfo] = []

    @property
    def line_count(self) -> int:
        return max(0, self.end_line - self.start_line + 1)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "file_path": self.file_path,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "line_count": self.line_count,
            "language": self.language,
            "method_count": len(self.methods),
        }


class CodeParser:
    """代码解析器"""

    def __init__(self, language: str = "python"):
        self.language = language
        self._parser = None
        self._language_obj = None
        if HAS_TREE_SITTER:
            self._init_parser()

    def _init_parser(self):
        try:
            mod_name = LANG_MODULES.get(self.language)
            if not mod_name:
                return
            mod = importlib.import_module(mod_name)
            # 兼容 tree-sitter 0.21.0 / 0.21.3+ / 0.23.x 的 Language() 签名差异
            # 0.21.0: Language(path, name)  -- path 必须为 None 或动态库路径，name 是语言名
            # 0.21.3+ / 0.23.x: Language(ptr) -- 直接接受 ptr
            # 通过尝试两种调用方式自动选择
            try:
                # 0.23.x / 0.21.3+: Language(ptr)
                lang_obj = Language(mod.language())
            except (TypeError, FileNotFoundError, OSError):
                # 0.21.0: Language(name, ptr)  -- 第一个参数实际被当 path
                lang_obj = Language(self.language, mod.language())
            self._parser = Parser(lang_obj)
            self._language_obj = lang_obj
        except Exception as e:
            log.error("Parser init failed for %s: %s", self.language, e)
            self._parser = None

    def parse_source(self, source: str) -> Optional[Any]:
        """解析源码, 返回 AST"""
        if not self._parser:
            return None
        try:
            if isinstance(source, str):
                source_bytes = source.encode("utf-8", errors="ignore")
            else:
                source_bytes = source
            return self._parser.parse(source_bytes)
        except Exception as e:
            log.error("parse_source failed: %s", e)
            return None

    def _compute_complexity(self, node) -> int:
        """计算圈复杂度: 初始值 1, 遇到分支 +1"""
        cc = 1
        if not hasattr(node, "children"):
            return cc
        for child in node.children:
            t = child.type
            if t in BRANCH_TYPES:
                cc += 1
            elif t in ("boolean_operator",):
                cc += 1
            cc += self._compute_complexity(child)
        return cc

    def _walk_functions(self, node, file_path: str, source_lines: List[str],
                       class_name: Optional[str] = None,
                       functions: List[FunctionInfo] = None,
                       classes: List[ClassInfo] = None) -> tuple:
        """递归遍历 AST 提取函数"""
        if functions is None:
            functions = []
        if classes is None:
            classes = []

        func_types = FUNCTION_NODE_TYPES.get(self.language, ["function_definition"])
        class_types = CLASS_NODE_TYPES.get(self.language, ["class_definition"])

        if not hasattr(node, "children"):
            return functions, classes

        for child in node.children:
            if child.type in func_types:
                fi = self._extract_function(child, file_path, source_lines, class_name)
                if fi:
                    functions.append(fi)
            elif child.type in class_types:
                ci = self._extract_class(child, file_path, source_lines)
                if ci:
                    classes.append(ci)
                    # 提取类中的方法
                    sub_funcs, _ = self._walk_functions(
                        child, file_path, source_lines,
                        class_name=ci.name, functions=[], classes=[]
                    )
                    ci.methods.extend(sub_funcs)
                    functions.extend(sub_funcs)
            else:
                # 递归
                self._walk_functions(child, file_path, source_lines,
                                    class_name=class_name,
                                    functions=functions, classes=classes)

        return functions, classes

    def _extract_function(self, node, file_path: str, source_lines: List[str],
                          class_name: Optional[str]) -> Optional[FunctionInfo]:
        try:
            start_line = node.start_point[0] + 1
            end_line = node.end_point[0] + 1
            name = "anonymous"
            # 不同语言函数名提取
            if self.language == "python":
                name_node = node.child_by_field_name("name")
                if name_node:
                    name = source_lines[name_node.start_point[0]][name_node.start_point[1]:name_node.end_point[1]]
            elif self.language in ("javascript", "typescript", "java"):
                name_node = node.child_by_field_name("name")
                if name_node:
                    name = source_lines[name_node.start_point[0]][name_node.start_point[1]:name_node.end_point[1]]
            else:
                # 兜底: 取第一行第一个单词
                if start_line <= len(source_lines):
                    line = source_lines[start_line - 1]
                    name = line.strip().split("(", 1)[0].split("def ", 1)[-1].strip() or "anonymous"
            fi = FunctionInfo(
                name=name, file_path=file_path,
                start_line=start_line, end_line=end_line,
                language=self.language, class_name=class_name,
            )
            fi.complexity = self._compute_complexity(node)
            # 提取 calls
            fi.calls = self._extract_calls(node, source_lines)
            # 提取 parameters
            fi.parameters = self._extract_parameters(node, source_lines)
            return fi
        except Exception as e:
            return None

    def _extract_class(self, node, file_path: str, source_lines: List[str]) -> Optional[ClassInfo]:
        try:
            start_line = node.start_point[0] + 1
            end_line = node.end_point[0] + 1
            name = "anonymous"
            name_node = node.child_by_field_name("name")
            if name_node:
                name = source_lines[name_node.start_point[0]][name_node.start_point[1]:name_node.end_point[1]]
            return ClassInfo(
                name=name, file_path=file_path,
                start_line=start_line, end_line=end_line,
                language=self.language,
            )
        except Exception:
            return None

    def _extract_calls(self, node, source_lines: List[str]) -> List[str]:
        calls = []
        call_types = CALL_NODE_TYPES.get(self.language, ["call"])
        self._collect_calls(node, source_lines, call_types, calls)
        return list(set(calls))

    def _collect_calls(self, node, source_lines, call_types, out):
        if not hasattr(node, "children"):
            return
        for child in node.children:
            if child.type in call_types:
                fn_node = child.child_by_field_name("function")
                if fn_node is not None:
                    line_idx = fn_node.start_point[0]
                    col_start = fn_node.start_point[1]
                    col_end = fn_node.end_point[1]
                    if line_idx < len(source_lines):
                        text = source_lines[line_idx][col_start:col_end].strip()
                        if text:
                            out.append(text)
            self._collect_calls(child, source_lines, call_types, out)

    def _extract_parameters(self, node, source_lines: List[str]) -> List[str]:
        params = []
        params_node = node.child_by_field_name("parameters")
        if params_node is None:
            return params
        for child in params_node.children:
            if child.type in ("identifier", "typed_parameter", "default_parameter",
                             "typed_default_parameter", "dotted_name"):
                line_idx = child.start_point[0]
                col_start = child.start_point[1]
                col_end = child.end_point[1]
                if line_idx < len(source_lines):
                    text = source_lines[line_idx][col_start:col_end].strip()
                    # 去掉类型注解
                    text = text.split(":")[0].split("=")[0].strip()
                    if text and text != "self" and text != "cls":
                        params.append(text)
            elif child.type in ("list_splat", "dict_splat", "keyword_argument"):
                line_idx = child.start_point[0]
                col_start = child.start_point[1]
                col_end = child.end_point[1]
                if line_idx < len(source_lines):
                    text = source_lines[line_idx][col_start:col_end].strip()
                    if text:
                        params.append(text)
        return params

    def parse_file(self, file_path: str) -> Dict[str, Any]:
        """解析单个文件, 返回所有函数和类"""
        try:
            with open(file_path, "rb") as f:
                source_bytes = f.read()
        except Exception as e:
            return {"functions": [], "classes": [], "error": str(e)}
        source_text = source_bytes.decode("utf-8", errors="ignore")
        source_lines = source_text.splitlines()
        tree = self.parse_source(source_bytes)
        if tree is None:
            return {"functions": [], "classes": [], "error": "parser not available"}
        functions, classes = self._walk_functions(tree.root_node, file_path, source_lines)
        return {
            "functions": [f.to_dict() for f in functions],
            "classes": [c.to_dict() for c in classes],
        }


def parse_file(file_path: str, language: Optional[str] = None) -> Dict[str, Any]:
    """便捷接口: 解析单个文件, 自动推断语言"""
    if language is None:
        ext = os.path.splitext(file_path)[1]
        language = EXT_TO_LANG.get(ext.lower(), "python")
    parser = CodeParser(language)
    return parser.parse_file(file_path)


def compute_complexity(source: str, language: str = "python") -> int:
    """计算整个文件的圈复杂度之和"""
    parser = CodeParser(language)
    tree = parser.parse_source(source)
    if tree is None:
        return 1
    return parser._compute_complexity(tree.root_node)