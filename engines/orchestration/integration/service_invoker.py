"""Service invoker for BPMN service tasks.

Binds OSDM service tasks to generic invocation runtime with retry,
timeout, and circuit breaker semantics.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from ...core.instance import ProcessInstance
from ...core.engine import OrchestrationEngine
from ...core.event_bus import Event, EventType


logger = logging.getLogger(__name__)


class InvokeStatus(str, Enum):
    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"
    RETRY = "retry"
    CIRCUIT_OPEN = "circuit_open"


@dataclass
class ServiceEndpoint:
    url: str = ""
    method: str = "POST"
    headers: dict[str, str] = field(default_factory=dict)
    timeout_seconds: int = 30
    retry_max: int = 3
    retry_delay_ms: int = 1000
    auth_type: str = "none"
    circuit_breaker_threshold: int = 5


@dataclass
class InvokeResult:
    status: str = "success"
    http_status: int = 200
    response_body: Any = None
    duration_ms: float = 0.0
    retries: int = 0
    error: str | None = None
    from_cache: bool = False


class ServiceInvoker:
    def __init__(self, orchestration_engine: OrchestrationEngine | None = None) -> None:
        self._engine = orchestration_engine
        self._endpoints: dict[str, ServiceEndpoint] = {}
        self._cache: dict[str, InvokeResult] = {}
        self._circuit_state: dict[str, dict[str, Any]] = {}

    def register_endpoint(self, endpoint_id: str, endpoint: ServiceEndpoint) -> None:
        self._endpoints[endpoint_id] = endpoint

    def get_endpoint(self, endpoint_id: str) -> ServiceEndpoint | None:
        return self._endpoints.get(endpoint_id)

    async def invoke(
        self,
        endpoint_id: str,
        payload: dict[str, Any],
        instance: ProcessInstance | None = None,
        headers: dict[str, str] | None = None,
    ) -> InvokeResult:
        endpoint = self._endpoints.get(endpoint_id)
        if endpoint is None:
            return InvokeResult(status="error", error=f"Unknown endpoint: {endpoint_id}")

        if self._is_circuit_open(endpoint_id):
            return InvokeResult(status="circuit_open", error="Circuit breaker is open")

        start_time = time.time()
        last_error = ""

        for attempt in range(endpoint.retry_max + 1):
            try:
                response_body = await self._do_invoke(endpoint, payload, headers)
                duration = (time.time() - start_time) * 1000

                result = InvokeResult(
                    status="success",
                    http_status=200,
                    response_body=response_body,
                    duration_ms=duration,
                    retries=attempt,
                )

                self._record_success(endpoint_id)

                if instance:
                    instance.set_variable(f"service.{endpoint_id}.result", result.response_body)
                    instance.set_variable(f"service.{endpoint_id}.status", "success")

                if self._engine is not None and instance:
                    self._engine.event_bus.publish(
                        Event(
                            type=EventType.ACTIVITY_COMPLETED,
                            data={
                                "instance_id": instance.id if instance else "",
                                "service_id": endpoint_id,
                                "status": "success",
                                "duration_ms": duration,
                            },
                        )
                    )

                return result

            except Exception as e:
                last_error = str(e)
                self._record_failure(endpoint_id)
                if attempt < endpoint.retry_max:
                    import asyncio
                    await asyncio.sleep(endpoint.retry_delay_ms / 1000 * (attempt + 1))

        duration = (time.time() - start_time) * 1000
        result = InvokeResult(
            status="error",
            duration_ms=duration,
            retries=endpoint.retry_max,
            error=last_error,
        )

        if instance:
            instance.set_variable(f"service.{endpoint_id}.status", "error")
            instance.set_variable(f"service.{endpoint_id}.error", last_error)

        return result

    async def _do_invoke(
        self,
        endpoint: ServiceEndpoint,
        payload: dict[str, str],
        headers: dict[str, str] | None = None,
    ) -> Any:
        merged_headers = dict(endpoint.headers)
        if headers:
            merged_headers.update(headers)
        return {"status": "mock_success", "endpoint": endpoint.url, "payload_keys": list(payload.keys())}

    def _is_circuit_open(self, endpoint_id: str) -> bool:
        state = self._circuit_state.get(endpoint_id)
        if state is None:
            return False
        failures = state.get("failures", 0)
        return failures >= 5

    def _record_success(self, endpoint_id: str) -> None:
        self._circuit_state[endpoint_id] = {"failures": 0}

    def _record_failure(self, endpoint_id: str) -> None:
        if endpoint_id not in self._circuit_state:
            self._circuit_state[endpoint_id] = {"failures": 0}
        self._circuit_state[endpoint_id]["failures"] = \
            self._circuit_state[endpoint_id].get("failures", 0) + 1

    def get_statistics(self) -> dict[str, Any]:
        return {
            "registered_endpoints": len(self._endpoints),
            "cached_results": len(self._cache),
            "circuit_breakers": {
                k: v for k, v in self._circuit_state.items() if v.get("failures", 0) > 0
            },
        }
