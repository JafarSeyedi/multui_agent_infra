"""Version tracking for deployments and definition revisions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..core.engine import ProcessDefinition


@dataclass(frozen=True)
class VersionConflict(RuntimeError):
    """Raised when two incompatible versions conflict."""


def _next_version(definitions: list[ProcessDefinition]) -> int:
    if not definitions:
        return 1
    return max(item.version for item in definitions) + 1


class VersionManager:
    """Assign and validate versions per key/tenant tuple."""

    def __init__(self) -> None:
        self._index: dict[tuple[str | None, str], list[ProcessDefinition]] = {}

    def versions(self, key: str, tenant_id: str | None = None) -> list[ProcessDefinition]:
        return list(self._index.get((tenant_id, key), []))

    def assign_version(self, definition: ProcessDefinition) -> ProcessDefinition:
        key = (definition.tenant_id, definition.key)
        versions = self._index.setdefault(key, [])
        definition = definition.__class__(
            **{
                **definition.__dict__,
                "version": _next_version(versions),
            }
        )
        versions.append(definition)
        return definition

    def get_latest(self, key: str, tenant_id: str | None = None) -> ProcessDefinition | None:
        versions = self.versions(key, tenant_id)
        return versions[-1] if versions else None

    def snapshot(self, key: str, tenant_id: str | None = None) -> list[dict[str, Any]]:
        return [item.__dict__ for item in self.versions(key, tenant_id)]
