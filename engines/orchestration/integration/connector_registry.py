"""Pluggable connector registry."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


@dataclass(frozen=True)
class Connector:
    key: str
    handler: Callable[..., Any]


class ConnectorRegistry:
    """Register connectors by key and invoke them by reference."""

    def __init__(self) -> None:
        self._connectors: dict[str, Connector] = {}

    def register(self, key: str, handler: Callable[..., Any]) -> None:
        self._connectors[key] = Connector(key=key, handler=handler)

    def get(self, key: str) -> Callable[..., Any]:
        connector = self._connectors.get(key)
        if connector is None:
            raise KeyError(f"Connector not found: {key}")
        return connector.handler

    def execute(self, key: str, *args: Any, **kwargs: Any) -> Any:
        return self.get(key)(*args, **kwargs)

    def unregister(self, key: str) -> None:
        self._connectors.pop(key, None)

    def list(self) -> list[str]:
        return sorted(self._connectors)
