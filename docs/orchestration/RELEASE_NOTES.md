# Release Notes — multi-agent-infra

## Iteration: ISDM→KSDM Consolidation, LSDM Creation, Agentic BPMN Extension

### 1. ISDM → KSDM Consolidation

- Merged `isdm_models.py` into `ksdm_models.py` — `ISDMDocument` → `KSDMMetricsDocument`
- Removed `ISDM = "isdm"` from `DocumentStandard`
- Deleted all `isdm_parsers/`, `isdm_writers/`, `isdm_models.py`
- Moved BI and ML‑mining parsers/writers from `isdm_*` → `ksdm_*` names
- Renamed and updated 3 test files (`test_isdm_*` → `test_ksdm_*_metrics.py`)
- Fixed pre‑existing broken imports in `parsers/__init__.py` (usdm_parsers paths)
- Removed `docs/knowledge/conformance/isdm-parser-writer-compliance.md`

### 2. Process Mining Removal from KSDM

- Removed `Xes*`, `Dmn*`, `Dd*`, `ProcessMiningDocument` from `ksdm_models.py` (~99 lines)
- Deleted `ksdm_writers/process_mining/` directory (4 files)
- Rewrote `ksdm_parsers/__init__.py` and `ksdm_writers/__init__.py` as clean export‑only modules
- All KSDM parsers now inherit `BaseDocumentParser` and set `media_type`
- All KSDM writers now inherit `BaseDocumentWriter`

### 3. LSDM (Log Standard Definition Model) — New Engine

- Created `lsdm_models.py` with `EventLogDocument`, `LogEvent`, XES/Syslog/CEF/ES‑bulk models
- Created `lsdm_parsers/` (xes, syslog, cef, es_bulk) — all inherit `BaseDocumentParser`
- Created `lsdm_writers/` (xes, syslog, cef, es_bulk) — all inherit `BaseDocumentWriter`
- Added `SYSLOG`, `CEF`, `ES_BULK` to `DocumentFormat` and `MEDIA_TYPES`

### 4. Agentic BPMN Extension (OSDM)

**New Enums (6):**
| Enum | Values |
|---|---|
| `ReflectionStrategy` | `SELF`, `CROSS`, `HUMAN` |
| `CollaborationStrategyType` | `VOTING`, `ROLE`, `DEBATE`, `COMPETITION` |
| `MergeStrategyType` | `MAJORITY`, `LEADER`, `FASTEST`, `MOST_COMPLETE` |
| `VotingRule` | `MAJORITY`, `ABSOLUTE_MAJORITY`, `MINORITY` |
| `RoleStrategyType` | `LEADER_DRIVEN`, `COMPOSED` |
| `CompetitionRule` | `FASTEST`, `MOST_COMPLETE` |

**New Strategy Config Dataclasses (5):**
- `VotingConfig`, `RoleConfig`, `CompetitionConfig`, `CollaborationStrategy`, `MergeStrategy`

**New BPMN Element Classes (5):**
| Class | Parent | Purpose |
|---|---|---|
| `AgenticTask` | `Task` | Single/multi-agent task with reflection |
| `AgenticLane` | `Lane` | Agent participant with capabilities |
| `DivergingAgenticGateway` | `Gateway` | Multi-agent fan-out with collaboration strategy |
| `MergingAgenticGateway` | `Gateway` | Multi-agent fan-in with merge strategy |
| `AgenticMessageFlow` | `MessageFlow` | Agent communication with protocol metadata |

**Exports Updated:**
- `engines/document/models/__init__.py` — all 16 new symbols exported in `__all__`

**Documentation Created:**
- `docs/orchestration/agentic_bpmn_extension.md` — design rationale and architecture
- `docs/orchestration/compliance/COMPLIANCE_AGENTIC_BPMN.md` — BPMN 2.0 extension compliance
- `docs/orchestration/compliance/COMPARISON_AGENTIC_BPMN.md` — overlap analysis with interaction layer

### 5. Tests

- 19 core knowledge tests all pass
- All lint/import checks pass
- No new dependencies introduced

### 6. Files Changed

```
Modified:
  engines/document/models/__init__.py
  engines/document/models/osdm_models.py
  engines/document/models/media_types.py
  engines/knowledge/models/ksdm_models.py
  engines/knowledge/parsers/__init__.py
  engines/knowledge/writers/__init__.py
  tests/knowledge/test_models.py
  tests/knowledge/test_writers.py
  tests/knowledge/test_engines.py

Created:
  engines/knowledge/models/lsdm_models.py
  engines/knowledge/parsers/lsdm_parsers/__init__.py
  engines/knowledge/parsers/lsdm_parsers/base.py
  engines/knowledge/parsers/lsdm_parsers/xes_parser.py
  engines/knowledge/parsers/lsdm_parsers/syslog_parser.py
  engines/knowledge/parsers/lsdm_parsers/cef_parser.py
  engines/knowledge/parsers/lsdm_parsers/es_bulk_parser.py
  engines/knowledge/writers/lsdm_writers/__init__.py
  engines/knowledge/writers/lsdm_writers/base.py
  engines/knowledge/writers/lsdm_writers/xes_writer.py
  engines/knowledge/writers/lsdm_writers/syslog_writer.py
  engines/knowledge/writers/lsdm_writers/cef_writer.py
  engines/knowledge/writers/lsdm_writers/es_bulk_writer.py
  docs/orchestration/agentic_bpmn_extension.md
  docs/orchestration/compliance/COMPLIANCE_AGENTIC_BPMN.md
  docs/orchestration/compliance/COMPARISON_AGENTIC_BPMN.md
  tests/knowledge/test_ksdm_bi_metrics.py  (renamed from test_isdm_bi.py)
  tests/knowledge/test_ksdm_ml_metrics.py  (renamed from test_isdm_ml.py)
  tests/knowledge/test_ksdm_process_metrics.py (renamed from test_isdm_process.py)

Deleted:
  engines/knowledge/models/isdm_models.py
  engines/knowledge/parsers/isdm_parsers/
  engines/knowledge/writers/isdm_writers/
  engines/knowledge/writers/ksdm_writers/process_mining/
  tests/knowledge/test_isdm_bi.py
  tests/knowledge/test_isdm_ml.py
  tests/knowledge/test_isdm_process.py
  docs/knowledge/conformance/isdm-parser-writer-compliance.md
```
