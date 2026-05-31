"""Dynamic step injection for orchestration runtime.

Supports injecting additional steps into running process instances
per Flowable/Orch8 patterns.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable
from uuid import uuid4


logger = logging.getLogger(__name__)


@dataclass
class InjectionRequest:
    request_id: str = ""
    instance_id: str = ""
    target_activity_id: str = ""
    insert_position: str = "after"
    new_activities: list[dict[str, Any]] = field(default_factory=list)
    new_flows: list[dict[str, Any]] = field(default_factory=list)
    update_transitions: bool = True
    reason: str = ""

    def __post_init__(self) -> None:
        if not self.request_id:
            self.request_id = str(uuid4())


@dataclass
class InjectionResult:
    request_id: str = ""
    instance_id: str = ""
    success: bool = False
    injected_activities: list[str] = field(default_factory=list)
    updated_flows: list[str] = field(default_factory=list)
    error: str | None = None
    timestamp: str = ""


class DynamicInjectionManager:
    def __init__(self, engine: Any) -> None:
        self._engine = engine
        self._injection_history: list[InjectionResult] = []
        self._pre_injection_hooks: list[Callable[..., Any]] = []
        self._post_injection_hooks: list[Callable[..., Any]] = []

    def register_pre_injection_hook(self, hook: Callable[..., Any]) -> None:
        self._pre_injection_hooks.append(hook)

    def register_post_injection_hook(self, hook: Callable[..., Any]) -> None:
        self._post_injection_hooks.append(hook)

    async def inject_activities(self, request: InjectionRequest) -> InjectionResult:
        result = InjectionResult(
            request_id=request.request_id,
            instance_id=request.instance_id,
            timestamp=datetime.utcnow().isoformat(),
        )

        try:
            instance = self._engine.instances.get(request.instance_id)
            if instance is None:
                result.error = f"Instance not found: {request.instance_id}"
                return result

            for hook in self._pre_injection_hooks:
                await hook(request)

            if request.insert_position == "after":
                await self._inject_after(instance, request, result)
            elif request.insert_position == "before":
                await self._inject_before(instance, request, result)
            elif request.insert_position == "parallel":
                await self._inject_parallel(instance, request, result)
            else:
                result.error = f"Unknown insert position: {request.insert_position}"
                return result

            for hook in self._post_injection_hooks:
                await hook(request, result)

            result.success = True
            logger.info("Injected %d activities into instance %s",
                         len(result.injected_activities), request.instance_id)

        except Exception as e:
            result.error = str(e)
            logger.exception("Dynamic injection failed for instance %s", request.instance_id)

        self._injection_history.append(result)
        return result

    async def _inject_after(self, instance: Any, request: InjectionRequest, result: InjectionResult) -> None:
        current_activity = request.target_activity_id
        for activity_data in request.new_activities:
            aid = activity_data.get("id", str(uuid4()))
            activity_data["id"] = aid
            result.injected_activities.append(aid)
            instance.set_variable(f"_injected.{aid}", {
                "injected_at": datetime.utcnow().isoformat(),
                "position": "after",
                "target": current_activity,
            })
        for flow_data in request.new_flows:
            fid = flow_data.get("id", str(uuid4()))
            flow_data["id"] = fid
            result.updated_flows.append(fid)
        instance.set_variable("_last_injection", {
            "request_id": request.request_id,
            "activities": result.injected_activities,
            "timestamp": datetime.utcnow().isoformat(),
        })

    async def _inject_before(self, instance: Any, request: InjectionRequest, result: InjectionResult) -> None:
        for activity_data in request.new_activities:
            aid = activity_data.get("id", str(uuid4()))
            activity_data["id"] = aid
            result.injected_activities.append(aid)
        instance.set_variable("_last_injection", {
            "request_id": request.request_id,
            "activities": result.injected_activities,
            "position": "before",
            "timestamp": datetime.utcnow().isoformat(),
        })

    async def _inject_parallel(self, instance: Any, request: InjectionRequest, result: InjectionResult) -> None:
        for activity_data in request.new_activities:
            aid = activity_data.get("id", str(uuid4()))
            activity_data["id"] = aid
            result.injected_activities.append(aid)
        instance.set_variable("_last_injection", {
            "request_id": request.request_id,
            "activities": result.injected_activities,
            "position": "parallel",
            "timestamp": datetime.utcnow().isoformat(),
        })

    def get_injection_history(self, instance_id: str | None = None) -> list[InjectionResult]:
        if instance_id:
            return [r for r in self._injection_history if r.instance_id == instance_id]
        return list(self._injection_history)
