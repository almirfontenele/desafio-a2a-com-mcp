"""
Repository for rooms, reservations, and policy documents.
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from mcp_config import SALAS_FILE, RESERVAS_FILE, POLITICA_FILE
from mcp_models import Sala, Reserva


class RoomRepository:
    """
    Manages in-memory state of meeting rooms, bookings, and policies.
    """

    def __init__(self) -> None:
        self._salas: dict[str, Sala] = {}
        self._reservas: list[Reserva] = []
        self._politica_texto: str = ""
        self._res_counter: int = 1
        self.reload()

    def reload(self) -> None:
        """Reload all baseline data from fixed JSON and markdown files."""
        self._salas.clear()
        self._reservas.clear()

        if SALAS_FILE.exists():
            with open(SALAS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                for item in data:
                    s = Sala(
                        id=item["id"],
                        nome=item["nome"],
                        capacidade=item["capacidade"],
                        recursos=item.get("recursos", []),
                    )
                    self._salas[s.id] = s

        max_num = 0
        if RESERVAS_FILE.exists():
            with open(RESERVAS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                for item in data:
                    r = Reserva(
                        id=item["id"],
                        sala=item["sala"],
                        inicio=item["inicio"],
                        fim=item["fim"],
                        responsavel=item["responsavel"],
                    )
                    self._reservas.append(r)
                    if r.id.startswith("res-"):
                        try:
                            num = int(r.id.split("-")[1])
                            if num > max_num:
                                max_num = num
                        except ValueError:
                            pass

        self._res_counter = max_num + 1

        if POLITICA_FILE.exists():
            with open(POLITICA_FILE, "r", encoding="utf-8") as f:
                self._politica_texto = f.read()

    def get_salas(self) -> list[Sala]:
        return list(self._salas.values())

    def get_sala(self, sala_id: str) -> Sala | None:
        return self._salas.get(sala_id)

    def get_politica_texto(self) -> str:
        return self._politica_texto

    def get_reservas(self) -> list[Reserva]:
        return list(self._reservas)

    def find_conflicts(self, sala_id: str, inicio: str, fim: str) -> list[dict[str, Any]]:
        dt_inicio = datetime.fromisoformat(inicio)
        dt_fim = datetime.fromisoformat(fim)
        conflitos = []
        for r in self._reservas:
            if r.sala == sala_id:
                r_inicio = datetime.fromisoformat(r.inicio)
                r_fim = datetime.fromisoformat(r.fim)
                if dt_inicio < r_fim and dt_fim > r_inicio:
                    conflitos.append({
                        "id": r.id,
                        "inicio": r.inicio,
                        "fim": r.fim,
                        "responsavel": r.responsavel,
                    })
        return conflitos

    def find_alternative_rooms(self, requested_sala_id: str, inicio: str, fim: str) -> list[str]:
        requested_room = self.get_sala(requested_sala_id)
        if not requested_room:
            return []
        req_cap = requested_room.capacidade

        alternativas: list[Sala] = []
        for s in self._salas.values():
            if s.id == requested_sala_id:
                continue
            if s.capacidade < req_cap:
                continue
            conflitos = self.find_conflicts(s.id, inicio, fim)
            if not conflitos:
                alternativas.append(s)

        # Ordenadas por capacidade crescente e por id alfabetico, max 3
        alternativas.sort(key=lambda s: (s.capacidade, s.id))
        return [s.id for s in alternativas[:3]]

    def create_reserva(self, sala_id: str, inicio: str, fim: str, responsavel: str) -> Reserva:
        res_id = f"res-{self._res_counter:04d}"
        self._res_counter += 1
        reserva = Reserva(
            id=res_id,
            sala=sala_id,
            inicio=inicio,
            fim=fim,
            responsavel=responsavel,
        )
        self._reservas.append(reserva)
        return reserva
