"""
HTTP Server for A2A Protocol (Agent Card, /a2a, /reset).
"""

from __future__ import annotations

import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Any

from agent_bridge import ReservationBridgeService
from agent_config import AGENT_CARD
from agent_task_manager import TaskManager
from agent_dispatcher import A2ADispatcher
from agent_mcp_client import MCPClient


class AgentServiceContainer:
    """Dependency Injection Container for A2A Agent."""

    def __init__(self, mcp_url: str | None = None) -> None:
        self.task_manager = TaskManager()
        self.mcp_client = MCPClient(mcp_url)
        self.bridge_service = ReservationBridgeService(self.task_manager, self.mcp_client)
        self.dispatcher = A2ADispatcher(self.task_manager, self.bridge_service)

    def reset(self) -> None:
        self.task_manager.clear()


class A2ARequestHandler(BaseHTTPRequestHandler):
    """Handles HTTP requests for A2A Agent."""

    container: AgentServiceContainer

    def log_message(self, format: str, *args: Any) -> None:
        pass

    def do_GET(self) -> None:
        if self.path == "/.well-known/agent-card.json":
            self.send_json_response(200, AGENT_CARD)
        elif self.path in ("/", "/a2a"):
            self.send_json_response(200, {"status": "ok", "service": "a2a-agent"})
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self) -> None:
        if self.path == "/reset":
            self.container.reset()
            self.send_json_response(200, {"status": "reset"})
            return

        if self.path != "/a2a" and not self.path.startswith("/a2a?"):
            self.send_response(404)
            self.end_headers()
            return

        content_length = int(self.headers.get("Content-Length", 0))
        raw_body = self.rfile.read(content_length)
        traceparent = self.headers.get("traceparent")

        try:
            body = json.loads(raw_body.decode("utf-8"))
        except Exception:
            self.send_json_response(200, {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32700, "message": "Parse error"},
            })
            return

        req_id = body.get("id")
        method = body.get("method", "")
        params = body.get("params", {}) or {}

        try:
            result, error = self.container.dispatcher.dispatch(method, params, traceparent)
        except Exception as e:
            self.send_json_response(200, {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32603, "message": f"Internal error: {str(e)}"},
            })
            return

        if error:
            self.send_json_response(200, {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": error,
            })
        else:
            self.send_json_response(200, {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": result,
            })

    def send_json_response(self, status: int, data: dict[str, Any]) -> None:
        resp_bytes = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(resp_bytes)))
        self.end_headers()
        self.wfile.write(resp_bytes)


def create_a2a_server(port: int, container: AgentServiceContainer | None = None) -> HTTPServer:
    """Factory function for creating an A2A HTTP Server."""
    service_container = container or AgentServiceContainer()

    class BoundHandler(A2ARequestHandler):
        pass

    BoundHandler.container = service_container
    return HTTPServer(("0.0.0.0", port), BoundHandler)
