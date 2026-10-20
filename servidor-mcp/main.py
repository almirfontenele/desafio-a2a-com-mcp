#!/usr/bin/env python3
"""
Entrypoint for Servidor MCP - Central de Salas.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Ensure package directory is in sys.path
sys.path.insert(0, str(Path(__file__).parent.resolve()))

from mcp_config import DEFAULT_MCP_PORT, get_request_state_secret
from server import create_mcp_server, MCPServiceContainer


def main() -> None:
    try:
        get_request_state_secret()
    except Exception as e:
        print(f"[MCP-SERVER] Erro ao iniciar servidor MCP: {e}", file=sys.stderr)
        sys.exit(1)

    port = int(os.environ.get("MCP_PORT", DEFAULT_MCP_PORT))
    container = MCPServiceContainer()
    server = create_mcp_server(port, container)
    print(f"[MCP-SERVER] Ouvindo em http://0.0.0.0:{port}/mcp", file=sys.stderr)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
