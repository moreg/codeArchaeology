# -*- coding: utf-8 -*-
"""
app.config — 配置管理
======================
支持环境变量与 .env 文件
"""
import os
from pathlib import Path
from typing import List

try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    pass


class Settings:
    """应用配置"""

    # 数据库
    DATABASE_URL: str = os.environ.get(
        "DATABASE_URL",
        f"sqlite:///{Path(__file__).parent.parent / 'data' / 'code_archaeology.db'}"
    )

    # LLM
    LLM_MODE: str = os.environ.get("LLM_MODE", "mock")
    OPENAI_API_KEY: str = os.environ.get("OPENAI_API_KEY", "")
    OPENAI_BASE_URL: str = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
    OPENAI_MODEL: str = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
    OLLAMA_BASE_URL: str = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL: str = os.environ.get("OLLAMA_MODEL", "qwen2.5")

    # 服务器
    HOST: str = os.environ.get("HOST", "0.0.0.0")
    PORT: int = int(os.environ.get("PORT", "8000"))

    # CORS
    CORS_ORIGINS: List[str] = [
        o.strip() for o in os.environ.get(
            "CORS_ORIGINS",
            "http://localhost:5173,http://127.0.0.1:5173"
        ).split(",") if o.strip()
    ]

    # 示例项目
    SAMPLE_PROJECT_PATH: str = os.environ.get(
        "SAMPLE_PROJECT_PATH",
        str(Path(__file__).parent.parent.parent / "sample-project")
    )

    # 允许扫描的根路径白名单（逗号分隔）
    # 留空则仅允许 SAMPLE_PROJECT_PATH
    ALLOWED_SCAN_ROOTS: List[str] = [
        p.strip() for p in os.environ.get(
            "ALLOWED_SCAN_ROOTS",
            ""
        ).split(",") if p.strip()
    ]

    # 支持的语言
    SUPPORTED_LANGUAGES: List[str] = ["python", "javascript", "typescript", "java"]

    # 跳过的目录
    SKIP_DIRS: List[str] = [
        "node_modules", ".git", "build", "dist", "__pycache__",
        ".venv", "venv", "env", ".idea", ".vscode", "target", "out",
    ]

    # 文件大小限制 (10MB)
    MAX_FILE_SIZE: int = 10 * 1024 * 1024

    # 评分权重
    SCORING_WEIGHTS: dict = {
        "complexity": 0.25,
        "duplication": 0.20,
        "comment": 0.15,
        "author_centrality": 0.20,
        "test_coverage": 0.20,
    }


settings = Settings()


def get_settings() -> Settings:
    return settings