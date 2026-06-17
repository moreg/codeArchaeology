# -*- coding: utf-8 -*-
"""
app.main — FastAPI 入口
========================
"""
import os
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import settings
from .utils.logger import get_logger
from .models.database import init_db, engine, Base
from .api import scan, graph, score, analyze, sample, websocket

log = get_logger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """启动事件: 初始化数据库"""
    log.info("CodeArchaeology Backend 启动中...")
    log.info("LLM 模式: %s", settings.LLM_MODE)
    log.info("示例项目: %s", settings.SAMPLE_PROJECT_PATH)
    # 确保 data 目录
    data_dir = Path(__file__).parent.parent / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    # 初始化数据库
    try:
        from .models import project, file, function, call_relation
        from .models import git_commit, git_blame, score as score_model
        from .models import analysis_result
        Base.metadata.create_all(bind=engine)
        log.info("数据库表已就绪")
    except Exception as e:
        log.error("数据库初始化失败: %s", e)
    yield
    log.info("Backend 关闭")


app = FastAPI(
    title="代码考古学 API",
    description="Code Archaeology Backend - 让接手屎山的开发者 30 秒看懂老代码",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    log.error("未处理异常 %s %s: %s", request.method, request.url, exc)
    # 不向客户端返回内部异常详情；详细错误仅写日志
    return JSONResponse(
        status_code=500,
        content={"error": "internal_error", "detail": "服务器内部错误"},
    )


@app.get("/")
async def root():
    return {
        "name": "Code Archaeology Backend",
        "version": "0.1.0",
        "status": "ok",
        "llm_mode": settings.LLM_MODE,
    }


@app.get("/health")
async def health():
    return {"status": "ok"}


# 挂载路由
app.include_router(scan.router, prefix="/api", tags=["scan"])
app.include_router(graph.router, prefix="/api", tags=["graph"])
app.include_router(score.router, prefix="/api", tags=["score"])
app.include_router(analyze.router, prefix="/api", tags=["analyze"])
app.include_router(sample.router, prefix="/api", tags=["sample"])
app.include_router(websocket.router, tags=["websocket"])