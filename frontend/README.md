# 代码考古学 · Frontend

> CodeArchaeology — 让接手"祖传代码"的人，在 30 秒内理解全貌、热点与历史。

## 技术栈

- **React 18** + **TypeScript 5**（严格模式）
- **Vite 5** 构建 + 开发服务器
- **Zustand** 全局状态管理
- **Cytoscape.js** + **cose-bilkent** 宇宙图布局
- **Monaco Editor** 只读代码预览
- **Chart.js** + **react-chartjs-2** 评分雷达图
- **Axios** API 客户端
- **CSS Modules** 组件级样式

## 启动

```bash
cd code-archaeology/frontend
npm install
npm run dev
```

默认运行在 <http://localhost:5173>。

| 命令 | 说明 |
| --- | --- |
| `npm run dev` | 启动 Vite dev server（端口 5173） |
| `npm run build` | 类型检查 + 生产构建 |
| `npm run preview` | 预览生产构建产物 |
| `npm run typecheck` | 仅运行 TypeScript 类型检查 |

## Mock 模式（无需后端）

前端自带完整 mock 数据。`VITE_USE_MOCK=true` 时强制使用 mock，否则在 API 不可达时自动降级到 mock。

```bash
# 强制使用 mock
VITE_USE_MOCK=true npm run dev
```

或在后端未启动时直接 `npm run dev`，前端会自动 fallback，**保证 demo 永不崩溃**。

## API 代理

`vite.config.ts` 已配置：
- `/api/*` → `http://localhost:8000`
- `/ws/*` → `ws://localhost:8000`（启用 WebSocket 转发）

后端启动后无需修改任何前端代码即可联调。

## 目录结构

```
src/
├── api/                 # API 客户端 + mock 数据
│   ├── client.ts        # axios 实例 + 6 个 API + WebSocket
│   └── mockData.ts      # 30 nodes + 50 edges + 评分/故事/重构
├── components/          # 业务组件（每个组件独立 .module.css）
│   ├── TopBar/          # 顶部 48px 操作栏
│   ├── FileTree/        # 左侧 240px 文件树
│   ├── UniverseMap/     # 中间宇宙图 + Tooltip + Legend + Info
│   ├── DetailPanel/     # 右侧 320px 节点详情
│   └── ScorePanel/      # 屎山评分面板
├── hooks/
│   └── useCytoscape.ts  # Cytoscape 实例化 + 交互封装
├── layouts/
│   └── ThreeColumnLayout.tsx  # 三栏布局
├── store/
│   └── useAppStore.ts   # Zustand 全局状态
├── styles/
│   ├── tokens.css       # 设计令牌（颜色/字体/间距/阴影）
│   └── global.css       # 全局样式
├── types/
│   └── index.ts         # 全部 TypeScript 类型
├── utils/
│   └── colorMode.ts     # 颜色模式 + 评级 + 工具函数
├── App.tsx              # 应用入口（启动时 loadSample）
└── main.tsx             # React 18 createRoot
```

## 关键组件 Props / State

### `useAppStore` (Zustand)
| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `scanId` | `string \| null` | 当前扫描 ID |
| `projectName` | `string` | 项目名（显示在 TopBar） |
| `viewLevel` | `'file' \| 'module' \| 'function'` | 当前视图层级 |
| `colorMode` | `'complexity' \| 'frequency' \| 'author' \| 'test_coverage'` | 颜色模式 |
| `selectedNode` | `GraphNode \| null` | 选中的节点 |
| `searchKeyword` | `string` | 全局搜索关键字 |
| `scanProgress` | `number` | 扫描进度（已完成文件数） |
| `scanStatus` | `'idle' \| 'scanning' \| 'done' \| 'error'` | 扫描状态 |
| `graphData` | `GraphData \| null` | 调用图 |
| `scoreData` | `ScoreData \| null` | 评分数据 |
| `activeTab` | `'detail' \| 'score'` | 右侧面板 Tab |

### `<TopBar />`
- Props: `onExportPNG?: () => void`
- 状态: 来自 store (`projectName`, `viewLevel`, `colorMode`, `searchKeyword`, `scoreData`, `scanProgress` 等)
- 行为: 切换项目、切换视图层级、切换颜色模式、Ctrl+K 搜索、导出 PNG

### `<FileTree />`
- 无 Props
- 状态: 内部 `search` / `activeLangs` / `expanded`（持久化到 localStorage）
- 行为: 树形展开折叠、文件搜索、语言过滤、点击文件 → `setSelectedNode`

### `<UniverseMap />`
- 无 Props（所有交互通过 store）
- 子组件: `MapTooltip` / `MapLegend` / `MapInfo`
- 交互: 单击选节点、双击背景取消、滚轮缩放 0.2x-3x、Shift 框选、拖拽节点

### `<DetailPanel />`
- 无 Props
- 子区块: 概览 / 老员工故事会 / 代码预览（Monaco） / 重构建议
- Tab 切换: `detail` ↔ `score`（与 `<ScorePanel />` 互斥渲染）

### `<ScorePanel />`
- 无 Props
- 区块: 大数字 + 评级 / 五维雷达图 / 维度详情 / 热点 Top 10 列表
- 交互: 点击热点 → 跳回 Detail Tab + 选中节点

### `<ThreeColumnLayout />`
- Props: `topBar` / `left` / `center` / `right`（均为 ReactNode）
- 行为: 左/右面板折叠动画（200ms），< 1280px 显示警告提示

## 4 种颜色模式映射

| 模式 | 颜色逻辑 |
| --- | --- |
| 圈复杂度 | `≤5` 绿 → `6-10` 黄绿 → `11-20` 黄 → `21-30` 橙 → `>30` 红 |
| 修改频率 | 三档蓝色（最近 / 中期 / 冷代码） |
| 作者分布 | 按 `author` 字符串 hash 到 10 色调色板 |
| 测试覆盖 | 绿（有覆盖）/ 红（无覆盖） |

## 4 种边类型映射

| call_type | 样式 |
| --- | --- |
| `direct` | 实线 #888888 + 三角箭头 + 宽度按 call_count 1-4px |
| `indirect` | 虚线 #CCCCCC 1px |
| `callback` | 点线 #FF8C00 2px + 三角箭头 |
| `dataflow` | 实线 #4A90D9 + 三角箭头 + 宽度按 call_count 1-3px |

## 节点形状映射

| 层级 | 形状 | 大小 |
| --- | --- | --- |
| `file` | ellipse | `20 + √line_count * 3` → 20-80px |
| `module` | hexagon | `30 + complexity * 1.5` → 30-100px |
| `function` | round-rectangle | `12 + complexity * 0.4` → 12-22px |

## 后端 API 对齐

前端调用以下端点（通过 Vite 代理转发到 `http://localhost:8000`）：

| Method | Path | 说明 |
| --- | --- | --- |
| `POST` | `/api/sample/load` | 加载示例项目，返回 scan_id |
| `GET` | `/api/scan/{id}/status` | 查询扫描进度 |
| `GET` | `/api/scan/{id}/graph?level=&color_mode=` | 获取调用图 |
| `GET` | `/api/scan/{id}/score` | 获取屎山评分 |
| `POST` | `/api/analyze/story` | 请求体 `{ scan_id, node_id }` → AI 故事 |
| `POST` | `/api/analyze/refactor` | 请求体 `{ scan_id, node_id }` → 重构建议 |
| `WS` | `/ws/scan/{scan_id}` | 扫描进度推送（`{ type: "progress" \| "complete" \| "error", ... }`） |

所有 API 在后端不可达时**自动降级到 mock**。

## 键盘快捷键

| 快捷键 | 行为 |
| --- | --- |
| `Ctrl + K` / `Cmd + K` | 聚焦搜索框 |
| `Esc` | 清空搜索 |
| `Shift + 拖拽` | Cytoscape 框选 |
| 双击背景 | 取消节点选择 |
| 滚轮 | 缩放画布（0.2x - 3x） |

## 可访问性

- 所有交互按钮带 `aria-label` / `aria-pressed` / `aria-selected`
- 键盘可导航（Tab + Enter / Space）
- `:focus-visible` 沙金描边
- 暗色高对比文本（WCAG AA）

## 浏览器要求

Chrome / Firefox / Edge 最新两个版本（>= 2023）。
