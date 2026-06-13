from __future__ import annotations

from typing import Any

from .._types import RawData


class ParameterMapper:
    """Maps generic parameter dicts to tool-specific signatures."""

    def __init__(self, mapping: dict[str, str] | None = None) -> None:
        self._mapping = mapping or {}

    def map(self, params: RawData) -> RawData:
        mapped: RawData = {}
        for key, value in params.items():
            target_key = self._mapping.get(key, key)
            mapped[target_key] = value
        return mapped

    def validate(self, params: RawData, required: list[str]) -> list[str]:
        missing = [r for r in required if r not in params]
        return missing
