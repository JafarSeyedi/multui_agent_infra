"""Communication engine for service consumption and exposure."""

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
