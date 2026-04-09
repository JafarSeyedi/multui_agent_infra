# agents/orchestration/interaction/base_strategy.py
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional, Dict, Any

from agents.buses.base import MessageBus
from agents.orchestration.models import (
    OrchestrationRequest,
    OrchestrationResult,
    AgentMessage,
)


class InteractionStrategy(ABC):
    scenario_name: str  # باید در subclass تعریف بشه
    
    def __init__(
        self,
        agent_registry,
        message_bus: Optional[MessageBus] = None,
        storage=None,
    ):
        self.agent_registry = agent_registry
        self.message_bus = message_bus
        self.storage = storage

    @abstractmethod
    async def execute(self, request: OrchestrationRequest) -> OrchestrationResult:
        """اجرای استراتژی و برگرداندن نتیجه"""
        pass

    async def _emit(
        self,
        message_type: str,
        payload: Dict[str, Any],
        sender: str = "Strategy",
        recipient: str = "system",
        message_id: Optional[str] = None,
    ) -> None:
        """Helper مرکزی برای publish کردن AgentMessage."""
        if not self.message_bus:
            return
        await self.message_bus.publish(
            AgentMessage(
                message_id=message_id or f"strategy_{message_type}",
                sender=sender,
                recipient=recipient,
                message_type=message_type,
                payload=payload,
                timestamp=datetime.utcnow(),
            )
        )
