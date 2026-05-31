"""Async continuation support for orchestration runtime.

Implements async-before and async-after markers per Camunda/Flowable patterns:
- Activities marked "async before" create a job before execution
- The engine suspends the token while the job executes
- When the job completes, the token resumes with "async after"
- Transaction boundary management across the async boundary
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable
from uuid import uuid4


logger = logging.getLogger(__name__)


class AsyncJobState(str, Enum):
    CREATED = "created"
    PENDING = "pending"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMED_OUT = "timed_out"
    CANCELLED = "cancelled"


from enum import Enum


@dataclass
class AsyncJob:
    job_id: str = ""
    instance_id: str = ""
    activity_id: str = ""
    async_type: str = "before"
    state: str = AsyncJobState.CREATED
    retries: int = 3
    error_message: str = ""
    created_at: str = ""
    executed_at: str | None = None
    completed_at: str | None = None
    handler: Callable[..., Any] | None = None
    payload: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()
        if not self.job_id:
            self.job_id = str(uuid4())


class AsyncContinuationManager:
    def __init__(self, scheduler: Any | None = None) -> None:
        self._jobs: dict[str, AsyncJob] = {}
        self._activity_jobs: dict[str, str] = {}
        self._scheduler = scheduler

    def create_async_before_job(
        self,
        instance_id: str,
        activity_id: str,
        handler: Callable[..., Any] | None = None,
        payload: dict[str, Any] | None = None,
    ) -> AsyncJob:
        job = AsyncJob(
            instance_id=instance_id,
            activity_id=activity_id,
            async_type="before",
            handler=handler,
            payload=payload or {},
        )
        self._jobs[job.job_id] = job
        self._activity_jobs[f"{instance_id}:{activity_id}"] = job.job_id
        logger.debug("Async-before job created: %s for %s/%s",
                      job.job_id[:8], instance_id[:8], activity_id)
        return job

    def create_async_after_job(
        self,
        instance_id: str,
        activity_id: str,
        handler: Callable[..., Any] | None = None,
        payload: dict[str, Any] | None = None,
    ) -> AsyncJob:
        job = AsyncJob(
            instance_id=instance_id,
            activity_id=activity_id,
            async_type="after",
            handler=handler,
            payload=payload or {},
        )
        self._jobs[job.job_id] = job
        logger.debug("Async-after job created: %s for %s/%s",
                      job.job_id[:8], instance_id[:8], activity_id)
        return job

    async def execute_job(self, job_id: str) -> AsyncJob | None:
        job = self._jobs.get(job_id)
        if job is None:
            return None
        job.state = AsyncJobState.EXECUTING
        job.executed_at = datetime.utcnow().isoformat()
        try:
            if job.handler:
                await job.handler(job)
            job.state = AsyncJobState.COMPLETED
            job.completed_at = datetime.utcnow().isoformat()
        except Exception as e:
            job.retries -= 1
            if job.retries > 0:
                job.state = AsyncJobState.PENDING
                job.error_message = str(e)
            else:
                job.state = AsyncJobState.FAILED
                job.error_message = str(e)
        return job

    def get_job(self, job_id: str) -> AsyncJob | None:
        return self._jobs.get(job_id)

    def get_job_for_activity(self, instance_id: str, activity_id: str) -> AsyncJob | None:
        job_id = self._activity_jobs.get(f"{instance_id}:{activity_id}")
        if job_id:
            return self._jobs.get(job_id)
        return None

    def get_pending_jobs(self, instance_id: str | None = None) -> list[AsyncJob]:
        jobs = [j for j in self._jobs.values() if j.state == AsyncJobState.PENDING]
        if instance_id:
            jobs = [j for j in jobs if j.instance_id == instance_id]
        return jobs

    def get_failed_jobs(self, instance_id: str | None = None) -> list[AsyncJob]:
        jobs = [j for j in self._jobs.values() if j.state == AsyncJobState.FAILED]
        if instance_id:
            jobs = [j for j in jobs if j.instance_id == instance_id]
        return jobs

    def cancel_job(self, job_id: str) -> bool:
        job = self._jobs.get(job_id)
        if job and job.state in (AsyncJobState.CREATED, AsyncJobState.PENDING, AsyncJobState.EXECUTING):
            job.state = AsyncJobState.CANCELLED
            return True
        return False

    def get_statistics(self) -> dict[str, int]:
        stats: dict[str, int] = {}
        for job in self._jobs.values():
            stats[job.state] = stats.get(job.state, 0) + 1
        stats["total"] = len(self._jobs)
        return stats
