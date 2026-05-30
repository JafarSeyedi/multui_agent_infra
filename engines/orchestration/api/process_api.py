"""Process deployment and start/complete API wrappers."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4

from ..core.engine import OrchestrationEngine


@dataclass(frozen=True)
class ProcessAPI:
    engine: OrchestrationEngine

    def start_process(self, definition_key: str, variables: dict[str, object] | None = None) -> str:
        return self.engine.start_process(definition_key=definition_key, variables=variables or {})

    def complete_process(self, instance_id: str, end_activity_id: str | None = None) -> None:
        instance = self.engine.get_instance(instance_id)
        if end_activity_id:
            instance.current_activity_id = end_activity_id
        instance.complete()

    def list_running(self) -> list[str]:
        return list(self.engine.active_instances)

    def generate_temporary_correlation(self) -> str:
        return f"corr-{uuid4().hex}"
