"""
Execution Context Management

Manages execution context for process instances including:
- Variable scopes and data flow
- Execution hierarchy (process, subprocess, activity)
- Context propagation and isolation
- Transactional boundaries
- MSDM schema binding for variable typing
- DSDM serialization for persistence
"""

from __future__ import annotations

import logging
from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Protocol, cast
from collections.abc import Callable
from uuid import uuid4

from ..._types import Metadata, RawData, VariableValue

from ...document.models.dsdm_models import DataDocument, DataSchemaReference, SchemaBinding
from ...document.models.media_types import MEDIA_TYPES
from ...document.models.msdm_models import Attribute, DataType, Entity, ScalarType
from ...document.parsers.dsdm_parsers.dsdm_utils import build_node_from_python
from ...document.writers.dsdm_writers.json_writer import JSONWriter


logger = logging.getLogger(__name__)


class ContextScope(Enum):
    """Context scope levels"""
    GLOBAL = "global"  # Engine-wide scope
    PROCESS = "process"  # Process instance scope
    SUBPROCESS = "subprocess"  # Subprocess scope
    ACTIVITY = "activity"  # Activity/task scope
    LOCAL = "local"  # Local execution scope


class VariableScope(Enum):
    """Variable visibility scope"""
    PUBLIC = "public"  # Visible to all scopes
    PROTECTED = "protected"  # Visible to current and child scopes
    PRIVATE = "private"  # Visible only in current scope


@dataclass
class Variable:
    """Process variable with metadata and MSDM schema binding"""
    name: str
    value: VariableValue
    type: str = "object"
    scope: VariableScope = VariableScope.PUBLIC
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    is_transient: bool = False
    metadata: Metadata = field(default_factory=dict)
    schema_binding: SchemaBinding | None = None
    _schema_entity_cache: Entity | None = field(default=None, repr=False)

    def bind_schema(self, entity: Entity | None = None, attribute: Attribute | None = None) -> None:
        """Bind this variable to an MSDM schema element for type validation."""
        self.schema_binding = SchemaBinding(entity=entity, attribute=attribute, source_schema=None)
        self._schema_entity_cache = entity
        self.updated_at = datetime.utcnow()

    def to_msdm_type(self) -> DataType:
        """Convert variable type to MSDM DataType."""
        type_map = {
            "boolean": ScalarType.BOOLEAN,
            "integer": ScalarType.INT,
            "double": ScalarType.DOUBLE,
            "float": ScalarType.FLOAT,
            "string": ScalarType.STRING,
            "list": ScalarType.ARRAY,
            "json": ScalarType.JSON,
            "bytes": ScalarType.BINARY,
            "null": ScalarType.NULL,
        }
        return DataType(base=type_map.get(self.type, ScalarType.ANY))

    def to_record_payload(self, *, instance_id: str, scope_id: str) -> RawData:
        return {
            "instance_id": instance_id,
            "scope_id": scope_id,
            "name": self.name,
            "value": self.value,
            "value_type": self.type,
            "updated_at": self.updated_at.isoformat(),
            "payload": {
                "scope": self.scope.value,
                "created_at": self.created_at.isoformat(),
                "is_transient": self.is_transient,
                "metadata": dict(self.metadata),
            },
        }

    @classmethod
    def from_record_payload(cls, payload: RawData) -> Variable:
        nested_payload = cast(dict[str, Any], payload.get("payload")) if isinstance(payload.get("payload"), dict) else {}
        schema_binding_data = nested_payload.get("schema_binding") if isinstance(nested_payload.get("schema_binding"), dict) else None
        schema_binding: SchemaBinding | None = None
        if schema_binding_data:
            entity_data = schema_binding_data.get("entity")
            if isinstance(entity_data, dict):
                schema_binding = SchemaBinding(
                    entity=Entity(name=str(entity_data.get("name", "unknown"))),
                    attribute=None,
                    source_schema=None,
                )
        return cls(
            name=str(payload["name"]),
            value=payload.get("value"),
            type=str(payload.get("value_type", "object")),
            scope=VariableScope(str(nested_payload.get("scope", VariableScope.PUBLIC.value))),
            created_at=_parse_datetime(nested_payload.get("created_at")),
            updated_at=_parse_datetime(payload.get("updated_at")),
            is_transient=bool(nested_payload.get("is_transient", False)),
            metadata=dict(nested_payload.get("metadata") or {}),
            schema_binding=schema_binding,
        )

    async def to_dsdm_document(self, *, instance_id: str, context_id: str) -> DataDocument:
        """Serialize this variable to a DSDM DataDocument."""
        payload = {
            "name": self.name,
            "value": self.value,
            "type": self.type,
            "scope": self.scope.value,
            "is_transient": self.is_transient,
            "updated_at": self.updated_at.isoformat(),
            "created_at": self.created_at.isoformat(),
            "metadata": dict(self.metadata),
        }
        node = build_node_from_python(payload, path=f"$.variables.{self.name}", name=self.name)
        return DataDocument(
            title=f"Variable {self.name}",
            document_id=f"variable:{instance_id}:{context_id}:{self.name}",
            media_type=MEDIA_TYPES["json"],
            root=node,
        )


_TYPE_INFERRERS: list[tuple[type, str]] = [
    (bool, "boolean"),
    (int, "integer"),
    (float, "double"),
    (str, "string"),
    (list, "list"),
    (tuple, "list"),
    (dict, "json"),
    (bytes, "bytes"),
]


def _INFER_TYPE(value: Any) -> str:
    if value is None:
        return "null"
    for cls, type_name in _TYPE_INFERRERS:
        if isinstance(value, cls):
            return type_name
    return "object"


class ExecutionContext:
    """
    Execution context for process instances.

    Manages hierarchical variable scopes, execution state, and context
    propagation through the process execution tree.
    Supports MSDM schema binding for variable validation and DSDM serialization.
    """

    def __init__(
        self,
        context_id: str,
        scope: ContextScope,
        parent: ExecutionContext | None = None
    ) -> None:
        self.context_id = context_id
        self.scope = scope
        self.parent = parent
        self.children: list[ExecutionContext] = []

        # MSDM schema binding for context-level typing
        self.schema_entity: Entity | None = None
        self._schema_registry: dict[str, Entity] = {}

        # Variable storage
        self.variables: dict[str, Variable] = {}

        # Execution metadata
        self.metadata: Metadata = {}
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

        # State tracking
        self.is_active = True
        self.is_scope = True

        # Register with parent
        if parent:
            parent.children.append(self)
    
    def set_variable(
        self,
        name: str,
        value: VariableValue,
        variable_type: str | None = None,
        scope: VariableScope = VariableScope.PUBLIC,
        is_transient: bool = False
    ) -> None:
        """Set a variable in this context"""
        if variable_type is None:
            variable_type = self._infer_type(value)
        
        if name in self.variables:
            # Update existing variable
            var = self.variables[name]
            var.value = value
            var.type = variable_type
            var.updated_at = datetime.utcnow()
        else:
            # Create new variable
            var = Variable(
                name=name,
                value=value,
                type=variable_type,
                scope=scope,
                is_transient=is_transient
            )
            self.variables[name] = var
        
        self.updated_at = datetime.utcnow()
        logger.debug(f"Set variable '{name}' in context {self.context_id}")
    
    def get_variable(self, name: str, search_parent: bool = True) -> VariableValue | None:
        """Get a variable value from this context or parent contexts"""
        # Check local variables
        if name in self.variables:
            var = self.variables[name]
            # Check visibility
            if var.scope != VariableScope.PRIVATE or not search_parent:
                return var.value
        
        # Search parent contexts if allowed
        if search_parent and self.parent:
            parent_value = self.parent.get_variable(name, search_parent=True)
            if parent_value is not None:
                return parent_value
        
        return None
    
    def get_variable_object(self, name: str) -> Variable | None:
        """Get the full variable object"""
        if name in self.variables:
            return self.variables[name]
        
        if self.parent:
            return self.parent.get_variable_object(name)
        
        return None
    
    def has_variable(self, name: str, search_parent: bool = True) -> bool:
        """Check if a variable exists"""
        if name in self.variables:
            return True
        
        if search_parent and self.parent:
            return self.parent.has_variable(name, search_parent=True)
        
        return False
    
    def remove_variable(self, name: str) -> bool:
        """Remove a variable from this context"""
        if name in self.variables:
            del self.variables[name]
            self.updated_at = datetime.utcnow()
            logger.debug(f"Removed variable '{name}' from context {self.context_id}")
            return True
        return False
    
    def get_all_variables(self, include_parent: bool = True) -> dict[str, VariableValue]:
        """Get all variables as a flat dictionary"""
        result = {}
        
        # Get parent variables first (so local variables override)
        if include_parent and self.parent:
            result.update(self.parent.get_all_variables(include_parent=True))
        
        # Add local variables
        for name, var in self.variables.items():
            if var.scope != VariableScope.PRIVATE or not include_parent:
                result[name] = var.value
        
        return result
    
    def set_variables(self, variables: dict[str, VariableValue]) -> None:
        """Set multiple variables at once"""
        for name, value in variables.items():
            self.set_variable(name, value)
    
    def create_child_context(
        self,
        scope: ContextScope,
        context_id: str | None = None
    ) -> ExecutionContext:
        """Create a child execution context"""
        if context_id is None:
            context_id = f"{self.context_id}:{str(uuid4())[:8]}"
        
        child = ExecutionContext(
            context_id=context_id,
            scope=scope,
            parent=self
        )
        
        logger.debug(f"Created child context {child.context_id} under {self.context_id}")
        return child
    
    def destroy(self) -> None:
        """Destroy this context and remove from parent"""
        self.is_active = False
        
        # Destroy all children
        for child in self.children[:]:
            child.destroy()
        
        # Remove from parent
        if self.parent:
            self.parent.children.remove(self)
        
        logger.debug(f"Destroyed context {self.context_id}")
    
    def copy_variables_to(self, target: ExecutionContext, names: list[str] | None = None) -> None:
        """Copy variables to another context"""
        if names is None:
            # Copy all non-private variables
            for name, var in self.variables.items():
                if var.scope != VariableScope.PRIVATE:
                    target.set_variable(
                        name=name,
                        value=deepcopy(var.value),
                        variable_type=var.type,
                        scope=var.scope,
                        is_transient=var.is_transient
                    )
        else:
            # Copy specific variables
            for name in names:
                if name in self.variables:
                    var = self.variables[name]
                    target.set_variable(
                        name=name,
                        value=deepcopy(var.value),
                        variable_type=var.type,
scope=var.scope,
                        is_transient=var.is_transient
                    )

    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Get metadata value"""
        return self.metadata.get(key, default)

    def set_metadata(self, key: str, value: Any) -> None:
        """Set metadata value"""
        self.metadata[key] = value
        self.updated_at = datetime.utcnow()

    def bind_schema(self, entity: Entity) -> None:
        """Bind an MSDM Entity to this context for variable type validation."""
        self.schema_entity = entity
        self._schema_registry[entity.name] = entity

    def get_schema(self, name: str) -> Entity | None:
        """Get a schema entity by name from the registry."""
        return self._schema_registry.get(name)

    async def serialize_to_dsdm(self, *, instance_id: str) -> DataDocument:
        """Serialize all variables in this context to a DSDM DataDocument."""
        variables_dict = {}
        for name, var in self.variables.items():
            if var.is_transient:
                continue
            variables_dict[name] = {
                "value": var.value,
                "type": var.type,
                "updated_at": var.updated_at.isoformat(),
            }
        node = build_node_from_python(
            {"variables": variables_dict, "context_id": self.context_id, "scope": self.scope.value},
            path=f"$.contexts.{self.context_id}",
            name=self.context_id,
        )
        return DataDocument(
            title=f"Context {self.context_id}",
            document_id=f"context:{instance_id}:{self.context_id}",
            media_type=MEDIA_TYPES["json"],
            root=node,
        )

    async def serialize_to_json(self, *, instance_id: str) -> str:
        """Serialize variables to JSON string via DSDM."""
        doc = await self.serialize_to_dsdm(instance_id=instance_id)
        raw = await JSONWriter().write(doc)
        return raw.decode("utf-8")

    def _infer_type(self, value: Any) -> str:
        return _INFER_TYPE(value)

    def to_dict(self) -> RawData:
        """Convert context to dictionary representation"""
        return {
            "context_id": self.context_id,
            "scope": self.scope.value,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "variables": {
                name: {
                    "value": var.value,
                    "type": var.type,
                    "scope": var.scope.value,
                    "is_transient": var.is_transient
                }
                for name, var in self.variables.items()
            },
            "metadata": self.metadata,
            "children_count": len(self.children)
        }

    def to_variable_record_payloads(self, *, instance_id: str) -> list[RawData]:
        return [
            variable.to_record_payload(instance_id=instance_id, scope_id=self.context_id)
            for variable in self.variables.values()
        ]

    def restore_variable_records(self, payloads: list[RawData]) -> None:
        self.variables = {}
        for payload in payloads:
            variable = Variable.from_record_payload(payload)
            self.variables[variable.name] = variable
        self.updated_at = datetime.utcnow()
    
    def __repr__(self) -> str:
        return (
            f"ExecutionContext(id={self.context_id}, scope={self.scope.value}, "
            f"vars={len(self.variables)}, children={len(self.children)})"
        )


class _VariableRepository(Protocol):
    async def save_persisted(self, key: str, record: RawData) -> None: ...
    def save(self, key: str, record: RawData) -> None: ...
    def get_by_scope(self, instance_id: str, context_id: str) -> list[RawData]: ...
    def list(self, predicate: Callable[[RawData], bool] | None = None) -> list[RawData]: ...


class ContextManager:
    """
    Manages execution contexts across the engine.
    
    Provides context lifecycle management, lookup, and cleanup.
    """
    
    def __init__(self, variable_repository: _VariableRepository | None = None) -> None:
        self.contexts: dict[str, ExecutionContext] = {}
        self.root_contexts: set[str] = set()
        self.variable_repository = variable_repository
    
    def create_context(
        self,
        scope: ContextScope,
        context_id: str | None = None,
        parent_id: str | None = None
    ) -> ExecutionContext:
        """Create a new execution context"""
        if context_id is None:
            context_id = str(uuid4())
        
        parent = None
        if parent_id:
            parent = self.contexts.get(parent_id)
            if not parent:
                raise ValueError(f"Parent context not found: {parent_id}")
        
        context = ExecutionContext(
            context_id=context_id,
            scope=scope,
            parent=parent
        )
        
        self.contexts[context_id] = context
        
        if parent is None:
            self.root_contexts.add(context_id)
        
        logger.info(f"Created context: {context_id} (scope: {scope.value})")
        return context
    
    def get_context(self, context_id: str) -> ExecutionContext | None:
        """Get a context by ID"""
        return self.contexts.get(context_id)
    
    def destroy_context(self, context_id: str) -> None:
        """Destroy a context and all its children"""
        context = self.contexts.get(context_id)
        if not context:
            return
        
        # Collect all contexts to destroy (context + all descendants)
        to_destroy = [context_id]
        queue = [context]
        
        while queue:
            current = queue.pop(0)
            for child in current.children:
                to_destroy.append(child.context_id)
                queue.append(child)
        
        # Destroy all contexts
        for ctx_id in to_destroy:
            ctx = self.contexts.pop(ctx_id, None)
            if ctx:
                ctx.destroy()
                self.root_contexts.discard(ctx_id)
        
        logger.info(f"Destroyed context tree: {context_id} ({len(to_destroy)} contexts)")
    
    def cleanup_inactive_contexts(self) -> int:
        """Clean up inactive contexts"""
        inactive = [
            ctx_id for ctx_id, ctx in self.contexts.items()
            if not ctx.is_active
        ]
        
        for ctx_id in inactive:
            self.destroy_context(ctx_id)
        
        return len(inactive)
    
    def get_statistics(self) -> RawData:
        """Get context manager statistics"""
        return {
            "total_contexts": len(self.contexts),
            "root_contexts": len(self.root_contexts),
            "active_contexts": sum(1 for ctx in self.contexts.values() if ctx.is_active),
            "scope_distribution": self._get_scope_distribution()
        }
    
    def _get_scope_distribution(self) -> dict[str, int]:
        """Get distribution of contexts by scope"""
        distribution: dict[str, int] = {}
        for ctx in self.contexts.values():
            scope = ctx.scope.value
            distribution[scope] = distribution.get(scope, 0) + 1
        return distribution

    async def persist_context_variables(self, instance_id: str, context_id: str) -> list[RawData]:
        context = self.get_context(context_id)
        if context is None:
            return []
        records = context.to_variable_record_payloads(instance_id=instance_id)
        if self.variable_repository is None:
            return records
        for record in records:
            key = f"{instance_id}:{context_id}:{record['name']}"
            if hasattr(self.variable_repository, "save_persisted"):
                await self.variable_repository.save_persisted(key, record)
            else:
                self.variable_repository.save(key, record)
        return records

    async def load_context_variables(self, instance_id: str, context_id: str) -> list[RawData]:
        context = self.get_context(context_id)
        if context is None:
            return []
        if self.variable_repository is None:
            return context.to_variable_record_payloads(instance_id=instance_id)
        if hasattr(self.variable_repository, "get_by_scope"):
            payloads = self.variable_repository.get_by_scope(instance_id, context_id)
        else:
            payloads = self.variable_repository.list(
                predicate=lambda row: row.get("instance_id") == instance_id and row.get("scope_id") == context_id
            )
        context.restore_variable_records(payloads)
        return payloads


def _parse_datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        return datetime.fromisoformat(value)
    return datetime.utcnow()
