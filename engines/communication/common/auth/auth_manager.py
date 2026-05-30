"""Central helper to apply authentication config to outgoing transport calls."""

from __future__ import annotations

from typing import Any

from ....document.models.ssdm_models import AuthConfig, AuthMethod
from .api_key import apply_api_key
from .jwt import apply_bearer_or_jwt_auth
from .oauth2 import OAuth2TokenProvider, token_from_client_credentials


class AuthManager:
    """Applies AuthConfig to headers / query params / cookies for outbound calls."""

    def __init__(self) -> None:
        self.oauth2_provider = OAuth2TokenProvider()

    async def apply(self, auth: AuthConfig | None, headers: dict[str, Any], params: dict[str, Any], cookies: dict[str, Any]) -> None:
        if auth is None or auth.method is AuthMethod.NONE:
            return

        if auth.method == AuthMethod.API_KEY:
            apply_api_key(auth, headers, params, cookies)
            return

        if auth.method in {AuthMethod.BEARER_TOKEN, AuthMethod.JWT, AuthMethod.OPENID_CONNECT}:
            token = auth.value or token_from_client_credentials(auth)
            if token:
                apply_bearer_or_jwt_auth(auth, headers)
            return

        if auth.method == AuthMethod.HTTP_BASIC:
            if auth.value:
                headers["Authorization"] = f"Basic {auth.value}"
            return

        if auth.method == AuthMethod.OAUTH2:
            token = await self.oauth2_provider.get_token(auth)
            if token:
                headers["Authorization"] = f"Bearer {token}"
            return

        if auth.method == AuthMethod.MUTUAL_TLS:
            # Mutual TLS is handled by transport-layer TLS context.
            return
