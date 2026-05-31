"""Deployment and version/migration APIs.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..core.engine import OrchestrationEngine
from ..persistence.definition_repository import DefinitionRepository


@dataclass
class DeploymentResult:
    deployment_id: str = ""
    name: str = ""
    deployed_definitions: list[str] = field(default_factory=list)
    success: bool = True


@dataclass(frozen=True)
class DeploymentAPI:
    engine: OrchestrationEngine

    async def deploy(
        self,
        name: str,
        resources: dict[str, str],
        source: str = "api",
        tenant_id: str | None = None,
    ) -> DeploymentResult:
        deployment = await self.engine.deploy(
            name=name,
            resources=resources,
            source=source,
            tenant_id=tenant_id,
        )
        return DeploymentResult(
            deployment_id=deployment.id,
            name=deployment.name,
            deployed_definitions=[d.key for d in deployment.definitions],
            success=True,
        )

    def get_deployment(self, deployment_id: str) -> dict[str, Any] | None:
        deployment = self.engine.deployments.get(deployment_id)
        if deployment is None:
            return None
        return {
            "deployment_id": deployment.id,
            "name": deployment.name,
            "definitions": [d.key for d in deployment.definitions],
            "deployed_at": deployment.deployment_time.isoformat() if deployment.deployment_time else None,
            "tenant_id": deployment.tenant_id,
        }

    def list_deployments(self, tenant_id: str | None = None) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        for dep_id, dep in self.engine.deployments.items():
            if tenant_id and dep.tenant_id != tenant_id:
                continue
            results.append({
                "deployment_id": dep.id,
                "name": dep.name,
                "definitions": [d.key for d in dep.definitions],
            })
        return results

    def get_definitions(
        self,
        key: str | None = None,
        version: int | None = None,
        tenant_id: str | None = None,
    ) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        for def_key, defn in self.engine.definitions.items():
            if key and defn.key != key:
                continue
            if version and defn.version != version:
                continue
            if tenant_id and defn.tenant_id != tenant_id:
                continue
            results.append({
                "id": defn.id,
                "key": defn.key,
                "name": defn.name,
                "version": defn.version,
                "type": defn.definition_type,
            })
        return results
