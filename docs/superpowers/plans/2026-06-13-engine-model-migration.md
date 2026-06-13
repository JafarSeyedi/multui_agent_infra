# Engine-Specific Model Migration — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move engine-specific SDM models, parsers, writers, and tests out of the centralized `engines/document/` into their owning engines (knowledge, orchestration, tools) — one big-bang commit with no backward-compat wrappers.

**Architecture:** Target engines gain a `models/` directory containing model files, `parsers/` subdirectory, and `writers/` subdirectory. `engines/document/` retains only shared/base models. All imports update from `engines.document.*` to the owning engine's path.

**Tech Stack:** Python 3.11+, pytest, mypy

---

## File Structure Summary

### Create in `engines/knowledge/`

```
models/
  __init__.py                         # re-export all knowledge models
  ksdm_models.py                      # ← from engines/document/models/
  query_models.py                     # ← from engines/document/models/
  parsers/
    __init__.py
    bi_aggregation/                   # ← from document/parsers/ksdm_parsers/bi_aggregation/ (11 files)
    ml_mining/                        # ← from document/parsers/ksdm_parsers/ml_mining/ (5 files)
    process_mining/                   # ← from document/parsers/ksdm_parsers/process_mining/ (2 files)
    query_models/                     # ← from document/parsers/ksdm_parsers/query_models/ (9 files)
    semantic_graph/                   # ← from document/parsers/ksdm_parsers/semantic_graph/ (3 files)
  writers/
    __init__.py
    bi_aggregation/                   # ← from document/writers/ksdm_writers/bi_aggregation/ (11 files)
    ml_mining/                        # ← from document/writers/ksdm_writers/ml_mining/ (5 files)
    process_mining/                   # ← from document/writers/ksdm_writers/process_mining/ (2 files)
    query_models/                     # ← from document/writers/ksdm_writers/query_models/ (9 files)
    semantic_graph/                   # ← from document/writers/ksdm_writers/semantic_graph/ (2 files)
tests/                                # ← from tests/knowledge/ (7 files)
```

### Create in `engines/orchestration/`

```
models/
  __init__.py                         # re-export all orchestration models
  osdm_models.py                      # ← from engines/document/models/ (59KB — very large)
  bam_models.py                       # ← from engines/document/models/
  parsers/
    __init__.py
    base_osdm_parser.py               # ← from document/parsers/osdm_parsers/
    bpmn_collaboration.py             #  (and 15 other flat parser files)
    bpmn_constants.py
    bpmn_diagram.py
    bpmn_flow_parser.py
    bpmn_reference_resolver.py
    bpmn_root_element.py
    bpmn_xml_parser.py
    cep_parser.py
    cmmn_xml_parser.py
    dmn_xml_parser.py
    epc_parser.py
    graphml_xml_parser.py
    pnml_xml_parser.py
    prefect_dag_parser.py
    scxml_parser.py
    uml_state_machine_parser.py
    xpd_parser.py
    bam/                              # separate family — subgroup
      __init__.py
      base_bam_parser.py
      bam_json_parser.py
      bam_yaml_parser.py
  writers/
    __init__.py
    base_osdm_writer.py               # ← from document/writers/osdm_writers/ (flat — 13 files)
    bpmn_xml_writer.py
    cep_writer.py
    cmmn_xml_writer.py
    dmn_xml_writer.py
    epc_writer.py
    graphml_xml_writer.py
    pnml_xml_writer.py
    prefect_dag_writer.py
    scxml_writer.py
    uml_state_machine_writer.py
    xpd_writer.py
    bam/
      __init__.py
      base_bam_writer.py
      bam_json_writer.py
      bam_yaml_writer.py
tests/                                # ← from tests/orchestration/ (32 files)
```

### Create in `engines/tools/`

```
models/
  __init__.py                         # re-export all tools models
  tsdm_models.py                      # ← from engines/document/models/
  parsers/
    __init__.py
    base_tsdm_parser.py               # ← from document/parsers/tsdm_parsers/
    tsdm_json_parser.py
  writers/
    __init__.py
    base_tsdm_writer.py               # ← from document/writers/tsdm_writers/
    tsdm_json_writer.py
tests/                                # ← from tests/tools/ (2 files)
```

---

### Task 1: Create target directory tree and `__init__.py` stubs

**Files to create:**
- Create (mkdir -p): all target directories listed above
- Create: `engines/knowledge/models/__init__.py`
- Create: `engines/knowledge/models/parsers/__init__.py`
- Create: `engines/knowledge/models/parsers/process_mining/__init__.py`
- Create: `engines/knowledge/models/writers/__init__.py`
- Create: `engines/knowledge/models/writers/process_mining/__init__.py`
- Create: `engines/knowledge/models/writers/semantic_graph/__init__.py`
- Create: `engines/orchestration/models/__init__.py`
- Create: `engines/orchestration/models/parsers/__init__.py`
- Create: `engines/orchestration/models/parsers/bam/__init__.py`
- Create: `engines/orchestration/models/writers/__init__.py`
- Create: `engines/orchestration/models/writers/bam/__init__.py`
- Create: `engines/tools/models/__init__.py`
- Create: `engines/tools/models/parsers/__init__.py`
- Create: `engines/tools/models/writers/__init__.py`

- [ ] **Step 1: Create all target directories**

```bash
# Knowledge engine
mkdir -p engines/knowledge/models/parsers/{bi_aggregation,ml_mining,process_mining,query_models,semantic_graph}
mkdir -p engines/knowledge/models/writers/{bi_aggregation,ml_mining,process_mining,query_models,semantic_graph}
mkdir -p engines/knowledge/tests

# Orchestration engine
mkdir -p engines/orchestration/models/parsers/bam
mkdir -p engines/orchestration/models/writers/bam
mkdir -p engines/orchestration/tests

# Tools engine
mkdir -p engines/tools/models/parsers
mkdir -p engines/tools/models/writers
mkdir -p engines/tools/tests
```

- [ ] **Step 2: Write all `__init__.py` stubs**

Write `engines/knowledge/models/__init__.py`:
```python
from .ksdm_models import (
    AttributeValue, DatasetSplit, EvaluationStage, FeatureImportance,
    FieldUsageType, ImportanceMethod, LossFunction, MiningField,
    MiningModelType, MiningSchema, ModelFormat, ModelGraph, ModelMetric,
    ModelNode, ModelParameter, ModelResult, MlMiningDocument, OpType,
    OptimizationAlgorithm, OutlierTreatment, ParameterName, Port,
    RegularizationConfig, TrainingConfig, TrainingTask,
)

from .query_models import (
    AggregationColumn, CalculatedMember, CubeRef, DaxQuery, DimensionRef,
    GraphQLField, GraphQLQuery, GraphQLTypeRef, HierarchyRef, JpqlQuery,
    KpiRef, MdxQuery, MeasureRef, OqlQuery, PowerQueryM, QueryColumn,
    QueryLanguage, QueryTransport, RestTransport, SqlTabularQuery,
    TabularRelationship, UnifiedQueryDocument, XmlaTransport,
)
```

Write `engines/knowledge/models/parsers/__init__.py`:
```python
from . import bi_aggregation
from . import ml_mining
from . import process_mining
from . import query_models
from . import semantic_graph
```

Write `engines/knowledge/models/parsers/process_mining/__init__.py`:
```python
```
(empty — namespace package)

Write `engines/knowledge/models/writers/__init__.py`:
```python
from . import bi_aggregation
from . import ml_mining
from . import process_mining
from . import query_models
from . import semantic_graph
```

Write `engines/knowledge/models/writers/process_mining/__init__.py`:
```python
```
(empty)

Write `engines/knowledge/models/writers/semantic_graph/__init__.py`:
```python
```
(empty)

Write `engines/orchestration/models/__init__.py` — copy the OSDM and BAM import lines from the original `engines/document/models/__init__.py` into the new file, replacing the import path from `from .osdm_models` / `from .bam_models` (relative to that file). The pattern is:

```python
# Copy all OSDM import lines from engines/document/models/__init__.py,
# changing `from .osdm_models import` to `from .osdm_models import`
# (same — it's already relative to the models directory)

# Copy all BAM import lines similarly
```

The original has these import blocks for OSDM:
```python
from .osdm_models import DecisionRule
from .osdm_models import InputClause, LiteralExpression, OutputClause, UnaryTests
from .osdm_models import ActionList, Activity, ...
# ... hundreds of classes across 3-4 import lines
from .osdm_models import AgenticLane, AgenticMessageFlow, ...
```

And for BAM:
```python
from .bam_models import (
    AlertNotification, ...
)
```

These import lines are identical regardless of whether the file is in `engines/document/models/` or `engines/orchestration/models/` since they use relative imports from the same directory. Just copy them verbatim into `engines/orchestration/models/__init__.py`.

Write `engines/orchestration/models/parsers/__init__.py`:
```python
from . import bam
```

Write `engines/orchestration/models/parsers/bam/__init__.py`:
```python
```

Write `engines/orchestration/models/writers/__init__.py`:
```python
from . import bam
```

Write `engines/orchestration/models/writers/bam/__init__.py`:
```python
```

Write `engines/tools/models/__init__.py`:
```python
from .tsdm_models import (
    AiModelTool, CliTool, CompositeTool, DbQueryTool, DbStatementTool,
    FileReadTool, FileWriteTool, GraphQLTool, GrpcServiceTool,
    HttpServiceTool, LoadBalanceStrategy, MCPTool, MessageBusTool,
    MibSnmpTool, NetconfProtocol, ParameterSource, ParameterType,
    PythonFunctionTool, SnmpVersion, TSDMDocument, TcpSocketTool,
    Tool, ToolKind, ToolOutput, ToolParameter, YangNetconfTool,
)
```

Write `engines/tools/models/parsers/__init__.py`:
```python
```

Write `engines/tools/models/writers/__init__.py`:
```python
```

---

### Task 2: Copy model files to target engines

- [ ] **Step 1: Copy `ksdm_models.py` and `query_models.py` to knowledge engine**

```bash
cp engines/document/models/ksdm_models.py engines/knowledge/models/ksdm_models.py
cp engines/document/models/query_models.py engines/knowledge/models/query_models.py
```

- [ ] **Step 2: Copy `osdm_models.py` and `bam_models.py` to orchestration engine**

```bash
cp engines/document/models/osdm_models.py engines/orchestration/models/osdm_models.py
cp engines/document/models/bam_models.py engines/orchestration/models/bam_models.py
```

- [ ] **Step 3: Copy `tsdm_models.py` to tools engine**

```bash
cp engines/document/models/tsdm_models.py engines/tools/models/tsdm_models.py
```

---

### Task 3: Copy parser files to target engines

- [ ] **Step 1: Copy ksdm_parsers to knowledge engine**

Skip `__init__.py` files during copy (they were already created correctly in Task 1).

```bash
# Copy all parser subgroup files (excluding __init__.py — already created)
cp engines/document/parsers/ksdm_parsers/bi_aggregation/*.py engines/knowledge/models/parsers/bi_aggregation/
cp engines/document/parsers/ksdm_parsers/ml_mining/*.py engines/knowledge/models/parsers/ml_mining/
cp engines/document/parsers/ksdm_parsers/process_mining/*.py engines/knowledge/models/parsers/process_mining/
cp engines/document/parsers/ksdm_parsers/query_models/*.py engines/knowledge/models/parsers/query_models/
cp engines/document/parsers/ksdm_parsers/semantic_graph/*.py engines/knowledge/models/parsers/semantic_graph/
```

Then re-write the `__init__.py` files (in case cp overwrote them) with the content from Task 1 Step 2.

- [ ] **Step 2: Copy osdm_parsers to orchestration engine (flat files)**

```bash
cp engines/document/parsers/osdm_parsers/*.py engines/orchestration/models/parsers/
```

Then re-write `engines/orchestration/models/parsers/__init__.py` (Task 1 content).

- [ ] **Step 3: Copy bam_parsers to orchestration engine (bam/ subdir)**

```bash
cp engines/document/parsers/bam_parsers/*.py engines/orchestration/models/parsers/bam/
```

Then re-write `engines/orchestration/models/parsers/bam/__init__.py` (Task 1 content).

- [ ] **Step 4: Copy tsdm_parsers to tools engine**

```bash
cp engines/document/parsers/tsdm_parsers/*.py engines/tools/models/parsers/
```

Then re-write `engines/tools/models/parsers/__init__.py` (Task 1 content).

---

### Task 4: Copy writer files to target engines

- [ ] **Step 1: Copy ksdm_writers to knowledge engine**

Then re-write `__init__.py` files in each target (Task 1 content).

```bash
cp engines/document/writers/ksdm_writers/bi_aggregation/*.py engines/knowledge/models/writers/bi_aggregation/
cp engines/document/writers/ksdm_writers/ml_mining/*.py engines/knowledge/models/writers/ml_mining/
cp engines/document/writers/ksdm_writers/process_mining/*.py engines/knowledge/models/writers/process_mining/
cp engines/document/writers/ksdm_writers/query_models/*.py engines/knowledge/models/writers/query_models/
cp engines/document/writers/ksdm_writers/semantic_graph/*.py engines/knowledge/models/writers/semantic_graph/
```

- [ ] **Step 2: Copy osdm_writers to orchestration engine (flat)**

```bash
cp engines/document/writers/osdm_writers/*.py engines/orchestration/models/writers/
```

Then re-write `engines/orchestration/models/writers/__init__.py` (Task 1 content).

- [ ] **Step 3: Copy bam_writers to orchestration engine (bam/ subdir)**

```bash
cp engines/document/writers/bam_writers/*.py engines/orchestration/models/writers/bam/
```

Then re-write `engines/orchestration/models/writers/bam/__init__.py` (Task 1 content).

- [ ] **Step 4: Copy tsdm_writers to tools engine**

```bash
cp engines/document/writers/tsdm_writers/*.py engines/tools/models/writers/
```

Then re-write `engines/tools/models/writers/__init__.py` (Task 1 content).

---

### Task 5: Update all imports across the codebase

Every file that imports from the old locations needs updating. This is the most critical task.

- [ ] **Step 1: Update KSDM model imports**

Replace all imports from `engines.document.models.ksdm_models` → `engines.knowledge.models.ksdm_models`.

Use `grep` to find all affected files first, then use `sed` to replace:

```bash
rg -l "from engines\.document\.models\.ksdm_models" --type py
rg -l "from engines\.document\.models\.import.*ksdm_models" --type py
```

Patterns to replace:
- `from engines.document.models.ksdm_models import` → `from engines.knowledge.models.ksdm_models import`
- `from engines.document.models import ksdm_models` → `from engines.knowledge.models import ksdm_models`
- `engines.document.models.ksdm_models.` → `engines.knowledge.models.ksdm_models.`

- [ ] **Step 2: Update query_models imports**

```bash
rg -l "from engines\.document\.models\.query_models" --type py
```

Replace: `from engines.document.models.query_models import` → `from engines.knowledge.models.query_models import`

- [ ] **Step 3: Update OSDM model imports**

```bash
rg -l "from engines\.document\.models\.osdm_models" --type py
```

Replace: `from engines.document.models.osdm_models import` → `from engines.orchestration.models.osdm_models import`

- [ ] **Step 4: Update TSDM model imports**

```bash
rg -l "from engines\.document\.models\.tsdm_models" --type py
```

Replace: `from engines.document.models.tsdm_models import` → `from engines.tools.models.tsdm_models import`

- [ ] **Step 5: Update BAM model imports**

```bash
rg -l "from engines\.document\.models\.bam_models" --type py
rg -l "from engines\.document\.models import.*bam" --type py
```

Replace: `from engines.document.models.bam_models import` → `from engines.orchestration.models.bam_models import`

- [ ] **Step 6: Update KSDM parser imports**

```bash
rg -l "from engines\.document\.parsers\.ksdm_parsers" --type py
```

Replace: `from engines.document.parsers.ksdm_parsers.` → `from engines.knowledge.models.parsers.`

- [ ] **Step 7: Update KSDM writer imports**

```bash
rg -l "from engines\.document\.writers\.ksdm_writers" --type py
```

Replace: `from engines.document.writers.ksdm_writers.` → `from engines.knowledge.models.writers.`

- [ ] **Step 8: Update OSDM parser imports**

```bash
rg -l "from engines\.document\.parsers\.osdm_parsers" --type py
rg -l "from engines\.document\.parsers\.bam_parsers" --type py
```

Replace:
- `from engines.document.parsers.osdm_parsers.` → `from engines.orchestration.models.parsers.`
- `from engines.document.parsers.bam_parsers.` → `from engines.orchestration.models.parsers.bam.`

- [ ] **Step 9: Update OSDM writer imports**

```bash
rg -l "from engines\.document\.writers\.osdm_writers" --type py
rg -l "from engines\.document\.writers\.bam_writers" --type py
```

Replace:
- `from engines.document.writers.osdm_writers.` → `from engines.orchestration.models.writers.`
- `from engines.document.writers.bam_writers.` → `from engines.orchestration.models.writers.bam.`

- [ ] **Step 10: Update TSDM parser/writer imports**

```bash
rg -l "from engines\.document\.parsers\.tsdm_parsers" --type py
rg -l "from engines\.document\.writers\.tsdm_writers" --type py
```

Replace:
- `from engines.document.parsers.tsdm_parsers.` → `from engines.tools.models.parsers.`
- `from engines.document.writers.tsdm_writers.` → `from engines.tools.models.writers.`

- [ ] **Step 11: Run import find-and-replace for remaining patterns**

```bash
# Also handle relative imports within ksdm_parsers that reference each other
# e.g., writers/ksdm_writers/bi_aggregation/__init__.py imports from ../query_models/
rg -l "from \.\.query_models" engines/document/writers/ksdm_writers --type py
rg -l "from \.\.query_models" engines/document/parsers/ksdm_parsers --type py
```

---

### Task 6: Update knowledge engine `__init__.py` files

- [ ] **Step 1: Update `engines/knowledge/ml_mining/__init__.py`**

Change from importing from `engines.document.models.ksdm_models` to `engines.knowledge.models.ksdm_models`.

- [ ] **Step 2: Update `engines/knowledge/graph/__init__.py`**

Change `GraphNode`, `GraphEdge` import from `engines.document.models.ksdm_models` to `engines.knowledge.models.ksdm_models`.

- [ ] **Step 3: Update any remaining knowledge engine internal imports**

Check `engines/knowledge/ml_mining/engine.py`, `engines/knowledge/bi_aggregation/engine.py`, etc. for any remaining `engines.document` references that weren't caught in Task 5.

---

### Task 7: Move test directories

- [ ] **Step 1: Move knowledge tests**

```bash
cp tests/knowledge/*.py engines/knowledge/tests/
```

Update imports in test files — replace `from engines.document.models.ksdm_models` → `from engines.knowledge.models.ksdm_models` and similar.

- [ ] **Step 2: Move orchestration tests**

```bash
cp -r tests/orchestration/* engines/orchestration/tests/
```

Update any document model imports in test files.

- [ ] **Step 3: Move tools tests**

```bash
cp tests/tools/*.py engines/tools/tests/
```

Update any document model imports in test files.

---

### Task 8: Delete old files and update document engine `__init__.py`

- [ ] **Step 1: Delete moved model files from document engine**

```bash
rm engines/document/models/ksdm_models.py
rm engines/document/models/query_models.py
rm engines/document/models/osdm_models.py
rm engines/document/models/tsdm_models.py
rm engines/document/models/bam_models.py
```

- [ ] **Step 2: Delete moved parser directories from document engine**

```bash
rm -rf engines/document/parsers/ksdm_parsers/
rm -rf engines/document/parsers/osdm_parsers/
rm -rf engines/document/parsers/tsdm_parsers/
rm -rf engines/document/parsers/bam_parsers/
```

- [ ] **Step 3: Delete moved writer directories from document engine**

```bash
rm -rf engines/document/writers/ksdm_writers/
rm -rf engines/document/writers/osdm_writers/
rm -rf engines/document/writers/tsdm_writers/
rm -rf engines/document/writers/bam_writers/
```

- [ ] **Step 4: Update `engines/document/models/__init__.py`**

Remove the import lines for `ksdm_models`, `osdm_models`, `tsdm_models`, `bam_models`, `query_models` and their corresponding entries in `__all__`.

- [ ] **Step 5: Update `engines/document/parsers/__init__.py`**

Remove any re-exports of moved parser modules (ksdm_parsers, osdm_parsers, tsdm_parsers, bam_parsers).

- [ ] **Step 6: Update `engines/document/writers/__init__.py`**

Remove any re-exports of moved writer modules.

---

### Task 9: Delete old test directories

- [ ] **Step 1: Remove old test directories**

```bash
rm -rf tests/knowledge/
rm -rf tests/orchestration/
rm -rf tests/tools/
```

---

### Task 10: Run tests and verify

- [ ] **Step 1: Run knowledge tests from new location**

```bash
python3 -m pytest engines/knowledge/tests/ -v --tb=short 2>&1 | tail -30
```

Expected: All tests pass.

- [ ] **Step 2: Run orchestration tests from new location**

```bash
python3 -m pytest engines/orchestration/tests/ -v --tb=short 2>&1 | tail -30
```

- [ ] **Step 3: Run tools tests from new location**

```bash
python3 -m pytest engines/tools/tests/ -v --tb=short 2>&1 | tail -30
```

- [ ] **Step 4: Full test collection check**

```bash
python3 -m pytest tests/ --collect-only 2>&1 | tail -20
```

Expected: No import errors — all tests collected successfully.

- [ ] **Step 5: Run remaining tests (agent, communication, document, interaction, memory, storage)**

```bash
python3 -m pytest tests/ -v --tb=short 2>&1 | tail -30
```

---

### Task 11: Update `AGENTS.md` test commands

- [ ] **Step 1: Update test commands in AGENTS.md**

Change:
```markdown
python3 -m pytest tests/knowledge/ -v
```
to:
```markdown
python3 -m pytest engines/knowledge/tests/ -v
python3 -m pytest engines/orchestration/tests/ -v
python3 -m pytest engines/tools/tests/ -v
```

---

### Task 12: Commit

- [ ] **Step 1: Stage and commit all changes**

```bash
git add engines/knowledge/models/
git add engines/orchestration/models/
git add engines/tools/models/
git add -u engines/document/
git add -u engines/knowledge/
git add -u engines/orchestration/
git add -u engines/tools/
git rm -r tests/knowledge/
git rm -r tests/orchestration/
git rm -r tests/tools/
git add AGENTS.md
git commit -m "refactor: move engine-specific models/parsers/writers/tests to owning engines

- KSDM/query models → knowledge engine
- OSDM/BAM models → orchestration engine
- TSDM models → tools engine
- Tests moved alongside their engines
- All imports updated to reference owning engine paths
- Shared/base models remain in engines/document/"
```
