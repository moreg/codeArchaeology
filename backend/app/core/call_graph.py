# -*- coding: utf-8 -*-
"""
app.core.call_graph — 调用图构建器
===================================
基于 NetworkX DiGraph 组装调用关系。
处理跨文件调用: import 追踪。
"""
import os
import re
from typing import List, Dict, Set, Tuple, Optional, Any

import networkx as nx


class CallGraphBuilder:
    """调用图构建器"""

    def __init__(self):
        self.graph = nx.DiGraph()
        self._imports: Dict[str, Dict[str, str]] = {}  # file -> {alias: module}
        self._function_index: Dict[str, Dict] = {}  # id -> function dict
        self._name_index: Dict[str, List[str]] = {}  # name -> [fid1, fid2, ...]

    def add_function(self, func: Dict[str, Any]):
        """添加一个函数节点"""
        fid = func.get("id")
        if not fid:
            return
        self.graph.add_node(fid, **func)
        self._function_index[fid] = func
        # 维护名称倒排索引
        name = func.get("name")
        if name:
            if name not in self._name_index:
                self._name_index[name] = []
            self._name_index[name].append(fid)

    def add_class(self, cls: Dict[str, Any]):
        """添加类节点"""
        cid = f"class_{cls.get('file_path')}_{cls.get('start_line')}_{cls.get('name')}"
        self.graph.add_node(cid, kind="class", **cls)

    def add_edge(self, source_id: str, target_id: str, call_type: str = "direct",
                 call_count: int = 1):
        """添加调用边"""
        if not self.graph.has_node(source_id) or not self.graph.has_node(target_id):
            return
        if self.graph.has_edge(source_id, target_id):
            data = self.graph[source_id][target_id]
            data["call_count"] = data.get("call_count", 1) + call_count
        else:
            self.graph.add_edge(source_id, target_id, call_type=call_type, call_count=call_count)

    def add_imports(self, file_path: str, imports: List[Dict[str, str]]):
        """添加 import 映射, 用于解析跨文件调用"""
        if file_path not in self._imports:
            self._imports[file_path] = {}
        for imp in imports:
            module = imp.get("module", "")
            alias = imp.get("alias") or imp.get("name") or module
            self._imports[file_path][alias] = module

    def resolve_call(self, caller_file: str, call_name: str) -> Optional[str]:
        """根据 import 解析调用, 返回被调用函数的 id"""
        if not call_name:
            return None
        # 直接匹配 (同名函数) - 使用倒排索引 O(1)
        fids = self._name_index.get(call_name, [])
        for fid in fids:
            func = self._function_index[fid]
            if func.get("file_path") != caller_file:
                return fid
        # 简化处理: 通过 module 映射
        imports = self._imports.get(caller_file, {})
        # call_name 可能是 "module.func" 形式
        parts = call_name.split(".")
        if len(parts) >= 2:
            module_alias = parts[0]
            func_name = parts[-1]
            if module_alias in imports:
                # 使用倒排索引查找
                fids = self._name_index.get(func_name, [])
                if fids:
                    return fids[0]
        return None

    def build_edges_from_functions(self, functions: List[Dict[str, Any]]):
        """根据函数中的 calls 字段构建边"""
        for func in functions:
            fid = func.get("id")
            if not fid:
                continue
            caller_file = func.get("file_path", "")
            for call_name in func.get("calls", []):
                target_id = self.resolve_call(caller_file, call_name)
                if target_id:
                    self.add_edge(fid, target_id, call_type="direct", call_count=1)

    def to_cytoscape_json(self) -> Dict[str, Any]:
        """转换为 Cytoscape.js 格式"""
        nodes = []
        for node_id, data in self.graph.nodes(data=True):
            nodes.append({
                "data": {
                    "id": node_id,
                    **data,
                }
            })
        edges = []
        for source, target, data in self.graph.edges(data=True):
            edges.append({
                "data": {
                    "source": source,
                    "target": target,
                    "label": data.get("call_type", "direct"),
                    "call_type": data.get("call_type", "direct"),
                    "call_count": data.get("call_count", 1),
                }
            })
        return {"nodes": nodes, "edges": edges}

    def to_graph_dict(self) -> Dict[str, Any]:
        """导出为可 JSON 序列化的字典"""
        nodes = []
        for node_id, data in self.graph.nodes(data=True):
            d = {"id": node_id}
            d.update({k: v for k, v in data.items() if isinstance(v, (str, int, float, bool, list, dict))})
            nodes.append(d)
        edges = []
        for source, target, data in self.graph.edges(data=True):
            edges.append({
                "source": source,
                "target": target,
                "call_type": data.get("call_type", "direct"),
                "call_count": data.get("call_count", 1),
            })
        return {"nodes": nodes, "edges": edges}

    def get_stats(self) -> Dict[str, Any]:
        """返回图统计信息"""
        return {
            "node_count": self.graph.number_of_nodes(),
            "edge_count": self.graph.number_of_edges(),
            "density": nx.density(self.graph),
            "is_dag": nx.is_directed_acyclic_graph(self.graph),
        }

    def find_cycles(self, max_length: int = 10) -> List[List[str]]:
        """找出图中的环"""
        try:
            cycles = list(nx.simple_cycles(self.graph))
            return [c[:max_length] for c in cycles[:20]]
        except Exception:
            return []

    def most_called_functions(self, n: int = 10) -> List[Tuple[str, int]]:
        """被调用最多的函数"""
        in_degrees = sorted(self.graph.in_degree(), key=lambda x: x[1], reverse=True)
        return in_degrees[:n]

    def most_calling_functions(self, n: int = 10) -> List[Tuple[str, int]]:
        """调用最多的函数"""
        out_degrees = sorted(self.graph.out_degree(), key=lambda x: x[1], reverse=True)
        return out_degrees[:n]


def build_call_graph(functions: List[Dict[str, Any]],
                     imports_map: Optional[Dict[str, List[Dict[str, str]]]] = None,
                     classes: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    """便捷接口: 构建调用图"""
    builder = CallGraphBuilder()
    for func in functions:
        builder.add_function(func)
    if classes:
        for cls in classes:
            builder.add_class(cls)
    if imports_map:
        for file_path, imps in imports_map.items():
            builder.add_imports(file_path, imps)
    builder.build_edges_from_functions(functions)
    return builder.to_graph_dict()


def extract_imports(source: str, language: str = "python") -> List[Dict[str, str]]:
    """从源码中提取 import (简化版, 不依赖 tree-sitter)"""
    imports = []
    if language == "python":
        for m in re.finditer(r"^\s*import\s+([\w.]+)(?:\s+as\s+(\w+))?", source, re.MULTILINE):
            imports.append({"module": m.group(1), "alias": m.group(2) or m.group(1).split(".")[-1]})
        for m in re.finditer(r"^\s*from\s+([\w.]+)\s+import\s+([^#\n]+)", source, re.MULTILINE):
            module = m.group(1)
            for name in m.group(2).split(","):
                name = name.strip().split(" as ")[0].strip()
                if name:
                    imports.append({"module": f"{module}.{name}", "alias": name})
    elif language in ("javascript", "typescript"):
        for m in re.finditer(r"^\s*import\s+(?:\{([^}]+)\}\s+from\s+)?['\"]([^'\"]+)['\"]", source, re.MULTILINE):
            module = m.group(2)
            names = m.group(1) or ""
            for name in names.split(","):
                name = name.strip()
                if name:
                    imports.append({"module": module, "alias": name})
    elif language == "java":
        for m in re.finditer(r"^\s*import\s+(?:static\s+)?([\w.]+(?:\.\*)?);", source, re.MULTILINE):
            module = m.group(1)
            name = module.split(".")[-1]
            imports.append({"module": module, "alias": name})
    return imports