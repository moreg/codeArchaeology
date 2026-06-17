# -*- coding: utf-8 -*-
"""
app.core.prompts — Prompt 模板
===============================
"""

STORY_PROMPT = """你是一名资深的「代码考古学家」，专门研究遗留代码的历史。
请基于以下真实数据, 撰写一段 200-400 字的函数故事:

## 函数信息
- 函数名: {function_name}
- 所属文件: {file_path}
- 起始行: {start_line} - 结束行: {end_line}
- 代码行数: {line_count}
- 圈复杂度: {complexity}
- 所属类: {class_name}

## 函数源码
```python
{code}
```

## Git Blame (每行最后修改者)
{blame}

## 提交历史 (最近 10 条)
{timeline}

## 调用关系 (被谁调用, 调用了谁)
{callers}
{callees}

## 输出要求
请输出一段 JSON (用 ```json 包裹), 包含以下字段:
1. summary: 一句话故事摘要, 不超过 50 字
2. timeline: 时间线数组, 每条包含 commit_hash, date, author, message 字段
3. narrative: 200-400 字的叙述性文本, 引用 commit hash, 描述函数演进与历史背景
4. risks: 风险点数组, 每个元素是字符串

## 重要约束
- 所有事实必须引用 commit hash, 严禁编造
- 无法考证时明确标注「无法考证」
- 不要输出 markdown 标题, 直接输出 JSON
"""


REFACTOR_PROMPT = """你是一名资深架构师, 专门接手屎山代码做重构。
请基于以下真实数据, 给出一份可操作的重构方案:

## 函数信息
- 函数名: {function_name}
- 所属文件: {file_path}
- 起始行: {start_line} - 结束行: {end_line}
- 代码行数: {line_count}
- 圈复杂度: {complexity}
- 圈复杂度评级: {cc_rating}

## 函数源码
```python
{code}
```

## 相关上下文
- 调用方: {callers}
- 被调用方: {callees}
- 同文件内其他函数: {siblings}

## 输出要求
请输出 JSON (用 ```json 包裹), 包含以下字段:
1. suggestion: 一句话重构建议, 不超过 60 字
2. priority: "high" | "medium" | "low"
3. problems: 问题列表, 每条描述一个具体的代码异味
4. plan: 重构步骤数组, 按顺序排列, 每步可执行
5. diff: 一个 unified diff 字符串, 展示重构前后的对比
6. estimated_reduction: 预计代码行减少百分比, 如 "60%"

## 重要约束
- diff 必须是合法的 unified diff 格式, 以 "--- a/..." 和 "+++ b/..." 开头
- 引用具体的行号和代码片段
- 不要输出 markdown 标题, 直接输出 JSON
"""