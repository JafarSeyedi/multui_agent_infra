"""Generic SSDM-driven client runtime for south-bound service invocation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, cast

from ...document.models.ssdm_models import (
    AuthConfig,
    MessageFormat,
    MessageBinding,
    ParameterLocation,
    ServiceBinding,
    ServiceOperation,
    SubscriptionType,
    Transport,
)
from ..common.auth.auth_manager import AuthManager
from ..common.serialization.avro_serializer import AvroSerializer, MessageSerializer
from ..common.serialization.json_serializer import JSONSerializer
from ..common.serialization.protobuf_serializer import ProtobufSerializer
from ..common.transport.amqp_client import AMQPTransport
from ..common.transport.base import AbstractTransport, TransportRequest, TransportResponse
from ..common.transport.grpc_client import GRPCTransport
from ..common.transport.http_client import HTTPTransport
from ..common.transport.kafka_client import KafkaTransport
from ..common.transport.mcp_adapter import MCPAdapter
from .binding_loader import BindingCatalog
from .circuit_breaker import CircuitBreakerRegistry
from .service_discovery import ServiceDiscovery


class InvocationHook(Protocol):
    async def __call__(self, operation: ServiceOperation, payload: dict[str, Any]) -> Any: ...


@dataclass
class InvocationResult:
    operation_id: str
    transport: Transport
    request: TransportRequest | None
    response: TransportResponse | None
    payload: Any
    metadata: dict[str, Any] = field(default_factory=dict)


class ServiceInvocationClient:
    """Invoke SSDM service operations over generic transports."""

    def __init__(
        self,
        *,
        binding_catalog: BindingCatalog | None = None,
        service_discovery: ServiceDiscovery | None = None,
        auth_manager: AuthManager | None = None,
        transport_overrides: dict[Transport, AbstractTransport] | None = None,
        serializer_overrides: dict[MessageFormat, MessageSerializer] | None = None,
        operation_hooks: dict[str, InvocationHook] | None = None,
    ) -> None:
        self.binding_catalog = binding_catalog or BindingCatalog({})
        self.service_discovery = service_discovery or ServiceDiscovery()
        self.auth_manager = auth_manager or AuthManager()
        self.transport_overrides = transport_overrides or {}
        self.serializer_overrides = serializer_overrides or {}
        self.operation_hooks = operation_hooks or {}
        self._transports: dict[Transport, AbstractTransport] = {}
        self._mcp_adapters: dict[str, MCPAdapter] = {}
        self._circuit_breakers = CircuitBreakerRegistry()

    async def invoke(
        self,
        operation: ServiceOperation,
        arguments: dict[str, Any] | None = None,
        *,
        binding: ServiceBinding | None = None,
        auth_config: AuthConfig | None = None,
    ) -> InvocationResult:
        payload = dict(arguments or {})
        hook = self.operation_hooks.get(operation.name)
        if hook is not None:
            hook_result = await hook(operation, payload)
            return InvocationResult(
                operation_id=operation.name,
                transport=binding.transport if binding else Transport.HTTP,
                request=None,
                response=None,
                payload=hook_result,
                metadata={"source": "operation_hook"},
            )

        selected_binding = binding or self._select_binding(operation.name)
        if selected_binding is None:
            raise RuntimeError(f"No binding registered for operation '{operation.name}'")

        breaker = self._circuit_breakers.get(operation.name)
        result = await breaker.execute(
            lambda: self._invoke_bound(
                operation,
                payload,
                selected_binding,
                auth_config=auth_config or selected_binding.auth_config,
            )
        )
        return cast(InvocationResult, result)

    async def close(self) -> None:
        for adapter in self._mcp_adapters.values():
            await adapter.close()
        self._mcp_adapters.clear()

        for transport in self._transports.values():
            await transport.close()
        self._transports.clear()

    async def _invoke_bound(
        self,
        operation: ServiceOperation,
        payload: dict[str, Any],
        binding: ServiceBinding,
        *,
        auth_config: AuthConfig | None,
    ) -> InvocationResult:
        if binding.transport in {Transport.STDIO, Transport.SSE} and binding.mcp_tools:
            return await self._invoke_mcp(operation, payload, binding)

        request = await self._build_request(operation, payload, binding, auth_config=auth_config)
        serializer = self._select_serializer(binding.message_binding)
        transport = self._get_transport(binding)
        response = await transport.send(
            request,
            payload_serializer=serializer.serialize if serializer else None,
            content_type=serializer.content_type if serializer else None,
        )
        result_payload = self._decode_response(response, serializer)
        return InvocationResult(
            operation_id=operation.name,
            transport=binding.transport,
            request=request,
            response=response,
            payload=result_payload,
            metadata={"binding": binding.operation_id},
        )

    async def _invoke_mcp(
        self,
        operation: ServiceOperation,
        payload: dict[str, Any],
        binding: ServiceBinding,
    ) -> InvocationResult:
        tools = binding.mcp_tools or []
        if not tools:
            raise RuntimeError(f"MCP binding for operation '{operation.name}' has no tools")
        tool = tools[0]
        endpoint_key = binding.endpoint_url or binding.operation_id
        adapter = self._mcp_adapters.get(endpoint_key)
        if adapter is None:
            adapter = MCPAdapter(
                transport=binding.transport,
                command=getattr(binding, "command", None),
                server_url=binding.endpoint_url,
                timeout_ms=tool.timeout_ms or binding.timeout_ms,
            )
            self._mcp_adapters[endpoint_key] = adapter

        tool_payload = self._map_mcp_arguments(tool.parameter_mappings, payload)
        tool_result = await adapter.call_tool(tool.tool_name, tool_payload)
        mapped_result = self._map_mcp_response(tool.response_mappings, tool_result)
        return InvocationResult(
            operation_id=operation.name,
            transport=binding.transport,
            request=None,
            response=None,
            payload=mapped_result,
            metadata={"tool_name": tool.tool_name, "binding": binding.operation_id},
        )

    async def _build_request(
        self,
        operation: ServiceOperation,
        payload: dict[str, Any],
        binding: ServiceBinding,
        *,
        auth_config: AuthConfig | None,
    ) -> TransportRequest:
        resolved = self.service_discovery.resolve(
            operation.name,
            binding.endpoint_url,
            discovery=None,
        )
        endpoint = resolved.target or binding.endpoint_url
        if not endpoint:
            raise RuntimeError(f"No endpoint resolved for operation '{operation.name}'")

        headers = dict(binding.headers)
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
                if body_payload is None:
                    body_payload = {}
                if isinstance(body_payload, dict):
                    body_payload[parameter.name] = value
            else:
                params[parameter.name] = value

        if operation.request_body is not None:
            body_payload = payload.get("body", body_payload if body_payload is not None else payload)

        method = binding.http_method or (operation.http_method.value if operation.http_method else "POST")
        url = self._build_url(endpoint, operation, payload, params)

        await self.auth_manager.apply(auth_config, headers, params, cookies)

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

    def _build_url(
        self,
        endpoint: str,
        operation: ServiceOperation,
        payload: dict[str, Any],
        params: dict[str, Any],
    ) -> str:
        if operation.path and binding_like_http(endpoint, operation):
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

    def _build_transport_params(self, message_binding: MessageBinding | None) -> dict[str, Any]:
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

    def _select_binding(self, operation_id: str) -> ServiceBinding | None:
        bindings = self.binding_catalog.get(operation_id)
        return bindings[0] if bindings else None

    def _select_serializer(self, message_binding: MessageBinding | None) -> MessageSerializer | None:
        message_format = message_binding.message_format if message_binding else MessageFormat.JSON
        override = self.serializer_overrides.get(message_format)
        if override is not None:
            return override
        if message_format == MessageFormat.AVRO:
            return AvroSerializer()
        if message_format == MessageFormat.PROTOBUF:
            return ProtobufSerializer()
        return JSONSerializer()

    def _get_transport(self, binding: ServiceBinding) -> AbstractTransport:
        override = self.transport_overrides.get(binding.transport)
        if override is not None:
            return override
        cached = self._transports.get(binding.transport)
        if cached is not None:
            return cached
        if binding.transport in {Transport.HTTP, Transport.HTTPS, Transport.HTTP2}:
            transport: AbstractTransport = HTTPTransport(timeout_ms=binding.timeout_ms, max_retries=binding.max_retries)
        elif binding.transport == Transport.GRPC:
            transport = GRPCTransport(use_tls=binding.transport != Transport.GRPC and False, max_retries=binding.max_retries)
        elif binding.transport == Transport.AMQP:
            transport = AMQPTransport(request_timeout_ms=binding.timeout_ms, max_retries=binding.max_retries)
        elif binding.transport == Transport.KAFKA:
            transport = KafkaTransport(request_timeout_ms=binding.timeout_ms)
        else:
            raise RuntimeError(f"Unsupported transport '{binding.transport.value}'")
        self._transports[binding.transport] = transport
        return transport

    def _decode_response(self, response: TransportResponse, serializer: MessageSerializer | None) -> Any:
        if serializer is None:
            return response.body
        try:
            return serializer.deserialize(response.body)
        except Exception:
            return response.json()

    @staticmethod
    def _map_mcp_arguments(mappings: list[Any], payload: dict[str, Any]) -> dict[str, Any]:
        if not mappings:
            return payload
        result: dict[str, Any] = {}
        for mapping in mappings:
            result[mapping.target] = resolve_mapping_source(payload, mapping.source)
        return result

    @staticmethod
    def _map_mcp_response(mappings: list[Any], tool_result: dict[str, Any]) -> Any:
        if not mappings:
            return tool_result
        body: dict[str, Any] = {}
        headers: dict[str, Any] = {}
        for mapping in mappings:
            value = resolve_mapping_source(tool_result, mapping.source)
            if mapping.target.startswith("header."):
                headers[mapping.target.split(".", 1)[1]] = value
            else:
                body[mapping.target] = value
        if headers:
            body["_headers"] = headers
        return body


def resolve_mapping_source(payload: dict[str, Any], source: str) -> Any:
    current: Any = payload
    for part in source.split("."):
        if isinstance(current, dict):
            current = current.get(part)
        else:
            return None
    return current


def binding_like_http(endpoint: str, operation: ServiceOperation) -> bool:
    return bool(operation.http_method or endpoint.startswith("http://") or endpoint.startswith("https://"))
