# -*- coding: utf-8 -*-
"""
app.api.graph — 调用图查询
===========================
"""
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Query

from ..utils.logger import get_logger
from ..models.database import db_session
from ..models.project import Project
from ..models.function import Function
from ..models.call_relation import CallRelation

log = get_logger("api.graph")

router = APIRouter()


@router.get("/scan/{scan_id}/graph")
async def get_graph(
    scan_id: str,
    level: str = Query("function", description="function | file | module"),
    color_mode: str = Query("complexity", description="complexity | frequency | author | test_coverage"),
):
    """获取调用图"""
    try:
        with db_session() as db:
            project = db.query(Project).filter(Project.id == scan_id).first()
            if not project:
                raise HTTPException(status_code=404, detail={
                    "error": "not_found",
                    "detail": f"scan_id {scan_id} 不存在",
                })
            nodes: List[Dict[str, Any]] = []
            edges: List[Dict[str, Any]] = []
            if level == "function":
                funcs = db.query(Function).filter(Function.project_id == scan_id).all()
                for f in funcs:
                    nodes.append({
                        "id": f.id,
                        "name": f.name,
                        "level": "function",
                        "file_path": f.file_path,
                        "start_line": f.start_line,
                        "end_line": f.end_line,
                        "complexity": f.complexity,
                        "line_count": f.line_count,
                        "author": f.author or "",
                        "last_modified": f.last_modified or "",
                        "last_commit_hash": f.last_commit_hash or "",
                        "test_coverage": f.test_coverage or 0,
                    })
                relations = db.query(CallRelation).filter(
                    CallRelation.project_id == scan_id
                ).all()
                for r in relations:
                    edges.append({
                        "source": r.source,
                        "target": r.target,
                        "call_type": r.call_type or "direct",
                        "call_count": r.call_count or 1,
                    })
            elif level == "file":
                # 按文件聚合
                files_map: Dict[str, Dict[str, Any]] = {}
                funcs = db.query(Function).filter(Function.project_id == scan_id).all()
                for f in funcs:
                    fp = f.file_path
                    if fp not in files_map:
                        files_map[fp] = {
                            "id": f"file_{fp}",
                            "name": fp.split("/")[-1] if fp else "",
                            "level": "file",
                            "file_path": fp,
                            "start_line": f.start_line,
                            "end_line": f.end_line,
                            "complexity": 0,
                            "line_count": 0,
                            "function_count": 0,
                            "max_complexity": 0,
                        }
                    cur = files_map[fp]
                    cur["line_count"] = max(cur["line_count"], f.line_count or 0)
                    cur["end_line"] = max(cur["end_line"], f.end_line or 0)
                    cur["function_count"] += 1
                    if (f.complexity or 1) > cur["max_complexity"]:
                        cur["max_complexity"] = f.complexity
                for fp, item in files_map.items():
                    item["complexity"] = item["max_complexity"]
                    del item["max_complexity"]
                    nodes.append(item)
            return {
                "scan_id": scan_id,
                "level": level,
                "color_mode": color_mode,
                "nodes": nodes,
                "edges": edges,
            }
    except HTTPException:
        raise
    except Exception as e:
        log.error("get_graph 失败: %s", e)
        raise HTTPException(status_code=500, detail={
            "error": "internal_error",
            "detail": "服务器内部错误",
        })