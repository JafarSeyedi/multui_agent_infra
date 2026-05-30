"""Authentication helpers for communication transports."""

from .auth_manager import AuthManager
from .api_key import apply_api_key
from .jwt import apply_bearer_or_jwt_auth
from .oauth2 import OAuth2TokenProvider, token_from_client_credentials
from .mtls import prepare_tls_context

__all__ = [
    "AuthManager",
    "OAuth2TokenProvider",
    "apply_api_key",
    "apply_bearer_or_jwt_auth",
    "prepare_tls_context",
    "token_from_client_credentials",
]
