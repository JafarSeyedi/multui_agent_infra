"""JWT helper functions used by the auth manager."""

from __future__ import annotations

from typing import Any

from ....document.models.ssdm_models import AuthConfig


def apply_bearer_or_jwt_auth(auth: AuthConfig, headers: dict[str, Any]) -> None:
    """Attach bearer token value directly as `Authorization` header."""
    if auth.value:
        headers.setdefault("Authorization", f"Bearer {auth.value}")
        return

    if auth.jwt_validation and auth.jwt_validation.jwks_uri:
        # A production deployment should resolve the JWKS and validate inbound tokens.
        # For outbound outbound calls we keep behavior explicit and fail-safe by
        # not sending unverified tokens.
        return
