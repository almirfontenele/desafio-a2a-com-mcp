"""
Task Manager and In-Memory Repository for A2A Tasks.
"""

from __future__ import annotations

import secrets
from agent_models import TaskRecord, TaskState


class TaskManager:
    """
    Manages in-memory store and lifecycle of A2A Tasks.
    """

    def __init__(self) -> None:
        self._tasks: dict[str, TaskRecord] = {}

    def create_task(self, traceparent: str | None = None) -> TaskRecord:
        task_id = f"task-{secrets.token_hex(6)}"
        context_id = f"ctx-{secrets.token_hex(6)}"
        task = TaskRecord(id=task_id, context_id=context_id, state=TaskState.SUBMITTED)
        task.traceparent = traceparent
        self._tasks[task_id] = task
        return task

    def get_task(self, task_id: str) -> TaskRecord | None:
        return self._tasks.get(task_id)

    def clear(self) -> None:
        self._tasks.clear()
