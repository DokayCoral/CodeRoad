"""CLI input handler using prompt_toolkit for interactive input.

Supports multi-line input, command history, and Ctrl+C interrupt detection.
"""

import logging
from pathlib import Path

from prompt_toolkit import PromptSession
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.history import FileHistory
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.styles import Style

logger = logging.getLogger(__name__)

HISTORY_FILE = Path.home() / ".claude-code-clone" / ".input_history"

# Styles for prompt_toolkit
INPUT_STYLE = Style.from_dict({
    "prompt": "bold green",
    "input": "",
    "toolbar": "bg:#333333 #888888",
})

# Key bindings for the input handler
bindings = KeyBindings()


@bindings.add("escape", "enter")
def _(event):
    """Alt+Enter to insert a newline without submitting."""
    event.current_buffer.insert_text("\n")


def create_input_session() -> PromptSession:
    """Create a configured prompt_toolkit session."""
    history = None
    try:
        HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
        history = FileHistory(str(HISTORY_FILE))
    except Exception:
        pass

    return PromptSession(
        history=history,
        style=INPUT_STYLE,
        key_bindings=bindings,
        multiline=False,
        wrap_lines=True,
        bottom_toolbar=_get_toolbar,
    )


# Shared toolbar text — updated by render_status_bar before each prompt
_toolbar_text: str = ""


def set_toolbar_text(text: str) -> None:
    """Update the bottom toolbar text (called before prompt_toolkit renders)."""
    global _toolbar_text
    _toolbar_text = text


def _get_toolbar() -> HTML:
    """Return current toolbar text as prompt_toolkit HTML."""
    return HTML(f"<b>{_toolbar_text}</b>")


def get_user_input(session: PromptSession, prompt_text: str = "> ") -> str | None:
    """Get user input with interrupt handling.

    Returns:
        User input string, or None if interrupted (Ctrl+C).
    """
    try:
        return session.prompt(prompt_text)
    except KeyboardInterrupt:
        return ""  # Cancel current input, stay in conversation
    except EOFError:
        return None  # Ctrl+D = exit
