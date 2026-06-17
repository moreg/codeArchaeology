# 贡献指南 Contributing

欢迎来到「代码考古学」！本文档面向所有想为本项目贡献代码、文档、问题报告或想法的伙伴。

我们欢迎所有形式的贡献：报告 Bug、提出功能建议、改进文档、提交代码、设计资源等。

---

## 目录

- [行为准则](#行为准则)
- [我能帮什么忙](#我能帮什么忙)
- [开发环境搭建](#开发环境搭建)
- [项目结构速览](#项目结构速览)
- [开发流程](#开发流程)
- [代码风格](#代码风格)
- [测试要求](#测试要求)
- [提交规范](#提交规范)
- [Pull Request 流程](#pull-request-流程)
- [Issue 报告规范](#issue-报告规范)
- [安全漏洞报告](#安全漏洞报告)
- [国际化与本地化](#国际化与本地化)

---

## 行为准则

请保持友善、包容、专业。本项目面向中文开发者社区，请使用中文或英文交流，避免人身攻击、政治或不当言论。维护者有权删除违反规范的评论、PR、Issue。

---

## 我能帮什么忙

按上手难度从低到高：

| 难度 | 适合的贡献 |
|------|------------|
| 🟢 入门 | 文档错别字、补充注释、修复 Issue 中 `good first issue` 标签的任务 |
| 🟡 进阶 | 新增/改进 scoring、call_graph 算法，新增更多语言的 parser 支持 |
| 🟠 高级 | 优化 Cytoscape 性能、设计后端分布式架构、SQL 调优 |
| 🔴 专家 | 安全审计、性能基准、AI/LLM 集成优化、CI/CD 平台化 |

不确定从何开始？在 [Issues](https://github.com/moreg/codeArchaeology/issues) 找标有 `good first issue` 或 `help wanted` 的任务。

---

## 开发环境搭建

### 1. 必备工具

| 工具 | 版本 | 用途 |
|------|------|------|
| Git | 任意 | 版本控制 |
| Python | 3.9+ | 后端（推荐 3.11/3.12） |
| Node.js | 18+ | 前端 |
| Docker | 任意 | 一键启动后端（可选） |

### 2. 克隆与初始化

```bash
git clone https://github.com/moreg/codeArchaeology.git
cd codeArchaeology

# 初始化示例项目 git 历史（仅首次，会写入 38 个 commit）
cd sample-project
python setup-git-history.py
cd ..

# 后端
cd backend
python -m pip install -r requirements.txt
cp .env.example .env  # Windows: copy .env.example .env
uvicorn app.main:app --reload --port 8000

# 前端（新开终端）
cd frontend
npm install
npm run dev
```

打开 http://localhost:5173 ，浏览器应能看到代码宇宙图。

### 3. 验证环境

```bash
# 后端测试
cd backend && pytest tests/ -v

# 前端类型检查 + 构建
cd frontend && npm run typecheck && npm run build
```

三个命令都应**全绿**。如有问题，先看 [README 的常见问题](README.md#常见问题) 一节。

---

## 项目结构速览

```
code-archaeology/
├── backend/                    # FastAPI 后端
│   ├── app/
│   │   ├── core/               # 业务核心：scanner / parser / call_graph / scoring / llm
│   │   ├── api/                # REST + WebSocket 路由层
│   │   ├── models/             # SQLAlchemy 数据模型
│   │   └── main.py             # FastAPI 入口
│   ├── tests/                  # pytest 单测（64 用例）
│   ├── data/                   # SQLite 数据（git ignore）
│   ├── requirements.txt
│   └── Dockerfile
│
├── frontend/                   # React + TypeScript + Vite
│   ├── src/
│   │   ├── components/         # 5 大 UI 模块
│   │   ├── store/              # Zustand 全局状态
│   │   ├── api/                # 后端客户端
│   │   └── types/              # 全局 TypeScript 类型
│   ├── vite.config.ts
│   └── package.json
│
├── sample-project/             # 演示用祖传 Python 爬虫（故意保留"屎山"）
│
├── .github/workflows/ci.yml    # GitHub Actions CI
├── README.md
├── CONTRIBUTING.md             # 你正在看的这个
├── LICENSE
└── .gitignore
```

**关键约定**：
- 业务逻辑放 `app/core/`，HTTP/WebSocket 放 `app/api/`，数据契约放 `app/models/`
- 前端组件按业务域分目录，不按文件类型
- `sample-project/` 是**有意的反例**，请勿清理它的"丑代码"（它是评分系统的靶子）

---

## 开发流程

### 推荐的 Git 工作流

我们采用 **trunk-based** 的简化版：每个功能开一个短生命周期分支，PR 合入 `main`。

```bash
# 1. 同步最新 main
git checkout main
git pull origin main

# 2. 开新分支（feat/fix/docs/ci/chore 前缀 + 短描述）
git checkout -b feat/add-rust-parser
# 或
git checkout -b fix/scan-cross-drive-bug

# 3. 开发 + 写测试 + 跑本地检查（见下文）
# 4. 提交（遵循下面的 commit 规范）
git add -p
git commit -m "feat(parser): add rust language support via tree-sitter-rust"

# 5. 推送 + 开 PR
git push origin feat/add-rust-parser
# 然后在 GitHub 开 Pull Request
```

### 一次性本地检查

提交前请跑完三件套，**任一失败都不应提交**：

```bash
# 后端
cd backend
pytest tests/ -v --tb=short
python -c "from app.main import app"  # 确保 import 不报错

# 前端
cd frontend
npm run typecheck
npm run build
```

CI 会自动跑同样的检查，但本地先过能省一次 PR 迭代。

---

## 代码风格

### Python（后端）

| 项目 | 约定 |
|------|------|
| 格式化 | 暂未强制 ruff/black，但请保持 4 空格缩进、行长 ≤ 100、UTF-8 编码 |
| 类型注解 | 公开函数必须带 `typing` 注解；内部 helper 可省略 |
| 字符串 | 用 `pathlib.Path` 处理路径，不用 `os.path` 拼接；用 `datetime.now(timezone.utc)`，**不要用** `datetime.utcnow()` |
| 日志 | 用 `from ..utils.logger import get_logger`；**不要用** `print()` |
| 异常 | 路由层用 `HTTPException`，内部层向上抛；**不要** 把 `str(e)` 直接返回给客户端 |
| 数据库 | SQLAlchemy Session 走 `app.models.database` 的 `db_session()` 上下文管理器 |
| 异步 | 用 `asyncio.get_running_loop()`；**不要** `asyncio.get_event_loop()` |

### TypeScript / React（前端）

| 项目 | 约定 |
|------|------|
| 格式化 | 跟随 Prettier 默认（2 空格、分号、引号偏好 single） |
| 命名 | 组件 PascalCase、hook camelCase + `use` 前缀、类型/接口 PascalCase |
| 状态 | 跨组件用 Zustand store（`src/store/`），单组件内用 `useState` |
| 副作用 | 异步操作放 `useEffect` 或自定义 hook，**不要**在 render 体内发请求 |
| 错误 | 失败必须抛错给 UI，**不要** 静默降级到 mock（mock 仅在 `import.meta.env.DEV` 下生效） |
| 类型 | 任何 `any` 都需有 `// TODO: narrow this` 注释；新接口在 `src/types/` 定义 |
| 空值 | TS strict 模式，可能 `undefined` 的字段访问必须用 `?.` 或 `||` 兜底 |

### 不做的事

请勿在 PR 中包含：

- 任何对 `sample-project/` 的"美化"或清理（它是产品演示的一部分）
- 与本次变更无关的格式化（用 `git add -p` 精确 stage）
- `console.log` 调试代码（用 IDE debugger 或临时 `import.meta.env.DEV` 守卫）
- 未经讨论的依赖升级（`requirements.txt` / `package.json` 升级请单独开 PR）
- 任何密钥、`.env`、数据库 dump、SQLite `.db` 文件

---

## 测试要求

每个 PR 必须满足：

### 后端
- 新增/修改的 `app/core/*.py` 函数必须**有对应 pytest 用例**（在 `tests/test_*.py`）
- 修复 bug 时，先写一个能复现 bug 的失败测试，再修复（红 → 绿）
- 公共 API（`app/api/*.py` 的路由）建议加至少一个 happy path 测试
- 所有测试通过：`pytest tests/ -v` 必须 100% pass

### 前端
- 新增组件需要有最小可运行的 demo 或 story（可放在 `*.stories.tsx` 或 README 中）
- 修复 bug 时附复现步骤（issue 链接 + 修复前后对比）
- `npm run typecheck` 必须 0 错误
- `npm run build` 必须成功

### 不在 CI 范围但建议做
- 性能：单测 100 文件扫描 < 30s（参考 `sample-project/` 当前 ~5s）
- 可访问性：键盘可达性、aria 标签

---

## 提交规范

我们使用 **Conventional Commits** 1.0，commit message 格式：

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Type

| Type | 用途 |
|------|------|
| `feat` | 新功能 |
| `fix` | 修 Bug |
| `docs` | 仅文档 |
| `refactor` | 既不修 bug 也不加功能的代码改动 |
| `perf` | 性能优化 |
| `test` | 仅测试 |
| `chore` | 构建/工具/依赖/ci |
| `style` | 格式化（无逻辑改动） |
| `revert` | 回滚 |

### Scope（可选但建议）

后端：`parser` / `scanner` / `call_graph` / `scoring` / `git_analyzer` / `llm` / `api` / `models` / `db` / `security` / `docker` / `deps` 等  
前端：`components/UniverseMap` / `store` / `api` / `hooks/useCytoscape` / `types` / `styles` 等

### Subject
- 中文或英文皆可（保持一致即可）
- 不超过 72 字符
- 祈使句："add" 而不是 "added" 或 "adds"
- 首字母不大写、末尾不加句号

### 例子

```bash
feat(parser): add rust language support
fix(scanner): handle paths on different drives in relpath
docs(readme): clarify llm mode configuration
refactor(api): split _do_scan into single-purpose helpers
test(git_analyzer): explicitly close Repo to avoid Windows file lock
ci: add github actions workflow for backend and frontend
chore(deps): bump tree-sitter to 0.23 for python 3.12 support
```

### Breaking change
破坏性变更必须在 footer 加 `BREAKING CHANGE: <description>`，并在 subject 用 `!`：

```bash
feat(api)!: rename /api/scan response field "ok" to "status"
```

---

## Pull Request 流程

1. **开 PR 前**
   - 确认本地 `pytest` + `npm run typecheck` + `npm run build` 全过
   - 确认 commit message 符合规范
   - 如果 PR 超过 400 行 diff，请先在 Issue 里讨论方案

2. **PR 标题**
   - 与首个 commit 保持一致，或总结所有 commits 的核心变更
   - 同样遵循 Conventional Commits 格式

3. **PR 描述模板**（自动填充）
   ```markdown
   ## 变更说明
   - 改了什么、为什么

   ## 关联 Issue
   Closes #xxx

   ## 测试
   - 怎么测的、覆盖了哪些边界

   ## 截图（如有 UI 变更）
   ![](attachment)

   ## Checklist
   - [ ] pytest 全过
   - [ ] npm run typecheck 全过
   - [ ] npm run build 成功
   - [ ] 新增/修改的函数有测试
   - [ ] 无遗留的 `print()` / `console.log()` / `TODO` 注释
   - [ ] 无 commit 包含密钥或 .env
   ```

4. **Review 流程**
   - 维护者会在 3 个工作日内首次响应
   - 优先合并小 PR（< 200 行），大功能拆 PR
   - Squash merge 模式，最终 commit message 由 PR 标题决定

5. **合并后**
   - 分支自动删除
   - CI 会自动跑全量检查，详见 [Actions](https://github.com/moreg/codeArchaeology/actions)

---

## Issue 报告规范

### Bug 报告

请用以下结构：

```markdown
**环境**
- OS: Windows 11 / macOS 14 / Ubuntu 22.04
- Python: 3.12.3
- Node: 20.10.0
- 浏览器（如前端相关）: Chrome 120

**复现步骤**
1. ...
2. ...

**预期行为**
应该...

**实际行为**
实际...

**截图/日志**
（粘贴或拖拽）

**可能的原因**
（如果有想法）
```

### 功能建议

请用以下结构：

```markdown
**要解决的问题**
用户/开发者当前遇到什么痛点

**提议的方案**
（如果有想法）

**替代方案考虑**
（考虑过哪些其他方法）

**优先级**
- [ ] 阻断（核心功能不可用）
- [ ] 高（影响日常使用）
- [ ] 中（有 workaround）
- [ ] 低（nice to have）
```

---

## 安全漏洞报告

⚠️ **请勿在公开 Issue 中披露安全漏洞**。

请通过 GitHub Security Advisories 私下报告：
https://github.com/moreg/codeArchaeology/security/advisories/new

我们承诺：
- 24 小时内首次响应
- 7 天内评估严重性
- 修复后公开致谢（除非你要求匿名）

常见可关注的安全点（参考历史审计）：
- 路径遍历（`/api/scan` 接受任意 path → 需在白名单内）
- 异常信息泄露（`str(e)` 直接返回给客户端 → 改为通用错误码）
- SQL 注入（统一走 SQLAlchemy ORM 即可，**不要**拼接 f-string）
- 依赖漏洞（运行 `pip-audit` / `npm audit` 定期检查）

---

## 国际化与本地化

当前 UI 文案以中文为主，文档双语（中英）共存。

### 新增文案
- UI 字符串集中在 `frontend/src/` 各组件的常量中
- 如需新增 i18n key，请同时维护中英两个版本
- 错误提示简洁、用户可理解（不要直接给后端原始异常）

### 文档翻译
- 欢迎提交英文版 README/CONTRIBUTING
- 翻译请保留原文档段落结构，避免意译

---

## 路线图与功能请求

当前优先级（按社区需求调整）：

| 优先级 | 方向 | 欢迎 PR |
|--------|------|---------|
| P1 | VS Code / TRAE IDE 插件 | ✅ |
| P1 | 考古报告导出 PDF/HTML | ✅ |
| P2 | 多用户协作标注 | 待设计 |
| P2 | Rust / Go / C++ parser | ✅ |
| P3 | 时序图、依赖图 | 待设计 |

实施前请先开 Issue 讨论设计，避免重复劳动或方向偏差。

---

## 社区

- **GitHub Issues**: 一切技术问题、Bug、功能建议
- **GitHub Discussions**（即将开放）: 一般讨论、想法、Q&A
- **TRAE 大赛**: 见赛事官方群

---

## 许可证

提交代码即表示你同意按 [MIT License](LICENSE) 授权你的贡献。

---

**「代码考古学，欢迎每一位考古队员。」** 🏛️
