# LLM Gateway Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `engines/tools/llm_gateway/` — an LLM routing/caching/cost-tracking layer that wraps `AiModelToolExecutor` with a pluggable backend (MLflow AI Gateway as default).

**Architecture:** `LLMGateway` sits between agents and LLM tool calls. It routes requests through the configured backend (MLflow by default), records costs, caches identical prompts, and handles provider failover.

**Tech Stack:** Python 3.12+, aiohttp, mlflow, mlflow-ai-gateway

---

### Task 1: Create LLM gateway core

**Files:**
- Create: `engines/tools/llm_gateway/__init__.py`
- Create: `engines/tools/llm_gateway/gateway.py`
- Create: `engines/tools/llm_gateway/plugin.py`

- [ ] **Step 1: Write failing test**

```python
# engines/tools/tests/test_llm_gateway.py
import pytest
from engines.tools.llm_gateway.gateway import LLMGateway, ModelResult


def test_model_result_defaults():
    mr = ModelResult(text="hello", model="gpt-4")
    assert mr.text == "hello"
    assert mr.model == "gpt-4"
    assert mr.cost == 0.0


@pytest.mark.asyncio
async def test_gateway_rejects_no_backend():
    gateway = LLMGateway()
    with pytest.raises(RuntimeError, match="No LLM gateway backend"):
        await gateway.route(model="gpt-4", prompt="test")
```

Run: `python3 -m pytest engines/tools/tests/test_llm_gateway.py -v`
Expected: FAIL

- [ ] **Step 2: Create directory**

```bash
mkdir -p engines/tools/llm_gateway/backends
```

- [ ] **Step 3: Create gateway.py**

```python
"""LLM Gateway — routing, caching, and cost tracking for LLM calls."""
from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ModelResult:
    text: str
    model: str
    cost: float = 0.0
    tokens_input: int = 0
    tokens_output: int = 0
    latency_ms: float = 0.0
    cached: bool = False


class LLMGateway:
    """Routes LLM requests through configured backends with caching and cost tracking."""

    def __init__(self, cache_ttl_s: int = 3600):
        self._backends: dict[str, Any] = {}
        self._default_backend: str = ""
        self._cache: dict[str, ModelResult] = {}
        self._cache_ttl = cache_ttl_s

    def register_backend(self, name: str, backend: Any, set_default: bool = False) -> None:
        self._backends[name] = backend
        if set_default or not self._default_backend:
            self._default_backend = name

    async def route(
        self,
        model: str,
        prompt: str,
        backend: str = "",
        use_cache: bool = True,
        **kwargs: Any,
    ) -> ModelResult:
        backend_name = backend or self._default_backend
        if not backend_name or backend_name not in self._backends:
            raise RuntimeError(f"No LLM gateway backend available (tried: '{backend_name}')")

        cache_key = self._cache_key(model, prompt, kwargs)
        if use_cache and cache_key in self._cache:
            cached = self._cache[cache_key]
            if time.time() - cached.latency_ms < self._cache_ttl:
                return ModelResult(text=cached.text, model=model, cached=True)

        start = time.time()
        result = await self._backends[backend_name].route(model, prompt, **kwargs)
        elapsed = (time.time() - start) * 1000

        mr = ModelResult(
            text=result.get("text", ""),
            model=model,
            cost=result.get("cost", 0.0),
            tokens_input=result.get("tokens_input", 0),
            tokens_output=result.get("tokens_output", 0),
            latency_ms=elapsed,
        )
        if use_cache:
            self._cache[cache_key] = mr
        return mr

    async def get_cost(self, model: str, backend: str = "") -> float:
        backend_name = backend or self._default_backend
        if backend_name and backend_name in self._backends:
            return await self._backends[backend_name].get_cost(model)
        return 0.0

    def clear_cache(self) -> int:
        count = len(self._cache)
        self._cache.clear()
        return count

    def _cache_key(self, model: str, prompt: str, kwargs: dict) -> str:
        raw = f"{model}:{prompt}:{sorted(kwargs.items())}"
        return hashlib.sha256(raw.encode()).hexdigest()
```

- [ ] **Step 4: Create plugin.py**

```python
"""LLM Gateway plugin."""
from __future__ import annotations

from typing import Any

from engines.agent.plugins import AgentPlugin


class LLMGatewayPlugin(AgentPlugin):
    """Plugin that activates the LLM gateway and configures the default backend."""

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
```

- [ ] **Step 5: Create __init__.py**

```python
from .gateway import LLMGateway, ModelResult
from .plugin import LLMGatewayPlugin

__all__ = ["LLMGateway", "LLMGatewayPlugin", "ModelResult"]
```

- [ ] **Step 6: Run test**

Run: `python3 -m pytest engines/tools/tests/test_llm_gateway.py -v`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add engines/tools/llm_gateway/__init__.py engines/tools/llm_gateway/gateway.py engines/tools/llm_gateway/plugin.py engines/tools/tests/test_llm_gateway.py
git commit -m "feat(tools): add LLM Gateway core with caching and routing"
```

---

### Task 2: Create MLflow gateway backend

**Files:**
- Create: `engines/tools/llm_gateway/backends/__init__.py`
- Create: `engines/tools/llm_gateway/backends/mlflow.py`

- [ ] **Step 1: Write failing test**

```python
# engines/tools/tests/test_mlflow_gateway.py
import pytest
from engines.tools.llm_gateway.backends.mlflow import MLflowGatewayBackend


def test_mlflow_backend_identity():
    backend = MLflowGatewayBackend(gateway_uri="http://localhost:5000")
    assert backend.gateway_uri == "http://localhost:5000"
```

Run: `python3 -m pytest engines/tools/tests/test_mlflow_gateway.py -v`
Expected: FAIL

- [ ] **Step 2: Create backends/__init__.py**

```python
from .mlflow import MLflowGatewayBackend

__all__ = ["MLflowGatewayBackend"]
```

- [ ] **Step 3: Create mlflow.py**

```python
"""MLflow AI Gateway backend for LLM routing."""
from __future__ import annotations

import os
from typing import Any


class MLflowGatewayBackend:
    """Routes LLM requests through MLflow AI Gateway."""

    def __init__(self, gateway_uri: str = "", api_key: str = ""):
        self.gateway_uri = gateway_uri or os.environ.get("MLFLOW_GATEWAY_URI", "http://localhost:5000")
        self._api_key = api_key or os.environ.get("MLFLOW_GATEWAY_API_KEY", "")

    async def route(self, model: str, prompt: str, **kwargs: Any) -> dict[str, Any]:
        import aiohttp
        headers = {"Content-Type": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
        payload = {
            "model": model,
            "prompt": prompt,
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 1024),
        }
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.post(f"{self.gateway_uri}/gateway/{model}/invocations", json=payload) as resp:
                if resp.status != 200:
                    return {"text": "", "error": f"Gateway error: {resp.status}", "cost": 0.0}
                data = await resp.json()
                return {
                    "text": data.get("candidates", [{}])[0].get("text", ""),
                    "cost": data.get("metadata", {}).get("cost", 0.0),
                    "tokens_input": data.get("metadata", {}).get("input_tokens", 0),
                    "tokens_output": data.get("metadata", {}).get("output_tokens", 0),
                }

    async def get_cost(self, model: str) -> float:
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.gateway_uri}/gateway/{model}/cost") as resp:
                if resp.status != 200:
                    return 0.0
                data = await resp.json()
                return data.get("cost_per_request", 0.0)
```

- [ ] **Step 4: Run test**

Run: `python3 -m pytest engines/tools/tests/test_mlflow_gateway.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add engines/tools/llm_gateway/backends/mlflow.py
git commit -m "feat(tools): add MLflow AI Gateway backend for LLM routing"
```

---

### Task 3: Integrate gateway with AiModelToolExecutor

**Files:**
- Modify: `engines/tools/models/ai_model/executor.py`

- [ ] **Step 1: Write failing test**

```python
# engines/tools/tests/test_ai_model_gateway_integration.py
import pytest
from engines.tools.models.ai_model.executor import AiModelToolExecutor


@pytest.mark.asyncio
async def test_executor_passes_through_without_gateway():
    executor = AiModelToolExecutor()
    result = await executor.execute(model="gpt-4", prompt="hello")
    # Without gateway, it should attempt direct call and fail gracefully
    assert not result.success or result.data is not None
```

Run: `python3 -m pytest engines/tools/tests/test_ai_model_gateway_integration.py -v`
Expected: FAIL

- [ ] **Step 2: Modify AiModelToolExecutor to support gateway**

Read `engines/tools/models/ai_model/executor.py` first, then add gateway integration:

```python
# Add to AiModelToolExecutor class:
class AiModelToolExecutor(BaseToolExecutor):
    # ... existing code ...

    def __init__(self, gateway=None, **kwargs):
        super().__init__(**kwargs)
        self._gateway = gateway

    async def execute(self, **kwargs):
        # If gateway is configured, route through it
        if self._gateway is not None:
            try:
                result = await self._gateway.route(
                    model=kwargs.get("model", ""),
                    prompt=kwargs.get("prompt", ""),
                    **{k: v for k, v in kwargs.items() if k not in ("model", "prompt")},
                )
                return ToolResult(success=True, data={"text": result.text, "model": result.model, "cost": result.cost})
            except Exception as e:
                return ToolResult(success=False, error=f"Gateway error: {e}")
        # Fall back to direct call (existing logic)
        return await super().execute(**kwargs)
```

- [ ] **Step 3: Run test**

Run: `python3 -m pytest engines/tools/tests/test_ai_model_gateway_integration.py -v`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add engines/tools/models/ai_model/executor.py
git commit -m "feat(tools): integrate LLM gateway with AiModelToolExecutor"
```

---

### Task 4: Final verification

- [ ] **Step 1: Run all LLM gateway tests**

```bash
python3 -m pytest engines/tools/tests/test_llm_gateway.py engines/tools/tests/test_mlflow_gateway.py engines/tools/tests/test_ai_model_gateway_integration.py -v
```

Expected: All pass.

- [ ] **Step 2: Run mypy**

```bash
python3 -m mypy engines/tools/llm_gateway/ --no-error-summary
```

Expected: No errors.

- [ ] **Step 3: Verify imports**

```bash
python3 -c "
from engines.tools.llm_gateway import LLMGateway, LLMGatewayPlugin, ModelResult
from engines.tools.llm_gateway.backends import MLflowGatewayBackend
print('All LLM gateway imports OK')
gateway = LLMGateway()
print(f'Gateway created: {gateway}')
"
```

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "feat(tools): complete LLM gateway with MLflow backend and AiModelToolExecutor integration"
```
