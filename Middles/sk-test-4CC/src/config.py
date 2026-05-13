"""Configuration management for Code Clone platform.

Reads API constants directly from src/config.txt (key=value format).
Simple, isolated, easy to modify — just edit the text file.
"""

from pathlib import Path


def _parse_config_txt(filepath: Path) -> dict[str, str]:
    """Parse a simple key=value config file.

    Supports formats:
        KEY="value"
        KEY=value
        KEY="value with spaces"

    Lines starting with # are treated as comments.
    """
    result: dict[str, str] = {}
    if not filepath.exists():
        return result

    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            result[key] = value

    return result


def _config_path() -> Path:
    """Get path to config.txt relative to the project root (src/..)."""
    return Path(__file__).resolve().parent.parent / "src" / "config.txt"


def get_api_key() -> str:
    """Read ANTHROPIC_AUTH_TOKEN from config.txt."""
    cfg = _parse_config_txt(_config_path())
    return cfg.get("ANTHROPIC_AUTH_TOKEN", "")


def get_base_url() -> str:
    """Read ANTHROPIC_BASE_URL from config.txt."""
    cfg = _parse_config_txt(_config_path())
    return cfg.get("ANTHROPIC_BASE_URL", "https://api.deepseek.com/anthropic")


def get_model() -> str:
    """Read ANTHROPIC_MODEL from config.txt."""
    cfg = _parse_config_txt(_config_path())
    return cfg.get("ANTHROPIC_MODEL", "deepseek-v4-pro[1m]")


def get_system_prompt() -> str:
    """Read SYSTEM_PROMPT from config.txt (custom AI behavior instructions)."""
    cfg = _parse_config_txt(_config_path())
    return cfg.get("SYSTEM_PROMPT", "")


def get_mcp_servers() -> list[dict]:
    """Read MCP_SERVERS from config.txt (JSON array).

    Each server: {"name": "...", "command": "...", "args": [...]}
    """
    import json as _json
    cfg = _parse_config_txt(_config_path())
    raw = cfg.get("MCP_SERVERS", "")
    if not raw:
        return []
    try:
        return _json.loads(raw)
    except _json.JSONDecodeError:
        return []


def get_compression_threshold() -> float:
    """Read COMPRESSION_THRESHOLD from config.txt (0.0-1.0, default 0.7)."""
    cfg = _parse_config_txt(_config_path())
    try:
        return float(cfg.get("COMPRESSION_THRESHOLD", "0.7"))
    except (ValueError, TypeError):
        return 0.7


def is_configured() -> bool:
    """Check whether config.txt exists and has a valid auth token."""
    return bool(get_api_key())


def get_sessions_dir() -> Path:
    """Get the sessions directory, creating if needed."""
    sessions_dir = Path.home() / ".claude-code-clone" / "sessions"
    sessions_dir.mkdir(parents=True, exist_ok=True)
    return sessions_dir
