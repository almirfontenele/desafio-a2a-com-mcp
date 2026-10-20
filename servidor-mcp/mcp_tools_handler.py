"""
Handler for MCP tools execution and discovery.
"""

from __future__ import annotations

import json
from typing import Any

from mcp_config import SERVER_INFO, ERRO_SEM_ALTERNATIVA
from mcp_models import Sala
from mcp_repository import RoomRepository
from mcp_rules import BookingPolicyValidator
from mcp_security import HMACStateTokenService


class ToolsHandler:
    """
    Handles discovery (tools/list) and execution (tools/call) for domain tools:
    - listar_salas
    - consultar_disponibilidade
    - reservar_sala (including MRTR elicitation and retry)
    """

    def __init__(
        self,
        repository: RoomRepository,
        policy_validator: BookingPolicyValidator,
        token_service: HMACStateTokenService,
    ) -> None:
        self._repository = repository
        self._validator = policy_validator
        self._token_service = token_service

    def get_tools_list(self) -> dict[str, Any]:
        tools = [
            {
                "name": "listar_salas",
                "description": "Lista todas as salas com capacidade e recursos.",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "title": "listar_salasArguments",
                },
                "outputSchema": {
                    "type": "object",
                    "properties": {
                        "salas": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "id": {"type": "string"},
                                    "nome": {"type": "string"},
                                    "capacidade": {"type": "integer"},
                                    "recursos": {"type": "array", "items": {"type": "string"}},
                                },
                                "required": ["id", "nome", "capacidade", "recursos"],
                            },
                        }
                    },
                    "required": ["salas"],
                },
            },
            {
                "name": "consultar_disponibilidade",
                "description": "Diz se uma sala esta livre no intervalo, e quais reservas conflitam.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "sala": {"type": "string", "title": "Sala"},
                        "inicio": {"type": "string", "title": "Inicio"},
                        "fim": {"type": "string", "title": "Fim"},
                    },
                    "required": ["sala", "inicio", "fim"],
                    "title": "consultar_disponibilidadeArguments",
                },
                "outputSchema": {
                    "type": "object",
                    "properties": {
                        "sala": {"type": "string"},
                        "livre": {"type": "boolean"},
                        "conflitos": {"type": "array"},
                    },
                    "required": ["sala", "livre", "conflitos"],
                },
            },
            {
                "name": "reservar_sala",
                "description": "Reserva uma sala. Se o intervalo estiver ocupado, pergunta qual alternativa usar.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "sala": {"type": "string", "title": "Sala"},
                        "inicio": {"type": "string", "title": "Inicio"},
                        "fim": {"type": "string", "title": "Fim"},
                        "responsavel": {"type": "string", "title": "Responsavel"},
                    },
                    "required": ["sala", "inicio", "fim", "responsavel"],
                    "title": "reservar_salaArguments",
                },
                "outputSchema": {
                    "type": "object",
                    "properties": {
                        "reserva": {"type": ["string", "null"]},
                        "reservado": {"type": "boolean"},
                        "sala": {"type": ["string", "null"]},
                        "inicio": {"type": ["string", "null"]},
                        "fim": {"type": ["string", "null"]},
                        "responsavel": {"type": ["string", "null"]},
                        "politica": {"type": ["string", "null"]},
                        "motivo": {"type": ["string", "null"]},
                    },
                },
            },
        ]
        return {
            "result": {
                "cacheScope": "private",
                "resultType": "complete",
                "tools": tools,
                "ttlMs": 0,
                "_meta": SERVER_INFO["io.modelcontextprotocol/serverInfo"],
            }
        }

    def execute_tool(self, params: dict[str, Any], meta: dict[str, Any]) -> tuple[int, dict[str, Any]]:
        tool_name = params.get("name")
        args = params.get("arguments", {}) or {}

        if tool_name == "listar_salas":
            return self._handle_listar_salas()
        elif tool_name == "consultar_disponibilidade":
            return self._handle_consultar_disponibilidade(args)
        elif tool_name == "reservar_sala":
            return self._handle_reservar_sala(params, meta)
        else:
            return 200, {
                "error": {"code": -32602, "message": f"Unknown tool: {tool_name}"}
            }

    def _handle_listar_salas(self) -> tuple[int, dict[str, Any]]:
        salas_dicts = [s.to_dict() for s in self._repository.get_salas()]
        salas_json_str = json.dumps(salas_dicts)
        return 200, {
            "result": {
                "content": [{"type": "text", "text": salas_json_str}],
                "isError": False,
                "resultType": "complete",
                "structuredContent": salas_dicts,
                "_meta": SERVER_INFO["io.modelcontextprotocol/serverInfo"],
            }
        }

    def _handle_consultar_disponibilidade(self, args: dict[str, Any]) -> tuple[int, dict[str, Any]]:
        sala_id = args.get("sala", "")
        inicio = args.get("inicio", "")
        fim = args.get("fim", "")

        val_result = self._validator.validate(sala_id, inicio, fim)
        if not val_result.is_valid:
            return 200, {
                "result": {
                    "content": [{"type": "text", "text": val_result.error_message or "Erro de validacao"}],
                    "isError": True,
                    "resultType": "complete",
                    "_meta": SERVER_INFO["io.modelcontextprotocol/serverInfo"],
                }
            }

        conflitos = self._repository.find_conflicts(sala_id, inicio, fim)
        structured = {
            "sala": sala_id,
            "livre": len(conflitos) == 0,
            "conflitos": conflitos,
        }
        return 200, {
            "result": {
                "content": [{"type": "text", "text": json.dumps(structured)}],
                "isError": False,
                "resultType": "complete",
                "structuredContent": structured,
                "_meta": SERVER_INFO["io.modelcontextprotocol/serverInfo"],
            }
        }

    def _handle_reservar_sala(self, params: dict[str, Any], meta: dict[str, Any]) -> tuple[int, dict[str, Any]]:
        args = params.get("arguments", {}) or {}
        input_responses = params.get("inputResponses")
        request_state = params.get("requestState")

        # Caso de Retry MRTR
        if request_state is not None or input_responses is not None:
            return self._handle_mrtr_retry(input_responses, request_state)

        # Caso Inicial de reservar_sala
        sala_id = args.get("sala", "")
        inicio = args.get("inicio", "")
        fim = args.get("fim", "")
        responsavel = args.get("responsavel", "")

        val_result = self._validator.validate(sala_id, inicio, fim)
        if not val_result.is_valid:
            return 200, {
                "result": {
                    "content": [{"type": "text", "text": val_result.error_message or "Erro de validacao"}],
                    "isError": True,
                    "resultType": "complete",
                    "_meta": SERVER_INFO["io.modelcontextprotocol/serverInfo"],
                }
            }

        conflitos = self._repository.find_conflicts(sala_id, inicio, fim)
        if not conflitos:
            # Sala livre: reserva direta
            reserva = self._repository.create_reserva(sala_id, inicio, fim, responsavel)
            structured = {
                "reserva": reserva.id,
                "reservado": True,
                "sala": reserva.sala,
                "inicio": reserva.inicio,
                "fim": reserva.fim,
                "responsavel": reserva.responsavel,
                "politica": self._repository.get_politica_versao(),
                "motivo": None,
            }
            return 200, {
                "result": {
                    "content": [{"type": "text", "text": json.dumps(structured, indent=2)}],
                    "isError": False,
                    "resultType": "complete",
                    "structuredContent": structured,
                    "_meta": SERVER_INFO["io.modelcontextprotocol/serverInfo"],
                }
            }

        # Conflito detectado: verificar capabilities do cliente para elicitation
        client_caps = meta.get("io.modelcontextprotocol/clientCapabilities", {})
        form_cap = client_caps.get("elicitation", {}).get("form")
        if form_cap is None:
            return 400, {
                "error": {
                    "code": -32021,
                    "message": "Client did not declare the form elicitation capability required by resolver '__main__:escolha_de_sala'",
                    "data": {
                        "requiredCapabilities": {
                            "elicitation": {
                                "form": {}
                            }
                        }
                    },
                }
            }

        # Alternativas de salas
        alternativas = self._repository.find_alternative_rooms(sala_id, inicio, fim)
        if not alternativas:
            return 200, {
                "result": {
                    "content": [{"type": "text", "text": ERRO_SEM_ALTERNATIVA}],
                    "isError": True,
                    "resultType": "complete",
                    "_meta": SERVER_INFO["io.modelcontextprotocol/serverInfo"],
                }
            }

        # Token HMAC requestState
        token = self._token_service.generate_token({
            "sala": sala_id,
            "inicio": inicio,
            "fim": fim,
            "responsavel": responsavel,
        })

        input_requests = {
            "__main__:escolha_de_sala": {
                "method": "elicitation/create",
                "params": {
                    "message": "A sala pedida esta ocupada nesse intervalo. Escolha uma alternativa.",
                    "mode": "form",
                    "requestedSchema": {
                        "properties": {
                            "sala": {
                                "description": "Sala alternativa escolhida",
                                "enum": alternativas,
                                "title": "Sala",
                                "type": "string",
                            }
                        },
                        "required": ["sala"],
                        "type": "object",
                    },
                },
            }
        }

        return 200, {
            "result": {
                "inputRequests": input_requests,
                "requestState": token,
                "resultType": "input_required",
                "_meta": SERVER_INFO["io.modelcontextprotocol/serverInfo"],
            }
        }

    def _handle_mrtr_retry(self, input_responses: Any, request_state: Any) -> tuple[int, dict[str, Any]]:
        if not request_state or not input_responses:
            return 400, {
                "error": {"code": -32602, "message": "Missing requestState or inputResponses for retry"}
            }

        sealed_payload = self._token_service.verify_token(request_state)
        if not sealed_payload:
            return 400, {
                "error": {"code": -32602, "message": "Invalid or tampered requestState signature"}
            }

        sealed_inicio = sealed_payload["inicio"]
        sealed_fim = sealed_payload["fim"]
        sealed_responsavel = sealed_payload["responsavel"]

        resp_entry = next(iter(input_responses.values()), {})
        action = resp_entry.get("action")

        if action == "decline":
            structured = {
                "reserva": None,
                "reservado": False,
                "sala": None,
                "inicio": None,
                "fim": None,
                "responsavel": None,
                "politica": None,
                "motivo": "recusado",
            }
            return 200, {
                "result": {
                    "content": [{"type": "text", "text": json.dumps(structured, indent=2)}],
                    "isError": False,
                    "resultType": "complete",
                    "structuredContent": structured,
                    "_meta": SERVER_INFO["io.modelcontextprotocol/serverInfo"],
                }
            }

        if action == "accept":
            chosen_sala = (resp_entry.get("content") or {}).get("sala")
            if not chosen_sala or self._repository.get_sala(chosen_sala) is None:
                return 200, {
                    "result": {
                        "content": [{"type": "text", "text": f"Sala inexistente: {chosen_sala}"}],
                        "isError": True,
                        "resultType": "complete",
                        "_meta": SERVER_INFO["io.modelcontextprotocol/serverInfo"],
                    }
                }

            reserva = self._repository.create_reserva(chosen_sala, sealed_inicio, sealed_fim, sealed_responsavel)
            structured = {
                "reserva": reserva.id,
                "reservado": True,
                "sala": reserva.sala,
                "inicio": reserva.inicio,
                "fim": reserva.fim,
                "responsavel": reserva.responsavel,
                "politica": self._repository.get_politica_versao(),
                "motivo": None,
            }
            return 200, {
                "result": {
                    "content": [{"type": "text", "text": json.dumps(structured, indent=2)}],
                    "isError": False,
                    "resultType": "complete",
                    "structuredContent": structured,
                    "_meta": SERVER_INFO["io.modelcontextprotocol/serverInfo"],
                }
            }

        return 400, {
            "error": {"code": -32602, "message": f"Unknown action: {action}"}
        }
