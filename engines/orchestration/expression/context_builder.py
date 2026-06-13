"""Helpers to build stable expression contexts from heterogeneous payloads."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ExpressionContext:
    """Dictionary-backed expression context."""

    data: dict[str, object]

    @classmethod
    def from_mapping(cls, mapping: dict[str, object] | None) -> ExpressionContext:
        return cls(data=dict(mapping or {}))

    def merge(self, extra: dict[str, object]) -> ExpressionContext:
        merged = dict(self.data)
        merged.update(extra)
        return ExpressionContext(data=merged)
