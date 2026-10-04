"""
A2A Domain models for Tasks, Messages, and Artifacts.
"""

from __future__ import annotations

import secrets
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class TaskState(str, Enum):
    SUBMITTED = "TASK_STATE_SUBMITTED"
    WORKING = "TASK_STATE_WORKING"
    INPUT_REQUIRED = "TASK_STATE_INPUT_REQUIRED"
    COMPLETED = "TASK_STATE_COMPLETED"
    CANCELED = "TASK_STATE_CANCELED"
    FAILED = "TASK_STATE_FAILED"

    @property
    def is_terminal(self) -> bool:
        return self in (TaskState.COMPLETED, TaskState.CANCELED, TaskState.FAILED)


@dataclass
class TaskRecord:
    id: str
    context_id: str
    state: TaskState = TaskState.SUBMITTED
    history: list[dict[str, Any]] = field(default_factory=list)
    artifacts: list[dict[str, Any]] = field(default_factory=list)
    latest_message: dict[str, Any] | None = None

    # Bridge MRTR Internal State (Never exposed in to_dict)
    request_state: str | None = None
    req_key: str | None = None
    alternatives: list[str] = field(default_factory=list)
    original_args: dict[str, str] = field(default_factory=dict)
    traceparent: str | None = None

    def add_user_message(self, text: str, message_id: str | None = None) -> dict[str, Any]:
        mid = message_id or f"msg-{secrets.token_hex(6)}"
        msg = {
            "messageId": mid,
            "role": "ROLE_USER",
            "parts": [{"text": text}],
        }
        if self.id:
            msg["taskId"] = self.id
        if self.context_id:
            msg["contextId"] = self.context_id
        self.history.append(msg)
        return msg

    def set_agent_message(self, text: str) -> dict[str, Any]:
        mid = f"msg-{secrets.token_hex(6)}"
        msg = {
            "messageId": mid,
            "role": "ROLE_AGENT",
            "parts": [{"text": text}],
            "taskId": self.id,
            "contextId": self.context_id,
        }
        self.history.append(msg)
        self.latest_message = msg
        return msg

    def set_artifact(self, name: str, structured_content: dict[str, Any]) -> dict[str, Any]:
        import json
        artifact = {
            "artifactId": f"art-{secrets.token_hex(6)}",
            "name": name,
            "parts": [{"text": json.dumps(structured_content)}],
        }
        self.artifacts = [artifact]
        return artifact

    def to_dict(self) -> dict[str, Any]:
        status: dict[str, Any] = {"state": self.state.value if isinstance(self.state, TaskState) else self.state}
        if self.latest_message:
            status["message"] = self.latest_message
        return {
            "id": self.id,
            "contextId": self.context_id,
            "status": status,
            "history": self.history,
            "artifacts": self.artifacts,
        }
