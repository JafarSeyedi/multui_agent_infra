from typing import TYPE_CHECKING

from .models import OrchestrationRequest, OrchestrationResult
from .interaction.registry import InteractionStrategyRegistry

if TYPE_CHECKING:
    from agents.registry import AgentRegistry
    from agents.message_bus import MessageBus


class NativeOrchestrationBackend:
    """
    این backend یک facade ساده است
    وظیفه: انتخاب استراتژی و اجرای آن
    """

    def __init__(self, agent_registry: "AgentRegistry", message_bus: "MessageBus"):
        self.agent_registry = agent_registry
        self.message_bus = message_bus
        self.strategy_registry = InteractionStrategyRegistry()

    async def execute(self, request: OrchestrationRequest) -> OrchestrationResult:

        # انتخاب استراتژی مناسب
        strategy = self.strategy_registry.get_strategy(request.interaction_mode)

        try:
            result = await strategy.execute(
                request=request,
                agent_registry=self.agent_registry,
                message_bus=self.message_bus
            )

            # استراتژی‌ها همیشه OrchestrationResult برمی‌گردانند
            return result

        except Exception as e:

            # fallback برای شکست‌های شدید
            return OrchestrationResult(
                success=False,
                results=[],
                final_context=request.context,
                metadata={"error": str(e)}
            )
