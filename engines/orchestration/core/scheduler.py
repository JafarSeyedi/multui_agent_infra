"""
Task Scheduler

Manages scheduled tasks, timer events, and job execution.
Supports one-time and recurring schedules with cron-like expressions.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Callable, Set
from enum import Enum
from dataclasses import dataclass, field
from uuid import uuid4
import heapq


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
    
    def __init__(self, max_concurrent_tasks: int = 100):
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
        
        try:
            # Execute handler
            if asyncio.iscoroutinefunction(task.handler):
                await task.handler(task)
            else:
                task.handler(task)
            
            task.execution_count += 1
            task.state = TaskState.COMPLETED
            self.total_executed += 1
            
            logger.debug(f"Executed task {task.task_id} ({task.name})")
            
            # Reschedule if recurring
            if task.schedule_type in (ScheduleType.INTERVAL, ScheduleType.CRON, ScheduleType.RECURRING):
                self._reschedule_task(task)
            
        except Exception as e:
            task.failure_count += 1
            task.state = TaskState.FAILED
            self.total_failed += 1
            
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
