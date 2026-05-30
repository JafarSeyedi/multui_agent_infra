"""Generate gateway/reverse-proxy configuration from SSDM exposure models."""

from __future__ import annotations

from typing import Any

from ...document.models.ssdm_models import GatewayRule, ServiceExposure


class GatewayConfigWriter:
    """Serialize gateway rules into a normalized dict payload."""

    def dump(self, exposure: ServiceExposure) -> dict[str, Any]:
        return {
            "service_type": exposure.type.value,
            "ingress": self._dump_ingress(exposure.ingress) if exposure.ingress else None,
            "reverse_proxy_rules": [self._dump_rule(rule) for rule in exposure.reverse_proxy_rules],
        }

    @staticmethod
    def _dump_ingress(ingress: Any) -> dict[str, Any]:
        return {
            "host": ingress.host,
            "tls_secret": ingress.tls_secret,
            "paths": [GatewayConfigWriter._dump_rule(rule) for rule in ingress.paths],
        }

    @staticmethod
    def _dump_rule(rule: GatewayRule) -> dict[str, Any]:
        return {
            "path": rule.path,
            "upstream": rule.upstream,
            "methods": list(rule.methods),
            "host": rule.host,
            "rewrite_path": rule.rewrite_path,
            "strip_path": rule.strip_path,
            "timeout_ms": rule.timeout_ms,
            "request_size_limit_bytes": rule.request_size_limit_bytes,
        }
