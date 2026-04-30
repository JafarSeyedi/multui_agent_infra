from typing import Any, Dict, List, Optional

from .base_strategy import InteractionStrategy
from ..agents.models import AgentOutput
from .interaction_models import (
    InteractionRequest,
    InteractionResult,
)


class DebateStrategy(InteractionStrategy):
    scenario_name = "debate"

    async def execute(self, request: InteractionRequest) -> InteractionResult:
        context: Dict[str, Any] = dict(request.context or {})
        agents = request.agents or []

        if len(agents) < 2:
            raise ValueError("DebateStrategy requires at least two agents (proposer & critic).")

        # استخراج نام عامل‌ها
        proposer_agent_meta = agents[0]
        critic_agent_meta = agents[1]
        
        proposer_name = proposer_agent_meta.agent_name
        critic_name = critic_agent_meta.agent_name

        max_rounds = int(request.metadata.get("max_rounds", 5))
        history: List[Dict[str, Any]] = []
        results: List[AgentOutput] = []
        current_answer: Optional[Any] = None
        approved_round: Optional[int] = None

        for round_id in range(1, max_rounds + 1):
            # ✅ حل خطای Missing recipient
            await self._emit(
                message_type="debate_round_started",
                payload={"round": round_id},
                sender="DebateStrategy",
                recipient="all_participants",
                message_id=f"debate_start_{round_id}",
            )

            # --- گام اول: Proposer ---
            proposer_output = await self._run_agent(
                agent_name=proposer_name,
                agent_id=f"proposer_round_{round_id}",
                context=context,
                payload={
                    "history": history, 
                    "round": round_id,
                    "mode": "propose"
                }
            )
            results.append(proposer_output)

            if proposer_output.error:
                break  # توقف در صورت خطا

            # استخراج پاسخ فعلی از خروجی عامل
            current_answer = proposer_output.payload or proposer_output.message

            # --- گام دوم: Critic ---
            critic_output = await self._run_agent(
                agent_name=critic_name,
                agent_id=f"critic_round_{round_id}",
                context=context,
                payload={
                    "answer": current_answer,
                    "history": history,
                    "round": round_id,
                    "mode": "critique"
                }
            )
            results.append(critic_output)

            if critic_output.error:
                break

            # ثبت در تاریخچه برای دور بعد
            critic_data = critic_output.payload or critic_output.message
            history.append({
                "round": round_id, 
                "answer": current_answer, 
                "critique": critic_data
            })

            # ✅ منطق تایید (بررسی خروجی Critic)
            if isinstance(critic_data, dict) and critic_data.get("approved") is True:
                approved_round = round_id
                await self._emit(
                    message_type="debate_finished",
                    payload={"round": round_id, "status": "approved"},
                    sender="DebateStrategy",
                    recipient="orchestrator",
                    message_id=f"debate_finished_{round_id}",
                )
                break

            # ✅ اطلاع‌رسانی پایان دور
            await self._emit(
                message_type="debate_round_completed",
                payload={"round": round_id},
                sender="DebateStrategy",
                recipient="all_participants",
                message_id=f"debate_round_{round_id}",
            )

        # آپدیت کانتکست نهایی
        context["debate_history"] = history
        context["final_answer"] = current_answer
        
        # محاسبه موفقیت کلی: اگر هیچ عاملی خطا نداده باشد
        is_overall_success = all(res.error is None for res in results)

        return InteractionResult(
            success=is_overall_success,
            results=results,
            final_context=context,
            metadata={
                "rounds_executed": len(history), 
                "approved_round": approved_round,
                "max_rounds_reached": len(history) >= max_rounds and not approved_round
            },
        )
