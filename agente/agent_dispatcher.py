"""
JSON-RPC Method Dispatcher for A2A Protocol.
"""

from __future__ import annotations

from typing import Any
from agent_bridge import ReservationBridgeService
from agent_task_manager import TaskManager


class A2ADispatcher:
    """
    Dispatches JSON-RPC 2.0 methods (SendMessage, GetTask) to appropriate services.
    """

    def __init__(
        self,
        task_manager: TaskManager,
        bridge_service: ReservationBridgeService,
    ) -> None:
        self._task_manager = task_manager
        self._bridge_service = bridge_service

    def dispatch(
        self,
        method: str,
        params: dict[str, Any],
        traceparent: str | None = None,
    ) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
        if method == "SendMessage":
            message_obj = params.get("message", {})
            return self._bridge_service.process_message(message_obj, traceparent)
        elif method == "GetTask":
            task_id = params.get("id")
            task = self._task_manager.get_task(task_id)
            if not task:
                return None, {"code": -32000, "message": f"Task not found: {task_id}"}
            return {"task": task.to_dict()}, None
        else:
            return None, {"code": -32601, "message": f"Method not found: {method}"}
