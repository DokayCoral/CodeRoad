# Research: Claude Code 核心功能复刻平台

**Feature**: 001-claude-code-clone
**Date**: 2026-05-12

## 1. 编程语言选择

**Decision**: Python 3.11+

**Rationale**:
- 与 AI SDK（Anthropic SDK、OpenAI SDK）的 Python 首发支持和最佳文档匹配
- Rich 生态：rich/textual 提供出色的终端 UI，prompt_toolkit 提供交互式输入
- 快速原型开发周期，符合学习平台的目标
- 跨平台支持（Windows/Linux/macOS）无需额外配置

**Alternatives considered**:
- Node.js/TypeScript: AI SDK 支持良好，但进程管理（Shell 工具）和文件系统权限控制不如 Python 直观
- Go: 性能优秀但 AI SDK 生态不如 Python 成熟，终端 UI 库选择有限
- Rust: 过于重量级，学习曲线陡峭，不利于快速迭代

## 2. AI 模型接入 SDK

**Decision**: anthropic SDK (主) + openai SDK (备)，通过抽象层统一

**Rationale**:
- 用户学习目标是理解 Claude Code 原理，优先使用 Claude API
- OpenAI API 作为可选替代，通过配置切换（FR-014 要求）
- 抽象层让工具定义与模型提供商解耦

**Alternatives considered**:
- 仅用 OpenAI SDK: 不符合"模仿 Claude Code"的学习目标
- LangChain: 过度抽象，不符合 Simplicity First 原则

## 3. 终端 UI 框架

**Decision**: prompt_toolkit (输入) + rich (渲染)

**Rationale**:
- prompt_toolkit: 成熟的终端输入库，支持多行输入、历史记录、自动补全、按键绑定
- rich: Markdown + 语法高亮渲染，流式输出支持（Live update），Panel/Layout 组件
- 两者组合是 Python CLI 工具的行业标准（如 pgcli、http-prompt）

**Alternatives considered**:
- textual: 全功能 TUI 框架但过于重量级，更适合全屏应用而非行式对话界面
- blessings/blessed: 终端控制过于底层
- 纯 print: 无法实现流式 Markdown 渲染和交互式输入体验

## 4. 会话存储格式

**Decision**: JSON 文件（按日期组织）+ YAML 配置文件

**Rationale**:
- Simplicity First: 无需数据库，直接文件系统存储
- JSON 易于序列化/反序列化，人类可读可调试
- 按日期分目录组织会话历史 (`sessions/YYYY-MM-DD/<session-id>.json`)
- 单一用户本地工具，无需并发控制

**Alternatives considered**:
- SQLite: 查询能力更好但增加复杂度，且会话通常按时间线性访问
- Markdown 文件: Claude Code 的实际格式，但解析更复杂，JSON 更易于程序处理

## 5. 流式响应实现

**Decision**: SSE (Server-Sent Events) 事件流解析 + rich Live 组件实时渲染

**Rationale**:
- Anthropic/OpenAI SDK 均原生支持 streaming 迭代器
- 解析 token stream → 累积 Markdown 行 → rich Live 渲染增量更新
- 首个 token 延迟 <2s 由 SDK 内置的超时+重试机制保证

## 6. 工具执行与安全模型

**Decision**: 工具注册表 + 权限分级 + 子进程沙箱

**Rationale**:
- 工具定义为 Python dataclass/pydantic model，含 name/parameters/permission_level
- 权限级别: `read` (自动) / `write` (确认) / `shell_read` (自动) / `shell_write` (确认)
- Shell 命令通过 subprocess.run() 执行，30s 超时，禁止 `shell=True` 模式（防注入）
- 危险命令黑名单检查（rm -rf、format、mkfs 等）作为附加保护层

## 7. 项目结构模式

**Decision**: 单一 Python package + src layout

**Rationale**:
- 终端 CLI 应用，单项目结构最简洁
- src/ 下按功能模块划分: models/, tools/, services/, cli/
- 符合 Constitution I (Simplicity First) 原则

## Summary of All Tech Choices

| Category | Decision |
|----------|----------|
| Language | Python 3.11+ |
| AI SDK | anthropic + openai (abstracted) |
| Terminal UI | prompt_toolkit + rich |
| Storage | JSON files + YAML config |
| Streaming | SDK native streaming + rich Live |
| Shell | subprocess.run (no shell=True) |
| Testing | pytest + pytest-mock |
| Linting | ruff (format + lint) |
| Package mgmt | uv / pip |
