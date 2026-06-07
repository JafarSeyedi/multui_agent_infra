"""User task adapter for BPMN user tasks.

Integrates user tasks/forms/claims/completions with durable state.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..core.instance import ProcessInstance
from ..core.engine import OrchestrationEngine


@dataclass
class TaskForm:
    form_key: str = ""
    form_fields: dict[str, dict[str, Any]] = field(default_factory=dict)
    default_values: dict[str, Any] = field(default_factory=dict)


@dataclass
class UserTaskClaim:
    task_id: str
    claimant: str = ""
    claimed_at: str = ""
    completed: bool = False
    completion_data: dict[str, Any] = field(default_factory=dict)


@dataclass
class ClaimResult:
    task_id: str
    claimed: bool = False
    claimant: str | None = None
    error: str | None = None


class UserTaskAdapter:
    def __init__(self, orchestration_engine: OrchestrationEngine | None = None) -> None:
        self._engine = orchestration_engine
        self._claims: dict[str, UserTaskClaim] = {}
        self._forms: dict[str, TaskForm] = {}

    def register_claim(self, task_id: str, claim: UserTaskClaim) -> None:
        self._claims[task_id] = claim

    def get_claim(self, task_id: str) -> UserTaskClaim | None:
        return self._claims.get(task_id)

    def claim_task(
        self,
        task_id: str,
        claimant: str,
        instance: ProcessInstance | None = None,
    ) -> ClaimResult:
        from datetime import datetime
        if task_id in self._claims:
            existing = self._claims[task_id]
            if existing.claimant and existing.claimant != claimant:
                return ClaimResult(task_id=task_id, claimed=False, error=f"Already claimed by {existing.claimant}")

        claim = UserTaskClaim(
            task_id=task_id,
            claimant=claimant,
            claimed_at=datetime.utcnow().isoformat(),
        )
        self._claims[task_id] = claim

        if instance:
            instance.set_variable(f"task.{task_id}.claimant", claimant)
            instance.set_variable(f"task.{task_id}.claimed", True)

        return ClaimResult(task_id=task_id, claimed=True, claimant=claimant)

    def release_task(self, task_id: str, instance: ProcessInstance | None = None) -> bool:
        claim = self._claims.get(task_id)
        if claim is None:
            return False
        claim.claimant = ""
        claim.claimed_at = ""
        if instance:
            instance.set_variable(f"task.{task_id}.claimant", None)
            instance.set_variable(f"task.{task_id}.claimed", False)
        return True

    def complete_task(
        self,
        task_id: str,
        completion_data: dict[str, Any] | None = None,
        instance: ProcessInstance | None = None,
    ) -> bool:
        claim = self._claims.get(task_id)
        if claim is None:
            return False
        claim.completed = True
        if completion_data:
            claim.completion_data = completion_data
        if instance:
            instance.set_variable(f"task.{task_id}.status", "completed")
            if completion_data:
                for key, value in completion_data.items():
                    instance.set_variable(f"task.{task_id}.output.{key}", value)
        return True

    def register_form(self, form_key: str, form: TaskForm) -> None:
        self._forms[form_key] = form

    def get_form(self, form_key: str) -> TaskForm | None:
        return self._forms.get(form_key)

    def is_claimed(self, task_id: str) -> bool:
        claim = self._claims.get(task_id)
        return claim is not None and bool(claim.claimant)

    def is_completed(self, task_id: str) -> bool:
        claim = self._claims.get(task_id)
        return claim is not None and claim.completed
