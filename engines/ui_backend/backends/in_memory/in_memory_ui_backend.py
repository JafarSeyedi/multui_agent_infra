# engines/ui_backend/backends/in_memory/in_memory_ui_backend.py
from __future__ import annotations

import uuid
from typing import Any

from ...models.ui_backend_models import Session
from ...plugin import IUIAdapter, ISessionManager


class InMemoryUIAdapter(IUIAdapter):
    name = "in_memory"

    def __init__(self) -> None:
        self._actions: list[dict[str, Any]] = []

    async def render(self, component: str, props: dict[str, Any]) -> dict[str, Any]:
        return {"component": component, "props": props, "html": f"<{component} />"}

    async def handle_action(self, action: str, payload: dict[str, Any]) -> dict[str, Any]:
        self._actions.append({"action": action, "payload": payload})
        return {"status": "handled", "action": action}


class InMemorySessionManager(ISessionManager):
    name = "in_memory"

    def __init__(self) -> None:
        self._sessions: dict[str, Session] = {}

    async def create_session(self, user_id: str) -> str:
        session_id = str(uuid.uuid4())
        self._sessions[session_id] = Session(session_id=session_id, user_id=user_id)
        return session_id

    async def get_session(self, session_id: str) -> dict[str, Any] | None:
        session = self._sessions.get(session_id)
        if session is None:
            return None
        return {"session_id": session.session_id, "user_id": session.user_id, "data": session.data}

    async def destroy_session(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)
