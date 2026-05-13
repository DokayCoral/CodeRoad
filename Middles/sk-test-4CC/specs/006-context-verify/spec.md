# Feature Specification: 上下文管理可视化与验证

**Feature Branch**: `006-context-verify`  
**Created**: 2026-05-12  
**Status**: Draft  
**Input**: User description: "完善一下上下文管理功能，并且要给出我可视化或者可检验的验证方法。"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - 使用 /context 命令检查上下文状态 (Priority: P1)

作为一名开发者，我希望能随时在对话中输入 `/context` 命令来查看当前会话的详细上下文信息（消息数、token 估算、压缩状态、会话文件路径、项目上下文等），以便确认上下文管理功能是否正常工作。

**Why this priority**: 提供一个即时可用的检查命令，是验证所有上下文管理功能的基础能力。

**Independent Test**: 启动对话，发送几条消息后输入 `/context`，验证返回详细的上下文状态报告。

**Acceptance Scenarios**:

1. **Given** 用户在对话中, **When** 输入 `/context`，**Then** 显示一份结构化的上下文状态报告，包含：消息数量、估算 token 数、是否触发过压缩、会话存储路径、已加载的项目上下文信息
2. **Given** 对话尚未开始（刚进入会话选择界面）, **When** `/context` 命令不可用，**Then** 这不适用——`/context` 仅在对话中有效

---

### User Story 2 - 查看上下文事件日志 (Priority: P1)

作为一名开发者，我希望平台自动将上下文相关事件（会话保存、加载、压缩触发、项目上下文加载）记录到本地日志文件，以便在退出平台后能回溯检查上下文管理的执行情况。

**Why this priority**: 日志文件提供了独立于平台界面的持久化验证手段，用户可以在任意时间查看历史行为。

**Independent Test**: 进行一次包含多轮对话、退出再重启恢复会话的操作，然后查看 `~/.claude-code-clone/context.log` 文件，验证其中记录了关键事件。

**Acceptance Scenarios**:

1. **Given** 用户完成一次对话后退出, **When** 查看 `~/.claude-code-clone/context.log`，**Then** 日志中包含 "SESSION_SAVED" 事件，记录了消息数和 token 数
2. **Given** 用户重启平台并恢复之前的会话, **When** 查看日志文件，**Then** 日志中包含 "SESSION_LOADED" 事件，记录了会话 ID 和恢复的消息数
3. **Given** 对话长度接近上下文窗口 70%, **When** 压缩被触发，**Then** 日志中包含 "CONTEXT_COMPRESSED" 事件，记录了压缩前后的消息数和 token 数

---

### User Story 3 - 状态栏显示上下文关键指标 (Priority: P2)

作为一名开发者，我希望状态栏能持续显示上下文的实时数据（当前消息数、估算 token 数、token 占压缩阈值的百分比），以便在对话过程中随时感知上下文状态，无需执行额外命令。

**Why this priority**: 状态栏已在 spec 005 中实现基础版本，本需求在其基础上增加更多上下文相关的可视化信息，让用户无需主动查询就能跟踪上下文状态。

**Independent Test**: 进行多轮对话，观察状态栏中的数字是否随每次回复更新。当 token 数接近压缩阈值时，观察百分比变化。

**Acceptance Scenarios**:

1. **Given** 用户在对话中, **When** 每次 AI 回复完成，**Then** 状态栏更新消息数和 token 数
2. **Given** token 数超过压缩阈值 70%, **When** 压缩发生，**Then** 状态栏数字显著下降（压缩前后的差异可见）

---

### User Story 4 - 项目上下文加载确认 (Priority: P2)

作为一名开发者，我希望启动平台进入对话时能明确看到系统加载了哪些项目上下文信息（来自哪个文件、检测到什么技术栈），以便确认上下文加载功能正确工作。

**Why this priority**: 项目上下文是 Claude Code 的核心功能之一，用户在对话开始时应能确认 AI 是否获取了正确的项目背景。

**Independent Test**: 创建一个包含明确指令的 CLAUDE.md 文件，启动平台进入对话，观察启动信息是否包含项目上下文摘要。

**Acceptance Scenarios**:

1. **Given** 项目根目录存在 `CLAUDE.md`, **When** 用户进入对话，**Then** 显示"已加载项目上下文: CLAUDE.md (XX 字符)"，以及检测到的技术栈
2. **Given** 项目根目录不存在 `CLAUDE.md`, **When** 用户进入对话，**Then** 显示"未检测到项目配置文件，AI 将使用通用规则"

---

### User Story 5 - 使用命令主动管理上下文 (Priority: P1)

作为一名开发者，我希望通过命令主动控制对话上下文——清除历史、手动压缩、回退消息、固定重要信息、刷新项目配置，以便在对话过程中灵活调整 AI 的上下文窗口。

**Why this priority**: 上下文控制是"上下文管理"的核心价值——用户不应只能被动观察，而应能主动干预。

**Independent Test**: 在对话中依次测试 `/clear`（确认消息清空但项目上下文保留）、`/compress`（确认 token 数下降）、`/pin`（确认固定消息在压缩后保留）等命令。

**Acceptance Scenarios**:

1. **Given** 用户有多轮对话历史, **When** 输入 `/clear`，**Then** 对话历史被清空，但项目上下文和任务列表保留
2. **Given** 对话中固定了一条消息, **When** 触发压缩，**Then** 固定消息在压缩后依然存在于对话中
3. **Given** 用户修改了 CLAUDE.md, **When** 输入 `/reload`，**Then** 系统重新加载项目上下文并显示更新结果
4. **Given** 用户有 N 条消息, **When** 输入 `/rollback M`（M < N），**Then** 第 M 条之后的消息被丢弃

---

### User Story 6 - 会话生命周期管理 (Priority: P2)

作为一名开发者，我希望能够删除不需要的旧会话，以及将当前会话导出为 Markdown 文件，以便管理会话存储空间和离线分享对话内容。

**Why this priority**: 会话删除和导出是会话管理的自然延伸，避免存储空间膨胀和提供内容可移植性。

**Independent Test**: 使用 `/sessions` 查看会话列表并删除一个旧会话，重启后确认该会话不在列表中。使用 `/export` 导出当前会话，检查生成的 `.md` 文件。

**Acceptance Scenarios**:

1. **Given** 用户有多个历史会话, **When** 输入 `/sessions` 并选择删除某个会话，**Then** 该会话的 JSON 文件被永久删除
2. **Given** 用户在当前会话中, **When** 输入 `/export`，**Then** 生成包含完整对话、工具调用和时间戳的 Markdown 文件

---

### User Story 7 - 自定义 AI 行为指令 (Priority: P2)

作为一名开发者，我希望在 config.txt 中配置自定义系统提示词（`SYSTEM_PROMPT`）和压缩触发阈值（`COMPRESSION_THRESHOLD`），以便让 AI 遵循特定的行为规则，以及控制上下文压缩的触发时机。

**Why this priority**: 可配置性是平台灵活性的体现——不同项目可能需要不同的 AI 行为或压缩策略。

**Independent Test**: 在 config.txt 中设置 `SYSTEM_PROMPT="所有回复使用英文"`，重启后在对话中输入中文问题，验证 AI 回复使用英文。

**Acceptance Scenarios**:

1. **Given** config.txt 配置了 `SYSTEM_PROMPT="请所有回复使用英文"`, **When** 用户发送中文问题，**Then** AI 回复使用英文
2. **Given** config.txt 配置了 `COMPRESSION_THRESHOLD=0.3`, **When** 对话 token 达到 30% 窗口限制，**Then** 系统触发自动压缩

---

### Edge Cases

- 日志文件过大（超过 10MB）时，系统应自动轮转保留最近内容
- 用户在极短时间内连续执行 `/context` 命令时，系统应能正常响应
- 项目配置文件编码非 UTF-8 时，系统应给出明确警告并使用默认规则
- `/rollback` 参数超出范围时，系统应给出明确错误提示
- `/pin` 在没有用户消息时执行，系统应给出提示
- LangChain LLM 摘要失败时，系统应自动回退到本地关键词提取

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: 系统必须提供 `/context` 命令，在对话中显示当前会话的完整上下文状态报告
- **FR-002**: `/context` 输出必须包含：会话 ID、消息数量、估算 token 数、压缩阈值百分比、会话存储路径、项目上下文来源文件、已加载的技术栈列表、是否触发过压缩
- **FR-003**: 系统必须将上下文关键事件写入 `~/.claude-code-clone/context.log` 日志文件，事件类型至少包括：SESSION_SAVED、SESSION_LOADED、CONTEXT_COMPRESSED、PROJECT_CONTEXT_LOADED
- **FR-004**: 每条日志记录必须包含时间戳、事件类型和相关数据（消息数、token 数、会话 ID 等）
- **FR-005**: 项目上下文加载完成后，系统必须在对话界面向用户明确展示加载结果（来源文件、技术栈、指令长度）
- **FR-006**: 状态栏必须持续显示消息数、token 占压缩阈值的百分比、以及上一轮对话的 token 增量（Δtoken）
- **FR-007**: 系统必须提供 `/clear` 命令，清空当前会话的全部对话历史但保留项目上下文和任务列表
- **FR-008**: 系统必须提供 `/compress` 命令，使用 LangChain LLM 摘要对早期消息进行压缩，并在失败时回退到本地关键词提取
- **FR-009**: 系统必须提供 `/pin` 命令，将最后一条用户消息标记为固定（pinned），压缩时固定消息不被移除
- **FR-010**: 系统必须提供 `/rollback N` 命令，丢弃第 N 条消息之后的所有对话，N 必须在有效范围内
- **FR-011**: 系统必须提供 `/reload` 命令，不重启即重新加载项目配置文件（CLAUDE.md）并更新会话上下文
- **FR-012**: 系统必须提供 `/sessions` 命令，列出所有历史会话并支持删除指定会话
- **FR-013**: 系统必须提供 `/export` 命令，将当前会话导出为可读的 Markdown 文件（含消息内容、工具调用记录和时间戳）
- **FR-014**: 系统必须从 config.txt 读取 `SYSTEM_PROMPT` 配置项，用于自定义 AI 行为指令
- **FR-015**: 系统必须从 config.txt 读取 `COMPRESSION_THRESHOLD` 配置项（0.0-1.0），用于自定义自动压缩触发阈值

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 用户在对话中输入 `/context` 后，1 秒内收到完整的上下文状态报告
- **SC-002**: 100% 的上下文事件（保存、加载、压缩、项目上下文加载）被记录到日志文件
- **SC-003**: 用户在对话开始后的前 3 秒内能看到项目上下文加载结果
- **SC-004**: 日志文件轮转机制确保文件不超过 10MB

### 验证方法（供用户手动验证）

| 验证项 | 验证方法 |
|--------|----------|
| `/context` 命令 | 对话中输入 `/context`，观察输出是否包含所有必需字段 |
| 上下文存储 | 1) 对话后输入 `/context` 查看存储路径；2) 退出后用 `cat` 查看 JSON 文件内容 |
| 上下文加载恢复 | 1) 记下 `/context` 显示的会话 ID；2) 退出重启选择该会话；3) 问 AI "我们刚才在聊什么"——应能回忆 |
| 上下文压缩 | 1) 粘贴大量文本使 token 接近 126K；2) 观察日志或 `/context` 是否显示压缩事件 |
| 项目上下文 | 1) 在项目根目录创建 CLAUDE.md；2) 启动进入对话观察启动信息；3) `/context` 确认来源 |
| 事件日志 | `cat ~/.claude-code-clone/context.log` 查看是否有 SESSION_SAVED 等事件记录 |

## Assumptions

- 上下文日志文件存储在 `~/.claude-code-clone/context.log`，与现有会话存储同目录
- 日志格式为每行一个 JSON 对象（JSONL 格式），便于程序解析
- `/context` 命令仅在有活跃会话时可用，会话选择界面不支持该命令
- 状态栏的基础实现已存在（spec 005），本 spec 在其上增强
