# Tasks: 上下文管理可视化与验证

**Input**: Design documents from `specs/006-context-verify/`
**Prerequisites**: plan.md, spec.md

**Tests**: Manual end-to-end verification (terminal rendering not automatable)

## Format: `[ID] [P?] [Story] Description`

---

## Phase 1: Foundation — Model & Config Changes

**Purpose**: Data model and configuration prerequisites for all new commands.

- [x] T001 [P] Add `pinned: bool = False` field to Message model in `src/models/__init__.py`
- [x] T002 [P] Add `input_tokens: int = 0` and `output_tokens: int = 0` fields to Message model in `src/models/__init__.py`
- [x] T003 Add `SYSTEM_PROMPT` and `COMPRESSION_THRESHOLD` parsing to `src/config.py` (read from config.txt, default threshold 0.7)
- [x] T004 Update `compress_messages()` in `src/services/context_service.py` to skip messages with `pinned=True`
- [x] T005 Update `_build_system_prompt()` in `src/cli/app.py` to append custom SYSTEM_PROMPT from config

**Checkpoint**: Models ready for new commands; compression respects pinned messages; custom system prompt works.

---

## Phase 2: Context Control Commands

**Purpose**: 5 new slash commands for active context management.

### /clear — Reset conversation

- [x] T006 [P] [US1] Implement `/clear` command handler in `src/cli/app.py` — clear `session.messages` but preserve `session.project_context` and `session.task_list`
- [x] T007 [US1] After `/clear`, auto-save session and re-render status bar in `src/cli/app.py`

### /compress — Manual compression

- [x] T008 [P] [US2] Implement `/compress` command handler in `src/cli/app.py` — directly call `compress_messages` on current session, log via `log_context_compressed`
- [x] T009 [US2] After compression, render info message with before/after counts in `src/cli/app.py`

### /reload — Refresh project context

- [x] T010 [P] [US3] Implement `/reload` command handler in `src/cli/app.py` — re-call `load_project_context(Path.cwd())`, update `session.project_context`, log via `log_project_context_loaded`
- [x] T011 [US3] After reload, render confirmation showing new config source and instruction length in `src/cli/app.py`

### /rollback — Revert to message N

- [x] T012 [P] [US4] Implement `/rollback N` command handler in `src/cli/app.py` — truncate `session.messages` to first N messages, validate N is in range
- [x] T013 [US4] After rollback, auto-save session and display new message count in `src/cli/app.py`

### /pin — Pin last user message

- [x] T014 [P] [US5] Implement `/pin` command handler in `src/cli/app.py` — find last Message with `role == USER` and set `pinned = True`
- [x] T015 [US5] After pin, render confirmation showing which message was pinned and auto-save in `src/cli/app.py`

### Help update

- [x] T016 Update `render_help()` in `src/cli/app.py` to list all 11 commands

**Checkpoint**: 5 new commands operational; compression respects pinned messages; custom system prompt works; reload updates project context.

---

## Phase 3: Session Management Commands

**Purpose**: Session deletion and export.

### Service layer

- [x] T017 [P] Implement `delete_session(session_id: str) -> bool` in `src/services/session_service.py` — remove the JSON file from the date directory
- [x] T018 [P] Implement `export_session(session: Session) -> str` in `src/services/session_service.py` — serialize session to readable Markdown with messages, tool calls, timestamps; return file path

### /sessions — Session manager

- [x] T019 [US6] Implement `/sessions` command handler in `src/cli/app.py` — show session list with delete option, call `delete_session` on confirmation
- [x] T020 [US6] Implement `render_session_manager()` in `src/cli/renderer.py` — table of sessions with #/date/messages/preview/delete_option

### /export — Export current session

- [x] T021 [US7] Implement `/export` command handler in `src/cli/app.py` — call `export_session`, display output file path
- [x] T022 [US7] Export format must include: session id, timestamps, message role headers, code blocks for AI responses, tool call records with parameters and results

**Checkpoint**: Sessions can be deleted from within the app; sessions export to readable Markdown.

---

## Phase 4: Visibility Enhancement

**Purpose**: Token consumption tracking in status bar and /context report.

- [x] T023 [P] Update `render_status_bar()` in `src/cli/renderer.py` to show last-turn token delta: `Δ+450 tokens`
- [x] T024 [P] Update `render_context_report()` in `src/cli/renderer.py` to include last 3 turns' token consumption
- [x] T025 In `run_conversation()` in `src/cli/app.py`, calculate per-turn token delta from last two messages and pass to status bar

**Checkpoint**: Status bar shows per-turn token consumption; /context shows recent trend.

---

## Phase 5: Polish & Verification

**Purpose**: End-to-end verification of all 26 context management features.

- [x] T026 Run full verification script (plan.md appendix): create CLAUDE.md, start app, test all 11 commands, check context.log, verify session JSON, export and inspect .md file, clean up
- [x] T027 Update `/help` output to accurately reflect all 11 available commands with brief descriptions
- [x] T028 Verify all 26 verification methods from the verification matrix pass

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Foundation)**: No dependencies — start immediately
- **Phase 2 (Context Control)**: Depends on T001-T005
- **Phase 3 (Session Mgmt)**: Depends on T001-T002 (models)
- **Phase 4 (Visibility)**: Depends on T001-T002 (models + token fields)
- **Phase 5 (Polish)**: Depends on all Phases 2-4 complete

### Within Each Phase

| Phase | Parallel Tasks |
|-------|---------------|
| Phase 1 | T001, T002 can run in parallel |
| Phase 2 | T006, T008, T010, T012, T014 all independent [P] |
| Phase 3 | T017, T018 can run in parallel [P] |
| Phase 4 | T023, T024 can run in parallel [P] |

### Cross-Phase Parallel Opportunities

- Phases 2, 3, and 4 can begin in parallel once Phase 1 is complete
- Phase 5 requires all others done

---

## Implementation Strategy

### MVP (Phase 1 + Phase 2 only)

1. Complete T001-T005 (foundation)
2. Complete T006-T016 (5 context control commands + help update)
3. **STOP and VALIDATE**: `/clear` → `/context` shows reset; `/pin` → fill → `/compress` → pin survives

### Incremental Delivery

1. Foundation → data model ready
2. Context Control → 5 new commands → Demo: "I can manage my conversation context"
3. Session Management → delete + export → Demo: "I can clean up and export sessions"
4. Visibility → Δtoken → Demo: "I can see token usage per turn"
5. Polish → full verification → Demo: "All 26 features verified"

---

## Notes

- [P] tasks = different files, no dependencies
- All file paths are relative to repository root
- Commit after each completed phase
- Run `python -m src.cli.app` after each phase to verify
