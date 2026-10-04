"""
Configuration and Agent Card specification for A2A Agent.
"""

from __future__ import annotations

import os

PROTOCOLO_MCP = "2026-07-28"
DEFAULT_AGENT_PORT = 7300
DEFAULT_MCP_URL = "http://127.0.0.1:7301/mcp"

AGENT_CARD = {
    "name": "Central de Salas",
    "description": "Reserva salas de reuniao da Hill Valley Tech.",
    "provider": {
        "organization": "Hill Valley Tech",
        "url": "https://hillvalley.example",
    },
    "version": "1.0.0",
    "supportedInterfaces": [
        {
            "url": "http://127.0.0.1:7300/a2a",
            "protocolBinding": "JSONRPC",
            "protocolVersion": "1.0",
        }
    ],
    "capabilities": {
        "streaming": False,
        "pushNotifications": False,
        "extendedAgentCard": False,
    },
    "defaultInputModes": ["text/plain"],
    "defaultOutputModes": ["text/plain"],
    "skills": [
        {
            "id": "reservar-sala",
            "name": "Reservar sala",
            "description": "Reserva uma sala em um intervalo. Se houver conflito, pergunta qual alternativa usar.",
            "tags": ["salas", "agenda"],
            "inputModes": ["text/plain"],
            "outputModes": ["text/plain"],
            "examples": [
                "reservar sala=sala-garagem inicio=2026-11-03T14:00:00-03:00 fim=2026-11-03T15:00:00-03:00 responsavel=Marty"
            ],
        }
    ],
}


def get_mcp_url() -> str:
    return os.environ.get("MCP_URL", DEFAULT_MCP_URL)
