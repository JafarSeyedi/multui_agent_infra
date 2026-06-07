"""Process instance API for orchestration.

Exposes process/case/state start/signal/message/terminate/suspend/resume operations.
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from typing import Any

from ..core.correlation import CorrelationKeySet
from ..core.engine import OrchestrationEngine
from ..core.instance import ProcessInstance


logger = logging.getLogger(__name__)


@dataclass
class StartProcessResult:
    instance_id: str = ""
    definition_key: str = ""
    business_key: str | None = None
    variables: dict[str, Any] = field(default_factory=dict)
    started: bool = True


@dataclass
class SignalResult:
    instance_id: str = ""
    signal_name: str = ""
    success: bool = True


@dataclass(frozen=True)
class ProcessAPI:
    engine: OrchestrationEngine

    async def start_process(
        self,
        definition_key: str,
        business_key: str | None = None,
        variables: dict[str, Any] | None = None,
        tenant_id: str | None = None,
    ) -> StartProcessResult:
        instance = await self.engine.start_process_instance(
            process_definition_key=definition_key,
            business_key=business_key,
            variables=variables,
            tenant_id=tenant_id,
        )
        return StartProcessResult(
            instance_id=instance.id,
            definition_key=definition_key,
            business_key=business_key,
            variables=variables or {},
            started=True,
        )

    async def terminate(
        self,
        instance_id: str,
        reason: str = "api-request",
    ) -> bool:
        await self.engine.delete_instance(instance_id, reason)
        return True

    async def suspend(self, instance_id: str) -> bool:
        await self.engine.update_instance_state(
            instance_id, __import__("engines.orchestration.core.instance", fromlist=["InstanceState"]).InstanceState.SUSPENDED, reason="api-suspend"
        )
        return True

    async def resume(self, instance_id: str) -> bool:
        from ..core.instance import InstanceState
        await self.engine.update_instance_state(
            instance_id, InstanceState.ACTIVE, reason="api-resume"
        )
        return True

    async def signal(
        self,
        instance_id: str,
        signal_name: str,
        variables: dict[str, Any] | None = None,
    ) -> SignalResult:
        try:
            signal_manager = getattr(self.engine, "signal_manager", None)
            if signal_manager is not None:
                await signal_manager.broadcast(signal_name, instance_id, variables or {})
            return SignalResult(instance_id=instance_id, signal_name=signal_name, success=True)
        except Exception as e:
            logger.error("Signal failed for %s: %s", instance_id, e)
            return SignalResult(instance_id=instance_id, signal_name=signal_name, success=False)

    async def send_message(
        self,
        instance_id: str,
        message_name: str,
        correlation_keys: dict[str, str] | None = None,
        variables: dict[str, Any] | None = None,
    ) -> bool:
        try:
            ck_set = CorrelationKeySet()
            if correlation_keys:
                for name, value in correlation_keys.items():
                    ck_set.add_key(name, value)
            await self.engine.correlation_engine.correlate_message(
                message_name=message_name,
                correlation_keys=ck_set,
                payload=variables or {},
                ttl_seconds=60,
            )
            return True
        except Exception as e:
            logger.error("Message failed for %s: %s", instance_id, e)
            return False
