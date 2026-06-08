# OSDM Agentic BPMN Extension — BPMN 2.0 Compliance

## Extension Type

Per BPMN 2.0 §14 (Extensions), these additions are **standard BPMN extensions** — they subclass existing BPMN 2.0 types and add vendor-specific attributes without breaking the base specification.

## Per-Element Compliance

### `AgenticTask`

| Aspect | Status |
|---|---|
| **Extends** | `Task` → `Activity` → `FlowNode` → `FlowElement` → `BaseElement` |
| **Base spec compliance** | Fully inherits BPMN 2.0 §8.5 Task semantics (I/O, loop, multi-instance) |
| **Added fields** | `reflection_strategy`, `human_feedback_enabled`, `agent_id`, `trust_threshold`, `max_reflection_rounds`, `reflection_config`, `agent_ids` |
| **BPMN 2.0 clause** | §8.5 Task — extended with agent-specific attributes |
| **Serialization** | XML via `extensionElements` or custom element namespace |
| **Status** | ✅ Compliant |

### `AgenticLane`

| Aspect | Status |
|---|---|
| **Extends** | `Lane` → `BaseElement` |
| **Base spec compliance** | Fully inherits BPMN 2.0 §11.1 Lane semantics (partition, flow node refs, resources) |
| **Added fields** | `trust_score`, `agent_id`, `agent_capabilities`, `model_provider`, `system_prompt` |
| **BPMN 2.0 clause** | §11.1 Lane — extended with agent metadata |
| **Serialization** | XML via `extensionElements` on `<bpmn:lane>` |
| **Status** | ✅ Compliant |

### `DivergingAgenticGateway`

| Aspect | Status |
|---|---|
| **Extends** | `Gateway` → `FlowNode` → `FlowElement` → `BaseElement` |
| **Base spec compliance** | Inherits BPMN 2.0 §10.5 Gateway semantics (gateway type + direction) |
| **Added fields** | `collaboration_strategy` (`CollaborationStrategy`), `agent_ids`, `min_agents` |
| **BPMN 2.0 clause** | §10.5 Gateway — extended with agent fan-out semantics |
| **Gateway type** | Inherits `GatewayType.EXCLUSIVE` by default (can be overridden) |
| **Status** | ⚠️ Requires custom gateway direction logic — not a standard XOR/AND split |

### `MergingAgenticGateway`

| Aspect | Status |
|---|---|
| **Extends** | `Gateway` → `FlowNode` → `FlowElement` → `BaseElement` |
| **Base spec compliance** | Inherits BPMN 2.0 §10.5 Gateway semantics |
| **Added fields** | `merge_strategy` (`MergeStrategy`), `wait_for_all`, `timeout_seconds` |
| **BPMN 2.0 clause** | §10.5 Gateway — extended with agent fan-in semantics |
| **Status** | ⚠️ Requires custom merge logic — not a standard gateway type |

### `AgenticMessageFlow`

| Aspect | Status |
|---|---|
| **Extends** | `MessageFlow` → `BaseElement` |
| **Base spec compliance** | Fully inherits BPMN 2.0 §15.2.2 MessageFlow semantics (source, target, message ref) |
| **Added fields** | `agent_communication`, `communication_protocol`, `reflection_enabled` |
| **BPMN 2.0 clause** | §15.2.2 MessageFlow — extended with agent communication metadata |
| **Status** | ✅ Compliant |

## Extension-Aware Serialization (Proposed)

For XML serialization, agentic attributes would be stored in a custom namespace:

```xml
<bpmn:task id="Task_1" name="Analyze data">
  <bpmn:extensionElements>
    <agn:agenticTask
      reflectionStrategy="self"
      trustThreshold="0.8"
      maxReflectionRounds="3"/>
  </bpmn:extensionElements>
</bpmn:task>
```

## Summary

| Element | BPMN 2.0 Compliant | Extension Type |
|---|---|---|
| `AgenticTask` | ✅ | Standard extension of Task |
| `AgenticLane` | ✅ | Standard extension of Lane |
| `DivergingAgenticGateway` | ⚠️ | Extension of Gateway (custom routing) |
| `MergingAgenticGateway` | ⚠️ | Extension of Gateway (custom merge) |
| `AgenticMessageFlow` | ✅ | Standard extension of MessageFlow |
