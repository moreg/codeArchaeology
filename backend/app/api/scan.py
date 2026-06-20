# -*- coding: utf-8 -*-
"""
app.api.scan — 扫描相关路由
============================
"""
import os
import uuid
from typing import Dict, Any, Optional, List

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel, Field

from ..config import settings
from ..utils.logger import get_logger
from ..core.scanner import Scanner, EXT_TO_LANG
from ..core.parser import CodeParser
from ..core.call_graph import CallGraphBuilder
from ..core.git_analyzer import GitAnalyzer
from ..core.scoring import ScoringEngine
from ..models.database import db_session
from ..models.project import Project
from ..models.file import File
from ..models.function import Function
from ..models.call_relation import CallRelation
from ..models.git_commit import GitCommit
from ..models.score import Score
from .progress import progress_manager

log = get_logger("api.scan")

router = APIRouter()


class ScanRequest(BaseModel):
    path: str = Field(..., description="项目绝对路径")
    languages: Optional[List[str]] = Field(default=None, description="分析的语言")


def _is_within(child: str, parent: str) -> bool:
    """检查 child 是否在 parent 之内（防止 .. 绕过）"""
    try:
        child_abs = os.path.realpath(child)
        parent_abs = os.path.realpath(parent)
        return os.path.commonpath([child_abs, parent_abs]) == parent_abs
    except (ValueError, OSError):
        return False


def _validate_scan_path(req_path: str) -> str:
    """校验扫描路径：白名单 + 系统目录黑名单 + 必须在 ALLOWED_SCAN_ROOTS/SAMPLE_PROJECT_PATH 内"""
    if not req_path or not isinstance(req_path, str):
        raise HTTPException(status_code=400, detail={
            "error": "invalid_path",
            "detail": "路径无效",
        })
    abs_path = os.path.abspath(req_path)
    if not os.path.exists(abs_path):
        raise HTTPException(status_code=400, detail={
            "error": "path_not_found",
            "detail": "路径不存在",
        })
    if not os.path.isdir(abs_path):
        raise HTTPException(status_code=400, detail={
            "error": "not_a_directory",
            "detail": "路径不是目录",
        })

    # 黑名单：阻止扫描系统/敏感目录
    lower = abs_path.lower()
    blocked_substrings = (
        os.sep + "windows" + os.sep, "/windows/",
        os.sep + "system32", "/system32",
        os.sep + "etc" + os.sep, "/etc/",
        os.sep + "proc" + os.sep, "/proc/",
        os.sep + "sys" + os.sep, "/sys/",
        os.sep + ".ssh" + os.sep, "/.ssh/",
        os.sep + ".gnupg" + os.sep, "/.gnupg/",
    )
    for sub in blocked_substrings:
        if sub in lower:
            raise HTTPException(status_code=403, detail={
                "error": "forbidden_path",
                "detail": "不允许扫描该路径",
            })

    # 白名单：必须在 ALLOWED_SCAN_ROOTS 或 SAMPLE_PROJECT_PATH 内
    allowed_roots = list(settings.ALLOWED_SCAN_ROOTS) or [settings.SAMPLE_PROJECT_PATH]
    allowed_roots = [os.path.abspath(p) for p in allowed_roots if p]
    if not any(_is_within(abs_path, root) or abs_path == root for root in allowed_roots):
        raise HTTPException(status_code=403, detail={
            "error": "path_not_allowed",
            "detail": "路径不在允许扫描的范围内",
        })
    return abs_path


def _persist_files(scan_id: str, files: list, project_path: str) -> None:
    with db_session() as db:
        for fi in files:
            rel = os.path.relpath(fi.path, project_path)
            f = File(
                project_id=scan_id,
                path=fi.path,
                relative_path=rel,
                language=fi.language,
                size=fi.size,
                line_count=fi.lines,
            )
            db.add(f)


async def _parse_files(scan_id: str, files: list, project_path: str) -> Dict[str, Any]:
    """解析阶段：解析每个文件、提取函数/类、检测测试文件"""
    all_functions: List[Dict[str, Any]] = []
    all_classes: List[Dict[str, Any]] = []
    source_by_file: Dict[str, str] = {}
    all_file_paths: List[str] = []
    test_files: List[str] = []
    total = len(files)
    for i, fi in enumerate(files, 1):
        if progress_manager.is_scan_error(scan_id):
            break
        rel = os.path.relpath(fi.path, project_path)
        await progress_manager.update_progress(scan_id, i, total, current_file=rel)
        try:
            with open(fi.path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            source_by_file[fi.path] = content
            all_file_paths.append(fi.path)
            if "test" in rel.lower() or "/tests/" in rel:
                test_files.append(fi.path)
            parser = CodeParser(fi.language)
            parsed = parser.parse_file(fi.path)
            for fd in parsed.get("functions", []):
                fd["project_id"] = scan_id
                all_functions.append(fd)
            for cd in parsed.get("classes", []):
                cd["project_id"] = scan_id
                all_classes.append(cd)
        except Exception as e:
            log.warning("解析失败 %s: %s", fi.path, e)
            continue
    return {
        "all_functions": all_functions,
        "all_classes": all_classes,
        "source_by_file": source_by_file,
        "all_file_paths": all_file_paths,
        "test_files": test_files,
    }


def _analyze_git(scan_id: str, project_path: str, all_functions: List[Dict[str, Any]]) -> Dict[str, int]:
    """Git 分析阶段：作者统计、blame 汇总、提交记录"""
    authors: Dict[str, int] = {}
    git_analyzer = GitAnalyzer(project_path)
    if not git_analyzer.is_valid_repo():
        return authors
    try:
        authors = git_analyzer.get_shortlog()
        for func in all_functions:
            fp = func.get("file_path", "")
            if not fp:
                continue
            sl = func.get("start_line", 0)
            el = func.get("end_line", 0)
            if sl and el:
                try:
                    blame_info = git_analyzer.get_function_blame(fp, sl, el)
                    func["author"] = blame_info.get("author", "unknown")
                    func["last_commit_hash"] = blame_info.get("commit_hash", "")
                except Exception:
                    pass
            last = git_analyzer.get_file_last_modified(fp)
            if last:
                func["last_modified"] = last.get("committed_at", "")
        commits = git_analyzer.get_commits(max_count=500)
        with db_session() as db:
            for c in commits:
                gc = GitCommit(
                    project_id=scan_id,
                    hash=c["hash"],
                    author=c["author"],
                    email=c["email"],
                    message=c["message"],
                    committed_at=c["committed_at"],
                    files_changed=c["files_changed"],
                )
                db.add(gc)
    except Exception as e:
        log.warning("Git 分析失败: %s", e)
    return authors


def _build_call_graph_for_functions(all_functions: List[Dict[str, Any]], all_classes: List[Dict[str, Any]]) -> Dict[str, Any]:
    builder = CallGraphBuilder()
    for func in all_functions:
        builder.add_function(func)
    for cls in all_classes:
        builder.add_class(cls)
    builder.build_edges_from_functions(all_functions)
    return builder.to_graph_dict()


def _persist_functions_and_relations(scan_id: str, all_functions: List[Dict[str, Any]], graph_dict: Dict[str, Any]) -> None:
    with db_session() as db:
        for func in all_functions:
            fid = func.get("id")
            if not fid:
                continue
            f_record = db.query(File).filter(
                File.project_id == scan_id,
                File.path == func.get("file_path"),
            ).first()
            f = Function(
                id=fid,
                project_id=scan_id,
                file_id=f_record.id if f_record else None,
                name=func.get("name", "anonymous"),
                file_path=func.get("file_path", ""),
                start_line=func.get("start_line", 0),
                end_line=func.get("end_line", 0),
                line_count=func.get("line_count", 0),
                language=func.get("language", "python"),
                class_name=func.get("class_name") or "",
                complexity=func.get("complexity", 1),
                author=func.get("author", ""),
                last_modified=func.get("last_modified", ""),
                last_commit_hash=func.get("last_commit_hash", ""),
                test_coverage=0,
            )
            db.add(f)
        for edge in graph_dict.get("edges", []):
            cr = CallRelation(
                project_id=scan_id,
                source=edge["source"],
                target=edge["target"],
                call_type=edge.get("call_type", "direct"),
                call_count=edge.get("call_count", 1),
            )
            db.add(cr)


def _compute_and_persist_score(scan_id: str, scoring_ctx: Dict[str, Any]) -> None:
    engine = ScoringEngine()
    score_result = engine.score(scoring_ctx)
    with db_session() as db:
        sc = Score(
            project_id=scan_id,
            total_score=score_result["total_score"],
            rating=score_result["rating"],
            rating_color=score_result["rating_color"],
            dimensions=score_result["dimensions"],
            hot_spots=score_result["hot_spots"],
        )
        db.add(sc)


async def _do_scan(scan_id: str, project_path: str, languages: Optional[List[str]]):
    """后台扫描任务（编排器；每个阶段已拆为独立函数）"""
    try:
        log.info("开始扫描 scan_id=%s path=%s", scan_id, project_path)
        with db_session() as db:
            project = db.query(Project).filter(Project.id == scan_id).first()
            if not project:
                project = Project(
                    id=scan_id,
                    name=os.path.basename(project_path) or scan_id,
                    path=project_path,
                    languages=",".join(languages or list(EXT_TO_LANG.values())),
                    status="scanning",
                )
                db.add(project)
            project.status = "scanning"
            project.progress = 0
            project.error = ""

        # Step 1: 扫描文件
        scanner = Scanner(project_path, languages)
        files = scanner.scan()
        total = len(files)
        await progress_manager.start_scan(scan_id, total=total,
                                          project_name=os.path.basename(project_path))
        _persist_files(scan_id, files, project_path)

        # Step 2: 解析文件
        parsed = await _parse_files(scan_id, files, project_path)
        all_functions = parsed["all_functions"]
        all_classes = parsed["all_classes"]
        source_by_file = parsed["source_by_file"]
        all_file_paths = parsed["all_file_paths"]
        test_files = parsed["test_files"]

        # Step 3: Git 分析
        log.info("Git 分析中...")
        authors = _analyze_git(scan_id, project_path, all_functions)

        # Step 4: 调用图
        log.info("构建调用图...")
        graph_dict = _build_call_graph_for_functions(all_functions, all_classes)
        _persist_functions_and_relations(scan_id, all_functions, graph_dict)

        # Step 5: 评分
        log.info("评分中...")
        scoring_ctx = {
            "functions": all_functions,
            "source_by_file": source_by_file,
            "authors": authors,
            "all_files": all_file_paths,
            "test_files": test_files,
        }
        _compute_and_persist_score(scan_id, scoring_ctx)

        # 收尾
        with db_session() as db:
            project = db.query(Project).filter(Project.id == scan_id).first()
            if project:
                project.status = "done"
                project.progress = total
                from datetime import datetime, timezone
                project.finished_at = datetime.now(timezone.utc)

        duration = 0.0
        info = progress_manager.get_scan_info(scan_id)
        if "started_at" in info:
            import time
            duration = time.time() - info["started_at"]
        await progress_manager.complete_scan(scan_id, duration=duration)
        log.info("扫描完成 scan_id=%s duration=%.2fs", scan_id, duration)

    except Exception as e:
        log.error("扫描失败 scan_id=%s: %s", scan_id, e)
        import traceback
        log.debug(traceback.format_exc())
        await progress_manager.error_scan(scan_id, "扫描失败，详见后端日志")
        with db_session() as db:
            project = db.query(Project).filter(Project.id == scan_id).first()
            if project:
                project.status = "error"
                project.error = "扫描失败，详见后端日志"


@router.post("/scan")
async def start_scan(req: ScanRequest, background_tasks: BackgroundTasks):
    """启动一个项目扫描"""
    try:
        abs_path = _validate_scan_path(req.path)
        scan_id = str(uuid.uuid4())
        background_tasks.add_task(_do_scan, scan_id, abs_path, req.languages)
        return {
            "scan_id": scan_id,
            "status": "scanning",
        }
    except HTTPException:
        raise
    except Exception as e:
        log.error("start_scan 失败: %s", e)
        # 不向客户端返回 str(e)
        raise HTTPException(status_code=500, detail={
            "error": "internal_error",
            "detail": "服务器内部错误",
        })


@router.get("/scan/{scan_id}/status")
async def get_status(scan_id: str):
    """获取扫描状态"""
    return progress_manager.get_status(scan_id)
