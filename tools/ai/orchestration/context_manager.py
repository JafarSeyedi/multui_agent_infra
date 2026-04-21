"""
Context Manager for Orchestration

Manages execution context for workflows and tasks including:
- Context creation and lifecycle management
- Data sharing between tasks
- Variable scoping and isolation
- Context persistence and recovery
- Context inheritance and merging
- Context validation and schema enforcement

This implementation provides:

    Hierarchical Context Scoping: Global, workflow, task, and local scopes
    Variable Management: Set, get, delete variables with type validation
    Context Lifecycle: Create, update, complete, and cleanup contexts
    Schema Validation: Validate contexts against predefined schemas
    Variable References: Resolve {{variable.name}} references in values
    Context Inheritance: Parent-child context relationships
    Change Tracking: Audit trail of all context modifications
    Task Context: Separate context for task execution with input/output
    Persistence: Save and restore contexts via state manager
    Export/Import: Serialize and deserialize contexts for debugging
"""

import uuid
import json
import copy
import threading
from typing import Dict, List, Optional, Any, Set, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from collections import defaultdict
import re

from ..shared.logger import get_logger
from ..shared.state_manager import state_manager
from ..shared.config import config

logger = get_logger(__name__)


class ContextScope(Enum):
    """Scope levels for context variables"""
    GLOBAL = "global"       # Shared across all workflows
    WORKFLOW = "workflow"    # Specific to a workflow instance
    TASK = "task"           # Specific to a task
    LOCAL = "local"         # Temporary, not persisted


class AccessMode(Enum):
    """Access modes for context variables"""
    READ = "read"
    WRITE = "write"
    READ_WRITE = "read_write"
    APPEND = "append"


class VariableType(Enum):
    """Supported variable types for validation"""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    LIST = "list"
    DICT = "dict"
    ANY = "any"


@dataclass
class ContextVariable:
    """Represents a variable in the context"""
    name: str
    value: Any
    scope: ContextScope
    type: VariableType = VariableType.ANY
    required: bool = False
    immutable: bool = False
    description: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    created_by: Optional[str] = None  # Task or workflow ID
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "value": self._serialize_value(self.value),
            "scope": self.scope.value,
            "type": self.type.value,
            "required": self.required,
            "immutable": self.immutable,
            "description": self.description,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "created_by": self.created_by
        }
    
    def _serialize_value(self, value: Any) -> Any:
        """Serialize value for storage"""
        if isinstance(value, datetime):
            return value.isoformat()
        elif isinstance(value, (set, tuple)):
            return list(value)
        return value
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ContextVariable":
        return cls(
            name=data["name"],
            value=data["value"],
            scope=ContextScope(data["scope"]),
            type=VariableType(data.get("type", "any")),
            required=data.get("required", False),
            immutable=data.get("immutable", False),
            description=data.get("description"),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.now(),
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else datetime.now(),
            created_by=data.get("created_by")
        )


@dataclass
class ContextSchema:
    """Schema definition for context validation"""
    variables: Dict[str, VariableType]
    required: List[str]
    allowed_patterns: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "variables": {k: v.value for k, v in self.variables.items()},
            "required": self.required,
            "allowed_patterns": self.allowed_patterns
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ContextSchema":
        return cls(
            variables={k: VariableType(v) for k, v in data.get("variables", {}).items()},
            required=data.get("required", []),
            allowed_patterns=data.get("allowed_patterns", {})
        )


@dataclass
class WorkflowContext:
    """Execution context for a workflow"""
    context_id: str
    workflow_id: str
    parent_context_id: Optional[str] = None
    variables: Dict[str, ContextVariable] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    status: str = "active"  # active, paused, completed, failed
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "context_id": self.context_id,
            "workflow_id": self.workflow_id,
            "parent_context_id": self.parent_context_id,
            "variables": {k: v.to_dict() for k, v in self.variables.items()},
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "status": self.status,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorkflowContext":
        variables = {}
        for name, var_data in data.get("variables", {}).items():
            variables[name] = ContextVariable.from_dict(var_data)
        
        return cls(
            context_id=data["context_id"],
            workflow_id=data["workflow_id"],
            parent_context_id=data.get("parent_context_id"),
            variables=variables,
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.now(),
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else datetime.now(),
            completed_at=datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None,
            status=data.get("status", "active"),
            metadata=data.get("metadata", {})
        )


@dataclass
class TaskContext:
    """Execution context for a task"""
    task_id: str
    workflow_context_id: str
    parent_task_id: Optional[str] = None
    local_variables: Dict[str, Any] = field(default_factory=dict)
    input_data: Dict[str, Any] = field(default_factory=dict)
    output_data: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "workflow_context_id": self.workflow_context_id,
            "parent_task_id": self.parent_task_id,
            "local_variables": self.local_variables,
            "input_data": self.input_data,
            "output_data": self.output_data,
            "created_at": self.created_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TaskContext":
        return cls(
            task_id=data["task_id"],
            workflow_context_id=data["workflow_context_id"],
            parent_task_id=data.get("parent_task_id"),
            local_variables=data.get("local_variables", {}),
            input_data=data.get("input_data", {}),
            output_data=data.get("output_data", {}),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.now()
        )


@dataclass
class ContextChange:
    """Records a change to the context"""
    context_id: str
    variable_name: str
    old_value: Any
    new_value: Any
    changed_by: str
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "context_id": self.context_id,
            "variable_name": self.variable_name,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "changed_by": self.changed_by,
            "timestamp": self.timestamp.isoformat()
        }


class ContextManager:
    """
    Manages execution context for workflows and tasks.
    
    Features:
    - Hierarchical context scoping (global, workflow, task, local)
    - Variable persistence and recovery
    - Context inheritance and merging
    - Schema validation
    - Change tracking and auditing
    - Concurrent access management
    """
    
    def __init__(self, storage_key: str = "context_manager"):
        self.storage_key = storage_key
        self.workflow_contexts: Dict[str, WorkflowContext] = {}
        self.task_contexts: Dict[str, TaskContext] = {}
        self.global_variables: Dict[str, ContextVariable] = {}
        self.context_schemas: Dict[str, ContextSchema] = {}
        self.change_history: List[ContextChange] = []
        
        self._lock = threading.RLock()
        
        # Default schemas
        self._register_default_schemas()
        
        # Load persisted data
        self._load_data()
        
        logger.info("ContextManager initialized")
    
    def _register_default_schemas(self) -> None:
        """Register default context schemas"""
        # Workflow schema
        self.context_schemas["workflow_default"] = ContextSchema(
            variables={
                "workflow_name": VariableType.STRING,
                "workflow_version": VariableType.STRING,
                "created_by": VariableType.STRING,
                "priority": VariableType.INTEGER,
                "tags": VariableType.LIST,
                "parameters": VariableType.DICT
            },
            required=["workflow_name"],
            allowed_patterns={
                "workflow_name": r"^[a-zA-Z_][a-zA-Z0-9_]*$"
            }
        )
        
        # Task schema
        self.context_schemas["task_default"] = ContextSchema(
            variables={
                "task_name": VariableType.STRING,
                "task_type": VariableType.STRING,
                "retry_count": VariableType.INTEGER,
                "timeout": VariableType.INTEGER,
                "input": VariableType.DICT,
                "output": VariableType.DICT
            },
            required=["task_name", "task_type"]
        )
    
    def _load_data(self) -> None:
        """Load persisted context data"""
        try:
            # Load workflow contexts
            wf_data = state_manager.get(f"{self.storage_key}.workflows", {})
            for ctx_id, ctx_data in wf_data.items():
                if isinstance(ctx_data, dict):
                    self.workflow_contexts[ctx_id] = WorkflowContext.from_dict(ctx_data)
            
            # Load task contexts
            task_data = state_manager.get(f"{self.storage_key}.tasks", {})
            for task_id, task_ctx_data in task_data.items():
                if isinstance(task_ctx_data, dict):
                    self.task_contexts[task_id] = TaskContext.from_dict(task_ctx_data)
            
            # Load global variables
            global_data = state_manager.get(f"{self.storage_key}.global_vars", {})
            for name, var_data in global_data.items():
                if isinstance(var_data, dict):
                    self.global_variables[name] = ContextVariable.from_dict(var_data)
            
            # Load change history
            history_data = state_manager.get(f"{self.storage_key}.history", [])
            for change_data in history_data:
                if isinstance(change_data, dict):
                    self.change_history.append(ContextChange(**change_data))
            
        except Exception as e:
            logger.warning(f"Failed to load context data: {e}")
    
    def _save_data(self) -> None:
        """Save context data to persistence"""
        try:
            wf_data = {ctx_id: ctx.to_dict() for ctx_id, ctx in self.workflow_contexts.items()}
            state_manager.set(f"{self.storage_key}.workflows", wf_data)
            
            task_data = {task_id: ctx.to_dict() for task_id, ctx in self.task_contexts.items()}
            state_manager.set(f"{self.storage_key}.tasks", task_data)
            
            global_data = {name: var.to_dict() for name, var in self.global_variables.items()}
            state_manager.set(f"{self.storage_key}.global_vars", global_data)
            
            history_data = [change.to_dict() for change in self.change_history[-1000:]]  # Keep last 1000
            state_manager.set(f"{self.storage_key}.history", history_data)
            
        except Exception as e:
            logger.error(f"Failed to save context data: {e}")
    
    def create_context(self, workflow_id: str, parent_context_id: str = None,
                      initial_data: Dict[str, Any] = None,
                      schema_name: str = "workflow_default") -> WorkflowContext:
        """
        Create a new workflow context.
        
        Args:
            workflow_id: Workflow identifier
            parent_context_id: Parent context for inheritance
            initial_data: Initial context data
            schema_name: Schema to validate against
            
        Returns:
            Created WorkflowContext
        """
        context_id = str(uuid.uuid4())
        
        context = WorkflowContext(
            context_id=context_id,
            workflow_id=workflow_id,
            parent_context_id=parent_context_id,
            created_at=datetime.now(),
            status="active"
        )
        
        # Add initial variables
        if initial_data:
            for key, value in initial_data.items():
                self.set_variable(
                    context_id=context_id,
                    name=key,
                    value=value,
                    scope=ContextScope.WORKFLOW,
                    created_by="context_creation"
                )
        
        # Validate against schema
        if schema_name in self.context_schemas:
            self.validate_context(context, schema_name)
        
        with self._lock:
            self.workflow_contexts[context_id] = context
        
        self._save_data()
        
        logger.debug(f"Created workflow context {context_id} for workflow {workflow_id}")
        
        return context
    
    def create_task_context(self, task_id: str, workflow_context_id: str,
                           parent_task_id: str = None,
                           input_data: Dict[str, Any] = None) -> TaskContext:
        """
        Create a new task context.
        
        Args:
            task_id: Task identifier
            workflow_context_id: Parent workflow context
            parent_task_id: Parent task (for nested tasks)
            input_data: Input data for the task
            
        Returns:
            Created TaskContext
        """
        task_context = TaskContext(
            task_id=task_id,
            workflow_context_id=workflow_context_id,
            parent_task_id=parent_task_id,
            input_data=input_data or {},
            created_at=datetime.now()
        )
        
        with self._lock:
            self.task_contexts[task_id] = task_context
        
        self._save_data()
        
        logger.debug(f"Created task context for task {task_id}")
        
        return task_context
    
    def get_context(self, context_id: str) -> Optional[WorkflowContext]:
        """Get workflow context by ID"""
        with self._lock:
            return self.workflow_contexts.get(context_id)
    
    def get_task_context(self, task_id: str) -> Optional[TaskContext]:
        """Get task context by task ID"""
        with self._lock:
            return self.task_contexts.get(task_id)
    
    def set_variable(self, context_id: str, name: str, value: Any,
                    scope: ContextScope = ContextScope.WORKFLOW,
                    immutable: bool = False,
                    var_type: VariableType = VariableType.ANY,
                    created_by: str = None) -> bool:
        """
        Set a variable in the context.
        
        Args:
            context_id: Context identifier
            name: Variable name
            value: Variable value
            scope: Variable scope
            immutable: Whether variable can be modified
            var_type: Expected variable type
            created_by: Creator identifier
            
        Returns:
            True if successful
        """
        with self._lock:
            # Get the appropriate variable store
            if scope == ContextScope.GLOBAL:
                var_store = self.global_variables
            else:
                context = self.workflow_contexts.get(context_id)
                if not context:
                    logger.error(f"Context {context_id} not found")
                    return False
                var_store = context.variables
            
            # Check immutability
            if name in var_store and var_store[name].immutable:
                logger.warning(f"Cannot modify immutable variable {name}")
                return False
            
            # Get old value for change tracking
            old_value = var_store[name].value if name in var_store else None
            
            # Create or update variable
            variable = ContextVariable(
                name=name,
                value=value,
                scope=scope,
                type=var_type,
                immutable=immutable,
                created_by=created_by,
                updated_at=datetime.now()
            )
            
            if name in var_store:
                variable.created_at = var_store[name].created_at
            
            var_store[name] = variable
            
            # Record change
            change = ContextChange(
                context_id=context_id,
                variable_name=name,
                old_value=old_value,
                new_value=value,
                changed_by=created_by or "system",
                timestamp=datetime.now()
            )
            self.change_history.append(change)
            
            self._save_data()
            
            logger.debug(f"Set variable {name}={value} in context {context_id}")
            return True
    
    def get_variable(self, context_id: str, name: str, 
                    default: Any = None,
                    scope: ContextScope = None) -> Any:
        """
        Get a variable from the context.
        
        Args:
            context_id: Context identifier
            name: Variable name
            default: Default value if not found
            scope: Specific scope to look in (searches all if None)
            
        Returns:
            Variable value or default
        """
        with self._lock:
            # Check global scope
            if scope is None or scope == ContextScope.GLOBAL:
                if name in self.global_variables:
                    return self.global_variables[name].value
            
            # Check workflow context
            context = self.workflow_contexts.get(context_id)
            if context:
                if scope is None or scope == ContextScope.WORKFLOW:
                    if name in context.variables:
                        return context.variables[name].value
                
                # Check parent contexts
                if scope is None and context.parent_context_id:
                    return self.get_variable(context.parent_context_id, name, default, scope)
            
            # Check task context
            task_ctx = self.task_contexts.get(context_id)
            if task_ctx and (scope is None or scope == ContextScope.TASK):
                if name in task_ctx.local_variables:
                    return task_ctx.local_variables[name]
                if name in task_ctx.input_data:
                    return task_ctx.input_data[name]
                if name in task_ctx.output_data:
                    return task_ctx.output_data[name]
            
            return default
    
    def get_all_variables(self, context_id: str, 
                         include_global: bool = True,
                         include_parent: bool = True) -> Dict[str, Any]:
        """
        Get all variables from a context.
        
        Args:
            context_id: Context identifier
            include_global: Include global variables
            include_parent: Include parent context variables
            
        Returns:
            Dictionary of all variables
        """
        result = {}
        
        with self._lock:
            # Add global variables
            if include_global:
                for name, var in self.global_variables.items():
                    result[name] = var.value
            
            # Add workflow context variables
            context = self.workflow_contexts.get(context_id)
            if context:
                for name, var in context.variables.items():
                    result[name] = var.value
                
                # Add parent context variables
                if include_parent and context.parent_context_id:
                    parent_vars = self.get_all_variables(context.parent_context_id, False, True)
                    result.update(parent_vars)
            
            # Add task context variables
            task_ctx = self.task_contexts.get(context_id)
            if task_ctx:
                result.update(task_ctx.local_variables)
                result.update(task_ctx.input_data)
                result.update(task_ctx.output_data)
        
        return result
    
    def delete_variable(self, context_id: str, name: str,
                       scope: ContextScope = ContextScope.WORKFLOW) -> bool:
        """
        Delete a variable from the context.
        
        Args:
            context_id: Context identifier
            name: Variable name
            scope: Variable scope
            
        Returns:
            True if deleted
        """
        with self._lock:
            if scope == ContextScope.GLOBAL:
                if name in self.global_variables:
                    old_value = self.global_variables[name].value
                    del self.global_variables[name]
                    
                    # Record deletion
                    change = ContextChange(
                        context_id="global",
                        variable_name=name,
                        old_value=old_value,
                        new_value=None,
                        changed_by="system",
                        timestamp=datetime.now()
                    )
                    self.change_history.append(change)
                    
                    self._save_data()
                    return True
            else:
                context = self.workflow_contexts.get(context_id)
                if context and name in context.variables:
                    old_value = context.variables[name].value
                    del context.variables[name]
                    
                    change = ContextChange(
                        context_id=context_id,
                        variable_name=name,
                        old_value=old_value,
                        new_value=None,
                        changed_by="system",
                        timestamp=datetime.now()
                    )
                    self.change_history.append(change)
                    
                    self._save_data()
                    return True
            
            return False
    
    def update_task_output(self, task_id: str, output_data: Dict[str, Any]) -> bool:
        """
        Update task output data.
        
        Args:
            task_id: Task identifier
            output_data: Output data to merge
            
        Returns:
            True if successful
        """
        with self._lock:
            task_ctx = self.task_contexts.get(task_id)
            if not task_ctx:
                logger.error(f"Task context {task_id} not found")
                return False
            
            task_ctx.output_data.update(output_data)
            
            # Also update workflow context with output
            for key, value in output_data.items():
                self.set_variable(
                    task_ctx.workflow_context_id,
                    f"task_{task_id}_{key}",
                    value,
                    scope=ContextScope.WORKFLOW,
                    created_by=task_id
                )
            
            self._save_data()
            return True
    
    def get_task_input(self, task_id: str) -> Dict[str, Any]:
        """Get input data for a task"""
        with self._lock:
            task_ctx = self.task_contexts.get(task_id)
            if task_ctx:
                return task_ctx.input_data.copy()
            return {}
    
    def resolve_variable_references(self, context_id: str, 
                                   value: Any) -> Any:
        """
        Resolve variable references in a value.
        
        Supports syntax: {{variable.name}} or ${{variable.name}}
        
        Args:
            context_id: Context to resolve from
            value: Value containing references
            
        Returns:
            Value with references resolved
        """
        if isinstance(value, str):
            # Pattern for variable references
            pattern = r'\{\{([^}]+)\}\}|\$\{([^}]+)\}'
            
            def replace_var(match):
                var_path = match.group(1) or match.group(2)
                parts = var_path.strip().split('.')
                
                # Get variable value
                current_value = self.get_variable(context_id, parts[0])
                
                # Navigate nested properties
                for part in parts[1:]:
                    if isinstance(current_value, dict):
                        current_value = current_value.get(part)
                    elif hasattr(current_value, part):
                        current_value = getattr(current_value, part)
                    else:
                        return match.group(0)  # Keep original if not found
                
                return str(current_value) if current_value is not None else ""
            
            return re.sub(pattern, replace_var, value)
        
        elif isinstance(value, dict):
            return {
                k: self.resolve_variable_references(context_id, v)
                for k, v in value.items()
            }
        
        elif isinstance(value, list):
            return [
                self.resolve_variable_references(context_id, item)
                for item in value
            ]
        
        return value
    
    def merge_contexts(self, target_context_id: str, 
                      source_context_id: str,
                      overwrite: bool = False) -> bool:
        """
        Merge source context into target context.
        
        Args:
            target_context_id: Target context ID
            source_context_id: Source context ID
            overwrite: Whether to overwrite existing variables
            
        Returns:
            True if successful
        """
        with self._lock:
            target = self.workflow_contexts.get(target_context_id)
            source = self.workflow_contexts.get(source_context_id)
            
            if not target or not source:
                logger.error(f"Context not found: {target_context_id} or {source_context_id}")
                return False
            
            for name, var in source.variables.items():
                if overwrite or name not in target.variables:
                    target.variables[name] = copy.deepcopy(var)
                    target.variables[name].updated_at = datetime.now()
            
            self._save_data()
            return True
    
    def validate_context(self, context: WorkflowContext, 
                        schema_name: str) -> Tuple[bool, List[str]]:
        """
        Validate context against a schema.
        
        Args:
            context: Workflow context to validate
            schema_name: Name of schema to validate against
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        if schema_name not in self.context_schemas:
            return True, []  # No schema, no validation
        
        schema = self.context_schemas[schema_name]
        errors = []
        
        # Check required variables
        for required_var in schema.required:
            if required_var not in context.variables:
                errors.append(f"Required variable '{required_var}' missing")
        
        # Check variable types
        for name, var in context.variables.items():
            if name in schema.variables:
                expected_type = schema.variables[name]
                actual_type = self._get_value_type(var.value)
                
                if expected_type != VariableType.ANY and actual_type != expected_type:
                    errors.append(
                        f"Variable '{name}' expected type {expected_type.value}, "
                        f"got {actual_type.value}"
                    )
            
            # Check pattern
            if name in schema.allowed_patterns:
                pattern = schema.allowed_patterns[name]
                if isinstance(var.value, str):
                    if not re.match(pattern, var.value):
                        errors.append(
                            f"Variable '{name}' value '{var.value}' does not match pattern '{pattern}'"
                        )
        
        return len(errors) == 0, errors
    
    def _get_value_type(self, value: Any) -> VariableType:
        """Get VariableType from Python value"""
        if isinstance(value, str):
            return VariableType.STRING
        elif isinstance(value, int):
            return VariableType.INTEGER
        elif isinstance(value, float):
            return VariableType.FLOAT
        elif isinstance(value, bool):
            return VariableType.BOOLEAN
        elif isinstance(value, list):
            return VariableType.LIST
        elif isinstance(value, dict):
            return VariableType.DICT
        else:
            return VariableType.ANY
    
    def complete_context(self, context_id: str, status: str = "completed") -> bool:
        """
        Mark a workflow context as completed.
        
        Args:
            context_id: Context identifier
            status: Final status (completed, failed, cancelled)
            
        Returns:
            True if successful
        """
        with self._lock:
            context = self.workflow_contexts.get(context_id)
            if not context:
                return False
            
            context.status = status
            context.completed_at = datetime.now()
            
            self._save_data()
            return True
    
    def get_context_history(self, context_id: str, limit: int = 100) -> List[ContextChange]:
        """Get change history for a specific context"""
        return [
            change for change in self.change_history
            if change.context_id == context_id
        ][-limit:]
    
    def export_context(self, context_id: str, include_history: bool = False) -> Dict[str, Any]:
        """Export context for debugging or serialization"""
        with self._lock:
            context = self.workflow_contexts.get(context_id)
            if not context:
                return {"error": "Context not found"}
            
            result = context.to_dict()
            
            if include_history:
                result["history"] = [
                    change.to_dict() for change in self.get_context_history(context_id)
                ]
            
            return result
    
    def import_context(self, context_data: Dict[str, Any]) -> Optional[WorkflowContext]:
        """Import a previously exported context"""
        try:
            context = WorkflowContext.from_dict(context_data)
            
            with self._lock:
                # Generate new ID to avoid conflicts
                context.context_id = str(uuid.uuid4())
                self.workflow_contexts[context.context_id] = context
            
            self._save_data()
            
            return context
            
        except Exception as e:
            logger.error(f"Failed to import context: {e}")
            return None
    
    def cleanup_old_contexts(self, max_age_days: int = 7) -> int:
        """Clean up completed contexts older than max_age_days"""
        cutoff = datetime.now()
        cutoff_timestamp = cutoff.timestamp() - (max_age_days * 24 * 3600)
        cutoff_date = datetime.fromtimestamp(cutoff_timestamp)
        
        cleaned = 0
        
        with self._lock:
            # Clean workflow contexts
            to_remove = []
            for ctx_id, context in self.workflow_contexts.items():
                if context.status in ["completed", "failed"]:
                    if context.completed_at and context.completed_at < cutoff_date:
                        to_remove.append(ctx_id)
            
            for ctx_id in to_remove:
                del self.workflow_contexts[ctx_id]
                cleaned += 1
            
            # Clean task contexts
            to_remove_tasks = []
            for task_id, task_ctx in self.task_contexts.items():
                if task_ctx.created_at < cutoff_date:
                    to_remove_tasks.append(task_id)
            
            for task_id in to_remove_tasks:
                del self.task_contexts[task_id]
                cleaned += 1
            
            self._save_data()
        
        logger.info(f"Cleaned up {cleaned} old contexts")
        return cleaned
    
    def get_context_summary(self) -> Dict[str, Any]:
        """Get summary of all contexts"""
        with self._lock:
            active_workflows = len([c for c in self.workflow_contexts.values() if c.status == "active"])
            completed_workflows = len([c for c in self.workflow_contexts.values() if c.status == "completed"])
            failed_workflows = len([c for c in self.workflow_contexts.values() if c.status == "failed"])
            
            return {
                "total_workflow_contexts": len(self.workflow_contexts),
                "active_workflows": active_workflows,
                "completed_workflows": completed_workflows,
                "failed_workflows": failed_workflows,
                "total_task_contexts": len(self.task_contexts),
                "global_variables": len(self.global_variables),
                "total_changes": len(self.change_history),
                "schemas_loaded": len(self.context_schemas)
            }
    
    def register_schema(self, name: str, schema: ContextSchema) -> None:
        """Register a new context schema"""
        self.context_schemas[name] = schema
        logger.debug(f"Registered schema: {name}")
    
    def clear(self) -> None:
        """Clear all contexts (use with caution)"""
        with self._lock:
            self.workflow_contexts.clear()
            self.task_contexts.clear()
            self.global_variables.clear()
            self.change_history.clear()
            self._save_data()
            logger.warning("All contexts cleared")


# Singleton instance
_context_manager: Optional[ContextManager] = None


def get_context_manager() -> ContextManager:
    """Get global ContextManager instance"""
    global _context_manager
    if _context_manager is None:
        _context_manager = ContextManager()
    return _context_manager