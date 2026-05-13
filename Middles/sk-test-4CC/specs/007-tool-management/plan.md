# Implementation Plan: 工具管理体系——Skills + MCP + CLI

**Branch**: `007-tool-management` | **Date**: 2026-05-12 | **Spec**: [spec.md](./spec.md)

## Summary

建立三层工具管理体系：
1. **Skills** — `.claude/skills/` 下 SKILL.md 的安装/卸载/列表/热加载
2. **MCP** — MCP 客户端协议（stdio），JSON-RPC，`tools/list` + `tools/call`
3. **CLI** — 现有 bash 工具归入 CLI 类型，`/tools` 汇总展示

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: 无新增（MCP 使用标准库 subprocess + json）
**Storage**: `.claude/skills/` (Skills 文件), `config.txt` (MCP_SERVERS JSON 配置)
**Testing**: 手动端到端验证

## Constitution Check

| Principle | Status |
|-----------|--------|
| I. Simplicity First | ✅ PASS — Skills 是文件操作，MCP 是 subprocess + JSON-RPC |
| II-V | ✅ PASS |

## 新增命令一览

| 命令 | 类型 | 功能 |
|------|------|------|
| `/skills` | Skills | 列出所有已安装 Skill |
| `/skill-install <path>` | Skills | 从路径安装 SKILL.md |
| `/skill-uninstall <name>` | Skills | 删除指定 Skill |
| `/mcp` | MCP | 列出 MCP 服务器及连接状态 |
| `/mcp-connect <name>` | MCP | 连接 MCP 服务器 |
| `/mcp-disconnect <name>` | MCP | 断开 MCP 服务器 |
| `/tools` | 汇总 | Skills + MCP + CLI 工具状态 |

## 源代码改动

```text
src/services/skill_service.py     # NEW: Skills CRUD + 扫描 + 热加载
src/services/mcp_service.py       # NEW: MCP JSON-RPC 客户端 + 连接管理
src/cli/renderer.py               # +render_skills_list, render_mcp_status, render_tools_summary
src/cli/app.py                    # +7 命令 + MCP 工具合并到 AI 工具列表
src/config.py                     # +get_mcp_servers()
```

## Implementation

### Phase 1: Skills 管理 (FR-001 ~ FR-004)

- `src/services/skill_service.py`: `list_skills()`, `install_skill(path)`, `uninstall_skill(name)`, 解析 SKILL.md frontmatter
- `renderer.py`: `render_skills_list()` — Rich 表格显示名称/描述/路径
- `app.py`: `/skills`, `/skill-install`, `/skill-uninstall` 命令

### Phase 2: MCP 管理 (FR-005 ~ FR-009)

- `config.py`: `get_mcp_servers()` 读取 config.txt 中 MCP_SERVERS JSON
- `src/services/mcp_service.py`: MCPClient 类 — `connect()`, `disconnect()`, `list_tools()`, `call_tool()`, JSON-RPC over subprocess stdio
- `renderer.py`: `render_mcp_status()` — 表格显示名称/传输/状态
- `app.py`: `/mcp`, `/mcp-connect`, `/mcp-disconnect` + `_register_tools()` 合并 MCP 工具

### Phase 3: CLI + 汇总 (FR-010 ~ FR-011)

- `renderer.py`: `render_tools_summary()` — 三大类型分段展示
- `app.py`: `/tools` 命令
