# Tasks: 工具管理体系——Skills + MCP + CLI

**Input**: Design documents from `specs/007-tool-management/`
**Prerequisites**: plan.md, spec.md

## Format: `[ID] [P?] [Story] Description`

---

## Phase 1: Foundational — Service Layer

**Purpose**: Core services that all user stories depend on.

- [x] T001 [P] Create `src/services/skill_service.py` — `list_skills()` scans `.claude/skills/` for SKILL.md, parses name/description from frontmatter, returns list of dicts
- [x] T002 [P] Create `src/services/mcp_service.py` — `MCPClient` class with `__init__(command, args)`, `connect()` subprocess.Popen, `disconnect()` terminate, `_send_request(method, params)` JSON-RPC, `list_tools()`, `call_tool(name, arguments)`
- [x] T003 Add `get_mcp_servers()` to `src/config.py` — parse `MCP_SERVERS` from config.txt as JSON list of {name, command, args}
- [x] T004 [P] Ensure `.claude/skills/` directory is auto-created on startup in `src/cli/app.py` main()

**Checkpoint**: skill_service and mcp_service ready for command integration.

---

## Phase 2: US1 + US2 — Skills 管理 (P1)

**Goal**: View, install, and uninstall Skills. Hot-reload on install.

**Independent Test**: `/skills` → see empty list → `/skill-install test.md` → `/skills` shows new skill → `/skill-uninstall` → `/skills` empty.

- [x] T005 [P] [US1] Implement `render_skills_list()` in `src/cli/renderer.py` — Rich table with name, description, source path; "No skills installed" for empty
- [x] T006 [US1] Implement `/skills` command in `src/cli/app.py` — calls `list_skills()`, renders table
- [x] T007 [US2] Implement `install_skill(path)` in `src/services/skill_service.py` — copy file to `.claude/skills/`, validate it's Markdown, reject on name conflict
- [x] T008 [US2] Implement `uninstall_skill(name)` in `src/services/skill_service.py` — delete file from `.claude/skills/`, return False if not found
- [x] T009 [US2] Implement `/skill-install <path>` command in `src/cli/app.py` — calls `install_skill()`, shows result
- [x] T010 [US2] Implement `/skill-uninstall <name>` command in `src/cli/app.py` — calls `uninstall_skill()`, shows result

**Checkpoint**: Skills full lifecycle operational. `/skills` lists, install/uninstall works.

---

## Phase 3: US3 — MCP 连接管理 (P1)

**Goal**: View MCP servers, connect/disconnect, see connection status.

**Independent Test**: Config a test MCP server → `/mcp` shows it → `/mcp-connect` → status "connected" → `/mcp-disconnect` → status "disconnected".

- [x] T011 [P] [US3] Implement `render_mcp_status()` in `src/cli/renderer.py` — Rich table: name, transport, status (with color coding), tools count
- [x] T012 [US3] Implement `/mcp` command in `src/cli/app.py` — reads `get_mcp_servers()`, shows connection status for each
- [x] T013 [US3] Implement `/mcp-connect <name>` command in `src/cli/app.py` — instantiates MCPClient, calls `connect()`, calls `list_tools()`, stores client in session-level dict
- [x] T014 [US3] Implement `/mcp-disconnect <name>` command in `src/cli/app.py` — calls `disconnect()`, removes from dict

**Checkpoint**: MCP servers can be connected/disconnected. `/mcp` shows live status.

---

## Phase 4: US4 — AI 通过 MCP 调用工具 (P2)

**Goal**: Connected MCP servers' tools appear in AI's tool list. AI can call them and get results.

**Independent Test**: Connect MCP server with tools → ask AI to use one of those tools → confirm result.

- [x] T015 [US4] In `_register_tools()` in `src/cli/app.py`, merge MCP tools into AI tool schemas — each MCP tool gets a ToolDef with a handler that calls `mcp_client.call_tool()`
- [x] T016 [US4] Handle MCP tool call errors gracefully — timeout 30s, return error message to AI, keep connection alive

**Checkpoint**: AI can discover and call MCP tools. Results flow back to conversation.

---

## Phase 5: US5 — `/tools` 汇总 + CLI (P2)

**Goal**: Single command showing all three tool types. CLI tools (bash) included.

**Independent Test**: `/tools` shows three sections: Skills, MCP, CLI — each with name, type, status.

- [x] T017 [P] [US5] Implement `render_tools_summary()` in `src/cli/renderer.py` — three panels: Skills (from skill_service), MCP (from mcp sessions), CLI (from registry)
- [x] T018 [US5] Implement `/tools` command in `src/cli/app.py` — aggregates data from all three sources, renders summary

**Checkpoint**: `/tools` shows complete tool inventory across all three types.

---

## Phase 6: Polish

- [x] T019 Update `render_help()` in `src/cli/app.py` — add all 7 new commands to help text
- [x] T020 End-to-end verification: test `/skills` → install → AI use → `/mcp` → connect → AI use → `/tools` → verify all types shown

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Foundational)**: No dependencies
- **Phase 2 (US1+US2)**: Depends on T001
- **Phase 3 (US3)**: Depends on T002, T003
- **Phase 4 (US4)**: Depends on Phase 3 (MCP clients must be connectable)
- **Phase 5 (US5)**: Depends on Phases 2, 3, 4

### Parallel Opportunities

| Phase | Parallel Tasks |
|-------|---------------|
| Phase 1 | T001, T002, T003, T004 all independent [P] |
| Phase 2 | T005 independent [P]; T007, T008 independent [P] |
| Phase 3 | T011 independent [P] |
| Phase 5 | T017 independent [P] |

### Cross-Phase

- Phases 2 and 3 can begin in parallel once Phase 1 is complete
- Phase 4 requires Phase 3
- Phase 5 requires Phases 2, 3, 4

---

## Implementation Strategy

### MVP (Phase 1 + Phase 2 only)

Complete T001-T010 → Skills management fully working → Demo: "I can install and use Skills".

### Incremental Delivery

1. Foundational → services ready
2. Skills → list, install, uninstall → Demo
3. MCP Connect → connect/disconnect → Demo
4. MCP Tools → AI calls MCP tools → Demo
5. `/tools` → all types in one view → Demo
