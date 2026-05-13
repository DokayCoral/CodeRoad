"""Rich-based terminal renderer for AI responses and UI components.

Handles:
- Streaming Markdown rendering with code syntax highlighting
- Tool call status display
- Task list rendering
- Session selection UI
"""

import re
from typing import Optional

from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.layout import Layout
from rich import box

from src.models import ToolCall, ToolCallStatus, Task, TaskStatus

console = Console()


def render_streaming_response() -> Live:
    """Create a Live context for streaming Markdown rendering.

    Returns a Live display that can be updated incrementally.
    """
    md = Markdown("", code_theme="monokai")
    return Live(md, console=console, refresh_per_second=10, transient=False)


def update_streaming_content(live: Live, text: str) -> None:
    """Update the streaming display with accumulated text."""
    # Clean text for Markdown rendering (strip leading whitespace in code blocks)
    live.update(Markdown(text, code_theme="monokai"))


def render_markdown(text: str) -> None:
    """Render complete Markdown text at once."""
    console.print(Markdown(text, code_theme="monokai"))


def render_tool_call(tool_call: ToolCall) -> None:
    """Render a tool call status indicator."""
    status_colors = {
        ToolCallStatus.PENDING: "yellow",
        ToolCallStatus.APPROVED: "blue",
        ToolCallStatus.EXECUTING: "yellow",
        ToolCallStatus.SUCCESS: "green",
        ToolCallStatus.ERROR: "red",
        ToolCallStatus.CANCELLED: "dim",
    }
    color = status_colors.get(tool_call.status, "white")

    icon_map = {
        ToolCallStatus.PENDING: "⏳",
        ToolCallStatus.APPROVED: "✓",
        ToolCallStatus.EXECUTING: "⚙",
        ToolCallStatus.SUCCESS: "✓",
        ToolCallStatus.ERROR: "✗",
        ToolCallStatus.CANCELLED: "⊘",
    }
    icon = icon_map.get(tool_call.status, "?")

    params_str = ", ".join(f"{k}={v}" for k, v in tool_call.parameters.items())

    text = Text()
    text.append(f"  {icon} ", style=color)
    text.append(f"{tool_call.tool_name}", style=f"bold {color}")
    if params_str:
        text.append(f"({params_str[:80]})", style="dim")
    if tool_call.duration_ms:
        text.append(f" [{tool_call.duration_ms}ms]", style="dim")

    console.print(text)


def render_tool_result(tool_call: ToolCall) -> None:
    """Render a tool execution result."""
    if tool_call.status == ToolCallStatus.ERROR:
        console.print(f"  [red]Error:[/red] {tool_call.result}")
    elif tool_call.result and len(tool_call.result) < 500:
        console.print(f"  [dim]{tool_call.result[:500]}[/dim]")


def render_approval_prompt(tool_call: ToolCall) -> bool:
    """Ask user for tool execution approval.

    Returns True if approved, False otherwise.
    """
    console.print()
    console.print(f"  [bold yellow]Tool:[/bold yellow] {tool_call.tool_name}")
    params_str = ", ".join(f"{k}={v}" for k, v in tool_call.parameters.items())
    console.print(f"  [dim]Parameters:[/dim] {params_str[:200]}")

    try:
        response = input("  Execute? [Y/n] ").strip().lower()
        return response in ("", "y", "yes")
    except (KeyboardInterrupt, EOFError):
        return False


def render_session_list(sessions: list[dict]) -> Optional[str]:
    """Display recent session list and let user choose.

    Returns session ID or None for new session.
    """
    console.clear()
    console.print()
    console.print(Panel.fit(
        "[bold]Code Clone[/bold] - Session Manager",
        border_style="blue",
    ))
    console.print()

    table = Table(box=box.SIMPLE, show_header=True)
    table.add_column("#", style="dim", width=3)
    table.add_column("Session", style="bold")
    table.add_column("Messages", justify="right")
    table.add_column("Preview", style="dim", max_width=60)

    table.add_row("N", "[green]New Session[/green]", "", "Start a new coding session")

    for i, sess in enumerate(sessions, 1):
        msg_count = sess.get("message_count", 0)
        preview = sess.get("preview", "")[:55]
        created = sess.get("created_at", "")
        if created:
            created = created[:10]
        table.add_row(
            str(i),
            f"{created} ({sess['id'][:8]}...)",
            str(msg_count),
            preview,
        )

    console.print(table)
    console.print()

    try:
        choice = input("  Select session (N for new): ").strip()
        if choice.lower() in ("", "n", "new"):
            return None
        idx = int(choice) - 1
        if 0 <= idx < len(sessions):
            return sessions[idx]["id"]
    except ValueError:
        pass
    return None


def render_task_list(tasks: list[Task]) -> None:
    """Render a task list with status indicators."""
    if not tasks:
        return

    console.print()
    table = Table(box=box.SIMPLE, show_header=True, title="Tasks")
    table.add_column("ID", style="dim", width=6)
    table.add_column("Status", width=8)
    table.add_column("Title", style="bold")
    table.add_column("Deps", style="dim", width=8)

    status_icons = {
        TaskStatus.PENDING: "[dim]⏳ PEND[/dim]",
        TaskStatus.IN_PROGRESS: "[yellow]⚙ DOING[/yellow]",
        TaskStatus.COMPLETED: "[green]✓ DONE[/green]",
        TaskStatus.CANCELLED: "[dim]⊘ CANC[/dim]",
    }

    for task in tasks:
        icon = status_icons.get(task.status, "?")
        deps = ", ".join(d[:8] for d in task.dependencies) if task.dependencies else "-"
        table.add_row(task.id[:6], icon, task.title[:60], deps)

    console.print(table)


def render_welcome() -> None:
    """Render the welcome banner."""
    console.print()
    console.print(Panel.fit(
        "[bold blue]Code Clone v1.0.0[/bold blue]\n"
        "[dim]A Claude Code core functionality clone for learning[/dim]\n\n"
        "• AI-powered coding assistant with streaming responses\n"
        "• File tools: read, write, edit, search\n"
        "• Shell command execution with safety gates\n"
        "• Project context awareness\n"
        "• Session management\n"
        "• Task tracking\n\n"
        "[dim]Type /help for commands, Ctrl+C to interrupt, Ctrl+D to exit[/dim]",
        border_style="blue",
    ))


def render_session_manager() -> None:
    """Render a session management interface (list + delete)."""
    from src.services.session_service import list_recent_sessions

    sessions = list_recent_sessions(50)
    if not sessions:
        console.print("  [dim]No saved sessions found.[/dim]")
        return

    table = Table(box=box.SIMPLE, show_header=True, title="Session Manager")
    table.add_column("#", style="dim", width=3)
    table.add_column("Date", width=10)
    table.add_column("Session ID", width=10)
    table.add_column("Msgs", justify="right", width=5)
    table.add_column("Preview", style="dim", max_width=50)

    for i, s in enumerate(sessions, 1):
        created = s.get("created_at", "")[:10]
        table.add_row(
            str(i),
            created,
            s["id"][:8],
            str(s.get("message_count", 0)),
            s.get("preview", "")[:50],
        )

    console.print(table)
    console.print("  [dim]Enter # to delete, or press Enter to skip[/dim]")


def render_status_bar(
    msg_count: int = 0,
    est_tokens: int = 0,
    session_id: str = "",
    compress_threshold: int = 126000,
    delta_tokens: int = 0,
) -> None:
    """Render a persistent status bar. Also updates prompt_toolkit toolbar."""
    from src.cli.input_handler import set_toolbar_text

    pct = min(100, int(est_tokens / compress_threshold * 100)) if compress_threshold else 0
    bar_plain = f"Msg:{msg_count}  Token:~{est_tokens:,} ({pct}%)"
    if delta_tokens > 0:
        bar_plain += f"  +{delta_tokens:,}"
    if session_id:
        bar_plain += f"  {session_id[:8]}"

    # Sync to prompt_toolkit bottom toolbar — the ONLY status bar location
    set_toolbar_text(bar_plain)


def render_context_report(
    session_id: str,
    msg_count: int,
    est_tokens: int,
    compress_threshold: int,
    compressed: bool,
    session_path: str,
    project_source: str,
    tech_stack: list[str],
) -> None:
    """Render a detailed context status report for the /context command."""
    pct = min(100, int(est_tokens / compress_threshold * 100)) if compress_threshold else 0

    console.print()
    console.print(Panel.fit(
        f"[bold]Session[/bold]  {session_id}\n"
        f"[bold]Messages[/bold]  {msg_count}\n"
        f"[bold]Tokens[/bold]    ~{est_tokens:,} / {compress_threshold:,} ({pct}%)\n"
        f"[bold]Compressed[/bold] {'Yes' if compressed else 'No'}\n"
        f"[bold]Storage[/bold]    {session_path}\n"
        f"[bold]Config[/bold]     {project_source or '(none)'}\n"
        f"[bold]Tech Stack[/bold] {', '.join(tech_stack) if tech_stack else '(none)'}",
        title="Context Status",
        border_style="blue",
    ))
    console.print()


def render_error(message: str) -> None:
    """Render an error message."""
    console.print(f"  [red]✗ {message}[/red]")


def render_info(message: str) -> None:
    """Render an info message."""
    console.print(f"  [blue]ℹ {message}[/blue]")


def render_skills_list(skills: list[dict]) -> None:
    """Render installed skills as a Rich table."""
    if not skills:
        console.print("  [dim]No skills installed.[/dim]")
        console.print("  [dim]Use /skill-install <path> to add a SKILL.md[/dim]")
        return

    table = Table(box=box.SIMPLE, show_header=True, title="Installed Skills")
    table.add_column("Name", style="bold")
    table.add_column("Description", style="dim", max_width=50)
    table.add_column("File", style="dim")

    for s in skills:
        table.add_row(
            s.get("name", "?"),
            s.get("description", "")[:50],
            Path(s.get("path", "")).name,
        )

    console.print(table)


def render_mcp_status(servers: list[dict], clients: dict) -> None:
    """Render MCP server connection status."""
    if not servers:
        console.print("  [dim]No MCP servers configured.[/dim]")
        console.print("  [dim]Add MCP_SERVERS to config.txt as JSON array[/dim]")
        return

    table = Table(box=box.SIMPLE, show_header=True, title="MCP Servers")
    table.add_column("Name", style="bold")
    table.add_column("Transport", style="dim")
    table.add_column("Status")
    table.add_column("Tools", justify="right")

    for s in servers:
        name = s.get("name", "?")
        transport = s.get("command", "?")
        client = clients.get(name)
        if client and client.is_connected:
            status = "[green]connected[/green]"
            tools = str(client.tool_count)
        elif client:
            status = "[red]disconnected[/red]"
            tools = "-"
        else:
            status = "[dim]not connected[/dim]"
            tools = "-"
        table.add_row(name, transport, status, tools)

    console.print(table)


def render_tools_summary(
    skills: list[dict],
    mcp_servers: list[dict],
    mcp_clients: dict,
    cli_tools: list[dict],
) -> None:
    """Render a combined tools inventory across all three types."""
    console.print()
    console.print(Panel.fit("[bold]Tool Inventory[/bold]", border_style="blue"))
    console.print()

    # Skills section
    console.print("[bold]Skills[/bold]")
    if skills:
        for s in skills:
            console.print(f"  [green]●[/green] {s['name']} — [dim]{s.get('description', '')[:60]}[/dim]")
    else:
        console.print("  [dim](none)[/dim]")

    # MCP section
    console.print()
    console.print("[bold]MCP Tools[/bold]")
    if mcp_servers:
        for s in mcp_servers:
            name = s.get("name", "?")
            client = mcp_clients.get(name)
            status = "[green]connected[/green]" if (client and client.is_connected) else "[dim]disconnected[/dim]"
            tool_count = client.tool_count if (client and client.is_connected) else 0
            console.print(f"  [blue]●[/blue] {name} ({status}) — {tool_count} tools")
    else:
        console.print("  [dim](none)[/dim]")

    # CLI section
    console.print()
    console.print("[bold]CLI Tools[/bold]")
    if cli_tools:
        for t in cli_tools:
            console.print(f"  [yellow]●[/yellow] {t['name']} — [dim]{t.get('description', '')[:60]}[/dim]")
    else:
        console.print("  [dim](none)[/dim]")

    console.print()


def render_success(message: str) -> None:
    """Render a success message."""
    console.print(f"  [green]✓ {message}[/green]")
