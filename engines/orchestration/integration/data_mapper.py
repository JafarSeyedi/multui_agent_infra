"""Data mapping helpers used by tasks, connectors, and expressions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class DataMapper:
    """Simple declarative data mapper with dotted-path support."""

    @staticmethod
    def get_path(payload: dict[str, Any], path: str) -> Any:
        current: Any = payload
        for part in path.split("."):
            if not isinstance(current, dict):
                return None
            current = current.get(part)
            if current is None:
                return None
        return current

    @staticmethod
    def map_payload(payload: dict[str, Any], mapping: dict[str, str]) -> dict[str, Any]:
        return {target: DataMapper.get_path(payload, source) for target, source in mapping.items()}
