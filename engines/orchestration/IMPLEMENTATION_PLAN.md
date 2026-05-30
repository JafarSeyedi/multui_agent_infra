# Orchestration Runtime Upgrade Plan

## Goal
- Upgrade `engines/orchestration` from scaffold/lightweight runtime code to a model-driven orchestration runtime aligned with:
  - `engines/document/models/osdm_models.py`
  - `engines/document/models/msdm_models.py`
  - `engines/document/models/dsdm_models.py`
  - `engines/storage/*`
- Make the work resumable in slices, with clear checkpoints and file-level TODOs.

## Core Rules
- All runtime records must be represented with MSDM-defined structures.
- All persisted runtime data must be serialized through DSDM-compatible documents/writers.
- Time-based runtime data must prefer time-series/event-log persistence.
- Engine-specific runtimes must share core execution, correlation, scheduling, tracing, and persistence primitives.
- No engine may rely on service-specific hardcoded logic when an OSDM concept exists.

## Delivery Phases

### Phase 1 — Runtime Data Foundation
- Build a reusable runtime-record schema layer for orchestration runtime objects.
- Introduce DSDM-backed serialization helpers for runtime records.
- Integrate state persistence with `engines/storage` adapters.
- Wire the first engine path (`bpmn`) to the upgraded persistence layer.

### Phase 2 — Core Runtime Refactor
- Replace ad hoc runtime classes with OSDM-aware execution records.
- Refactor context, token, instance, scheduler, correlation, and event bus to use shared runtime records and repositories.
- Make all lifecycle, audit, timer, and variable events persistable and replayable.

### Phase 3 — Persistence and Observability
- Upgrade repositories to support key-value, relational, event-log, and time-series backends.
- Add runtime audit trails, event streams, job/timer history, and metrics traces.
- Add recovery/replay and migration support.

### Phase 4 — BPMN Completion
- Rework BPMN runtime to support full OSDM/BPMN semantics: activities, gateways, event definitions, MI/loop, compensation, transactions, choreography, collaboration, data objects, lanes/participants, boundary/event subprocess semantics.

### Phase 5 — CMMN / State Machine / DMN
- Rework CMMN case runtime to support sentries, planning, discretionary items, case file items, and milestone/state semantics.
- Rework state-machine runtime to support hierarchy, parallel regions, history, pseudostates, and event/action semantics.
- Rework DMN runtime to support complete decision tables, FEEL, decision services, invocation, and hit policies.

### Phase 6 — CEP / Multi-Agent / Integration
- Rework CEP runtime with windowing, correlation, aggregation, temporal operators, and persistence.
- Rework multi-agent runtime with protocol-aware interaction, routing, negotiation, and coordination state.
- Align integration layer with communication/runtime/data mapping layers.

### Phase 7 — API / Deployment / Validation / Tests
- Upgrade public APIs to expose model-driven runtime features.
- Upgrade deployment/version/migration to support instance-safe evolution.
- Deepen validators against OSDM semantic requirements.
- Add engine test suites and replay scenarios.

## Continuation Checkpoints
- **Checkpoint A:** Runtime schema + DSDM/state persistence foundation complete.
- **Checkpoint B:** Core execution primitives refactored and persisted.
- **Checkpoint C:** BPMN runtime upgraded to production-grade semantics baseline.
- **Checkpoint D:** CMMN / State Machine / DMN parity slice complete.
- **Checkpoint E:** CEP / Multi-Agent / integrations complete.
- **Checkpoint F:** APIs, validators, deployment, tests, and recovery complete.

## Folder and File TODOs

### Root Docs
- [ ] `engines/orchestration/README.md` — rewrite around model-driven runtime architecture, storage strategy, replay, and engine parity guarantees.
- [ ] `engines/orchestration/STRUCTURE.md` — update from folder inventory to real execution architecture and dependencies.
- [ ] `engines/orchestration/FILE_MANIFEST.md` — regenerate with file purpose, ownership, and runtime maturity status.
- [ ] `engines/orchestration/TREE_VIEW.txt` — regenerate after structural changes.
- [ ] `engines/orchestration/__init__.py` — export only stable public APIs after refactor.
- [ ] `engines/orchestration/create_files.sh` — remove or limit to scaffolding-only use after implementation stabilizes.

### `core/`
- [ ] `engines/orchestration/core/__init__.py` — export only persisted/model-driven runtime primitives.
- [ ] `engines/orchestration/core/context.py` — replace loose variable storage with MSDM/DSDM-backed scoped execution state and serialization hooks.
- [ ] `engines/orchestration/core/correlation.py` — align message/signal/correlation semantics with OSDM event/message definitions and persistent subscriptions.
- [ ] `engines/orchestration/core/engine.py` — make deployment, definition registry, instance lifecycle, and engine dispatch storage-backed and OSDM-aware.
- [ ] `engines/orchestration/core/event_bus.py` — persist domain events, support replay, filtering, ordering, and observability hooks.
- [ ] `engines/orchestration/core/instance.py` — replace ad hoc instance/activity state with schema-backed runtime records for process/case/state/decision instances.
- [ ] `engines/orchestration/core/scheduler.py` — persist jobs/timers, support recovery, retries, cron/calendar/timer-definition semantics.
- [ ] `engines/orchestration/core/token.py` — align token semantics with BPMN/state/petri-like execution models and persist token history.
- [ ] `engines/orchestration/core/transaction.py` — support compensation, transaction boundaries, retries, and durable transaction/audit history.

### `runtime/`
- [ ] `engines/orchestration/runtime/__init__.py` — export the new runtime record/schema layer and stable managers only.
- [ ] `engines/orchestration/runtime/compensation.py` — support full compensation stack, ordering, scope, and audit records.
- [ ] `engines/orchestration/runtime/error_handler.py` — classify runtime/definition/integration/storage errors and persist recovery actions.
- [ ] `engines/orchestration/runtime/executor.py` — support async orchestration tasks, retries, cancellation, backpressure, and lifecycle tracing.
- [ ] `engines/orchestration/runtime/resource_manager.py` — manage runtime resources, leases, quotas, and concurrency limits.
- [ ] `engines/orchestration/runtime/state_manager.py` — persist state snapshots/history through DSDM + storage adapters, with reload/replay support.
- [ ] `engines/orchestration/runtime/timer_manager.py` — map OSDM timer semantics to persistent scheduler/timer records.
- [ ] `engines/orchestration/runtime/variable_manager.py` — support scoped variables, DSDM serialization, schema binding, and conflict/version control.

### `persistence/`
- [ ] `engines/orchestration/persistence/__init__.py` — expose storage-backed repositories and codecs.
- [ ] `engines/orchestration/persistence/repository.py` — add DSDM/MSDM-aware codec helpers and storage-backed repository abstractions.
- [ ] `engines/orchestration/persistence/instance_repository.py` — persist instance records, current snapshot, and lifecycle transitions.
- [ ] `engines/orchestration/persistence/event_repository.py` — persist runtime/event-bus/domain events with correlation and replay querying.
- [ ] `engines/orchestration/persistence/history_repository.py` — store audit/history timelines in time-series/event-log friendly form.
- [ ] `engines/orchestration/persistence/definition_repository.py` — store versioned deployed definitions plus source/parsed/runtime-ready forms.
- [ ] `engines/orchestration/persistence/variable_repository.py` — persist scoped variable revisions with schema binding and time-based history.

### `bpmn/`
- [ ] `engines/orchestration/bpmn/__init__.py` — export stable BPMN runtime surface only.
- [ ] `engines/orchestration/bpmn/engine.py` — orchestrate BPMN execution with durable state, eventing, error handling, and persistence hooks.
- [ ] `engines/orchestration/bpmn/process_executor.py` — implement full process traversal, scope creation, token routing, and event semantics.
- [ ] `engines/orchestration/bpmn/activity_handler.py` — support all task/activity kinds, boundary behavior, IO mapping, async/await, compensation markers.
- [ ] `engines/orchestration/bpmn/gateway_handler.py` — support exclusive/inclusive/parallel/event-based/complex gateway semantics correctly.
- [ ] `engines/orchestration/bpmn/event_handler.py` — implement start/end/intermediate/boundary/event-subprocess/message/signal/error/escalation/link/timer/cancel semantics.
- [ ] `engines/orchestration/bpmn/sequence_flow.py` — support condition evaluation, default flows, skip logic, and execution graph semantics.
- [ ] `engines/orchestration/bpmn/data_object_handler.py` — bind BPMN data objects/stores/messages to MSDM/DSDM models and persistence.
- [ ] `engines/orchestration/bpmn/collaboration_handler.py` — support participants, message flow, lanes, pools, conversation/collaboration semantics.
- [ ] `engines/orchestration/bpmn/choreography_handler.py` — support choreography tasks, loop types, and participant/message coordination.
- [ ] `engines/orchestration/bpmn/transaction_handler.py` — support BPMN transaction subprocess and cancellation/compensation semantics.
- [ ] `engines/orchestration/bpmn/adhoc_handler.py` — support ad hoc subprocess ordering, completion, and activation rules.
- [ ] `engines/orchestration/bpmn/loop_handler.py` — support standard loops, MI sequential/parallel, completion conditions, cardinality, collections.
- [ ] `engines/orchestration/bpmn/global_task_handler.py` — support global tasks/callable behavior and reuse across call activities.

### `cmmn/`
- [ ] `engines/orchestration/cmmn/__init__.py` — export stable CMMN runtime APIs.
- [ ] `engines/orchestration/cmmn/engine.py` — coordinate case lifecycle, durable state, and sentry/event interaction.
- [ ] `engines/orchestration/cmmn/case_executor.py` — implement case plan model execution and state transitions.
- [ ] `engines/orchestration/cmmn/stage_handler.py` — implement stage activation/completion/reentry/nesting semantics.
- [ ] `engines/orchestration/cmmn/task_handler.py` — support human/process/case/decision/task execution kinds.
- [ ] `engines/orchestration/cmmn/milestone_handler.py` — support milestone state, criteria, and auditing.
- [ ] `engines/orchestration/cmmn/sentry_evaluator.py` — support entry/exit criteria with event and condition parts.
- [ ] `engines/orchestration/cmmn/case_file_manager.py` — bind case file items/data to MSDM/DSDM and persistence.
- [ ] `engines/orchestration/cmmn/discretionary_handler.py` — support discretionary items and planning activation.
- [ ] `engines/orchestration/cmmn/planning_table_handler.py` — support planning table behavior and authorized planning actions.

### `state_machine/`
- [ ] `engines/orchestration/state_machine/__init__.py` — export stable state-machine runtime APIs.
- [ ] `engines/orchestration/state_machine/engine.py` — coordinate durable state-machine lifecycle and event dispatch.
- [ ] `engines/orchestration/state_machine/state_executor.py` — implement state entry/exit/do behavior and nested execution.
- [ ] `engines/orchestration/state_machine/transition_handler.py` — implement trigger matching, guard evaluation, priority/order, and target resolution.
- [ ] `engines/orchestration/state_machine/guard_evaluator.py` — support expression languages and contextual data access.
- [ ] `engines/orchestration/state_machine/action_executor.py` — execute entry/exit/transition actions with integration/runtime hooks.
- [ ] `engines/orchestration/state_machine/history_manager.py` — support shallow/deep history persistence and restoration.
- [ ] `engines/orchestration/state_machine/parallel_state_handler.py` — support orthogonal regions and join/termination behavior.
- [ ] `engines/orchestration/state_machine/hierarchical_handler.py` — support hierarchical nesting, pseudostates, and parent-child propagation.

### `dmn/`
- [ ] `engines/orchestration/dmn/__init__.py` — export stable DMN runtime APIs.
- [ ] `engines/orchestration/dmn/engine.py` — coordinate decision execution and integration with process/case runtimes.
- [ ] `engines/orchestration/dmn/decision_executor.py` — support decision graph traversal and dependency resolution.
- [ ] `engines/orchestration/dmn/decision_table_evaluator.py` — support input/output clauses, rule matching, types, and annotations.
- [ ] `engines/orchestration/dmn/literal_expression_eval.py` — support literal expression execution with typed context.
- [ ] `engines/orchestration/dmn/invocation_handler.py` — support invocation/business knowledge/decision service behavior.
- [ ] `engines/orchestration/dmn/feel_engine.py` — complete FEEL coverage progressively, with strict typing and function libraries.
- [ ] `engines/orchestration/dmn/hit_policy_handler.py` — support all DMN hit policies with exact semantics.

### `cep/`
- [ ] `engines/orchestration/cep/__init__.py` — export stable CEP runtime APIs.
- [ ] `engines/orchestration/cep/engine.py` — coordinate pattern execution and durable streaming/runtime state.
- [ ] `engines/orchestration/cep/pattern_matcher.py` — implement event sequence, absence, threshold, and temporal operators.
- [ ] `engines/orchestration/cep/window_manager.py` — support tumbling/sliding/session/time/count windows and recovery.
- [ ] `engines/orchestration/cep/aggregator.py` — support aggregate functions and grouped aggregations.
- [ ] `engines/orchestration/cep/stream_processor.py` — manage ingest, watermark/order, and stream state transitions.
- [ ] `engines/orchestration/cep/rule_evaluator.py` — evaluate CEP rules against typed event/context data.
- [ ] `engines/orchestration/cep/event_store.py` — persist/query event streams in time-series/event-log storage.

### `multi_agent/`
- [ ] `engines/orchestration/multi_agent/__init__.py` — export stable multi-agent runtime APIs.
- [ ] `engines/orchestration/multi_agent/engine.py` — coordinate agent interaction lifecycle and durable conversation state.
- [ ] `engines/orchestration/multi_agent/agent_executor.py` — execute agent behaviors with runtime context and retry/control semantics.
- [ ] `engines/orchestration/multi_agent/interaction_handler.py` — manage interaction state and OSDM interaction model semantics.
- [ ] `engines/orchestration/multi_agent/protocol_handler.py` — implement protocol-specific behavior and transitions.
- [ ] `engines/orchestration/multi_agent/message_router.py` — support addressing, routing, broadcast, and persistent delivery/audit.
- [ ] `engines/orchestration/multi_agent/coordination_handler.py` — support coordination/consensus/orchestration patterns.
- [ ] `engines/orchestration/multi_agent/negotiation_handler.py` — support negotiation phases, offers, acceptance, and timeout handling.

### `integration/`
- [ ] `engines/orchestration/integration/__init__.py` — export stable integration APIs only.
- [ ] `engines/orchestration/integration/service_invoker.py` — bind OSDM service tasks to `engines/communication` generic invocation runtime.
- [ ] `engines/orchestration/integration/message_adapter.py` — bind messages/signals/events to communication and storage layers.
- [ ] `engines/orchestration/integration/script_executor.py` — support safe, auditable script execution with typed inputs/outputs.
- [ ] `engines/orchestration/integration/business_rule_adapter.py` — integrate DMN/business rule execution with runtime scopes.
- [ ] `engines/orchestration/integration/user_task_adapter.py` — integrate user tasks/forms/claims/completions with durable state.
- [ ] `engines/orchestration/integration/data_mapper.py` — support schema-aware mapping between MSDM/DSDM structures and runtime variables.
- [ ] `engines/orchestration/integration/connector_registry.py` — centralize pluggable connectors and runtime capability discovery.

### `monitoring/`
- [ ] `engines/orchestration/monitoring/__init__.py` — export stable observability APIs.
- [ ] `engines/orchestration/monitoring/metrics_collector.py` — emit durable metrics from runtime/audit/timer/token activity.
- [ ] `engines/orchestration/monitoring/tracer.py` — add trace spans around execution lifecycle and persistence.
- [ ] `engines/orchestration/monitoring/logger.py` — structured logging with correlation/instance/job identifiers.
- [ ] `engines/orchestration/monitoring/health_checker.py` — health/readiness checks across storage/scheduler/engines.
- [ ] `engines/orchestration/monitoring/performance_monitor.py` — track throughput/latency/backlog/hotspot metrics.

### `validation/`
- [ ] `engines/orchestration/validation/__init__.py` — export stable validators.
- [ ] `engines/orchestration/validation/validator.py` — define shared validation contract and result model.
- [ ] `engines/orchestration/validation/bpmn_validator.py` — structural + semantic BPMN validation aligned with OSDM fields.
- [ ] `engines/orchestration/validation/cmmn_validator.py` — structural + semantic CMMN validation.
- [ ] `engines/orchestration/validation/dmn_validator.py` — structural + semantic DMN validation.
- [ ] `engines/orchestration/validation/state_machine_validator.py` — structural + semantic state-machine validation.
- [ ] `engines/orchestration/validation/semantic_validator.py` — cross-model semantic validation across BPMN/DMN/CMMN/messages/data.

### `expression/`
- [ ] `engines/orchestration/expression/__init__.py` — export stable evaluators only.
- [ ] `engines/orchestration/expression/evaluator.py` — define shared expression contract with typed context/result/errors.
- [ ] `engines/orchestration/expression/python_evaluator.py` — safe Python expression evaluation.
- [ ] `engines/orchestration/expression/javascript_evaluator.py` — JS expression execution strategy and safety controls.
- [ ] `engines/orchestration/expression/feel_evaluator.py` — FEEL adapter used across BPMN/DMN/CMMN.
- [ ] `engines/orchestration/expression/juel_evaluator.py` — JUEL compatibility layer for BPMN-like expressions.
- [ ] `engines/orchestration/expression/context_builder.py` — build typed expression contexts from runtime state and schemas.

### `deployment/`
- [ ] `engines/orchestration/deployment/__init__.py` — export stable deployment APIs only.
- [ ] `engines/orchestration/deployment/deployer.py` — deploy parsed OSDM definitions with storage-backed versioning.
- [ ] `engines/orchestration/deployment/version_manager.py` — manage definition versions and runtime selection policies.
- [ ] `engines/orchestration/deployment/migration_handler.py` — migrate live instances safely across versions.
- [ ] `engines/orchestration/deployment/tenant_manager.py` — support tenant-aware deployments, definitions, and runtime isolation.

### `api/`
- [ ] `engines/orchestration/api/__init__.py` — export stable API surface.
- [ ] `engines/orchestration/api/engine_api.py` — expose engine lifecycle, health, and registry operations.
- [ ] `engines/orchestration/api/process_api.py` — expose process/case/state start/signal/message/terminate/suspend/resume operations.
- [ ] `engines/orchestration/api/task_api.py` — expose user/task/work-item operations with audit and validation.
- [ ] `engines/orchestration/api/instance_api.py` — expose instance query/history/token/variable/timer inspection APIs.
- [ ] `engines/orchestration/api/deployment_api.py` — expose deployment/version/migration APIs.
- [ ] `engines/orchestration/api/admin_api.py` — expose admin/recovery/replay/cleanup operations.

### `utils/`
- [ ] `engines/orchestration/utils/__init__.py` — export only stable shared helpers.
- [ ] `engines/orchestration/utils/id_generator.py` — unify runtime IDs for instances/tokens/jobs/events.
- [ ] `engines/orchestration/utils/time_utils.py` — support OSDM timer/duration/date-cycle parsing and conversions.
- [ ] `engines/orchestration/utils/xml_parser.py` — support BPMN/CMMN/DMN/XML helper behavior needed by runtime/deployment/validation.
- [ ] `engines/orchestration/utils/json_parser.py` — support JSON runtime/config loading helpers.
- [ ] `engines/orchestration/utils/graph_utils.py` — provide graph traversal/join/reachability/cycle helpers for BPMN/state/CEP models.
- [ ] `engines/orchestration/utils/type_converter.py` — map DSDM values to runtime/native types with MSDM-aware coercion.

### Tests
- [ ] `engines/orchestration/tests/__init__.py` — keep package marker only.
- [ ] `engines/orchestration/tests/test_core/__init__.py` — replace with real tests for runtime schemas, state, scheduler, correlation.
- [ ] `engines/orchestration/tests/test_bpmn/__init__.py` — replace with BPMN semantic scenarios.
- [ ] `engines/orchestration/tests/test_cmmn/__init__.py` — replace with CMMN lifecycle scenarios.
- [ ] `engines/orchestration/tests/test_state_machine/__init__.py` — replace with hierarchy/history/parallel tests.
- [ ] `engines/orchestration/tests/test_dmn/__init__.py` — replace with decision/hit-policy tests.
- [ ] `engines/orchestration/tests/test_cep/__init__.py` — replace with event/window/pattern tests.
- [ ] `engines/orchestration/tests/test_multi_agent/__init__.py` — replace with protocol/coordination tests.

## Immediate Next Slice
- [ ] Add runtime-record schema and DSDM serialization helpers.
- [ ] Upgrade `runtime/state_manager.py` to persist state snapshots through storage adapters.
- [ ] Wire `bpmn/engine.py` to the upgraded state persistence path.
- [ ] Add storage-backed repository helpers for later phases.
