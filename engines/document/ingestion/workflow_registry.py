# engines/document/ingestion/router/workflow_registry.py

from __future__ import annotations

from typing import Dict, List

class WorkflowRegistry:
    def __init__(self) -> None:
        self._registry: Dict[str, List[str]] = {}

        # default workflow for any unregistered type
        self.default_workflow: List[str] = [
                "extract",
                "parse",
                "chunk",
                "embed",
                "store",
            ]

    # ---------------------------------------------------------------------
    def register(self, key: str, steps: List[str]):
        self._registry[key.lower()] = steps

    # ---------------------------------------------------------------------
    def get(self, key: str) -> List[str] | None:
        if key in self._registry:
            return self._registry[key]

        return None
