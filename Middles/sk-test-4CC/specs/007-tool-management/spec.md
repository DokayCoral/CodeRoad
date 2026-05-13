# Feature Specification: 工具管理体系——Skills + MCP + CLI

**Feature Branch**: `007-tool-management`  
**Created**: 2026-05-12  
**Status**: Draft  
**Input**: User description: "建立、完善工具管理工作。注意过程的可验证方法。"

## Clarifications

### Session 2026-05-12

- Q: "工具"指什么？ → A: Skills（.claude/skills/ 下的 SKILL.md）+ MCP（Model Context Protocol）+ 命令行执行，不是底层文件/shell 工具
- Q: Skills 管理范围？ → A: 完整生命周期——列出、热加载、安装/卸载
- Q: MCP 集成深度？ → A: 完整交互——连接/断开管理 + AI 可通过 MCP 协议实际调用工具

## User Scenarios & Testing *(mandatory)*

### User Story 1 - 查看已安装的 Skills (Priority: P1)

作为一名开发者，我希望通过 `/skills` 命令查看当前项目已安装的所有 Skills（名称、描述、来源文件），以便了解 AI 有哪些可用的专项能力。

**Why this priority**: Skills 是 Claude Code 的核心扩展机制——用户必须能查看 AI 当前的能力集。

**Independent Test**: 在对话中输入 `/skills`，验证列出所有 `.claude/skills/` 下的 SKILL.md 文件。

**Acceptance Scenarios**:

1. **Given** `.claude/skills/` 下存在多个 SKILL.md, **When** 输入 `/skills`，**Then** 列出每个 Skill 的名称、描述和文件路径
2. **Given** `.claude/skills/` 为空或不存在, **When** 输入 `/skills`，**Then** 提示 "No skills installed"

---

### User Story 2 - 安装和卸载 Skills (Priority: P1)

作为一名开发者，我希望通过命令从文件路径或 URL 安装新 Skill，以及卸载不需要的 Skill。

**Why this priority**: 可扩展性——用户应能动态添加新能力而非只查看已有能力。

**Independent Test**: 创建一个简单的 SKILL.md 文件并安装，验证 `/skills` 列表中新增该 Skill。

**Acceptance Scenarios**:

1. **Given** 用户有一个本地 SKILL.md 文件, **When** 输入 `/skill-install /path/to/skill.md`，**Then** 文件被复制到 `.claude/skills/` 并立即可用
2. **Given** 用户想移除某个 Skill, **When** 输入 `/skill-uninstall <skill-name>`，**Then** 对应文件被删除，`/skills` 列表中不再显示
3. **Given** 用户安装了一个 Skill, **When** AI 处理下一个请求，**Then** AI 能识别并调用该 Skill（无需重启）

---

### User Story 3 - MCP 服务器连接管理 (Priority: P1)

作为一名开发者，我希望通过命令管理 MCP 服务器的连接——查看已配置的服务器、连接/断开、查看连接状态。

**Why this priority**: MCP 是 AI 调用外部工具的标准协议——必须先建立连接才能使用。

**Independent Test**: 配置一个 MCP 服务器，连接后验证 `/mcp` 显示连接状态为 "connected"。

**Acceptance Scenarios**:

1. **Given** config 中配置了 MCP 服务器, **When** 输入 `/mcp`，**Then** 列出所有服务器及其连接状态
2. **Given** 服务器已配置但未连接, **When** 输入 `/mcp-connect <name>`，**Then** 建立连接并更新状态
3. **Given** 服务器已连接, **When** 输入 `/mcp-disconnect <name>`，**Then** 断开连接

---

### User Story 4 - AI 通过 MCP 调用工具 (Priority: P2)

作为一名开发者，我希望 AI 能通过 MCP 协议发现并调用外部服务器提供的工具，工具调用结果返回对话中。

**Why this priority**: MCP 的最终价值——不只是管理连接，而是让 AI 扩展能力边界。

**Independent Test**: 连接一个提供工具列表的 MCP 服务器，验证 AI 在需要时能调用该工具并返回结果。

**Acceptance Scenarios**:

1. **Given** MCP 服务器已连接并提供工具列表, **When** AI 处理用户请求，**Then** AI 的工具列表中包含 MCP 服务器提供的工具
2. **Given** AI 决定调用 MCP 工具, **When** 工具执行完成，**Then** 结果显示在对话中

---

### User Story 5 - 命令行执行管理 (Priority: P2)

作为一名开发者，我希望平台能执行 Shell 命令（已有 bash 工具），并在 `/tools` 中看到其状态。

**Why this priority**: 命令行是最基础的工具——Skills 和 MCP 的补充。

**Acceptance Scenarios**:

1. **Given** 用户输入 `/tools`, **When** 查看列表，**Then** bash 工具显示为 "CLI" 类型，与其他 Skills/MCP 工具区分

### Edge Cases

- Skill 文件名冲突时：安装应拒绝覆盖，提示用户先卸载旧版本
- MCP 服务器连接失败时：显示具体错误原因（网络不可达、认证失败、协议不匹配）
- MCP 工具调用超时时：设置 30 秒超时，超时后返回错误并保持连接
- Skills 目录不存在时：首次启动自动创建 `.claude/skills/`
- Skills 解析失败（非 Markdown 或格式损坏）时：跳过该 Skill 并记录警告

## Requirements *(mandatory)*

### Functional Requirements

**Skills 管理**

- **FR-001**: 系统必须提供 `/skills` 命令，列出 `.claude/skills/` 下所有已安装的 Skill（名称、描述、文件路径）
- **FR-002**: 系统必须提供 `/skill-install <path|url>` 命令，将 SKILL.md 文件安装到 `.claude/skills/`
- **FR-003**: 系统必须提供 `/skill-uninstall <name>` 命令，删除指定 Skill 的文件
- **FR-004**: 新安装的 Skill 必须在下一个 AI 请求中立即可用（热加载，无需重启）

**MCP 管理**

- **FR-005**: 系统必须提供 `/mcp` 命令，列出所有已配置的 MCP 服务器及其连接状态
- **FR-006**: 系统必须提供 `/mcp-connect <name>` 命令，建立与 MCP 服务器的连接
- **FR-007**: 系统必须提供 `/mcp-disconnect <name>` 命令，断开与 MCP 服务器的连接
- **FR-008**: 系统必须实现 MCP 客户端协议，支持 `tools/list` 和 `tools/call` 两个核心方法
- **FR-009**: MCP 服务器提供的工具必须合并到 AI 可用工具列表中，AI 可透明调用

**命令行**

- **FR-010**: 系统必须保留现有 bash 工具的 Shell 命令执行能力
- **FR-011**: 系统必须提供 `/tools` 命令，汇总展示所有类型工具（Skills / MCP / CLI）及其状态

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: `/skills` 命令在 1 秒内完成列表渲染
- **SC-002**: 安装的 Skill 在 5 秒内被 AI 识别（下一个请求即生效）
- **SC-003**: MCP 连接在 10 秒内完成（或返回明确错误）
- **SC-004**: MCP 工具调用在 30 秒内返回结果（或超时断开）
- **SC-005**: 100% 的 Skills 安装/卸载操作有明确的成功/失败反馈

### 验证方法

| 验证项 | 验证方法 |
|--------|----------|
| `/skills` 列表 | 对话中输入 `/skills` → 确认列出所有已安装 Skill |
| Skill 安装 | 创建测试 SKILL.md → `/skill-install ...` → `/skills` 确认新增 |
| Skill 卸载 | `/skill-uninstall <name>` → `/skills` 确认移除 |
| 热加载 | 安装 Skill 后直接让 AI 使用该 Skill → 确认被识别 |
| `/mcp` 状态 | 配置测试服务器 → `/mcp` → 确认列出 |
| MCP 连接 | `/mcp-connect <name>` → `/mcp` 确认状态变为 connected |
| MCP 工具调用 | 连接后让 AI 调用 MCP 工具 → 确认返回结果 |
| `/tools` 汇总 | 输入 `/tools` → 确认三种类型（Skills/MCP/CLI）均列出 |
| CLI 执行 | AI 执行 `git status` → 返回结果 |

## Assumptions

- Skills 文件为 Markdown 格式（`.md`），存放在 `.claude/skills/` 目录
- MCP 服务器配置存储在 config.txt 中（JSON 格式的 `MCP_SERVERS` 配置项）
- MCP 协议使用 stdio 或 HTTP 传输（优先实现 stdio）
- 命令行工具复用已有的 bash 工具，不做额外改动
