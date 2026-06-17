# -*- coding: utf-8 -*-
"""
app.core.mock_data — LLM 不可用时的预置演示数据
================================================
"""

MOCK_STORIES = [
    {
        "function_name": "parse_config",
        "file_path": "config/load_config.py",
        "summary": "这是一个配置解析函数, 由张师兄在 2023-09-15 创建, 圈复杂度高达 67, 是整个项目的最大屎山。",
        "narrative": (
            "据 git blame 记录, 这个函数最初由 张师兄 在 2023-09-15 (commit a1b2c3d) 创建, "
            "用于解析多来源配置 (py/json/ini/yaml/toml)。函数在随后的两年里被频繁修改:\n"
            " - 2023-11-20 (commit b2c3d4e) 张师兄在紧急修复生产事故时增加了 6 层嵌套 if-else;\n"
            " - 2024-06-25 (commit c3d4e5f) 孙七 尝试把 if-else 改成 switch (其实是 dict.get);\n"
            " - 2025-05-20 (commit d4e5f6a) 王五 又加了 8 个新字段的处理分支。\n"
            "目前圈复杂度已经累积到 67 (commit e5f6a7b 测得), 是项目里最危险的函数。\n\n"
            "风险点:\n"
            " 1. 任何一处改动都可能引发隐藏的 bug, 因为 if-else 嵌套太深, 单元测试覆盖率几乎为 0;\n"
            " 2. 函数注释只有开头 2 行, 后续 22 段逻辑全部没有说明, 接手的人完全靠猜。\n"
            "无法考证: 这个函数的原始设计意图, 因为最早的 commit message 只写了 '新增配置解析'。"
        ),
        "timeline": [
            {"commit_hash": "a1b2c3d", "date": "2023-09-15", "author": "张师兄", "message": "新增配置解析"},
            {"commit_hash": "b2c3d4e", "date": "2023-11-20", "author": "张师兄", "message": "紧急修复生产事故"},
            {"commit_hash": "c3d4e5f", "date": "2024-06-25", "author": "孙七", "message": "把 if-else 改成 switch"},
            {"commit_hash": "d4e5f6a", "date": "2025-05-20", "author": "王五", "message": "新增 SpiderPool"},
            {"commit_hash": "e5f6a7b", "date": "2026-03-15", "author": "赵六", "message": "修复生产事故"},
        ],
        "risks": [
            "圈复杂度 67, 重构风险极高",
            "无单元测试覆盖",
            "嵌套深度过深, 可读性差",
        ],
    },
    {
        "function_name": "dispatch",
        "file_path": "crawler/spider.py",
        "summary": "任务派发器, 师兄遗作, 嵌套 5 层 if-else。",
        "narrative": (
            "这个 dispatch 函数在 2023-01-22 (commit f6a7b8c) 由张师兄初次提交, "
            "目的是把不同类型的 task 路由到对应的 parser。函数内有 5 层嵌套 if-else "
            "(参考 commit 9h0i1j2), 是项目里中等危险度的代码。"
        ),
        "timeline": [
            {"commit_hash": "f6a7b8c", "date": "2023-01-22", "author": "张师兄", "message": "WIP: 新增爬虫模块"},
            {"commit_hash": "9h0i1j2", "date": "2023-05-20", "author": "张师兄", "message": "临时方案, 下周重构"},
        ],
        "risks": [
            "5 层嵌套 if-else, 难以单测",
        ],
    },
    {
        "function_name": "save_record",
        "file_path": "database/db_manager.py",
        "summary": "数据库写入函数, 孙七 2024 年接手后增加了批量写入支持。",
        "narrative": (
            "save_record 由 张师兄 在 2023-07 创建, 2024 年孙七接手后增加了 error handling。"
        ),
        "timeline": [
            {"commit_hash": "k2l3m4n", "date": "2023-07-08", "author": "张师兄", "message": "新增 database/ 模块"},
        ],
        "risks": [],
    },
    {
        "function_name": "parse",
        "file_path": "parser/html_parser.py",
        "summary": "HTML 解析, 王五贡献了 json-ld 支持。",
        "narrative": "基础 HTML 解析, 多个作者协作维护。",
        "timeline": [
            {"commit_hash": "p5q6r7s", "date": "2023-03-05", "author": "李四", "message": "新增 html 解析器"},
        ],
        "risks": [],
    },
    {
        "function_name": "fetch_one",
        "file_path": "crawler/main.py",
        "summary": "单条抓取函数, 张师兄手写。",
        "narrative": "单条抓取封装, 含重试逻辑。",
        "timeline": [
            {"commit_hash": "t8u9v0w", "date": "2023-02-04", "author": "张师兄", "message": "修复登录超时"},
        ],
        "risks": [],
    },
]


MOCK_REFACTORS = [
    {
        "function_name": "parse_config",
        "file_path": "config/load_config.py",
        "suggestion": "将 22 段 if-else 拆分为 5 个职责单一的子函数 (load_from_file / apply_env / apply_override / validate / finalize)",
        "priority": "high",
        "diff": (
            "--- a/config/load_config.py\n"
            "+++ b/config/load_config.py\n"
            "@@ -255,20 +255,15 @@\n"
            " def parse_config(path=None, override=None, env_prefix=\"CRAWLER_\"):\n"
            "     cfg = {}\n"
            "     base = DEFAULT_CONFIG\n"
            "     for k, v in base.items():\n"
            "         if isinstance(v, dict):\n"
            "             cfg[k] = dict(v)\n"
            "         else:\n"
            "             cfg[k] = v\n"
            "-    # 1. 加载文件\n"
            "-    if path:\n"
            "-        ...\n"
            "+    cfg = _init_default()\n"
            "+    if path:\n"
            "+        cfg = _merge_file(cfg, path)\n"
            "+    cfg = _apply_env(cfg, env_prefix)\n"
            "+    if override:\n"
            "+        cfg = _merge_override(cfg, override)\n"
            "+    return _validate_and_finalize(cfg)\n"
        ),
        "estimated_reduction": "60% 代码行数",
    },
    {
        "function_name": "dispatch",
        "file_path": "crawler/spider.py",
        "suggestion": "用策略模式替换 5 层嵌套 if-else",
        "priority": "medium",
        "diff": (
            "--- a/crawler/spider.py\n"
            "+++ b/crawler/spider.py\n"
            "@@ -79,20 +79,15 @@\n"
            "-    if task is None:\n"
            "-        return None\n"
            "-    url = task.get(\"url\")\n"
            "-    parser_name = task.get(\"parser\", self.DEFAULT_PARSER)\n"
            "-    if parser_name not in self.parsers:\n"
            "-        log.warning(\"未知 parser: %s, 使用默认 html\", parser_name)\n"
            "-        parser_name = \"html\"\n"
            "+    parser = self._get_parser(task.get(\"parser\"))\n"
            "     ...\n"
        ),
        "estimated_reduction": "40% 代码行数",
    },
    {
        "function_name": "save_record",
        "file_path": "database/db_manager.py",
        "suggestion": "将 JSON 序列化抽成 helper, 主函数保持 15 行以内",
        "priority": "low",
        "diff": (
            "--- a/database/db_manager.py\n"
            "+++ b/database/db_manager.py\n"
            "@@ -94,20 +94,12 @@\n"
            "     def save_record(self, record):\n"
            "-        ...\n"
            "+        return _save_record_impl(self._conn(), record)\n"
        ),
        "estimated_reduction": "30% 代码行数",
    },
    {
        "function_name": "parse",
        "file_path": "parser/html_parser.py",
        "suggestion": "把 4 种抽取策略拆成独立方法",
        "priority": "medium",
        "diff": (
            "--- a/parser/html_parser.py\n"
            "+++ b/parser/html_parser.py\n"
            "@@ -38,20 +38,15 @@\n"
            "-    # 尝试多种策略\n"
            "-    content = (\n"
            "-        self._try_article(raw)\n"
            "-        or self._try_main(raw)\n"
            "-        or self._try_density(raw)\n"
            "-        or self._fallback(raw)\n"
            "-    )\n"
            "+    content = self._run_strategies(raw)\n"
        ),
        "estimated_reduction": "20% 代码行数",
    },
    {
        "function_name": "fetch_one",
        "file_path": "crawler/main.py",
        "suggestion": "下载 + 解析 + 写库 分三步, 便于 mock 测试",
        "priority": "medium",
        "diff": (
            "--- a/crawler/main.py\n"
            "+++ b/crawler/main.py\n"
            "@@ -79,30 +79,20 @@\n"
            "-    raw = downloader.request(method, url, headers=headers)\n"
            "-    if raw is None:\n"
            "-        ...\n"
            "-    try:\n"
            "-        parsed = parser.parse(raw, base_url=url)\n"
            "+    raw = _safe_download(downloader, method, url, headers)\n"
            "+    parsed = _safe_parse(parser, raw, url)\n"
        ),
        "estimated_reduction": "35% 代码行数",
    },
]


def get_mock_story(function_name: str, file_path: str = "") -> dict:
    """根据函数名查找对应的 mock story"""
    for s in MOCK_STORIES:
        if s["function_name"] == function_name:
            if not file_path or file_path.endswith(s["file_path"]):
                return {
                    "node_id": f"func_{file_path}_{function_name}",
                    "summary": s["summary"],
                    "timeline": s["timeline"],
                    "narrative": s["narrative"],
                    "model": "mock",
                    "generated_at": "2026-06-16T22:30:00",
                    "risks": s.get("risks", []),
                }
    # fallback: 返回通用 mock
    return {
        "node_id": f"func_{file_path}_{function_name}",
        "summary": f"{function_name} 是一个项目里的函数, 历史细节无法考证。",
        "timeline": [],
        "narrative": (
            f"无法考证: 这个项目未启用 git, 或 {function_name} 在 git 历史中没有明确记录。"
            "建议接入 git 后再试。"
        ),
        "model": "mock",
        "generated_at": "2026-06-16T22:30:00",
        "risks": [],
    }


def get_mock_refactor(function_name: str, file_path: str = "") -> dict:
    for r in MOCK_REFACTORS:
        if r["function_name"] == function_name:
            if not file_path or file_path.endswith(r["file_path"]):
                return {
                    "node_id": f"func_{file_path}_{function_name}",
                    "suggestion": r["suggestion"],
                    "priority": r["priority"],
                    "diff": r["diff"],
                    "estimated_reduction": r["estimated_reduction"],
                }
    return {
        "node_id": f"func_{file_path}_{function_name}",
        "suggestion": "无法考证: 缺少上下文, 请提供更详细的代码片段",
        "priority": "low",
        "diff": "--- a/\n+++ b/\n",
        "estimated_reduction": "0%",
    }