# 代码考古学 - 后端 (Code Archaeology Backend)

让接手"代码屎山"的开发者 30 秒看懂老代码的全貌、热点和历史。

## 功能

- **扫描项目**: 递归遍历目录, 用 tree-sitter 解析 Python/JS/TS/Java
- **调用图**: NetworkX 组装函数级调用关系, 暴露 Cytoscape JSON
- **Git 分析**: blame、log、shortlog、文件耦合度
- **屎山评分**: 5 维度 (圈复杂度/重复率/注释/作者集中度/测试覆盖) 0-100 分
- **LLM 故事**: OpenAI/Ollama/Mock 三种适配器, 生成函数故事与重构建议
- **WebSocket 进度**: 实时推送扫描进度

## 快速启动

### 本地开发

```bash
# 1. 安装依赖 (Python 3.9+)
pip install -r requirements.txt

# 2. 复制环境变量
cp .env.example .env

# 3. 启动服务
uvicorn app.main:app --reload --port 8000
```

打开 http://localhost:8000/docs 看 API 文档。

### Docker

```bash
docker compose up --build
```

服务运行在 http://localhost:8000

## API 一览

| Method | Path | 说明 |
|--------|------|------|
| POST | `/api/sample/load` | 加载内置示例项目 |
| POST | `/api/scan` | 扫描自定义路径 |
| GET | `/api/scan/{id}/status` | 扫描进度 |
| GET | `/api/scan/{id}/graph` | 调用图 |
| GET | `/api/scan/{id}/score` | 屎山评分 |
| POST | `/api/analyze/story` | 生成函数故事 |
| POST | `/api/analyze/refactor` | 生成重构建议 |
| WS | `/ws/scan/{scan_id}` | 实时进度推送 |

详见 [spec.md](../.trae/specs/build-code-archaeology-mvp/spec.md)。

## LLM 模式

通过 `LLM_MODE` 环境变量切换:
- `mock` (默认): 返回预置演示数据, 无外部依赖
- `openai`: 需要 `OPENAI_API_KEY`
- `ollama`: 需要本地 Ollama 服务运行

Mock 模式下, 所有 demo 流程都能跑通。

## 外部依赖

- **Python 3.9+**
- **Git**: 用于 GitPython 读取历史
- **Docker** (可选): 用于容器化部署
- **OpenAI API Key** (可选): 用于云端 LLM
- **Ollama** (可选): 用于本地 LLM

## 测试

```bash
pytest tests/ -v
```

## 演示模式

无 API Key 也能完整演示: 后端默认用 Mock LLM, 示例项目内置, 前端调用 `POST /api/sample/load` 即可启动完整链路。