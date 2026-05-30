"""Deployment API wrapper."""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import asdict
from typing import Any

from ..core.engine import OrchestrationEngine, ProcessDefinition
from ..deployment.deployer import DeploymentArtifact, Deployer


@dataclass(frozen=True)
class DeploymentAPI:
    engine: OrchestrationEngine
    deployer: Deployer

    def create_definition_payload(self, definition_data: dict[str, Any]) -> ProcessDefinition:
        return ProcessDefinition(**definition_data)  # type: ignore[arg-type]

    def deploy(self, definition: ProcessDefinition) -> str:
        artifact = self.deployer.deploy(definition)
        return self.engine.deploy(
            name=artifact.definition.definition_key if hasattr(artifact.definition, "definition_key") else artifact.definition.key,
            definition=asdict(artifact.definition),
            definition_type=artifact.definition.definition_type,
            tenant_id=artifact.definition.tenant_id,
        )

    async def undeploy(self, deployment_id: str) -> bool:
        return self.engine.delete_deployment(deployment_id)
