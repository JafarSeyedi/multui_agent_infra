"""Serialize SSDM binding objects to JSON or YAML documents."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from ...document.models.ssdm_models import ServiceBinding, MessageBinding, AuthConfig


class BindingWriter:
    """Serialize service and MCP bindings for exchange between engines."""

    def __init__(self, *, compact: bool = False) -> None:
        self.compact = compact

    def write(self, bindings: list[ServiceBinding], *, output_format: str = "yaml") -> bytes:
        payload = {"bindings": [self._dump_binding(b) for b in bindings]}
        if output_format.lower() in {"json", ".json"}:
            data = json.dumps(payload, indent=None if self.compact else 2, ensure_ascii=False)
        else:
            data = yaml.safe_dump(payload, sort_keys=False)
        return data.encode("utf-8")

    def write_file(self, bindings: list[ServiceBinding], path: str | Path, *, output_format: str | None = None) -> Path:
        if output_format is None:
            output_format = Path(path).suffix.lower() or ".json"
        out = self.write(bindings, output_format=output_format)
        out_path = Path(path)
        out_path.write_bytes(out)
        return out_path

    @staticmethod
    def _dump_message_binding(binding: MessageBinding) -> dict[str, Any]:
        return {
            "transport": binding.transport.value,
            "topic": binding.topic,
            "queue": binding.queue,
            "message_format": binding.message_format.value,
            "subscription_type": binding.subscription_type.value,
            "group_id": binding.group_id,
            "routing_key": binding.routing_key,
            "reply_to": binding.reply_to,
        }

    @staticmethod
    def _dump_auth(auth: AuthConfig) -> dict[str, Any] | None:
        if auth is None:
            return None
        return {
            "method": auth.method.value,
            "location": auth.location.value if auth.location else None,
            "param_name": auth.param_name,
            "value_source": auth.value_source.value,
            "value": auth.value,
            "oauth2_flow": auth.oauth2_flow.value if auth.oauth2_flow else None,
            "oauth2_token_url": auth.oauth2_token_url,
            "oauth2_authorization_url": auth.oauth2_authorization_url,
            "oauth2_scopes": auth.oauth2_scopes,
            "openid_connect_url": auth.open_id_connect_url,
            "tls_cert_file": auth.tls_cert_file,
            "tls_key_file": auth.tls_key_file,
            "tls_ca_file": auth.tls_ca_file,
        }

    def _dump_binding(self, binding: ServiceBinding) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "operation_id": binding.operation_id,
            "transport": binding.transport.value,
            "endpoint_url": binding.endpoint_url,
            "http_method": binding.http_method,
            "timeout_ms": binding.timeout_ms,
            "retry_policy": binding.retry_policy.value,
            "max_retries": binding.max_retries,
            "headers": binding.headers,
        }
        if binding.auth_config is not None:
            payload["auth_config"] = self._dump_auth(binding.auth_config)
        if binding.message_binding is not None:
            payload["message_binding"] = self._dump_message_binding(binding.message_binding)
        return payload


def serialize_bindings(bindings: list[ServiceBinding], output_format: str = "yaml") -> bytes:
    return BindingWriter().write(bindings, output_format=output_format)
