"""Unit tests for entity models."""

from src.models import (
    Session,
    Message,
    MessageRole,
    ToolCall,
    ToolCallStatus,
    Task,
    TaskStatus,
    ProjectContext,
)


class TestMessage:
    """Tests for Message entity."""

    def test_create_user_message(self):
        msg = Message(role=MessageRole.USER, content="Hello")
        assert msg.role == MessageRole.USER
        assert msg.content == "Hello"
        assert msg.tool_calls == []

    def test_to_api_message(self):
        msg = Message(role=MessageRole.USER, content="Write a function")
        api_msg = msg.to_api_message()
        assert api_msg["role"] == "user"
        assert api_msg["content"] == "Write a function"


class TestToolCall:
    """Tests for ToolCall entity."""

    def test_create_pending_tool_call(self):
        tc = ToolCall(tool_name="read", parameters={"file_path": "/test.py"})
        assert tc.tool_name == "read"
        assert tc.status == ToolCallStatus.PENDING
        assert tc.approval_required is False

    def test_to_api_format(self):
        tc = ToolCall(tool_name="read", parameters={"file_path": "/test.py"})
        api = tc.to_api_format()
        assert api["type"] == "tool_use"
        assert api["name"] == "read"
        assert api["input"] == {"file_path": "/test.py"}


class TestTask:
    """Tests for Task entity and state machine."""

    def test_create_pending_task(self):
        task = Task(title="Add login page")
        assert task.title == "Add login page"
        assert task.status == TaskStatus.PENDING

    def test_is_blocked_when_dependency_incomplete(self):
        dep = Task(id="1", title="Setup DB", status=TaskStatus.IN_PROGRESS)
        task = Task(id="2", title="Add login", dependencies=["1"])
        assert task.is_blocked([dep, task])

    def test_is_not_blocked_when_dependency_completed(self):
        dep = Task(id="1", title="Setup DB", status=TaskStatus.COMPLETED)
        task = Task(id="2", title="Add login", dependencies=["1"])
        assert not task.is_blocked([dep, task])

    def test_status_transitions(self):
        task = Task(title="Test task")
        assert task.status == TaskStatus.PENDING
        task.status = TaskStatus.IN_PROGRESS
        assert task.status == TaskStatus.IN_PROGRESS
        task.status = TaskStatus.COMPLETED
        assert task.status == TaskStatus.COMPLETED


class TestSession:
    """Tests for Session entity."""

    def test_create_session(self):
        session = Session()
        assert session.status.value == "active"
        assert session.messages == []

    def test_add_message(self):
        session = Session()
        msg = Message(role=MessageRole.USER, content="Hi")
        session.add_message(msg)
        assert len(session.messages) == 1
        assert session.messages[0].content == "Hi"
