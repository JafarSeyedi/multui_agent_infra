"""Parse transport/auth mapping definitions into SSDM binding models."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from ...document.models.ssdm_models import MessageBinding, MessageFormat, RetryPolicy, ServiceBinding, SubscriptionType, Transport
from ...document.models.ssdm_models import AuthConfig, AuthMethod, HttpMethod, ApiKeyLocation, OAuth2Flow, ValueSource


class BindingParser:
    """Parse one or more bindings from JSON/YAML dictionaries or files."""

    @staticmethod
    def parse_raw(data: dict[str, Any], *, default_transport: Transport = Transport.HTTP) -> list[ServiceBinding]:
        bindings: list[ServiceBinding] = []
        raw_bindings = data.get("bindings", [])
        for raw in raw_bindings:
            if not isinstance(raw, dict):
                continue
            binding = BindingParser._parse_service_binding(raw, default_transport=default_transport)
            if binding:
                bindings.append(binding)
        return bindings

    @staticmethod
    def parse_service_bindings_file(path: str | Path, *, default_transport: Transport = Transport.HTTP) -> list[ServiceBinding]:
        raw = Path(path).read_text(encoding="utf-8")
        text = raw.strip()
        if not text:
            return []

        try:
            content = json.loads(text)
        except json.JSONDecodeError:
            content = yaml.safe_load(text)

        if not isinstance(content, dict):
            return []
        return BindingParser.parse_raw(content, default_transport=default_transport)

    @staticmethod
    def _parse_auth(raw: dict[str, Any] | None) -> AuthConfig | None:
        if not raw:
            return None
        method = str(raw.get("method", "none"))
        try:
            method_enum = AuthMethod(method)
        except ValueError:
            method_enum = AuthMethod.NONE

        location = raw.get("location")
        location_enum = None
        if isinstance(location, str) and location:
            try:
                location_enum = ApiKeyLocation(location)
            except ValueError:
                location_enum = None

        oauth_flow = raw.get("oauth2_flow")
        oauth2_flow = None
        if isinstance(oauth_flow, str):
            try:
                oauth2_flow = OAuth2Flow(oauth_flow)
            except ValueError:
                oauth2_flow = None

        return AuthConfig(
            method=method_enum,
            location=location_enum,
            param_name=raw.get("param_name"),
            value=raw.get("value"),
            value_source=ValueSource(raw.get("value_source", ValueSource.STATIC.value)) if raw.get("value_source") else ValueSource.STATIC,
            oauth2_flow=oauth2_flow,
            oauth2_client_id=raw.get("oauth2_client_id"),
            oauth2_client_secret=raw.get("oauth2_client_secret"),
            oauth2_token_url=raw.get("oauth2_token_url") or raw.get("token_url"),
            oauth2_authorization_url=raw.get("oauth2_authorization_url") or raw.get("authorization_url"),
            oauth2_scopes=list(raw.get("oauth2_scopes", [])),
            oauth2_pkce=bool(raw.get("oauth2_pkce", False)),
            oauth2_device_auth_endpoint=raw.get("oauth2_device_auth_endpoint"),
            open_id_connect_url=raw.get("open_id_connect_url"),
            tls_cert=raw.get("tls_cert"),
            tls_key=raw.get("tls_key"),
            tls_ca=raw.get("tls_ca"),
            tls_cert_file=raw.get("tls_cert_file"),
            tls_key_file=raw.get("tls_key_file"),
            tls_ca_file=raw.get("tls_ca_file"),
            jwt_validation=None,
        )

    @staticmethod
    def _parse_retry(raw: Any) -> RetryPolicy:
        if not raw:
            return RetryPolicy.NONE
        try:
            return RetryPolicy(str(raw))
        except ValueError:
            return RetryPolicy.NONE

    @staticmethod
    def _parse_http_method(raw: Any) -> str | None:
        if not raw:
            return None
        try:
            return HttpMethod(str(raw).upper()).value
        except ValueError:
            return str(raw).upper()

    @staticmethod
    def _parse_message_binding(raw: dict[str, Any] | None) -> MessageBinding | None:
        if not raw:
            return None
        transport = raw.get("transport", Transport.AMQP)
        if isinstance(transport, str):
            try:
                transport = Transport(transport)
            except ValueError:
                transport = Transport.AMQP

        format_raw = raw.get("message_format")
        msg_format = MessageFormat.JSON
        if isinstance(format_raw, str):
            try:
                msg_format = MessageFormat(format_raw.upper())
            except ValueError:
                msg_format = MessageFormat.JSON

        return MessageBinding(
            transport=transport,
            topic=raw.get("topic") or raw.get("channel"),
            queue=raw.get("queue"),
            message_format=msg_format,
            subscription_type=BindingParser._parse_subscription_type(
                raw.get("subscription_type") or raw.get("subscriptionType")
            ),
            group_id=raw.get("group_id") or raw.get("groupId"),
            routing_key=raw.get("routing_key") or raw.get("routingKey"),
            reply_to=raw.get("reply_to") or raw.get("replyTo"),
        )

    @staticmethod
    def _parse_subscription_type(raw: Any) -> SubscriptionType:
        if not raw:
            return SubscriptionType.PUB_SUB
        if isinstance(raw, SubscriptionType):
            return raw
        try:
            return SubscriptionType(str(raw))
        except Exception:
            return SubscriptionType.PUB_SUB

    @staticmethod
    def _parse_service_binding(raw: dict[str, Any], *, default_transport: Transport) -> ServiceBinding:
        transport = raw.get("transport", default_transport.value)
        if isinstance(transport, str):
            try:
                transport = Transport(transport)
            except ValueError:
                transport = default_transport

        return ServiceBinding(
            operation_id=str(raw["operation_id"] if "operation_id" in raw else raw.get("operationId", "")),
            transport=transport,
            endpoint_url=raw.get("endpoint_url") or raw.get("url") or raw.get("target_url"),
            http_method=BindingParser._parse_http_method(raw.get("http_method") or raw.get("method")),
            auth_config=BindingParser._parse_auth(raw.get("auth") or raw.get("auth_config")),
            timeout_ms=int(raw.get("timeout_ms", 30000)),
            retry_policy=BindingParser._parse_retry(raw.get("retry_policy")),
            max_retries=int(raw.get("max_retries", 3)),
            headers=dict(raw.get("headers") or {}),
            message_binding=BindingParser._parse_message_binding(raw.get("message") or raw.get("message_binding")),
        )


def parse_bindings(source: dict[str, Any] | str | Path, *, default_transport: Transport = Transport.HTTP) -> list[ServiceBinding]:
    """Convenience helper for one-shot parsing from dict / JSON / YAML source."""
    if isinstance(source, (str, Path)):
        return BindingParser.parse_service_bindings_file(source, default_transport=default_transport)
    if isinstance(source, dict):
        return BindingParser.parse_raw(source, default_transport=default_transport)
    return []
