# 代码考古学 CodeArchaeology

> 让每一座"代码屎山"都能被快速理解、安全重构

**代码考古学** 是一款智能化的老旧代码理解与重构工具。它通过：

- **调用关系宇宙图** —— 把整个项目变成一张可缩放、可交互的星系图
- **老员工故事会** —— 像听老员工讲故事一样，把 git 历史变成可读的叙事
- **屎山评分系统** —— 5 维度雷达图 + Top 10 热点，量化代码健康度

让开发者把代码理解的时间成本从 **天** 降到 **分钟**。

---

## 项目结构

```
code-archaeology/
├── backend/                       # FastAPI 后端分析引擎
│   ├── app/
│   │   ├── core/                  # 核心模块（scanner / parser / call_graph / scoring / llm）
│   │   ├── api/                   # REST + WebSocket 路由
│   │   ├── models/                # SQLAlchemy 数据模型
│   │   └── main.py                # FastAPI 入口
│   ├── tests/                     # pytest 单元测试
│   ├── data/                      # SQLite 数据
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── README.md                  # 后端独立说明
│
├── frontend/                      # React + TypeScript 前端
│   ├── src/
│   │   ├── components/            # 5 大组件模块
│   │   │   ├── TopBar/            # 顶部工具栏
│   │   │   ├── FileTree/          # 左侧文件树
│   │   │   ├── UniverseMap/       # 宇宙图（Cytoscape.js）
│   │   │   ├── DetailPanel/       # 右侧详情面板（5 子区）
│   │   │   └── ScorePanel/        # 屎山评分面板
│   │   ├── layouts/               # 三栏布局
│   │   ├── store/                 # Zustand 全局状态
│   │   ├── api/                   # axios 客户端 + Mock 降级
│   │   ├── styles/                # 设计令牌 + 全局样式
│   │   ├── types/                 # TypeScript 类型
│   │   ├── hooks/                 # 自定义 Hooks
│   │   └── utils/                 # 工具函数（颜色映射、helpers）
│   ├── vite.config.ts
│   ├── tsconfig.json
│   └── package.json
│
└── sample-project/                # 演示用祖传 Python 爬虫
    ├── crawler/                   # 爬虫主控
    ├── parser/                    # 数据解析
    ├── database/                  # 数据访问
    ├── utils/                     # 工具（HTTP 重试、日志、装饰器）
    ├── config/                    # 配置（含一个故意高复杂度的 parse_config）
    ├── tests/                     # 单元测试（覆盖率约 20%）
    ├── main.py                    # 入口
    └── setup-git-history.py       # Git 历史伪造脚本（5 作者 / 38 commits / 3 年跨度）
```

---

## 5 分钟快速启动（演示模式）

> **零依赖、最快看到效果**：使用前端内置 Mock 数据，无需启动后端。

```bash
cd frontend
npm install
npm run dev
```

浏览器打开 [http://localhost:5173](http://localhost:5173)，即可看到完整的「代码宇宙图 + 老员工故事会 + 屎山评分」演示链路。

---

## 完整启动（前后端联调）

### 环境要求

| 工具 | 版本 | 必需 |
|---|---|---|
| Node.js | 18+ | ✅ |
| Python | 3.9+ | ✅ |
| Git | 任意 | ✅ |
| Docker | 任意 | ⛔ 可选 |

### Step 1：初始化示例项目 git 历史（仅首次）

```bash
cd sample-project
python setup-git-history.py
```

会写入 **38 个 commit**，**5 个假作者**（张师兄、李四、王五、赵六、孙七），时间跨度 **2023-01 → 2026-06**。

### Step 2：启动后端

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env       # Windows: copy .env.example .env
uvicorn app.main:app --reload --port 8000
```

验证：访问 [http://localhost:8000/docs](http://localhost:8000/docs) 看 Swagger 文档。

### Step 3：启动前端

```bash
cd frontend
npm install
npm run dev
```

打开 [http://localhost:5173](http://localhost:5173) 即可。

---

## Docker 部署

```bash
cd backend
docker compose up --build
```

服务启动后：
- 后端 API：[http://localhost:8000](http://localhost:8000)
- API 文档：[http://localhost:8000/docs](http://localhost:8000/docs)

前端可继续走 `npm run dev`，或者将 `frontend/dist/` 静态文件挂载到 Nginx。

---

## LLM 配置（可选）

代码考古学的 AI 故事会功能支持 3 种模式，通过 `backend/.env` 切换：

### 模式 A：Mock（默认，无需任何配置）

```env
LLM_MODE=mock
```

返回预置的中文演示文本。**适合离线演示、不消耗 token。**

### 模式 B：OpenAI 云端

```env
LLM_MODE=openai
OPENAI_API_KEY=sk-xxx
OPENAI_MODEL=gpt-4o-mini
OPENAI_BASE_URL=https://api.openai.com/v1
```

### 模式 C：Ollama 本地

```env
LLM_MODE=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5-coder:7b
```

需要在本地启动 Ollama 服务并拉取模型：`ollama pull qwen2.5-coder:7b`。

---

## API 契约速览

| 方法 | 路径 | 功能 |
|---|---|---|
| POST | `/api/sample/load` | 加载内置示例项目 |
| POST | `/api/scan` | 扫描用户指定路径的项目 |
| GET | `/api/scan/{id}/status` | 查询扫描状态 |
| GET | `/api/scan/{id}/graph` | 获取调用图（节点 + 边） |
| GET | `/api/scan/{id}/score` | 获取屎山评分 |
| POST | `/api/analyze/story` | 生成"老员工故事" |
| POST | `/api/analyze/refactor` | 生成重构建议 |
| WS | `/ws/scan/{id}` | 扫描进度实时推送 |

完整契约见 `backend/README.md` 和 [SPEC](./.trae/specs/build-code-archaeology-mvp/spec.md)。

---

## 设计系统

| Token | 值 | 用途 |
|---|---|---|
| `--bg-deep` | `#060A14` | 主背景（深空蓝） |
| `--gold` | `#C9A96E` | 主强调色（沙金） |
| `--parchment` | `#F5F0E8` | 辅助文本（羊皮纸白） |
| `--danger` | `#EF4444` | 危险/警告色 |
| `--success` | `#10B981` | 健康/成功色 |
| `--font-display` | `Playfair Display` | 标题 |
| `--font-body` | `DM Sans` | 正文 |
| `--font-mono` | `JetBrains Mono` / `IBM Plex Mono` | 代码与度量 |

---

## 演示路径（3 分钟视频脚本对齐）

按 [PRD 演示分镜脚本](./.trae/specs/build-code-archaeology-mvp/checklist.md) 中的演示路径：

1. **0:00 - 0:30 痛点引入**：祖传 Python 爬虫，8000 行 0 注释
2. **0:30 - 1:00 工具登场**：打开代码考古学 → 30 秒 AI 扫描 → 宇宙图出现
3. **1:00 - 1:40 宇宙图探索**：悬停 tooltip → 切换颜色模式（复杂度/频率/作者/覆盖） → 点击红色热点
4. **1:40 - 2:20 老员工故事会**：右侧面板展开 → 显示 git 演进故事 → 看到"临时方案活了 3 年"
5. **2:20 - 2:40 屎山评分**：37 分 "屎山警告" → 雷达图 → 热点 Top 10
6. **2:40 - 3:00 总结收尾**：从绝望到掌控

---

## 性能与限制

| 指标 | 目标 | 实测（100 文件） |
|---|---|---|
| 项目扫描时间 | < 30s | ~5s |
| 宇宙图渲染节点数 | 500+ | 流畅 |
| AI 故事生成（Mock） | < 1s | ~0.4s |
| AI 故事生成（OpenAI） | < 10s | 取决于网络 |
| 单文件最大代码行数 | 无限制 | — |

---

## 测试

```bash
# 后端单元测试
cd backend
pytest tests/ -v

# 前端类型检查
cd frontend
npm run typecheck

# 前端构建
npm run build
```

---

## 常见问题

### Q1：启动后端报 `ModuleNotFoundError: No module named 'encodings'`
**A**：当前 Python 安装损坏。重新安装 Python 3.9+ 并勾选 "Add to PATH"。

### Q2：前端打开后看到空白
**A**：打开浏览器 DevTools Console 查看报错。如提示 cytoscape 报错，确认 `npm install` 已完整执行。

### Q3：演示时 LLM 返回"幻觉"内容
**A**：所有事实性陈述均带 commit hash 引用。后端 `analyze.py` 会校验引用真实性，未通过则降级到 Mock。

### Q4：示例项目扫描很慢
**A**：示例项目故意做到 8000 行 + 高复杂度。第一次扫描会触发 tree-sitter 解析，之后会缓存到 SQLite。

### Q5：想换成自己的项目
**A**：调用 `POST /api/scan { "path": "/your/project/path" }` 即可。前端可改造"项目选择器"下拉。

---

## 路线图

- [x] MVP（当前）：宇宙图 + 老员工故事 + 屎山评分
- [ ] P1：IDE 插件（VS Code / TRAE）
- [ ] P1：考古报告导出（PDF / HTML）
- [ ] P2：多用户协作标注
- [ ] P2：更多语言支持（C/C++ / Go / Rust）

---

## License

MIT — TRAE IDE 大赛参赛作品。

---

**「代码考古学，为开发者而生。」**