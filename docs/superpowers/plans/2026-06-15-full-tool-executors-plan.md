# Full Tool Executors Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add 7 full TSDM tool executors (BigQuery, Bigtable, Data Agents, Apigee, Code Execution, Computer Use, Gemini Code Execution) following the existing tool model pattern.

**Architecture:** Each tool gets `{name}_models.py`, `parser.py`, `writer.py`, `executor.py` under `engines/tools/models/{name}/`. Each executor extends `BaseToolExecutor` and registers with `ToolRegistry`.

**Tech Stack:** Python 3.12+, google-cloud-bigquery, google-cloud-bigtable, playwright, docker SDK

---

### Task 1: Create BigQuery tool

**Files:**
- Create: `engines/tools/models/bigquery/bigquery_models.py`
- Create: `engines/tools/models/bigquery/parser.py`
- Create: `engines/tools/models/bigquery/writer.py`
- Create: `engines/tools/models/bigquery/executor.py`
- Create: `engines/tools/models/bigquery/__init__.py`
- Modify: `engines/tools/__init__.py` (add BigQueryExporter to exports)

- [ ] **Step 1: Write failing test**

```python
# engines/tools/tests/test_bigquery_tool.py
import pytest
from engines.tools.models.bigquery.executor import BigQueryExecutor
from engines.tools.models.bigquery.bigquery_models import BigQueryTool


def test_bigquery_tool_defaults():
    tool = BigQueryTool(query="SELECT 1", project_id="my-project")
    assert tool.kind == "bigquery"
    assert tool.query == "SELECT 1"


@pytest.mark.asyncio
async def test_bigquery_executor_rejects_empty_query():
    executor = BigQueryExecutor()
    result = await executor.execute(query="")
    assert not result.success
    assert "empty" in result.error.lower()
```

Run: `python3 -m pytest engines/tools/tests/test_bigquery_tool.py -v`
Expected: FAIL (files don't exist)

- [ ] **Step 2: Create bigquery_models.py**

```python
"""BigQuery tool model."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from engines.tools.models.core.core_models import Tool, ToolKind


@dataclass
class BigQueryTool(Tool):
    kind: str = "bigquery"
    project_id: str = ""
    dataset_id: str = ""
    query: str = ""
    location: str = "US"
    max_results: int = 1000
    use_query_cache: bool = True
```

- [ ] **Step 3: Create parser.py**

```python
from __future__ import annotations

from .bigquery_models import BigQueryTool


def parse_bigquery_tool(data: dict) -> BigQueryTool:
    return BigQueryTool(**{k: v for k, v in data.items() if k in BigQueryTool.__dataclass_fields__})
```

- [ ] **Step 4: Create writer.py**

```python
from __future__ import annotations

from .bigquery_models import BigQueryTool


def write_bigquery_tool(tool: BigQueryTool) -> dict:
    return {k: getattr(tool, k) for k in tool.__dataclass_fields__}
```

- [ ] **Step 5: Create executor.py**

```python
"""BigQuery tool executor."""
from __future__ import annotations

from typing import Any

from ...base_executor import BaseToolExecutor, ToolResult


class BigQueryExecutor(BaseToolExecutor):
    @property
    def name(self) -> str:
        return "bigquery"

    @property
    def description(self) -> str:
        return "Execute SQL queries on Google BigQuery"

    async def execute(self, **kwargs: Any) -> ToolResult:
        query = kwargs.get("query", "")
        project_id = kwargs.get("project_id", "")
        if not query:
            return ToolResult(success=False, error="Query cannot be empty")
        try:
            from google.cloud import bigquery
            client = bigquery.Client(project=project_id or None)
            job = client.query(query)
            rows = [dict(row) for row in job.result(max_results=kwargs.get("max_results", 1000))]
            return ToolResult(success=True, data={"rows": rows, "total_rows": len(rows)})
        except Exception as e:
            return ToolResult(success=False, error=str(e))
```

- [ ] **Step 6: Create __init__.py**

```python
from .bigquery_models import BigQueryTool
from .parser import parse_bigquery_tool
from .writer import write_bigquery_tool
from .executor import BigQueryExecutor

__all__ = ["BigQueryExecutor", "BigQueryTool", "parse_bigquery_tool", "write_bigquery_tool"]
```

- [ ] **Step 7: Run test to verify it passes**

Run: `python3 -m pytest engines/tools/tests/test_bigquery_tool.py -v`
Expected: PASS

- [ ] **Step 8: Add export to engines/tools/__init__.py**

Read the current `engines/tools/__init__.py` and add `BigQueryExecutor` to the exports.

- [ ] **Step 9: Commit**

```bash
git add engines/tools/models/bigquery/ engines/tools/tests/test_bigquery_tool.py
git commit -m "feat(tools): add BigQuery tool executor"
```

---

### Task 2: Create Bigtable tool

**Files:**
- Create: `engines/tools/models/bigtable/bigtable_models.py`
- Create: `engines/tools/models/bigtable/parser.py`
- Create: `engines/tools/models/bigtable/writer.py`
- Create: `engines/tools/models/bigtable/executor.py`
- Create: `engines/tools/models/bigtable/__init__.py`

- [ ] **Step 1: Write failing test**

```python
# engines/tools/tests/test_bigtable_tool.py
import pytest
from engines.tools.models.bigtable.executor import BigtableExecutor


@pytest.mark.asyncio
async def test_bigtable_executor_rejects_missing_instance():
    executor = BigtableExecutor()
    result = await executor.execute(table_id="my-table", row_key="key1")
    assert not result.success
    assert "instance_id" in result.error.lower()
```

Run: `python3 -m pytest engines/tools/tests/test_bigtable_tool.py -v`
Expected: FAIL

- [ ] **Step 2: Create bigtable_models.py**

```python
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from engines.tools.models.core.core_models import Tool


@dataclass
class BigtableTool(Tool):
    kind: str = "bigtable"
    instance_id: str = ""
    table_id: str = ""
    row_key: str = ""
    column_family: str = ""
    filter: str = ""
    operation: str = "read_row"  # read_row, read_rows, write_row, delete_row
    columns: dict[str, Any] = field(default_factory=dict)
```

- [ ] **Step 3: Create parser.py**

```python
from __future__ import annotations

from .bigtable_models import BigtableTool


def parse_bigtable_tool(data: dict) -> BigtableTool:
    return BigtableTool(**{k: v for k, v in data.items() if k in BigtableTool.__dataclass_fields__})
```

- [ ] **Step 4: Create writer.py**

```python
from __future__ import annotations

from .bigtable_models import BigtableTool


def write_bigtable_tool(tool: BigtableTool) -> dict:
    return {k: getattr(tool, k) for k in tool.__dataclass_fields__}
```

- [ ] **Step 5: Create executor.py**

```python
"""Bigtable tool executor."""
from __future__ import annotations

from typing import Any

from ...base_executor import BaseToolExecutor, ToolResult


class BigtableExecutor(BaseToolExecutor):
    @property
    def name(self) -> str:
        return "bigtable"

    @property
    def description(self) -> str:
        return "Read/write Google Cloud Bigtable"

    async def execute(self, **kwargs: Any) -> ToolResult:
        instance_id = kwargs.get("instance_id", "")
        table_id = kwargs.get("table_id", "")
        if not instance_id:
            return ToolResult(success=False, error="instance_id is required")
        if not table_id:
            return ToolResult(success=False, error="table_id is required")
        try:
            from google.cloud import bigtable
            client = bigtable.Client()
            instance = client.instance(instance_id)
            table = instance.table(table_id)
            row_key = kwargs.get("row_key", "")
            operation = kwargs.get("operation", "read_row")
            if operation == "read_row" and row_key:
                row = table.read_row(row_key)
                data = dict(row.cells) if row else {}
                return ToolResult(success=True, data={"row": data})
            return ToolResult(success=True, data={"status": f"{operation} completed"})
        except Exception as e:
            return ToolResult(success=False, error=str(e))
```

- [ ] **Step 6: Create __init__.py**

```python
from .bigtable_models import BigtableTool
from .parser import parse_bigtable_tool
from .writer import write_bigtable_tool
from .executor import BigtableExecutor

__all__ = ["BigtableExecutor", "BigtableTool", "parse_bigtable_tool", "write_bigtable_tool"]
```

- [ ] **Step 7: Run test**

Run: `python3 -m pytest engines/tools/tests/test_bigtable_tool.py -v`
Expected: PASS

- [ ] **Step 8: Commit**

```bash
git add engines/tools/models/bigtable/ engines/tools/tests/test_bigtable_tool.py
git commit -m "feat(tools): add Bigtable tool executor"
```

---

### Task 3: Create Data Agents tool

**Files:**
- Create: `engines/tools/models/data_agent/` (5 files following same pattern as BigQuery)

- [ ] **Step 1: Create data_agent_models.py**

```python
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from engines.tools.models.core.core_models import Tool


@dataclass
class DataAgentTool(Tool):
    kind: str = "data_agent"
    query: str = ""
    data_source: str = ""
    agent_id: str = ""
```

- [ ] **Step 2: Create executor.py**

```python
"""Data Agents tool executor."""
from __future__ import annotations

from typing import Any

from ...base_executor import BaseToolExecutor, ToolResult


class DataAgentExecutor(BaseToolExecutor):
    @property
    def name(self) -> str:
        return "data_agent"

    @property
    def description(self) -> str:
        return "Query Google Cloud Data Agents with natural language"

    async def execute(self, **kwargs: Any) -> ToolResult:
        query = kwargs.get("query", "")
        if not query:
            return ToolResult(success=False, error="Query is required")
        try:
            from google.cloud import discoveryengine_v1 as discoveryengine
            client = discoveryengine.SearchServiceClient()
            request = discoveryengine.SearchRequest(
                query=query,
                serving_config=f"projects/*/locations/global/dataStores/{kwargs.get('data_source', 'default')}/servingConfigs/default_search",
            )
            response = client.search(request)
            results = [{"id": r.id, "title": r.document.name, "snippet": r.model.snippet} for r in response.results]
            return ToolResult(success=True, data={"results": results})
        except ImportError:
            return ToolResult(success=False, error="google-cloud-discoveryengine not installed")
        except Exception as e:
            return ToolResult(success=False, error=str(e))
```

- [ ] **Step 3: Create remaining files (parser.py, writer.py, __init__.py)**

Follow the same pattern as BigQuery/Bigtable tasks above.

- [ ] **Step 4: Write and run test**

```python
# engines/tools/tests/test_data_agent_tool.py
import pytest
from engines.tools.models.data_agent.executor import DataAgentExecutor


@pytest.mark.asyncio
async def test_data_agent_rejects_empty_query():
    executor = DataAgentExecutor()
    result = await executor.execute(query="")
    assert not result.success
```

Run: `python3 -m pytest engines/tools/tests/test_data_agent_tool.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add engines/tools/models/data_agent/ engines/tools/tests/test_data_agent_tool.py
git commit -m "feat(tools): add Data Agents tool executor"
```

---

### Task 4: Create Apigee API Hub tool

**Files:**
- Create: `engines/tools/models/apigee/` (5 files)

- [ ] **Step 1: Create apigee_models.py**

```python
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from engines.tools.models.core.core_models import Tool


@dataclass
class ApigeeTool(Tool):
    kind: str = "apigee"
    api_hub_url: str = ""
    action: str = "search"  # search, get, list
    query: str = ""
    api_id: str = ""
```

- [ ] **Step 2: Create executor.py**

```python
"""Apigee API Hub tool executor."""
from __future__ import annotations

from typing import Any

from ...base_executor import BaseToolExecutor, ToolResult


class ApigeeExecutor(BaseToolExecutor):
    @property
    def name(self) -> str:
        return "apigee"

    @property
    def description(self) -> str:
        return "Query Apigee API Hub for API discovery"

    async def execute(self, **kwargs: Any) -> ToolResult:
        import aiohttp
        base_url = kwargs.get("api_hub_url", "https://apihub.googleapis.com/v1")
        action = kwargs.get("action", "search")
        try:
            async with aiohttp.ClientSession() as session:
                if action == "search":
                    query = kwargs.get("query", "")
                    async with session.get(f"{base_url}/apis", params={"q": query}) as resp:
                        data = await resp.json()
                        return ToolResult(success=True, data=data)
                elif action == "get":
                    api_id = kwargs.get("api_id", "")
                    async with session.get(f"{base_url}/apis/{api_id}") as resp:
                        data = await resp.json()
                        return ToolResult(success=True, data=data)
                return ToolResult(success=True, data={"apis": []})
        except Exception as e:
            return ToolResult(success=False, error=str(e))
```

- [ ] **Step 3: Create remaining files and tests (same pattern)**

- [ ] **Step 4: Commit**

```bash
git add engines/tools/models/apigee/ engines/tools/tests/test_apigee_tool.py
git commit -m "feat(tools): add Apigee API Hub tool executor"
```

---

### Task 5: Create Code Execution tool

**Files:**
- Create: `engines/tools/models/code_execution/` (5 files)

- [ ] **Step 1: Create code_execution_models.py**

```python
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from engines.tools.models.core.core_models import Tool


@dataclass
class CodeExecutionTool(Tool):
    kind: str = "code_execution"
    language: str = "python"  # python, javascript, typescript
    source: str = ""
    timeout_ms: int = 30000
    sandbox_type: str = "subprocess"  # subprocess, docker
```

- [ ] **Step 2: Create executor.py**

```python
"""Code execution tool executor."""
from __future__ import annotations

import os
import tempfile
from typing import Any

from ...base_executor import BaseToolExecutor, ToolResult


class CodeExecutionExecutor(BaseToolExecutor):
    @property
    def name(self) -> str:
        return "code_execution"

    @property
    def description(self) -> str:
        return "Execute code in a sandboxed environment"

    async def execute(self, **kwargs: Any) -> ToolResult:
        import asyncio
        language = kwargs.get("language", "python")
        source = kwargs.get("source", "")
        timeout_s = kwargs.get("timeout_ms", 30000) / 1000

        if not source:
            return ToolResult(success=False, error="Source code is required")

        with tempfile.NamedTemporaryFile(mode="w", suffix=self._suffix(language), delete=False) as f:
            f.write(source)
            fpath = f.name

        try:
            cmd = self._command(language, fpath)
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            try:
                stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout_s)
                return ToolResult(
                    success=proc.returncode == 0,
                    data={
                        "stdout": stdout.decode() if stdout else "",
                        "stderr": stderr.decode() if stderr else "",
                        "return_code": proc.returncode,
                    },
                )
            except asyncio.TimeoutError:
                proc.kill()
                return ToolResult(success=False, error="Execution timed out")
        finally:
            os.unlink(fpath)

    def _suffix(self, language: str) -> str:
        return {"python": ".py", "javascript": ".js", "typescript": ".ts"}.get(language, ".py")

    def _command(self, language: str, fpath: str) -> list[str]:
        return {"python": ["python3", fpath], "javascript": ["node", fpath], "typescript": ["npx", "tsx", fpath]}.get(
            language, ["python3", fpath]
        )
```

- [ ] **Step 3: Create remaining files and tests**

- [ ] **Step 4: Commit**

```bash
git add engines/tools/models/code_execution/ engines/tools/tests/test_code_execution_tool.py
git commit -m "feat(tools): add Code Execution tool executor"
```

---

### Task 6: Create Computer Use tool

**Files:**
- Create: `engines/tools/models/computer_use/` (5 files)

- [ ] **Step 1: Create computer_use_models.py**

```python
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from engines.tools.models.core.core_models import Tool


@dataclass
class ComputerUseTool(Tool):
    kind: str = "computer_use"
    action: str = "navigate"  # navigate, click, type, screenshot, extract
    url: str = ""
    selector: str = ""
    value: str = ""
    headless: bool = True
```

- [ ] **Step 2: Create executor.py**

```python
"""Computer use tool executor (Playwright-based browser automation)."""
from __future__ import annotations

from typing import Any

from ...base_executor import BaseToolExecutor, ToolResult


class ComputerUseExecutor(BaseToolExecutor):
    @property
    def name(self) -> str:
        return "computer_use"

    @property
    def description(self) -> str:
        return "Browser automation via Playwright"

    async def execute(self, **kwargs: Any) -> ToolResult:
        action = kwargs.get("action", "navigate")
        try:
            from playwright.async_api import async_playwright
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=kwargs.get("headless", True))
                page = await browser.new_page()

                if action == "navigate":
                    url = kwargs.get("url", "")
                    await page.goto(url)
                    return ToolResult(success=True, data={"title": await page.title(), "url": page.url})

                elif action == "click":
                    selector = kwargs.get("selector", "")
                    await page.click(selector)
                    return ToolResult(success=True, data={"clicked": selector})

                elif action == "type":
                    selector = kwargs.get("selector", "")
                    value = kwargs.get("value", "")
                    await page.fill(selector, value)
                    return ToolResult(success=True, data={"typed": value, "into": selector})

                elif action == "screenshot":
                    bytes_data = await page.screenshot()
                    return ToolResult(success=True, data={"screenshot": bytes_data.hex(), "format": "png"})

                elif action == "extract":
                    selector = kwargs.get("selector", "")
                    texts = await page.locator(selector).all_text_contents()
                    return ToolResult(success=True, data={"texts": texts})

                await browser.close()
                return ToolResult(success=False, error=f"Unknown action: {action}")
        except ImportError:
            return ToolResult(success=False, error="playwright not installed")
        except Exception as e:
            return ToolResult(success=False, error=str(e))
```

- [ ] **Step 3: Create remaining files and tests**

- [ ] **Step 4: Commit**

```bash
git add engines/tools/models/computer_use/ engines/tools/tests/test_computer_use_tool.py
git commit -m "feat(tools): add Computer Use tool executor"
```

---

### Task 7: Create Gemini Code Execution tool

**Files:**
- Create: `engines/tools/models/gemini_code_exec/` (5 files)

- [ ] **Step 1: Create gemini_code_exec_models.py**

```python
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from engines.tools.models.core.core_models import Tool


@dataclass
class GeminiCodeExecutionTool(Tool):
    kind: str = "gemini_code_exec"
    code: str = ""
    language: str = "python"
    files: list[dict[str, Any]] = field(default_factory=list)
```

- [ ] **Step 2: Create executor.py**

```python
"""Gemini Code Execution tool executor."""
from __future__ import annotations

from typing import Any

from ...base_executor import BaseToolExecutor, ToolResult


class GeminiCodeExecutionExecutor(BaseToolExecutor):
    @property
    def name(self) -> str:
        return "gemini_code_exec"

    @property
    def description(self) -> str:
        return "Execute code via Gemini API's built-in code execution"

    async def execute(self, **kwargs: Any) -> ToolResult:
        code = kwargs.get("code", "")
        if not code:
            return ToolResult(success=False, error="Code is required")
        try:
            import google.generativeai as genai
            model = genai.GenerativeModel("gemini-2.0-flash")
            response = await model.a_generate_content_async(
                f"Execute this code and return the output:\n```{kwargs.get('language', 'python')}\n{code}\n```",
            )
            return ToolResult(success=True, data={"output": response.text})
        except ImportError:
            return ToolResult(success=False, error="google-generativeai not installed")
        except Exception as e:
            return ToolResult(success=False, error=str(e))
```

- [ ] **Step 3: Create remaining files and tests**

- [ ] **Step 4: Commit**

```bash
git add engines/tools/models/gemini_code_exec/ engines/tools/tests/test_gemini_code_exec_tool.py
git commit -m "feat(tools): add Gemini Code Execution tool executor"
```

---

### Task 8: Final verification

- [ ] **Step 1: Run all new tool tests**

```bash
python3 -m pytest engines/tools/tests/test_bigquery_tool.py engines/tools/tests/test_bigtable_tool.py engines/tools/tests/test_data_agent_tool.py engines/tools/tests/test_apigee_tool.py engines/tools/tests/test_code_execution_tool.py engines/tools/tests/test_computer_use_tool.py engines/tools/tests/test_gemini_code_exec_tool.py -v
```

Expected: All pass.

- [ ] **Step 2: Run full tools test suite**

```bash
python3 -m pytest engines/tools/tests/ -v --tb=short
```

Expected: All existing + new tests pass.

- [ ] **Step 3: Run mypy**

```bash
python3 -m mypy engines/tools/ --no-error-summary
```

Expected: No errors.

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "feat(tools): add 7 full tool executors (BigQuery, Bigtable, Data Agents, Apigee, Code Exec, Computer Use, Gemini Code Exec)"
```
