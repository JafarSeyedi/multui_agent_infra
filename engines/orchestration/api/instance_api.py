"""Instance query/history/token/variable/timer inspection APIs.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

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
    variables: dict[str, Any] = field(default_factory=dict)
    tokens: list[dict[str, Any]] = field(default_factory=list)
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

    def get_variables(self, instance_id: str) -> dict[str, Any]:
        instance = self.engine.instances.get(instance_id)
        if instance is None:
            return {}
        return instance.get_all_variables()

    def get_tokens(self, instance_id: str) -> list[dict[str, Any]]:
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

    def get_history(self, instance_id: str) -> list[dict[str, Any]]:
        try:
            rows = self.engine.history_repository.query(instance_id)
            return rows
        except Exception:
            return []
