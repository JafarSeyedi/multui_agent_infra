# Plugins, Tools, and Observability Design

**Date:** 2026-06-15
**Status:** Draft

## Overview

Extend the unified agent engine with infrastructure and feature-extension plugins across six categories, classified by integration depth:

| Category | Approach | Count | Location |
|----------|----------|-------|----------|
| MCP Config (A) | YAML manifest → existing MCPClient | 5 | `engines/tools/models/mcp/definitions/` |
| Full Tool Executor (C) | TSDM model + executor | 7 | `engines/tools/models/{name}/` |
| Observability System | Cross-engine plugin + backends | 1 plugin + 9 backends | `engines/observability/` |
| TTS/Media System | Plugin system + backends | 1 plugin + 2 backends | `engines/tts/` |
| LLM Gateway System | Plugin system + backend | 1 plugin + 1 backend | `engines/tools/llm_gateway/` |

## Section 1: MCP Config (Option A)

### Tools
- Dapr
- DBOS
- Restate
- Daytona
- Cisco AI Defense

### Design
Each tool gets an MCP definition YAML in `engines/tools/models/mcp/definitions/`:
```yaml
# dapr_mcp.yaml
id: dapr-mcp
name: Dapr
server_command: ["npx", "@dapr/mcp-server"]
tools: [pubsub, state, actors, workflows, bindings]
```

The existing `MCPToolExecutor` (currently a stub) is fixed to use the real `MCPClient` from `engines/agent/skill/mcp_client.py`. The auto-loading reads all `.yaml` files from `definitions/` directory at registry init.

### Files to create/modify
- `engines/tools/models/mcp/definitions/dapr.yaml`
- `engines/tools/models/mcp/definitions/dbos.yaml`
- `engines/tools/models/mcp/definitions/restate.yaml`
- `engines/tools/models/mcp/definitions/daytona.yaml`
- `engines/tools/models/mcp/definitions/cisco_ai_defense.yaml`
- Modify: `engines/tools/models/mcp/executor.py` (wire to real MCPClient)

## Section 2: Full Tool Executor (Option C)

### Tools
- BigQuery — SQL query execution on Google BigQuery
- Bigtable — NoSQL read/write on Google Bigtable
- Google Cloud Data Agents — natural language → SQL
- Apigee API Hub — REST API discovery and management
- Code Execution — sandboxed Python/JS execution
- Computer Use — Playwright-based browser automation
- Gemini API Code Execution — server-side code execution

### Design
Each follows the existing TSDM pattern:
```
engines/tools/models/{name}/
├── {name}_models.py   # Model dataclass (extends Tool base)
├── parser.py          # dict → model
├── writer.py          # model → dict
└── executor.py        # BaseToolExecutor subclass
```

Key model designs:

**BigQueryTool** — extends existing pattern (similar to DbQueryTool):
- Fields: `project_id`, `query`, `dataset_id`, `location`, `max_results`
- Executor uses `google-cloud-bigquery` SDK
- Returns rows as `list[dict]`

**BigtableTool** — new model:
- Fields: `instance_id`, `table_id`, `row_key`, `column_family`, `filter`
- Executor uses `google-cloud-bigtable` SDK
- Operations: `read_row`, `read_rows`, `write_row`, `delete_row`

**DataAgentTool** — wraps Cloud Data Agent API:
- Fields: `query`, `data_source`, `agent_id`
- Natural language → SQL via Google's Data Agent service

**ApigeeTool** — wraps Apigee API Hub:
- Fields: `api_hub_url`, `action` (search, get, list), `filters`
- Uses HTTP REST to Apigee API Hub

**CodeExecutionTool** — sandboxed execution:
- Fields: `language` (python, javascript, typescript), `source`, `timeout`, `sandbox_type` (docker, subprocess)
- Executor writes source to temp file, runs in container/sandbox, captures stdout/stderr

**ComputerUseTool** — browser automation:
- Fields: `action` (navigate, click, type, screenshot, extract), `url`, `selector`, `value`
- Executor wraps Playwright (async) — launches browser, performs action, returns result

**GeminiCodeExecutionTool** — Gemini API code execution:
- Fields: `code`, `language`, `files`
- Uses Gemini API's built-in code execution capability

### Files to create
- `engines/tools/models/bigquery/` (4 files)
- `engines/tools/models/bigtable/` (4 files)
- `engines/tools/models/data_agent/` (4 files)
- `engines/tools/models/apigee/` (4 files)
- `engines/tools/models/code_execution/` (4 files)
- `engines/tools/models/computer_use/` (4 files)
- `engines/tools/models/gemini_code_exec/` (4 files)

## Section 3: Observability System

### Architecture
New engine `engines/observability/` provides cross-cutting observability for all other engines.

### Structure
```
engines/observability/
├── __init__.py
├── core/
│   ├── types.py          # Span, Metric, Event dataclasses
│   ├── backends.py       # ObservabilityBackend(ABC)
│   ├── wrappers.py       # Proxy wrappers for registries/executors
│   └── loader.py         # Discovers + loads trace_definitions.yaml from each engine
├── backends/
│   ├── __init__.py       # Backend auto-select by config
│   ├── agentops.py       # Default backend — purpose-built for agents
│   ├── datadog.py
│   ├── mlflow.py
│   ├── weave.py
│   ├── arize.py
│   ├── freeplay.py
│   ├── future_agi.py
│   ├── langwatch.py
│   └── grafana.py
├── config/
│   └── observability.yaml
└── plugin.py             # ObservabilityPlugin(AgentPlugin)
```

### Trace Definitions (per engine)
Each engine declares its trace points in a local `trace_definitions.yaml`:

```yaml
# engines/agent/trace_definitions.yaml
engine: agent
spans:
  - name: agent.run
    attributes: [agent_name, workflow_id]
  - name: mediator.send
    attributes: [sender, recipient]
```

Engines with definitions: `agent/`, `orchestration/`, `tools/`, `communication/`, `knowledge/`, `memory/`, `storage/`.

### How Instrumentation Works
The `ObservabilityPlugin` wraps key objects at activation:
1. `AgentRegistry` — wraps `run()` method
2. `ToolRegistry` — wraps `execute()` method
3. `MultiAgentMediator` — wraps `send_message()`, `broadcast()`
4. `OrchestrationEngine` — wraps `execute_workflow()`
5. `MessageBus` — wraps `publish()`, `subscribe()`

Wrapping uses Python `__getattr__` proxy pattern — no modifications to engine code.

### Default Backend
AgentOps (`backends/agentops.py`) — purpose-built for AI agent observability:
- Agent execution spans
- LLM call tracing with token counts and cost
- Tool invocation tracking
- Built-in session management aligned with workflow orchestration

### Configuration
```yaml
# engines/observability/config/observability.yaml
backend: agentops
agentops:
  api_key: ${AGENTOPS_API_KEY}
```

### Files to create
- `engines/observability/__init__.py`
- `engines/observability/core/` (4 files)
- `engines/observability/backends/` (10 files including __init__)
- `engines/observability/config/observability.yaml`
- `engines/observability/plugin.py`
- `engines/agent/trace_definitions.yaml`
- `engines/orchestration/trace_definitions.yaml`
- `engines/tools/trace_definitions.yaml`
- `engines/communication/trace_definitions.yaml`
- `engines/knowledge/trace_definitions.yaml`
- `engines/memory/trace_definitions.yaml`
- `engines/storage/trace_definitions.yaml`

## Section 4: TTS/Media System

### Architecture
New engine `engines/tts/` provides a unified text-to-speech interface with pluggable backends.

### Structure
```
engines/tts/
├── __init__.py
├── engine.py           # TTSEngine — unified interface
├── plugin.py           # TTSPlugin(AgentPlugin) — ABC
└── backends/
    ├── __init__.py
    ├── cartesia.py     # CartesiaTTSPlugin
    └── elevenlabs.py   # ElevenLabsTTSPlugin
```

### TTSEngine Interface
```python
class TTSEngine:
    async def synthesize(self, text: str, voice: str, **options) -> bytes
    async def list_voices(self) -> list[VoiceSpec]
```

### TTSPlugin ABC
```python
class TTSPlugin(AgentPlugin):
    def plugin_type(self): return "SKILL"  # or "TOOL"
    @abstractmethod
    async def synthesize(self, text: str, voice: str, **options) -> bytes
    @abstractmethod
    async def list_voices(self) -> list[VoiceSpec]
```

### Default Backends
- Cartesia — uses Cartesia REST API for ultra-low-latency TTS
- ElevenLabs — uses ElevenLabs API for high-quality voice synthesis

### Files to create
- `engines/tts/` (5 files including __init__ and backends)

## Section 5: LLM Gateway System

### Architecture
Module at `engines/tools/llm_gateway/` provides LLM routing/caching/cost tracking on top of AiModelToolExecutor.

### Structure
```
engines/tools/llm_gateway/
├── __init__.py
├── plugin.py          # LLMGatewayPlugin(AgentPlugin)
├── gateway.py         # LLMGateway — routing/caching/cost
└── backends/
    ├── __init__.py
    └── mlflow.py      # MLflowGateway backend
```

### LLMGateway Interface
```python
class LLMGateway:
    async def route(self, model: str, prompt: str, **kwargs) -> ModelResult
    async def get_cost(self, model: str) -> CostInfo
```

### Default Backend
MLflow AI Gateway — provides:
- Unified endpoint for OpenAI, Anthropic, Gemini providers
- Cost tracking per model/per request
- Fallback routing on provider failure
- Request caching for identical prompts

### Integration
The `LLMGatewayPlugin` registers as a TOOL-type plugin and wraps `AiModelToolExecutor` calls. When the gateway is active, all LLM tool calls route through it.

### Files to create
- `engines/tools/llm_gateway/` (6 files including __init__ and backends)

## Integration with Existing Architecture

```
                                ┌─────────────────────────┐
                                │   ObservabilityPlugin    │
                                │   (engines/observability)│
                                └──────┬──────────────────┘
                                       │ wraps
        ┌───────────────┬───────────────┼───────────────┬──────────────────┐
        │               │               │               │                  │
   ┌────▼────┐   ┌─────▼─────┐   ┌─────▼─────┐   ┌─────▼─────┐    ┌───────┴───────┐
   │ Agent   │   │Orchestr.  │   │ Tools     │   │ Communic. │    │  Knowledge    │
   │ Engine  │   │ Engine    │   │ Engine    │   │ Engine    │    │  + Memory     │
   └─────────┘   └───────────┘   └─────┬─────┘   └───────────┘    └───────────────┘
                                       │
                      ┌────────────────┼────────────────┐
                      │                │                │
                 ┌────▼────┐    ┌──────▼──────┐   ┌─────▼─────┐
                 │ MCP     │    │  Full Tool  │   │ LLM       │
                 │ Config  │    │  Executors  │   │ Gateway   │
                 │(5 tools)│    │  (7 tools)  │   │(mlflow)   │
                 └─────────┘    └─────────────┘   └───────────┘

┌─────────────────────────────────────────────────────────────────────┐
│  TTS Engine                          LLM Gateway                    │
│  (engines/tts)                       (engines/tools/llm_gateway)   │
│   ├─ Cartesia                         └─ MLflow AI Gateway          │
│   └─ ElevenLabs                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## Not Yet Implemented / Open Issues
- A2UI (Agent-to-UI) — remains as open issue for future design
- Google Cloud Agent Platform express mode — remains as open issue

## Self-Review Checklist
- No placeholders, TODOs, or TBDs
- Architecture matches feature descriptions across all 5 sections
- Each section is independently implementable
- No contradictions between sections
- Scope is clear and bounded — 5 independent subsystems, no single monolithic delivery
