# -*- coding: utf-8 -*-
"""
app.core.scoring — 屎山评分引擎
=================================
5 个维度评分 (0-100), 加权平均得总分。
- complexity: 基于平均圈复杂度反向投影
- duplication: 基于重复代码片段占比反向
- comment: 有注释行数 / 总行数 * 100
- author_centrality: 基尼系数反向 (作者分布越均匀分越高)
- test_coverage: 被测试文件覆盖的代码行 / 总代码行 * 100
"""
import os
import re
from typing import List, Dict, Optional, Any
from collections import Counter


RATING_THRESHOLDS = [
    (90, "excellent", "#10B981", "考古宝藏"),
    (70, "good", "#84CC16", "略有灰尘"),
    (50, "fair", "#EAB308", "需要清理"),
    (30, "warning", "#F44336", "屎山警告"),
    (0, "danger", "#B71C1C", "危险遗址"),
]


def get_rating(score: float):
    """根据分数返回评级"""
    for threshold, key, color, label in RATING_THRESHOLDS:
        if score >= threshold:
            return key, color, label
    return "danger", "#B71C1C", "危险遗址"


def score_complexity(functions: List[Dict[str, Any]]) -> float:
    """圈复杂度评分: CC<=10 给 100, 每 +5 减 10, 最低 0"""
    if not functions:
        return 100.0
    ccs = [f.get("complexity", 1) for f in functions]
    avg = sum(ccs) / len(ccs)
    if avg <= 10:
        return 100.0
    penalty = (avg - 10) / 5 * 10
    return max(0.0, 100.0 - penalty)


def score_duplication(source_by_file: Dict[str, str]) -> float:
    """重复代码评分: 计算 50 字符片段重复率, 反向投影"""
    if not source_by_file:
        return 100.0
    chunks = []
    CHUNK_LEN = 50
    for content in source_by_file.values():
        text = re.sub(r"\s+", "", content or "")
        for i in range(0, max(0, len(text) - CHUNK_LEN), CHUNK_LEN):
            chunks.append(text[i:i + CHUNK_LEN])
    if not chunks:
        return 100.0
    counter = Counter(chunks)
    total = len(chunks)
    dup = sum(c - 1 for c in counter.values() if c > 1)
    dup_rate = dup / total if total else 0
    return max(0.0, 100.0 - dup_rate * 200)


def score_comment(source_by_file: Dict[str, str]) -> float:
    """注释覆盖率: 注释行 / 总行"""
    if not source_by_file:
        return 0.0
    total_lines = 0
    comment_lines = 0
    comment_pattern = re.compile(r"^\s*(#|//|/\*|\*|<!--)")
    for content in source_by_file.values():
        for line in (content or "").splitlines():
            total_lines += 1
            if comment_pattern.match(line):
                comment_lines += 1
    if total_lines == 0:
        return 0.0
    return min(100.0, comment_lines / total_lines * 100)


def score_author_centrality(authors: Dict[str, int]) -> float:
    """作者集中度: 基尼系数反向（得分越高表示贡献越分散，越健康）"""
    if not authors:
        return 0.0
    counts = sorted(authors.values())
    n = len(counts)
    total = sum(counts)
    if total == 0 or n == 0:
        return 0.0
    # 基尼系数（标准公式：sorted 后用绝对均值差）
    mean = total / n
    if mean == 0:
        return 0.0
    abs_diffs = 0.0
    for i in range(n):
        for j in range(n):
            abs_diffs += abs(counts[i] - counts[j])
    gini = abs_diffs / (2 * n * n * mean)
    # 反向: 基尼 0 -> 100, 基尼 1 -> 0
    score = max(0.0, min(100.0, 100.0 - gini * 100))
    return round(score, 2)


def score_test_coverage(
    all_files: List[str],
    test_files: List[str],
) -> float:
    """测试覆盖率: 测试文件覆盖的代码行 / 总代码行"""
    if not all_files:
        return 0.0
    test_set = set(test_files)
    covered_lines = 0
    total_lines = 0
    for f in all_files:
        try:
            with open(f, "rb") as fh:
                lines = sum(1 for _ in fh)
        except Exception:
            lines = 0
        total_lines += lines
        # 简单规则: 文件名含 test_ 或 tests/ 视为测试
        if any(t in f for t in test_set) or "test_" in os.path.basename(f) or "/tests/" in f.replace("\\", "/"):
            covered_lines += lines
    if total_lines == 0:
        return 0.0
    return min(100.0, covered_lines / total_lines * 100)


def compute_total_score(
    dimensions: Dict[str, float],
    weights: Optional[Dict[str, float]] = None,
) -> float:
    """加权平均"""
    if not dimensions:
        return 0.0
    if weights is None:
        n = len(dimensions)
        weights = {k: 1.0 / n for k in dimensions}
    total_w = sum(weights.get(k, 0) for k in dimensions)
    if total_w == 0:
        return sum(dimensions.values()) / len(dimensions)
    score = sum(dimensions[k] * weights.get(k, 0) for k in dimensions)
    return round(score / total_w, 2)


def find_hot_spots(
    functions: List[Dict[str, Any]],
    top_n: int = 10,
) -> List[Dict[str, Any]]:
    """热点函数: 按圈复杂度倒序"""
    sorted_funcs = sorted(
        functions,
        key=lambda f: (f.get("complexity", 1), f.get("line_count", 0)),
        reverse=True,
    )
    out = []
    for i, f in enumerate(sorted_funcs[:top_n], 1):
        cc = f.get("complexity", 1)
        if cc >= 50:
            severity = "extreme"
            color = "#F44336"
            suggestion = "立即重构: 拆分为多个职责单一的函数"
        elif cc >= 30:
            severity = "high"
            color = "#FF9800"
            suggestion = "建议重构: 提取子函数或策略模式"
        elif cc >= 15:
            severity = "medium"
            color = "#FFC107"
            suggestion = "可考虑拆分, 降低圈复杂度"
        else:
            severity = "low"
            color = "#4CAF50"
            suggestion = "状态良好"
        out.append({
            "rank": i,
            "file_path": f.get("file_path", ""),
            "function_name": f.get("name", "anonymous"),
            "complexity": cc,
            "line_count": f.get("line_count", 0),
            "severity": severity,
            "severity_color": color,
            "suggestion": suggestion,
        })
    return out


class ScoringEngine:
    """评分引擎"""

    DEFAULT_WEIGHTS = {
        "complexity": 0.25,
        "duplication": 0.20,
        "comment": 0.15,
        "author_centrality": 0.20,
        "test_coverage": 0.20,
    }

    def __init__(self, weights: Optional[Dict[str, float]] = None):
        self.weights = weights or self.DEFAULT_WEIGHTS

    def score(self, ctx: Dict[str, Any]) -> Dict[str, Any]:
        """执行评分"""
        functions = ctx.get("functions", [])
        source_by_file = ctx.get("source_by_file", {})
        authors = ctx.get("authors", {})
        all_files = ctx.get("all_files", [])
        test_files = ctx.get("test_files", [])

        dims = {
            "complexity": round(score_complexity(functions), 2),
            "duplication": round(score_duplication(source_by_file), 2),
            "comment": round(score_comment(source_by_file), 2),
            "author_centrality": round(score_author_centrality(authors), 2),
            "test_coverage": round(score_test_coverage(all_files, test_files), 2),
        }
        total = compute_total_score(dims, self.weights)
        rating, color, label = get_rating(total)
        hot_spots = find_hot_spots(functions, top_n=10)
        return {
            "total_score": total,
            "rating": label,
            "rating_key": rating,
            "rating_color": color,
            "dimensions": dims,
            "hot_spots": hot_spots,
        }


def compute_score(ctx: Dict[str, Any], weights: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
    """便捷接口"""
    engine = ScoringEngine(weights)
    return engine.score(ctx)