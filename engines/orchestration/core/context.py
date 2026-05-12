"""
Execution Context Management

Manages execution context for process instances including:
- Variable scopes and data flow
- Execution hierarchy (process, subprocess, activity)
- Context propagation and isolation
- Transactional boundaries
"""

import logging
from datetime import datetime
from typing import Any, Set
from enum import Enum
from dataclasses import dataclass, field
from uuid import uuid4
from copy import deepcopy


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
    """Process variable with metadata"""
    name: str
    value: Any
    type: str  # string, integer, boolean, json, xml, bytes, etc.
    scope: VariableScope = VariableScope.PUBLIC
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    is_transient: bool = False  # Transient variables not persisted
    metadata: dict[str, Any] = field(default_factory=dict)


class ExecutionContext:
    """
    Execution context for process instances.
    
    Manages hierarchical variable scopes, execution state, and context
    propagation through the process execution tree.
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
        self.children: list['ExecutionContext'] = []
        
        # Variable storage
        self.variables: dict[str, Variable] = {}
        
        # Execution metadata
        self.metadata: dict[str, Any] = {}
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        
        # State tracking
        self.is_active = True
        self.is_scope = True  # Whether this context creates a variable scope
        
        # Register with parent
        if parent:
            parent.children.append(self)
    
    def set_variable(
        self,
        name: str,
        value: Any,
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
    
    def get_variable(self, name: str, search_parent: bool = True) -> Any | None:
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
    
    def get_all_variables(self, include_parent: bool = True) -> dict[str, Any]:
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
    
    def set_variables(self, variables: dict[str, Any]) -> None:
        """Set multiple variables at once"""
        for name, value in variables.items():
            self.set_variable(name, value)
    
    def create_child_context(
        self,
        scope: ContextScope,
        context_id: str | None = None
    ) -> 'ExecutionContext':
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
    
    def copy_variables_to(self, target: 'ExecutionContext', names: list[str] | None = None) -> None:
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
    
    def _infer_type(self, value: Any) -> str:
        """Infer variable type from value"""
        if isinstance(value, bool):
            return "boolean"
        elif isinstance(value, int):
            return "integer"
        elif isinstance(value, float):
            return "double"
        elif isinstance(value, str):
            return "string"
        elif isinstance(value, (list, tuple)):
            return "list"
        elif isinstance(value, dict):
            return "json"
        elif isinstance(value, bytes):
            return "bytes"
        elif value is None:
            return "null"
        else:
            return "object"
    
    def to_dict(self) -> dict[str, Any]:
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
    
    def __repr__(self) -> str:
        return (
            f"ExecutionContext(id={self.context_id}, scope={self.scope.value}, "
            f"vars={len(self.variables)}, children={len(self.children)})"
        )


class ContextManager:
    """
    Manages execution contexts across the engine.
    
    Provides context lifecycle management, lookup, and cleanup.
    """
    
    def __init__(self) -> None:
        self.contexts: dict[str, ExecutionContext] = {}
        self.root_contexts: Set[str] = set()
    
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
    
    def get_statistics(self) -> dict[str, Any]:
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
