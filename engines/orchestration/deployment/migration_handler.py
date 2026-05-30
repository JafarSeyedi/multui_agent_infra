"""Migration helper for moving instances across definition versions."""

from __future__ import annotations

from dataclasses import dataclass

from ..core.instance import ProcessInstance
from ..core.instance import InstanceManager


@dataclass(frozen=True)
class MigrationPlan:
    source_definition_id: str
    target_definition_id: str
    strategy: str


@dataclass(frozen=True)
class MigrationResult:
    instance_id: str
    migrated: bool
    message: str


class MigrationHandler:
    """Perform lightweight definition migration for running instances."""

    def __init__(self, instance_manager: InstanceManager | None = None) -> None:
        self.instance_manager = instance_manager

    def migrate(self, instance: ProcessInstance, plan: MigrationPlan) -> MigrationResult:
        if self.instance_manager and instance.state.name != "ACTIVE":
            raise RuntimeError("Cannot migrate inactive instances")
        instance.definition_id = plan.target_definition_id
        return MigrationResult(
            instance_id=instance.id,
            migrated=True,
            message=f"Migrated from {plan.source_definition_id} to {plan.target_definition_id}",
        )
