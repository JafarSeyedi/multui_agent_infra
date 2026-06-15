from __future__ import annotations

from typing import Any

from ..core.backends import ObservabilityBackend


class DatadogBackend(ObservabilityBackend):
    def __init__(self, api_key: str = ""):
        self._api_key = api_key

    async def start_span(self, name: str, attributes: dict[str, Any] | None = None) -> Any:
        try:
            from ddtrace import tracer
            return tracer.trace(name, resource=name)
        except ImportError:
            return None

    async def end_span(self, span: Any, status: str = "ok") -> None:
        if span is not None:
            try:
                span.finish()
            except Exception:
                pass

    async def record_metric(self, name: str, value: float, tags: dict[str, str] | None = None) -> None:
        try:
            from ddtrace import statsd
            statsd.gauge(name, value, tags=tags or {})
        except ImportError:
            pass

    async def record_event(self, name: str, attributes: dict[str, Any] | None = None) -> None:
        pass

    async def shutdown(self) -> None:
        pass
