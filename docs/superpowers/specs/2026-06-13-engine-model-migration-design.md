# Engine-Specific Model Migration — Phase 1

## Overview

Move engine-specific SDM models, parsers, and writers out of the centralized
`engines/document/` into their owning engines. Shared/base models stay in
`engines/document/`. This is Phase 1 of the broader refactoring described in
`refactoring.md`.

## Scope

### Moves (Phase 1)

| Engine | Models | Parsers | Writers | Tests |
|--------|--------|---------|---------|-------|
| **knowledge** | ksdm_models, query_models | bi_aggregation/, ml_mining/, process_mining/, semantic_graph/, query_models/ | bi_aggregation/, ml_mining/, process_mining/, semantic_graph/, query_models/ | `tests/knowledge/` → `engines/knowledge/tests/` |
| **orchestration** | osdm_models, bam_models | osdm parser files (flat), bam/ (separate family) | osdm writer files (flat), bam/ (separate family) | `tests/orchestration/` → `engines/orchestration/tests/` |
| **tools** | tsdm_models | tsdm_json_parser.py (flat) | tsdm_json_writer.py (flat) | `tests/tools/` → `engines/tools/tests/` |

### Stays in `engines/document/`

| Path | Reason |
|------|--------|
| `models/base.py` | `BaseDocument` — base class for ALL models |
| `models/media_types.py` | `DocumentFormat`, `MediaType`, `MEDIA_TYPES` — single source of truth |
| `models/standard.py` | `DocumentStandard` enum |
| `models/msdm_models.py` (+ capabilities, registry) | MSDM — shared schema model |
| `models/ssdm_models.py` (+ capabilities, registry) | SSDM — service model (not yet split) |
| `models/csdm_core.py`, `csdm_entities.py`, `csdm_tables.py` | CSDM — CAD, shared |
| `models/esdm_models.py` | ESDM — spreadsheet, shared |
| `models/psdm_models.py` | PSDM — presentation, shared |
| `models/usdm_models.py` | USDM — text, shared |
| `models/dsdm_models.py` | DSDM — data, shared |
| `models/lsdm_models.py` | LSDM — event logs, shared |
| `models/document_registry.py` | Shared registry |
| `models/exceptions.py` | Shared exceptions |
| `parsers/base.py` | `BaseDocumentParser` abstract class |
| `writers/base.py` | `BaseDocumentWriter` abstract class |
| All parsers/writers for shared models | csdm_parsers, esdm_parsers, psdm_parsers, usdm_parsers, dsdm_parsers, lsdm_parsers, msdm_parsers, ssdm_parsers |

## Target Directory Layout

```
engines/{engine}/
  __init__.py
  models/
    __init__.py
    {model_files}.py
    parsers/
      {subgroup}/     # only when multiple distinct parser families exist
        __init__.py
        ...
    writers/
      {subgroup}/
        __init__.py
        ...
  tests/
    conftest.py       # moved from tests/{engine}/
    ...
```

### Examples

**knowledge:**
```
engines/knowledge/models/
  __init__.py
  ksdm_models.py
  query_models.py
  parsers/
    bi_aggregation/
    ml_mining/
    process_mining/
    semantic_graph/
    query_models/
  writers/
    bi_aggregation/
    ml_mining/
    process_mining/
    semantic_graph/
    query_models/
```

**orchestration:**
```
engines/orchestration/models/
  __init__.py
  osdm_models.py
  bam_models.py
  parsers/
    __init__.py
    base_osdm_parser.py
    bpmn_xml_parser.py
    cep_parser.py
    cmmn_xml_parser.py
    dmn_xml_parser.py
    ...              # other osdm parser files (flat)
    bam/             # separate family — uses subgroup
      __init__.py
      base_bam_parser.py
      bam_json_parser.py
      bam_yaml_parser.py
  writers/
    __init__.py
    base_osdm_writer.py
    bpmn_xml_writer.py
    cep_writer.py
    ...              # other osdm writer files (flat)
    bam/
      __init__.py
      base_bam_writer.py
      bam_json_writer.py
      bam_yaml_writer.py
```

**tools:**
```
engines/tools/models/
  __init__.py
  tsdm_models.py
  parsers/
    __init__.py
    base_tsdm_parser.py
    tsdm_json_parser.py
  writers/
    __init__.py
    base_tsdm_writer.py
    tsdm_json_writer.py
```

## Import Rule

All models/parsers/writers are imported from their owning engine. No
distinction between "internal" and "cross-engine" consumers.

```python
# KSDM — always from knowledge engine
from engines.knowledge.models.ksdm_models import SemanticGraphDocument

# OSDM — always from orchestration engine
from engines.orchestration.models.osdm_models import ProcessDefinition

# TSDM — always from tools engine
from engines.tools.models.tsdm_models import TSDMDocument

# Shared infra — stays in document engine
from engines.document.models.base import BaseDocument
from engines.document.models.media_types import DocumentFormat
```

Pattern for parsers/writers:
```python
from engines.knowledge.models.parsers.ml_mining import PmmlParser
from engines.orchestration.models.parsers.bpmn_xml_parser import BpmnXmlParser
from engines.tools.models.writers.tsdm_json_writer import TsdmJsonWriter
```

## `__init__.py` Updates

### `engines/knowledge/ml_mining/__init__.py`
Currently re-exports KSDM model types from `engines.document.models.ksdm_models`.
Change to import from `engines.knowledge.models.ksdm_models`.

### `engines/knowledge/graph/__init__.py`
Currently re-exports `GraphNode`, `GraphEdge` from `engines.document.models.ksdm_models`.
Change to import from `engines.knowledge.models.ksdm_models`.

### `engines/knowledge/__init__.py`
No structural change needed — already eagerly imports sub-engines.
The new `models/__init__.py` handles model exports.

### `engines/document/parsers/__init__.py` and `writers/__init__.py`
Remove re-exports of moved parsers/writers.

## Approach

**Big-bang move with no backward-compat wrappers.** All files move in one
commit, all imports updated simultaneously, old files deleted. Rationale:
cleaner long-term state, no wrapper cleanup debt.

## Execution Order

1. Create target directories under each engine
2. Copy files to new locations (preserving originals for now)
3. Update all imports across the codebase (systematic find-and-replace)
4. Update `__init__.py` files in knowledge (ml_mining, graph)
5. Move test directories (`tests/knowledge/` → `engines/knowledge/tests/`,
   same for orchestration, tools) and update their imports
6. Delete moved files from old locations — only the files that were
   copied in step 2 (e.g., `engines/document/models/ksdm_models.py`,
   `engines/document/models/osdm_models.py`,
   `engines/document/models/tsdm_models.py`,
   `engines/document/models/bam_models.py`,
   `engines/document/models/query_models.py`,
   `engines/document/parsers/ksdm_parsers/` (entire directory),
   `engines/document/parsers/osdm_parsers/` (entire directory),
   `engines/document/parsers/tsdm_parsers/` (entire directory),
   `engines/document/parsers/bam_parsers/` (entire directory),
   `engines/document/writers/ksdm_writers/` (entire directory),
   `engines/document/writers/osdm_writers/` (entire directory),
   `engines/document/writers/tsdm_writers/` (entire directory),
   `engines/document/writers/bam_writers/` (entire directory))
7. Update `engines/document/models/__init__.py` — remove re-exports of
   moved models (ksdm_models, osdm_models, tsdm_models, bam_models)
   from both imports and `__all__`
8. Update `engines/document/parsers/__init__.py`
   and `engines/document/writers/__init__.py` — remove moved parser/writer re-exports
9. Run full test suite
10. Update `AGENTS.md` test commands (new test paths)

## Verification

- `python3 -m pytest engines/knowledge/tests/ -v` — 146+ tests pass
- `python3 -m pytest engines/orchestration/tests/ -v`
- `python3 -m pytest engines/tools/tests/ -v`
- `python3 -m pytest tests/ --collect-only` — no import failures
- `mypy engines/ --ignore-missing-imports`
