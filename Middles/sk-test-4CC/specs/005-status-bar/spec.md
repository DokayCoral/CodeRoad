# Feature Specification: 固定状态栏

**Feature Branch**: `005-status-bar`  
**Created**: 2026-05-12  
**Status**: Draft  
**Input**: User description: "系统应该在界面上固定占用一部分，以展示一些相关信息。比如当前上下文长度。"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - 查看固定状态栏信息 (Priority: P1)

作为一名开发者，在 Code Clone 会话中，我希望屏幕底部始终有一个固定区域展示关键状态信息（如当前上下文 token 数、消息数量、会话名称等），以便随时了解系统状态而不需要手动查询。

**Why this priority**: 状态栏是终端应用的标配 UI 模式（类比 vim 状态栏、htop 顶栏），提供持续可见的关键信息，帮助用户理解系统当前状态。

**Independent Test**: 启动会话，观察屏幕底部是否有固定状态栏。发送多条消息后，验证状态栏中的消息数和 token 数实时更新。

**Acceptance Scenarios**:

1. **Given** 用户在对话界面中, **When** 查看屏幕底部，**Then** 固定的状态栏始终可见，不被对话内容覆盖
2. **Given** 用户发送了一条消息并获得 AI 回复, **When** 对话完成，**Then** 状态栏中的消息数和 token 数更新为最新值
3. **Given** 用户滚动查看历史对话, **When** 滚动屏幕，**Then** 状态栏始终固定在底部不随内容滚动

---

### Edge Cases

- 终端窗口非常窄时（<60 字符宽），状态栏内容应截断而非换行
- 终端窗口调整大小时，状态栏应保持在底部正确位置
- 当状态栏内容过长时，应优先显示最重要的信息（token 数 > 消息数 > 其他）

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: 系统必须在对话界面底部保留一行固定状态栏，不被对话内容覆盖
- **FR-002**: 状态栏必须显示当前会话的消息数量和估算 token 数
- **FR-003**: 状态栏必须在每次 AI 回复完成后自动更新为最新值
- **FR-004**: 状态栏必须在视觉上与对话区域区分开（如反色、分隔线或不同背景色）

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 状态栏在 100% 的对话回合中始终可见且信息正确
- **SC-002**: 状态栏更新延迟 <100ms（在 AI 回复完成后的 100ms 内更新）

## Assumptions

- 终端支持至少 24 行高度（状态栏占用 1 行不影响正常使用）
- 状态栏内容的计算已经在现有代码中实现（estimate_session_tokens 等）
