"""External task pattern for orchestration runtime.

Implements the external task pattern per Camunda/Flowable:
- External task registration
- Worker polling and locking
- Task completion/failure handling
- Timeout and retry management
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable
from uuid import uuid4


logger = logging.getLogger(__name__)


class ExternalTaskState(str, Enum):
    PENDING = "pending"
    LOCKED = "locked"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMED_OUT = "timed_out"
    CANCELLED = "cancelled"


from enum import Enum


@dataclass
class ExternalTask:
    task_id: str = ""
    topic_name: str = ""
    instance_id: str = ""
    activity_id: str = ""
    worker_id: str | None = None
    lock_expiration: str | None = None
    priority: int = 0
    retries: int = 3
    error_message: str = ""
    error_details: str = ""
    state: str = ExternalTaskState.PENDING
    create_time: str = ""
    last_failure_time: str | None = None
    variables: dict[str, Any] = field(default_factory=dict)
    lock_duration_ms: int = 60000

    def __post_init__(self) -> None:
        if not self.create_time:
            self.create_time = datetime.utcnow().isoformat()
        if not self.task_id:
            self.task_id = str(uuid4())


@dataclass
class ExternalTaskQuery:
    topic_name: str | None = None
    worker_id: str | None = None
    instance_id: str | None = None
    state: str | None = None
    priority_min: int | None = None
    created_after: str | None = None
    limit: int = 100
    offset: int = 0


@dataclass
class FetchAndLockRequest:
    worker_id: str = ""
    max_tasks: int = 10
    topics: list[str] = field(default_factory=list)
    lock_duration_ms: int = 60000
    priority_enabled: bool = False


class ExternalTaskWorker:
    def __init__(
        self,
        worker_id: str,
        task_manager: ExternalTaskManager,
        handler: Callable[..., Any],
        topics: list[str] | None = None,
        max_tasks: int = 10,
        lock_duration_ms: int = 60000,
        poll_interval_seconds: float = 5.0,
    ) -> None:
        self._worker_id = worker_id
        self._task_manager = task_manager
        self._handler = handler
        self._topics = topics or []
        self._max_tasks = max_tasks
        self._lock_duration_ms = lock_duration_ms
        self._poll_interval = poll_interval_seconds
        self._running = False
        self._poll_task: asyncio.Task | None = None

    async def start(self) -> None:
        self._running = True
        self._poll_task = asyncio.create_task(self._poll_loop())
        logger.info("External task worker '%s' started (topics=%s)", self._worker_id, self._topics)

    async def stop(self) -> None:
        self._running = False
        if self._poll_task:
            self._poll_task.cancel()
            try:
                await self._poll_task
            except asyncio.CancelledError:
                pass
        logger.info("External task worker '%s' stopped", self._worker_id)

    async def _poll_loop(self) -> None:
        while self._running:
            try:
                tasks = await self._task_manager.fetch_and_lock(FetchAndLockRequest(
                    worker_id=self._worker_id,
                    max_tasks=self._max_tasks,
                    topics=self._topics,
                    lock_duration_ms=self._lock_duration_ms,
                    priority_enabled=True,
                ))
                for task in tasks:
                    asyncio.create_task(self._process_task(task))
            except asyncio.CancelledError:
                break
            except Exception:
                logger.exception("Worker '%s' poll error", self._worker_id)
            await asyncio.sleep(self._poll_interval)

    async def _process_task(self, task: ExternalTask) -> None:
        try:
            result = await self._handler(task)
            await self._task_manager.complete(task.task_id, self._worker_id, result or {})
        except Exception as e:
            logger.exception("External task %s failed", task.task_id)
            await self._task_manager.fail(
                task.task_id, self._worker_id,
                error_message=str(e), retries=task.retries,
            )


class ExternalTaskManager:
    def __init__(self) -> None:
        self._tasks: dict[str, ExternalTask] = {}
        self._instance_tasks: dict[str, list[str]] = {}
        self._topic_queues: dict[str, list[str]] = {}

    async def create_task(
        self,
        topic_name: str,
        instance_id: str,
        activity_id: str,
        variables: dict[str, Any] | None = None,
        priority: int = 0,
        retries: int = 3,
    ) -> ExternalTask:
        task = ExternalTask(
            task_id=str(uuid4()),
            topic_name=topic_name,
            instance_id=instance_id,
            activity_id=activity_id,
            priority=priority,
            retries=retries,
            variables=variables or {},
        )
        self._tasks[task.task_id] = task
        if instance_id not in self._instance_tasks:
            self._instance_tasks[instance_id] = []
        self._instance_tasks[instance_id].append(task.task_id)
        if topic_name not in self._topic_queues:
            self._topic_queues[topic_name] = []
        self._topic_queues[topic_name].append(task.task_id)
        logger.debug("External task created: %s (topic=%s, instance=%s)",
                      task.task_id[:8], topic_name, instance_id)
        return task

    async def fetch_and_lock(self, request: FetchAndLockRequest) -> list[ExternalTask]:
        now = datetime.utcnow()
        locked: list[ExternalTask] = []

        topics = request.topics or list(self._topic_queues.keys())
        for topic in topics:
            queue = self._topic_queues.get(topic, [])
            for task_id in queue:
                if len(locked) >= request.max_tasks:
                    break
                task = self._tasks.get(task_id)
                if task is None:
                    continue
                if task.state == ExternalTaskState.LOCKED:
                    if task.lock_expiration:
                        try:
                            exp = datetime.fromisoformat(task.lock_expiration)
                            if exp > now:
                                continue
                        except ValueError:
                            pass
                    else:
                        continue
                if task.state not in (ExternalTaskState.PENDING, ExternalTaskState.FAILED):
                    continue
                lock_exp = datetime.utcnow().isoformat()
                task.state = ExternalTaskState.LOCKED
                task.worker_id = request.worker_id
                task.lock_expiration = lock_exp
                locked.append(task)

        return locked

    async def complete(
        self,
        task_id: str,
        worker_id: str,
        variables: dict[str, Any] | None = None,
    ) -> ExternalTask | None:
        task = self._tasks.get(task_id)
        if task is None:
            return None
        if task.worker_id != worker_id:
            raise ValueError(f"Task {task_id[:8]} is locked by {task.worker_id}, not {worker_id}")
        task.state = ExternalTaskState.COMPLETED
        task.worker_id = None
        task.lock_expiration = None
        if variables:
            task.variables.update(variables)
        logger.debug("External task completed: %s", task_id[:8])
        return task

    async def fail(
        self,
        task_id: str,
        worker_id: str,
        error_message: str = "",
        error_details: str = "",
        retries: int | None = None,
        retry_timeout_ms: int = 60000,
    ) -> ExternalTask | None:
        task = self._tasks.get(task_id)
        if task is None:
            return None
        if task.worker_id != worker_id:
            raise ValueError(f"Task {task_id[:8]} is locked by {task.worker_id}")
        task.worker_id = None
        task.lock_expiration = None
        task.error_message = error_message
        task.error_details = error_details
        task.last_failure_time = datetime.utcnow().isoformat()

        remaining = retries if retries is not None else task.retries
        if remaining > 1:
            task.state = ExternalTaskState.PENDING
            task.retries = remaining - 1
            logger.warning("External task %s failed, %d retries remaining: %s",
                            task_id[:8], task.retries, error_message)
        else:
            task.state = ExternalTaskState.FAILED
            logger.error("External task %s failed permanently: %s", task_id[:8], error_message)
        return task

    async def cancel(self, task_id: str) -> ExternalTask | None:
        task = self._tasks.get(task_id)
        if task is None:
            return None
        task.state = ExternalTaskState.CANCELLED
        task.worker_id = None
        task.lock_expiration = None
        return task

    def query_tasks(self, query: ExternalTaskQuery) -> list[ExternalTask]:
        results = list(self._tasks.values())
        if query.topic_name:
            results = [t for t in results if t.topic_name == query.topic_name]
        if query.worker_id:
            results = [t for t in results if t.worker_id == query.worker_id]
        if query.instance_id:
            results = [t for t in results if t.instance_id == query.instance_id]
        if query.state:
            results = [t for t in results if t.state == query.state]
        if query.priority_min is not None:
            results = [t for t in results if t.priority >= query.priority_min]
        results.sort(key=lambda t: t.priority, reverse=True)
        return results[query.offset:query.offset + query.limit]

    def get_instance_tasks(self, instance_id: str) -> list[ExternalTask]:
        task_ids = self._instance_tasks.get(instance_id, [])
        return [self._tasks[tid] for tid in task_ids if tid in self._tasks]

    def get_statistics(self) -> dict[str, int]:
        stats: dict[str, int] = {}
        for task in self._tasks.values():
            stats[task.state] = stats.get(task.state, 0) + 1
        stats["total"] = len(self._tasks)
        return stats
