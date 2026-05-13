"""Tool registry with permission-based access control.

Manages all registered tools, their permission levels, and dispatch logic.
"""

from dataclasses import dataclass, field
from typing import Any, Callable

from src.models import PermissionLevel


@dataclass
class ToolDef:
    """Definition of a registered tool."""

    name: str
    description: str
    parameters: dict  # JSON Schema for parameters
    permission_level: PermissionLevel
    handler: Callable[..., str]
    needs_approval: bool = False

    def to_api_schema(self) -> dict:
        """Generate AI API-compatible tool schema."""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": {
                "type": "object",
                "properties": self.parameters,
                "required": list(self.parameters.keys()),
            },
        }


class ToolRegistry:
    """Central registry for all platform tools."""

    def __init__(self):
        self._tools: dict[str, ToolDef] = {}

    def register(self, tool: ToolDef) -> None:
        """Register a tool definition."""
        self._tools[tool.name] = tool

    def get(self, name: str) -> ToolDef | None:
        """Get a tool by name."""
        return self._tools.get(name)

    def list_all(self) -> list[ToolDef]:
        """List all registered tools."""
        return list(self._tools.values())

    def get_schemas(self) -> list[dict]:
        """Get API-compatible schemas for all tools."""
        return [t.to_api_schema() for t in self._tools.values()]

    def execute(self, name: str, params: dict) -> str:
        """Execute a tool by name with given parameters."""
        tool = self._tools.get(name)
        if not tool:
            return f"[ERROR] Unknown tool: {name}"
        try:
            return tool.handler(**params)
        except Exception as e:
            return f"[ERROR] Tool execution failed: {e}"

    def needs_approval(self, name: str, params: dict | None = None) -> bool:
        """Check if a tool requires user approval."""
        tool = self._tools.get(name)
        if not tool:
            return False
        return tool.permission_level in (
            PermissionLevel.WRITE,
            PermissionLevel.SHELL_WRITE,
            PermissionLevel.BLOCKED,
        )

    def get_permission_level(self, name: str) -> PermissionLevel | None:
        tool = self._tools.get(name)
        return tool.permission_level if tool else None


# Global singleton
tool_registry = ToolRegistry()
