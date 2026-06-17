<!--
感谢你提交 PR！请完成以下检查项，节省 review 周期。
详细的贡献流程见 CONTRIBUTING.md。
-->

## 变更说明

<!-- 用 1-3 句话说明这次 PR 改了什么、为什么。 -->

-

## 关联 Issue

<!-- 用了关键词 Closes/Resolves/Fixes/Refs 触发自动关闭。留空表示无需关闭任何 issue。 -->

- Closes #

## 改动类型

请勾选（多选）：

- [ ] 🐛 Bug 修复（non-breaking change 修复问题）
- [ ] ✨ 新功能（non-breaking change 添加能力）
- [ ] 💥 破坏性变更（fix or feature that would cause existing functionality to change）
- [ ] 📝 文档 / 仅文字
- [ ] ♻️ 重构（无功能变更）
- [ ] ⚡ 性能优化
- [ ] ✅ 测试（加测试或修正现有测试）
- [ ] 🔧 工具 / 构建 / CI
- [ ] ⬆️ 依赖升级

## 涉及模块

请勾选（多选）：

- [ ] backend/app/core
- [ ] backend/app/api
- [ ] backend/app/models
- [ ] backend/tests
- [ ] backend/Dockerfile / requirements.txt
- [ ] frontend/src/components
- [ ] frontend/src/store / api / hooks
- [ ] frontend/src/types
- [ ] frontend/public
- [ ] .github（CI / 模板）
- [ ] docs（README / CONTRIBUTING / CoC / LICENSE）
- [ ] sample-project

## 测试

<!-- 描述你如何测试这次变更。 -->

- [ ] 写了新测试
- [ ] 改了现有测试
- [ ] 手动验证过，步骤：___
- [ ] 不需要测试（请说明原因）

### 跑过的命令

<!-- 把本地跑过的命令输出粘贴过来，或勾选确认 -->

- [ ] `cd backend && pytest tests/ -v` —— 全过
- [ ] `cd backend && python -c "from app.main import app"` —— 无 import 错误
- [ ] `cd frontend && npm run typecheck` —— 0 错误
- [ ] `cd frontend && npm run build` —— 成功
- [ ] 启服务后端 + 前端，冒烟一遍主流程

## UI 变更

<!-- 如果改了 UI，必须提供截图或录屏。 -->

- [ ] 包含 before/after 截图
- [ ] 包含录屏（如涉及交互）
- [ ] 包含 design / 视觉对比说明
- [ ] 无 UI 变更

## Breaking Change 说明

<!-- 如果勾选了 "破坏性变更"，必须在此说明影响范围、迁移路径。 -->

## 检查清单

- [ ] commit message 遵循 [Conventional Commits](https://www.conventionalcommits.org/)（如 `feat(api): add rate limiting`）
- [ ] PR 标题遵循 Conventional Commits
- [ ] 公共 API 改了的话更新了 README / backend/README
- [ ] 没引入 `print()` / `console.log()` / `TODO` 调试代码
- [ ] 没引入 `console.log` 暴露的密钥 / token / 用户数据
- [ ] 没在 sample-project 里改"演示用的丑代码"
- [ ] 没把 `.env` / `*.db` / `node_modules` / `dist` 误提交
- [ ] 我已阅读并遵守 [CONTRIBUTING.md](../../blob/main/CONTRIBUTING.md) 和 [CODE_OF_CONDUCT.md](../../blob/main/CODE_OF_CONDUCT.md)

## 截图 / 录屏

<!-- 粘贴图片或拖拽到评论区。 -->

| Before | After |
|--------|-------|
|  |  |

## 维护者 Review 备注

<!-- Reviewer 填。 -->
