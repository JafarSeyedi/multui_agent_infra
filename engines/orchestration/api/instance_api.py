"""Instance query and lifecycle API."""

from __future__ import annotations

from dataclasses import dataclass

from ..core.engine import OrchestrationEngine
from ..core.instance import InstanceState


@dataclass(frozen=True)
class InstanceAPI:
    engine: OrchestrationEngine

    def get(self, instance_id: str):
        return self.engine.get_instance(instance_id)

    def suspend(self, instance_id: str) -> None:
        self.engine.suspend_instance(instance_id)

    def resume(self, instance_id: str) -> None:
        self.engine.resume_instance(instance_id)

    def terminate(self, instance_id: str, reason: str = "terminated") -> None:
        instance = self.engine.get_instance(instance_id)
        if instance.state != InstanceState.TERMINATED:
            instance.terminate(reason)

    def states(self) -> dict[str, int]:
        state_count: dict[str, int] = {item.value: 0 for item in InstanceState}
        for instance in self.engine.instances.values():
            state_count[instance.state.value] += 1
        return state_count
