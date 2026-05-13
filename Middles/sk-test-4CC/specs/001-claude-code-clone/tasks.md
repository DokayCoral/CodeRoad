# Tasks: Claude Code 核心功能复刻平台

**Input**: Design documents from `specs/001-claude-code-clone/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/

**Tests**: TDD is NON-NEGOTIABLE per project constitution. Contract tests, integration tests, and unit tests are included for all user stories.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- Paths follow the structure defined in plan.md

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [x] T001 Create project structure per plan.md: `src/` with models/, tools/, services/, cli/ subdirectories; `tests/` with contract/, integration/, unit/ subdirectories
- [x] T002 Initialize Python project with dependencies in `requirements.txt` (anthropic, openai, prompt-toolkit, rich, pydantic, pyyaml, pytest, pytest-mock, ruff)
- [x] T003 [P] Configure ruff linting and formatting in `pyproject.toml`
- [x] T004 [P] Configure pytest in `pyproject.toml` with test paths and markers (contract, integration, unit)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**CRITICAL**: No user story work can begin until this phase is complete

- [x] T005 Implement configuration management in `src/config.py` (load/save ~/.claude-code-clone/config.yml, API key handling, model selection)
- [x] T006 [P] Implement session JSON storage layer in `src/services/session_service.py` (read/write sessions/YYYY-MM-DD/<id>.json with atomic overwrite)
- [x] T007 [P] Create base entity models with pydantic in `src/models/` (Session, Message, ToolCall, Task, ProjectContext per data-model.md)
- [x] T008 [P] Implement AI service base class and factory in `src/services/ai_service.py` (abstract provider interface, Anthropic provider, OpenAI provider, factory dispatch by config)
- [x] T009 [P] Implement tool registry with permission levels in `src/tools/registry.py` (register tools by name, permission_level enum: read/shell_read/write/shell_write/blocked)
- [x] T010 Implement CLI app entry point skeleton in `src/cli/app.py` (argument parsing, session start/select loop, graceful shutdown handling)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - 启动编程会话并与 AI 交互 (Priority: P1)

**Goal**: User can start a session, send natural language coding requests, receive streaming AI responses with Markdown rendering, maintain multi-turn conversation context, and save/restore sessions.

**Independent Test**: Start a new session, input a coding question (e.g., "How to read a JSON file in Python"), verify streaming response with code formatting appears. Continue with follow-up question referencing prior context. End session, verify session appears in session list on restart.

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T011 [P] [US1] Contract test for AI service streaming interface in `tests/contract/test_ai_service.py` (streaming response contract, error handling, timeout behavior)
- [x] T012 [P] [US1] Integration test for session lifecycle in `tests/integration/test_session_flow.py` (create session, send messages, verify context maintained across 50 rounds, save and restore)

### Implementation for User Story 1

- [x] T013 [P] [US1] Create Message model with validation in `src/models/message.py` (role enum, content, tool_calls list, timestamp, token_count)
- [x] T014 [P] [US1] Create Session model with validation in `src/models/session.py` (id uuid, messages list, task_list, project_context, status enum)
- [x] T015 [US1] Implement SessionService in `src/services/session_service.py` (create/load/save session, list recent sessions for selection UI, archive old sessions)
- [x] T016 [P] [US1] Implement Anthropic AI service in `src/services/ai_service.py` (Anthropic SDK client, message construction with system prompt, streaming API call, tool use response parsing)
- [x] T017 [P] [US1] Implement OpenAI AI service in `src/services/ai_service.py` (OpenAI SDK client, message construction, streaming API call, tool call response parsing)
- [x] T018 [US1] Implement StreamService in `src/services/stream_service.py` (SSE event stream parsing, token accumulation, Markdown line buffering, first-token latency tracking)
- [x] T019 [P] [US1] Implement CLI input handler in `src/cli/input_handler.py` (prompt_toolkit session with multi-line input, Ctrl+C interrupt detection, command history)
- [x] T020 [P] [US1] Implement rich Markdown renderer in `src/cli/renderer.py` (streaming Markdown with code syntax highlighting, Live update for incremental rendering, tool call status display)
- [x] T021 [US1] Implement main CLI app conversation loop in `src/cli/app.py` (session start → user input → AI stream → tool call dispatch → response render → repeat; interrupt handling per FR-013)
- [x] T022 [US1] Implement context window compression in `src/services/context_service.py` (token counting, trigger threshold detection, early-message summarization via AI, preserve recent messages + key tool calls per FR-002b)
- [x] T023 [US1] Implement session list selection UI in `src/cli/app.py` (show recent sessions with date/title preview, new session option, continue selection per FR-010)

**Checkpoint**: User Story 1 fully functional - can start sessions, chat with AI, get streaming responses, maintain context, save/restore sessions

---

## Phase 4: User Story 2 - 使用工具操作代码文件 (Priority: P1)

**Goal**: AI can read project files, write new files, edit existing files with exact string replacement, search code with regex and glob patterns. Tools follow tiered approval model (read auto-execute, write/edit require confirmation).

**Independent Test**: In a session, request AI to read a file (auto-execute), search for a keyword (auto-execute), create a new file (approve confirmation), edit an existing file (approve confirmation). Verify file system changes are correct, backups are created, conflicts are detected.

### Tests for User Story 2

- [x] T024 [P] [US2] Contract test for Read tool in `tests/contract/test_tool_read.py` (file found, not found, permission denied, binary detection, offset/limit, symlink follow)
- [x] T025 [P] [US2] Contract test for Write tool in `tests/contract/test_tool_write.py` (create new file with confirmation, overwrite existing with backup, parent directory creation, external modification conflict detection)
- [x] T026 [P] [US2] Contract test for Edit tool in `tests/contract/test_tool_edit.py` (exact string replacement, non-unique string error, not-found error, external modification detection)
- [x] T027 [P] [US2] Contract test for Grep tool in `tests/contract/test_tool_grep.py` (regex match, file filtering, output modes, context lines, case-insensitive, binary skip)
- [x] T028 [P] [US2] Contract test for Glob tool in `tests/contract/test_tool_glob.py` (pattern match, sorted by mtime, hidden files, no matches, path not found)
- [x] T029 [US2] Integration test for file tool pipeline in `tests/integration/test_tool_pipeline.py` (read → edit → read verify → write new file → search verify chain)

### Implementation for User Story 2

- [x] T030 [P] [US2] Implement Read tool in `src/tools/read.py` (file open with encoding detection, line number prefix, offset/limit support, binary detection via null bytes, symlink resolution)
- [x] T031 [P] [US2] Implement Write tool in `src/tools/write.py` (content write with atomic overwrite, .bak backup creation, parent directory auto-create after confirmation, new-file prompt, external modification timestamp check)
- [x] T032 [P] [US2] Implement Edit tool in `src/tools/edit.py` (exact string match with whitespace normalization, uniqueness check, external modification detection via mtime comparison, conflict resolution UI: overwrite/skip/diff)
- [x] T033 [P] [US2] Implement Grep tool in `src/tools/grep.py` (regex compilation with error handling, file walking with .gitignore respect, output mode dispatch, context line extraction, binary file skip, result head_limit truncation)
- [x] T034 [P] [US2] Implement Glob tool in `src/tools/glob.py` (glob pattern expansion via pathlib, mtime sorting, hidden file handling, 1000 result limit)
- [x] T035 [US2] Register all file tools in `src/tools/registry.py` (read: permission_level=read, write: permission_level=write, edit: permission_level=write, grep: permission_level=read, glob: permission_level=read)
- [x] T036 [US2] Integrate tool execution loop in `src/services/ai_service.py` (parse tool_use response, dispatch to tool registry, collect tool_result, send back to AI for follow-up, approval flow for write tools)

**Checkpoint**: User Stories 1 AND 2 both work independently - AI can read, write, edit, search files with proper approval flow

---

## Phase 5: User Story 3 - 执行 Shell 命令 (Priority: P2)

**Goal**: AI can execute shell commands on behalf of the user. Read-only commands auto-execute; commands with side effects require user confirmation. Dangerous commands are blocked. 30-second timeout enforced.

**Independent Test**: Request AI to check git status (auto-execute), then request installing a package (approval required). Verify dangerous commands (rm -rf /) are blocked. Test timeout by running a sleep command exceeding 30 seconds.

### Tests for User Story 3

- [x] T037 [P] [US3] Contract test for Bash tool in `tests/contract/test_tool_bash.py` (read-only auto-execute, write-command confirmation, dangerous command blocked, timeout termination, non-zero exit, command not found)
- [x] T038 [US3] Integration test for shell approval pipeline in `tests/integration/test_shell_pipeline.py` (auto-execute chain, user approval flow, timeout handling, error recovery)

### Implementation for User Story 3

- [x] T039 [P] [US3] Create ToolCall model with state machine in `src/models/tool_call.py` (status transitions: pending→approved→executing→success/error/cancelled, approval_required flag, duration tracking)
- [x] T040 [US3] Implement Bash tool in `src/tools/bash.py` (subprocess.run with capture_output, 30s default timeout via signal, working directory context, environment inheritance)
- [x] T041 [US3] Implement command classification in `src/tools/bash.py` (shell_read whitelist: cat/ls/git-status/find/grep/etc, shell_write detection: git-commit/install/rm/mv/etc, blocked blacklist: rm-rf-root/mkfs/dd/fork-bomb, interactive command rejection)
- [x] T042 [US3] Register Bash tool in `src/tools/registry.py` (dynamic permission level based on command classification, description parameter for approval UI)
- [x] T043 [US3] Integrate shell approval UI in `src/cli/app.py` (show command with description, [Y/n] prompt for write commands, timeout notification, error display with stderr, blocked command override option)

**Checkpoint**: User Stories 1, 2, AND 3 all work independently - AI can execute shell commands with safety gates

---

## Phase 6: User Story 5 - 项目上下文感知与配置 (Priority: P2)

**Goal**: AI automatically loads project configuration (CLAUDE.md style) at session start. AI-generated code suggestions follow project conventions and style. Config file changes take effect in subsequent sessions.

**Independent Test**: Create a CLAUDE.md with project-specific rules. Start a session and verify AI responses adhere to those rules. Modify CLAUDE.md, start a new session, verify updated rules apply.

### Tests for User Story 5

- [x] T044 [P] [US5] Unit test for config loading in `tests/unit/test_config.py` (CLAUDE.md parsing, YAML config parsing, missing file fallback, merge priority)
- [x] T045 [US5] Integration test for context-aware session in `tests/integration/test_context_flow.py` (create project config, start session, verify AI system prompt includes project context, code style adherence check)

### Implementation for User Story 5

- [x] T046 [P] [US5] Implement project config loader in `src/config.py` (CLAUDE.md Markdown parsing, project tech stack detection, code convention extraction, directory structure summary)
- [x] T047 [P] [US5] Create ProjectContext model in `src/models/project_context.py` (project_name, config_file_path, instructions, tech_stack list, directory_structure, code_conventions)
- [x] T048 [US5] Enhance ContextService in `src/services/context_service.py` (load project config at session start, merge project instructions into AI system prompt, detect project tech stack from files in working directory)
- [x] T049 [US5] Integrate project context loading into session startup in `src/cli/app.py` (scan for CLAUDE.md on session start, display loaded context info, notify user if no config found)

**Checkpoint**: User Stories 1, 2, 3, AND 5 all work independently - AI understands project context

---

## Phase 7: User Story 4 - 任务规划与跟踪 (Priority: P3)

**Goal**: AI can decompose complex requests into structured task lists, track task status (pending → in_progress → completed), manage task dependencies, and auto-update task status as work progresses.

**Independent Test**: Give AI a complex request ("add user authentication to the project"). Verify AI creates a task list. As AI completes subtasks, verify tasks auto-update. Verify dependent tasks unblock when prerequisites complete.

### Tests for User Story 4

- [x] T050 [P] [US4] Unit test for Task model and state machine in `tests/unit/test_models.py` (state transitions valid, dependency blocking logic, status enum validation)

### Implementation for User Story 4

- [x] T051 [P] [US4] Create Task model with state machine in `src/models/task.py` (status transitions: pending→in_progress↔pending, in_progress→completed, →cancelled; dependency check: blocked if any dependency not completed)
- [x] T052 [US4] Implement TaskService in `src/services/task_service.py` (create task list from AI response parsing, update task status, check and unblock dependent tasks, serialize tasks to session JSON)
- [x] T053 [US4] Implement task list rendering in `src/cli/renderer.py` (rich Panel/Table display, status icons, progress indicator, dependency graph visualization)
- [x] T054 [US4] Integrate task auto-update in `src/cli/app.py` (detect when AI tool calls correspond to task completion, prompt AI to update task status, display task progress after each turn)

**Checkpoint**: All user stories (1-5) now independently functional

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [x] T055 [P] Run quickstart.md validation end-to-end (setup venv, install deps, configure API key, start session, complete all 6 key workflows)
- [x] T056 [P] Code cleanup and refactoring (remove dead code, consolidate duplicate patterns, ensure consistent error handling across all tools)
- [x] T057 [P] Security hardening (verify API key never logged, audit subprocess call patterns for injection, validate file path traversal protection in all tools)
- [x] T058 Final integration test run: `pytest tests/ -v` with all tests passing

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phases 3-7)**: All depend on Foundational phase completion
  - US1 (Phase 3): No story dependencies
  - US2 (Phase 4): No story dependencies (but benefits from US1's AI service for integration)
  - US3 (Phase 5): No story dependencies (but benefits from US2's tool registry)
  - US5 (Phase 6): No story dependencies
  - US4 (Phase 7): No story dependencies
  - All can proceed in parallel once Foundational phase is complete
- **Polish (Phase 8)**: Depends on all desired user stories being complete

### Within Each User Story

- Tests MUST be written and FAIL before implementation (TDD per constitution)
- Models before services
- Services before CLI integration
- Core implementation before error handling polish
- Story complete before moving to next priority (if sequential)

### Parallel Opportunities

- Phase 1: T003, T004 can run in parallel
- Phase 2: T006, T007, T008, T009 can run in parallel (different files, no deps)
- US1 Tests: T011, T012 can run in parallel
- US1 Impl: T013, T014, T016, T017, T019, T020 can run in parallel
- US2 Tests: T024, T025, T026, T027, T028 can run in parallel
- US2 Impl: T030, T031, T032, T033, T034 can run in parallel
- US3: T037, T039 can run in parallel
- US5: T044, T046, T047 can run in parallel
- Across stories: US1, US2, US3, US5, US4 can all be worked on in parallel after Foundational

---

## Parallel Example: User Story 2

```bash
# Launch all US2 contract tests together:
Task: "Contract test for Read tool in tests/contract/test_tool_read.py"
Task: "Contract test for Write tool in tests/contract/test_tool_write.py"
Task: "Contract test for Edit tool in tests/contract/test_tool_edit.py"
Task: "Contract test for Grep tool in tests/contract/test_tool_grep.py"
Task: "Contract test for Glob tool in tests/contract/test_tool_glob.py"

# Launch all US2 tool implementations together:
Task: "Implement Read tool in src/tools/read.py"
Task: "Implement Write tool in src/tools/write.py"
Task: "Implement Edit tool in src/tools/edit.py"
Task: "Implement Grep tool in src/tools/grep.py"
Task: "Implement Glob tool in src/tools/glob.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test US1 independently - start session, chat with AI, save/restore
5. Demo if ready: "I have a working AI coding assistant with streaming responses"

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. US1 → AI chat works → MVP!
3. US2 → File tools work → AI can read/write/edit/search code → Demo!
4. US3 → Shell commands work → AI can run tests, git, install deps → Demo!
5. US5 → Project context works → AI follows project conventions → Demo!
6. US4 → Task tracking works → Full Claude Code clone → Demo!
7. Polish → Production quality

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (AI conversation core)
   - Developer B: User Story 2 (File tools)
   - Developer C: User Story 3 (Shell execution) + User Story 5 (Context)
   - Developer D: User Story 4 (Task management)
3. All stories integrate at their respective checkpoints

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story must be independently completable and testable per Constitution V
- TDD cycle enforced: write tests → verify FAIL → implement → verify PASS (Constitution III)
- Commit after each task or logical group (Constitution: "why" not "what")
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
