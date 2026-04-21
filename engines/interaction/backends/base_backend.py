# agents/interaction/backends/base_backend.py
from abc import ABC, abstractmethod
from engines.interaction.interaction_models import InteractionRequest, InteractionResult

class BaseOrchestrationBackend(ABC):
    @abstractmethod
    async def execute(self, request: InteractionRequest) -> InteractionResult: ...
