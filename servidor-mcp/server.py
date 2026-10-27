"""
ASGI Application and MCP Protocol Server using the official Python MCP SDK.
"""

from __future__ import annotations

import json
import sys
from typing import Any

import uvicorn
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Route

from mcp.server.lowlevel import Server
from mcp.types import (
    Tool,
    Resource,
    ServerCapabilities,
    ToolsCapability,
    ResourcesCapability,
)

from mcp_config import PROTOCOLO_MCP
from mcp_repository import RoomRepository
from mcp_rules import BookingPolicyValidator
from mcp_resources_handler import ResourcesHandler
from mcp_tools_handler import ToolsHandler
from mcp_security import HMACStateTokenService


class MCPServiceContainer:
    """Dependency Injection Container for MCP Server."""

    def __init__(self, secret: str | None = None) -> None:
        self.repository = RoomRepository()
        self.validator = BookingPolicyValidator(self.repository)
        self.token_service = HMACStateTokenService(secret)
        self.tools_handler = ToolsHandler(self.repository, self.validator, self.token_service)
        self.resources_handler = ResourcesHandler(self.repository)

        # Initialize official MCP Lowlevel Server instance
        self.mcp_server = Server("central-de-salas", version="1.0.0")
        self._register_mcp_handlers()

    def _register_mcp_handlers(self) -> None:
        @self.mcp_server.list_tools()
        async def handle_list_tools() -> list[Tool]:
            return self.tools_handler.get_tool_definitions()

        @self.mcp_server.list_resources()
        async def handle_list_resources() -> list[Resource]:
            return self.resources_handler.get_resource_definitions()

    def reset(self) -> None:
        self.repository.reload()


def create_mcp_app(container: MCPServiceContainer | None = None) -> Starlette:
    """Creates the ASGI Starlette application for the MCP server."""
    service_container = container or MCPServiceContainer()

    async def get_root(request: Request) -> Response:
        return JSONResponse({"status": "ok", "service": "mcp-server"})

    async def post_reset(request: Request) -> Response:
        service_container.reset()
        return JSONResponse({"status": "reset"})

    async def post_mcp(request: Request) -> Response:
        try:
            body = await request.json()
        except Exception:
            return JSONResponse(
                {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {"code": -32700, "message": "Parse error"},
                },
                status_code=400,
            )

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
            return JSONResponse(
                {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {"code": -32602, "message": "Invalid params: _meta missing"},
                },
                status_code=400,
            )

        protocol_version = meta.get("io.modelcontextprotocol/protocolVersion")
        if not protocol_version or protocol_version != PROTOCOLO_MCP:
            return JSONResponse(
                {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {"code": -32602, "message": "Invalid params: missing or invalid protocolVersion"},
                },
                status_code=400,
            )

        client_capabilities = meta.get("io.modelcontextprotocol/clientCapabilities")
        if client_capabilities is None or not isinstance(client_capabilities, dict):
            return JSONResponse(
                {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {"code": -32602, "message": "Invalid params: missing clientCapabilities"},
                },
                status_code=400,
            )

        # Roteamento de métodos JSON-RPC
        if method == "tools/list":
            result_data = service_container.tools_handler.get_tools_list()
            return JSONResponse({"jsonrpc": "2.0", "id": req_id, **result_data}, status_code=200)
        elif method == "resources/read":
            status_code, result_data = service_container.resources_handler.read_resource(params.get("uri", ""))
            return JSONResponse({"jsonrpc": "2.0", "id": req_id, **result_data}, status_code=status_code)
        elif method == "tools/call":
            status_code, result_data = service_container.tools_handler.execute_tool(params, meta)
            return JSONResponse({"jsonrpc": "2.0", "id": req_id, **result_data}, status_code=status_code)
        else:
            return JSONResponse(
                {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {"code": -32601, "message": f"Method not found: {method}"},
                },
                status_code=200,
            )

    routes = [
        Route("/", get_root, methods=["GET"]),
        Route("/mcp", get_root, methods=["GET"]),
        Route("/mcp", post_mcp, methods=["POST"]),
        Route("/reset", post_reset, methods=["POST"]),
    ]
    app = Starlette(routes=routes)
    app.state.container = service_container
    return app


def create_mcp_server(port: int, container: MCPServiceContainer | None = None) -> uvicorn.Server:
    """Factory function for creating an MCP ASGI Server via Uvicorn."""
    service_container = container or MCPServiceContainer()
    app = create_mcp_app(service_container)
    config = uvicorn.Config(
        app=app,
        host="0.0.0.0",
        port=port,
        log_level="warning",
        access_log=False,
    )
    server = uvicorn.Server(config)
    # Backward compatible methods
    server.serve_forever = server.run
    server.server_close = lambda: None
    return server
