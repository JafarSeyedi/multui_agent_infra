from __future__ import annotations

from typing import Any

from .backends import ObservabilityBackend


def wrap_registry(registry: Any, backend: ObservabilityBackend, engine_name: str, trace_defs: dict | None = None) -> Any:
    trace_defs = trace_defs or {}

    class TracedRegistry:
        def __init__(self, inner: Any):
            self._inner = inner

        def __getattr__(self, name: str) -> Any:
            return getattr(self._inner, name)

        async def run(self, *args: Any, **kwargs: Any) -> Any:
            span_name = f"{engine_name}.run"
            span = await backend.start_span(span_name, {"engine": engine_name})
            try:
                result = await self._inner.run(*args, **kwargs)
                await backend.end_span(span, "ok")
                await backend.record_metric(f"{engine_name}.run.count", 1, {"status": "ok"})
                return result
            except Exception as e:
                await backend.end_span(span, "error")
                await backend.record_metric(f"{engine_name}.run.count", 1, {"status": "error"})
                raise

        async def execute(self, *args: Any, **kwargs: Any) -> Any:
            span_name = f"{engine_name}.execute"
            span = await backend.start_span(span_name, {"engine": engine_name})
            try:
                result = await self._inner.execute(*args, **kwargs)
                await backend.end_span(span, "ok")
                return result
            except Exception as e:
                await backend.end_span(span, "error")
                raise

    return TracedRegistry(registry)


def wrap_send(
    send_fn: Any, backend: ObservabilityBackend, engine_name: str
) -> Any:
    async def traced_send(*args: Any, **kwargs: Any) -> Any:
        span_name = f"{engine_name}.send"
        span = await backend.start_span(span_name, {"engine": engine_name})
        try:
            result = await send_fn(*args, **kwargs)
            await backend.end_span(span, "ok")
            return result
        except Exception as e:
            await backend.end_span(span, "error")
            raise

    return traced_send


def wrap_broadcast(
    broadcast_fn: Any, backend: ObservabilityBackend, engine_name: str
) -> Any:
    async def traced_broadcast(*args: Any, **kwargs: Any) -> Any:
        span_name = f"{engine_name}.broadcast"
        span = await backend.start_span(span_name, {"engine": engine_name})
        try:
            result = await broadcast_fn(*args, **kwargs)
            await backend.end_span(span, "ok")
            return result
        except Exception as e:
            await backend.end_span(span, "error")
            raise

    return traced_broadcast
