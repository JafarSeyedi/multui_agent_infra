from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from .models import Session


@dataclass
class MemoryEntry:
    content: str
    author: str = ""
    timestamp: str = ""
    custom_metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class SearchMemoryResponse:
    memories: list[MemoryEntry] = field(default_factory=list)


class BaseMemoryService(ABC):
    @abstractmethod
    async def add_session_to_memory(self, session: Session) -> None:
        ...

    @abstractmethod
    async def search_memory(
        self, app_name: str, user_id: str, query: str,
    ) -> SearchMemoryResponse:
        ...


class InMemoryMemoryService(BaseMemoryService):
    def __init__(self) -> None:
        self._store: dict[str, list[MemoryEntry]] = {}

    def _key(self, app_name: str, user_id: str) -> str:
        return f"{app_name}:{user_id}"

    async def add_session_to_memory(self, session: Session) -> None:
        key = self._key(session.app_name, session.user_id)
        if key not in self._store:
            self._store[key] = []
        for event in session.events:
            if event.content and isinstance(event.content, dict):
                text = event.content.get("text", "")
                if text:
                    self._store[key].append(
                        MemoryEntry(
                            content=text,
                            author=event.author,
                            timestamp=event.timestamp.isoformat(),
                        )
                    )

    async def search_memory(
        self, app_name: str, user_id: str, query: str,
    ) -> SearchMemoryResponse:
        key = self._key(app_name, user_id)
        entries = self._store.get(key, [])
        if not query:
            return SearchMemoryResponse(memories=entries[:10])

        query_lower = query.lower()
        matched = [
            e for e in entries
            if query_lower in e.content.lower()
        ]
        return SearchMemoryResponse(memories=matched[:10])
