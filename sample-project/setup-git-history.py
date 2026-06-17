# -*- coding: utf-8 -*-
"""
setup-git-history.py — 初始化 sample-project 的 git 历史
=========================================================
用法: python setup-git-history.py
会自动:
  1. 在当前目录初始化 git 仓库
  2. 写入 5 个假作者的 25+ commit, 时间跨度 2023-01 到 2026-06
  3. 模拟真实的开发节奏: 早期密集 -> 毕业 -> 偶尔维护

跨平台: Windows Git Bash / Linux / macOS 都能跑
"""
import os
import sys
import subprocess
import datetime
import random
import json


AUTHORS = [
    {"name": "张师兄", "email": "zhang@lab.edu"},
    {"name": "李四",   "email": "li@lab.edu"},
    {"name": "王五",   "email": "wang@company.io"},
    {"name": "赵六",   "email": "zhao@startup.cn"},
    {"name": "孙七",   "email": "sun@lab.edu"},
]

# Commit 历史, 按时间顺序
# (date, author_index, message, files_to_touch)
HISTORY = [
    # === 2023 Q1: 初期, 只有 main.py ===
    ("2023-01-15 10:23:00", 0, "初始版本: 写了个爬虫 demo, 跑通 example.com", ["main.py"]),
    ("2023-01-22 14:35:00", 0, "WIP: 新增爬虫模块 crawler/", ["main.py", "crawler/__init__.py"]),
    ("2023-01-28 16:50:00", 0, "把 if-else 改成 switch (其实是 dict)", ["crawler/main.py"]),
    ("2023-02-04 09:12:00", 0, "修复登录超时", ["crawler/main.py", "crawler/downloader.py"]),
    ("2023-02-19 20:30:00", 0, "临时方案, 下周重构", ["crawler/spider.py"]),
    ("2023-03-05 11:15:00", 1, "新增 html 解析器", ["parser/__init__.py", "parser/html_parser.py"]),
    ("2023-03-18 13:42:00", 0, "加了点注释", ["crawler/spider.py", "crawler/url_manager.py"]),
    ("2023-04-02 19:05:00", 0, "co-authored-by: 李四 <li@lab.edu>", ["parser/html_parser.py", "crawler/spider.py"]),
    # === 2023 Q2: 加 parser 和 database ===
    ("2023-04-15 10:00:00", 0, "新增 parser/ 模块", ["parser/html_parser.py", "parser/json_parser.py"]),
    ("2023-05-01 15:20:00", 1, "json_parser 支持嵌套", ["parser/json_parser.py"]),
    ("2023-05-20 22:10:00", 0, "merge conflict 解决, 选我的版本", ["crawler/main.py", "crawler/spider.py"]),
    ("2023-06-10 11:30:00", 0, "WIP: 新增爬虫模块 parser/content_extractor", ["parser/content_extractor.py"]),
    ("2023-06-25 14:00:00", 2, "加入项目: 重构 downloader.py", ["crawler/downloader.py"]),
    ("2023-07-08 16:45:00", 0, "新增 database/ 模块", ["database/__init__.py", "database/db_manager.py"]),
    ("2023-07-22 09:30:00", 0, "SQLite schema 初始化", ["database/models.py"]),
    # === 2023 Q3: 数据库完善 + utils ===
    ("2023-08-12 13:20:00", 1, "utils/ 拆分", ["utils/__init__.py", "utils/logger.py", "utils/helpers.py"]),
    ("2023-08-28 17:00:00", 0, "http_retry 装饰器", ["utils/http_retry.py"]),
    ("2023-09-15 10:23:00", 0, "新增配置解析", ["config/load_config.py", "config/settings.py"]),
    ("2023-09-30 21:15:00", 0, "临时方案, 下周重构 (再次)", ["config/load_config.py"]),
    ("2023-10-14 11:40:00", 2, "修复迁移脚本", ["database/migrations.py"]),
    # === 2023 Q4: 大量细节修补 ===
    ("2023-11-05 15:30:00", 0, "清理过期 TODO", ["main.py", "crawler/main.py"]),
    ("2023-11-20 20:00:00", 0, "紧急修复生产事故: 数据库锁死", ["database/db_manager.py"]),
    ("2023-12-15 09:50:00", 0, "co-authored-by: 王五 <wang@company.io>", ["crawler/downloader.py"]),
    ("2023-12-30 16:00:00", 3, "加入项目: 加了点 tests", ["tests/test_main.py"]),
    # === 2024 Q1: 师兄毕业, 项目交接 ===
    ("2024-01-10 10:00:00", 0, "毕业前最后一波修改", ["README.md"]),
    ("2024-02-14 22:30:00", 0, "把项目交给师弟, 写了交接文档", ["README.md"]),
    ("2024-03-20 14:00:00", 0, "临走前清理 TODO", ["main.py", "crawler/main.py"]),
    # === 2024 Q2: 师弟接手, 偶尔维护 ===
    ("2024-04-12 11:00:00", 4, "新同学加入, 修点小 bug", ["utils/http_retry.py"]),
    ("2024-05-18 16:30:00", 4, "紧急修复: parse_config 又挂了", ["config/load_config.py"]),
    ("2024-06-25 10:15:00", 4, "把 if-else 改成 switch (这次是真的策略模式)", ["config/load_config.py"]),
    # === 2024 Q3-Q4: 半年没人维护 ===
    ("2024-08-30 09:00:00", 3, "回来修个 bug: 数据库路径错误", ["database/db_manager.py"]),
    ("2024-11-15 14:00:00", 4, "升级 Python 3.11 兼容", ["utils/helpers.py", "database/models.py"]),
    # === 2025 ===
    ("2025-02-08 11:30:00", 3, "修复登录超时 (又来了)", ["crawler/downloader.py"]),
    ("2025-05-20 15:00:00", 4, "新增 SpiderPool", ["crawler/spider.py"]),
    ("2025-09-12 10:45:00", 3, "co-authored-by: 赵六 <zhao@startup.cn>", ["parser/html_parser.py"]),
    ("2025-12-01 16:20:00", 4, "清理过期 TODO (3)", ["config/load_config.py", "database/db_manager.py"]),
    # === 2026 ===
    ("2026-03-15 13:00:00", 3, "修复生产事故: 数据库又锁死了", ["database/db_manager.py"]),
    ("2026-06-16 22:00:00", 4, "迁移到 FastAPI 后端, 保留 sample 作为 demo", ["main.py"]),
]


def run(cmd, env=None, check=True):
    """执行 shell 命令"""
    full_env = os.environ.copy()
    if env:
        full_env.update(env)
    print(f"  $ {cmd[:80]}{'...' if len(cmd) > 80 else ''}")
    result = subprocess.run(
        cmd, shell=True, env=full_env, capture_output=True, text=True
    )
    if check and result.returncode != 0:
        print(f"  !! FAILED: {result.stderr}")
        sys.exit(1)
    return result


def git_init():
    """初始化仓库"""
    if os.path.exists(".git"):
        print("  -> .git 已存在, 跳过 init")
        return
    run("git init")
    run('git config user.name "张师兄"')
    run('git config user.email "zhang@lab.edu"')
    run("git config commit.gpgsign false")
    run("git config core.autocrlf false")


def create_files_at_date(date, files_to_touch):
    """在指定日期前, 确保文件存在"""
    # 这里我们只确保文件存在即可, 内容在第一次 commit 时已有
    pass


def make_commit(date_str, author_idx, message, files):
    """创建单个 commit"""
    author = AUTHORS[author_idx]
    env = {
        "GIT_AUTHOR_NAME": author["name"],
        "GIT_AUTHOR_EMAIL": author["email"],
        "GIT_AUTHOR_DATE": date_str,
        "GIT_COMMITTER_NAME": author["name"],
        "GIT_COMMITTER_EMAIL": author["email"],
        "GIT_COMMITTER_DATE": date_str,
    }
    # 添加文件
    existing = [f for f in files if os.path.exists(f)]
    if not existing:
        existing = ["README.md"] if os.path.exists("README.md") else ["main.py"]
    run(f"git add {' '.join(existing)}")
    # 提交
    run(f'git commit -m "{message}"', env=env)


def main():
    print("=== setup-git-history.py ===")
    print("当前目录:", os.getcwd())
    if not os.path.exists("main.py"):
        print("!! 当前目录没有 main.py, 请在 sample-project/ 目录下运行")
        sys.exit(1)
    git_init()
    print()
    print(f"准备创建 {len(HISTORY)} 个 commit...")
    print()
    # 时间从最早到最晚
    history = sorted(HISTORY, key=lambda h: h[0])
    for i, (date, author_idx, msg, files) in enumerate(history, 1):
        print(f"[{i:2d}/{len(history)}] {date}  {AUTHORS[author_idx]['name']:8s}  {msg[:40]}")
        make_commit(date, author_idx, msg, files)
    print()
    print("=== 完成 ===")
    print(f"共 {len(HISTORY)} 个 commit")
    print()
    print("验证:")
    os.system("git log --oneline | head -10")
    print("...")
    os.system("git log --oneline | wc -l")
    print("总 commit 数如上")


if __name__ == "__main__":
    main()