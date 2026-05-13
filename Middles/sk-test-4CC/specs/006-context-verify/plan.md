# Implementation Plan: 上下文管理可视化与验证

**Branch**: `006-context-verify` | **Date**: 2026-05-12 | **Spec**: [spec.md](./spec.md)

## Summary

完成全部 12 项未实现的上下文管理功能（5 个维度 × 26 项功能），并为每项提供可操作的验证方法。目标：/help 列出 11 个命令，/context 显示 7 项信息，context.log 记录 4 种事件，所有功能均可在 15 分钟内完成端到端验证。

## Phase 0 成果（已实现）

- `/context` 命令 + `render_context_report()` 渲染
- `context_logger.py` — JSONL 事件日志（SESSION_SAVED/LOADED/COMPRESSED/PROJECT_CONTEXT_LOADED）
- 启动时项目上下文确认显示
- 状态栏 （spec 005）持续显示消息数和 token 百分比

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: langchain, langchain-anthropic（LLM 摘要）；已有 rich + prompt_toolkit
**Storage**: `~/.claude-code-clone/` (session JSON + context.log)
**Testing**: 手动端到端验证流程

## Constitution Check

| Principle | Status |
|-----------|--------|
| I. Simplicity First | ✅ PASS — 每个新功能都是独立的命令处理或配置项 |
| II-V | ✅ PASS |

## Implementation: 12 项功能 × 3 批次

### 批次 A：上下文控制（5 命令 + 1 配置项）

| Task | 文件 | 内容 |
|------|------|------|
| A1 | `src/cli/app.py` | `/clear` — 清空对话历史保留项目上下文 |
| A2 | `src/cli/app.py` | `/compress` — 手动触发上下文压缩 |
| A3 | `src/cli/app.py` | `/reload` — 不重启重新加载 CLAUDE.md |
| A4 | `src/cli/app.py` | `/rollback N` — 丢弃第 N 条消息之后的所有对话 |
| A5 | `src/cli/app.py` | `/pin` — 标记最后一条用户消息为 pinned |
| A6 | `src/models/__init__.py` | Message 新增 `pinned: bool` 和 `input_tokens: int` / `output_tokens: int` |
| A7 | `src/services/context_service.py` | `compress_messages` 跳过 `pinned=True` 的消息 |
| A8 | `src/config.py` | 读取 `SYSTEM_PROMPT` 和 `COMPRESSION_THRESHOLD` |
| A9 | `src/cli/app.py` | `_build_system_prompt` 拼接自定义 SYSTEM_PROMPT |

### 批次 B：会话管理（2 命令 + 1 服务函数）

| Task | 文件 | 内容 |
|------|------|------|
| B1 | `src/services/session_service.py` | `delete_session(session_id)` — 删除会话 JSON 文件 |
| B2 | `src/services/session_service.py` | `export_session(session)` — 导出为 Markdown 文件 |
| B3 | `src/cli/app.py` | `/sessions` — 会话管理界面（列表 / 删除） |
| B4 | `src/cli/app.py` | `/export` — 导出当前会话为 .md 文件 |

### 批次 C：可见性增强（1 项显示）

| Task | 文件 | 内容 |
|------|------|------|
| C1 | `src/cli/renderer.py` | `render_status_bar` 增加上一轮 token 消耗量 |
| C2 | `src/cli/renderer.py` | `render_context_report` 增加最后几轮 token 趋势 |

## 源代码改动汇总

```text
src/cli/app.py                   # +8 命令: /clear /compress /reload /rollback /pin /sessions /export (增强 /context)
src/models/__init__.py           # Message.pinned, Message.input_tokens, Message.output_tokens
src/config.py                    # SYSTEM_PROMPT + COMPRESSION_THRESHOLD 读取
src/services/context_service.py  # compress_messages 跳过 pinned 消息
src/services/session_service.py  # delete_session + export_session
src/cli/renderer.py              # render_status_bar Δtoken + render_context_report 趋势
```

## 验证：全量 26 项端到端流程

```bash
# === 准备 ===
echo 'SYSTEM_PROMPT="请所有回复使用英文"' >> src/config.txt
echo "# Test Rules\n- Use Go style" > CLAUDE.md
mkdir -p src/sub && echo "# Sub Project" > src/sub/CLAUDE.md

# === 启动 ===
python -m src.cli/app.py
# [obs] 启动时看到 "已加载项目上下文: CLAUDE.md"
# [obs] 状态栏在最底部显示

# === 在对话中验证 ===
> /context          # [obs] 7 项信息完整显示
> /help             # [obs] 所有命令在列表中

# 验证存储和恢复
> 帮我写一个 hello world 函数
> /context          # [obs] Msg:4 (含 AI 回复)
> /exit             # 退出
# [file] cat ~/.claude-code-clone/sessions/.../<id>.json | grep -c '"role"'  确认 >0

# 重新启动恢复
> python -m src.cli.app
> [选择刚才的会话]
> 我们刚才聊了什么？
# [obs] AI 记得之前的对话

# 验证压缩
> /compress         # [cmd] 手动压缩
> /context          # [obs] 确认数值变化

# 验证清除
> /clear            # [cmd]
> /context          # [obs] Msg:0, 但 Project Context 不变

# 验证 pin
> 这是一条重要消息，请记住
> /pin              # [cmd]
> /context          # [obs] 确认 pinned

# 验证 rollback
> /rollback 2       # [cmd]
> /context          # [obs] 确认消息数减少

# 验证 export
> /export           # [cmd]
# [file] cat exported_*.md | head -50  确认同步输出

# 验证 delete
> /sessions         # [cmd]
> [选择删除]
# [obs] 重启后会话不在列表中

# 验证 reload
# 修改 CLAUDE.md
> /reload           # [cmd]
> /context          # [obs] Config 更新时间变化

# === 退出验证 ===
> /exit
# [file] cat ~/.claude-code-clone/context.log  确认 4 种事件类型
# [file] cat exported_*.md  确认 Markdown 格式正确

# === 清理 ===
rm CLAUDE.md src/sub/CLAUDE.md
git checkout src/config.txt  # 恢复原始配置
```

## 成功标准

- `/help` 列出所有 9 个命令（/help /context /clear /compress /pin /rollback /reload /tasks /exit）；/sessions /export 为附加管理命令
- `/context` 显示 7 项信息
- `context.log` 包含 4 种事件类型
- 状态栏显示 Msg/Token/Δtoken
- 26 项验证方法全部可通过
