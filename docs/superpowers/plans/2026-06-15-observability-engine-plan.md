# Observability Engine Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `engines/observability/` — a cross-cutting observability engine that instruments all other engines (agent, orchestration, tools, communication, knowledge, memory, storage) via proxy wrappers and pluggable backends.

**Architecture:** Each engine declares trace points in `trace_definitions.yaml`. The ObservabilityPlugin discovers these at startup and wraps key registry/executor objects with tracing proxies. Backend adapters (AgentOps default, plus Datadog, MLflow, etc.) implement the `ObservabilityBackend` ABC.

**Tech Stack:** Python 3.12+, AgentOps SDK, ddtrace, mlflow, wandb, openinference, asyncio

---

### Task 1: Create core observability types and backend ABC

**Files:**
- Create: `engines/observability/__init__.py`
- Create: `engines/observability/core/__init__.py`
- Create: `engines/observability/core/types.py`
- Create: `engines/observability/core/backends.py`

- [ ] **Step 1: Write failing test**

```python
# engines/observability/tests/test_core.py
import pytest
from engines.observability.core.types import Span, Metric, Event
from engines.observability.core.backends import ObservabilityBackend


def test_span_defaults():
    span = Span(name="test.operation")
    assert span.name == "test.operation"
    assert span.attributes == {}
    assert span.status == "ok"


def test_backend_is_abstract():
    with pytest.raises(TypeError):
        ObservabilityBackend()
```

Run: `python3 -m pytest engines/observability/tests/test_core.py -v`
Expected: FAIL (files don't exist)

- [ ] **Step 2: Create engines/observability/ directory**

```bash
mkdir -p engines/observability/core engines/observability/backends engines/observability/config engines/observability/tests
```

- [ ] **Step 3: Create __init__.py**

```python
from .core.backends import ObservabilityBackend
from .core.types import Span, Metric, Event
from .plugin import ObservabilityPlugin

__all__ = ["Event", "Metric", "ObservabilityBackend", "ObservabilityPlugin", "Span"]
```

- [ ] **Step 4: Create types.py**

```python
"""Observability data types."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class Span:
    name: str
    attributes: dict[str, Any] = field(default_factory=dict)
    status: str = "ok"
    start_time: float = 0.0
    end_time: float = 0.0
    parent_id: str = ""
    span_id: str = ""
    trace_id: str = ""


@dataclass
class Metric:
    name: str
    value: float = 0.0
    type: str = "counter"  # counter, histogram, gauge
    tags: dict[str, str] = field(default_factory=dict)
    timestamp: float = 0.0


@dataclass
class Event:
    name: str
    attributes: dict[str, Any] = field(default_factory=dict)
    timestamp: float = 0.0
    severity: str = "info"
```

- [ ] **Step 5: Create backends.py**

```python
"""Observability backend abstraction."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class ObservabilityBackend(ABC):
    """Abstract backend for observability data."""

    @abstractmethod
    async def start_span(self, name: str, attributes: dict[str, Any] | None = None) -> Any:
        ...

    @abstractmethod
    async def end_span(self, span: Any, status: str = "ok") -> None:
        ...

    @abstractmethod
    async def record_metric(self, name: str, value: float, tags: dict[str, str] | None = None) -> None:
        ...

    @abstractmethod
    async def record_event(self, name: str, attributes: dict[str, Any] | None = None) -> None:
        ...

    async def shutdown(self) -> None:
        """Gracefully shut down the backend."""
```

- [ ] **Step 6: Create core/__init__.py**

```python
from .types import Event, Metric, Span
from .backends import ObservabilityBackend

__all__ = ["Event", "Metric", "ObservabilityBackend", "Span"]
```

- [ ] **Step 7: Run test**

Run: `python3 -m pytest engines/observability/tests/test_core.py -v`
Expected: PASS

- [ ] **Step 8: Commit**

```bash
git add engines/observability/__init__.py engines/observability/core/ engines/observability/tests/test_core.py
git commit -m "feat(observability): add core types and backend ABC"
```

---

### Task 2: Create AgentOps backend (default)

**Files:**
- Create: `engines/observability/backends/__init__.py`
- Create: `engines/observability/backends/agentops.py`

- [ ] **Step 1: Write failing test**

```python
# engines/observability/tests/test_backends.py
import pytest
from engines.observability.backends.agentops import AgentOpsBackend


@pytest.mark.asyncio
async def test_agentops_connect_and_shutdown():
    backend = AgentOpsBackend(api_key="test-key")
    await backend.shutdown()
```

Run: `python3 -m pytest engines/observability/tests/test_backends.py -v`
Expected: FAIL

- [ ] **Step 2: Create backends/__init__.py**

```python
from .agentops import AgentOpsBackend

__all__ = ["AgentOpsBackend"]
```

- [ ] **Step 3: Create agentops.py**

```python
"""AgentOps observability backend."""
from __future__ import annotations

import os
from typing import Any

from ..core.backends import ObservabilityBackend


class AgentOpsBackend(ObservabilityBackend):
    """Observability backend using AgentOps (default)."""

    def __init__(self, api_key: str = ""):
        self._api_key = api_key or os.environ.get("AGENTOPS_API_KEY", "")
        self._client = None

    async def start_span(self, name: str, attributes: dict[str, Any] | None = None) -> Any:
        try:
            import agentops
            if self._client is None:
                self._client = agentops
                self._client.init(api_key=self._api_key)
            return self._client.start_span(name, attributes or {})
        except ImportError:
            return None

    async def end_span(self, span: Any, status: str = "ok") -> None:
        if span is not None:
            try:
                import agentops
                agentops.end_span(span, status=status)
            except ImportError:
                pass

    async def record_metric(self, name: str, value: float, tags: dict[str, str] | None = None) -> None:
        try:
            import agentops
            agentops.record_metric(name, value, tags or {})
        except ImportError:
            pass

    async def record_event(self, name: str, attributes: dict[str, Any] | None = None) -> None:
        try:
            import agentops
            agentops.record_event(name, attributes or {})
        except ImportError:
            pass

    async def shutdown(self) -> None:
        if self._client is not None:
            try:
                self._client.end_session("Success")
            except Exception:
                pass
            self._client = None
```

- [ ] **Step 4: Run test**

Run: `python3 -m pytest engines/observability/tests/test_backends.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add engines/observability/backends/agentops.py
git commit -m "feat(observability): add AgentOps backend (default)"
```

---

### Task 3: Create remaining backend stubs

**Files:**
- Create: `engines/observability/backends/datadog.py`
- Create: `engines/observability/backends/mlflow.py`
- Create: `engines/observability/backends/weave.py`
- Create: `engines/observability/backends/arize.py`
- Create: `engines/observability/backends/freeplay.py`
- Create: `engines/observability/backends/future_agi.py`
- Create: `engines/observability/backends/langwatch.py`
- Create: `engines/observability/backends/grafana.py`

- [ ] **Step 1: Create each backend as a minimal adapter extending ObservabilityBackend**

Each follows the same pattern (example: datadog.py):
```python
"""Datadog observability backend."""
from __future__ import annotations

from typing import Any

from ..core.backends import ObservabilityBackend


class DatadogBackend(ObservabilityBackend):
    def __init__(self, api_key: str = ""):
        self._api_key = api_key

    async def start_span(self, name: str, attributes: dict[str, Any] | None = None) -> Any:
        try:
            from ddtrace import tracer
            return tracer.trace(name, resource=name)
        except ImportError:
            return None

    async def end_span(self, span: Any, status: str = "ok") -> None:
        if span is not None:
            try:
                span.finish()
            except Exception:
                pass

    async def record_metric(self, name: str, value: float, tags: dict[str, str] | None = None) -> None:
        try:
            from ddtrace import statsd
            statsd.gauge(name, value, tags=tags or {})
        except ImportError:
            pass

    async def record_event(self, name: str, attributes: dict[str, Any] | None = None) -> None:
        pass

    async def shutdown(self) -> None:
        pass
```

Create all 8 backends with the same structure but different SDK imports:
- `mlflow.py` — uses `mlflow.start_span`, `mlflow.end_span`
- `weave.py` — uses `wandb.Weave`
- `arize.py` — uses `openinference`
- `freeplay.py` — uses Freeplay SDK
- `future_agi.py` — uses Future AGI SDK
- `langwatch.py` — uses LangWatch SDK
- `grafana.py` — uses Grafana Cloud OTLP endpoint via `opentelemetry`

- [ ] **Step 2: Update backends/__init__.py**

```python
from .agentops import AgentOpsBackend
from .datadog import DatadogBackend
from .mlflow import MLflowBackend
from .weave import WeaveBackend
from .arize import ArizeBackend
from .freeplay import FreeplayBackend
from .future_agi import FutureAGIBackend
from .langwatch import LangWatchBackend
from .grafana import GrafanaBackend

__all__ = [
    "AgentOpsBackend",
    "ArizeBackend",
    "DatadogBackend",
    "FreeplayBackend",
    "FutureAGIBackend",
    "GrafanaBackend",
    "LangWatchBackend",
    "MLflowBackend",
    "WeaveBackend",
]
```

- [ ] **Step 3: Run import test**

```bash
python3 -c "from engines.observability.backends import AgentOpsBackend, DatadogBackend, MLflowBackend; print('all backends import OK')"
```

Expected: OK

- [ ] **Step 4: Commit**

```bash
git add engines/observability/backends/
git commit -m "feat(observability): add 8 remaining backend adapters (Datadog, MLflow, Weave, Arize, Freeplay, Future AGI, LangWatch, Grafana)"
```

---

### Task 4: Create trace definition loader and config

**Files:**
- Create: `engines/observability/core/loader.py`
- Create: `engines/observability/config/observability.yaml`

- [ ] **Step 1: Write failing test**

```python
# engines/observability/tests/test_loader.py
import pytest
from engines.observability.core.loader import discover_trace_definitions


def test_discover_trace_definitions_returns_dict():
    defs = discover_trace_definitions()
    assert isinstance(defs, dict)
```

Run: `python3 -m pytest engines/observability/tests/test_loader.py -v`
Expected: FAIL

- [ ] **Step 2: Create loader.py**

```python
"""Discover and load trace_definitions.yaml from all engines."""
from __future__ import annotations

import os
from typing import Any

import yaml


_ENGINES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
_OBSERVABILITY_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def discover_trace_definitions() -> dict[str, dict[str, Any]]:
    """Scan all engine directories for trace_definitions.yaml files."""
    definitions: dict[str, dict[str, Any]] = {}
    if not os.path.isdir(_ENGINES_DIR):
        return definitions
    for engine_name in sorted(os.listdir(_ENGINES_DIR)):
        engine_path = os.path.join(_ENGINES_DIR, engine_name)
        trace_file = os.path.join(engine_path, "trace_definitions.yaml")
        if os.path.isfile(trace_file):
            with open(trace_file) as f:
                data = yaml.safe_load(f)
            if isinstance(data, dict):
                definitions[engine_name] = data
    return definitions


def load_config() -> dict[str, Any]:
    """Load observability config."""
    config_path = os.path.join(_OBSERVABILITY_DIR, "config", "observability.yaml")
    if os.path.isfile(config_path):
        with open(config_path) as f:
            return yaml.safe_load(f) or {}
    return {"backend": "agentops"}
```

- [ ] **Step 3: Create config file**

```yaml
# engines/observability/config/observability.yaml
backend: agentops
agentops:
  api_key: ${AGENTOPS_API_KEY}
```

- [ ] **Step 4: Run test**

Run: `python3 -m pytest engines/observability/tests/test_loader.py -v`
Expected: PASS (returns empty dict, no trace files exist yet)

- [ ] **Step 5: Commit**

```bash
git add engines/observability/core/loader.py engines/observability/config/observability.yaml
git commit -m "feat(observability): add trace definition loader and config"
```

---

### Task 5: Create proxy wrappers

**Files:**
- Create: `engines/observability/core/wrappers.py`

- [ ] **Step 1: Write failing test**

```python
# engines/observability/tests/test_wrappers.py
import pytest
from engines.observability.core.wrappers import wrap_registry


class FakeRegistry:
    def __init__(self):
        self.calls = []

    async def run(self, name: str, data: dict) -> dict:
        self.calls.append((name, data))
        return {"result": "ok"}


class FakeBackend:
    def __init__(self):
        self.spans = []

    async def start_span(self, name, attributes=None):
        self.spans.append(("start", name, attributes))
        return "span-1"

    async def end_span(self, span, status="ok"):
        self.spans.append(("end", span, status))

    async def record_metric(self, name, value, tags=None):
        pass

    async def record_event(self, name, attributes=None):
        pass


@pytest.mark.asyncio
async def test_wrap_registry_instruments_run():
    registry = FakeRegistry()
    backend = FakeBackend()
    wrapped = wrap_registry(registry, backend, "agent")
    result = await wrapped.run("test-agent", {"key": "val"})
    assert result == {"result": "ok"}
    assert any("start" in s for s in backend.spans)
    assert any("end" in s for s in backend.spans)
```

Run: `python3 -m pytest engines/observability/tests/test_wrappers.py -v`
Expected: FAIL

- [ ] **Step 2: Create wrappers.py**

```python
"""Proxy wrappers for instrumenting engines with observability."""
from __future__ import annotations

from typing import Any

from .backends import ObservabilityBackend


def wrap_registry(registry: Any, backend: ObservabilityBackend, engine_name: str, trace_defs: dict | None = None) -> Any:
    """Wrap a registry/executor with tracing."""
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
    """Wrap a send/communicate function with tracing."""

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
    """Wrap a broadcast function with tracing."""

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
```

- [ ] **Step 3: Run test**

Run: `python3 -m pytest engines/observability/tests/test_wrappers.py -v`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add engines/observability/core/wrappers.py
git commit -m "feat(observability): add proxy wrappers for engine instrumentation"
```

---

### Task 6: Create ObservabilityPlugin

**Files:**
- Create: `engines/observability/plugin.py`

- [ ] **Step 1: Write failing test**

```python
# engines/observability/tests/test_plugin.py
import pytest
from engines.observability.plugin import ObservabilityPlugin


def test_observability_plugin_identity():
    plugin = ObservabilityPlugin()
    assert plugin.plugin_id() == "observability"
    assert plugin.plugin_type() == "SKILL"
```

Run: `python3 -m pytest engines/observability/tests/test_plugin.py -v`
Expected: FAIL

- [ ] **Step 2: Create plugin.py**

```python
"""Observability plugin — instruments all engines with tracing."""
from __future__ import annotations

from typing import Any

from engines.agent.plugins import AgentPlugin


class ObservabilityPlugin(AgentPlugin):
    """Cross-cutting observability plugin.

    Discovers trace_definitions.yaml from all engines, selects the configured
    backend, and wraps key registry/executor objects with tracing proxies.
    """

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
        # Store trace definitions for later use by wrappers
        self._wrapped_registries.setdefault(engine_name, []).append(span_def)
```

- [ ] **Step 3: Run test**

Run: `python3 -m pytest engines/observability/tests/test_plugin.py -v`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add engines/observability/plugin.py
git commit -m "feat(observability): add ObservabilityPlugin with backend auto-selection"
```

---

### Task 7: Create trace definition files for each engine

- [ ] **Step 1: Create engines/agent/trace_definitions.yaml**

```yaml
engine: agent
spans:
  - name: agent.run
    description: Agent execution
    attributes: [agent_name, workflow_id]
  - name: mediator.send
    description: Agent-to-agent message
    attributes: [sender, recipient]
  - name: mediator.broadcast
    description: Broadcast to all agents
    attributes: [sender]
metrics:
  - name: agent.run.duration_ms
    type: histogram
  - name: agent.run.count
    type: counter
```

- [ ] **Step 2: Create engines/orchestration/trace_definitions.yaml**

```yaml
engine: orchestration
spans:
  - name: workflow.execute
    description: Full workflow execution
    attributes: [workflow_id, instance_id]
  - name: workflow.step
    description: Individual workflow step
    attributes: [step_id, step_type]
  - name: mediator.execute_agent
    description: Agent execution via mediator
    attributes: [agent_id]
metrics:
  - name: workflow.duration_ms
    type: histogram
  - name: workflow.steps.count
    type: counter
```

- [ ] **Step 3: Create engines/tools/trace_definitions.yaml**

```yaml
engine: tools
spans:
  - name: tool.execute
    description: Tool invocation
    attributes: [tool_name, tool_type]
  - name: tool.mcp.call
    description: MCP tool call
    attributes: [tool_name, server]
metrics:
  - name: tool.execute.count
    type: counter
  - name: tool.execute.duration_ms
    type: histogram
  - name: tool.error.count
    type: counter
```

- [ ] **Step 4: Create engines/communication/trace_definitions.yaml**

```yaml
engine: communication
spans:
  - name: message.publish
    description: Message published to bus
    attributes: [message_type, sender, recipient]
  - name: message.subscribe
    description: Subscription registered
    attributes: [recipient]
metrics:
  - name: message.publish.count
    type: counter
  - name: message.publish.duration_ms
    type: histogram
```

- [ ] **Step 5: Create engines/knowledge/trace_definitions.yaml**

```yaml
engine: knowledge
spans:
  - name: knowledge.query
    description: Knowledge base query
    attributes: [engine_name, query_type]
  - name: knowledge.ingest
    description: Document ingestion
    attributes: [engine_name, doc_count]
metrics:
  - name: knowledge.query.count
    type: counter
  - name: knowledge.query.duration_ms
    type: histogram
```

- [ ] **Step 6: Create engines/memory/trace_definitions.yaml**

```yaml
engine: memory
spans:
  - name: memory.store
    description: Memory storage operation
    attributes: [memory_type]
  - name: memory.retrieve
    description: Memory retrieval
    attributes: [memory_type, query]
metrics:
  - name: memory.operation.count
    type: counter
  - name: memory.operation.duration_ms
    type: histogram
```

- [ ] **Step 7: Create engines/storage/trace_definitions.yaml**

```yaml
engine: storage
spans:
  - name: storage.read
    description: Storage read operation
    attributes: [storage_type]
  - name: storage.write
    description: Storage write operation
    attributes: [storage_type]
  - name: storage.delete
    description: Storage delete operation
    attributes: [storage_type]
metrics:
  - name: storage.operation.count
    type: counter
  - name: storage.operation.duration_ms
    type: histogram
```

- [ ] **Step 8: Verify loader discovers all files**

```bash
python3 -c "from engines.observability.core.loader import discover_trace_definitions; d = discover_trace_definitions(); print(f'Found {len(d)} engines with trace defs: {list(d.keys())}')"
```

Expected: Found 7 engines with trace defs: ['agent', 'communication', 'knowledge', 'memory', 'orchestration', 'storage', 'tools']

- [ ] **Step 9: Commit**

```bash
git add engines/agent/trace_definitions.yaml engines/orchestration/trace_definitions.yaml engines/tools/trace_definitions.yaml engines/communication/trace_definitions.yaml engines/knowledge/trace_definitions.yaml engines/memory/trace_definitions.yaml engines/storage/trace_definitions.yaml
git commit -m "feat(observability): add trace definitions for all 7 engines"
```

---

### Task 8: Final verification

- [ ] **Step 1: Run all observability tests**

```bash
python3 -m pytest engines/observability/tests/ -v
```

Expected: All tests pass.

- [ ] **Step 2: Run mypy**

```bash
python3 -m mypy engines/observability/ --no-error-summary
```

Expected: No errors.

- [ ] **Step 3: Verify backend imports**

```bash
python3 -c "
from engines.observability.backends import AgentOpsBackend, DatadogBackend, MLflowBackend
from engines.observability import ObservabilityPlugin, ObservabilityBackend
from engines.observability.core.loader import discover_trace_definitions, load_config
defs = discover_trace_definitions()
print(f'Trace definitions: {len(defs)} engines')
cfg = load_config()
print(f'Config: {cfg}')
print('All observability imports OK')
"
```

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "feat(observability): complete observability engine with plugin, wrappers, backends, and trace definitions"
```
