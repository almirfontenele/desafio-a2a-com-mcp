"""
Domain models for MCP Server.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Sala:
    id: str
    nome: str
    capacidade: int
    recursos: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "nome": self.nome,
            "capacidade": self.capacidade,
            "recursos": list(self.recursos),
        }


@dataclass(frozen=True)
class Reserva:
    id: str
    sala: str
    inicio: str
    fim: str
    responsavel: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "sala": self.sala,
            "inicio": self.inicio,
            "fim": self.fim,
            "responsavel": self.responsavel,
        }


@dataclass(frozen=True)
class ValidationResult:
    is_valid: bool
    error_message: str | None = None
