"""mTLS helper for creating TLS contexts from auth model settings."""

from __future__ import annotations

import ssl

from ....document.models.ssdm_models import AuthConfig


def prepare_tls_context(auth: AuthConfig) -> ssl.SSLContext | None:
    """Create TLS context from certificate configuration when available."""
    if not auth.tls_cert and not auth.tls_cert_file:
        return None

    context = ssl.create_default_context(purpose=ssl.Purpose.SERVER_AUTH)
    if auth.tls_ca_file:
        context.load_verify_locations(cafile=auth.tls_ca_file)
    if auth.tls_ca:
        context.load_verify_locations(cadata=auth.tls_ca)

    cert = auth.tls_cert_file or auth.tls_cert
    key = auth.tls_key_file or auth.tls_key
    if cert:
        if key:
            context.load_cert_chain(cert, key)
        else:
            context.load_cert_chain(cert)
    return context
