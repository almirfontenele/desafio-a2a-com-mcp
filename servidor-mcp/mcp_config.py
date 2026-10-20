"""
Configuration and constants for MCP Server.
"""

from __future__ import annotations

import os
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent.resolve()
DADOS_DIR = BASE_DIR / "dados"
SALAS_FILE = DADOS_DIR / "salas.json"
RESERVAS_FILE = DADOS_DIR / "reservas.json"
POLITICA_FILE = DADOS_DIR / "politica-de-uso.md"

PROTOCOLO_MCP = "2026-07-28"
VERSAO_POLITICA = "2026-11-01"
DEFAULT_MCP_PORT = 7301
TOKEN_EXPIRATION_SECONDS = 1800  # 30 minutos

SERVER_INFO = {
    "io.modelcontextprotocol/serverInfo": {
        "name": "central-de-salas",
        "version": "1.0.0",
    }
}

ERRO_SALA = "Sala inexistente: {sala}"
ERRO_JANELA = "Fora da janela de uso: a politica permite reservas entre 08:00 e 20:00"
ERRO_DURACAO = "Duracao acima do limite: a politica permite no maximo 2 horas"
ERRO_INTERVALO = "Intervalo invalido: fim deve ser posterior a inicio"
ERRO_SEM_ALTERNATIVA = "Sem alternativas disponiveis no intervalo"


def get_request_state_secret() -> str:
    """Retrieve the HMAC secret key from the environment."""
    secret = os.environ.get("REQUEST_STATE_SECRET")
    if not secret or not secret.strip():
        raise RuntimeError("REQUEST_STATE_SECRET environment variable is required")
    if len(secret.strip().encode("utf-8")) < 32:
        raise RuntimeError("REQUEST_STATE_SECRET must have at least 32 bytes")
    return secret.strip()
