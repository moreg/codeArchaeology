# -*- coding: utf-8 -*-
"""
app.api.score — 评分查询
==========================
"""
from fastapi import APIRouter, HTTPException

from ..utils.logger import get_logger
from ..models.database import db_session
from ..models.project import Project
from ..models.score import Score

log = get_logger("api.score")

router = APIRouter()


@router.get("/scan/{scan_id}/score")
async def get_score(scan_id: str):
    """获取屎山评分"""
    try:
        with db_session() as db:
            project = db.query(Project).filter(Project.id == scan_id).first()
            if not project:
                raise HTTPException(status_code=404, detail={
                    "error": "not_found",
                    "detail": f"scan_id {scan_id} 不存在",
                })
            score = db.query(Score).filter(Score.project_id == scan_id).first()
            if not score:
                # 还没算出来, 跑一个临时评分
                return {
                    "scan_id": scan_id,
                    "status": "pending",
                    "total_score": 0,
                    "rating": "计算中",
                    "rating_color": "#999999",
                    "dimensions": {
                        "complexity": 0,
                        "duplication": 0,
                        "comment": 0,
                        "author_centrality": 0,
                        "test_coverage": 0,
                    },
                    "hot_spots": [],
                }
            return {
                "scan_id": scan_id,
                "total_score": score.total_score,
                "rating": score.rating,
                "rating_color": score.rating_color,
                "dimensions": score.dimensions or {},
                "hot_spots": score.hot_spots or [],
            }
    except HTTPException:
        raise
    except Exception as e:
        log.error("get_score 失败: %s", e)
        raise HTTPException(status_code=500, detail={
            "error": "internal_error",
            "detail": "服务器内部错误",
        })