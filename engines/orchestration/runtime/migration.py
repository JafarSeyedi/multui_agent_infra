"""Process instance migration for orchestration runtime.

Supports migrating running process instances from one process definition version
to another, per Camunda/Flowable migration patterns.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from ..core.instance import InstanceState


logger = logging.getLogger(__name__)


@dataclass
class MigrationMapping:
    source_activity_id: str
    target_activity_id: str
    update_event_trigger: bool = False


@dataclass
class MigrationPlan:
    source_definition_key: str
    source_definition_version: int
    target_definition_key: str
    target_definition_version: int
    activity_mappings: list[MigrationMapping] = field(default_factory=list)
    validate_only: bool = False

    @property
    def source_id(self) -> str:
        return f"{self.source_definition_key}:{self.source_definition_version}"

    @property
    def target_id(self) -> str:
        return f"{self.target_definition_key}:{self.target_definition_version}"


@dataclass
class MigrationResult:
    migration_id: str = ""
    plan: MigrationPlan | None = None
    instances_migrated: int = 0
    instances_failed: int = 0
    instances_skipped: int = 0
    errors: list[dict[str, str]] = field(default_factory=list)
    started_at: str = ""
    completed_at: str | None = None
    status: str = "pending"
    total_count: int = 0


@dataclass
class BatchOperation:
    operation_id: str = ""
    operation_type: str = ""
    instance_filter: dict[str, Any] = field(default_factory=dict)
    total_count: int = 0
    processed_count: int = 0
    failed_count: int = 0
    status: str = "pending"
    parameters: dict[str, Any] = field(default_factory=dict)
    errors: list[dict[str, str]] = field(default_factory=list)
    created_at: str = ""
    started_at: str | None = None
    completed_at: str | None = None


class ProcessInstanceMigrator:
    def __init__(self, engine: Any) -> None:
        self._engine = engine

    def create_migration_plan(
        self,
        source_definition_key: str,
        source_version: int,
        target_definition_key: str,
        target_version: int,
                activity_mappings: list[dict[str, Any]] | None = None,
    ) -> MigrationPlan:
        mappings = []
        if activity_mappings:
            for m in activity_mappings:
                mappings.append(MigrationMapping(
                    source_activity_id=m["source"],
                    target_activity_id=m["target"],
                    update_event_trigger=bool(m.get("update_event_trigger", False)),
                ))

        return MigrationPlan(
            source_definition_key=source_definition_key,
            source_definition_version=source_version,
            target_definition_key=target_definition_key,
            target_definition_version=target_version,
            activity_mappings=mappings,
        )

    def validate_migration(self, plan: MigrationPlan) -> list[str]:
        errors = []
        source_def = self._engine.get_definition(plan.source_definition_key, plan.source_definition_version)
        if source_def is None:
            errors.append(f"Source definition not found: {plan.source_id}")

        target_def = self._engine.get_definition(plan.target_definition_key, plan.target_definition_version)
        if target_def is None:
            errors.append(f"Target definition not found: {plan.target_id}")

        for mapping in plan.activity_mappings:
            has_source = False
            has_target = False
            if source_def and isinstance(source_def.definition_xml, dict):
                elements = source_def.definition_xml.get("flow_elements", {})
                has_source = mapping.source_activity_id in elements
            if target_def and isinstance(target_def.definition_xml, dict):
                elements = target_def.definition_xml.get("flow_elements", {})
                has_target = mapping.target_activity_id in elements
            if not has_source:
                errors.append(f"Source activity not found: {mapping.source_activity_id}")
            if not has_target:
                errors.append(f"Target activity not found: {mapping.target_activity_id}")

        return errors

    async def execute_migration(
        self,
        plan: MigrationPlan,
        instance_ids: list[str] | None = None,
        batch_size: int = 100,
    ) -> MigrationResult:
        result = MigrationResult(
            migration_id=f"mig_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            plan=plan,
            started_at=datetime.utcnow().isoformat(),
        )

        if plan.validate_only:
            errors = self.validate_migration(plan)
            if errors:
                result.errors = [{"validation": e} for e in errors]
                result.status = "validation_failed"
            else:
                result.status = "validated"
            return result

        validation_errors = self.validate_migration(plan)
        if validation_errors:
            result.errors = [{"validation": e} for e in validation_errors]
            result.status = "failed"
            return result

        if instance_ids is None:
            instance_ids = [
                iid for iid, inst in self._engine.instances.items()
                if inst.definition_key == plan.source_definition_key
                and inst.state in (InstanceState.ACTIVE, InstanceState.SUSPENDED)
            ]

        result.total_count = len(instance_ids)

        for i in range(0, len(instance_ids), batch_size):
            batch = instance_ids[i:i + batch_size]
            for instance_id in batch:
                try:
                    await self._migrate_single_instance(instance_id, plan)
                    result.instances_migrated += 1
                except Exception as e:
                    result.instances_failed += 1
                    result.errors.append({"instance_id": instance_id, "error": str(e)})
                    logger.exception("Migration failed for instance %s", instance_id)

        result.status = "completed" if result.instances_failed == 0 else "completed_with_errors"
        result.completed_at = datetime.utcnow().isoformat()
        logger.info("Migration completed: %d migrated, %d failed",
                     result.instances_migrated, result.instances_failed)
        return result

    async def _migrate_single_instance(self, instance_id: str, plan: MigrationPlan) -> None:
        instance = self._engine.instances.get(instance_id)
        if instance is None:
            raise ValueError(f"Instance not found: {instance_id}")

        for mapping in plan.activity_mappings:
            if instance.current_activity_id == mapping.source_activity_id:
                old_activity = instance.current_activity_id
                instance.current_activity_id = mapping.target_activity_id
                instance.set_variable("_migration_mapping", {
                    "source": mapping.source_activity_id,
                    "target": mapping.target_activity_id,
                    "migrated_at": datetime.utcnow().isoformat(),
                })
                logger.info("Migrated instance %s: %s -> %s",
                             instance_id, old_activity, mapping.target_activity_id)


class BatchOperationManager:
    def __init__(self, engine: Any) -> None:
        self._engine = engine
        self._operations: dict[str, BatchOperation] = {}

    async def suspend_instances(
        self,
        definition_key: str | None = None,
        instance_ids: list[str] | None = None,
        batch_size: int = 100,
    ) -> BatchOperation:
        return await self._execute_batch(
            operation_type="suspend",
            instance_filter={"definition_key": definition_key} if definition_key else {},
            instance_ids=instance_ids,
            batch_size=batch_size,
            action_fn=self._engine.update_instance_state,
            action_args={"new_state": InstanceState.SUSPENDED, "reason": "batch-suspend"},
        )

    async def resume_instances(
        self,
        definition_key: str | None = None,
        instance_ids: list[str] | None = None,
        batch_size: int = 100,
    ) -> BatchOperation:
        return await self._execute_batch(
            operation_type="resume",
            instance_filter={"definition_key": definition_key} if definition_key else {},
            instance_ids=instance_ids,
            batch_size=batch_size,
            action_fn=self._engine.update_instance_state,
            action_args={"new_state": InstanceState.ACTIVE, "reason": "batch-resume"},
        )

    async def delete_instances(
        self,
        definition_key: str | None = None,
        instance_ids: list[str] | None = None,
        cascade: bool = True,
        batch_size: int = 100,
    ) -> BatchOperation:
        return await self._execute_batch(
            operation_type="delete",
            instance_filter={"definition_key": definition_key} if definition_key else {},
            instance_ids=instance_ids,
            batch_size=batch_size,
            action_fn=self._engine.delete_instance,
            action_args={"reason": "batch-delete"},
        )

    async def modify_instance(
        self,
        instance_id: str,
        activity_id: str | None = None,
        transition_id: str | None = None,
        variables: dict[str, Any] | None = None,
        cancel_at_activity: str | None = None,
    ) -> dict[str, Any]:
        result: dict[str, Any] = {"instance_id": instance_id, "status": "not_found"}

        instance = self._engine.instances.get(instance_id)
        if instance is None:
            return result

        if activity_id:
            tokens = self._engine.token_manager.get_instance_tokens(instance_id)
            for token in tokens:
                if cancel_at_activity:
                    self._engine.token_manager.cancel_at(token.token_id, cancel_at_activity)
                if activity_id:
                    self._engine.token_manager.move_to(token.token_id, activity_id)

        if variables:
            for name, value in variables.items():
                instance.set_variable(name, value)
                await self._engine.variable_manager.set_persisted(instance_id, instance_id, name, value)

        if transition_id:
            tokens = self._engine.token_manager.get_instance_tokens(instance_id)
            for token in tokens:
                if token.current_element_id == activity_id:
                    self._engine.token_manager.move_to(token.token_id, transition_id)

        result["status"] = "completed"
        return result

    async def _execute_batch(
        self,
        operation_type: str,
        instance_filter: dict[str, Any],
        instance_ids: list[str] | None,
        batch_size: int,
        action_fn: Any,
        action_args: dict[str, Any],
    ) -> BatchOperation:
        from uuid import uuid4
        op = BatchOperation(
            operation_id=str(uuid4()),
            operation_type=operation_type,
            instance_filter=instance_filter,
            parameters=action_args,
            created_at=datetime.utcnow().isoformat(),
            started_at=datetime.utcnow().isoformat(),
        )

        if instance_ids is None:
            for iid, inst in self._engine.instances.items():
                match = True
                for key, value in instance_filter.items():
                    if getattr(inst, key, None) != value:
                        match = False
                        break
                if match:
                    instance_ids = instance_ids or []
                    instance_ids.append(iid)

        if instance_ids is None:
            instance_ids = []

        op.total_count = len(instance_ids)

        for i in range(0, len(instance_ids), batch_size):
            batch = instance_ids[i:i + batch_size]
            for instance_id in batch:
                try:
                    await action_fn(instance_id, **action_args)
                    op.processed_count += 1
                except Exception as e:
                    op.failed_count += 1
                    op.errors.append({"instance_id": instance_id, "error": str(e)})

        op.status = "completed" if op.failed_count == 0 else "completed_with_errors"
        op.completed_at = datetime.utcnow().isoformat()
        self._operations[op.operation_id] = op
        return op

    def get_operation(self, operation_id: str) -> BatchOperation | None:
        return self._operations.get(operation_id)

    def list_operations(self, operation_type: str | None = None) -> list[BatchOperation]:
        ops = list(self._operations.values())
        if operation_type:
            ops = [o for o in ops if o.operation_type == operation_type]
        return sorted(ops, key=lambda o: o.created_at, reverse=True)
