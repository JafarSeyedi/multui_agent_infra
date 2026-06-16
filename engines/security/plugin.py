# engines/security/plugin.py
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Optional


class IAuthenticator(ABC):
    name: str = "base"

    @abstractmethod
    async def authenticate(self, credentials: dict[str, Any]) -> Optional[str]: ...


class IAuthorizer(ABC):
    name: str = "base"

    @abstractmethod
    async def authorize(self, principal: str, resource: str, action: str) -> bool: ...
