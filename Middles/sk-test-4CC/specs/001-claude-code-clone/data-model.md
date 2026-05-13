# Data Model: Claude Code 核心功能复刻平台

**Feature**: 001-claude-code-clone
**Date**: 2026-05-12

## Entities

### Session

Represents a single interactive coding session from start to end.

| Field | Type | Description |
|-------|------|-------------|
| id | string (UUID v4) | Unique session identifier |
| created_at | datetime (ISO 8601) | Session start timestamp |
| updated_at | datetime (ISO 8601) | Last message/activity timestamp |
| messages | list[Message] | Ordered list of conversation messages |
| task_list | list[Task] | Associated tasks (may be empty) |
| project_context | ProjectContext | Loaded project configuration snapshot |
| status | enum: active | archived | Current session state |

**Identity**: `id` (UUID v4)
**Lifecycle**: `active` → (user ends or starts new session) → `archived`
**Storage**: `sessions/YYYY-MM-DD/<id>.json`

### Message

A single turn in the conversation, possibly containing tool calls.

| Field | Type | Description |
|-------|------|-------------|
| id | string (UUID v4) | Unique message identifier |
| role | enum: user | assistant | system | Message sender |
| content | string | Message text content |
| tool_calls | list[ToolCall] | Tool invocations in this message (optional) |
| timestamp | datetime (ISO 8601) | When message was created |
| token_count | int | Approximate token count for this message |

**Identity**: `id` (UUID v4)
**Relationship**: Belongs to exactly one Session

### ToolCall

A single tool invocation requested by the AI and executed by the platform.

| Field | Type | Description |
|-------|------|-------------|
| id | string (UUID v4) | Unique call identifier |
| tool_name | string | Registered tool name (read, write, edit, grep, glob, bash) |
| parameters | dict | Tool-specific arguments |
| result | string | Execution output or error |
| status | enum: pending | approved | executing | success | error | cancelled |
| approval_required | bool | Whether user confirmation was needed |
| approved_by_user | bool | null | null if not required, else true/false |
| duration_ms | int | null | Execution time in milliseconds |

**Identity**: `id` (UUID v4)
**Relationship**: Belongs to exactly one Message

### Task

A work unit tracked within a session.

| Field | Type | Description |
|-------|------|-------------|
| id | string (UUID v4) | Unique task identifier |
| title | string | Short task description |
| description | string | Detailed task description |
| status | enum: pending | in_progress | completed | cancelled |
| dependencies | list[string] | IDs of tasks this task depends on |
| created_at | datetime (ISO 8601) | When task was created |
| completed_at | datetime (ISO 8601) | null | When task was completed |

**Identity**: `id` (UUID v4)
**State transitions**:
- `pending` → `in_progress` (AI starts working)
- `in_progress` → `completed` (work done)
- `in_progress` → `pending` (back to queue)
- `pending` / `in_progress` → `cancelled` (no longer needed)
- Blocked if any `dependencies` task is not `completed`

### ProjectContext

Project-level configuration loaded at session start.

| Field | Type | Description |
|-------|------|-------------|
| project_name | string | Project/workspace name |
| config_file_path | string | Path to the loaded config file (e.g., CLAUDE.md) |
| instructions | string | Project-specific AI instructions |
| tech_stack | list[string] | Detected/configured technology stack |
| directory_structure | dict | Summary of project directory layout |
| code_conventions | string | Project coding standards and conventions |

**Storage**: Project config file (YAML/Markdown) at project root

## Entity Relationships

```
Session (1) ──── (N) Message ──── (N) ToolCall
Session (1) ──── (N) Task
Session (1) ──── (1) ProjectContext
Task    (N) ──── (N) Task (dependencies, self-referential)
```

## Storage Schema

```
~/.claude-code-clone/
├── config.yml              # Global user config (API keys, preferences)
└── sessions/
    └── YYYY-MM-DD/
        └── <uuid>.json     # Full session data (messages + tool calls + tasks)
```
