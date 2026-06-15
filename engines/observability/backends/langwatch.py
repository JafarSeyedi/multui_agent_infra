from __future__ import annotations

from typing import Any

from ..core.backends import ObservabilityBackend


class LangWatchBackend(ObservabilityBackend):
    def __init__(self, api_key: str = ""):
        self._api_key = api_key

    async def start_span(self, name: str, attributes: dict[str, Any] | None = None) -> Any:
        try:
            import langwatch
            return langwatch.start_span(name, attributes or {})
        except ImportError:
            return None

    async def end_span(self, span: Any, status: str = "ok") -> None:
        pass

    async def record_metric(self, name: str, value: float, tags: dict[str, str] | None = None) -> None:
        pass

    async def record_event(self, name: str, attributes: dict[str, Any] | None = None) -> None:
        pass

    async def shutdown(self) -> None:
        pass
