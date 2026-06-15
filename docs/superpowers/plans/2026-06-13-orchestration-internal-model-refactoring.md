# Orchestration Internal Model Refactoring Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Split the 1766-line `osdm_models.py` monolith into engine-specific model files, move parsers/writers into engine directories, relocate tests into engine dirs, and update all ~188 import sites — all in a single big-bang commit.

**Architecture:** 184 classes currently in one file get redistributed into 9 files across 6 engine subdirectories + 2 shared model files in `models/`. Parsers/writers (16 parser + 12 writer files + BAM subdirs) move from `models/parsers/` and `models/writers/` into their respective engine directories. Tests (29 files) move from `engines/orchestration/tests/` into engine-specific `tests/` dirs.

**Tech Stack:** Python 3.11+, pydantic v2, `from __future__ import annotations` for forward references, relative imports within orchestration engine.

**Key constraint:** All imports within `engines/orchestration/` use relative paths. External imports use absolute paths.

---

### Task 1: Create directory structure and `__init__.py` files

**Files:**
- Create: 18 new directories with `__init__.py`

- [ ] **Step 1: Create all engine model directories**

```bash
for dir in bpmn/models bpmn/parsers bpmn/writers bpmn/tests \
           dmn/models dmn/parsers dmn/writers dmn/tests \
           cmmn/models cmmn/parsers cmmn/writers cmmn/tests \
           cep/models cep/parsers cep/writers cep/tests \
           state_machine/models state_machine/parsers state_machine/writers state_machine/tests \
           bam/models bam/parsers bam/writers bam/tests; do
  mkdir -p engines/orchestration/$dir
  touch engines/orchestration/$dir/__init__.py
done
```

### Task 2: Extract `shared_models.py` from `osdm_models.py`

**Files:**
- Create: `engines/orchestration/models/shared_models.py`
- Reference: `engines/orchestration/models/osdm_models.py` (keep original)

- [ ] **Step 1: Create shared_models.py with truly shared classes**

Copy the following from `osdm_models.py` into `models/shared_models.py`:
- Imports: `from __future__ import annotations`, `from dataclasses import dataclass, field`, `from enum import Enum`, `from typing import Any`
- Enums: `ParticipantBandKind`, `MessageVisibleKind`, `AlignmentKind`, `TimerCalculationType`, `TimeReference`, `DurationResolution`, `EscapeType`, `CorrelationPropertyType`, `CaseFileMultiplicity`, `ItemKind`, `TimerEventType`, `RelationshipDirection`, `ResourceParameterType`, `WorkflowStateType`, `PseudoStateKind`
- Classes: `BaseElement`, `RootElement`, `ExtensionAttributeDefinition`, `ExtensionDefinition`, `ExtensionAttributeValue`, `Extension`
- Diagram: `Bounds`, `Locator`, `DiagramElement`, `Edge`, `Shape`
- Error handling: `ErrorHandlingOperator`, `RetryBackoffRate`, `CloudResourceBinding`, `ErrorHandlingConfig`, `RetryConfig`, `TimeoutConfig`
- Document: `BaseOSDMDocument`, `OSDMModel`, `ActionList`
- Also import `BaseDocument` from `engines.document.models.base`, `DocumentStandard` from `engines.document.models.standard`, `DocumentFormat` from `engines.document.models.media_types`, `MSDMDocument`, `Entity` from `engines.document.models.msdm_models`, `SSDMDocument`, `ServiceOperation`, `ServiceBinding` from `engines.document.models.ssdm_models`, `TSDMDocument` from `engines.tools.models.tsdm_models`

### Task 3: Create `bpmn_models.py`

**Files:**
- Create: `engines/orchestration/bpmn/models/bpmn_models.py`
- Reference: `engines/orchestration/models/osdm_models.py`

- [ ] **Step 1: Create bpmn_models.py**

New file with imports:
```python
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from ..models.shared_models import (
    BaseElement, RootElement, BaseOSDMDocument, Bounds, Locator,
    DiagramElement, Edge, Shape, Extension, ExtensionAttributeDefinition,
    ExtensionAttributeValue, ExtensionDefinition,
    ErrorHandlingConfig, RetryConfig, TimeoutConfig,
    ErrorHandlingOperator, RetryBackoffRate, CloudResourceBinding,
    ItemKind, TimerEventType, RelationshipDirection,
    ResourceParameterType, WorkflowStateType, PseudoStateKind,
    ParticipantBandKind, MessageVisibleKind, AlignmentKind,
    TimerCalculationType, TimeReference, DurationResolution,
    EscapeType, CorrelationPropertyType, CaseFileMultiplicity,
)
```

Copy ALL remaining classes that are BPMN-specific from osdm_models.py (the full list from the spec under `bpmn_models.py` section). This includes ~130+ classes.

The imports from `shared_models.py` should use relative paths as shown.

### Task 4: Create DMN, CMMN, CEP, state machine, agentic, and multi-agent model files

**Files:**
- Create: 6 model files

- [ ] **Step 1: Create `dmn/models/dmn_models.py`**

```python
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from ..models.shared_models import BaseElement, BaseOSDMDocument, ...
from ..bpmn.models.bpmn_models import FlowNode, ...
```

Copy: `DecisionLogicType` enum, `InformationRequirement`, `KnowledgeRequirement`, `AuthorityRequirement`, `DecisionService`, `LiteralExpression`, `UnaryTests`, `InputClause`, `OutputClause`, `DecisionRule`, `DecisionTable`, `Decision(FlowNode)`, `BusinessKnowledgeModel(FlowNode)`, `InputData(FlowNode)`, `KnowledgeSource(FlowNode)`, `DMNDefinition`, `Binding`, `Invocation`, `ContextEntry`, `Context`, `Relation`, `FormalParameter`, `FunctionDefinition`, `DMNDocument`

- [ ] **Step 2: Create `cmmn/models/cmmn_models.py`**

```python
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from ..models.shared_models import BaseElement, BaseOSDMDocument, ...
from ..bpmn.models.bpmn_models import Activity, FlowNode, ...
```

Copy: `CaseFileMultiplicity` (already shared), `PlanItem(BaseElement)`, `DiscretionaryItem(PlanItem)`, `CaseFileItem(BaseElement)`, `CaseTask(Activity)`, `ProcessTask(Activity)`, `HumanTask(Activity)`, `ApplicabilityRule(BaseElement)`, `EntryCriterion(BaseElement)`, `ExitCriterion(BaseElement)`, `Stage(FlowNode)`, `Milestone(FlowNode)`, `MilestoneKind(Enum)`, `DecisionTask(Activity)`, `EventListener(FlowNode)`, `Sentry(BaseElement)`, `CMMNDefinition`, `CMMNDocument`

- [ ] **Step 3: Create `cep/models/cep_models.py`**

```python
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from ..models.shared_models import BaseOSDMDocument, ...
```

Copy: `CEPOperator(Enum)`, `EventStream`, `CEPRule`, `CEPDocument`

- [ ] **Step 4: Create `state_machine/models/state_machine_models.py`**

```python
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from ..models.shared_models import BaseElement, BaseOSDMDocument, ...
from ..bpmn.models.bpmn_models import StateNode, Transition, ...
```

Copy: `State(StateNode)`, `StateTransition(Transition)`, `StateInvoke`, `StateMachineRegion(BaseElement)`, `StateMachineModel`, `PseudoState(StateNode)`, `Place(State)`, `PnTransition(Transition)`, `Arc(Transition)`, `StateMachineDocument`

- [ ] **Step 5: Create `models/agentic_models.py`**

```python
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from ..bpmn.models.bpmn_models import Task, MessageFlow, Gateway, Lane
```

Copy: `ReflectionStrategy`, `CollaborationStrategyType`, `MergeStrategyType`, `VotingRule`, `RoleStrategyType`, `CompetitionRule`, `VotingConfig`, `RoleConfig`, `CompetitionConfig`, `CollaborationStrategy`, `MergeStrategy`, `AgenticTask(Task)`, `AgenticMessageFlow(MessageFlow)`, `DivergingAgenticGateway(Gateway)`, `MergingAgenticGateway(Gateway)`, `AgenticLane(Lane)`

- [ ] **Step 6: Create `models/multi_agent_models.py`**

```python
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from ..models.shared_models import BaseElement, BaseOSDMDocument
```

Copy: `InteractionStrategy`, `InteractionProtocol(BaseElement)`, `InteractionModel`, `MultiAgentInteractionDocument(BaseOSDMDocument)`

### Task 5: Move BAM models to `bam/models/`

**Files:**
- Move: `engines/orchestration/models/bam_models.py` → `engines/orchestration/bam/models/bam_models.py`
- Update: imports within `bam/models/bam_models.py`

- [ ] **Step 1: Move and update imports**

```bash
cp engines/orchestration/models/bam_models.py engines/orchestration/bam/models/bam_models.py
```

Update imports in `bam/models/bam_models.py`:
- `from engines.document.models.base import BaseDocument` → keep (external)
- `from engines.document.models.media_types import ...` → keep
- `from engines.document.models.msdm_models import Entity` → keep
- `from engines.orchestration.models.osdm_models import CEPRule, Process` → `from ..cep.models.cep_models import CEPRule` and `from ..bpmn.models.bpmn_models import Process`

### Task 6: Move parsers to engine directories

**Files:**
- Move: 16 parser files + BAM parsers (3 files) → engine `parsers/` dirs
- Update: imports within each parser to point to new model locations

- [ ] **Step 1: Copy parser files to engine directories**

```bash
# BPMN parsers
cp engines/orchestration/models/parsers/bpmn_xml_parser.py engines/orchestration/bpmn/parsers/
cp engines/orchestration/models/parsers/bpmn_collaboration.py engines/orchestration/bpmn/parsers/
cp engines/orchestration/models/parsers/bpmn_constants.py engines/orchestration/bpmn/parsers/
cp engines/orchestration/models/parsers/bpmn_diagram.py engines/orchestration/bpmn/parsers/
cp engines/orchestration/models/parsers/bpmn_flow_parser.py engines/orchestration/bpmn/parsers/
cp engines/orchestration/models/parsers/bpmn_reference_resolver.py engines/orchestration/bpmn/parsers/
cp engines/orchestration/models/parsers/bpmn_root_element.py engines/orchestration/bpmn/parsers/
cp engines/orchestration/models/parsers/epc_parser.py engines/orchestration/bpmn/parsers/
cp engines/orchestration/models/parsers/graphml_xml_parser.py engines/orchestration/bpmn/parsers/
cp engines/orchestration/models/parsers/pnml_xml_parser.py engines/orchestration/bpmn/parsers/
cp engines/orchestration/models/parsers/prefect_dag_parser.py engines/orchestration/bpmn/parsers/
cp engines/orchestration/models/parsers/scxml_parser.py engines/orchestration/bpmn/parsers/
cp engines/orchestration/models/parsers/xpd_parser.py engines/orchestration/bpmn/parsers/
# DMN parsers
cp engines/orchestration/models/parsers/dmn_xml_parser.py engines/orchestration/dmn/parsers/
# CMMN parsers
cp engines/orchestration/models/parsers/cmmn_xml_parser.py engines/orchestration/cmmn/parsers/
# CEP parsers
cp engines/orchestration/models/parsers/cep_parser.py engines/orchestration/cep/parsers/
# State Machine parsers
cp engines/orchestration/models/parsers/uml_state_machine_parser.py engines/orchestration/state_machine/parsers/
# BAM parsers
cp -r engines/orchestration/models/parsers/bam/ engines/orchestration/bam/parsers/
```

- [ ] **Step 2: Update imports in each parser**

Each parser that imports from `engines.orchestration.models.osdm_models` or `..osdm_models` must be updated to point to the new model locations. The pattern is:

For BPMN parsers (in `bpmn/parsers/`):
```python
# Old: from engines.orchestration.models.osdm_models import Process, Task, ...
# New:
from ..models.bpmn_models import Process, Task, ...
from ..models.shared_models import BaseElement, ...
```

For DMN parsers (in `dmn/parsers/`):
```python
from ..models.dmn_models import Decision, DecisionTable, ...
```

For CMMN parsers (in `cmmn/parsers/`):
```python
from ..models.cmmn_models import Stage, Milestone, ...
```

For CEP parsers (in `cep/parsers/`):
```python
from ..models.cep_models import CEPRule, EventStream, ...
```

For State Machine parsers (in `state_machine/parsers/`):
```python
from ..models.state_machine_models import State, StateMachineModel, ...
```

For BAM parsers (in `bam/parsers/`):
```python
from ..models.bam_models import MetricDefinition, ...
```

### Task 7: Move writers to engine directories

**Files:**
- Move: 12 writer files + BAM writers (3 files) → engine `writers/` dirs
- Update: imports within each writer

- [ ] **Step 1: Copy writer files to engine directories**

```bash
# BPMN writers
cp engines/orchestration/models/writers/bpmn_xml_writer.py engines/orchestration/bpmn/writers/
cp engines/orchestration/models/writers/epc_writer.py engines/orchestration/bpmn/writers/
cp engines/orchestration/models/writers/graphml_xml_writer.py engines/orchestration/bpmn/writers/
cp engines/orchestration/models/writers/pnml_xml_writer.py engines/orchestration/bpmn/writers/
cp engines/orchestration/models/writers/prefect_dag_writer.py engines/orchestration/bpmn/writers/
cp engines/orchestration/models/writers/scxml_writer.py engines/orchestration/bpmn/writers/
cp engines/orchestration/models/writers/xpd_writer.py engines/orchestration/bpmn/writers/
# DMN writers
cp engines/orchestration/models/writers/dmn_xml_writer.py engines/orchestration/dmn/writers/
# CMMN writers
cp engines/orchestration/models/writers/cmmn_xml_writer.py engines/orchestration/cmmn/writers/
# CEP writers
cp engines/orchestration/models/writers/cep_writer.py engines/orchestration/cep/writers/
# State Machine writers
cp engines/orchestration/models/writers/uml_state_machine_writer.py engines/orchestration/state_machine/writers/
# BAM writers
cp -r engines/orchestration/models/writers/bam/ engines/orchestration/bam/writers/
```

- [ ] **Step 2: Update imports in each writer**

Same pattern as parsers — update all `from engines.orchestration.models.osdm_models import X` to relative imports from the new model locations.

### Task 8: Update orchestration engine imports (all modules)

**Files:** All 175 import sites within `engines/orchestration/`

- [ ] **Step 1: Bulk-update with sed (pattern-based)**

The most common patterns across orchestration engine files:

**Pattern 1:** `from engines.orchestration.models.osdm_models import ...` → relative import
```python
# In bpmn/ files:
from ..bpmn.models.bpmn_models import Process, Task, ...
# In dmn/ files:
from ..dmn.models.dmn_models import ...
# etc
```

**Pattern 2:** `from .osdm_models import ...` → relative import
```python
from .bpmn_models import ...
```

**Pattern 3:** `from engines.orchestration.models.parsers.bpmn_xml_parser import ...` → relative
```python
from ..bpmn.parsers.bpmn_xml_parser import ...
```

- [ ] **Step 2: Fix imports in `bpmn/engine.py`** (imports parsers)
- [ ] **Step 3: Fix imports in `bpmn/process_model.py`** (imports osdm_models)
- [ ] **Step 4: Fix imports in all BPMN handlers** (activity_handler, event_handler, gateway_handler, loop_handler, etc.)
- [ ] **Step 5: Fix imports in `dmn/engine.py`**
- [ ] **Step 6: Fix imports in DMN modules** (decision_executor, decision_table_evaluator, etc.)
- [ ] **Step 7: Fix imports in `cmmn/engine.py`** and all CMMN handlers
- [ ] **Step 8: Fix imports in `cep/` modules** (engine, pattern_matcher, etc.)
- [ ] **Step 9: Fix imports in `state_machine/` modules** (engine, state_executor, etc.)
- [ ] **Step 10: Fix imports in `bam/engine.py`**
- [ ] **Step 11: Fix imports in any orchestrator-level files**

### Task 9: Update external imports (knowledge, agent, tools, tests)

**Files:** ~13 sites outside `engines/orchestration/`

- [ ] **Step 1: Fix imports in `engines/knowledge/`**

```python
# Old: from engines.orchestration.models.osdm_models import Process
# New: from engines.orchestration.bpmn.models.bpmn_models import Process
```

- [ ] **Step 2: Fix imports in `engines/agent/`**

```python
# Old: from engines.orchestration.models.osdm_models import StateMachineModel
# New: from engines.orchestration.state_machine.models.state_machine_models import StateMachineModel
```

- [ ] **Step 3: Fix imports in root `tests/`**

Update `tests/document/test_bam_*.py` files to import from `engines.orchestration.bam.models.bam_models` instead of `engines.orchestration.models.bam_models`.

### Task 10: Delete old files and update `models/__init__.py`

- [ ] **Step 1: Update `models/__init__.py`**

Remove reference to `osdm_models` and `bam_models`. Add re-exports from all new model files.

- [ ] **Step 2: Delete old `osdm_models.py`**

```bash
rm engines/orchestration/models/osdm_models.py
```

- [ ] **Step 3: Delete old parser/writer files (keep base parsers/writers)**

DO NOT delete `base_osdm_parser.py` or `base_osdm_writer.py` — they stay as shared infrastructure.

```bash
# Delete BPMN parsers (old location)
rm engines/orchestration/models/parsers/bpmn_xml_parser.py
rm engines/orchestration/models/parsers/bpmn_collaboration.py
rm engines/orchestration/models/parsers/bpmn_constants.py
rm engines/orchestration/models/parsers/bpmn_diagram.py
rm engines/orchestration/models/parsers/bpmn_flow_parser.py
rm engines/orchestration/models/parsers/bpmn_reference_resolver.py
rm engines/orchestration/models/parsers/bpmn_root_element.py
rm engines/orchestration/models/parsers/epc_parser.py
rm engines/orchestration/models/parsers/graphml_xml_parser.py
rm engines/orchestration/models/parsers/pnml_xml_parser.py
rm engines/orchestration/models/parsers/prefect_dag_parser.py
rm engines/orchestration/models/parsers/scxml_parser.py
rm engines/orchestration/models/parsers/xpd_parser.py
# Delete DMN parsers
rm engines/orchestration/models/parsers/dmn_xml_parser.py
# Delete CMMN parsers
rm engines/orchestration/models/parsers/cmmn_xml_parser.py
# Delete CEP parsers
rm engines/orchestration/models/parsers/cep_parser.py
# Delete State Machine parsers
rm engines/orchestration/models/parsers/uml_state_machine_parser.py
# Leave base_osdm_parser.py in place!

# Delete BPMN writers (old location)
rm engines/orchestration/models/writers/bpmn_xml_writer.py
rm engines/orchestration/models/writers/epc_writer.py
rm engines/orchestration/models/writers/graphml_xml_writer.py
rm engines/orchestration/models/writers/pnml_xml_writer.py
rm engines/orchestration/models/writers/prefect_dag_writer.py
rm engines/orchestration/models/writers/scxml_writer.py
rm engines/orchestration/models/writers/xpd_writer.py
# Delete DMN writers
rm engines/orchestration/models/writers/dmn_xml_writer.py
# Delete CMMN writers
rm engines/orchestration/models/writers/cmmn_xml_writer.py
# Delete CEP writers
rm engines/orchestration/models/writers/cep_writer.py
# Delete State Machine writers
rm engines/orchestration/models/writers/uml_state_machine_writer.py
# Leave base_osdm_writer.py in place!
```

- [ ] **Step 4: Delete old `bam_models.py`**

```bash
rm engines/orchestration/models/bam_models.py
```

- [ ] **Step 5: Delete old BAM parser/writer directories**

```bash
rm -rf engines/orchestration/models/parsers/bam/
rm -rf engines/orchestration/models/writers/bam/
```

### Task 11: Move test files

**Files:** 29 test files from `engines/orchestration/tests/test_*/`

- [ ] **Step 1: Copy test files to engine directories**

```bash
# BPMN tests
cp engines/orchestration/tests/test_bpmn/*.py engines/orchestration/bpmn/tests/
# DMN tests
cp engines/orchestration/tests/test_dmn/*.py engines/orchestration/dmn/tests/
# CMMN tests
cp engines/orchestration/tests/test_cmmn/*.py engines/orchestration/cmmn/tests/
# CEP tests
cp engines/orchestration/tests/test_cep/*.py engines/orchestration/cep/tests/
# State Machine tests
cp engines/orchestration/tests/test_state_machine/*.py engines/orchestration/state_machine/tests/
# BAM tests
cp engines/orchestration/tests/test_bam/*.py engines/orchestration/bam/tests/
```

- [ ] **Step 2: Update test imports**

Each test file imports from `engines.orchestration.models.osdm_models` or `engines.orchestration.models.bam_models`. Update to absolute imports pointing to the new locations:

```python
# Old: from engines.orchestration.models.osdm_models import Process, Task
# New: from engines.orchestration.bpmn.models.bpmn_models import Process, Task
```

- [ ] **Step 3: Delete old test directories**

```bash
rm -rf engines/orchestration/tests/test_bpmn
rm -rf engines/orchestration/tests/test_dmn
rm -rf engines/orchestration/tests/test_cmmn
rm -rf engines/orchestration/tests/test_cep
rm -rf engines/orchestration/tests/test_state_machine
rm -rf engines/orchestration/tests/test_bam
```

Keep `engines/orchestration/tests/test_core/` and `engines/orchestration/tests/test_multi_agent/` and `engines/orchestration/tests/test_command.py`.

### Task 12: Run full test suite

- [ ] **Step 1: Run orchestration tests**

```bash
python3 -m pytest engines/orchestration/ -v 2>&1 | head -150
```

Expected: all tests pass except the known pre-existing failure `test_bpmn_message_wait_path_persists_waiting_token_and_subscription`.

- [ ] **Step 2: Run dependent engine tests**

```bash
python3 -m pytest engines/knowledge/tests/ -v 2>&1 | tail -30
python3 -m pytest tests/document/test_bam* -v 2>&1 | tail -30
```

- [ ] **Step 3: Fix any import errors**

If any import errors appear, trace the missing import, determine the correct new path, and fix it.

### Task 13: Cleanup — remove old parser/writer `__init__.py` stubs

- [ ] **Step 1: Check if any old parser/writer init files reference moved modules**

```bash
grep -r "parsers\|writers" engines/orchestration/models/ --include="__init__.py"
```

- [ ] **Step 2: Clean up old `models/parsers/__init__.py` and `models/writers/__init__.py`**

Remove any re-exports or imports that point to files that no longer exist.

### Task 14: Final verification and commit

- [ ] **Step 1: Verify no dangling imports**

```bash
grep -rn "engines.orchestration.models.osdm_models\|engines.orchestration.models.bam_models" --include="*.py" . | grep -v __pycache__
```

Expected: 0 results.

- [ ] **Step 2: Run final full test suite**

```bash
python3 -m pytest engines/orchestration/ -v
```

- [ ] **Step 3: Commit**

```bash
git add engines/orchestration/
git commit -m "refactor(orchestration): split osdm_models.py into engine-specific model files, move parsers/writers/tests to engine dirs

- Split osdm_models.py (1766 lines, 184 classes) into 9 files:
  shared_models.py, bpmn_models.py, dmn_models.py, cmmn_models.py,
  cep_models.py, state_machine_models.py, agentic_models.py,
  multi_agent_models.py
- Moved 16 parser files into bpmn/parsers/, dmn/parsers/,
  cmmn/parsers/, cep/parsers/, state_machine/parsers/
- Moved 12 writer files into bpmn/writers/, dmn/writers/,
  cmmn/writers/, cep/writers/, state_machine/writers/
- Moved BAM models/parsers/writers into bam/models/, bam/parsers/,
  bam/writers/
- Moved 29 test files into engine-specific tests/ dirs
- Updated ~188 import sites to use relative imports within
  orchestration engine, absolute imports from external packages"
```
