"""
Base Orchestrator for Multi-Agent System

Provides the foundational orchestration layer for managing workflows, agents, and task execution.
Handles:
- Workflow lifecycle management
- Agent coordination and communication
- Task scheduling and execution
- State management and persistence
- Error handling and recovery
- Event propagation

This implementation provides:

Task Management: Submit, queue, execute, and track tasks with priority levels
Workflow Orchestration: Start, monitor, and cancel workflows
Agent Coordination: Select appropriate agents for tasks and handle failover
State Persistence: Save and restore orchestrator state
Event Bus Integration: Publish and subscribe to events
Health Monitoring: Track orchestrator health and detect degradation
Error Handling: Retry failed tasks, handle timeouts, reassign from failed agents
Metrics Collection: Track tasks, workflows, and performance metrics
Callback System: Register callbacks for task/workflow completion and errors
Abstract Methods: Extensible for concrete orchestrator implementations
"""

import asyncio
import threading
import uuid
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Set, Tuple, Callable, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, Future

from ..shared.logger import get_logger
from ..shared.state_manager import state_manager
from ..shared.config import config

from .agent_registry import AgentRegistry, AgentInfo, AgentStatus, AgentType, Capability, get_agent_registry
from .workflow_engine import WorkflowEngine, Workflow, WorkflowStatus, get_workflow_engine
from .context_manager import ContextManager, WorkflowContext, get_context_manager
from .event_bus import EventBus, Event, EventType, get_event_bus

logger = get_logger(__name__)


class OrchestrationStatus(Enum):
    """Status of the orchestrator"""
    INITIALIZING = "initializing"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPING = "stopping"
    STOPPED = "stopped"
    DEGRADED = "degraded"


class TaskPriority(Enum):
    """Priority levels for tasks"""
    CRITICAL = 0
    HIGH = 1
    NORMAL = 2
    LOW = 3
    BACKGROUND = 4


@dataclass
class OrchestrationConfig:
    """Configuration for the orchestrator"""
    max_concurrent_workflows: int = 10
    max_concurrent_tasks: int = 50
    task_timeout_seconds: int = 300
    retry_attempts: int = 3
    retry_delay_seconds: int = 5
    enable_state_persistence: bool = True
    enable_event_bus: bool = True
    health_check_interval: int = 30
    metrics_collection_enabled: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "max_concurrent_workflows": self.max_concurrent_workflows,
            "max_concurrent_tasks": self.max_concurrent_tasks,
            "task_timeout_seconds": self.task_timeout_seconds,
            "retry_attempts": self.retry_attempts,
            "retry_delay_seconds": self.retry_delay_seconds,
            "enable_state_persistence": self.enable_state_persistence,
            "enable_event_bus": self.enable_event_bus,
            "health_check_interval": self.health_check_interval,
            "metrics_collection_enabled": self.metrics_collection_enabled
        }


@dataclass
class Task:
    """Represents a task to be executed by an agent"""
    task_id: str
    task_type: str
    payload: Dict[str, Any]
    priority: TaskPriority = TaskPriority.NORMAL
    timeout_seconds: int = 300
    retry_count: int = 0
    max_retries: int = 3
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    agent_id: Optional[str] = None
    workflow_id: Optional[str] = None
    status: str = "pending"  # pending, running, completed, failed, cancelled
    error_message: Optional[str] = None
    result: Optional[Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "task_type": self.task_type,
            "payload": self.payload,
            "priority": self.priority.value,
            "timeout_seconds": self.timeout_seconds,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "agent_id": self.agent_id,
            "workflow_id": self.workflow_id,
            "status": self.status,
            "error_message": self.error_message
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Task":
        return cls(
            task_id=data["task_id"],
            task_type=data["task_type"],
            payload=data.get("payload", {}),
            priority=TaskPriority(data.get("priority", TaskPriority.NORMAL.value)),
            timeout_seconds=data.get("timeout_seconds", 300),
            retry_count=data.get("retry_count", 0),
            max_retries=data.get("max_retries", 3),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.now(),
            started_at=datetime.fromisoformat(data["started_at"]) if data.get("started_at") else None,
            completed_at=datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None,
            agent_id=data.get("agent_id"),
            workflow_id=data.get("workflow_id"),
            status=data.get("status", "pending"),
            error_message=data.get("error_message")
        )


class BaseOrchestrator(ABC):
    """
    Base orchestrator for managing multi-agent workflows.
    
    This abstract class provides the core orchestration functionality that
    concrete orchestrators can extend and customize.
    """
    
    def __init__(self, name: str, config: OrchestrationConfig = None):
        """
        Initialize the base orchestrator.
        
        Args:
            name: Orchestrator instance name
            config: Orchestration configuration
        """
        self.name = name
        self.config = config or OrchestrationConfig()
        self.orchestrator_id = str(uuid.uuid4())
        self.status = OrchestrationStatus.INITIALIZING
        
        # Core components
        self.agent_registry: AgentRegistry = get_agent_registry()
        self.workflow_engine: WorkflowEngine = get_workflow_engine()
        self.context_manager: ContextManager = get_context_manager()
        self.event_bus: EventBus = get_event_bus() if self.config.enable_event_bus else None
        
        # Task management
        self.tasks: Dict[str, Task] = {}
        self.task_queue: List[Task] = []
        self.active_tasks: Dict[str, Task] = {}
        self.task_futures: Dict[str, Future] = {}
        
        # Workflow tracking
        self.active_workflows: Dict[str, WorkflowContext] = {}
        self.workflow_history: List[str] = []
        
        # Threading
        self._executor = ThreadPoolExecutor(max_workers=self.config.max_concurrent_tasks)
        self._scheduler_thread: Optional[threading.Thread] = None
        self._stop_scheduler = threading.Event()
        self._lock = threading.RLock()
        
        # Metrics
        self.metrics: Dict[str, Any] = {
            "tasks_submitted": 0,
            "tasks_completed": 0,
            "tasks_failed": 0,
            "workflows_started": 0,
            "workflows_completed": 0,
            "workflows_failed": 0
        }
        
        # Callbacks
        self._on_task_complete_callbacks: List[Callable] = []
        self._on_workflow_complete_callbacks: List[Callable] = []
        self._on_error_callbacks: List[Callable] = []
        
        # Load state
        self._load_state()
        
        # Register this orchestrator as an agent
        self._register_as_agent()
        
        # Setup event handlers
        self._setup_event_handlers()
        
        # Start scheduler
        self._start_scheduler()
        
        self.status = OrchestrationStatus.RUNNING
        logger.info(f"BaseOrchestrator '{name}' initialized with ID {self.orchestrator_id}")
    
    def _register_as_agent(self) -> None:
        """Register the orchestrator itself as an agent in the registry"""
        agent_info = self.agent_registry.create_agent_info(
            name=self.name,
            agent_type=AgentType.ORCHESTRATOR,
            capabilities=[
                Capability.WORKFLOW_EXECUTION,
                Capability.PLANNING,
                Capability.COORDINATOR
            ],
            version="1.0.0",
            max_concurrent_tasks=self.config.max_concurrent_tasks,
            metadata={
                "orchestrator_id": self.orchestrator_id,
                "config": self.config.to_dict()
            }
        )
        self.agent_registry.register_agent(agent_info)
        self.orchestrator_agent_id = agent_info.agent_id
    
    def _setup_event_handlers(self) -> None:
        """Setup event bus handlers"""
        if not self.event_bus:
            return
        
        # Subscribe to relevant events
        self.event_bus.subscribe(EventType.TASK_COMPLETED, self._handle_task_completed_event)
        self.event_bus.subscribe(EventType.TASK_FAILED, self._handle_task_failed_event)
        self.event_bus.subscribe(EventType.WORKFLOW_COMPLETED, self._handle_workflow_completed_event)
        self.event_bus.subscribe(EventType.WORKFLOW_FAILED, self._handle_workflow_failed_event)
        self.event_bus.subscribe(EventType.AGENT_STATUS_CHANGED, self._handle_agent_status_event)
    
    def _start_scheduler(self) -> None:
        """Start the background task scheduler"""
        def scheduler_loop():
            while not self._stop_scheduler.is_set():
                try:
                    self._process_task_queue()
                    self._check_stalled_tasks()
                    self._update_health()
                except Exception as e:
                    logger.error(f"Error in scheduler loop: {e}")
                self._stop_scheduler.wait(1)  # Check every second
        
        self._scheduler_thread = threading.Thread(target=scheduler_loop, daemon=True)
        self._scheduler_thread.start()
    
    def _process_task_queue(self) -> None:
        """Process pending tasks from the queue"""
        with self._lock:
            # Sort by priority (lower number = higher priority)
            self.task_queue.sort(key=lambda t: t.priority.value)
            
            # Process tasks up to max concurrent
            available_slots = self.config.max_concurrent_tasks - len(self.active_tasks)
            
            for task in self.task_queue[:available_slots]:
                if task.status == "pending":
                    self._submit_task(task)
                    self.task_queue.remove(task)
    
    def _submit_task(self, task: Task) -> None:
        """Submit a task for execution"""
        # Find suitable agent
        agent = self._select_agent_for_task(task)
        
        if not agent:
            logger.warning(f"No agent available for task {task.task_id} of type {task.task_type}")
            task.status = "pending"
            return
        
        # Assign task to agent
        if self.agent_registry.assign_task_to_agent(task.task_id, agent.agent_id):
            task.agent_id = agent.agent_id
            task.started_at = datetime.now()
            task.status = "running"
            self.active_tasks[task.task_id] = task
            
            # Submit for execution
            future = self._executor.submit(self._execute_task, task)
            self.task_futures[task.task_id] = future
            
            # Update agent status
            self.agent_registry.update_agent_heartbeat(
                agent.agent_id,
                status=AgentStatus.BUSY if agent.active_tasks >= agent.max_concurrent_tasks else AgentStatus.ACTIVE,
                current_task_id=task.task_id
            )
            
            logger.debug(f"Submitted task {task.task_id} to agent {agent.name}")
    
    def _select_agent_for_task(self, task: Task) -> Optional[AgentInfo]:
        """Select the best agent for a task"""
        # Map task type to required capability
        capability_map = {
            "code_analysis": Capability.CODE_ANALYSIS,
            "code_generation": Capability.CODE_GENERATION,
            "test_generation": Capability.TEST_GENERATION,
            "documentation": Capability.DOCUMENTATION,
            "code_review": Capability.CODE_REVIEW,
            "refactoring": Capability.REFACTORING,
            "debugging": Capability.DEBUGGING,
            "validation": Capability.VALIDATION,
            "planning": Capability.PLANNING,
        }
        
        capability = capability_map.get(task.task_type, Capability.WORKFLOW_EXECUTION)
        
        return self.agent_registry.select_agent_for_task(capability)
    
    def _execute_task(self, task: Task) -> Any:
        """
        Execute a task. Override this method in concrete orchestrators.
        
        Args:
            task: Task to execute
            
        Returns:
            Task result
        """
        # This should be overridden by concrete orchestrators
        # Default implementation just returns None
        logger.warning(f"Task execution not implemented for task type: {task.task_type}")
        return None
    
    def _complete_task(self, task_id: str, result: Any = None, error: Exception = None) -> None:
        """Mark a task as completed"""
        with self._lock:
            if task_id not in self.active_tasks:
                return
            
            task = self.active_tasks[task_id]
            task.completed_at = datetime.now()
            
            if error:
                task.status = "failed"
                task.error_message = str(error)
                self.metrics["tasks_failed"] += 1
                
                # Handle retry
                if task.retry_count < task.max_retries:
                    task.retry_count += 1
                    task.status = "pending"
                    task.started_at = None
                    task.agent_id = None
                    self.task_queue.append(task)
                    logger.info(f"Retrying task {task_id} (attempt {task.retry_count}/{task.max_retries})")
                else:
                    self._notify_task_failed(task, error)
            else:
                task.status = "completed"
                task.result = result
                self.metrics["tasks_completed"] += 1
                self._notify_task_complete(task, result)
            
            # Clean up
            del self.active_tasks[task_id]
            if task_id in self.task_futures:
                del self.task_futures[task_id]
            
            # Update agent
            if task.agent_id:
                self.agent_registry.update_task_status(
                    task.agent_id, task_id, completed=(error is None),
                    duration=(task.completed_at - task.started_at).total_seconds() if task.started_at else None
                )
            
            # Emit event
            if self.event_bus:
                event_type = EventType.TASK_COMPLETED if not error else EventType.TASK_FAILED
                self.event_bus.emit(Event(
                    type=event_type,
                    source=self.orchestrator_id,
                    data={
                        "task_id": task_id,
                        "task_type": task.task_type,
                        "result": result,
                        "error": str(error) if error else None,
                        "duration": (task.completed_at - task.started_at).total_seconds() if task.started_at else 0
                    }
                ))
    
    def submit_task(self, task_type: str, payload: Dict[str, Any],
                   priority: TaskPriority = TaskPriority.NORMAL,
                   workflow_id: str = None,
                   max_retries: int = 3) -> str:
        """
        Submit a task for execution.
        
        Args:
            task_type: Type of task to execute
            payload: Task payload data
            priority: Task priority
            workflow_id: Associated workflow ID (optional)
            max_retries: Maximum retry attempts
            
        Returns:
            Task ID
        """
        task_id = str(uuid.uuid4())
        
        task = Task(
            task_id=task_id,
            task_type=task_type,
            payload=payload,
            priority=priority,
            max_retries=max_retries,
            workflow_id=workflow_id
        )
        
        with self._lock:
            self.tasks[task_id] = task
            self.task_queue.append(task)
            self.metrics["tasks_submitted"] += 1
        
        # Emit event
        if self.event_bus:
            self.event_bus.emit(Event(
                type=EventType.TASK_SUBMITTED,
                source=self.orchestrator_id,
                data={"task_id": task_id, "task_type": task_type}
            ))
        
        logger.debug(f"Submitted task {task_id} of type {task_type}")
        
        return task_id
    
    def start_workflow(self, workflow: Workflow, context_data: Dict[str, Any] = None) -> str:
        """
        Start a workflow execution.
        
        Args:
            workflow: Workflow to execute
            context_data: Initial context data
            
        Returns:
            Workflow execution ID
        """
        # Create workflow context
        context = self.context_manager.create_context(
            workflow_id=workflow.workflow_id,
            initial_data=context_data or {}
        )
        
        # Register with workflow engine
        self.workflow_engine.register_workflow(workflow)
        
        # Start execution
        execution_id = self.workflow_engine.start_workflow(workflow.workflow_id, context.context_id)
        
        with self._lock:
            self.active_workflows[execution_id] = context
            self.metrics["workflows_started"] += 1
        
        # Submit initial tasks based on workflow
        self._schedule_workflow_tasks(workflow, context)
        
        # Emit event
        if self.event_bus:
            self.event_bus.emit(Event(
                type=EventType.WORKFLOW_STARTED,
                source=self.orchestrator_id,
                data={"workflow_id": workflow.workflow_id, "execution_id": execution_id}
            ))
        
        logger.info(f"Started workflow {workflow.workflow_id} with execution ID {execution_id}")
        
        return execution_id
    
    def _schedule_workflow_tasks(self, workflow: Workflow, context: WorkflowContext) -> None:
        """
        Schedule tasks for a workflow.
        
        Args:
            workflow: Workflow definition
            context: Workflow context
        """
        # Get initial tasks (those with no dependencies)
        initial_tasks = self.workflow_engine.get_ready_tasks(workflow.workflow_id, context.context_id)
        
        for task_def in initial_tasks:
            self.submit_task(
                task_type=task_def.get("type", "unknown"),
                payload={
                    "task_definition": task_def,
                    "workflow_context": context.data
                },
                workflow_id=workflow.workflow_id
            )
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get the status of a task"""
        with self._lock:
            task = self.tasks.get(task_id)
            if not task:
                return None
            
            result = task.to_dict()
            if task_id in self.task_futures:
                result["future_done"] = self.task_futures[task_id].done()
            
            return result
    
    def get_workflow_status(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get the status of a workflow execution"""
        return self.workflow_engine.get_workflow_status(execution_id)
    
    def cancel_task(self, task_id: str) -> bool:
        """Cancel a pending or running task"""
        with self._lock:
            task = self.tasks.get(task_id)
            if not task:
                return False
            
            if task.status == "pending":
                # Remove from queue
                if task in self.task_queue:
                    self.task_queue.remove(task)
                task.status = "cancelled"
                return True
            
            elif task.status == "running":
                # Try to cancel future
                if task_id in self.task_futures:
                    cancelled = self.task_futures[task_id].cancel()
                    if cancelled:
                        task.status = "cancelled"
                        self._complete_task(task_id, error=Exception("Task cancelled"))
                        return True
            
            return False
    
    def cancel_workflow(self, execution_id: str) -> bool:
        """Cancel a workflow execution"""
        result = self.workflow_engine.cancel_workflow(execution_id)
        
        if result:
            # Cancel all associated tasks
            with self._lock:
                for task in self.tasks.values():
                    if task.workflow_id == execution_id and task.status in ["pending", "running"]:
                        self.cancel_task(task.task_id)
        
        return result
    
    def _check_stalled_tasks(self) -> None:
        """Check for tasks that have timed out"""
        now = datetime.now()
        
        with self._lock:
            for task_id, task in list(self.active_tasks.items()):
                if task.started_at:
                    elapsed = (now - task.started_at).total_seconds()
                    if elapsed > task.timeout_seconds:
                        logger.warning(f"Task {task_id} timed out after {elapsed:.2f} seconds")
                        self._complete_task(task_id, error=TimeoutError(f"Task timed out after {task.timeout_seconds}s"))
    
    def _update_health(self) -> None:
        """Update orchestrator health status"""
        # Update agent heartbeat
        self.agent_registry.update_agent_heartbeat(
            self.orchestrator_agent_id,
            status=AgentStatus.ACTIVE if self.status == OrchestrationStatus.RUNNING else AgentStatus.DEGRADED,
            metrics={
                "active_tasks": len(self.active_tasks),
                "queued_tasks": len(self.task_queue),
                "active_workflows": len(self.active_workflows)
            }
        )
        
        # Check if degraded
        if len(self.active_tasks) >= self.config.max_concurrent_tasks * 0.9:
            if self.status == OrchestrationStatus.RUNNING:
                self.status = OrchestrationStatus.DEGRADED
                logger.warning("Orchestrator entered DEGRADED state due to high load")
        elif self.status == OrchestrationStatus.DEGRADED and len(self.active_tasks) < self.config.max_concurrent_tasks * 0.7:
            self.status = OrchestrationStatus.RUNNING
            logger.info("Orchestrator returned to RUNNING state")
    
    def _handle_task_completed_event(self, event: Event) -> None:
        """Handle task completed event"""
        task_id = event.data.get("task_id")
        if task_id:
            # Update workflow if needed
            task = self.tasks.get(task_id)
            if task and task.workflow_id:
                self.workflow_engine.update_task_status(
                    task.workflow_id, task_id, "completed", event.data.get("result")
                )
    
    def _handle_task_failed_event(self, event: Event) -> None:
        """Handle task failed event"""
        task_id = event.data.get("task_id")
        if task_id:
            task = self.tasks.get(task_id)
            if task and task.workflow_id:
                self.workflow_engine.update_task_status(
                    task.workflow_id, task_id, "failed", error=event.data.get("error")
                )
    
    def _handle_workflow_completed_event(self, event: Event) -> None:
        """Handle workflow completed event"""
        execution_id = event.data.get("execution_id")
        with self._lock:
            if execution_id in self.active_workflows:
                del self.active_workflows[execution_id]
                self.metrics["workflows_completed"] += 1
                self.workflow_history.append(execution_id)
        
        self._notify_workflow_complete(execution_id, event.data)
    
    def _handle_workflow_failed_event(self, event: Event) -> None:
        """Handle workflow failed event"""
        execution_id = event.data.get("execution_id")
        with self._lock:
            if execution_id in self.active_workflows:
                del self.active_workflows[execution_id]
                self.metrics["workflows_failed"] += 1
        
        self._notify_workflow_failed(execution_id, event.data.get("error"))
    
    def _handle_agent_status_event(self, event: Event) -> None:
        """Handle agent status change event"""
        agent_id = event.data.get("agent_id")
        new_status = event.data.get("new_status")
        
        if new_status == AgentStatus.OFFLINE.value:
            # Handle agent failure - reassign its tasks
            self._reassign_agent_tasks(agent_id)
    
    def _reassign_agent_tasks(self, agent_id: str) -> None:
        """Reassign tasks from a failed agent"""
        with self._lock:
            for task_id, task in list(self.active_tasks.items()):
                if task.agent_id == agent_id:
                    logger.info(f"Reassigning task {task_id} from failed agent {agent_id}")
                    # Reset task for reassignment
                    task.status = "pending"
                    task.started_at = None
                    task.agent_id = None
                    del self.active_tasks[task_id]
                    self.task_queue.append(task)
    
    def _load_state(self) -> None:
        """Load persisted state"""
        if not self.config.enable_state_persistence:
            return
        
        try:
            saved_state = state_manager.get(f"orchestrator.{self.name}", {})
            if saved_state:
                # Restore tasks
                tasks_data = saved_state.get("tasks", {})
                for task_id, task_data in tasks_data.items():
                    self.tasks[task_id] = Task.from_dict(task_data)
                    if task_data.get("status") == "pending":
                        self.task_queue.append(self.tasks[task_id])
                
                # Restore metrics
                self.metrics = saved_state.get("metrics", self.metrics)
                
                logger.info(f"Loaded state for orchestrator '{self.name}'")
        except Exception as e:
            logger.warning(f"Failed to load state: {e}")
    
    def _save_state(self) -> None:
        """Save current state"""
        if not self.config.enable_state_persistence:
            return
        
        try:
            state = {
                "tasks": {tid: task.to_dict() for tid, task in self.tasks.items()},
                "metrics": self.metrics,
                "timestamp": datetime.now().isoformat()
            }
            state_manager.set(f"orchestrator.{self.name}", state)
        except Exception as e:
            logger.error(f"Failed to save state: {e}")
    
    def on_task_complete(self, callback: Callable) -> None:
        """Register callback for task completion"""
        self._on_task_complete_callbacks.append(callback)
    
    def on_workflow_complete(self, callback: Callable) -> None:
        """Register callback for workflow completion"""
        self._on_workflow_complete_callbacks.append(callback)
    
    def on_error(self, callback: Callable) -> None:
        """Register callback for errors"""
        self._on_error_callbacks.append(callback)
    
    def _notify_task_complete(self, task: Task, result: Any) -> None:
        """Notify task completion callbacks"""
        for callback in self._on_task_complete_callbacks:
            try:
                callback(task, result)
            except Exception as e:
                logger.error(f"Error in task complete callback: {e}")
    
    def _notify_task_failed(self, task: Task, error: Exception) -> None:
        """Notify task failure callbacks"""
        for callback in self._on_error_callbacks:
            try:
                callback(task, error)
            except Exception as e:
                logger.error(f"Error in error callback: {e}")
    
    def _notify_workflow_complete(self, execution_id: str, data: Dict[str, Any]) -> None:
        """Notify workflow completion callbacks"""
        for callback in self._on_workflow_complete_callbacks:
            try:
                callback(execution_id, data)
            except Exception as e:
                logger.error(f"Error in workflow complete callback: {e}")
    
    def _notify_workflow_failed(self, execution_id: str, error: str) -> None:
        """Notify workflow failure callbacks"""
        for callback in self._on_error_callbacks:
            try:
                callback(execution_id, error)
            except Exception as e:
                logger.error(f"Error in error callback: {e}")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get orchestrator metrics"""
        with self._lock:
            return {
                **self.metrics,
                "active_tasks": len(self.active_tasks),
                "queued_tasks": len(self.task_queue),
                "active_workflows": len(self.active_workflows),
                "status": self.status.value,
                "total_tasks": len(self.tasks),
                "orchestrator_id": self.orchestrator_id
            }
    
    def pause(self) -> None:
        """Pause the orchestrator"""
        self.status = OrchestrationStatus.PAUSED
        logger.info(f"Orchestrator '{self.name}' paused")
    
    def resume(self) -> None:
        """Resume the orchestrator"""
        self.status = OrchestrationStatus.RUNNING
        logger.info(f"Orchestrator '{self.name}' resumed")
    
    def stop(self) -> None:
        """Stop the orchestrator"""
        self.status = OrchestrationStatus.STOPPING
        self._stop_scheduler.set()
        
        if self._scheduler_thread:
            self._scheduler_thread.join(timeout=5)
        
        self._executor.shutdown(wait=True)
        
        # Deregister from agent registry
        self.agent_registry.deregister_agent(self.orchestrator_agent_id)
        
        # Save final state
        self._save_state()
        
        self.status = OrchestrationStatus.STOPPED
        logger.info(f"Orchestrator '{self.name}' stopped")
    
    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """
        Get the capabilities of this orchestrator.
        
        Returns:
            List of capability strings
        """
        pass
    
    @abstractmethod
    def handle_custom_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """
        Handle custom events. Override in concrete orchestrators.
        
        Args:
            event_type: Type of event
            data: Event data
        """
        pass