from __future__ import annotations

from abc import ABC
from typing import Any


class BaseStorage(ABC):
    """Shared lifecycle helpers for all storage adapters."""

    def __init__(self) -> None:
        self._connected = False

    @property
    def is_connected(self) -> bool:
        return bool(getattr(self, "_connected", False))

    async def connect(self) -> None:
        """Initialize the backend connection if needed."""
        self._connected = True

    async def disconnect(self) -> None:
        """Close the backend connection if needed."""
        self._connected = False

    async def health(self) -> bool:
        """Return whether the backend is considered healthy."""
        return self.is_connected

    async def ensure_connected(self) -> None:
        """Connect lazily when a derived storage uses on-demand initialization."""
        if not self.is_connected:
            await self.connect()

    async def __aenter__(self) -> "BaseStorage":
        await self.connect()
        return self

    async def __aexit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        await self.disconnect()
