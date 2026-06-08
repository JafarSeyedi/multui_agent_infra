# Agentic BPMN vs Interaction Layer — Overlap Analysis

## Purpose

The agentic BPMN extension in OSDM (`engines/document/models/osdm_models.py`) and the interaction layer (`engines/interaction/`) both describe multi-agent collaboration patterns — but at different levels of abstraction. This document maps the overlap and clarifies the boundary.

## Strategy Mapping

| Agentic BPMN Concept | BPMN Type | Interaction Layer Strategy | Runtime Equivalent |
|---|---|---|---|
| `CollaborationStrategyType.VOTING` | `CollaborationStrategy` | `EnsembleStrategy` | Each agent votes → majority/aggregator |
| `CollaborationStrategyType.ROLE` (leader_driven) | `RoleConfig` | `CoordinatorStrategy` | Leader dispatches → agents execute sequentially |
| `CollaborationStrategyType.ROLE` (composed) | `RoleConfig` | `RoundRobinStrategy` | Agents take turns in order |
| `CollaborationStrategyType.DEBATE` | `CollaborationStrategy` | `DebateStrategy` | Proposer ↔ Critic iterative rounds |
| `CollaborationStrategyType.COMPETITION` | `CompetitionConfig` | `BroadcastStrategy` + fastest-wins | All agents run in parallel → first result wins |
| `ReflectionStrategy.SELF` | (on `AgenticTask`) | `SelfRefineStrategy` | Generate → Critique → Refine loop |
| `ReflectionStrategy.CROSS` | (on `AgenticTask`) | `DebateStrategy` (multi-critic) | Generator output critiqued by other agents |
| `MergeStrategyType.MAJORITY` | `MergeStrategy` | `EnsembleStrategy._aggregate_votes(mode="majority")` | Most common vote wins |
| `MergeStrategyType.LEADER` | `MergeStrategy` | `CoordinatorStrategy._run_validation` | Leader/validator selects best result |
| `MergeStrategyType.FASTEST` | `MergeStrategy` | `BroadcastStrategy` + first-responder | First completed agent output wins |
| `AgenticLane.agent_capabilities` | Lane metadata | (not modelled) | Capability-based agent selection |
| `AgenticMessageFlow` | MessageFlow | `AgentMessage` bus events | Communication protocol metadata |

## What Each Layer Provides

| Concern | Agentic BPMN (OSDM) | Interaction Layer |
|---|---|---|
| **Level** | Modelling / design-time | Runtime execution |
| **Form** | BPMN model elements (subclasses) | Python strategy classes |
| **Purpose** | Specify *what* pattern to use in a diagram | Execute *how* the pattern runs |
| **Persistence** | Serialized in BPMN XML/JSON | Transient Python objects |
| **Agent registry** | `agent_ids` list (references) | `InteractionStrategy.agent_registry` |
| **Message bus** | Not modelled | `InteractionStrategy.message_bus` |
| **Result handling** | `MergeStrategy` (modelling) | `InteractionResult` fields (runtime) |

## Coupling Points

1. **Strategy name overlap**: Both layers define `DEBATE`, `VOTING`, `ROLE` concepts but with different enums (`CollaborationStrategyType` vs `InteractionStrategy.scenario_name`).
2. **Runtime dispatch**: A future compiler would read `DivergingAgenticGateway.collaboration_strategy` → `InteractionStrategyRegistry.get(...)`.
3. **`InteractionStrategy` enum in OSDM**: Line 284 of `osdm_models.py` defines `InteractionStrategy` with values `broadcast`, `debate`, `coordinator`, etc. — this is a **duplicate** of the interaction layer's `scenario_name` strings. This enum should be kept in sync with `engines/interaction/` strategy names.

## Risk: Duplicate Enum

The `InteractionStrategy` enum in `osdm_models.py:284` replicates the scenario names from `engines/interaction/backends/native_backend.py`. If new strategies are added to the interaction layer, this enum must be updated. Consider replacing with a shared constant or importing from `engines.interaction`.

## Recommendation

Keep the separation clear:
- **Agentic BPMN** owns the *what* — modelled in BPMN diagrams.
- **Interaction layer** owns the *how* — runtime strategy execution.
- A thin **adapter/compiler** (not yet implemented) would translate between them.

This avoids circular dependency: `engines.document.models.osdm_models` imports nothing from `engines.interaction`, and vice versa.
