# Implementation Plan: 终端交替屏幕隔离体验

**Branch**: `002-clean-startup-screen` | **Date**: 2026-05-12 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/002-clean-startup-screen/spec.md`

## Summary

使用 ANSI 交替屏幕缓冲区（alternate screen buffer）替代 `console.clear()`，实现类似 vim/less/htop 的"新窗口"隔离体验。启动时切换到交替屏幕，退出时完全恢复原终端内容。撤回之前 `console.clear()` 的实现。

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: 无需新增依赖（Python 标准库 `sys.stdout.write` + ANSI 转义序列，rich 的 `console.clear()` 作为降级方案）
**Storage**: N/A
**Testing**: 手动验证（自动化测试无法验证终端显示状态）
**Target Platform**: Cross-platform terminal (Windows Terminal, CMD Win10+, macOS Terminal, GNOME Terminal)
**Project Type**: CLI application (已有)
**Performance Goals**: 交替屏幕切换 <50ms
**Constraints**: 异常退出时也必须恢复屏幕（atexit + signal handler）

## Constitution Check

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Simplicity First | ✅ PASS | 仅需 ANSI 转义序列 + atexit 注册，约 20 行代码 |
| II. Clear Contracts | ✅ N/A | 无新接口 |
| III. Test-Driven Development | ✅ PASS | 手动验证（终端渲染无法自动化） |
| IV. Documentation as Code | ✅ PASS | Plan + spec 更新记录变更 |
| V. Continuous Validation | ✅ PASS | 独立功能，可单独验证 |

**Gate Result**: ALL PASS

## Project Structure

### Documentation

```text
specs/002-clean-startup-screen/
├── plan.md              # This file (alternate screen buffer approach)
├── spec.md              # Updated specification
└── checklists/requirements.md
```

### Source Code Changes

```text
src/cli/app.py           # 撤回 console.clear()，替换为 alternate screen buffer
                         # - main(): 进入交替屏幕
                         # - 注册 atexit + signal handler: 退出时恢复屏幕
                         # - 检测终端能力，不支持时降级为 console.clear()
```

## Implementation Steps

1. 撤回现有的 `console.clear()` 调用
2. 在 `main()` 开头写入 ANSI `\033[?1049h` 进入交替屏幕
3. 注册 `atexit.register()` 写入 `\033[?1049l` 退出交替屏幕
4. 注册 `signal.signal(SIGINT, ...)` 确保 Ctrl+C 时也恢复屏幕
5. 添加终端能力检测（`sys.stdout.isatty()`），非交互模式或管道时跳过
6. 交替屏幕不支持时降级使用 `console.clear()`

## Complexity Tracking

No violations.
