"""Load and normalize service bindings from SSDM documents or binding JSON specs."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ...document.models.ssdm_models import (
    MessageBinding,
    MessageFormat,
    OperationType,
    RetryPolicy,
    ServiceBinding,
    SSDMDocument,
    SubscriptionType,
    Transport,
)
from ..bindings.binding_parser import BindingParser


@dataclass
class BindingCatalog:
    """Lookup table for operation-id → one or more service bindings."""

    by_operation: dict[str, list[ServiceBinding]]

    @property
    def operations(self) -> list[str]:
        return list(self.by_operation.keys())

    def add(self, binding: ServiceBinding) -> None:
        self.by_operation.setdefault(binding.operation_id, []).append(binding)

    def get(self, operation_id: str) -> list[ServiceBinding]:
        return list(self.by_operation.get(operation_id, []))

    def has(self, operation_id: str) -> bool:
        return operation_id in self.by_operation

    def add_many(self, bindings: list[ServiceBinding]) -> None:
        for binding in bindings:
            self.add(binding)

    @classmethod
    def from_bindings(cls, bindings: list[ServiceBinding]) -> "BindingCatalog":
        catalog = cls({})
        catalog.add_many(bindings)
        return catalog

    @classmethod
    def from_file(cls, path: str | Path) -> "BindingCatalog":
        path_obj = Path(path)
        bindings = BindingParser.parse_service_bindings_file(path_obj)
        return cls.from_bindings(bindings)

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "BindingCatalog":
        return cls.from_bindings(BindingParser.parse_raw(raw))

    @classmethod
    def from_ssdm_document(
        cls,
        document: SSDMDocument,
        *,
        default_transport: Transport = Transport.HTTP,
        endpoint_override: str | None = None,
    ) -> "BindingCatalog":
        catalog = cls({})
        for operation in document.operations:
            catalog.add(
                _operation_to_binding(
                    operation,
                    default_transport=default_transport,
                    endpoint_override=endpoint_override,
                    service_servers=document.servers,
                )
            )
        return catalog

    @classmethod
    def from_ssdm_documents(
        cls,
        documents: list[SSDMDocument],
        *,
        default_transport: Transport = Transport.HTTP,
        endpoint_override: str | None = None,
    ) -> "BindingCatalog":
        catalog = cls({})
        for doc in documents:
            if doc is None:
                continue
            for binding in from_ssdm_single(document=doc, default_transport=default_transport, endpoint_override=endpoint_override):
                catalog.add(binding)
        return catalog

    def merge(self, other: "BindingCatalog") -> None:
        for op_id, bindings in other.by_operation.items():
            self.by_operation.setdefault(op_id, []).extend(bindings)


# ---------------------------------------------------------------------------
# Builders
# ---------------------------------------------------------------------------
def _operation_to_binding(
    operation,
    *,
    default_transport: Transport,
    endpoint_override: str | None,
    service_servers,
) -> ServiceBinding:
    operation_id = operation.name
    transport = _infer_transport(operation, default_transport)

    endpoint = endpoint_override
    if endpoint is None and getattr(operation, "servers", None):
        if operation.servers:
            endpoint = operation.servers[0].url

    if endpoint is None and service_servers:
        endpoint = service_servers[0].url

    headers = {"X-Operation-Id": operation_id}
    for ann in getattr(operation, "annotations", []) or []:
        if getattr(ann, "key", "").lower().startswith("x-transport-header-"):
            header_name = ann.key.split("-", 2)[-1]
            headers[header_name] = str(ann.value)

    message_binding: MessageBinding | None = None
    path = getattr(operation, "path", None)
    message_path = getattr(operation, "channel", None)

    if transport in {Transport.AMQP, Transport.MQTT, Transport.KAFKA, Transport.SSE}:
        topic = message_path or path
        message_binding = MessageBinding(
            transport=transport,
            topic=topic,
            queue=topic if transport == Transport.AMQP else None,
            message_format=MessageFormat.JSON,
            subscription_type=_infer_subscription_type(operation.type),
            group_id=getattr(operation, "extensions", {}).get("message_group", None)
            if isinstance(getattr(operation, "extensions", {}), dict)
            else None,
            routing_key=getattr(operation, "extensions", {}).get("routing_key", None)
            if isinstance(getattr(operation, "extensions", {}), dict)
            else None,
            reply_to=getattr(operation, "extensions", {}).get("reply_to", None)
            if isinstance(getattr(operation, "extensions", {}), dict)
            else None,
        )

    if transport == Transport.GRPC:
        # Keep full method path in endpoint_url so transport adapters can route correctly.
        endpoint = _merge_endpoint_path(endpoint or "", str(path or operation_id))

    if operation.http_method:
        method = str(operation.http_method)
    else:
        method = None

    retry_policy = getattr(operation, "extensions", {}).get("retry_policy", RetryPolicy.NONE)
    if not isinstance(retry_policy, RetryPolicy):
        try:
            retry_policy = RetryPolicy(str(retry_policy))
        except Exception:
            retry_policy = RetryPolicy.NONE

    max_retries = getattr(operation, "extensions", {}).get("max_retries", 3)
    if not isinstance(max_retries, int):
        max_retries = 3

    return ServiceBinding(
        operation_id=operation_id,
        transport=transport,
        endpoint_url=endpoint,
        http_method=method,
        auth_config=None,
        timeout_ms=int(getattr(operation, "extensions", {}).get("timeout_ms", 30000))
        if isinstance(getattr(operation, "extensions", {}), dict)
        else 30000,
        retry_policy=retry_policy,
        max_retries=max_retries,
        headers=headers,
        message_binding=message_binding,
    )


def _merge_endpoint_path(base: str, path: str) -> str:
    if not base:
        return path
    if base.endswith("/"):
        return f"{base.rstrip('/')}" + (f"/{path.lstrip('/')}" if path else "")
    if path:
        return f"{base}/{path.lstrip('/')}"
    return base


def _infer_transport(operation, default_transport: Transport) -> Transport:
    if getattr(operation, "type", OperationType.REQUEST_RESPONSE) in {
        OperationType.PUBLISH,
        OperationType.SUBSCRIBE,
        OperationType.NOTIFICATION,
        OperationType.ONE_WAY,
    }:
        # Async/streaming operations are usually backed by message transport.
        return Transport.AMQP

    # If path clearly looks like a gRPC method path, use gRPC transport.
    path = getattr(operation, "path", "") or ""
    if path.startswith("/") and "." in path:
        return Transport.GRPC
    if operation.http_method:
        return Transport.HTTP

    op_extensions = getattr(operation, "extensions", {}) or {}
    if isinstance(op_extensions, dict):
        declared_transport = op_extensions.get("transport")
        if declared_transport:
            try:
                return Transport(declared_transport)
            except Exception:
                pass

    return default_transport


def _infer_subscription_type(op_type) -> SubscriptionType:
    if op_type == OperationType.SUBSCRIBE:
        return SubscriptionType.QUEUE
    if op_type == OperationType.PUBLISH:
        return SubscriptionType.PUB_SUB
    return SubscriptionType.PUB_SUB


def from_ssdm_single(
    *,
    document: SSDMDocument,
    default_transport: Transport = Transport.HTTP,
    endpoint_override: str | None = None,
) -> list[ServiceBinding]:
    return [
        _operation_to_binding(
            op,
            default_transport=default_transport,
            endpoint_override=endpoint_override,
            service_servers=document.servers,
        )
        for op in document.operations
    ]
