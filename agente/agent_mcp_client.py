"""
MCP Client for communicating with the internal MCP Server.
"""

from __future__ import annotations

import json
import secrets
import urllib.error
import urllib.request
from typing import Any

from agent_config import PROTOCOLO_MCP, get_mcp_url


class MCPClient:
    """
    HTTP Client that formats and dispatches JSON-RPC 2.0 requests to the MCP Server
    with mandatory _meta headers, client capabilities, and traceparent context.
    """

    def __init__(self, mcp_url: str | None = None) -> None:
        self._mcp_url = mcp_url or get_mcp_url()

    def _send_request(
        self,
        method: str,
        params: dict[str, Any],
        name: str | None = None,
        traceparent: str | None = None,
    ) -> tuple[int, dict[str, Any]]:
        meta: dict[str, Any] = {
            "io.modelcontextprotocol/protocolVersion": PROTOCOLO_MCP,
            "io.modelcontextprotocol/clientInfo": {
                "name": "agente-central-de-salas",
                "version": "1.0.0",
            },
            "io.modelcontextprotocol/clientCapabilities": {
                "elicitation": {
                    "form": {}
                }
            },
        }
        if traceparent:
            meta["traceparent"] = traceparent

        payload = {
            "jsonrpc": "2.0",
            "id": secrets.token_hex(6),  # Always generates a NEW JSON-RPC ID
            "method": method,
            "params": {**params, "_meta": meta},
        }

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "MCP-Protocol-Version": PROTOCOLO_MCP,
            "Mcp-Method": method,
        }
        if name:
            headers["Mcp-Name"] = name

        req = urllib.request.Request(
            self._mcp_url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                status = resp.status
                body = json.loads(resp.read().decode("utf-8"))
                return status, body
        except urllib.error.HTTPError as e:
            raw = e.read().decode("utf-8")
            try:
                return e.code, json.loads(raw)
            except Exception:
                return e.code, {"error": {"code": -32603, "message": raw}}
        except Exception as e:
            return 500, {"error": {"code": -32603, "message": str(e)}}

    def list_tools(self, traceparent: str | None = None) -> tuple[int, dict[str, Any]]:
        """Perform tool discovery via tools/list."""
        return self._send_request(
            method="tools/list",
            params={},
            name=None,
            traceparent=traceparent,
        )

    def read_resource(self, uri: str, traceparent: str | None = None) -> tuple[int, dict[str, Any]]:
        """Read an MCP resource via resources/read."""
        return self._send_request(
            method="resources/read",
            params={"uri": uri},
            name=uri,
            traceparent=traceparent,
        )

    def call_tool(
        self,
        tool_name: str,
        arguments: dict[str, Any],
        input_responses: dict[str, Any] | None = None,
        request_state: str | None = None,
        traceparent: str | None = None,
    ) -> tuple[int, dict[str, Any]]:
        params: dict[str, Any] = {
            "name": tool_name,
            "arguments": arguments,
        }
        if input_responses is not None:
            params["inputResponses"] = input_responses
        if request_state is not None:
            params["requestState"] = request_state

        return self._send_request(
            method="tools/call",
            params=params,
            name=tool_name,
            traceparent=traceparent,
        )
