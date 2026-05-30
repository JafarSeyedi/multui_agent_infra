"""Decision service/business knowledge model invocation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


@dataclass(frozen=True)
class InvocationError(RuntimeError):
    """Raised when service invocation fails."""


class InvocationHandler:
    def __init__(self) -> None:
        self._registry: dict[str, Callable[[Any], Any]] = {}

    def register(self, name: str, fn: Callable[[Any], Any]) -> None:
        self._registry[name] = fn

    def invoke(self, name: str, payload: dict[str, Any]) -> Any:
        handler = self._registry.get(name)
        if handler is None:
            raise InvocationError(f"No invocation handler for {name}")
        return handler(payload)
