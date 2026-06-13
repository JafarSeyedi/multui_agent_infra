"""Instance query/history/token/variable/timer inspection APIs.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from ..._types import FeelContext, Metadata, RawData
from ..core.engine import OrchestrationEngine


logger = logging.getLogger(__name__)


@dataclass
class InstanceInfo:
    instance_id: str = ""
    definition_key: str = ""
    definition_id: str = ""
    state: str = ""
    business_key: str | None = None
    start_time: str | None = None
    end_time: str | None = None
    variables: FeelContext = field(default_factory=dict)
    tokens: list[Metadata] = field(default_factory=list)
    current_activity_id: str | None = None
    is_suspended: bool = False


@dataclass(frozen=True)
class InstanceAPI:
    engine: OrchestrationEngine

    def get_instance(self, instance_id: str) -> InstanceInfo | None:
        instance = self.engine.instances.get(instance_id)
        if instance is None:
            return None
        return InstanceInfo(
            instance_id=instance.id,
            definition_key=instance.definition_key,
            definition_id=instance.definition_id,
            state=instance.state.value if hasattr(instance.state, "value") else str(instance.state),
            business_key=instance.business_key,
            start_time=instance.start_time.isoformat() if instance.start_time else None,
            end_time=instance.end_time.isoformat() if instance.end_time else None,
            variables=instance.get_all_variables(),
            current_activity_id=instance.current_activity_id,
            is_suspended=instance.is_suspended if hasattr(instance, "is_suspended") else False,
        )

    def query_instances(
        self,
        definition_key: str | None = None,
        state: str | None = None,
        business_key: str | None = None,
    ) -> list[InstanceInfo]:
        results: list[InstanceInfo] = []
        for instance_id, instance in self.engine.instances.items():
            if definition_key and instance.definition_key != definition_key:
                continue
            if state and instance.state.value != state:
                continue
            if business_key and instance.business_key != business_key:
                continue
            info = self.get_instance(instance_id)
            if info:
                results.append(info)
        return results

    def get_variables(self, instance_id: str) -> FeelContext:
        instance = self.engine.instances.get(instance_id)
        if instance is None:
            return {}
        return instance.get_all_variables()

    def get_tokens(self, instance_id: str) -> list[Metadata]:
        try:
            tokens = self.engine.token_manager.get_instance_tokens(instance_id)
            return [
                {
                    "token_id": t.token_id,
                    "state": t.state.value if hasattr(t.state, "value") else str(t.state),
                    "current_element": t.current_element_id,
                }
                for t in tokens
            ]
        except Exception:
            return []

    def get_history(self, instance_id: str) -> list[RawData]:
        try:
            rows = self.engine.history_repository.query(instance_id)
            return rows
        except Exception:
            return []

    async def modify_instance(
        self,
        instance_id: str,
        activity_id: str | None = None,
        transition_id: str | None = None,
        variables: FeelContext | None = None,
        cancel_at_activity: str | None = None,
    ) -> Metadata:
        return await self.engine.batch_manager.modify_instance(
            instance_id, activity_id=activity_id, transition_id=transition_id,
            variables=variables, cancel_at_activity=cancel_at_activity,
        )

    def get_incidents(
        self,
        instance_id: str | None = None,
        state: str | None = None,
        incident_type: str | None = None,
        limit: int = 100,
    ) -> list[Metadata]:
        from engines.orchestration.runtime.incident_manager import IncidentQuery
        query = IncidentQuery(
            instance_id=instance_id, state=state, incident_type=incident_type, limit=limit,
        )
        incidents = self.engine.incident_manager.query_incidents(query)
        return [
            {
                "incident_id": inc.incident_id, "type": inc.incident_type,
                "state": inc.state, "instance_id": inc.instance_id,
                "activity_id": inc.activity_id, "error_message": inc.error_message,
                "created_at": inc.created_at, "retry_count": inc.retry_count,
            }
            for inc in incidents
        ]

    async def resolve_incident(self, incident_id: str, resolution: str = "manual") -> Metadata:
        incident = self.engine.incident_manager.resolve_incident(incident_id, resolution)
        if incident is None:
            return {"success": False, "error": f"Incident not found: {incident_id}"}
        return {"success": True, "incident_id": incident.incident_id, "state": incident.state}

    def get_external_tasks(
        self,
        instance_id: str | None = None,
        topic_name: str | None = None,
        state: str | None = None,
        limit: int = 100,
    ) -> list[Metadata]:
        from engines.orchestration.runtime.external_task import ExternalTaskQuery
        query = ExternalTaskQuery(
            instance_id=instance_id, topic_name=topic_name, state=state, limit=limit,
        )
        tasks = self.engine.external_task_manager.query_tasks(query)
        return [
            {
                "task_id": t.task_id, "topic": t.topic_name, "state": t.state,
                "instance_id": t.instance_id, "activity_id": t.activity_id,
                "retries": t.retries, "priority": t.priority,
            }
            for t in tasks
        ]

    def get_forms(self, form_key: str | None = None) -> list[Metadata]:
        if form_key:
            form = self.engine.form_engine.get_form(form_key)
            return [form.to_dict()] if form else []
        return [f.to_dict() for f in self.engine.form_engine.list_forms()]

    async def submit_form(
        self, form_key: str, data: Metadata, instance_id: str | None = None,
    ) -> Metadata:
        return self.engine.form_engine.submit_form(form_key, data, instance_id)
