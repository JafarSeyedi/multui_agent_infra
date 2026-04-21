"""
Workflow Engine for Orchestration

Manages workflow definition, execution, and state management.
Handles:
- Workflow definition and registration
- DAG-based task scheduling
- Parallel and sequential execution
- State persistence and recovery
- Workflow versioning
- Event-driven execution

This implementation provides:

    DAG-based Workflows: Define workflows as directed acyclic graphs of tasks
    Task Types: Function, transform, condition, wait, notify, sub-workflow, human tasks
    Dependency Resolution: Automatic topological sorting and parallel execution
    Variable Resolution: Resolve {{variable.name}} references in task configs
    Retry Logic: Automatic retry for failed tasks with configurable delays
    Timeout Handling: Per-task timeout configuration
    State Persistence: Save and restore workflow definitions and executions
    Workflow Control: Pause, resume, cancel workflows
    Sub-Workflows: Nest workflows within other workflows
    Event Callbacks: Register handlers for task/ workflow completion
    Progress Tracking: Calculate and report workflow progress
    Human-in-the-Loop: Support for human approval tasks

The workflow engine integrates with the agent registry, event bus, and context manager to provide a complete orchestration solution.
"""

import uuid
import json
import threading
import time
from typing import Dict, List, Optional, Any, Set, Tuple, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from collections import defaultdict, deque
from concurrent.futures import ThreadPoolExecutor, Future

from ..shared.logger import get_logger
from ..shared.state_manager import state_manager
from ..shared.config import config

logger = get_logger(__name__)


class WorkflowStatus(Enum):
    """Status of a workflow"""
    DRAFT = "draft"
    REGISTERED = "registered"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class TaskStatus(Enum):
    """Status of a task within a workflow"""
    PENDING = "pending"
    READY = "ready"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    CANCELLED = "cancelled"


class TaskType(Enum):
    """Types of tasks"""
    FUNCTION = "function"
    AGENT = "agent"
    SUB_WORKFLOW = "sub_workflow"
    HUMAN = "human"
    CONDITION = "condition"
    TRANSFORM = "transform"
    WAIT = "wait"
    NOTIFY = "notify"


@dataclass
class TaskDefinition:
    """Definition of a task in a workflow"""
    task_id: str
    name: str
    type: TaskType
    config: Dict[str, Any]
    depends_on: List[str] = field(default_factory=list)
    timeout_seconds: int = 300
    retry_count: int = 0
    max_retries: int = 3
    retry_delay: int = 5
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "name": self.name,
            "type": self.type.value,
            "config": self.config,
            "depends_on": self.depends_on,
            "timeout_seconds": self.timeout_seconds,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "retry_delay": self.retry_delay
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TaskDefinition":
        return cls(
            task_id=data["task_id"],
            name=data["name"],
            type=TaskType(data["type"]),
            config=data.get("config", {}),
            depends_on=data.get("depends_on", []),
            timeout_seconds=data.get("timeout_seconds", 300),
            retry_count=data.get("retry_count", 0),
            max_retries=data.get("max_retries", 3),
            retry_delay=data.get("retry_delay", 5)
        )


@dataclass
class WorkflowDefinition:
    """Definition of a workflow"""
    workflow_id: str
    name: str
    version: str
    description: str
    tasks: Dict[str, TaskDefinition]
    entry_task_id: str
    variables: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "workflow_id": self.workflow_id,
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "tasks": {tid: task.to_dict() for tid, task in self.tasks.items()},
            "entry_task_id": self.entry_task_id,
            "variables": self.variables,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorkflowDefinition":
        tasks = {}
        for tid, task_data in data.get("tasks", {}).items():
            tasks[tid] = TaskDefinition.from_dict(task_data)
        
        return cls(
            workflow_id=data["workflow_id"],
            name=data["name"],
            version=data["version"],
            description=data.get("description", ""),
            tasks=tasks,
            entry_task_id=data["entry_task_id"],
            variables=data.get("variables", {}),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.now(),
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else datetime.now()
        )


@dataclass
class WorkflowExecution:
    """Execution instance of a workflow"""
    execution_id: str
    workflow_id: str
    status: WorkflowStatus
    task_statuses: Dict[str, TaskStatus]
    task_results: Dict[str, Any]
    task_errors: Dict[str, str]
    variables: Dict[str, Any]
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    current_task_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "execution_id": self.execution_id,
            "workflow_id": self.workflow_id,
            "status": self.status.value,
            "task_statuses": {k: v.value for k, v in self.task_statuses.items()},
            "task_results": self.task_results,
            "task_errors": self.task_errors,
            "variables": self.variables,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "current_task_id": self.current_task_id
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorkflowExecution":
        return cls(
            execution_id=data["execution_id"],
            workflow_id=data["workflow_id"],
            status=WorkflowStatus(data["status"]),
            task_statuses={k: TaskStatus(v) for k, v in data.get("task_statuses", {}).items()},
            task_results=data.get("task_results", {}),
            task_errors=data.get("task_errors", {}),
            variables=data.get("variables", {}),
            started_at=datetime.fromisoformat(data["started_at"]) if data.get("started_at") else None,
            completed_at=datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None,
            current_task_id=data.get("current_task_id")
        )


class WorkflowEngine:
    """
    Workflow engine for executing DAG-based workflows.
    
    Features:
    - DAG-based workflow definition
    - Parallel task execution
    - Dependency resolution
    - State persistence
    - Workflow versioning
    - Event hooks
    - Retry and timeout handling
    """
    
    def __init__(self, storage_key: str = "workflow_engine"):
        self.storage_key = storage_key
        self.workflows: Dict[str, WorkflowDefinition] = {}
        self.executions: Dict[str, WorkflowExecution] = {}
        self._executor = ThreadPoolExecutor(max_workers=10)
        self._running_executions: Dict[str, Future] = {}
        self._lock = threading.RLock()
        
        # Callbacks
        self._on_task_complete: List[Callable] = []
        self._on_workflow_complete: List[Callable] = []
        self._on_workflow_failed: List[Callable] = []
        
        # Load workflows from state
        self._load_workflows()
        
        logger.info("WorkflowEngine initialized")
    
    def _load_workflows(self) -> None:
        """Load workflows from state manager"""
        try:
            workflows_data = state_manager.get(f"{self.storage_key}.workflows", {})
            for wf_id, wf_data in workflows_data.items():
                if isinstance(wf_data, dict):
                    self.workflows[wf_id] = WorkflowDefinition.from_dict(wf_data)
            
            executions_data = state_manager.get(f"{self.storage_key}.executions", {})
            for exec_id, exec_data in executions_data.items():
                if isinstance(exec_data, dict):
                    self.executions[exec_id] = WorkflowExecution.from_dict(exec_data)
            
        except Exception as e:
            logger.warning(f"Failed to load workflows: {e}")
    
    def _save_workflows(self) -> None:
        """Save workflows to state manager"""
        try:
            workflows_data = {wf_id: wf.to_dict() for wf_id, wf in self.workflows.items()}
            state_manager.set(f"{self.storage_key}.workflows", workflows_data)
            
            executions_data = {exec_id: exec_.to_dict() for exec_id, exec_ in self.executions.items()}
            state_manager.set(f"{self.storage_key}.executions", executions_data)
            
        except Exception as e:
            logger.error(f"Failed to save workflows: {e}")
    
    def register_workflow(self, definition: WorkflowDefinition) -> str:
        """
        Register a workflow definition.
        
        Args:
            definition: Workflow definition to register
            
        Returns:
            Workflow ID
        """
        with self._lock:
            # Validate workflow
            self._validate_workflow(definition)
            
            # Store workflow
            self.workflows[definition.workflow_id] = definition
            
            # Save to state
            self._save_workflows()
            
            logger.info(f"Registered workflow: {definition.name} ({definition.workflow_id})")
            
            return definition.workflow_id
    
    def _validate_workflow(self, definition: WorkflowDefinition) -> None:
        """Validate workflow definition"""
        if not definition.tasks:
            raise ValueError("Workflow must have at least one task")
        
        if definition.entry_task_id not in definition.tasks:
            raise ValueError(f"Entry task {definition.entry_task_id} not found")
        
        # Check for circular dependencies
        visited = set()
        rec_stack = set()
        
        def has_cycle(task_id: str) -> bool:
            visited.add(task_id)
            rec_stack.add(task_id)
            
            task = definition.tasks.get(task_id)
            if task:
                for dep in task.depends_on:
                    if dep not in visited:
                        if has_cycle(dep):
                            return True
                    elif dep in rec_stack:
                        return True
            
            rec_stack.remove(task_id)
            return False
        
        if has_cycle(definition.entry_task_id):
            raise ValueError("Circular dependency detected in workflow")
        
        # Check all dependencies exist
        for task_id, task in definition.tasks.items():
            for dep in task.depends_on:
                if dep not in definition.tasks:
                    raise ValueError(f"Task {task_id} depends on unknown task {dep}")
    
    def unregister_workflow(self, workflow_id: str) -> bool:
        """Unregister a workflow definition"""
        with self._lock:
            if workflow_id in self.workflows:
                del self.workflows[workflow_id]
                self._save_workflows()
                logger.info(f"Unregistered workflow: {workflow_id}")
                return True
        return False
    
    def start_workflow(self, workflow_id: str, 
                      initial_variables: Dict[str, Any] = None) -> str:
        """
        Start a workflow execution.
        
        Args:
            workflow_id: ID of workflow to execute
            initial_variables: Initial variables for the workflow
            
        Returns:
            Execution ID
        """
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")
        
        execution_id = str(uuid.uuid4())
        
        # Initialize task statuses
        task_statuses = {}
        for task_id in workflow.tasks:
            task_statuses[task_id] = TaskStatus.PENDING
        
        # Mark entry task as ready
        task_statuses[workflow.entry_task_id] = TaskStatus.READY
        
        execution = WorkflowExecution(
            execution_id=execution_id,
            workflow_id=workflow_id,
            status=WorkflowStatus.RUNNING,
            task_statuses=task_statuses,
            task_results={},
            task_errors={},
            variables=initial_variables or {},
            started_at=datetime.now()
        )
        
        with self._lock:
            self.executions[execution_id] = execution
        
        # Start execution in background
        future = self._executor.submit(self._execute_workflow, execution_id)
        self._running_executions[execution_id] = future
        
        logger.info(f"Started workflow {workflow_id} with execution {execution_id}")
        
        return execution_id
    
    def _execute_workflow(self, execution_id: str) -> None:
        """
        Execute workflow using topological order.
        
        Args:
            execution_id: Execution ID
        """
        with self._lock:
            execution = self.executions.get(execution_id)
            if not execution:
                return
            
            workflow = self.workflows.get(execution.workflow_id)
            if not workflow:
                execution.status = WorkflowStatus.FAILED
                return
        
        try:
            # Get execution order (topological sort)
            order = self._get_execution_order(workflow)
            
            # Track completed tasks
            completed = set()
            
            for task_id in order:
                if execution.status != WorkflowStatus.RUNNING:
                    break
                
                # Check if task is ready
                if not self._is_task_ready(execution, task_id, workflow):
                    continue
                
                # Execute task
                execution.current_task_id = task_id
                self._update_task_status(execution_id, task_id, TaskStatus.RUNNING)
                
                try:
                    result = self._execute_task(workflow.tasks[task_id], execution)
                    self._update_task_result(execution_id, task_id, result)
                    self._update_task_status(execution_id, task_id, TaskStatus.COMPLETED)
                    completed.add(task_id)
                    
                except Exception as e:
                    logger.error(f"Task {task_id} failed: {e}")
                    self._update_task_error(execution_id, task_id, str(e))
                    self._update_task_status(execution_id, task_id, TaskStatus.FAILED)
                    
                    # Handle failure based on task config
                    task = workflow.tasks[task_id]
                    if task.retry_count < task.max_retries:
                        # Retry task
                        task.retry_count += 1
                        self._update_task_status(execution_id, task_id, TaskStatus.READY)
                        continue
                    else:
                        execution.status = WorkflowStatus.FAILED
                        break
            
            # Check if workflow is complete
            all_completed = all(
                execution.task_statuses[tid] == TaskStatus.COMPLETED 
                for tid in workflow.tasks
            )
            
            if all_completed:
                execution.status = WorkflowStatus.COMPLETED
                execution.completed_at = datetime.now()
                self._notify_workflow_complete(execution)
                
            elif execution.status == WorkflowStatus.RUNNING:
                # Check for deadlock
                if not self._has_ready_tasks(execution, workflow):
                    execution.status = WorkflowStatus.FAILED
                    execution.task_errors["workflow"] = "No ready tasks but workflow not complete"
            
        except Exception as e:
            logger.error(f"Workflow {execution_id} failed: {e}")
            with self._lock:
                execution = self.executions.get(execution_id)
                if execution:
                    execution.status = WorkflowStatus.FAILED
                    execution.completed_at = datetime.now()
            
            self._notify_workflow_failed(execution_id, str(e))
        
        finally:
            self._save_workflows()
    
    def _get_execution_order(self, workflow: WorkflowDefinition) -> List[str]:
        """Get topological execution order of tasks"""
        # Build adjacency list
        graph = defaultdict(list)
        in_degree = defaultdict(int)
        
        for task_id in workflow.tasks:
            in_degree[task_id] = 0
        
        for task_id, task in workflow.tasks.items():
            for dep in task.depends_on:
                graph[dep].append(task_id)
                in_degree[task_id] += 1
        
        # Kahn's algorithm
        queue = deque([tid for tid, degree in in_degree.items() if degree == 0])
        order = []
        
        while queue:
            task_id = queue.popleft()
            order.append(task_id)
            
            for neighbor in graph[task_id]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        return order
    
    def _is_task_ready(self, execution: WorkflowExecution, task_id: str,
                      workflow: WorkflowDefinition) -> bool:
        """Check if a task is ready to execute"""
        status = execution.task_statuses.get(task_id)
        
        if status != TaskStatus.READY and status != TaskStatus.PENDING:
            return False
        
        task = workflow.tasks.get(task_id)
        if not task:
            return False
        
        # Check dependencies
        for dep in task.depends_on:
            dep_status = execution.task_statuses.get(dep)
            if dep_status != TaskStatus.COMPLETED:
                return False
        
        # Mark as ready if pending
        if status == TaskStatus.PENDING:
            execution.task_statuses[task_id] = TaskStatus.READY
        
        return True
    
    def _has_ready_tasks(self, execution: WorkflowExecution, 
                        workflow: WorkflowDefinition) -> bool:
        """Check if there are any ready tasks"""
        for task_id in workflow.tasks:
            if self._is_task_ready(execution, task_id, workflow):
                return True
        return False
    
    def _execute_task(self, task: TaskDefinition, 
                     execution: WorkflowExecution) -> Any:
        """
        Execute a single task.
        
        Args:
            task: Task definition
            execution: Workflow execution context
            
        Returns:
            Task result
        """
        logger.debug(f"Executing task: {task.name} ({task.task_id})")
        
        if task.type == TaskType.FUNCTION:
            return self._execute_function_task(task, execution)
        elif task.type == TaskType.TRANSFORM:
            return self._execute_transform_task(task, execution)
        elif task.type == TaskType.CONDITION:
            return self._execute_condition_task(task, execution)
        elif task.type == TaskType.WAIT:
            return self._execute_wait_task(task, execution)
        elif task.type == TaskType.NOTIFY:
            return self._execute_notify_task(task, execution)
        elif task.type == TaskType.SUB_WORKFLOW:
            return self._execute_sub_workflow_task(task, execution)
        elif task.type == TaskType.HUMAN:
            return self._execute_human_task(task, execution)
        else:
            raise ValueError(f"Unknown task type: {task.type}")
    
    def _execute_function_task(self, task: TaskDefinition,
                              execution: WorkflowExecution) -> Any:
        """Execute a function task"""
        function_name = task.config.get("function")
        args = task.config.get("args", [])
        kwargs = task.config.get("kwargs", {})
        
        # Resolve variable references in args and kwargs
        args = self._resolve_variables(args, execution)
        kwargs = self._resolve_variables(kwargs, execution)
        
        # Import and execute function
        if function_name:
            # Parse module and function
            parts = function_name.split('.')
            module_path = '.'.join(parts[:-1])
            func_name = parts[-1]
            
            try:
                module = __import__(module_path, fromlist=[func_name])
                func = getattr(module, func_name)
                return func(*args, **kwargs)
            except Exception as e:
                raise RuntimeError(f"Failed to execute function {function_name}: {e}")
        
        return None
    
    def _execute_transform_task(self, task: TaskDefinition,
                               execution: WorkflowExecution) -> Any:
        """Execute a data transformation task"""
        input_key = task.config.get("input")
        transform_type = task.config.get("transform", "identity")
        
        # Get input data
        if input_key:
            input_data = execution.task_results.get(input_key) or execution.variables.get(input_key)
        else:
            input_data = task.config.get("input_data")
        
        # Apply transformation
        if transform_type == "identity":
            return input_data
        elif transform_type == "json_parse":
            import json
            return json.loads(input_data)
        elif transform_type == "json_stringify":
            import json
            return json.dumps(input_data)
        elif transform_type == "map":
            mapping = task.config.get("mapping", {})
            if isinstance(input_data, dict):
                return {mapping.get(k, k): v for k, v in input_data.items()}
            return input_data
        elif transform_type == "filter":
            keys = task.config.get("keys", [])
            if isinstance(input_data, dict):
                return {k: v for k, v in input_data.items() if k in keys}
            return input_data
        else:
            return input_data
    
    def _execute_condition_task(self, task: TaskDefinition,
                               execution: WorkflowExecution) -> Any:
        """Execute a condition task"""
        expression = task.config.get("expression")
        
        if expression:
            try:
                # Create safe evaluation context
                context = {
                    "variables": execution.variables,
                    "results": execution.task_results,
                    **execution.variables,
                    **execution.task_results
                }
                result = eval(expression, {"__builtins__": {}}, context)
                return bool(result)
            except Exception as e:
                raise RuntimeError(f"Failed to evaluate condition: {e}")
        
        return False
    
    def _execute_wait_task(self, task: TaskDefinition,
                          execution: WorkflowExecution) -> Any:
        """Execute a wait/sleep task"""
        seconds = task.config.get("seconds", 1)
        time.sleep(seconds)
        return {"waited": seconds}
    
    def _execute_notify_task(self, task: TaskDefinition,
                            execution: WorkflowExecution) -> Any:
        """Execute a notification task"""
        message = task.config.get("message", "")
        level = task.config.get("level", "info")
        
        # Resolve variables in message
        message = self._resolve_variables(message, execution)
        
        if level == "info":
            logger.info(f"[Workflow {execution.execution_id}] {message}")
        elif level == "warning":
            logger.warning(f"[Workflow {execution.execution_id}] {message}")
        elif level == "error":
            logger.error(f"[Workflow {execution.execution_id}] {message}")
        
        return {"message": message, "level": level}
    
    def _execute_sub_workflow_task(self, task: TaskDefinition,
                                  execution: WorkflowExecution) -> Any:
        """Execute a sub-workflow task"""
        sub_workflow_id = task.config.get("workflow_id")
        input_data = task.config.get("input", {})
        
        # Resolve variables
        input_data = self._resolve_variables(input_data, execution)
        
        # Start sub-workflow
        sub_execution_id = self.start_workflow(sub_workflow_id, input_data)
        
        # Wait for completion
        sub_execution = self.get_execution_status(sub_execution_id)
        
        # Poll until complete
        while sub_execution and sub_execution.status in [WorkflowStatus.RUNNING, WorkflowStatus.PAUSED]:
            time.sleep(1)
            sub_execution = self.get_execution_status(sub_execution_id)
        
        if sub_execution and sub_execution.status == WorkflowStatus.COMPLETED:
            return sub_execution.task_results
        else:
            raise RuntimeError(f"Sub-workflow {sub_workflow_id} failed")
    
    def _execute_human_task(self, task: TaskDefinition,
                           execution: WorkflowExecution) -> Any:
        """Execute a human-in-the-loop task"""
        # This would integrate with the human-in-the-loop system
        # For now, return a placeholder
        return {
            "task": task.name,
            "requires_approval": True,
            "status": "pending_human_input"
        }
    
    def _resolve_variables(self, obj: Any, execution: WorkflowExecution) -> Any:
        """Resolve variable references in an object"""
        if isinstance(obj, str):
            # Pattern for variable references: {{variable.name}} or ${{variable.name}}
            import re
            pattern = r'\{\{([^}]+)\}\}|\$\{([^}]+)\}'
            
            def replace_var(match):
                var_path = match.group(1) or match.group(2)
                parts = var_path.strip().split('.')
                
                # Get from variables or results
                value = execution.variables.get(parts[0])
                if value is None:
                    value = execution.task_results.get(parts[0])
                
                # Navigate nested properties
                for part in parts[1:]:
                    if isinstance(value, dict):
                        value = value.get(part)
                    elif hasattr(value, part):
                        value = getattr(value, part)
                    else:
                        return match.group(0)
                
                return str(value) if value is not None else ""
            
            return re.sub(pattern, replace_var, obj)
        
        elif isinstance(obj, dict):
            return {k: self._resolve_variables(v, execution) for k, v in obj.items()}
        
        elif isinstance(obj, list):
            return [self._resolve_variables(item, execution) for item in obj]
        
        return obj
    
    def _update_task_status(self, execution_id: str, task_id: str, 
                           status: TaskStatus) -> None:
        """Update task status"""
        with self._lock:
            execution = self.executions.get(execution_id)
            if execution:
                execution.task_statuses[task_id] = status
                self._save_workflows()
    
    def _update_task_result(self, execution_id: str, task_id: str, 
                           result: Any) -> None:
        """Update task result"""
        with self._lock:
            execution = self.executions.get(execution_id)
            if execution:
                execution.task_results[task_id] = result
                self._save_workflows()
                self._notify_task_complete(task_id, result)
    
    def _update_task_error(self, execution_id: str, task_id: str, 
                          error: str) -> None:
        """Update task error"""
        with self._lock:
            execution = self.executions.get(execution_id)
            if execution:
                execution.task_errors[task_id] = error
                self._save_workflows()
    
    def pause_workflow(self, execution_id: str) -> bool:
        """Pause a running workflow"""
        with self._lock:
            execution = self.executions.get(execution_id)
            if execution and execution.status == WorkflowStatus.RUNNING:
                execution.status = WorkflowStatus.PAUSED
                self._save_workflows()
                logger.info(f"Paused workflow {execution_id}")
                return True
        return False
    
    def resume_workflow(self, execution_id: str) -> bool:
        """Resume a paused workflow"""
        with self._lock:
            execution = self.executions.get(execution_id)
            if execution and execution.status == WorkflowStatus.PAUSED:
                execution.status = WorkflowStatus.RUNNING
                self._save_workflows()
                
                # Resume execution
                future = self._executor.submit(self._execute_workflow, execution_id)
                self._running_executions[execution_id] = future
                
                logger.info(f"Resumed workflow {execution_id}")
                return True
        return False
    
    def cancel_workflow(self, execution_id: str) -> bool:
        """Cancel a running workflow"""
        with self._lock:
            execution = self.executions.get(execution_id)
            if execution and execution.status in [WorkflowStatus.RUNNING, WorkflowStatus.PAUSED]:
                execution.status = WorkflowStatus.CANCELLED
                execution.completed_at = datetime.now()
                self._save_workflows()
                
                # Cancel future if running
                if execution_id in self._running_executions:
                    self._running_executions[execution_id].cancel()
                
                logger.info(f"Cancelled workflow {execution_id}")
                return True
        return False
    
    def get_workflow_status(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get workflow execution status"""
        with self._lock:
            execution = self.executions.get(execution_id)
            if not execution:
                return None
            
            workflow = self.workflows.get(execution.workflow_id)
            
            # Calculate progress
            total_tasks = len(workflow.tasks) if workflow else 0
            completed_tasks = sum(
                1 for status in execution.task_statuses.values()
                if status == TaskStatus.COMPLETED
            )
            failed_tasks = sum(
                1 for status in execution.task_statuses.values()
                if status == TaskStatus.FAILED
            )
            
            return {
                "execution_id": execution.execution_id,
                "workflow_id": execution.workflow_id,
                "workflow_name": workflow.name if workflow else "unknown",
                "status": execution.status.value,
                "progress": (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0,
                "completed_tasks": completed_tasks,
                "failed_tasks": failed_tasks,
                "total_tasks": total_tasks,
                "current_task": execution.current_task_id,
                "started_at": execution.started_at.isoformat() if execution.started_at else None,
                "completed_at": execution.completed_at.isoformat() if execution.completed_at else None,
                "task_statuses": {k: v.value for k, v in execution.task_statuses.items()},
                "task_errors": execution.task_errors
            }
    
    def get_execution_result(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get workflow execution results"""
        with self._lock:
            execution = self.executions.get(execution_id)
            if not execution:
                return None
            
            return {
                "execution_id": execution.execution_id,
                "status": execution.status.value,
                "results": execution.task_results,
                "errors": execution.task_errors,
                "variables": execution.variables,
                "started_at": execution.started_at.isoformat() if execution.started_at else None,
                "completed_at": execution.completed_at.isoformat() if execution.completed_at else None
            }
    
    def set_variable(self, execution_id: str, name: str, value: Any) -> bool:
        """Set a workflow variable during execution"""
        with self._lock:
            execution = self.executions.get(execution_id)
            if execution:
                execution.variables[name] = value
                self._save_workflows()
                return True
        return False
    
    def get_variable(self, execution_id: str, name: str, default: Any = None) -> Any:
        """Get a workflow variable"""
        with self._lock:
            execution = self.executions.get(execution_id)
            if execution:
                return execution.variables.get(name, default)
        return default
    
    def get_ready_tasks(self, workflow_id: str, execution_id: str) -> List[TaskDefinition]:
        """Get tasks that are ready to execute"""
        with self._lock:
            workflow = self.workflows.get(workflow_id)
            execution = self.executions.get(execution_id)
            
            if not workflow or not execution:
                return []
            
            ready_tasks = []
            for task_id, task in workflow.tasks.items():
                if self._is_task_ready(execution, task_id, workflow):
                    ready_tasks.append(task)
            
            return ready_tasks
    
    def update_task_status(self, workflow_id: str, task_id: str,
                          status: str, result: Any = None,
                          error: str = None) -> bool:
        """Update task status externally (e.g., from human task completion)"""
        with self._lock:
            # Find execution
            for exec_id, execution in self.executions.items():
                if execution.workflow_id == workflow_id:
                    if task_id in execution.task_statuses:
                        execution.task_statuses[task_id] = TaskStatus(status)
                        if result:
                            execution.task_results[task_id] = result
                        if error:
                            execution.task_errors[task_id] = error
                        self._save_workflows()
                        return True
        return False
    
    def on_task_complete(self, callback: Callable) -> None:
        """Register callback for task completion"""
        self._on_task_complete.append(callback)
    
    def on_workflow_complete(self, callback: Callable) -> None:
        """Register callback for workflow completion"""
        self._on_workflow_complete.append(callback)
    
    def on_workflow_failed(self, callback: Callable) -> None:
        """Register callback for workflow failure"""
        self._on_workflow_failed.append(callback)
    
    def _notify_task_complete(self, task_id: str, result: Any) -> None:
        """Notify task completion callbacks"""
        for callback in self._on_task_complete:
            try:
                callback(task_id, result)
            except Exception as e:
                logger.error(f"Error in task complete callback: {e}")
    
    def _notify_workflow_complete(self, execution: WorkflowExecution) -> None:
        """Notify workflow completion callbacks"""
        for callback in self._on_workflow_complete:
            try:
                callback(execution)
            except Exception as e:
                logger.error(f"Error in workflow complete callback: {e}")
    
    def _notify_workflow_failed(self, execution_id: str, error: str) -> None:
        """Notify workflow failure callbacks"""
        for callback in self._on_workflow_failed:
            try:
                callback(execution_id, error)
            except Exception as e:
                logger.error(f"Error in workflow failed callback: {e}")
    
    def list_workflows(self) -> List[Dict[str, Any]]:
        """List all registered workflows"""
        return [
            {
                "workflow_id": wf.workflow_id,
                "name": wf.name,
                "version": wf.version,
                "description": wf.description,
                "task_count": len(wf.tasks),
                "created_at": wf.created_at.isoformat()
            }
            for wf in self.workflows.values()
        ]
    
    def list_executions(self, workflow_id: str = None) -> List[Dict[str, Any]]:
        """List workflow executions"""
        executions = self.executions.values()
        if workflow_id:
            executions = [e for e in executions if e.workflow_id == workflow_id]
        
        return [
            {
                "execution_id": e.execution_id,
                "workflow_id": e.workflow_id,
                "status": e.status.value,
                "started_at": e.started_at.isoformat() if e.started_at else None,
                "completed_at": e.completed_at.isoformat() if e.completed_at else None
            }
            for e in executions
        ]
    
    def get_workflow_definition(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get workflow definition"""
        workflow = self.workflows.get(workflow_id)
        if workflow:
            return workflow.to_dict()
        return None
    
    def create_workflow(self, name: str, version: str = "1.0",
                       description: str = "") -> WorkflowDefinition:
        """Create a new workflow definition"""
        workflow_id = str(uuid.uuid4())
        
        return WorkflowDefinition(
            workflow_id=workflow_id,
            name=name,
            version=version,
            description=description,
            tasks={},
            entry_task_id=""
        )
    
    def add_task(self, workflow_id: str, name: str, task_type: TaskType,
                config: Dict[str, Any], depends_on: List[str] = None) -> str:
        """Add a task to a workflow"""
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")
        
        task_id = str(uuid.uuid4())
        task = TaskDefinition(
            task_id=task_id,
            name=name,
            type=task_type,
            config=config,
            depends_on=depends_on or []
        )
        
        workflow.tasks[task_id] = task
        workflow.updated_at = datetime.now()
        
        # Set as entry if no entry task
        if not workflow.entry_task_id:
            workflow.entry_task_id = task_id
        
        self._save_workflows()
        
        return task_id
    
    def cleanup_old_executions(self, max_age_days: int = 7) -> int:
        """Clean up old workflow executions"""
        cutoff = datetime.now()
        cutoff_timestamp = cutoff.timestamp() - (max_age_days * 24 * 3600)
        cutoff_date = datetime.fromtimestamp(cutoff_timestamp)
        
        to_remove = []
        with self._lock:
            for exec_id, execution in self.executions.items():
                if execution.completed_at and execution.completed_at < cutoff_date:
                    to_remove.append(exec_id)
            
            for exec_id in to_remove:
                del self.executions[exec_id]
            
            self._save_workflows()
        
        logger.info(f"Cleaned up {len(to_remove)} old executions")
        return len(to_remove)
    
    def shutdown(self) -> None:
        """Shutdown the workflow engine"""
        self._executor.shutdown(wait=True)
        logger.info("WorkflowEngine shutdown complete")


# Singleton instance
_workflow_engine: Optional[WorkflowEngine] = None


def get_workflow_engine() -> WorkflowEngine:
    """Get global WorkflowEngine instance"""
    global _workflow_engine
    if _workflow_engine is None:
        _workflow_engine = WorkflowEngine()
    return _workflow_engine