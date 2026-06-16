# engines/masking/plugin.py
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class IMaskingEngine(ABC):
    name: str = "base"

    @abstractmethod
    async def mask(self, data: dict[str, Any], rules: list[str]) -> dict[str, Any]: ...


class IAnonymizer(ABC):
    name: str = "base"

    @abstractmethod
    async def anonymize(self, text: str) -> str: ...
