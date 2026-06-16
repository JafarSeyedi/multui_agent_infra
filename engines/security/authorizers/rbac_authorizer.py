# engines/security/authorizers/rbac_authorizer.py
from __future__ import annotations

from ..plugin import IAuthorizer


class RBACAuthorizer(IAuthorizer):
    name = "rbac"

    def __init__(self, permissions: dict[str, list[str]] | None = None) -> None:
        self._permissions: dict[str, list[str]] = permissions or {}

    async def authorize(self, principal: str, resource: str, action: str) -> bool:
        allowed = self._permissions.get(resource, [])
        return action in allowed
