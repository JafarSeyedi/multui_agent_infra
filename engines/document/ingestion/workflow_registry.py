# engines/document/ingestion/router/workflow_registry.py
from __future__ import annotations


class WorkflowRegistry:
    def __init__(self) -> None:
        self._registry: dict[str, list[str]] = {}

        # default workflow for any unregistered type
        self.default_workflow: list[str] = [
                "extract",
                "parse",
                "chunk",
                "embed",
                "store",
            ]

    # ---------------------------------------------------------------------
    def register(self, key: str, steps: list[str]):
        self._registry[key.lower()] = steps

    # ---------------------------------------------------------------------
    def get(self, key: str) -> list[str] | None:
        if key in self._registry:
            return self._registry[key]

        return None
