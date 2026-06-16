from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class ObservabilityBackend(ABC):
    @abstractmethod
    async def start_span(self, name: str, attributes: dict[str, Any] | None = None) -> Any:
        ...

    @abstractmethod
    async def end_span(self, span: Any, status: str = "ok") -> None:
        ...

    @abstractmethod
    async def record_metric(self, name: str, value: float, tags: dict[str, str] | None = None) -> None:
        ...

    @abstractmethod
    async def record_event(self, name: str, attributes: dict[str, Any] | None = None) -> None:
        ...

    async def shutdown(self) -> None:
        pass
