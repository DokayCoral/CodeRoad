"""Entity models for Code Clone platform.

All models use Pydantic for validation and serialization.
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class SessionStatus(str, Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ToolCallStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    EXECUTING = "executing"
    SUCCESS = "success"
    ERROR = "error"
    CANCELLED = "cancelled"


class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class PermissionLevel(str, Enum):
    READ = "read"
    SHELL_READ = "shell_read"
    WRITE = "write"
    SHELL_WRITE = "shell_write"
    BLOCKED = "blocked"


class ToolCall(BaseModel):
    """A single tool invocation requested by AI and executed by the platform."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    tool_name: str
    parameters: dict = Field(default_factory=dict)
    result: Optional[str] = None
    status: ToolCallStatus = ToolCallStatus.PENDING
    approval_required: bool = False
    approved_by_user: Optional[bool] = None
    duration_ms: Optional[int] = None

    def to_api_format(self) -> dict:
        return {
            "type": "tool_use",
            "id": self.id,
            "name": self.tool_name,
            "input": self.parameters,
        }

    def to_result_format(self) -> dict:
        return {
            "type": "tool_result",
            "tool_use_id": self.id,
            "content": self.result or "",
            "is_error": self.status == ToolCallStatus.ERROR,
        }


class Message(BaseModel):
    """A single turn in the conversation."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    role: MessageRole
    content: str
    tool_calls: list[ToolCall] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.now)
    token_count: int = 0
    pinned: bool = False
    input_tokens: int = 0
    output_tokens: int = 0

    def to_api_message(self) -> dict:
        """Convert to AI API message format."""
        msg: dict = {"role": self.role.value, "content": self.content}
        if self.tool_calls:
            msg["content"] = [
                {"type": "text", "text": self.content or ""},
            ]
            for tc in self.tool_calls:
                msg["content"].append(tc.to_api_format())
        return msg


class Task(BaseModel):
    """A work unit tracked within a session."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    title: str
    description: str = ""
    status: TaskStatus = TaskStatus.PENDING
    dependencies: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None

    def is_blocked(self, all_tasks: list["Task"]) -> bool:
        """Check if this task is blocked by incomplete dependencies."""
        task_map = {t.id: t for t in all_tasks}
        for dep_id in self.dependencies:
            dep = task_map.get(dep_id)
            if dep and dep.status != TaskStatus.COMPLETED:
                return True
        return False


class ProjectContext(BaseModel):
    """Project-level configuration loaded at session start."""

    project_name: str = ""
    config_file_path: str = ""
    instructions: str = ""
    tech_stack: list[str] = Field(default_factory=list)
    directory_structure: dict = Field(default_factory=dict)
    code_conventions: str = ""


class Session(BaseModel):
    """A complete interactive coding session."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    messages: list[Message] = Field(default_factory=list)
    task_list: list[Task] = Field(default_factory=list)
    project_context: ProjectContext = Field(default_factory=ProjectContext)
    status: SessionStatus = SessionStatus.ACTIVE

    def add_message(self, message: Message) -> None:
        self.messages.append(message)
        self.updated_at = datetime.now()

    def last_messages(self, n: int) -> list[Message]:
        return self.messages[-n:] if n > 0 else self.messages
