"""
Task Scheduler

Manages scheduled tasks, timer events, and job execution.
Supports one-time and recurring schedules with cron-like expressions.
"""

from __future__ import annotations

import asyncio
import heapq
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging
from typing import Any, Callable, Set
from uuid import uuid4

from ..persistence.history_repository import HistoryRepository
from ..persistence.token_repository import TokenRepository


logger = logging.getLogger(__name__)


class ScheduleType(Enum):
    """Schedule types"""
    ONE_TIME = "one_time"  # Execute once at specific time
    RECURRING = "recurring"  # Execute repeatedly
    INTERVAL = "interval"  # Execute at fixed intervals
    CRON = "cron"  # Execute based on cron expression


class TaskState(Enum):
    """Scheduled task states"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ScheduledTask:
    """Scheduled task"""
    task_id: str
    name: str
    schedule_type: ScheduleType
    handler: Callable
    next_execution: datetime
    schedule_data: dict[str, Any] = field(default_factory=dict)
    state: TaskState = TaskState.PENDING
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_execution: datetime | None = None
    execution_count: int = 0
    failure_count: int = 0
    max_retries: int = 3
    retry_delay_seconds: int = 60
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def __lt__(self, other):
        """For heap ordering"""
        return self.next_execution < other.next_execution

    def to_record_payload(self) -> dict[str, Any]:
        return {
            "job_id": self.task_id,
            "job_type": self.schedule_type.value,
            "state": self.state.value,
            "updated_at": (self.last_execution or self.created_at).isoformat(),
            "payload": {
                "name": self.name,
                "next_execution": self.next_execution.isoformat(),
                "schedule_data": dict(self.schedule_data),
                "created_at": self.created_at.isoformat(),
                "last_execution": self.last_execution.isoformat() if self.last_execution else None,
                "execution_count": self.execution_count,
                "failure_count": self.failure_count,
                "max_retries": self.max_retries,
                "retry_delay_seconds": self.retry_delay_seconds,
                "metadata": dict(self.metadata),
            },
        }


class Scheduler:
    """
    Task scheduler for timer events and jobs.
    
    Features:
    - One-time and recurring schedules
    - Cron-like expressions
    - Retry logic with exponential backoff
    - Task prioritization
    - Concurrent execution control
    """
    
    def __init__(
        self,
        max_concurrent_tasks: int = 100,
        *,
        history_repository: HistoryRepository | None = None,
        token_repository: TokenRepository | None = None,
    ):
        self.max_concurrent_tasks = max_concurrent_tasks
        
        # Task storage
        self.tasks: dict[str, ScheduledTask] = {}
        self.task_heap: list[ScheduledTask] = []  # Min heap by next_execution
        
        # Execution tracking
        self.running_tasks: Set[str] = set()
        
        # State
        self.is_running = False
        self.is_paused = False
        self._scheduler_task: asyncio.Task | None = None
        
        # Statistics
        self.total_executed = 0
        self.total_failed = 0
        self.history_repository = history_repository
        self.token_repository = token_repository
        
        logger.info("Scheduler created")
    
    async def start(self) -> None:
        """Start the scheduler"""
        if self.is_running:
            return
        
        self.is_running = True
        self.is_paused = False
        self._scheduler_task = asyncio.create_task(self._scheduler_loop())
        logger.info("Scheduler started")
    
    async def stop(self) -> None:
        """Stop the scheduler"""
        if not self.is_running:
            return
        
        self.is_running = False
        
        if self._scheduler_task:
            self._scheduler_task.cancel()
            try:
                await self._scheduler_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Scheduler stopped")
    
    async def pause(self) -> None:
        """Pause the scheduler"""
        self.is_paused = True
        logger.info("Scheduler paused")
    
    async def resume(self) -> None:
        """Resume the scheduler"""
        self.is_paused = False
        logger.info("Scheduler resumed")
    
    def schedule_once(
        self,
        name: str,
        handler: Callable,
        execute_at: datetime,
        task_id: str | None = None,
        metadata: dict[str, Any] | None = None
    ) -> str:
        """
        Schedule a one-time task.
        
        Args:
            name: Task name
            handler: Task handler function
            execute_at: When to execute
            task_id: Optional task ID
            metadata: Optional metadata
        
        Returns:
            Task ID
        """
        if task_id is None:
            task_id = str(uuid4())
        
        task = ScheduledTask(
            task_id=task_id,
            name=name,
            schedule_type=ScheduleType.ONE_TIME,
            handler=handler,
            next_execution=execute_at,
            metadata=metadata or {}
        )
        
        self._add_task(task)
        logger.info(f"Scheduled one-time task '{name}' at {execute_at}")
        return task_id
    
    def schedule_interval(
        self,
        name: str,
        handler: Callable,
        interval_seconds: int,
        start_at: datetime | None = None,
        task_id: str | None = None,
        metadata: dict[str, Any] | None = None
    ) -> str:
        """
        Schedule a recurring task with fixed interval.
        
        Args:
            name: Task name
            handler: Task handler function
            interval_seconds: Interval between executions
            start_at: When to start (default: now)
            task_id: Optional task ID
            metadata: Optional metadata
        
        Returns:
            Task ID
        """
        if task_id is None:
            task_id = str(uuid4())
        
        if start_at is None:
            start_at = datetime.utcnow()
        
        task = ScheduledTask(
            task_id=task_id,
            name=name,
            schedule_type=ScheduleType.INTERVAL,
            handler=handler,
            next_execution=start_at,
            schedule_data={"interval_seconds": interval_seconds},
            metadata=metadata or {}
        )
        
        self._add_task(task)
        logger.info(f"Scheduled interval task '{name}' every {interval_seconds}s")
        return task_id
    
    def schedule_cron(
        self,
        name: str,
        handler: Callable,
        cron_expression: str,
        task_id: str | None = None,
        metadata: dict[str, Any] | None = None
    ) -> str:
        """
        Schedule a task with cron expression.
        
        Args:
            name: Task name
            handler: Task handler function
            cron_expression: Cron expression (e.g., "0 0 * * *")
            task_id: Optional task ID
            metadata: Optional metadata
        
        Returns:
            Task ID
        """
        if task_id is None:
            task_id = str(uuid4())
        
        # Calculate next execution from cron
        next_exec = self._calculate_next_cron_execution(cron_expression)
        
        task = ScheduledTask(
            task_id=task_id,
            name=name,
            schedule_type=ScheduleType.CRON,
            handler=handler,
            next_execution=next_exec,
            schedule_data={"cron_expression": cron_expression},
            metadata=metadata or {}
        )
        
        self._add_task(task)
        logger.info(f"Scheduled cron task '{name}' with expression '{cron_expression}'")
        return task_id
    
    def cancel_task(self, task_id: str) -> bool:
        """Cancel a scheduled task"""
        task = self.tasks.get(task_id)
        if not task:
            return False
        
        task.state = TaskState.CANCELLED
        logger.info(f"Cancelled task {task_id}")
        return True
    
    def get_task(self, task_id: str) -> ScheduledTask | None:
        """Get a scheduled task"""
        return self.tasks.get(task_id)
    
    def _add_task(self, task: ScheduledTask) -> None:
        """Add a task to the scheduler"""
        self.tasks[task.task_id] = task
        heapq.heappush(self.task_heap, task)

    async def _persist_task_state(self, task: ScheduledTask, action: str) -> None:
        if self.history_repository is None:
            return
        await self.history_repository.append_persisted(
            str(task.metadata.get("instance_id", "scheduler")),
            {
                "action": action,
                "activity_id": task.metadata.get("activity_id"),
                "payload": task.to_record_payload(),
                "created_at": datetime.utcnow().isoformat(),
            },
        )

    async def reload_tasks_from_history(self, instance_id: str) -> list[ScheduledTask]:
        if self.history_repository is None:
            return list(self.tasks.values())
        history_rows = self.history_repository.query(instance_id)
        restored: list[ScheduledTask] = []
        seen: set[str] = set()
        for row in history_rows:
            payload = row.get("payload")
            if not isinstance(payload, dict):
                continue
            job_payload = payload.get("payload")
            if not isinstance(job_payload, dict):
                continue
            task_id = str(payload.get("job_id", ""))
            if not task_id or task_id in seen:
                continue
            seen.add(task_id)
            task = ScheduledTask(
                task_id=task_id,
                name=str(job_payload.get("name", task_id)),
                schedule_type=ScheduleType(str(payload.get("job_type", ScheduleType.ONE_TIME.value))),
                handler=lambda _task: None,
                next_execution=datetime.fromisoformat(str(job_payload.get("next_execution", datetime.utcnow().isoformat()))),
                schedule_data=dict(job_payload.get("schedule_data") or {}),
                state=TaskState(str(payload.get("state", TaskState.PENDING.value))),
                metadata=dict(job_payload.get("metadata") or {}),
            )
            task.created_at = datetime.fromisoformat(str(job_payload.get("created_at", datetime.utcnow().isoformat())))
            last_execution = job_payload.get("last_execution")
            if last_execution:
                task.last_execution = datetime.fromisoformat(str(last_execution))
            task.execution_count = int(job_payload.get("execution_count", 0))
            task.failure_count = int(job_payload.get("failure_count", 0))
            task.max_retries = int(job_payload.get("max_retries", 3))
            task.retry_delay_seconds = int(job_payload.get("retry_delay_seconds", 60))
            self.tasks[task.task_id] = task
            if task.state in {TaskState.PENDING, TaskState.RUNNING}:
                heapq.heappush(self.task_heap, task)
            restored.append(task)
        return restored
    
    async def _scheduler_loop(self) -> None:
        """Main scheduler loop"""
        logger.info("Scheduler loop started")
        
        while self.is_running:
            try:
                if not self.is_paused:
                    await self.process_due_jobs()
                
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}", exc_info=True)
        
        logger.info("Scheduler loop stopped")
    
    async def process_due_jobs(self) -> int:
        """Process all due jobs"""
        now = datetime.utcnow()
        processed = 0
        
        while self.task_heap and self.task_heap[0].next_execution <= now:
            # Check concurrent task limit
            if len(self.running_tasks) >= self.max_concurrent_tasks:
                break
            
            task = heapq.heappop(self.task_heap)
            
            # Skip cancelled tasks
            if task.state == TaskState.CANCELLED:
                continue
            
            # Execute task
            asyncio.create_task(self._execute_task(task))
            processed += 1
        
        return processed
    
    async def _execute_task(self, task: ScheduledTask) -> None:
        """Execute a scheduled task"""
        task.state = TaskState.RUNNING
        task.last_execution = datetime.utcnow()
        self.running_tasks.add(task.task_id)
        await self._persist_task_state(task, "job.running")
        
        try:
            # Execute handler
            if asyncio.iscoroutinefunction(task.handler):
                await task.handler(task)
            else:
                task.handler(task)
            
            task.execution_count += 1
            task.state = TaskState.COMPLETED
            self.total_executed += 1
            await self._persist_task_state(task, "job.completed")
            
            logger.debug(f"Executed task {task.task_id} ({task.name})")
            
            # Reschedule if recurring
            if task.schedule_type in (ScheduleType.INTERVAL, ScheduleType.CRON, ScheduleType.RECURRING):
                self._reschedule_task(task)
            
        except Exception as e:
            task.failure_count += 1
            task.state = TaskState.FAILED
            self.total_failed += 1
            await self._persist_task_state(task, "job.failed")
            
            logger.error(f"Task {task.task_id} failed: {e}", exc_info=True)
            
            # Retry if under limit
            if task.failure_count < task.max_retries:
                self._schedule_retry(task)
        
        finally:
            self.running_tasks.discard(task.task_id)
    
    def _reschedule_task(self, task: ScheduledTask) -> None:
        """Reschedule a recurring task"""
        if task.schedule_type == ScheduleType.INTERVAL:
            interval = task.schedule_data.get("interval_seconds", 60)
            task.next_execution = datetime.utcnow() + timedelta(seconds=interval)
        
        elif task.schedule_type == ScheduleType.CRON:
            cron_expr = task.schedule_data.get("cron_expression", "")
            task.next_execution = self._calculate_next_cron_execution(cron_expr)
        
        task.state = TaskState.PENDING
        heapq.heappush(self.task_heap, task)
    
    def _schedule_retry(self, task: ScheduledTask) -> None:
        """Schedule a task retry"""
        delay = task.retry_delay_seconds * (2 ** (task.failure_count - 1))  # Exponential backoff
        task.next_execution = datetime.utcnow() + timedelta(seconds=delay)
        task.state = TaskState.PENDING
        heapq.heappush(self.task_heap, task)
        
        logger.info(f"Scheduled retry for task {task.task_id} in {delay}s")
    
    def _calculate_next_cron_execution(self, cron_expression: str) -> datetime:
        """Calculate next execution time from cron expression"""
        # Simplified cron parsing - in production, use croniter library
        # For now, just schedule 1 hour from now
        return datetime.utcnow() + timedelta(hours=1)
    
    def get_pending_tasks(self) -> list[ScheduledTask]:
        """Get all pending tasks"""
        return [t for t in self.tasks.values() if t.state == TaskState.PENDING]
    
    def get_running_tasks(self) -> list[ScheduledTask]:
        """Get all running tasks"""
        return [t for t in self.tasks.values() if t.state == TaskState.RUNNING]
    
    def get_statistics(self) -> dict[str, Any]:
        """Get scheduler statistics"""
        state_counts: dict[str, int] = {}
        for task in self.tasks.values():
            state = task.state.value
            state_counts[state] = state_counts.get(state, 0) + 1
        
        return {
            "total_tasks": len(self.tasks),
            "running_tasks": len(self.running_tasks),
            "pending_tasks": len([t for t in self.tasks.values() if t.state == TaskState.PENDING]),
            "total_executed": self.total_executed,
            "total_failed": self.total_failed,
            "state_distribution": state_counts,
            "is_paused": self.is_paused
        }
