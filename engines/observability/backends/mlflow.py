from __future__ import annotations

from typing import Any

from ..core.backends import ObservabilityBackend


class MLflowBackend(ObservabilityBackend):
    def __init__(self, tracking_uri: str = ""):
        self._tracking_uri = tracking_uri

    async def start_span(self, name: str, attributes: dict[str, Any] | None = None) -> Any:
        try:
            import mlflow
            if self._tracking_uri:
                mlflow.set_tracking_uri(self._tracking_uri)
            return mlflow.start_span(name, attributes=attributes or {})
        except ImportError:
            return None

    async def end_span(self, span: Any, status: str = "ok") -> None:
        if span is not None:
            try:
                span.close()
            except Exception:
                pass

    async def record_metric(self, name: str, value: float, tags: dict[str, str] | None = None) -> None:
        try:
            import mlflow
            mlflow.log_metric(name, value)
        except ImportError:
            pass

    async def record_event(self, name: str, attributes: dict[str, Any] | None = None) -> None:
        pass

    async def shutdown(self) -> None:
        pass
