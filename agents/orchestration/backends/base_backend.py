# agents/orchestration/base_backend.py
from abc import ABC, abstractmethod
from agents.orchestration.models import OrchestrationRequest, OrchestrationResult

class BaseOrchestrationBackend(ABC):
    @abstractmethod
    async def execute(self, request: OrchestrationRequest) -> OrchestrationResult: ...
