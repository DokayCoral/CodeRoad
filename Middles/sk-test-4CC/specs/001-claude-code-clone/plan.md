# Implementation Plan: Claude Code 核心功能复刻平台

**Branch**: `001-claude-code-clone` | **Date**: 2026-05-12 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-claude-code-clone/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

复刻开发一个模仿 Claude Code 核心功能的本地终端编程助手平台。用户通过自然语言与 AI 交互，AI 可调用文件读取/编辑/搜索和 Shell 命令执行等工具完成编码任务。目标是帮助理解 Claude Code 的工作原理。技术选型: Python 3.11+ CLI 应用，通过云端 API（Claude/OpenAI）接入 AI 模型，本地 JSON 文件存储会话历史。

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: anthropic SDK, openai SDK, prompt_toolkit, rich, pydantic, pyyaml, pytest
**Storage**: Local JSON files (sessions/) + YAML config (~/.claude-code-clone/config.yml)
**Testing**: pytest + pytest-mock
**Target Platform**: Cross-platform terminal (Windows/Linux/macOS)
**Project Type**: CLI application
**Performance Goals**: TTFT <2s (streaming), file read <3s (2000 lines), code search <5s (100k LOC), shell timeout 30s
**Constraints**: Single-user local tool, API-dependent (no offline mode), no database, no web UI
**Scale/Scope**: Single user, single active session, local filesystem only

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Simplicity First | ✅ PASS | Single project, no database, no web framework, minimal dependencies. Python stdlib + 5 core packages. |
| II. Clear Contracts | ✅ PASS | Tool contracts defined in `contracts/` for all 6 tools (Read, Write, Edit, Grep, Glob, Bash). CLI contract via `--help`. |
| III. Test-Driven Development | ✅ PASS | TDD cycle enforced per user story. Contract tests in `tests/contract/`, integration tests in `tests/integration/`, unit tests in `tests/unit/`. |
| IV. Documentation as Code | ✅ PASS | `research.md`, `data-model.md`, `quickstart.md`, `contracts/` all in version control alongside code. |
| V. Continuous Validation | ✅ PASS | 5 user stories independently testable. Checkpoints after each story phase. |

**Gate Result**: ALL PASS — No violations requiring justification in Complexity Tracking.

## Project Structure

### Documentation (this feature)

```text
specs/001-claude-code-clone/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── tool-read.md
│   ├── tool-write.md
│   ├── tool-edit.md
│   ├── tool-grep.md
│   ├── tool-glob.md
│   └── tool-bash.md
└── tasks.md             # Phase 2 output (/speckit-tasks command)
```

### Source Code (repository root)

```text
src/
├── __init__.py
├── models/
│   ├── __init__.py
│   ├── session.py       # Session entity
│   ├── message.py       # Message entity
│   ├── tool_call.py     # ToolCall entity
│   └── task.py          # Task entity
├── tools/
│   ├── __init__.py
│   ├── registry.py      # Tool registry + permission levels
│   ├── read.py          # Read tool
│   ├── write.py         # Write tool
│   ├── edit.py          # Edit tool
│   ├── grep.py          # Grep search tool
│   ├── glob.py          # Glob pattern tool
│   └── bash.py          # Shell execution tool
├── services/
│   ├── __init__.py
│   ├── ai_service.py    # AI API integration (anthropic/openai)
│   ├── session_service.py
│   ├── context_service.py  # Project context loading
│   ├── stream_service.py   # Streaming response handling
│   └── task_service.py
├── cli/
│   ├── __init__.py
│   ├── app.py           # Main CLI entry point
│   ├── input_handler.py # prompt_toolkit input
│   └── renderer.py      # rich Markdown rendering
└── config.py            # Configuration management

tests/
├── __init__.py
├── contract/
│   ├── test_tool_read.py
│   ├── test_tool_write.py
│   ├── test_tool_edit.py
│   ├── test_tool_grep.py
│   ├── test_tool_glob.py
│   └── test_tool_bash.py
├── integration/
│   ├── test_session_flow.py
│   └── test_tool_pipeline.py
└── unit/
    ├── test_models.py
    ├── test_registry.py
    └── test_config.py
```

**Structure Decision**: Single project (Option 1) — CLI application with no frontend/backend split. Tools, services, models, and CLI rendering are cleanly separated into modules within a single Python package.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No violations. All five constitutional principles pass without requiring justification.
