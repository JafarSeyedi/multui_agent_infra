"""API key authentication helper."""

from __future__ import annotations

from typing import Any

from ....document.models.ssdm_models import AuthConfig, ApiKeyLocation


def apply_api_key(auth: AuthConfig, headers: dict[str, Any], params: dict[str, Any], cookies: dict[str, Any]) -> None:
    """Apply API-key auth to request envelope dictionaries."""
    if not auth.param_name:
        return

    if auth.location is ApiKeyLocation.HEADER or auth.location is None:
        headers[auth.param_name] = str(auth.value or "")
    elif auth.location is ApiKeyLocation.QUERY:
        params[auth.param_name] = str(auth.value or "")
    elif auth.location is ApiKeyLocation.COOKIE:
        cookies[auth.param_name] = str(auth.value or "")
