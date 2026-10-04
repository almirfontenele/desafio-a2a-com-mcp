#!/usr/bin/env python3
"""
Entrypoint for Agente A2A - Central de Salas.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Ensure package directory is in sys.path
sys.path.insert(0, str(Path(__file__).parent.resolve()))

from agent_config import DEFAULT_AGENT_PORT
from server import create_a2a_server, AgentServiceContainer


def main() -> None:
    port = int(os.environ.get("AGENT_PORT", DEFAULT_AGENT_PORT))
    container = AgentServiceContainer()
    server = create_a2a_server(port, container)
    print(f"[A2A-AGENT] Ouvindo em http://0.0.0.0:{port}/a2a", file=sys.stderr)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
