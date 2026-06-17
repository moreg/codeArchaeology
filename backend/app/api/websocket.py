# -*- coding: utf-8 -*-
"""
app.api.websocket — WebSocket 进度推送
======================================
"""
import asyncio
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from ..utils.logger import get_logger
from .progress import progress_manager

log = get_logger("api.websocket")

router = APIRouter()


@router.websocket("/ws/scan/{scan_id}")
async def ws_scan(websocket: WebSocket, scan_id: str):
    """WebSocket: 推送扫描进度"""
    await websocket.accept()
    log.info("WebSocket 连接 scan_id=%s", scan_id)
    q = await progress_manager.subscribe(scan_id)
    try:
        # 先发一条初始状态
        status = progress_manager.get_status(scan_id)
        await websocket.send_text(json.dumps({
            "type": "status",
            "scan_id": scan_id,
            "status": status.get("status", "scanning"),
            "progress": status.get("progress", 0),
            "total": status.get("total", 0),
            "current_file": status.get("current_file", ""),
        }, ensure_ascii=False))
        while True:
            try:
                msg = await asyncio.wait_for(q.get(), timeout=60.0)
                await websocket.send_text(json.dumps(msg, ensure_ascii=False))
                if msg.get("type") in ("complete", "error"):
                    break
            except asyncio.TimeoutError:
                # 心跳
                await websocket.send_text(json.dumps({"type": "ping"}))
    except WebSocketDisconnect:
        log.info("WebSocket 断开 scan_id=%s", scan_id)
    except Exception as e:
        log.error("WebSocket 异常: %s", e)
    finally:
        await progress_manager.unsubscribe(scan_id, q)
        try:
            await websocket.close()
        except Exception:
            pass