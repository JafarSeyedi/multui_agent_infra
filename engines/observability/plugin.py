from __future__ import annotations

from typing import Any

from engines.agent.plugins import AgentPlugin


class ObservabilityPlugin(AgentPlugin):
    def __init__(self, config: dict[str, Any] | None = None):
        self._config = config or {}
        self._backend = None
        self._wrapped_registries: dict[str, Any] = {}

    def plugin_id(self) -> str:
        return "observability"

    def plugin_type(self) -> str:
        return "SKILL"

    def activate(self, registry: Any) -> None:
        from .core.loader import discover_trace_definitions, load_config
        config = load_config()
        backend_name = config.get("backend", "agentops")
        self._backend = self._create_backend(backend_name, config.get(backend_name, {}))

        trace_defs = discover_trace_definitions()

        for engine_name, defs in trace_defs.items():
            spans = defs.get("spans", [])
            for span_def in spans:
                span_name = span_def["name"]
                self._register_instrumentation(engine_name, span_name, span_def)

    def deactivate(self) -> None:
        if self._backend is not None:
            import asyncio
            try:
                asyncio.ensure_future(self._backend.shutdown())
            except Exception:
                pass

    def _create_backend(self, name: str, backend_config: dict[str, Any]) -> Any:
        backends = {
            "agentops": ("engines.observability.backends.agentops", "AgentOpsBackend"),
            "datadog": ("engines.observability.backends.datadog", "DatadogBackend"),
            "mlflow": ("engines.observability.backends.mlflow", "MLflowBackend"),
            "weave": ("engines.observability.backends.weave", "WeaveBackend"),
            "arize": ("engines.observability.backends.arize", "ArizeBackend"),
            "freeplay": ("engines.observability.backends.freeplay", "FreeplayBackend"),
            "future_agi": ("engines.observability.backends.future_agi", "FutureAGIBackend"),
            "langwatch": ("engines.observability.backends.langwatch", "LangWatchBackend"),
            "grafana": ("engines.observability.backends.grafana", "GrafanaBackend"),
        }
        mod_path, cls_name = backends.get(name, backends["agentops"])
        import importlib
        mod = importlib.import_module(mod_path)
        cls = getattr(mod, cls_name)
        return cls(**backend_config)

    def _register_instrumentation(self, engine_name: str, span_name: str, span_def: dict) -> None:
        self._wrapped_registries.setdefault(engine_name, []).append(span_def)
