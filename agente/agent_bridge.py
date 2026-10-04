"""
Reservation Bridge Service connecting A2A Task workflow to MCP MRTR tools.
"""

from __future__ import annotations

from typing import Any

from agent_models import TaskRecord, TaskState
from agent_parser import BookingMessageParser
from agent_task_manager import TaskManager
from agent_mcp_client import MCPClient


class ReservationBridgeService:
    """
    Coordinates the bridge between A2A SendMessage requests and internal MCP tools.
    Handles:
    - New booking task creation and execution
    - Intercepting MCP input_required (Elicitation) to pause Task in TASK_STATE_INPUT_REQUIRED
    - Task continuation upon user choice (MRTR retry with new JSON-RPC ID)
    - Decline handling leading to TASK_STATE_CANCELED
    """

    def __init__(self, task_manager: TaskManager, mcp_client: MCPClient) -> None:
        self._task_manager = task_manager
        self._mcp_client = mcp_client

    def process_message(
        self,
        message_obj: dict[str, Any],
        traceparent: str | None = None,
    ) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
        task_id = message_obj.get("taskId")
        parts = message_obj.get("parts", [])
        text = " ".join(p.get("text", "") for p in parts if isinstance(p, dict))
        msg_id = message_obj.get("messageId")

        if task_id:
            return self._handle_task_continuation(task_id, text, msg_id)
        else:
            return self._handle_new_booking(text, msg_id, traceparent)

    def _handle_new_booking(
        self,
        text: str,
        msg_id: str | None,
        traceparent: str | None,
    ) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
        task = self._task_manager.create_task(traceparent=traceparent)
        task.add_user_message(text, msg_id)
        task.state = TaskState.WORKING

        args = BookingMessageParser.parse_booking_arguments(text)
        task.original_args = args

        status_code, mcp_resp = self._mcp_client.call_tool(
            tool_name="reservar_sala",
            arguments=args,
            traceparent=traceparent,
        )

        res = mcp_resp.get("result") or {}
        if res.get("isError") or mcp_resp.get("error"):
            err_text = " ".join(p.get("text", "") for p in res.get("content", [])) or (mcp_resp.get("error") or {}).get("message", "Erro ao reservar")
            task.state = TaskState.FAILED
            task.set_agent_message(err_text)
            return {"task": task.to_dict()}, None

        if res.get("resultType") == "input_required":
            input_requests = res.get("inputRequests") or {}
            req_key = next(iter(input_requests), "__main__:escolha_de_sala")
            req_obj = input_requests.get(req_key, {})
            req_params = req_obj.get("params", {})
            schema = req_params.get("requestedSchema", {})
            properties = schema.get("properties", {})
            sala_prop = properties.get("sala", {})
            alternativas = sala_prop.get("enum", [])

            task.state = TaskState.INPUT_REQUIRED
            task.request_state = res.get("requestState")
            task.req_key = req_key
            task.alternatives = alternativas

            pause_text = f"alternativas: {', '.join(alternativas)}"
            task.set_agent_message(pause_text)
            return {"task": task.to_dict()}, None

        # Conclusão direta da reserva
        structured = res.get("structuredContent") or {}
        task.set_artifact("reserva", structured)
        task.state = TaskState.COMPLETED
        task.set_agent_message(f"Reserva {structured.get('reserva')} confirmada na {structured.get('sala')}.")
        return {"task": task.to_dict()}, None

    def _handle_task_continuation(
        self,
        task_id: str,
        text: str,
        msg_id: str | None,
    ) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
        task = self._task_manager.get_task(task_id)
        if not task:
            return None, {"code": -32000, "message": f"Task not found: {task_id}"}

        if task.state.is_terminal:
            return None, {"code": -32000, "message": f"Task {task_id} is in terminal state: {task.state.value}"}

        if task.state == TaskState.INPUT_REQUIRED:
            task.add_user_message(text, msg_id)
            action, choice_val = BookingMessageParser.parse_choice(text)

            if action == "decline":
                task.state = TaskState.WORKING
                status_code, mcp_resp = self._mcp_client.call_tool(
                    tool_name="reservar_sala",
                    arguments=task.original_args,
                    input_responses={
                        task.req_key or "__main__:escolha_de_sala": {
                            "action": "decline"
                        }
                    },
                    request_state=task.request_state,
                    traceparent=task.traceparent,
                )
                task.state = TaskState.CANCELED
                task.set_agent_message("Reserva recusada pelo usuario.")
                return {"task": task.to_dict()}, None

            if choice_val not in task.alternatives:
                # Escolha inválida/fora do enum: mantém pausada
                task.state = TaskState.INPUT_REQUIRED
                task.set_agent_message(f"alternativas: {', '.join(task.alternatives)}")
                return {"task": task.to_dict()}, None

            # Escolha válida: dispara retry MRTR
            task.state = TaskState.WORKING
            status_code, mcp_resp = self._mcp_client.call_tool(
                tool_name="reservar_sala",
                arguments=task.original_args,
                input_responses={
                    task.req_key or "__main__:escolha_de_sala": {
                        "action": "accept",
                        "content": {"sala": choice_val},
                    }
                },
                request_state=task.request_state,
                traceparent=task.traceparent,
            )

            res = mcp_resp.get("result") or {}
            if res.get("isError") or mcp_resp.get("error"):
                err_text = " ".join(p.get("text", "") for p in res.get("content", [])) or (mcp_resp.get("error") or {}).get("message", "Erro ao reservar")
                task.state = TaskState.FAILED
                task.set_agent_message(err_text)
                return {"task": task.to_dict()}, None

            structured = res.get("structuredContent") or {}
            task.set_artifact("reserva", structured)
            task.state = TaskState.COMPLETED
            task.set_agent_message(f"Reserva {structured.get('reserva')} confirmada na {structured.get('sala')}.")
            return {"task": task.to_dict()}, None

        return None, {"code": -32000, "message": f"Unexpected task state: {task.state.value}"}
