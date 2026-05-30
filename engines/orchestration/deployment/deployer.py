"""Definition deployment orchestration for orchestration engine definitions."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import uuid4

from ..core.engine import ProcessDefinition
from .version_manager import VersionManager


@dataclass(frozen=True)
class DeploymentError(RuntimeError):
    """Raised when a deployment cannot be processed."""


@dataclass(frozen=True)
class DeploymentArtifact:
    definition: ProcessDefinition
    content: bytes
    checksum: str


class Deployer:
    """Coordinate versioned process definition deployment."""

    def __init__(self, *, version_manager: VersionManager | None = None) -> None:
        self.version_manager = version_manager or VersionManager()

    def deploy(self, definition: ProcessDefinition, *, tenant_id: str | None = None) -> DeploymentArtifact:
        checksum = f"sha256:{uuid4().hex}"
        return DeploymentArtifact(
            definition=definition,
            content=definition.definition_xml.encode("utf-8"),
            checksum=checksum,
        )

    def apply(self, definition: ProcessDefinition, tenant_id: str | None = None) -> str:
        artifact = self.deploy(definition, tenant_id=tenant_id)
        return artifact.checksum

    def metadata(self, definition: ProcessDefinition) -> dict[str, Any]:
        return {
            "key": definition.key,
            "version": definition.version,
            "tenant_id": definition.tenant_id,
            "deployed_at": definition.deployed_at.isoformat(),
        }

    def _ensure_versioning(self, definition: ProcessDefinition, *, tenant_id: str | None) -> ProcessDefinition:
        resolved_tenant = tenant_id or definition.tenant_id
        if resolved_tenant:
            return self.version_manager.assign_version(definition)
        return definition
