"""AI service: abstraction layer over Anthropic and OpenAI APIs.

Handles message construction, streaming responses, tool use parsing,
and provider factory dispatch based on configuration.
"""

import logging
from typing import Iterator

from src.config import get_api_key, get_base_url, get_model
from src.models import Message, ToolCall, MessageRole, ToolCallStatus
from src.tools.registry import tool_registry

logger = logging.getLogger(__name__)


class AIProvider:
    """Abstract base for AI model providers."""

    def stream_response(
        self, messages: list[dict], tools: list[dict], system_prompt: str
    ) -> Iterator[tuple[str, list[ToolCall] | None]]:
        """Stream response tokens. Yields (text_delta, tool_calls_or_none)."""
        raise NotImplementedError

    def count_tokens(self, messages: list[dict]) -> int:
        """Estimate token count for messages."""
        raise NotImplementedError


class AnthropicProvider(AIProvider):
    """Anthropic Claude API provider."""

    def __init__(self, api_key: str, model: str, base_url: str = ""):
        from anthropic import Anthropic

        kwargs = {"api_key": api_key}
        if base_url:
            kwargs["base_url"] = base_url
        self.client = Anthropic(**kwargs)
        self.model = model

    def stream_response(
        self, messages: list[dict], tools: list[dict], system_prompt: str
    ) -> Iterator[tuple[str, list[ToolCall] | None]]:
        import anthropic

        api_messages = []
        for msg in messages:
            api_messages.append({"role": msg["role"], "content": msg["content"]})

        kwargs = {
            "model": self.model,
            "max_tokens": 8192,
            "messages": api_messages,
        }
        if system_prompt:
            kwargs["system"] = system_prompt
        if tools:
            kwargs["tools"] = [
                {
                    "name": t["name"],
                    "description": t["description"],
                    "input_schema": t["input_schema"],
                }
                for t in tools
            ]

        with self.client.messages.stream(**kwargs) as stream:
            current_block = None
            accumulated_text = ""
            tool_calls: list[dict] = []

            for event in stream:
                if event.type == "content_block_start":
                    current_block = event.content_block
                    if current_block.type == "tool_use":
                        tool_calls.append({
                            "id": current_block.tool_use.id if hasattr(current_block.tool_use, 'id') else getattr(current_block.tool_use, 'id', ''),
                            "name": current_block.tool_use.name if hasattr(current_block.tool_use, 'name') else getattr(current_block.tool_use, 'name', ''),
                            "input": {},
                            "input_json": "",
                        })

                elif event.type == "content_block_delta":
                    if event.delta.type == "text_delta":
                        accumulated_text += event.delta.text
                        yield (event.delta.text, None)
                    elif event.delta.type == "input_json_delta" and tool_calls:
                        tool_calls[-1]["input_json"] += event.delta.partial_json

                elif event.type == "content_block_stop":
                    pass

            # Parse completed tool calls
            if tool_calls:
                import json
                parsed: list[ToolCall] = []
                for tc in tool_calls:
                    try:
                        params = json.loads(tc["input_json"]) if tc["input_json"] else {}
                    except json.JSONDecodeError:
                        params = {}
                    parsed.append(ToolCall(
                        id=tc["id"],
                        tool_name=tc["name"],
                        parameters=params,
                        status=ToolCallStatus.PENDING,
                    ))
                yield ("", parsed)

    def count_tokens(self, messages: list[dict]) -> int:
        # Approximate: 1 token ≈ 4 characters
        total = 0
        for msg in messages:
            total += len(str(msg.get("content", ""))) // 4
        return total


class OpenAIProvider(AIProvider):
    """OpenAI API provider."""

    def __init__(self, api_key: str, model: str):
        from openai import OpenAI

        self.client = OpenAI(api_key=api_key)
        self.model = model

    def stream_response(
        self, messages: list[dict], tools: list[dict], system_prompt: str
    ) -> Iterator[tuple[str, list[ToolCall] | None]]:
        api_messages = []
        if system_prompt:
            api_messages.append({"role": "system", "content": system_prompt})
        for msg in messages:
            api_messages.append({"role": msg["role"], "content": msg["content"]})

        kwargs = {
            "model": self.model,
            "messages": api_messages,
            "stream": True,
            "max_tokens": 8192,
        }
        if tools:
            kwargs["tools"] = [
                {
                    "type": "function",
                    "function": {
                        "name": t["name"],
                        "description": t["description"],
                        "parameters": t["input_schema"],
                    },
                }
                for t in tools
            ]

        response = self.client.chat.completions.create(**kwargs)

        accumulated_tool_calls: dict[int, dict] = {}
        accumulated_text = ""

        for chunk in response:
            delta = chunk.choices[0].delta if chunk.choices else None
            if not delta:
                continue

            if delta.content:
                accumulated_text += delta.content
                yield (delta.content, None)

            if delta.tool_calls:
                for tc in delta.tool_calls:
                    idx = tc.index
                    if idx not in accumulated_tool_calls:
                        accumulated_tool_calls[idx] = {
                            "id": tc.id or "",
                            "name": "",
                            "arguments": "",
                        }
                    if tc.id:
                        accumulated_tool_calls[idx]["id"] = tc.id
                    if tc.function:
                        if tc.function.name:
                            accumulated_tool_calls[idx]["name"] = tc.function.name
                        if tc.function.arguments:
                            accumulated_tool_calls[idx]["arguments"] += tc.function.arguments

        if accumulated_tool_calls:
            import json
            parsed: list[ToolCall] = []
            for idx in sorted(accumulated_tool_calls.keys()):
                tc = accumulated_tool_calls[idx]
                try:
                    params = json.loads(tc["arguments"]) if tc["arguments"] else {}
                except json.JSONDecodeError:
                    params = {}
                parsed.append(ToolCall(
                    id=tc["id"],
                    tool_name=tc["name"],
                    parameters=params,
                    status=ToolCallStatus.PENDING,
                ))
            yield ("", parsed)

    def count_tokens(self, messages: list[dict]) -> int:
        total = 0
        for msg in messages:
            total += len(str(msg.get("content", ""))) // 4
        return total


def create_ai_provider() -> AIProvider:
    """Factory: create AI provider reading config from src/config.txt.

    Uses DeepSeek Anthropic-compatible proxy.
    """
    api_key = get_api_key()
    base_url = get_base_url()
    model = get_model()

    if not api_key:
        raise ValueError(
            "API key not configured. "
            "Please set ANTHROPIC_AUTH_TOKEN in src/config.txt"
        )

    return AnthropicProvider(api_key=api_key, model=model, base_url=base_url)
