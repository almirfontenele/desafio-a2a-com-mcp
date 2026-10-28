"""
Handler for MCP resources (politica://uso) using official MCP SDK types.
"""

from __future__ import annotations

from typing import Any
from mcp.types import Resource, TextResourceContents
from mcp_config import SERVER_INFO
from mcp_repository import RoomRepository


class ResourcesHandler:
    def __init__(self, repository: RoomRepository) -> None:
        self._repository = repository

    def get_resource_definitions(self) -> list[Resource]:
        return [
            Resource(
                uri="politica://uso",
                name="politica-de-uso",
                description="Politica de uso das salas de reuniao",
                mimeType="text/markdown",
            )
        ]

    def read_resource(self, uri: str) -> tuple[int, dict[str, Any]]:
        if uri != "politica://uso":
            return 400, {
                "error": {"code": -32602, "message": f"Resource not found: {uri}"}
            }

        content_item = TextResourceContents(
            uri="politica://uso",
            mimeType="text/markdown",
            text=self._repository.get_politica_texto(),
        ).model_dump(mode="json", by_alias=True, exclude_none=True)

        return 200, {
            "result": {
                "cacheScope": "private",
                "contents": [content_item],
                "resultType": "complete",
                "ttlMs": 0,
                "_meta": SERVER_INFO["io.modelcontextprotocol/serverInfo"],
            }
        }
