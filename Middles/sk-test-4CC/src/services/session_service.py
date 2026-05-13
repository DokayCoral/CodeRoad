"""Session storage and lifecycle management.

Handles creating, loading, saving, and listing coding sessions.
Sessions are stored as JSON files organized by date.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from src.config import get_sessions_dir
from src.models import Session, SessionStatus

logger = logging.getLogger(__name__)


def _session_path(session_id: str, date_str: str | None = None) -> Path:
    """Get the file path for a session."""
    if date_str:
        return get_sessions_dir() / date_str / f"{session_id}.json"
    # Search for session across date directories
    sessions_dir = get_sessions_dir()
    if not sessions_dir.exists():
        return sessions_dir / datetime.now().strftime("%Y-%m-%d") / f"{session_id}.json"
    for date_dir in sorted(sessions_dir.iterdir(), reverse=True):
        if date_dir.is_dir():
            candidate = date_dir / f"{session_id}.json"
            if candidate.exists():
                return candidate
    date_str = datetime.now().strftime("%Y-%m-%d")
    return sessions_dir / date_str / f"{session_id}.json"


def save_session(session: Session) -> Path:
    """Save a session to JSON file. Uses atomic write pattern."""
    date_str = session.created_at.strftime("%Y-%m-%d")
    dir_path = get_sessions_dir() / date_str
    dir_path.mkdir(parents=True, exist_ok=True)

    file_path = dir_path / f"{session.id}.json"
    tmp_path = file_path.with_suffix(".tmp")

    data = session.model_dump(mode="json")

    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)

    tmp_path.replace(file_path)
    return file_path


def load_session(session_id: str) -> Optional[Session]:
    """Load a session by ID from its JSON file."""
    file_path = _session_path(session_id)
    if not file_path.exists():
        return None

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return Session.model_validate(data)


def list_recent_sessions(limit: int = 20) -> list[dict]:
    """List recent sessions with preview info for selection UI."""
    sessions_dir = get_sessions_dir()
    if not sessions_dir.exists():
        return []

    sessions = []
    for date_dir in sorted(sessions_dir.iterdir(), reverse=True):
        if not date_dir.is_dir():
            continue
        for file in sorted(date_dir.iterdir(), reverse=True):
            if file.suffix == ".json" and not file.suffix == ".tmp":
                try:
                    with open(file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    sessions.append({
                        "id": data.get("id", file.stem),
                        "created_at": data.get("created_at", ""),
                        "updated_at": data.get("updated_at", ""),
                        "message_count": len(data.get("messages", [])),
                        "preview": _generate_preview(data),
                    })
                except (json.JSONDecodeError, KeyError):
                    continue
                if len(sessions) >= limit:
                    break
        if len(sessions) >= limit:
            break

    return sessions


def _generate_preview(data: dict) -> str:
    """Generate a short preview of the session content."""
    messages = data.get("messages", [])
    for msg in messages:
        if msg.get("role") == "user":
            content = msg.get("content", "")
            return content[:80] + ("..." if len(content) > 80 else "")
    return "(空会话)"


def archive_session(session_id: str) -> bool:
    """Archive a session by marking it as archived."""
    session = load_session(session_id)
    if not session:
        return False
    session.status = SessionStatus.ARCHIVED
    save_session(session)
    return True


def delete_session(session_id: str) -> bool:
    """Delete a session JSON file permanently."""
    file_path = _session_path(session_id)
    if file_path.exists():
        file_path.unlink()
        # Clean up empty date directory
        date_dir = file_path.parent
        if date_dir.is_dir() and not any(date_dir.iterdir()):
            date_dir.rmdir()
        return True
    return False


def export_session(session_id: str) -> str | None:
    """Export a session to a readable Markdown file.

    Returns the path to the exported file, or None if session not found.
    """
    session = load_session(session_id)
    if not session:
        return None

    lines = [
        f"# Session Export: {session.id}",
        f"**Created**: {session.created_at.isoformat()}",
        f"**Updated**: {session.updated_at.isoformat()}",
        f"**Status**: {session.status.value}",
        f"**Messages**: {len(session.messages)}",
        "",
        "---",
        "",
    ]

    for msg in session.messages:
        role_label = {
            "user": "### User",
            "assistant": "### AI",
            "system": "### System",
        }.get(msg.role.value, f"### {msg.role.value}")

        lines.append(role_label)
        lines.append(f"*{msg.timestamp.isoformat()}*")
        if msg.pinned:
            lines.append("📌 *Pinned*")
        lines.append("")

        if msg.content:
            # Use code fences for content that looks like code
            content = msg.content
            lines.append(content)
            lines.append("")

        if msg.tool_calls:
            lines.append("**Tool Calls:**")
            for tc in msg.tool_calls:
                lines.append(f"- `{tc.tool_name}` — params: {json.dumps(tc.parameters, ensure_ascii=False)[:200]}")
            lines.append("")

        lines.append("---")
        lines.append("")

    # Write to file
    export_dir = Path.home() / ".claude-code-clone" / "exports"
    export_dir.mkdir(parents=True, exist_ok=True)
    export_path = export_dir / f"session-{session.id[:8]}-{session.created_at.strftime('%Y%m%d')}.md"

    with open(export_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return str(export_path)
