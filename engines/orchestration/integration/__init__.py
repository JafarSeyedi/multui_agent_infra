"""External system integration adapters.

Aligns integration layer with communication/runtime/data mapping layers.
"""

from .business_rule_adapter import BusinessRule, BusinessRuleAdapter
from .connector_registry import Connector, ConnectorCapability, ConnectorRegistry
from .data_mapper import DataMapper, DataMapping, MappingDirection, MappingType
from .message_adapter import MessageAdapter, MessageDeliveryPolicy, MessageRoute
from .script_executor import ScriptExecutionError, ScriptExecutor, ScriptLanguage
from .service_invoker import InvokeResult, InvokeStatus, ServiceInvoker, ServiceEndpoint
from .user_task_adapter import ClaimResult, TaskForm, UserTaskAdapter, UserTaskClaim

__all__ = [
    "BusinessRule",
    "BusinessRuleAdapter",
    "ClaimResult",
    "Connector",
    "ConnectorCapability",
    "ConnectorRegistry",
    "DataMapper",
    "DataMapping",
    "InvokeResult",
    "InvokeStatus",
    "MappingDirection",
    "MappingType",
    "MessageAdapter",
    "MessageDeliveryPolicy",
    "MessageRoute",
    "ScriptExecutionError",
    "ScriptExecutor",
    "ScriptLanguage",
    "ServiceEndpoint",
    "ServiceInvoker",
    "TaskForm",
    "UserTaskAdapter",
    "UserTaskClaim",
]
