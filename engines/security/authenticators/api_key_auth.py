# engines/security/authenticators/api_key_auth.py
from __future__ import annotations

from typing import Any, Optional

from ..plugin import IAuthenticator


class ApiKeyAuthenticator(IAuthenticator):
    name = "api_key"

    def __init__(self, valid_keys: dict[str, str]) -> None:
        self._valid_keys = valid_keys

    async def authenticate(self, credentials: dict[str, Any]) -> Optional[str]:
        api_key = credentials.get("api_key", "")
        return self._valid_keys.get(api_key)
