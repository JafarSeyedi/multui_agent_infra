# Agentic BPMN Extension — Design Rationale

## 1. Motivation

Standard BPMN 2.0 models business processes with tasks, gateways, lanes, and message flows — but has no native concept of **AI agent collaboration**. As multi-agent systems become first-class process participants, we need to model who executes what, how agents collaborate, and how their outputs are merged, all within the same BPMN diagram.

## 2. Design Approach

We extend existing BPMN 2.0 types via **subclassing** rather than creating new top-level elements:

| BPMN 2.0 Type | Agentic Subclass | Extension |
|---|---|---|
| `Task` | `AgenticTask` | Reflection strategy, agent binding, trust threshold, human feedback |
| `Lane` | `AgenticLane` | Trust score, agent ID, capabilities, model provider, system prompt |
| `Gateway` | `DivergingAgenticGateway` | Collaboration strategy (voting/role/debate/competition), agent dispatch |
| `Gateway` | `MergingAgenticGateway` | Merge strategy (majority/leader/fastest/most_complete) |
| `MessageFlow` | `AgenticMessageFlow` | Agent communication protocol, reflection toggle |

Strategy configuration objects (`VotingConfig`, `RoleConfig`, `CompetitionConfig`, `CollaborationStrategy`, `MergeStrategy`) are plain `@dataclass` — they do **not** inherit `BaseElement`, as they are configuration values, not BPMN model elements.

## 3. Relationship with `engines/interaction/`

The interaction layer (`engines/interaction/`) provides **runtime** strategies: Broadcast, Debate, Coordinator, Ensemble, RoundRobin, SelfRefine, GroupChat. The agentic BPMN extension provides **modelling-time** strategy specification:

| BPMN `CollaborationStrategyType` | Maps to Interaction Strategy |
|---|---|
| `VOTING` | `EnsembleStrategy` |
| `ROLE` (leader_driven) | `CoordinatorStrategy` |
| `ROLE` (composed) | `RoundRobinStrategy` |
| `DEBATE` | `DebateStrategy` |
| `COMPETITION` | `BroadcastStrategy` (fastest-wins variant) |
| BPMN `ReflectionStrategy.SELF` | `SelfRefineStrategy` |
| BPMN `ReflectionStrategy.CROSS` | `DebateStrategy` (multi-critic) |

The BPMN model specifies **what** collaboration pattern to use; the interaction layer provides **how** to execute it. A runtime compiler would translate BPMN `CollaborationStrategy` → `InteractionStrategyRegistry.get(scenario)`.

## 4. Alternative Design Considered

The original (simpler) design considered three distinct task types instead of a single `AgenticTask`:

- **`AgentTask`** — single-agent task (agent_id + reflection)
- **`SkillTask`** — skill/tool execution task
- **`AgentInteractionTask`** — multi-agent collaboration (strategy + participants)

This was rejected for the current iteration because:
1. It would require a new task type hierarchy alongside `Task`, increasing model surface area.
2. Agent collaboration is often an _attribute_ of a task rather than a fundamentally different task kind.
3. `AgenticTask` with optional `agent_ids` and `collaboration_strategy` can cover all three cases.

A future refactor may adopt the simpler task types if the single `AgenticTask` becomes too overloaded.

## 5. Key Design Decisions

- **`AgenticTask`** holds both single-agent (`agent_id`, `reflection_strategy`) and multi-agent (`agent_ids`, `reflection_config`) fields — the runtime decides which to use based on presence of `agent_ids`.
- **`AgenticLane`** mirrors the BPMN `Lane` pattern: each lane represents one participant (agent), with capabilities and system prompt.
- **Diverging/Merging gateways** form a pair for multi-agent fan-out/fan-in, analogous to parallel gateway splits/joins.
- **`AgenticMessageFlow`** adds `agent_communication: bool = True` to distinguish agent-to-agent flows from regular message flows.
- Strategy configs are `@dataclass` without BPMN IDs — they are embedded values, not elements addressable by `id`.

## 6. Future Directions

- **Runtime compiler**: Translate agentic BPMN models into `InteractionRequest` objects against the interaction layer.
- **`AgentInteractionTask` / `SkillTask`**: Simplify `AgenticTask` if it grows unwieldy.
- **Dynamic agent discovery**: Replace `agent_ids` with capability-based queries.
- **Visual notation**: Define BPMN 2.0 extension markers (e.g., custom icon for agentic tasks with a "robot" decoration).
