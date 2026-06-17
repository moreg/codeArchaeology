# -*- coding: utf-8 -*-
"""
app.api.progress — 扫描进度管理器
==================================
使用 asyncio.Queue 实现 WebSocket 进度推送。
"""
import asyncio
import uuid
from typing import Dict, Any, Optional, List
from collections import defaultdict


class ProgressManager:
    """全局进度管理器"""

    def __init__(self):
        self._scan_info: Dict[str, Dict[str, Any]] = {}
        self._queues: Dict[str, List[asyncio.Queue]] = defaultdict(list)
        self._lock = asyncio.Lock()

    async def start_scan(self, scan_id: str, total: int = 0, project_name: str = ""):
        async with self._lock:
            self._scan_info[scan_id] = {
                "scan_id": scan_id,
                "project_name": project_name,
                "progress": 0,
                "total": total,
                "current_file": "",
                "status": "scanning",
                "started_at": asyncio.get_running_loop().time(),
            }
        await self._broadcast(scan_id, {
            "type": "start",
            "scan_id": scan_id,
            "total": total,
            "project_name": project_name,
        })

    async def update_progress(self, scan_id: str, current: int, total: int,
                             current_file: str = ""):
        async with self._lock:
            if scan_id in self._scan_info:
                self._scan_info[scan_id]["progress"] = current
                self._scan_info[scan_id]["total"] = total
                self._scan_info[scan_id]["current_file"] = current_file
        await self._broadcast(scan_id, {
            "type": "progress",
            "scan_id": scan_id,
            "current": current,
            "total": total,
            "file": current_file,
        })

    async def complete_scan(self, scan_id: str, duration: float = 0.0):
        async with self._lock:
            if scan_id in self._scan_info:
                self._scan_info[scan_id]["status"] = "done"
        await self._broadcast(scan_id, {
            "type": "complete",
            "scan_id": scan_id,
            "duration": duration,
        })

    async def error_scan(self, scan_id: str, message: str):
        async with self._lock:
            if scan_id in self._scan_info:
                self._scan_info[scan_id]["status"] = "error"
                self._scan_info[scan_id]["error"] = message
        await self._broadcast(scan_id, {
            "type": "error",
            "scan_id": scan_id,
            "message": message,
        })

    async def _broadcast(self, scan_id: str, message: Dict[str, Any]):
        # 复制队列列表避免迭代时修改
        queues = list(self._queues.get(scan_id, []))
        for q in queues:
            try:
                q.put_nowait(message)
            except asyncio.QueueFull:
                pass
            except Exception:
                pass

    def get_status(self, scan_id: str) -> Dict[str, Any]:
        info = self._scan_info.get(scan_id)
        if not info:
            return {
                "scan_id": scan_id,
                "status": "unknown",
                "progress": 0,
                "total": 0,
                "current_file": "",
            }
        return {
            "scan_id": scan_id,
            "status": info.get("status", "scanning"),
            "progress": info.get("progress", 0),
            "total": info.get("total", 0),
            "current_file": info.get("current_file", ""),
            "project_name": info.get("project_name", ""),
        }

    async def subscribe(self, scan_id: str) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue(maxsize=100)
        async with self._lock:
            self._queues[scan_id].append(q)
        return q

    async def unsubscribe(self, scan_id: str, q: asyncio.Queue):
        async with self._lock:
            if scan_id in self._queues:
                try:
                    self._queues[scan_id].remove(q)
                except ValueError:
                    pass


progress_manager = ProgressManager()