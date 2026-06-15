from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any

from .models import Event, Session


class BaseSessionService(ABC):
    @abstractmethod
    async def create_session(
        self, app_name: str, user_id: str, session_id: str,
    ) -> Session:
        ...

    @abstractmethod
    async def get_session(
        self, app_name: str, user_id: str, session_id: str,
    ) -> Session | None:
        ...

    @abstractmethod
    async def list_sessions(
        self, app_name: str, user_id: str,
    ) -> list[Session]:
        ...

    @abstractmethod
    async def delete_session(
        self, app_name: str, user_id: str, session_id: str,
    ) -> None:
        ...

    @abstractmethod
    async def append_event(
        self, session: Session, event: Event,
    ) -> None:
        ...


class InMemorySessionService(BaseSessionService):
    def __init__(self) -> None:
        self._sessions: dict[tuple[str, str, str], Session] = {}

    def _key(self, app_name: str, user_id: str, session_id: str) -> tuple[str, str, str]:
        return (app_name, user_id, session_id)

    async def create_session(
        self, app_name: str, user_id: str, session_id: str,
    ) -> Session:
        key = self._key(app_name, user_id, session_id)
        existing = self._sessions.get(key)
        if existing is not None:
            return existing
        session = Session(
            id=str(uuid.uuid4()),
            app_name=app_name,
            user_id=user_id,
            session_id=session_id,
        )
        self._sessions[key] = session
        return session

    async def get_session(
        self, app_name: str, user_id: str, session_id: str,
    ) -> Session | None:
        return self._sessions.get(self._key(app_name, user_id, session_id))

    async def list_sessions(
        self, app_name: str, user_id: str,
    ) -> list[Session]:
        prefix = (app_name, user_id)
        return [
            s for k, s in self._sessions.items()
            if k[:2] == prefix
        ]

    async def delete_session(
        self, app_name: str, user_id: str, session_id: str,
    ) -> None:
        self._sessions.pop(self._key(app_name, user_id, session_id), None)

    async def append_event(
        self, session: Session, event: Event,
    ) -> None:
        if not event.id:
            event.id = str(uuid.uuid4())
        session.events.append(event)
        session.updated_at = datetime.now(timezone.utc)
