"""Streaming response handling with Rich live rendering support."""

import time
from collections.abc import Iterator

from src.models import ToolCall


class StreamHandler:
    """Handles streaming AI responses, accumulating tokens and tracking latency."""

    def __init__(self):
        self.accumulated_text: str = ""
        self.start_time: float | None = None
        self.first_token_time: float | None = None
        self.token_count: int = 0

    def process_stream(
        self, stream: Iterator[tuple[str, list[ToolCall] | None]]
    ) -> Iterator[tuple[str, list[ToolCall] | None, bool]]:
        """Process a raw token stream.

        Yields (text_delta, tool_calls, is_complete) tuples.
        Tracks first-token latency.
        """
        if self.start_time is None:
            self.start_time = time.time()

        tool_calls_received: list[ToolCall] = []

        for text_delta, tool_calls in stream:
            if text_delta:
                if self.first_token_time is None:
                    self.first_token_time = time.time()
                self.accumulated_text += text_delta
                self.token_count += 1
                yield (text_delta, None, False)

            if tool_calls is not None:
                tool_calls_received = tool_calls
                yield ("", tool_calls, False)

        # Final yield with completion signal
        yield ("", tool_calls_received if tool_calls_received else None, True)

    @property
    def first_token_latency_ms(self) -> float | None:
        if self.first_token_time and self.start_time:
            return (self.first_token_time - self.start_time) * 1000
        return None

    @property
    def total_time_ms(self) -> float | None:
        if self.start_time:
            return (time.time() - self.start_time) * 1000
        return None

    def reset(self) -> None:
        self.accumulated_text = ""
        self.start_time = None
        self.first_token_time = None
        self.token_count = 0
