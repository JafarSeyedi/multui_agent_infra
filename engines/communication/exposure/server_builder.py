"""North-bound runtime builder for SSDM service exposure."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable

from ...document.models.ssdm_models import (
    InternalComponentType,
    InternalServiceBinding,
    NorthBoundBinding,
    ParameterLocation,
    ResponseMapping,
    ServiceOperation,
)

OperationHandler = Callable[[ServiceOperation, dict[str, Any], InternalServiceBinding | None], Awaitable[Any]]


@dataclass
class BuiltOperation:
    operation: ServiceOperation
    binding: NorthBoundBinding
    route_key: str
    transport: str


@dataclass
class BuiltNorthBoundServer:
    operations: dict[str, BuiltOperation] = field(default_factory=dict)

    @property
    def routes(self) -> list[str]:
        return list(self.operations.keys())


class NorthBoundServerBuilder:
    """Builds a runtime dispatch table for north-bound SSDM operations."""

    def __init__(
        self,
        *,
        default_handler: OperationHandler | None = None,
        component_handlers: dict[InternalComponentType, OperationHandler] | None = None,
    ) -> None:
        self.default_handler = default_handler
        self.component_handlers = component_handlers or {}

    def build(self, operations: list[ServiceOperation], bindings: list[NorthBoundBinding]) -> BuiltNorthBoundServer:
        binding_map = {binding.operation_id: binding for binding in bindings}
        built = BuiltNorthBoundServer()
        for operation in operations:
            binding = binding_map.get(operation.name)
            if binding is None:
                continue
            route_key = self._route_key(operation)
            built.operations[route_key] = BuiltOperation(
                operation=operation,
                binding=binding,
                route_key=route_key,
                transport=binding.transport.value,
            )
        return built

    async def dispatch(
        self,
        operation: ServiceOperation,
        payload: dict[str, Any],
        *,
        binding: NorthBoundBinding,
    ) -> Any:
        internal = binding.internal_binding
        handler = None
        if internal is not None:
            handler = self.component_handlers.get(internal.component_type)
        if handler is None:
            handler = self.default_handler
        if handler is None:
            raise RuntimeError(f"No handler registered for operation '{operation.name}'")

        internal_payload = self._map_request(operation, payload, internal)
        result = await handler(operation, internal_payload, internal)
        return self._map_response(result, internal.response_mappings if internal is not None else [])

    @staticmethod
    def _route_key(operation: ServiceOperation) -> str:
        if operation.http_method and operation.path:
            return f"{operation.http_method.value} {operation.path}"
        if operation.channel:
            return f"{operation.type.value}:{operation.channel}"
        return operation.name

    @staticmethod
    def _map_request(
        operation: ServiceOperation,
        payload: dict[str, Any],
        internal: InternalServiceBinding | None,
    ) -> dict[str, Any]:
        if internal is None or not internal.parameter_mappings:
            return payload

        mapped: dict[str, Any] = {}
        for mapping in internal.parameter_mappings:
            mapped[mapping.target] = _resolve_source(payload, mapping.source)

        for parameter in operation.parameters:
            if parameter.location == ParameterLocation.BODY and parameter.name in payload:
                mapped.setdefault(parameter.name, payload[parameter.name])
        return mapped

    @staticmethod
    def _map_response(result: Any, mappings: list[ResponseMapping]) -> Any:
        if not mappings or not isinstance(result, dict):
            return result
        mapped: dict[str, Any] = {}
        for mapping in mappings:
            mapped[mapping.target] = _resolve_source(result, mapping.source)
        return mapped


def _resolve_source(payload: dict[str, Any], source: str) -> Any:
    current: Any = payload
    for part in source.split("."):
        if isinstance(current, dict):
            current = current.get(part)
        else:
            return None
    return current
