"""Communication engine for service consumption and exposure.

Imports are lazy — use ``from engines.communication import X`` to avoid
triggering deep dependency chains on package import.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .bindings.binding_parser import BindingParser, parse_bindings
    from .bindings.binding_writer import BindingWriter
    from .bindings.mcp_binding_writer import MCPBindingWriter
    from .common.auth.auth_manager import AuthManager
    from .common.serialization.json_serializer import JSONSerializer
    from .common.transport.http_client import HTTPTransport
    from .consumption.binding_loader import BindingCatalog
    from .consumption.client_generator import ServiceInvocationClient
    from .consumption.service_discovery import ServiceDiscovery, DiscoveryResult
    from .exposure.server_builder import NorthBoundServerBuilder, OperationHandler
    from .messaging.channel_manager import MessageChannelManager


def __getattr__(name: str) -> object:
    import importlib

    _LAZY: dict[str, str] = {
        "AuthManager": ".common.auth.auth_manager",
        "BindingCatalog": ".consumption.binding_loader",
        "BindingParser": ".bindings.binding_parser",
        "BindingWriter": ".bindings.binding_writer",
        "DiscoveryResult": ".consumption.service_discovery",
        "HTTPTransport": ".common.transport.http_client",
        "JSONSerializer": ".common.serialization.json_serializer",
        "MCPBindingWriter": ".bindings.mcp_binding_writer",
        "MessageChannelManager": ".messaging.channel_manager",
        "NorthBoundServerBuilder": ".exposure.server_builder",
        "OperationHandler": ".exposure.server_builder",
        "ServiceDiscovery": ".consumption.service_discovery",
        "ServiceInvocationClient": ".consumption.client_generator",
        "parse_bindings": ".bindings.binding_parser",
    }
    if name in _LAZY:
        return getattr(importlib.import_module(_LAZY[name], __package__), name)
    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)


__all__ = [
    "AuthManager",
    "BindingCatalog",
    "BindingParser",
    "BindingWriter",
    "DiscoveryResult",
    "HTTPTransport",
    "JSONSerializer",
    "MCPBindingWriter",
    "MessageChannelManager",
    "NorthBoundServerBuilder",
    "OperationHandler",
    "ServiceDiscovery",
    "ServiceInvocationClient",
    "parse_bindings",
]
