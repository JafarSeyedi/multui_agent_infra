from __future__ import annotations

import os
from typing import Any

from ..core.backends import ObservabilityBackend


class AgentOpsBackend(ObservabilityBackend):
    def __init__(self, api_key: str = ""):
        self._api_key = api_key or os.environ.get("AGENTOPS_API_KEY", "")
        self._client = None

    async def start_span(self, name: str, attributes: dict[str, Any] | None = None) -> Any:
        try:
            import agentops
            if self._client is None:
                self._client = agentops
                self._client.init(api_key=self._api_key)
            return self._client.start_span(name, attributes or {})
        except ImportError:
            return None

    async def end_span(self, span: Any, status: str = "ok") -> None:
        if span is not None:
            try:
                import agentops
                agentops.end_span(span, status=status)
            except ImportError:
                pass

    async def record_metric(self, name: str, value: float, tags: dict[str, str] | None = None) -> None:
        try:
            import agentops
            agentops.record_metric(name, value, tags or {})
        except ImportError:
            pass

    async def record_event(self, name: str, attributes: dict[str, Any] | None = None) -> None:
        try:
            import agentops
            agentops.record_event(name, attributes or {})
        except ImportError:
            pass

    async def shutdown(self) -> None:
        if self._client is not None:
            try:
                self._client.end_session("Success")
            except Exception:
                pass
            self._client = None
