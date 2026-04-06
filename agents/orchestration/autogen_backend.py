# agents/orchestration/autogen_backend.py
from __future__ import annotations

import uuid
from datetime import datetime
from functools import cached_property
from typing import Dict, List, Optional, Type

from agents.buses.base import MessageBus
from agents.orchestration.interaction.base_strategy import InteractionStrategy
from agents.orchestration.backends.native_backend import NativeOrchestrationBackend
from agents.orchestration.models import (
    OrchestrationExecution,
    OrchestrationRequest,
    OrchestrationResult,
)


class AutoGenOrchestrationBackend:
    """AutoGen wrapper که قرارداد orchestration سیستم را حفظ می‌کند.

    رفتار:
    - اگر autogen نصب نباشد: شفاف به native backend fallback می‌کند.
    - اگر autogen نصب باشد: از GroupChat واقعی autogen استفاده می‌کند.
      اگر GroupChat اجرا با خطا مواجه شد، به native backend fallback می‌کند.
    """

    def __init__(
        self,
        registry,
        message_bus: Optional[MessageBus] = None,
        storage=None,
        strategy_overrides: Optional[Dict[str, Type[InteractionStrategy]]] = None,
    ):
        self.registry = registry
        self.message_bus = message_bus
        self.storage = storage
        self._strategy_overrides = strategy_overrides

        # native backend با تمام پارامترها ساخته می‌شه
        self._native = NativeOrchestrationBackend(
            registry=registry,
            message_bus=message_bus,
            storage=storage,
            strategy_overrides=strategy_overrides,
        )

    @cached_property
    def _autogen_available(self) -> bool:
        """یک‌بار چک می‌شه و نتیجه cache می‌مونه."""
        try:
            import autogen  # noqa: F401
            return True
        except Exception:
            return False

    def is_available(self) -> bool:
        """API عمومی برای بررسی در دسترس بودن autogen."""
        return self._autogen_available

    # ──────────────────────────────────────────────────────────────
    # entry point اصلی
    # ──────────────────────────────────────────────────────────────

    async def execute(self, request: OrchestrationRequest) -> OrchestrationResult:
        if not self._autogen_available:
            return await self._execute_with_native(
                request,
                backend_label="native",
                note=(
                    "AutoGen requested but package is not installed; "
                    "native backend used instead."
                ),
            )

        try:
            return await self._execute_with_autogen_group_chat(request)
        except NotImplementedError:
            # GroupChat هنوز برای این سناریو پیاده‌سازی نشده
            return await self._execute_with_native(
                request,
                backend_label="autogen-wrapper",
                note=(
                    "AutoGen is available but GroupChat is not implemented "
                    "for this scenario; native backend used."
                ),
            )
        except Exception as exc:  # noqa: BLE001
            # خطای غیرمنتظره — fallback به native
            return await self._execute_with_native(
                request,
                backend_label="autogen-wrapper-fallback",
                note=f"AutoGen GroupChat failed ({exc!r}); native backend used.",
            )

    # ──────────────────────────────────────────────────────────────
    # GroupChat واقعی
    # ──────────────────────────────────────────────────────────────

    async def _execute_with_autogen_group_chat(
        self,
        request: OrchestrationRequest,
    ) -> OrchestrationResult:
        """اجرای GroupChat واقعی با autogen.

        پیش‌نیازها:
        - autogen نصب باشد (توسط _autogen_available تضمین شده).
        - هر task حداقل یک agent_name داشته باشد.
        - llm_config از request.shared_context خوانده می‌شود
          (کلید "llm_config")، در غیر این صورت از مقدار پیش‌فرض
          استفاده می‌شود.

        ساختار shared_context مورد انتظار (اختیاری):
            {
                "llm_config": {"model": "gpt-4", ...}
            }
        """
        import autogen

        if not request.tasks:
            raise ValueError("request.tasks نمی‌تواند خالی باشد.")

        started_at = datetime.utcnow()
        notes: List[str] = []

        # ── خواندن llm_config از shared_context یا مقدار پیش‌فرض ──
        llm_config: Dict = dict(
            request.shared_context.get(
                "llm_config",
                {"model": "gpt-4"},
            )
        )

        # ── ساخت AssistantAgent برای هر task ──────────────────────
        autogen_agents: List[autogen.AssistantAgent] = []
        for task in request.tasks:
            agent = autogen.AssistantAgent(
                name=task.agent_name,
                system_message=task.description or "",
                llm_config=llm_config,
            )
            autogen_agents.append(agent)

        # ── ساخت GroupChat و Manager ───────────────────────────────
        group_chat = autogen.GroupChat(
            agents=autogen_agents,
            messages=[],
            max_round=max(len(request.tasks) * 2, 4),
        )
        manager = autogen.GroupChatManager(
            groupchat=group_chat,
            llm_config=llm_config,
        )

        # ── شروع مکالمه با اولین task ─────────────────────────────
        first_task = request.tasks[0]
        initial_message = (
            str(first_task.input_payload)
            if first_task.input_payload
            else (first_task.description or "start")
        )

        await autogen_agents[0].a_initiate_chat(
            manager,
            message=initial_message,
        )

        # ── جمع‌آوری نتایج از پیام‌های GroupChat ──────────────────
        chat_messages = group_chat.messages
        executions: List[OrchestrationExecution] = []

        for idx, task in enumerate(request.tasks):
            # هر task با پیام متناظرش در GroupChat جفت می‌شه
            # اگر پیام کافی نبود، فیلد content خالی می‌مونه
            content = ""
            if idx < len(chat_messages):
                content = chat_messages[idx].get("content", "")

            executions.append(
                OrchestrationExecution(
                    task_id=task.task_id or str(uuid.uuid4()),
                    agent_name=task.agent_name,
                    status="success",
                    output_payload={"content": content},
                )
            )

        notes.append(
            f"AutoGen GroupChat completed: "
            f"{len(chat_messages)} messages, "
            f"{len(autogen_agents)} agents."
        )

        return OrchestrationResult(
            workflow_id=request.workflow_id,
            scenario=request.scenario,
            backend_used="autogen-groupchat",
            status="success",
            started_at=started_at,
            completed_at=datetime.utcnow(),
            shared_context=dict(request.shared_context),
            steps=[],
            executions=executions,
            messages=[],
            notes=notes,
        )

    # ──────────────────────────────────────────────────────────────
    # native fallback
    # ──────────────────────────────────────────────────────────────

    async def _execute_with_native(
        self,
        request: OrchestrationRequest,
        backend_label: str,
        note: str,
    ) -> OrchestrationResult:
        """Native backend را اجرا می‌کند و label و note را inject می‌کند."""
        result = await self._native.execute(request)

        updated_notes = list(result.notes) + [note]

        return result.model_copy(
            update={
                "backend_used": backend_label,
                "notes": updated_notes,
            }
        )
