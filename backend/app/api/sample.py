# -*- coding: utf-8 -*-
"""
app.api.sample — 示例项目加载
==============================
"""
import os
import uuid
from fastapi import APIRouter, BackgroundTasks, HTTPException

from ..config import settings
from ..utils.logger import get_logger
from .scan import _do_scan

log = get_logger("api.sample")

router = APIRouter()


@router.post("/sample/load")
async def load_sample(background_tasks: BackgroundTasks):
    """加载内置示例项目"""
    sample_path = settings.SAMPLE_PROJECT_PATH
    if not os.path.exists(sample_path):
        raise HTTPException(status_code=404, detail={
            "error": "sample_not_found",
            "detail": f"示例项目不存在: {sample_path}",
        })
    scan_id = str(uuid.uuid4())
    background_tasks.add_task(_do_scan, scan_id, sample_path, ["python"])
    log.info("加载示例项目 scan_id=%s path=%s", scan_id, sample_path)
    return {
        "scan_id": scan_id,
        "project_name": "祖传 Python 爬虫",
        "status": "scanning",
    }