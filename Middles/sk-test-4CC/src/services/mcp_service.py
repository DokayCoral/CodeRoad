"""MCP (Model Context Protocol) client service.

Implements a minimal JSON-RPC 2.0 client over stdio for MCP servers.
Supports tools/list and tools/call — the two core MCP methods.
"""

import json
import logging
import subprocess
import time
from typing import Any

logger = logging.getLogger(__name__)

MCP_TIMEOUT = 30  # seconds


class MCPClient:
    """Minimal MCP JSON-RPC client over stdio subprocess."""

    def __init__(self, name: str, command: str, args: list[str] | None = None):
        self.name = name
        self.command = command
        self.args = args or []
        self.process: subprocess.Popen | None = None
        self._request_id = 0
        self._tools: list[dict] = []

    def connect(self) -> bool:
        """Start the MCP server subprocess and initialize connection.

        Returns True on success, False on failure.
        """
        try:
            self.process = subprocess.Popen(
                [self.command] + self.args,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            # Initialize: send initialize request
            result = self._send_request("initialize", {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "code-clone", "version": "1.0.0"},
            })
            if result is None:
                return False

            # Discover tools
            tools_result = self.list_tools()
            return tools_result is not None
        except Exception as e:
            logger.warning("MCP connect failed for %s: %s", self.name, e)
            return False

    def disconnect(self) -> None:
        """Terminate the MCP server subprocess."""
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
            except Exception:
                self.process.kill()
            finally:
                self.process = None
                self._tools = []

    def list_tools(self) -> list[dict] | None:
        """Call tools/list and return available tools."""
        result = self._send_request("tools/list", {})
        if result and "tools" in result:
            self._tools = result["tools"]
            return self._tools
        return None

    def call_tool(self, tool_name: str, arguments: dict | None = None) -> str | None:
        """Call a tool by name and return its result content as text.

        Returns the tool's text content, or an error string.
        """
        result = self._send_request("tools/call", {
            "name": tool_name,
            "arguments": arguments or {},
        })
        if result is None:
            return "[ERROR] MCP tool call failed: no response"
        if "isError" in result and result["isError"]:
            content = result.get("content", [{}])
            error_text = ""
            if isinstance(content, list) and content:
                error_text = content[0].get("text", "") if isinstance(content[0], dict) else str(content)
            return f"[ERROR] MCP tool error: {error_text}"
        # Extract text from content
        content = result.get("content", [])
        if isinstance(content, list):
            texts = [c.get("text", "") for c in content if isinstance(c, dict)]
            return "\n".join(texts) if texts else json.dumps(content)
        return str(content)

    @property
    def is_connected(self) -> bool:
        return self.process is not None and self.process.poll() is None

    @property
    def tool_count(self) -> int:
        return len(self._tools)

    def _send_request(self, method: str, params: dict) -> dict | None:
        """Send a JSON-RPC request and return the result."""
        if not self.process or self.process.poll() is not None:
            return None

        self._request_id += 1
        request = {
            "jsonrpc": "2.0",
            "id": self._request_id,
            "method": method,
            "params": params,
        }

        try:
            req_str = json.dumps(request) + "\n"
            self.process.stdin.write(req_str)
            self.process.stdin.flush()

            # Read response line
            start = time.time()
            while time.time() - start < MCP_TIMEOUT:
                if self.process.poll() is not None:
                    stderr = self.process.stderr.read() if self.process.stderr else ""
                    logger.warning("MCP process exited: %s", stderr[:200])
                    return None

                line = self.process.stdout.readline()
                if line:
                    response = json.loads(line)
                    if "error" in response:
                        logger.warning("MCP error: %s", response["error"])
                        return None
                    return response.get("result", {})
                time.sleep(0.05)

            # Timeout
            logger.warning("MCP request timeout for %s", method)
            return None
        except Exception as e:
            logger.warning("MCP request error: %s", e)
            return None
