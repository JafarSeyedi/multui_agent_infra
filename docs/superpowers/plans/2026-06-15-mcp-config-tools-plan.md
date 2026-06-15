# MCP Config Tools Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add 5 MCP server integration definitions (Dapr, DBOS, Restate, Daytona, Cisco AI Defense) as lightweight YAML configs consumed by a fixed MCPToolExecutor.

**Architecture:** YAML definitions in `engines/tools/models/mcp/definitions/` are auto-discovered by MCPToolExecutor. The executor is fixed to use the real `MCPClient` from `engines/agent/skill/mcp_client.py` instead of returning a stub result.

**Tech Stack:** Python 3.12+, YAML, MCP Python SDK (already installed), asyncio

---

### Task 1: Fix MCPToolExecutor to use real MCPClient

**Files:**
- Modify: `engines/tools/models/mcp/executor.py`
- Modify: `engines/tools/models/mcp/mcp_models.py` (add `server_command` field if missing)

- [ ] **Step 1: Read current MCPToolExecutor**

Read `engines/tools/models/mcp/executor.py` and `engines/tools/models/mcp/mcp_models.py` to understand current state.

- [ ] **Step 2: Write failing test**

```python
# engines/tools/tests/test_mcp_executor.py
import pytest
from engines.tools.models.mcp.executor import MCPToolExecutor


@pytest.mark.asyncio
async def test_mcp_executor_parses_server_command():
    executor = MCPToolExecutor(
        tool_name="test-tool",
        server_command=["echo", '{"result": "hello"}'],
    )
    assert executor.name == "test-tool"
    assert executor.description == "MCP tool: test-tool"


@pytest.mark.asyncio
async def test_mcp_executor_rejects_missing_server_command():
    with pytest.raises(ValueError, match="server_command"):
        MCPToolExecutor(tool_name="bad")
```

Run: `python3 -m pytest engines/tools/tests/test_mcp_executor.py -v`
Expected: FAIL (MCPToolExecutor doesn't exist or lacks these features)

- [ ] **Step 3: Update MCPTool model to include server_command**

In `engines/tools/models/mcp/mcp_models.py`, ensure `MCPTool` has a `server_command: list[str]` field (default `field(default_factory=list)`). Read the file first, then add the field.

- [ ] **Step 4: Rewrite MCPToolExecutor to use real MCPClient**

Replace `engines/tools/models/mcp/executor.py` content:

```python
"""MCP tool executor — delegates to real MCPClient."""

from __future__ import annotations

from typing import Any

from ...base_executor import BaseToolExecutor, ToolResult


class MCPToolExecutor(BaseToolExecutor):
    """Executes a tool via an MCP server using the real MCPClient."""

    def __init__(
        self,
        tool_name: str,
        server_command: list[str] | None = None,
        server_url: str | None = None,
        **kwargs: Any,
    ):
        super().__init__(**kwargs)
        self._name = tool_name
        self._server_command = server_command or []
        self._server_url = server_url
        self._client = None

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return f"MCP tool: {self._name}"

    async def execute(self, **kwargs: Any) -> ToolResult:
        try:
            result = await self._call_mcp(kwargs)
            return ToolResult(success=True, data={"result": result})
        except Exception as e:
            return ToolResult(success=False, error=str(e))

    async def _call_mcp(self, arguments: dict[str, Any]) -> Any:
        from engines.agent.skill.mcp_client import MCPClient

        if self._server_command:
            client = MCPClient(server_command=self._server_command)
        elif self._server_url:
            client = MCPClient(server_url=self._server_url)
        else:
            raise ValueError("MCPToolExecutor requires server_command or server_url")

        try:
            await client.connect()
            result = await client.call_tool(self._name, arguments)
            return result
        finally:
            await client.disconnect()
```

- [ ] **Step 5: Run test to verify it passes**

Run: `python3 -m pytest engines/tools/tests/test_mcp_executor.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add engines/tools/models/mcp/executor.py engines/tools/models/mcp/mcp_models.py engines/tools/tests/test_mcp_executor.py
git commit -m "fix(tools): wire MCPToolExecutor to real MCPClient"
```

---

### Task 2: Add MCP definitions directory + auto-discovery

**Files:**
- Create: `engines/tools/models/mcp/definitions/__init__.py`
- Create: `engines/tools/models/mcp/definitions/loader.py`

- [ ] **Step 1: Write failing test**

```python
# engines/tools/tests/test_mcp_definitions.py
import pytest
from engines.tools.models.mcp.definitions.loader import load_mcp_definitions


def test_load_mcp_definitions_returns_list():
    defs = load_mcp_definitions()
    assert isinstance(defs, list)


def test_load_mcp_definitions_contains_dapr():
    defs = load_mcp_definitions()
    dapr = [d for d in defs if d["id"] == "dapr-mcp"]
    assert len(dapr) == 1
    assert "pubsub" in dapr[0]["tools"]
```

Run: `python3 -m pytest engines/tools/tests/test_mcp_definitions.py -v`
Expected: FAIL (module doesn't exist)

- [ ] **Step 2: Create definitions/__init__.py**

Create empty file `engines/tools/models/mcp/definitions/__init__.py`.

- [ ] **Step 3: Create loader.py**

```python
"""Auto-discover MCP definitions from YAML files in this directory."""

from __future__ import annotations

import os
from typing import Any

import yaml


_DEFINITIONS_DIR = os.path.dirname(os.path.abspath(__file__))


def load_mcp_definitions() -> list[dict[str, Any]]:
    """Load all MCP definition YAML files from the definitions directory."""
    results: list[dict[str, Any]] = []
    if not os.path.isdir(_DEFINITIONS_DIR):
        return results
    for fname in sorted(os.listdir(_DEFINITIONS_DIR)):
        if fname.endswith(".yaml") or fname.endswith(".yml"):
            fpath = os.path.join(_DEFINITIONS_DIR, fname)
            with open(fpath) as f:
                data = yaml.safe_load(f)
            if isinstance(data, dict):
                results.append(data)
    return results


def get_mcp_definition(def_id: str) -> dict[str, Any] | None:
    """Get a specific MCP definition by ID."""
    for d in load_mcp_definitions():
        if d.get("id") == def_id:
            return d
    return None
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest engines/tools/tests/test_mcp_definitions.py -v`
Expected: PASS (currently returns empty list since no YAML files exist yet)

- [ ] **Step 5: Commit**

```bash
git add engines/tools/models/mcp/definitions/ engines/tools/tests/test_mcp_definitions.py
git commit -m "feat(tools): add MCP definition loader with YAML discovery"
```

---

### Task 3: Create Dapr MCP definition

- [ ] **Step 1: Create definition file**

Write `engines/tools/models/mcp/definitions/dapr.yaml`:

```yaml
id: dapr-mcp
name: Dapr
description: Dapr distributed application runtime MCP server
server_command: ["npx", "@dapr/mcp-server"]
tools:
  - pubsub
  - state
  - actors
  - workflows
  - bindings
  - configuration
  - secrets
```

- [ ] **Step 2: Run test**

Run: `python3 -m pytest engines/tools/tests/test_mcp_definitions.py::test_load_mcp_definitions_contains_dapr -v`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add engines/tools/models/mcp/definitions/dapr.yaml
git commit -m "feat(tools): add Dapr MCP definition"
```

---

### Task 4: Create DBOS MCP definition

- [ ] **Step 1: Create definition file**

Write `engines/tools/models/mcp/definitions/dbos.yaml`:

```yaml
id: dbos-mcp
name: DBOS
description: DBOS durable execution framework MCP server
server_command: ["npx", "@dbos/mcp-server"]
tools:
  - workflow
  - step
  - transaction
  - communicator
```

- [ ] **Step 2: Commit**

```bash
git add engines/tools/models/mcp/definitions/dbos.yaml
git commit -m "feat(tools): add DBOS MCP definition"
```

---

### Task 5: Create Restate MCP definition

- [ ] **Step 1: Create definition file**

Write `engines/tools/models/mcp/definitions/restate.yaml`:

```yaml
id: restate-mcp
name: Restate
description: Restate durable execution framework MCP server
server_command: ["npx", "@restate/mcp-server"]
tools:
  - service
  - virtual_object
  - workflow
  - state_machine
  - invocations
```

- [ ] **Step 2: Commit**

```bash
git add engines/tools/models/mcp/definitions/restate.yaml
git commit -m "feat(tools): add Restate MCP definition"
```

---

### Task 6: Create Daytona MCP definition

- [ ] **Step 1: Create definition file**

Write `engines/tools/models/mcp/definitions/daytona.yaml`:

```yaml
id: daytona-mcp
name: Daytona
description: Daytona development sandbox MCP server
server_command: ["npx", "@daytona/mcp-server"]
tools:
  - sandbox
  - environment
  - workspace
  - git
```

- [ ] **Step 2: Commit**

```bash
git add engines/tools/models/mcp/definitions/daytona.yaml
git commit -m "feat(tools): add Daytona MCP definition"
```

---

### Task 7: Create Cisco AI Defense MCP definition

- [ ] **Step 1: Create definition file**

Write `engines/tools/models/mcp/definitions/cisco_ai_defense.yaml`:

```yaml
id: cisco-ai-defense-mcp
name: Cisco AI Defense
description: Cisco AI security and defense MCP server
server_command: ["npx", "@cisco/ai-defense-mcp"]
tools:
  - policy
  - audit
  - threat_detection
  - compliance
```

- [ ] **Step 2: Commit**

```bash
git add engines/tools/models/mcp/definitions/cisco_ai_defense.yaml
git commit -m "feat(tools): add Cisco AI Defense MCP definition"
```

---

### Task 8: Final verification

- [ ] **Step 1: Run all MCP tests**

```bash
python3 -m pytest engines/tools/tests/test_mcp_executor.py engines/tools/tests/test_mcp_definitions.py -v
```

Expected: All tests pass.

- [ ] **Step 2: Run mypy**

```bash
python3 -m mypy engines/tools/models/mcp/ --no-error-summary
```

Expected: No errors.

- [ ] **Step 3: Commit**

```bash
git add -A
git commit -m "feat(tools): finalize MCP config tools with 5 definitions"
```
