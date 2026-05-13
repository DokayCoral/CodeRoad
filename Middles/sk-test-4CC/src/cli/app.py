"""Main CLI application: session management, conversation loop, tool execution.

This is the central orchestrator for the Code Clone platform,
implementing the full conversation loop with AI, tool dispatch,
approval flow, and session persistence.
"""

import atexit
import logging
import os
import signal
import sys
import time
from pathlib import Path

from src.config import get_sessions_dir, get_system_prompt, is_configured, get_mcp_servers
from src.models import (
    Message,
    MessageRole,
    Session,
    SessionStatus,
    ToolCall,
    ToolCallStatus,
)
from src.services.ai_service import create_ai_provider
from src.services.context_service import (
    load_project_context,
    compress_messages,
    should_compress,
    estimate_session_tokens,
    get_compress_threshold_tokens,
)
from src.services.session_service import (
    save_session,
    list_recent_sessions,
    load_session,
    delete_session,
    export_session,
)
from src.services.stream_service import StreamHandler
from src.cli.input_handler import create_input_session, get_user_input
from src.cli.renderer import (
    console,
    render_context_report,
    render_welcome,
    render_session_list,
    render_session_manager,
    render_skills_list,
    render_mcp_status,
    render_tools_summary,
    render_streaming_response,
    update_streaming_content,
    render_markdown,
    render_tool_call,
    render_approval_prompt,
    render_status_bar,
    render_task_list,
    render_error,
    render_info,
    render_success,
)
from src.services.context_logger import (
    log_session_saved,
    log_session_loaded,
    log_context_compressed,
    log_project_context_loaded,
)
from src.services.skill_service import list_skills, install_skill, uninstall_skill
from src.services.mcp_service import MCPClient
from src.tools.registry import tool_registry

logger = logging.getLogger(__name__)


def _handle_terminate(signum, frame):
    """Handle SIGTERM: restore screen, then exit."""
    _exit_alternate_screen()
    signal.signal(signum, signal.SIG_DFL)
    os.kill(os.getpid(), signum)


signal.signal(signal.SIGTERM, _handle_terminate)


def execute_tool_call(tc: ToolCall, session: Session | None = None) -> str:
    """Execute a single tool call and update its status.

    Tries registry first, then falls back to connected MCP clients.
    """
    tc.status = ToolCallStatus.EXECUTING
    start = time.time()

    # Try registry first
    result = tool_registry.execute(tc.tool_name, tc.parameters)

    # If not found in registry, try MCP clients
    if result.startswith("[ERROR] Unknown tool") and session:
        mcp_clients = getattr(session, '_mcp_clients', {})
        for name, client in mcp_clients.items():
            if client.is_connected:
                mcp_result = client.call_tool(tc.tool_name, tc.parameters)
                if mcp_result is not None:
                    result = mcp_result
                    break

    tc.result = result
    tc.duration_ms = int((time.time() - start) * 1000)

    if result.startswith("[ERROR]"):
        tc.status = ToolCallStatus.ERROR
    else:
        tc.status = ToolCallStatus.SUCCESS

    return result


def _build_system_prompt(session: Session) -> str:
    """Build the AI system prompt from project context and config."""
    ctx = session.project_context

    parts = [
        "You are a coding assistant that helps with software engineering tasks.",
        "You can use tools to read, write, edit, search code, and execute shell commands.",
        "",
    ]

    if ctx.instructions:
        parts.append("## Project Instructions")
        parts.append(ctx.instructions)
        parts.append("")

    if ctx.tech_stack:
        parts.append(f"**Tech Stack**: {', '.join(ctx.tech_stack)}")
        parts.append("")

    parts.append("## Guidelines")
    parts.append("- Write clean, secure, working code")
    parts.append("- Include necessary imports and error handling")
    parts.append("- Prefer editing existing files over creating new ones")
    parts.append("- Explain your reasoning when making decisions")
    parts.append("- Always use tools when you need to interact with the filesystem")

    # Append custom system prompt from config.txt if configured
    custom_prompt = get_system_prompt()
    if custom_prompt:
        parts.append("")
        parts.append("## Custom Instructions")
        parts.append(custom_prompt)

    return "\n".join(parts)


def _build_messages(session: Session) -> list[dict]:
    """Build AI API message list from session messages, handling compression."""
    messages = session.messages

    if should_compress(messages):
        before_msgs = len(messages)
        before_tokens = estimate_session_tokens(messages)
        logger.info(
            "Compressing conversation: %d messages, ~%d tokens",
            before_msgs, before_tokens,
        )
        messages = compress_messages(messages)
        log_context_compressed(
            before_msgs=before_msgs, after_msgs=len(messages),
            before_tokens=before_tokens, after_tokens=estimate_session_tokens(messages),
        )
        render_info("Conversation compressed to fit within context window")

    api_messages = []
    for msg in messages:
        if msg.content or msg.tool_calls:
            api_messages.append(msg.to_api_message())

    return api_messages


def handle_tool_calls(
    tool_calls: list[ToolCall], ai_message: Message, session: Session | None = None
) -> bool:
    """Handle a batch of tool calls from the AI.

    Returns True if all tool calls were processed, False if any were cancelled.
    """
    for tc in tool_calls:
        # Check permissions
        needs_approval = tool_registry.needs_approval(tc.tool_name, tc.parameters)

        if needs_approval:
            tc.approval_required = True
            approved = render_approval_prompt(tc)
            if not approved:
                tc.status = ToolCallStatus.CANCELLED
                tc.result = "User cancelled the operation"
                tc.approved_by_user = False
                render_tool_call(tc)
                ai_message.tool_calls.append(tc)
                continue
            tc.approved_by_user = True
            tc.status = ToolCallStatus.APPROVED

        # Execute
        render_tool_call(tc)
        result = execute_tool_call(tc, session)
        render_tool_call(tc)

        ai_message.tool_calls.append(tc)

    return True


def run_conversation(session: Session) -> None:
    """Main conversation loop."""
    provider = create_ai_provider()
    system_prompt = _build_system_prompt(session)
    input_session = create_input_session()

    # Log and display project context
    ctx = session.project_context
    if ctx.config_file_path:
        render_info(f"已加载项目上下文: {ctx.config_file_path} ({len(ctx.instructions)} 字符)")
        log_project_context_loaded(
            source_file=ctx.config_file_path,
            tech_stack=ctx.tech_stack,
            instructions_len=len(ctx.instructions),
        )
    else:
        render_info("未检测到项目配置文件，AI 将使用通用规则")
        log_project_context_loaded(
            source_file="(none)",
            tech_stack=ctx.tech_stack,
            instructions_len=0,
        )

    render_welcome()
    render_info(f"Project: {ctx.project_name}")
    if ctx.tech_stack:
        render_info(f"Tech Stack: {', '.join(ctx.tech_stack)}")

    # Track token delta for status bar (mutable container for assignment in closure)
    _token_state = {"prev": estimate_session_tokens(session.messages)}

    render_status_bar(
        msg_count=len(session.messages),
        est_tokens=_token_state["prev"],
        session_id=session.id,
        compress_threshold=get_compress_threshold_tokens(),
    )

    while True:
        # Get user input
        user_text = get_user_input(input_session, "\n> ")
        if user_text is None:
            render_info("Goodbye!")
            sys.exit(0)

        user_text = user_text.strip()
        if not user_text:
            continue

        # Handle special commands
        if user_text.lower() in ("/help", "/?"):
            render_help()
            continue
        if user_text.lower() == "/context":
            render_context_report(
                session_id=session.id,
                msg_count=len(session.messages),
                est_tokens=estimate_session_tokens(session.messages),
                compress_threshold=get_compress_threshold_tokens(),
                compressed=should_compress(session.messages),
                session_path=str(
                    Path.home() / ".claude-code-clone" / "sessions"
                    / session.created_at.strftime("%Y-%m-%d") / f"{session.id}.json"
                ),
                project_source=session.project_context.config_file_path or "(none)",
                tech_stack=session.project_context.tech_stack,
            )
            continue
        if user_text.lower() == "/clear":
            # Reset conversation but keep project context
            session.messages.clear()
            save_session(session)
            render_info("Conversation cleared. Project context preserved.")
            render_status_bar(
                msg_count=0, est_tokens=0,
                session_id=session.id,
                compress_threshold=get_compress_threshold_tokens(),
            )
            continue
        if user_text.lower() == "/compress":
            before_msgs = len(session.messages)
            before_tokens = estimate_session_tokens(session.messages)
            if before_msgs <= 20:
                render_info("Not enough messages to compress (need >20)")
                continue
            session.messages = compress_messages(session.messages)
            log_context_compressed(
                before_msgs=before_msgs, after_msgs=len(session.messages),
                before_tokens=before_tokens, after_tokens=estimate_session_tokens(session.messages),
            )
            save_session(session)
            render_info(f"Compressed: {before_msgs} → {len(session.messages)} messages, ~{before_tokens} → ~{estimate_session_tokens(session.messages)} tokens")
            continue
        if user_text.lower() == "/reload":
            ctx = load_project_context(Path.cwd())
            session.project_context = ctx
            log_project_context_loaded(
                source_file=ctx.config_file_path or "(none)",
                tech_stack=ctx.tech_stack,
                instructions_len=len(ctx.instructions),
            )
            save_session(session)
            if ctx.config_file_path:
                render_info(f"Reloaded: {ctx.config_file_path} ({len(ctx.instructions)} chars)")
            else:
                render_info("Reloaded: no project config found")
            continue
        if user_text.lower().startswith("/rollback"):
            parts = user_text.split()
            if len(parts) != 2 or not parts[1].isdigit():
                render_error("Usage: /rollback N (keep first N messages)")
                continue
            n = int(parts[1])
            if n < 0 or n > len(session.messages):
                render_error(f"Invalid: must be 0-{len(session.messages)}")
                continue
            session.messages = session.messages[:n]
            save_session(session)
            render_info(f"Rolled back to {n} messages")
            continue
        if user_text.lower() == "/pin":
            # Pin the last user message
            for msg in reversed(session.messages):
                if msg.role == MessageRole.USER:
                    msg.pinned = True
                    save_session(session)
                    render_info(f"Pinned message: {msg.content[:60]}...")
                    break
            else:
                render_error("No user message to pin")
            continue
        if user_text.lower() == "/sessions":
            try:
                render_session_manager()
                try:
                    choice = console.input("  Delete session # (or Enter to skip): ")
                except (KeyboardInterrupt, EOFError):
                    choice = ""
                if choice and choice.strip().isdigit():
                    sessions_list = list_recent_sessions(50)
                    idx = int(choice.strip()) - 1
                    if 0 <= idx < len(sessions_list):
                        sid = sessions_list[idx]["id"]
                        if sid == session.id:
                            render_error("Cannot delete the currently active session")
                        else:
                            if delete_session(sid):
                                render_success(f"Deleted session {sid[:8]}...")
                            else:
                                render_error("Delete failed")
            except Exception as e:
                render_error(f"Sessions command failed: {e}")
                logger.exception("sessions command error")
            continue
        if user_text.lower() == "/export":
            path = export_session(session.id)
            if path:
                render_success(f"Exported to: {path}")
            else:
                render_error("Export failed")
            continue

        # === Skills commands ===
        if user_text.lower() == "/skills":
            render_skills_list(list_skills())
            continue
        if user_text.lower().startswith("/skill-install"):
            parts = user_text.split(maxsplit=1)
            if len(parts) < 2:
                render_error("Usage: /skill-install <path>")
            else:
                try:
                    info = install_skill(parts[1].strip())
                    if info:
                        render_success(f"Installed: {info['name']}")
                    else:
                        render_error("Invalid or missing SKILL.md file")
                except FileExistsError as e:
                    render_error(str(e))
            continue
        if user_text.lower().startswith("/skill-uninstall"):
            parts = user_text.split(maxsplit=1)
            if len(parts) < 2:
                render_error("Usage: /skill-uninstall <name>")
            else:
                ok = uninstall_skill(parts[1].strip())
                if ok:
                    render_success("Skill uninstalled")
                else:
                    render_error("Skill not found")
            continue

        # === MCP commands ===
        if user_text.lower() == "/mcp":
            servers = get_mcp_servers()
            render_mcp_status(servers, getattr(session, '_mcp_clients', {}))
            continue
        if user_text.lower().startswith("/mcp-connect"):
            parts = user_text.split(maxsplit=1)
            if len(parts) < 2:
                render_error("Usage: /mcp-connect <name>")
            else:
                name = parts[1].strip()
                servers = get_mcp_servers()
                target = next((s for s in servers if s.get("name") == name), None)
                if not target:
                    render_error(f"MCP server not found: {name}")
                else:
                    if not hasattr(session, '_mcp_clients'):
                        session._mcp_clients = {}
                    client = MCPClient(name, target["command"], target.get("args", []))
                    if client.connect():
                        session._mcp_clients[name] = client
                        render_success(f"Connected to {name} ({client.tool_count} tools)")
                    else:
                        render_error(f"Failed to connect: {name}")
            continue
        if user_text.lower().startswith("/mcp-disconnect"):
            parts = user_text.split(maxsplit=1)
            if len(parts) < 2:
                render_error("Usage: /mcp-disconnect <name>")
            else:
                name = parts[1].strip()
                clients = getattr(session, '_mcp_clients', {})
                client = clients.pop(name, None)
                if client:
                    client.disconnect()
                    render_success(f"Disconnected: {name}")
                else:
                    render_error(f"Not connected: {name}")
            continue

        # === /tools summary ===
        if user_text.lower() == "/tools":
            skills = list_skills()
            mcp_servers = get_mcp_servers()
            mcp_clients = getattr(session, '_mcp_clients', {})
            cli_tools_list = [
                {"name": t.name, "description": t.description}
                for t in tool_registry.list_all()
            ]
            render_tools_summary(skills, mcp_servers, mcp_clients, cli_tools_list)
            continue

        if user_text.lower() == "/tasks":
            render_task_list(session.task_list)
            continue
        if user_text.lower() in ("/exit", "/quit"):
            render_info("Goodbye!")
            sys.exit(0)

        # Catch-all: any unrecognized / command
        if user_text.startswith("/"):
            render_error(f"Unknown command: {user_text.split()[0]}. Type /help for available commands.")
            continue

        # Create user message
        user_msg = Message(role=MessageRole.USER, content=user_text)
        session.add_message(user_msg)

        # Get API messages
        api_messages = _build_messages(session)
        tools = tool_registry.get_schemas()

        # Merge connected MCP server tools
        mcp_clients = getattr(session, '_mcp_clients', {})
        mcp_tool_names: set[str] = set()
        for name, client in mcp_clients.items():
            if client.is_connected and client._tools:
                for t in client._tools:
                    t_name = t.get("name", "")
                    if t_name and t_name not in mcp_tool_names:
                        mcp_tool_names.add(t_name)
                        tools.append({
                            "name": t_name,
                            "description": t.get("description", f"MCP tool from {name}"),
                            "input_schema": t.get("inputSchema", {"type": "object", "properties": {}}),
                        })

        # Stream AI response
        try:
            stream = provider.stream_response(api_messages, tools, system_prompt)
        except Exception as e:
            render_error(f"API call failed: {e}")
            error_msg = Message(
                role=MessageRole.SYSTEM,
                content=f"[Error: {e}]",
            )
            session.add_message(error_msg)
            continue

        handler = StreamHandler()
        ai_message = Message(role=MessageRole.ASSISTANT, content="")
        live = render_streaming_response()

        try:
            for text_delta, tool_calls_result, is_complete in handler.process_stream(stream):
                if text_delta:
                    update_streaming_content(live, handler.accumulated_text)

                if tool_calls_result:
                    # Stop live rendering before handling tools
                    live.stop()
                    ai_message.content = handler.accumulated_text
                    if ai_message.content:
                        session.add_message(ai_message)

                    # Create a new message for tool results
                    tool_msg = Message(role=MessageRole.ASSISTANT, content="")
                    handle_tool_calls(tool_calls_result, tool_msg, session)

                    if tool_msg.tool_calls:
                        session.add_message(tool_msg)

                    # Send tool results back to AI for follow-up
                    api_messages = _build_messages(session)
                    try:
                        followup_stream = provider.stream_response(
                            api_messages, tools, system_prompt,
                        )
                        handler.reset()
                        live = render_streaming_response()

                        ai_followup = Message(role=MessageRole.ASSISTANT, content="")
                        try:
                            for td, tc2, ic2 in handler.process_stream(followup_stream):
                                if td:
                                    update_streaming_content(live, handler.accumulated_text)
                                if ic2:
                                    ai_followup.content = handler.accumulated_text
                                    if ai_followup.content:
                                        session.add_message(ai_followup)
                        except KeyboardInterrupt:
                            # Interrupt current stream, preserve partial, stay in conversation
                            render_info("Interrupted")
                            ai_followup.content = handler.accumulated_text
                            if ai_followup.content:
                                session.add_message(ai_followup)
                    except Exception as e:
                        render_error(f"Follow-up API call failed: {e}")
                    break

                if is_complete:
                    break

        except KeyboardInterrupt:
            # Interrupt current stream, preserve partial, stay in conversation
            render_info("Interrupted — partial response preserved")
            ai_message.content = handler.accumulated_text
            if ai_message.content:
                session.add_message(ai_message)
        except Exception as e:
            # Prevent any streaming error from crashing the system
            render_error(f"Stream error: {e}")
            logger.exception("Streaming error")

        finally:
            try:
                live.stop()
            except Exception:
                pass

        # Add AI message and render statically (in case Live display stopped)
        if handler.accumulated_text and not ai_message.tool_calls:
            ai_message.content = handler.accumulated_text
            ai_message.token_count = len(handler.accumulated_text) // 4
            session.add_message(ai_message)
            console.print("")  # Ensure newline after streaming
            render_markdown(ai_message.content)

        # Save session after each turn
        try:
            saved_path = save_session(session)
            log_session_saved(
                msg_count=len(session.messages),
                token_count=estimate_session_tokens(session.messages),
                file_path=str(saved_path),
            )
        except Exception as e:
            render_error(f"Failed to save session: {e}")

        # Render status bar before next prompt (with token delta)
        cur_tokens = estimate_session_tokens(session.messages)
        delta = cur_tokens - _token_state["prev"]
        _token_state["prev"] = cur_tokens
        render_status_bar(
            msg_count=len(session.messages),
            est_tokens=cur_tokens,
            session_id=session.id,
            compress_threshold=get_compress_threshold_tokens(),
            delta_tokens=delta if delta > 0 else 0,
        )


def render_help() -> None:
    """Display help text."""
    render_markdown("""
## Commands

| Command | Description |
|---------|-------------|
| `/help` | Show this help |
| `/context` | Show context status report |
| `/clear` | Clear conversation history |
| `/compress` | Compress conversation context |
| `/pin` | Pin last message (survives compression) |
| `/rollback N` | Revert to first N messages |
| `/reload` | Reload project context (CLAUDE.md) |
| `/sessions` | Manage saved sessions (list/delete) |
| `/export` | Export current session to Markdown |
| `/skills` | List installed skills |
| `/skill-install` | Install a SKILL.md |
| `/skill-uninstall` | Uninstall a skill |
| `/mcp` | Show MCP server status |
| `/mcp-connect` | Connect to MCP server |
| `/mcp-disconnect` | Disconnect from MCP server |
| `/tools` | Show tool inventory (Skills/MCP/CLI) |
| `/tasks` | Show task list |
| `/exit` | Exit current session |
| `Ctrl+C` | Interrupt AI response |
| `Ctrl+D` | Exit |
""")


def _enable_windows_ansi() -> None:
    """Enable ANSI escape sequence processing on Windows consoles.

    Without this, \\033 escape codes are ignored on classic Windows CMD.
    Windows Terminal has native ANSI support and doesn't need this.
    """
    if sys.platform != "win32":
        return
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        # STD_OUTPUT_HANDLE = -11
        handle = kernel32.GetStdHandle(-11)
        if handle == 0 or handle == -1:
            return  # Invalid handle (e.g., redirected)
        mode = ctypes.c_uint32()
        if not kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
            return
        # ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004
        kernel32.SetConsoleMode(handle, mode.value | 0x0004)
    except Exception:
        pass  # Best effort — ANSI might not work on very old Windows


def _enter_alternate_screen() -> None:
    """Switch to the terminal's alternate screen buffer (like vim/less/htop).

    Enables Windows ANSI processing if needed, then uses escape sequence
    \\033[?1049h. Falls back to console.clear() for non-TTY environments.
    """
    _enable_windows_ansi()
    if sys.stdout.isatty():
        sys.stdout.write("\033[?1049h")
        sys.stdout.flush()
    else:
        console.clear()


def _exit_alternate_screen() -> None:
    """Restore the terminal's main screen buffer.

    Uses ANSI escape sequence \\033[?1049l. This brings back the original
    terminal content exactly as it was before entering the alternate screen.
    """
    if sys.stdout.isatty():
        sys.stdout.write("\033[?1049l")
        sys.stdout.flush()


def _restore_screen_on_exit() -> None:
    """Restore terminal screen on exit. Called via atexit and signal handlers."""
    _exit_alternate_screen()


# Register screen restoration for normal exit path (belt and suspenders with signal handlers above)
atexit.register(_restore_screen_on_exit)


def main():
    """Main entry point for Code Clone CLI.

    1. Enters alternate screen buffer (clean full-screen workspace)
    2. Shows session selection UI (list recent or create new)
    3. Loads/Creates session
    4. Runs the conversation loop
    5. On exit: restores original terminal screen automatically

    The alternate screen buffer creates a "new window" experience —
    the original terminal content is hidden during the session and
    fully restored when the program exits, even on Ctrl+C.
    """
    # Setup logging
    logging.basicConfig(
        level=logging.WARNING,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    # Check config.txt has a valid auth token
    if not is_configured():
        print("请在 src/config.txt 中配置有效的 ANTHROPIC_AUTH_TOKEN")
        print("格式: ANTHROPIC_AUTH_TOKEN=\"sk-xxxxx\"")
        sys.exit(1)

    # Enter alternate screen buffer for clean full-screen workspace
    _enter_alternate_screen()

    # Show initial status bar (persists through session selection)
    render_status_bar(msg_count=0, est_tokens=0)

    # Ensure config directory
    get_sessions_dir()

    # Ensure skills directory exists
    from src.services.skill_service import SKILLS_DIR
    SKILLS_DIR.mkdir(parents=True, exist_ok=True)

    # Register tools (once)
    _register_tools()

    try:
        while True:
            # Show session selection
            recent_sessions = list_recent_sessions()
            try:
                session_id = render_session_list(recent_sessions)
            except EOFError:
                break  # Ctrl+D at session list → exit program

            if session_id:
                session = load_session(session_id)
                if session:
                    session.status = SessionStatus.ACTIVE
                    log_session_loaded(session_id, len(session.messages))
                    render_success(f"Loaded session {session_id[:8]}...")
                    run_conversation(session)
                else:
                    render_error(f"Session {session_id[:8]}... not found, creating new")
                    project_context = load_project_context(Path.cwd())
                    session = Session(project_context=project_context)
                    render_success("New session created")
                    run_conversation(session)
            else:
                # Create new session
                project_context = load_project_context(Path.cwd())
                session = Session(project_context=project_context)
                render_success("New session created")
                run_conversation(session)
    except KeyboardInterrupt:
        render_info("\nGoodbye!")
    except Exception as e:
        render_error(f"Fatal error: {e}")
        logger.exception("Fatal error in main")
        sys.exit(1)


def _register_tools() -> None:
    """Register all tools into the global registry."""
    from src.tools.registry import ToolDef, PermissionLevel, tool_registry
    from src.tools.read import read_file
    from src.tools.write import write_file
    from src.tools.edit import edit_file
    from src.tools.grep import grep_search
    from src.tools.glob import glob_search
    from src.tools.bash import execute_bash

    tool_registry.register(ToolDef(
        name="read",
        description="Read a file from the local filesystem. Supports offset and limit for partial reads.",
        parameters={
            "file_path": {"type": "string", "description": "Absolute path to the file to read"},
            "offset": {"type": "integer", "description": "Starting line number (0-indexed)"},
            "limit": {"type": "integer", "description": "Maximum number of lines to read (default 2000)"},
        },
        permission_level=PermissionLevel.READ,
        handler=read_file,
    ))

    tool_registry.register(ToolDef(
        name="write",
        description="Create or overwrite a file. Prompts user to confirm if file doesn't exist.",
        parameters={
            "file_path": {"type": "string", "description": "Absolute path to write to"},
            "content": {"type": "string", "description": "Full file content to write"},
        },
        permission_level=PermissionLevel.WRITE,
        handler=write_file,
    ))

    tool_registry.register(ToolDef(
        name="edit",
        description="Perform exact string replacement in an existing file. old_string must be unique in the file.",
        parameters={
            "file_path": {"type": "string", "description": "Absolute path to the file to edit"},
            "old_string": {"type": "string", "description": "Exact text to find and replace"},
            "new_string": {"type": "string", "description": "Replacement text"},
        },
        permission_level=PermissionLevel.WRITE,
        handler=edit_file,
    ))

    tool_registry.register(ToolDef(
        name="grep",
        description="Search file contents using regex pattern matching. Supports file type filters and context lines.",
        parameters={
            "pattern": {"type": "string", "description": "Regular expression to search for"},
            "path_str": {"type": "string", "description": "File or directory to search in (default: current directory)"},
            "glob": {"type": "string", "description": "File pattern filter (e.g., '*.py')"},
            "output_mode": {"type": "string", "description": "Output mode: content, files_with_matches, or count"},
            "context": {"type": "integer", "description": "Lines of context around matches"},
            "case_insensitive": {"type": "boolean", "description": "Case-insensitive search"},
            "head_limit": {"type": "integer", "description": "Max results to return (default 250)"},
        },
        permission_level=PermissionLevel.READ,
        handler=grep_search,
    ))

    tool_registry.register(ToolDef(
        name="glob",
        description="Fast file pattern matching. Returns file paths sorted by modification time.",
        parameters={
            "pattern": {"type": "string", "description": "Glob pattern (e.g., '**/*.py', 'src/**/*.tsx')"},
            "path_str": {"type": "string", "description": "Root directory to search from (default: current directory)"},
        },
        permission_level=PermissionLevel.READ,
        handler=glob_search,
    ))

    tool_registry.register(ToolDef(
        name="bash",
        description="Execute a shell command and return its output. Read-only commands auto-execute; destructive commands require approval.",
        parameters={
            "command": {"type": "string", "description": "Shell command to execute"},
            "timeout": {"type": "integer", "description": "Timeout in seconds (1-120, default 30)"},
            "description": {"type": "string", "description": "Human-readable description of what the command does"},
        },
        permission_level=PermissionLevel.SHELL_WRITE,
        handler=execute_bash,
    ))


if __name__ == "__main__":
    main()
