"""
Handler for MCP resources (politica://uso).
"""

from __future__ import annotations

from typing import Any
from mcp_config import SERVER_INFO
from mcp_repository import RoomRepository


class ResourcesHandler:
    def __init__(self, repository: RoomRepository) -> None:
        self._repository = repository

    def read_resource(self, uri: str) -> tuple[int, dict[str, Any]]:
        if uri != "politica://uso":
            return 400, {
                "error": {"code": -32602, "message": f"Resource not found: {uri}"}
            }

        return 200, {
            "result": {
                "cacheScope": "private",
                "contents": [
                    {
                        "mimeType": "text/markdown",
                        "text": self._repository.get_politica_texto(),
                        "uri": "politica://uso",
                    }
                ],
                "resultType": "complete",
                "ttlMs": 0,
                "_meta": SERVER_INFO["io.modelcontextprotocol/serverInfo"],
            }
        }
