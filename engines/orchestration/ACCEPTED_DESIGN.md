# Accepted-By-Design Patterns

Type-safety trade-offs and design decisions that are intentionally
not pursued further. Each entry explains why the pattern is accepted.

## 1. Circular Import Chains

### Core Engine ↔ EngineServices (`Deployment`, `ProcessDefinition`)
- **File**: `core/_definition_models.py`
- **Status**: RESOLVED — extracted to shared module
- `Deployment` and `ProcessDefinition` moved from `engine.py` to
  `_definition_models.py`. Both `engine.py` and `engine_services.py`
  import from there directly.

### Instance ↔ InstanceStates
- **File**: `core/instance.py`
- **Status**: RESOLVED — direct import
- `ProcessState` now imported directly from `instance_states.py` at
  module level (no `TYPE_CHECKING`). InstanceStates already used
  `IProcessInstance` Protocol from `_context_protocols.py`.

### Token ↔ TokenStates
- **File**: `core/token.py`
- **Status**: RESOLVED — direct import
- Same pattern as Instance: `TokenState as TokenStateObj` imported
  directly from `token_states.py`.

### ModelNormalizer ↔ ProcessExecutor
- **File**: `bpmn/model_normalizer.py`
- **Status**: ACCEPTED — `TYPE_CHECKING` + lazy import
- `ProcessModel` cannot be extracted to a third module (too tightly
  coupled to process_executor internals). `TYPE_CHECKING` provides
  mypy annotations; lazy import inside the method body provides
  runtime access. Standard Python pattern.

### ContextProtocols ↔ EngineStates / InstanceStates / TokenStates
- **File**: `core/_context_protocols.py`
- **Status**: ACCEPTED — `TYPE_CHECKING` only
- Protocols MUST reference concrete state types in their attribute
  annotations. Importing them directly would create the exact circular
  dep this file was created to break. `TYPE_CHECKING` with
  `from __future__ import annotations` makes annotations strings at
  runtime, avoiding the cycle entirely.

## 2. `# type: ignore` Annotations

**Remaining: 57** (down from 62)

| Category | Count | Rationale |
|----------|-------|-----------|
| `import-not-found` / `import-untyped` | ~30 | Optional third-party packages (aiohttp, grpc, faiss, msgpack, sklearn, fitz, etc.) not installed in the dev environment. Runtime availability gated by lazy import. |
| `attr-defined` | 2 | Protobuf dynamic class access (`factory.GetPrototype`) — no static type info available. |
| `arg-type` | 2 | `StorageFactory.register()` generic parameter mismatch — factory type system needs `type[StorageT]` but concrete classes may have diverging signatures. |
| `arg-type` | 1 | `knowledge_rag_engine.py:313` — reflection loop type signature mismatch. Requires deeper refactor of the reflection subsystem. |

**Fixed this session** (5 removed):
- `decorators.py:39` → `cast(F, wrapper)`
- `decorators.py:131` → assertion guard
- `decorators.py:205` → isinstance + assertion
- `engine_bridge.py:316` → ABC `__init__` added
- `mcp_service.py:65` → removed (spurious — `MessagePayload` and `RawData` are both `dict[str, Any]`)

## 3. Non-Type-Safe Annotations (`Any`)

### Document Parsers (XML / HTML / DOCX / PDF)
- **Scope**: ~725 `: Any` annotations across `engines/document/parsers/`
- **Rationale**: XML/HTML tree nodes, PDF layout elements, and binary
  stream tokens are inherently untyped at the parser boundary. Parser
  output is always `dict[str, Any]` by design — typed models are
  constructed in a separate layer above the parser.

### CEP Event Processing
- **Scope**: `engines/orchestration/cep/` — event payloads and
  window aggregations
- **Rationale**: CEP events are schemaless by nature. Event types
  and fields are discovered at runtime from the event stream.

### Visitor Pattern Dispatch
- **Scope**: `validation/model_visitor.py`, `runtime/osdm_serializer.py`
- **Status**: ModelVisitor converted to dispatch dict. Serializer's
  `_flow_element_to_dict` kept isinstance (multi-statement branches
  with different dict keys per type).

### Metadata / Extensions
- **Scope**: `dict[str, Any]` for extension elements, custom
  attributes, and vendor-specific metadata
- **Rationale**: Extension data is defined by third-party schema
  authors and cannot be known at compile time.

## 4. Dispatch Dict Conversion

| File | Branches | Status |
|------|----------|--------|
| `validation/model_visitor.py` | 6 | `_VISIT_DISPATCH` |
| `dmn/decision_executor.py` | 7+4 | `_BOXED_EXPRESSION_HANDLERS` + `_BODY_EXTRACTORS` |
| `dmn/decision_table_evaluator.py` | 6 (Visitor-2) | `_ACTIVITY_DISPATCH` (prior session) |
| `dmn/hit_policy_handler.py` | 5 | `_HIT_POLICY_HANDLERS` (prior session) |
| `dmn/feel_engine.py` | 9 | `_OPERATOR_HANDLERS` (prior session) |
| `expression/feel_evaluator.py` | 30 | `_OP_HANDLERS` (prior session) |
| `bpmn/gateway_handler.py` | 5 | `_GATEWAY_TYPE_MAP` |
| `bpmn/gateway_classifier.py` | 5 | `_GATEWAY_CLASSIFIER_MAP` |
| `bpmn/bpmn_execution_semantics.py` | 5 | `_GATEWAY_SPLIT_HANDLERS` |
| `bpmn/global_task_handler.py` | 4 | `_GLOBAL_TASK_TYPE_MAP` |
| `runtime/osdm_serializer.py` | 3 | Kept isinstance — multi-statement branches with different dict keys per type |

## 5. Pydantic v2

- `class Config` → `model_config = ConfigDict(...)` — ALL instances converted
- `.dict()` → `.model_dump()` — ALL instances converted
- v1 fallback code (e.g. `_model_dump` in `base_agent.py`) — removed
- No remaining Pydantic v1 API usage

## 6. Deprecated Typing Imports

- `Dict`/`List`/`Set`/`Tuple` → bare `dict`/`list`/`set`/`tuple` — ALL converted
- `Optional[X]` → `X | None` — ALL converted
- `Union[X, Y]` → `X | Y` — ALL converted

## 7. Object Type Annotation

- `object` → `Any` — ALL 80+ occurrences replaced across ~24 files
- Rationale: `Any` enables progressive type-checking without forcing
  every boundary to be fully typed. `object` would require callers
  to narrow with `cast()` or `isinstance()` at every call site.
