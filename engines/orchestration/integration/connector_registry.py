"""Connector registry for integration layer.

Centralizes pluggable connectors and runtime capability discovery.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ConnectorCapability:
    capability_id: str = ""
    capability_type: str = ""
    supported_operations: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Connector:
    connector_id: str = ""
    name: str | None = None
    connector_type: str = "http"
    capabilities: list[ConnectorCapability] = field(default_factory=list)
    configuration: dict[str, Any] = field(default_factory=dict)
    is_available: bool = True
    priority: int = 0


class ConnectorRegistry:
    def __init__(self) -> None:
        self._connectors: dict[str, Connector] = {}
        self._capabilities: dict[str, list[str]] = {}

    def register(self, connector: Connector) -> None:
        self._connectors[connector.connector_id] = connector
        for cap in connector.capabilities:
            if cap.capability_id not in self._capabilities:
                self._capabilities[cap.capability_id] = []
            self._capabilities[cap.capability_id].append(connector.connector_id)

    def unregister(self, connector_id: str) -> bool:
        connector = self._connectors.pop(connector_id, None)
        if connector:
            for cap in connector.capabilities:
                connectors = self._capabilities.get(cap.capability_id, [])
                if connector_id in connectors:
                    connectors.remove(connector_id)
            return True
        return False

    def get_connector(self, connector_id: str) -> Connector | None:
        return self._connectors.get(connector_id)

    def list_connectors(self, connector_type: str | None = None) -> list[Connector]:
        connectors = list(self._connectors.values())
        if connector_type:
            connectors = [c for c in connectors if c.connector_type == connector_type]
        return connectors

    def list_available(self) -> list[Connector]:
        return [c for c in self._connectors.values() if c.is_available]

    def find_by_capability(self, capability_id: str) -> list[Connector]:
        connector_ids = self._capabilities.get(capability_id, [])
        return [self._connectors[cid] for cid in connector_ids if cid in self._connectors]

    def find_by_operation(self, operation: str) -> list[Connector]:
        results: list[Connector] = []
        for connector in self._connectors.values():
            for cap in connector.capabilities:
                if operation in cap.supported_operations:
                    results.append(connector)
                    break
        return results

    def get_statistics(self) -> dict[str, Any]:
        total = len(self._connectors)
        available = sum(1 for c in self._connectors.values() if c.is_available)
        types: dict[str, int] = {}
        for c in self._connectors.values():
            types[c.connector_type] = types.get(c.connector_type, 0) + 1
        return {
            "total": total,
            "available": available,
            "types": types,
            "capabilities": len(self._capabilities),
        }
