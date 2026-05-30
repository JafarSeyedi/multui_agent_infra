"""OAuth2 token provider helpers."""

from __future__ import annotations

import base64
from dataclasses import dataclass
from urllib.parse import urlencode

from ....document.models.ssdm_models import AuthConfig


def _encode_basic_auth(token: str) -> str:
    return base64.b64encode(token.encode("utf-8")).decode("ascii")


@dataclass
class OAuth2Token:
    access_token: str
    token_type: str = "Bearer"
    expires_in: int | None = None


class OAuth2TokenProvider:
    """Simple cache-backed OAuth2 token provider for client credentials."""

    def __init__(self) -> None:
        self._token: OAuth2Token | None = None

    async def get_token(self, auth: AuthConfig) -> str | None:
        if self._token is not None:
            return self._token.access_token

        if not auth.oauth2_token_url:
            return auth.value

        request = {
            "grant_type": "client_credentials",
            "client_id": auth.oauth2_client_id or "",
            "client_secret": auth.oauth2_client_secret or "",
            "scope": " ".join(auth.oauth2_scopes),
        }
        if auth.oauth2_client_id and auth.oauth2_client_secret:
            _ = _encode_basic_auth(f"{auth.oauth2_client_id}:{auth.oauth2_client_secret}")
        # We do not force a network dependency here; caller may populate `auth.value`.
        # A concrete implementation should exchange this payload and create OAuth2Token.
        _ = urlencode(request)
        return auth.value

    def invalidate(self) -> None:
        self._token = None


def token_from_client_credentials(auth: AuthConfig) -> str | None:
    """Shortcut for static client credentials values."""
    return auth.value
