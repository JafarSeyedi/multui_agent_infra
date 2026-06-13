"""Generic SSDM-driven client runtime for south-bound service invocation."""

from __future__ import annotations

from typing import Any, Protocol, cast

from ...document.models.ssdm_models import (
    AuthConfig,
    MessageBinding,
    MessageFormat,
    ServiceBinding,
    ServiceOperation,
    Transport,
)
from ..common.auth.auth_manager import AuthManager
from ..common.serialization.avro_serializer import AvroSerializer, MessageSerializer
from ..common.serialization.json_serializer import JSONSerializer
from ..common.serialization.protobuf_serializer import ProtobufSerializer
from ..common.transport.base import AbstractTransport, TransportRequest, TransportResponse
from .binding_loader import BindingCatalog
from .circuit_breaker import CircuitBreakerRegistry
from .mcp_service import MCPService
from .models import InvocationResult
from .request_builder import RequestBuilder
from .service_discovery import ServiceDiscovery
from .transport_factory import TransportFactory


class InvocationHook(Protocol):
    async def __call__(self, operation: ServiceOperation, payload: dict[str, Any]) -> Any: ...


class ServiceInvocationClient:
    """Invoke SSDM service operations over generic transports.

    Facade — delegates to specialized collaborators:
    - RequestBuilder for request construction
    - TransportFactory for transport creation/caching
    - MCPService for MCP tool invocation
    - CircuitBreakerRegistry for resilience
    """

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
        self.operation_hooks = operation_hooks or {}
        self._serializer_overrides = serializer_overrides or {}
        self._transport_factory = TransportFactory(overrides=transport_overrides)
        self._mcp_service = MCPService()
        self._request_builder = RequestBuilder(auth_manager=self.auth_manager, service_discovery=self.service_discovery)
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
        await self._mcp_service.close_all()
        await self._transport_factory.close_all()

    async def _invoke_bound(
        self,
        operation: ServiceOperation,
        payload: dict[str, Any],
        binding: ServiceBinding,
        *,
        auth_config: AuthConfig | None,
    ) -> InvocationResult:
        if binding.transport in {Transport.STDIO, Transport.SSE} and binding.mcp_tools:
            return await self._mcp_service.invoke(operation, payload, binding)

        request = await self._request_builder.build(operation, payload, binding, auth_config=auth_config)
        serializer = self._select_serializer(binding.message_binding)
        transport = self._transport_factory.get(binding.transport, timeout_ms=binding.timeout_ms, max_retries=binding.max_retries)
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

    def _select_binding(self, operation_id: str) -> ServiceBinding | None:
        bindings = self.binding_catalog.get(operation_id)
        return bindings[0] if bindings else None

    def _select_serializer(self, message_binding: MessageBinding | None) -> MessageSerializer | None:
        message_format = message_binding.message_format if message_binding else MessageFormat.JSON
        override = self._serializer_overrides.get(message_format)
        if override is not None:
            return override
        if message_format == MessageFormat.AVRO:
            return AvroSerializer()
        if message_format == MessageFormat.PROTOBUF:
            return ProtobufSerializer()
        return JSONSerializer()

    def _decode_response(self, response: TransportResponse, serializer: MessageSerializer | None) -> Any:
        if serializer is None:
            return response.body
        try:
            return serializer.deserialize(response.body)
        except Exception:
            return response.json()
