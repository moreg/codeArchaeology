# -*- coding: utf-8 -*-
"""
app.api.analyze — LLM 分析路由
================================
"""
import os
import uuid
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..utils.logger import get_logger
from ..core.llm_adapter import get_adapter
from ..core.git_analyzer import GitAnalyzer
from ..core.scoring import get_rating
from ..models.database import db_session
from ..models.project import Project
from ..models.function import Function
from ..models.analysis_result import AnalysisResult

log = get_logger("api.analyze")

router = APIRouter()


class AnalyzeRequest(BaseModel):
    scan_id: str = Field(..., description="扫描 ID")
    node_id: str = Field(..., description="函数节点 ID")


def _read_function_code(file_path: str, start_line: int, end_line: int) -> str:
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
        return "".join(lines[start_line - 1:end_line])
    except Exception as e:
        return f"(无法读取源码: {e})"


def _build_story_context(scan_id: str, node_id: str) -> Dict[str, Any]:
    """为 LLM story 生成准备上下文"""
    with db_session() as db:
        func = db.query(Function).filter(
            Function.id == node_id,
            Function.project_id == scan_id,
        ).first()
        if not func:
            return {}
        project = db.query(Project).filter(Project.id == scan_id).first()
        project_path = project.path if project else ""
        # 读取源码
        code = _read_function_code(func.file_path, func.start_line, func.end_line)
        # Git blame
        blame_str = "（无 git 历史）"
        timeline_str = "（无 git 历史）"
        if project_path:
            ga = GitAnalyzer(project_path)
            if ga.is_valid_repo():
                blame = ga.get_function_blame(func.file_path, func.start_line, func.end_line)
                if blame:
                    lines = []
                    for k, v in (blame.get("authors") or {}).items():
                        lines.append(f"  - {k}: {v} 行")
                    blame_str = "\n".join(lines) if lines else "无具体数据"
                history = ga.get_file_history(func.file_path, max_count=10)
                if history:
                    timeline_lines = []
                    for h in history:
                        timeline_lines.append(
                            f"  - {h['hash']} ({h['committed_at'][:10]}) {h['author']}: {h['message'][:60]}"
                        )
                    timeline_str = "\n".join(timeline_lines)
        cc_rating = "高" if func.complexity > 30 else "中" if func.complexity > 10 else "低"
        return {
            "node_id": node_id,
            "function_name": func.name,
            "file_path": func.file_path,
            "start_line": func.start_line,
            "end_line": func.end_line,
            "line_count": func.line_count,
            "complexity": func.complexity,
            "class_name": func.class_name or "",
            "code": code,
            "blame": blame_str,
            "timeline": timeline_str,
            "callers": "（暂未实现）",
            "callees": "（暂未实现）",
            "cc_rating": cc_rating,
        }


@router.post("/analyze/story")
async def analyze_story(req: AnalyzeRequest):
    """生成函数故事"""
    try:
        ctx = _build_story_context(req.scan_id, req.node_id)
        if not ctx:
            raise HTTPException(status_code=404, detail={
                "error": "function_not_found",
                "detail": f"node_id {req.node_id} 不存在",
            })
        adapter = get_adapter()
        result = adapter.generate_story(ctx)
        # 持久化
        try:
            with db_session() as db:
                ar = AnalysisResult(
                    id=str(uuid.uuid4()),
                    project_id=req.scan_id,
                    node_id=req.node_id,
                    kind="story",
                    result=result,
                )
                db.add(ar)
        except Exception as e:
            log.warning("持久化失败: %s", e)
        return result
    except HTTPException:
        raise
    except Exception as e:
        log.error("analyze_story 失败: %s", e)
        raise HTTPException(status_code=500, detail={
            "error": "internal_error",
            "detail": "服务器内部错误",
        })


@router.post("/analyze/refactor")
async def analyze_refactor(req: AnalyzeRequest):
    """生成重构建议"""
    try:
        ctx = _build_story_context(req.scan_id, req.node_id)
        if not ctx:
            raise HTTPException(status_code=404, detail={
                "error": "function_not_found",
                "detail": f"node_id {req.node_id} 不存在",
            })
        adapter = get_adapter()
        result = adapter.generate_refactor(ctx)
        try:
            with db_session() as db:
                ar = AnalysisResult(
                    id=str(uuid.uuid4()),
                    project_id=req.scan_id,
                    node_id=req.node_id,
                    kind="refactor",
                    result=result,
                )
                db.add(ar)
        except Exception as e:
            log.warning("持久化失败: %s", e)
        return result
    except HTTPException:
        raise
    except Exception as e:
        log.error("analyze_refactor 失败: %s", e)
        raise HTTPException(status_code=500, detail={
            "error": "internal_error",
            "detail": "服务器内部错误",
        })