"""
Business rules and policy validators for meeting room bookings.
"""

from __future__ import annotations

from datetime import datetime
from typing import Protocol

from mcp_config import ERRO_SALA, ERRO_JANELA, ERRO_DURACAO, ERRO_INTERVALO
from mcp_models import ValidationResult, Sala


class RoomLookup(Protocol):
    def get_sala(self, sala_id: str) -> Sala | None:
        ...


class BookingPolicyValidator:
    """
    Validates room booking requests against Hill Valley Tech usage policies:
    1. Room existence
    2. Operating hours window (08:00 to 20:00, -03:00 timezone)
    3. Maximum reservation duration (2 hours)
    4. Valid time window (fim > inicio)
    """

    def __init__(self, room_lookup: RoomLookup) -> None:
        self._room_lookup = room_lookup

    def validate(self, sala_id: str, inicio: str, fim: str) -> ValidationResult:
        sala = self._room_lookup.get_sala(sala_id)
        if sala is None:
            return ValidationResult(is_valid=False, error_message=ERRO_SALA.format(sala=sala_id))

        try:
            dt_inicio = datetime.fromisoformat(inicio)
            dt_fim = datetime.fromisoformat(fim)
        except Exception:
            return ValidationResult(is_valid=False, error_message="Formato de data invalido")

        # Janela de uso: 08:00 as 20:00
        start_hour = dt_inicio.hour + dt_inicio.minute / 60.0 + dt_inicio.second / 3600.0
        end_hour = dt_fim.hour + dt_fim.minute / 60.0 + dt_fim.second / 3600.0
        if (
            start_hour < 8.0
            or start_hour > 20.0
            or end_hour < 8.0
            or end_hour > 20.0
            or dt_inicio.date() != dt_fim.date()
        ):
            return ValidationResult(is_valid=False, error_message=ERRO_JANELA)

        # Duracao maxima 2 horas (7200 s)
        duracao = (dt_fim - dt_inicio).total_seconds()
        if duracao > 7200:
            return ValidationResult(is_valid=False, error_message=ERRO_DURACAO)

        # Intervalo valido: fim > inicio
        if dt_fim <= dt_inicio:
            return ValidationResult(is_valid=False, error_message=ERRO_INTERVALO)

        return ValidationResult(is_valid=True)
