"""Builder pattern — constructs TransportRequest from service bindings."""

from __future__ import annotations

from typing import Any

from ...document.models.ssdm_models import (
    AuthConfig,
    MessageBinding,
    ParameterLocation,
    ServiceBinding,
    ServiceOperation,
    SubscriptionType,
)
from ..common.auth.auth_manager import AuthManager
from ..common.transport.base import TransportRequest
from .service_discovery import ServiceDiscovery


class RequestBuilder:
    """Builds TransportRequest from operation, binding, and payload."""

    def __init__(
        self,
        auth_manager: AuthManager,
        service_discovery: ServiceDiscovery,
    ) -> None:
        self._auth_manager = auth_manager
        self._service_discovery = service_discovery

    async def build(
        self,
        operation: ServiceOperation,
        payload: dict[str, Any],
        binding: ServiceBinding,
        *,
        auth_config: AuthConfig | None,
    ) -> TransportRequest:
        resolved = self._service_discovery.resolve(
            operation.name,
            binding.endpoint_url,
            discovery=None,
        )
        endpoint = resolved.target or binding.endpoint_url
        if not endpoint:
            raise RuntimeError(f"No endpoint resolved for operation '{operation.name}'")

        headers: dict[str, str] = dict(binding.headers)
        params: dict[str, Any] = {}
        cookies: dict[str, str] = {}
        body_payload: Any = None

        for parameter in operation.parameters:
            if parameter.name not in payload:
                continue
            value = payload[parameter.name]
            if parameter.location == ParameterLocation.HEADER:
                headers[parameter.name] = str(value)
            elif parameter.location == ParameterLocation.COOKIE:
                cookies[parameter.name] = str(value)
            elif parameter.location == ParameterLocation.BODY:
                body_payload = self._merge_body(body_payload, parameter.name, value)
            else:
                params[parameter.name] = value

        if operation.request_body is not None:
            body_payload = payload.get("body", body_payload if body_payload is not None else payload)

        method = binding.http_method or (operation.http_method.value if operation.http_method else "POST")
        url = self._build_url(endpoint, operation, payload, params)

        await self._auth_manager.apply(auth_config, headers, params, cookies)

        transport_params = self._build_transport_params(binding.message_binding)
        transport_params.update(params)

        return TransportRequest(
            url=url,
            method=method,
            headers=headers,
            params=transport_params,
            cookies=cookies,
            timeout_ms=binding.timeout_ms,
            body=body_payload,
        )

    @staticmethod
    def _merge_body(body: Any, name: str, value: Any) -> Any:
        if body is None:
            return {name: value}
        if isinstance(body, dict):
            body[name] = value
        return body

    @staticmethod
    def _binding_like_http(endpoint: str, operation: ServiceOperation) -> bool:
        return bool(operation.http_method or endpoint.startswith("http://") or endpoint.startswith("https://"))

    @staticmethod
    def _build_url(
        endpoint: str,
        operation: ServiceOperation,
        payload: dict[str, Any],
        params: dict[str, Any],
    ) -> str:
        if operation.path and RequestBuilder._binding_like_http(endpoint, operation):
            path = operation.path
            for parameter in operation.parameters:
                if parameter.location == ParameterLocation.PATH and parameter.name in payload:
                    path = path.replace(f"{{{parameter.name}}}", str(payload[parameter.name]))
            if endpoint.endswith("/") and path.startswith("/"):
                return endpoint[:-1] + path
            if not endpoint.endswith("/") and not path.startswith("/"):
                return f"{endpoint}/{path}"
            return endpoint + path
        if operation.channel:
            return operation.channel
        return endpoint

    @staticmethod
    def _build_transport_params(message_binding: MessageBinding | None) -> dict[str, Any]:
        if message_binding is None:
            return {}
        params: dict[str, Any] = {}
        if message_binding.topic:
            params["topic"] = message_binding.topic
        if message_binding.queue:
            params["queue"] = message_binding.queue
        if message_binding.group_id:
            params["group_id"] = message_binding.group_id
        if message_binding.routing_key:
            params["routing_key"] = message_binding.routing_key
        if message_binding.reply_to:
            params["reply_to"] = message_binding.reply_to
        if message_binding.subscription_type == SubscriptionType.PULL:
            params["poll"] = True
        return params
