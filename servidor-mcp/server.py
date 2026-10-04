"""
HTTP Server and JSON-RPC transport dispatcher for MCP Protocol.
"""

from __future__ import annotations

import json
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Any

from mcp_config import PROTOCOLO_MCP
from mcp_repository import RoomRepository
from mcp_rules import BookingPolicyValidator
from mcp_resources_handler import ResourcesHandler
from mcp_tools_handler import ToolsHandler
from mcp_security import HMACStateTokenService


class MCPServiceContainer:
    """Dependency Injection Container for MCP Server."""

    def __init__(self) -> None:
        self.repository = RoomRepository()
        self.validator = BookingPolicyValidator(self.repository)
        self.token_service = HMACStateTokenService()
        self.tools_handler = ToolsHandler(self.repository, self.validator, self.token_service)
        self.resources_handler = ResourcesHandler(self.repository)

    def reset(self) -> None:
        self.repository.reload()


class MCPRequestHandler(BaseHTTPRequestHandler):
    """Handles HTTP requests for MCP Server (/mcp, /reset)."""

    container: MCPServiceContainer

    def log_message(self, format: str, *args: Any) -> None:
        pass

    def do_GET(self) -> None:
        if self.path in ("/", "/mcp"):
            self.send_json_response(200, {"status": "ok", "service": "mcp-server"})
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self) -> None:
        if self.path == "/reset":
            self.container.reset()
            self.send_json_response(200, {"status": "reset"})
            return

        if self.path != "/mcp" and not self.path.startswith("/mcp?"):
            self.send_response(404)
            self.end_headers()
            return

        content_length = int(self.headers.get("Content-Length", 0))
        raw_body = self.rfile.read(content_length)

        try:
            body = json.loads(raw_body.decode("utf-8"))
        except Exception:
            self.send_json_response(400, {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32700, "message": "Parse error"},
            })
            return

        req_id = body.get("id")
        method = body.get("method")
        params = body.get("params", {}) or {}
        meta = params.get("_meta") if isinstance(params, dict) else None

        # Stderr logging obrigatório por especificação
        traceparent = "none"
        if isinstance(meta, dict):
            traceparent = meta.get("traceparent") or "none"
        sys.stderr.write(f"[MCP-SERVER] POST {method} id={req_id} traceparent={traceparent}\n")
        sys.stderr.flush()

        # Validação de _meta
        if not isinstance(meta, dict):
            self.send_json_response(400, {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32602, "message": "Invalid params: _meta missing"},
            })
            return

        protocol_version = meta.get("io.modelcontextprotocol/protocolVersion")
        if not protocol_version or protocol_version != PROTOCOLO_MCP:
            self.send_json_response(400, {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32602, "message": "Invalid params: missing or invalid protocolVersion"},
            })
            return

        client_capabilities = meta.get("io.modelcontextprotocol/clientCapabilities")
        if client_capabilities is None or not isinstance(client_capabilities, dict):
            self.send_json_response(400, {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32602, "message": "Invalid params: missing clientCapabilities"},
            })
            return

        # Roteamento de métodos JSON-RPC
        if method == "tools/list":
            result_data = self.container.tools_handler.get_tools_list()
            self.send_json_response(200, {"jsonrpc": "2.0", "id": req_id, **result_data})
        elif method == "resources/read":
            status_code, result_data = self.container.resources_handler.read_resource(params.get("uri", ""))
            self.send_json_response(status_code, {"jsonrpc": "2.0", "id": req_id, **result_data})
        elif method == "tools/call":
            status_code, result_data = self.container.tools_handler.execute_tool(params, meta)
            self.send_json_response(status_code, {"jsonrpc": "2.0", "id": req_id, **result_data})
        else:
            self.send_json_response(200, {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32601, "message": f"Method not found: {method}"},
            })

    def send_json_response(self, status: int, data: dict[str, Any]) -> None:
        resp_bytes = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(resp_bytes)))
        self.end_headers()
        self.wfile.write(resp_bytes)


def create_mcp_server(port: int, container: MCPServiceContainer | None = None) -> HTTPServer:
    """Factory function for creating an MCP HTTP Server."""
    service_container = container or MCPServiceContainer()

    class BoundHandler(MCPRequestHandler):
        pass

    BoundHandler.container = service_container
    return HTTPServer(("0.0.0.0", port), BoundHandler)
