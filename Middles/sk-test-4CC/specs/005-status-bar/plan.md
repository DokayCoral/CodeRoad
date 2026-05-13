# Implementation Plan: 固定状态栏

**Branch**: `005-status-bar` | **Date**: 2026-05-12 | **Spec**: [spec.md](./spec.md)

## Summary

在对话界面底部添加一行固定状态栏，显示消息数、token 数、会话 ID 等关键信息。使用 Rich Panel 渲染，每次 AI 回复后更新。

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: rich (已有)
**Storage**: N/A
**Testing**: 手动验证
**Target Platform**: Cross-platform terminal
**Project Type**: CLI application (已有)

## Constitution Check

| Principle | Status |
|-----------|--------|
| I. Simplicity First | ✅ PASS — 新增 1 个渲染函数 + 1 处调用 |
| II-V | ✅ N/A / PASS |

**Gate Result**: ALL PASS

## Source Code Changes

```text
src/cli/renderer.py    # 新增 render_status_bar() 函数
src/cli/app.py         # 每次 AI 回复后调用 render_status_bar()
```

## Implementation Steps

1. 在 `renderer.py` 中添加 `render_status_bar(session)` 函数，用 Rich Panel 渲染一行状态信息
2. 在 `app.py` 的对话循环中，每次 AI 回复完成后调用 `render_status_bar()`
3. 状态栏内容：消息数 | 估算 token 数 | 会话 ID 缩略 | 压缩阈值
