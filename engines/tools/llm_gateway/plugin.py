from __future__ import annotations

from typing import Any

from engines.agent.plugins import AgentPlugin


class LLMGatewayPlugin(AgentPlugin):
    def __init__(self, config: dict[str, Any] | None = None):
        self._config = config or {}
        self._gateway = None

    def plugin_id(self) -> str:
        return "llm-gateway"

    def plugin_type(self) -> str:
        return "TOOL"

    def activate(self, registry: Any) -> None:
        from .gateway import LLMGateway
        self._gateway = LLMGateway()
        backend_name = self._config.get("backend", "mlflow")
        backend_config = self._config.get(backend_name, {})
        if backend_name == "mlflow":
            from .backends.mlflow import MLflowGatewayBackend
            backend = MLflowGatewayBackend(**backend_config)
            self._gateway.register_backend("mlflow", backend, set_default=True)

    def deactivate(self) -> None:
        self._gateway = None

    def get_gateway(self) -> Any:
        return self._gateway
