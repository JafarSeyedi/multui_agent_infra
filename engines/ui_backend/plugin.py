# engines/ui_backend/plugin.py
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class IUIAdapter(ABC):
    name: str = "base"

    @abstractmethod
    async def render(self, component: str, props: dict[str, Any]) -> dict[str, Any]: ...

    @abstractmethod
    async def handle_action(self, action: str, payload: dict[str, Any]) -> dict[str, Any]: ...


class ISessionManager(ABC):
    name: str = "base"

    @abstractmethod
    async def create_session(self, user_id: str) -> str: ...

    @abstractmethod
    async def get_session(self, session_id: str) -> dict[str, Any] | None: ...

    @abstractmethod
    async def destroy_session(self, session_id: str) -> None: ...
