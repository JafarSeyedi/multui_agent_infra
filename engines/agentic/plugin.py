# engines/agentic/plugin.py
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class IAgentOrchestrator(ABC):
    name: str = "base"

    @abstractmethod
    async def run_workflow(self, workflow: str, inputs: dict[str, Any]) -> dict[str, Any]: ...

    @abstractmethod
    async def get_status(self, workflow_id: str) -> str: ...


class IAgentDelegate(ABC):
    name: str = "base"

    @abstractmethod
    async def delegate(self, task: str, context: dict[str, Any]) -> dict[str, Any]: ...
