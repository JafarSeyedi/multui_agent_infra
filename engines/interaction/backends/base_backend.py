# agents/interaction/backends/base_backend.py
from abc import ABC
from abc import abstractmethod

from engines.interaction.interaction_models import InteractionRequest
from engines.interaction.interaction_models import InteractionResult

class BaseOrchestrationBackend(ABC):
    @abstractmethod
    async def execute(self, request: InteractionRequest) -> InteractionResult: ...
