# engines/observability/plugin.py
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Optional


class IMetricsCollector(ABC):
    name: str = "base"

    @abstractmethod
    async def increment(self, metric: str, tags: dict[str, str] | None = None, value: float = 1.0) -> None: ...

    @abstractmethod
    async def gauge(self, metric: str, value: float, tags: dict[str, str] | None = None) -> None: ...

    @abstractmethod
    async def histogram(self, metric: str, value: float, tags: dict[str, str] | None = None) -> None: ...


class ILogger(ABC):
    name: str = "base"

    @abstractmethod
    async def log(self, level: str, message: str, context: dict[str, Any] | None = None) -> None: ...


class ITracer(ABC):
    name: str = "base"

    @abstractmethod
    async def start_span(self, name: str, parent_id: Optional[str] = None) -> str: ...

    @abstractmethod
    async def end_span(self, span_id: str) -> None: ...
