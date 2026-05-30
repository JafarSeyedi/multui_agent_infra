"""Hierarchical/nested state handler."""

from __future__ import annotations

from typing import Any


class HierarchicalHandler:
    def normalize_path(self, state: str, parent: str | None = None) -> str:
        return f"{parent}.{state}" if parent else state

    def ancestors(self, state: str) -> list[str]:
        parts = state.split(".")
        out = []
        for i in range(1, len(parts) + 1):
            out.append(".".join(parts[:i]))
        return out
