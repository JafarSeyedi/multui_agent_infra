# Extension & Enhancement Plan v1.1 — Post-Compliance

## Overview
This document outlines the extension/augmentation plan for 15 major topic areas that go beyond the current BPMN 2.0 / CMMN 1.1 / DMN 1.3 / OSDM compliance scope. Each section includes: current state, proposed architecture, key design decisions, affected files, and estimated effort.

**Note to user**: Please review each section, add your concerns, notes, and design preferences. Once finalized, implementation will begin in the next steps.

---

## Topic 1: Work & Resource Management, Work Distribution and Rules

### Current State
- Basic `Resource`, `ResourceParameter`, `ResourceRole`, `HumanPerformer`, `Performer`, `PotentialOwner` OSDM classes exist
- `activity_handler.py` stores assignee/candidate variables but has no work distribution logic
- No work queue, no load balancing, no distribution rules

### Proposed Architecture

#### 1.1 Resource Registry (`engines/orchestration/resource/resource_registry.py`)
- Central registry of workers/agents with capabilities, availability, capacity
- `ResourceProfile`: worker_id, skills[], capacity, current_load, availability_schedule
- `ResourcePool`: named groups of resources with shared capabilities
- Integration with `engines/document/msdm_models.py` for resource entity definitions

#### 1.2 Work Distribution Engine (`engines/orchestration/resource/work_distributor.py`)
- Distribution strategies: RoundRobin, LeastLoaded, SkillBased, PriorityBased, CustomRule
- `DistributionRule`: condition expression + target resource selector
- Rules evaluated at task creation time using FEEL expressions against process variables
- Support for escalation: if no resource claims within timeout, re-distribute

#### 1.3 Work Queue (`engines/orchestration/resource/work_queue.py`)
- Per-resource work queues with priority ordering
- `WorkItem`: task_id, process_instance_id, priority, required_skills, deadline, assigned_resource
- Claim/Release/Delegate operations
- Integration with `runtime/listeners.py` for queue events

#### 1.4 Unified Cartable (`engines/orchestration/resource/cartable.py`)
- `CartableQuery`: filter by process type, task type, priority, deadline, custom fields
- `CartableView`: configurable columns, sorting, grouping
- Process-specific cartables: each process definition can define its own cartable layout
- Admin confirmation cartables: special view for admin-level task approval/rejection

### Key Design Decisions
- **Q1**: Should work distribution rules be defined in BPMN extension elements or in a separate configuration?
- **Q2**: Should the cartable be a separate service or part of the orchestration engine?
- **Q3**: How should resource availability integrate with external HR/identity systems?

### Affected Files
- New: `engines/orchestration/resource/` package
- Modify: `bpmn/activity_handler.py` (integrate work distribution at task creation)
- Modify: `runtime/listeners.py` (queue events)
- Modify: `engines/document/models/osdm_models.py` (resource extension attributes)

### Estimated Effort: ~40 hours

---

## Topic 2: Workflow Context Management & BPMN 2 RDBMS Extension

### Current State
- `ExecutionContext` in `core/context.py` manages process variables
- Variables stored as key-value pairs with optional MSDM schema binding
- No concept of "workflow context" as a first-class entity in RDBMS
- No support for cross-process shared context

### Proposed Architecture

#### 2.1 Workflow Context Entity (`engines/orchestration/context/workflow_context.py`)
- `WorkflowContext`: context_id, context_type, owner_process_id, shared_scope
- Context types: ProcessLocal, ProcessShared, CrossProcess, Global
- `ContextVariable`: variable_name, value, type_ref, msdm_entity_ref, created_at, updated_at
- Full CRUD with audit trail

#### 2.2 RDBMS Context Store (`engines/orchestration/context/rdbms_context_store.py`)
- Map `WorkflowContext` to RDBMS tables via `engines/document/msdm_models.py` Entity definitions
- Support for relational queries across workflow contexts
- Context indexing for fast lookup by process_instance_id, variable_name, entity_type
- Integration with `engines/storage/` for persistent storage

#### 2.3 BPMN 2 RDBMS Extension (`engines/orchestration/context/bpmn_rdbms_extension.py`)
- Extend BPMN Data Objects to reference RDBMS entities directly
- `RdbmsDataObject`: entity_name, query_template, parameter_bindings
- Support for CRUD operations on RDBMS entities as part of process execution
- Transaction management: RDBMS operations participate in process transactions

#### 2.4 Context Sharing API (`engines/orchestration/context/context_sharing.py`)
- `share_context(source_process_id, target_process_id, variable_filter)`
- `link_contexts(context_id_1, context_id_2, sync_mode)`: bidirectional sync
- `fork_context(parent_context_id, child_process_id)`: inherit + isolate

### Key Design Decisions
- **Q1**: Should workflow context be stored in the same database as process instances or a separate store?
- **Q2**: How should context variable versioning work for audit purposes?
- **Q3**: Should RDBMS entity operations be exposed as a new BPMN task type or as data object bindings?

### Affected Files
- New: `engines/orchestration/context/` package
- Modify: `core/context.py` (extend with RDBMS-backed storage)
- Modify: `bpmn/data_object_handler.py` (RDBMS data object support)
- Modify: `engines/document/models/osdm_models.py` (context entity definitions)

### Estimated Effort: ~32 hours

---

## Topic 3: Access Control & Authorization (RBAC)

### Current State
- No access control in the orchestration engine
- `PotentialOwner`, `Performer` are assignment mechanisms, not authorization
- No role definitions, no permission model

### Proposed Architecture

#### 3.1 Role Model (`engines/orchestration/auth/role_model.py`)
- `Role`: role_id, name, permissions[], parent_roles[] (hierarchy)
- `Permission`: resource_type, action, condition_expression
- `RoleAssignment`: user_id, role_id, scope (global/process-type/process-instance)
- Integration with `engines/document/msdm_models.py` for role entity definitions

#### 3.2 Context-Sensitive RBAC (`engines/orchestration/auth/context_rbac.py`)
- Permissions evaluated against process context at runtime
- `ContextCondition`: FEEL expression that must evaluate to true for permission to apply
- Example: "User can approve only if amount < 10000 AND department == user.department"
- Role inheritance with context override

#### 3.3 Authorization Service (`engines/orchestration/auth/auth_service.py`)
- `check_permission(user_id, resource, action, context) → bool`
- `get_authorized_actions(user_id, resource, context) → list[Action]`
- `get_authorized_users(resource, action, context) → list[User]`
- Caching layer for permission evaluation results

#### 3.4 Task-Level Authorization (`engines/orchestration/auth/task_auth.py`)
- Task assignment respects authorization: only authorized users can be assigned
- `authorize_task_claim(task_id, user_id) → AuthResult`
- `authorize_task_delegation(task_id, from_user, to_user) → AuthResult`
- Integration with `bpmn/activity_handler.py` at task creation/claim time

#### 3.5 Admin Authorization (`engines/orchestration/auth/admin_auth.py`)
- Admin-level operations: force-assign, force-complete, view-all, modify-any
- `AdminCartable`: view all tasks across all processes with filtering
- `AdminOverride`: override any authorization decision with audit trail

### Key Design Decisions
- **Q1**: Should roles be defined in the orchestration engine or imported from an external identity provider?
- **Q2**: How granular should permissions be? (process-level, task-level, activity-level, variable-level)
- **Q3**: Should authorization be evaluated at task creation or at task claim time (or both)?

### Affected Files
- New: `engines/orchestration/auth/` package
- Modify: `bpmn/activity_handler.py` (authorization checks)
- Modify: `runtime/listeners.py` (auth events)
- Modify: `api/task_api.py` (auth-protected endpoints)
- Modify: `engines/document/models/osdm_models.py` (role/permission entities)

### Estimated Effort: ~36 hours

---

## Topic 4: Model-Driven UI Forms

### Current State
- `forms/form_engine.py` exists with basic form rendering
- No model-driven form generation
- No integration with MSDM entity definitions for CRUD forms
- No workflow-related form types (task forms, process start forms)

### Proposed Architecture

#### 4.1 Form Model (`engines/orchestration/forms/form_model.py`)
- `FormDefinition`: form_id, form_type, fields[], layout, validation_rules[]
- Form types: TaskForm, ProcessStartForm, EntityCRUDForm, SubjectSpecificForm, AdminConfirmationForm
- `FormField`: field_id, label, field_type, required, default_value, validation, binding_expression
- Integration with `engines/document/msdm_models.py` for entity-driven field generation

#### 4.2 Entity-Driven Form Generator (`engines/orchestration/forms/entity_form_generator.py`)
- Auto-generate forms from MSDM Entity/Attribute definitions
- CRUD forms: Create, Read, Update, Delete operations on entities
- Field type mapping: String→text, Integer→number, Date→date, Boolean→checkbox, Enum→select
- Validation rules from MSDM constraints (min/max, pattern, required)

#### 4.3 Workflow Form Types (`engines/orchestration/forms/workflow_forms.py`)
- `TaskForm`: form attached to a UserTask, fields mapped to process variables
- `ProcessStartForm`: form for starting a new process instance
- `AdminConfirmationForm`: form for admin approval/rejection with comments
- Form data binding: form submission → process variables

#### 4.4 Form Layout Engine (`engines/orchestration/forms/layout_engine.py`)
- Grid-based layout with responsive sections
- Tabbed forms for complex data
- Conditional visibility: show/hide fields based on other field values
- Integration with `engines/document/models/osdm_models.py` for layout metadata

#### 4.5 Form Submission & Validation (`engines/orchestration/forms/form_submission.py`)
- `submit_form(form_id, data, instance_id) → SubmissionResult`
- Server-side validation against form rules and MSDM type constraints
- Partial save support (draft forms)
- File attachment handling (integration with Topic 10)

### Key Design Decisions
- **Q1**: Should form definitions be stored as BPMN extension elements or in a separate form repository?
- **Q2**: Should the form engine generate UI code (HTML/React) or just provide a data model for the UI layer?
- **Q3**: How should form versioning work when process definitions change?

### Affected Files
- New: `engines/orchestration/forms/form_model.py`, `entity_form_generator.py`, `workflow_forms.py`, `layout_engine.py`, `form_submission.py`
- Modify: `forms/form_engine.py` (extend with model-driven generation)
- Modify: `bpmn/activity_handler.py` (task form integration)
- Modify: `api/task_api.py` (form endpoints)

### Estimated Effort: ~40 hours

---

## Topic 5: Workflow, Messages, Choreography & Global Tasks Service Exposure

### Current State
- `bpmn/engine.py` deploys process definitions
- `choreography_executor.py` handles choreography internally
- No service exposure layer — no API for external systems to interact with workflows
- No message-based service invocation from BPMN

### Proposed Architecture

#### 5.1 Service Registry (`engines/orchestration/service/service_registry.py`)
- `ServiceDefinition`: service_id, service_type, endpoint, protocol, auth_config
- Service types: REST, GraphQL, gRPC, MessageQueue, Internal
- Integration with `engines/document/ssdm_models.py` for service/API standard definitions

#### 5.2 Workflow Service Exposure (`engines/orchestration/service/workflow_exposure.py`)
- Expose process operations as services: start, signal, message, query, manage
- `WorkflowServiceEndpoint`: process_definition_id, operation, protocol_adapter
- Auto-generate service definitions from BPMN message events and signal events
- WSDL/OpenAPI generation for exposed services

#### 5.3 Message-Based Service Invocation (`engines/orchestration/service/message_service.py`)
- `MessageServiceInvoker`: send/receive messages to/from external systems
- Correlation: match incoming messages to waiting process instances
- Integration with `engines/communication/` for protocol handling
- Support for request-response and fire-and-forget patterns

#### 5.4 Choreography Service Exposure (`engines/orchestration/service/choreography_service.py`)
- Expose choreography tasks as service operations
- `ChoreographyServiceEndpoint`: choreography_id, task_id, participant_role
- Message routing between choreography participants via service bus
- Integration with `bpmn/choreography_executor.py`

#### 5.5 Global Task Service (`engines/orchestration/service/global_task_service.py`)
- Expose global tasks as reusable service operations
- `GlobalTaskEndpoint`: task_id, input_parameters, output_parameters
- Service discovery: find available global tasks by capability
- Integration with `bpmn/global_task_handler.py`

### Key Design Decisions
- **Q1**: Should service exposure be auto-generated from BPMN definitions or manually configured?
- **Q2**: Which protocols should be supported initially? (REST + Message Queue first?)
- **Q3**: How should service versioning work with process versioning?

### Affected Files
- New: `engines/orchestration/service/` package
- Modify: `bpmn/engine.py` (service registration at deploy time)
- Modify: `bpmn/choreography_executor.py` (service-based participant coordination)
- Modify: `integration/message_adapter.py` (service message handling)
- Modify: `engines/document/models/osdm_models.py` (service definition entities)

### Estimated Effort: ~36 hours

---

## Topic 6: Service Tasks Service Consumption

### Current State
- `bpmn/activity_handler.py` has `ServiceTask` execution with retry/circuit breaker
- `integration/service_invoker.py` exists with basic HTTP connector
- No unified service consumption framework
- No support for complex service orchestration patterns

### Proposed Architecture

#### 6.1 Service Consumer Framework (`engines/orchestration/service/service_consumer.py`)
- `ServiceConsumer`: unified interface for all service consumption patterns
- Pattern support: Request-Response, Fire-and-Forget, Polling, Callback, Streaming
- `ServiceRequest`: endpoint, method, headers, body, timeout, retry_policy
- `ServiceResponse`: status, body, headers, error, latency

#### 6.2 Service Task Binding (`engines/orchestration/service/service_task_binding.py`)
- Map BPMN ServiceTask attributes to service consumption parameters
- `ServiceTaskBinding`: task_id, service_ref, operation, input_mapping, output_mapping
- Input mapping: process variables → service request parameters
- Output mapping: service response → process variables
- Error mapping: service errors → BPMN error events

#### 6.3 Connector Framework (`engines/orchestration/service/connector_framework.py`)
- `Connector`: pluggable adapter for different service protocols
- Built-in connectors: HTTP/REST, GraphQL, gRPC, JMS/AMQP, Kafka, Database
- `ConnectorRegistry`: discover and manage connectors
- Integration with `integration/connector_registry.py`

#### 6.4 Service Orchestration Patterns (`engines/orchestration/service/orchestration_patterns.py`)
- Parallel service calls with aggregation
- Sequential service calls with chaining
- Circuit breaker per service endpoint
- Bulkhead pattern: isolate service call failures
- Saga pattern: distributed transaction compensation

### Key Design Decisions
- **Q1**: Should service consumption be synchronous (wait for response) or asynchronous (callback)?
- **Q2**: How should service call timeouts interact with BPMN timer events?
- **Q3**: Should the connector framework be extensible via plugins?

### Affected Files
- New: `engines/orchestration/service/service_consumer.py`, `service_task_binding.py`, `connector_framework.py`, `orchestration_patterns.py`
- Modify: `bpmn/activity_handler.py` (integrate service consumer)
- Modify: `integration/service_invoker.py` (extend with patterns)
- Modify: `integration/connector_registry.py` (connector management)

### Estimated Effort: ~32 hours

---

## Topic 7: Event Bus, Message Bus, Distributed System & Scalability

### Current State
- `core/event_bus.py` exists with basic publish/subscribe
- `runtime/listeners.py` manages task/execution listeners
- No distributed event bus
- No message bus integration
- No scalability patterns

### Proposed Architecture

#### 7.1 Distributed Event Bus (`engines/orchestration/bus/distributed_event_bus.py`)
- `DistributedEventBus`: cluster-aware event publishing/subscribing
- Event partitioning by process instance ID for ordering guarantees
- Event sourcing: all events persisted in time-series storage
- Event replay: reconstruct process state from event log

#### 7.2 Message Bus Integration (`engines/orchestration/bus/message_bus_bridge.py`)
- Bridge between internal event bus and external message bus (Kafka, RabbitMQ, etc.)
- `MessageBusBridge`: topic mapping, serialization, delivery guarantees
- Inbound: external messages → internal events
- Outbound: internal events → external messages
- Integration with `engines/buses/`

#### 7.3 Scalability Patterns (`engines/orchestration/bus/scalability.py`)
- Process instance sharding: distribute instances across nodes
- `ShardRouter`: route process operations to correct shard
- Load balancing: distribute work across engine instances
- Horizontal scaling: add engine instances without downtime

#### 7.4 Distributed State Management (`engines/orchestration/bus/distributed_state.py`)
- Distributed cache for process instances and tokens
- State replication across engine nodes
- Consensus for critical operations (process start, migration)
- Integration with `runtime/state_manager.py`

#### 7.5 Event Sourcing & CQRS (`engines/orchestration/bus/event_sourcing.py`)
- `EventStore`: append-only event log for all process events
- `EventStream`: subscribe to event streams by process/instance/type
- CQRS: separate read models for queries vs. write models for commands
- Integration with `persistence/event_repository.py`

### Key Design Decisions
- **Q1**: Should the distributed event bus use a specific technology (Kafka, Redis, etc.) or be abstract?
- **Q2**: What consistency model is needed for process state? (strong vs. eventual)
- **Q3**: How should process instance migration work across cluster nodes?

### Affected Files
- New: `engines/orchestration/bus/` package
- Modify: `core/event_bus.py` (extend with distributed capabilities)
- Modify: `runtime/state_manager.py` (distributed state)
- Modify: `persistence/event_repository.py` (event sourcing)
- Modify: `engines/storage/` (distributed storage adapters)

### Estimated Effort: ~48 hours

---

## Topic 8: BPMN 2 Extension — Tool-Call Tasks

### Current State
- No concept of "tool-call" tasks in BPMN
- Service tasks invoke services but have no tool abstraction
- No integration with function/tool registries

### Proposed Architecture

#### 8.1 Tool-Call Task Type (`engines/orchestration/bpmn/tool_call_task.py`)
- New BPMN task type: `ToolCallTask` (extends ServiceTask)
- `ToolCallTask`: tool_name, tool_version, input_parameters[], output_schema
- Tool registry: discover available tools by name/capability
- Tool execution: invoke tool with parameters, map results to process variables

#### 8.2 Tool Registry (`engines/orchestration/bpmn/tool_registry.py`)
- `ToolDefinition`: tool_id, name, description, input_schema, output_schema, endpoint
- Tool discovery: search by capability, name, tags
- Tool versioning: multiple versions of same tool
- Integration with `engines/document/ssdm_models.py` for tool definitions

#### 8.3 Tool Execution Framework (`engines/orchestration/bpmn/tool_execution.py`)
- `ToolExecutor`: execute tool calls with timeout, retry, circuit breaker
- Input mapping: process variables → tool parameters
- Output mapping: tool results → process variables
- Error handling: tool errors → BPMN error events

#### 8.4 BPMN Extension Elements (`engines/orchestration/bpmn/tool_bpmn_extension.py`)
- BPMN extension elements for tool-call tasks in XML
- `<toolCall toolName="..." toolVersion="...">` extension
- Input/output mappings as extension elements
- Integration with `engines/document/parsers/osdm_parsers/bpmn_xml_parser.py`

### Key Design Decisions
- **Q1**: Should tool-call tasks be a new BPMN task type or an extension of ServiceTask?
- **Q2**: How should tool definitions be versioned and discovered?
- **Q3**: Should tool execution be synchronous or asynchronous?

### Affected Files
- New: `engines/orchestration/bpmn/tool_call_task.py`, `tool_registry.py`, `tool_execution.py`, `tool_bpmn_extension.py`
- Modify: `bpmn/activity_handler.py` (add ToolCallTask execution)
- Modify: `engines/document/parsers/osdm_parsers/bpmn_xml_parser.py` (parse extension)
- Modify: `engines/document/writers/osdm_writers/bpmn_xml_writer.py` (write extension)

### Estimated Effort: ~24 hours

---

## Topic 9: BPMN 2 Extension — Agentic System Integration

### Current State
- `multi_agent/` package exists with agent execution, negotiation, coordination
- No integration between BPMN processes and agentic systems
- No BPMN task type for agent interaction

### Proposed Architecture

#### 9.1 Agent Task Types (`engines/orchestration/bpmn/agent_tasks.py`)
- New BPMN task types:
  - `AgentTask`: invoke an agent with a goal/instruction
  - `AgentInteractionTask`: multi-turn interaction with an agent
  - `SkillTask`: invoke a specific skill/capability
- `AgentTask`: agent_id, goal, input_context, output_schema, timeout
- `SkillTask`: skill_name, skill_version, parameters[]

#### 9.2 Agent Registry (`engines/orchestration/bpmn/agent_registry.py`)
- `AgentDefinition`: agent_id, name, capabilities[], endpoint, protocol
- `SkillDefinition`: skill_id, name, description, input_schema, output_schema
- Agent discovery: find agents by capability
- Integration with `multi_agent/engine.py`

#### 9.3 Agent Execution Framework (`engines/orchestration/bpmn/agent_execution.py`)
- `AgentExecutor`: invoke agents, handle responses, manage timeouts
- `SkillExecutor`: invoke skills, map results
- Multi-turn interaction: maintain conversation context across task boundaries
- Agent response mapping: agent output → process variables

#### 9.4 Agent-Process Integration (`engines/orchestration/bpmn/agent_process_integration.py`)
- Agents can start processes: `agent_start_process(agent_id, process_def_id, variables)`
- Agents can signal processes: `agent_signal_process(signal_name, variables)`
- Agents can query process state: `agent_query_process(instance_id)`
- Process can wait for agent completion: async agent task with callback

#### 9.5 BPMN Extension Elements (`engines/orchestration/bpmn/agent_bpmn_extension.py`)
- BPMN extension elements for agent tasks
- `<agentTask agentId="..." goal="...">` extension
- `<skillTask skillName="...">` extension
- Integration with parser/writer

### Key Design Decisions
- **Q1**: Should agent tasks be blocking (process waits) or non-blocking (process continues)?
- **Q2**: How should agent conversation context be maintained across multiple agent tasks?
- **Q3**: What protocol should be used for agent communication? (REST, gRPC, message queue?)

### Affected Files
- New: `engines/orchestration/bpmn/agent_tasks.py`, `agent_registry.py`, `agent_execution.py`, `agent_process_integration.py`, `agent_bpmn_extension.py`
- Modify: `bpmn/activity_handler.py` (add agent task execution)
- Modify: `multi_agent/engine.py` (process integration API)
- Modify: `engines/document/parsers/osdm_parsers/bpmn_xml_parser.py`
- Modify: `engines/document/writers/osdm_writers/bpmn_xml_writer.py`

### Estimated Effort: ~40 hours

---

## Topic 10: Manual Tasks & User Tasks — Notes, Progress, Attachments

### Current State
- `bpmn/activity_handler.py` handles ManualTask and UserTask
- No support for notes, descriptions, progress percentage, state, file attachments
- No task-level metadata management

### Proposed Architecture

#### 10.1 Task Metadata Model (`engines/orchestration/task/task_metadata.py`)
- `TaskMetadata`: task_id, notes[], description, progress_percentage, custom_state
- `TaskNote`: note_id, author, content, timestamp, visibility (public/private)
- `TaskAttachment`: attachment_id, file_name, file_type, file_size, storage_ref, uploaded_by, uploaded_at
- `TaskProgress`: percentage, status_text, last_updated

#### 10.2 Task Notes API (`engines/orchestration/task/task_notes.py`)
- `add_note(task_id, content, author, visibility) → TaskNote`
- `get_notes(task_id, filter) → list[TaskNote]`
- `update_note(note_id, content) → TaskNote`
- `delete_note(note_id) → bool`
- Integration with `runtime/listeners.py` for note events

#### 10.3 Task Progress API (`engines/orchestration/task/task_progress.py`)
- `update_progress(task_id, percentage, status_text) → TaskProgress`
- `get_progress(task_id) → TaskProgress`
- Progress validation: 0-100 range, monotonic increase option
- Integration with `runtime/listeners.py` for progress events

#### 10.4 File Attachment Framework (`engines/orchestration/task/task_attachments.py`)
- `attach_file(task_id, file_data, file_name, file_type) → TaskAttachment`
- `get_attachments(task_id) → list[TaskAttachment]`
- `download_attachment(attachment_id) → file_data`
- `delete_attachment(attachment_id) → bool`
- Storage integration: files stored in `engines/storage/`, metadata in process context
- Integration with `engines/document/` for document ingestion (Topic 11)

#### 10.5 User Task Enhancement (`engines/orchestration/task/user_task_enhancement.py`)
- Extended UserTask lifecycle: Created → Assigned → InProgress → Completed
- Custom task states: user-defined states beyond standard BPMN states
- Task delegation: reassign from one user to another with history
- Task escalation: auto-escalate on deadline with notification
- Integration with `bpmn/activity_handler.py`

### Key Design Decisions
- **Q1**: Should task notes be stored as process variables or in a separate store?
- **Q2**: What file size limits and file type restrictions should apply?
- **Q3**: Should task progress be manually set or auto-calculated from subtasks?

### Affected Files
- New: `engines/orchestration/task/` package
- Modify: `bpmn/activity_handler.py` (enhanced user/manual task handling)
- Modify: `runtime/listeners.py` (task metadata events)
- Modify: `api/task_api.py` (task metadata endpoints)
- Modify: `forms/form_engine.py` (form attachment support)

### Estimated Effort: ~32 hours

---

## Topic 11: File Attachments, Document Engine Integration & RAG

### Current State
- No file attachment support in the orchestration engine
- No integration with document engine
- No RAG/knowledge layer integration

### Proposed Architecture

#### 11.1 Attachment-Document Bridge (`engines/orchestration/attachment/attachment_document_bridge.py`)
- `AttachmentDocumentBridge`: link task attachments to document engine documents
- On attachment upload: ingest into document engine, store document reference
- Document metadata: document_id, content_type, extraction_status, index_status
- Integration with `engines/document/` parsers for content extraction

#### 11.2 Workflow Attachment Context (`engines/orchestration/attachment/workflow_attachment_context.py`)
- `WorkflowAttachmentContext`: process-level attachment collection
- Attachments linked to: process instance, activity instance, case file item
- Full-text search across workflow attachments
- Attachment versioning: track changes to attached documents

#### 11.3 RAG Integration (`engines/orchestration/attachment/rag_integration.py`)
- `RagAttachmentIndexer`: index workflow attachments for RAG retrieval
- On attachment: extract text, generate embeddings, index in knowledge base
- Query: search workflow attachments by semantic similarity
- Integration with knowledge layer for context-aware task assignment

#### 11.4 Document Ingestion Pipeline (`engines/orchestration/attachment/document_ingestion.py`)
- `DocumentIngestionPipeline`: process attachment → extract → index → link
- Support for: PDF, Word, Excel, images (OCR), email, web pages
- Async ingestion with status tracking
- Integration with `engines/document/parsers/` for format-specific extraction

### Key Design Decisions
- **Q1**: Should document ingestion be synchronous or asynchronous?
- **Q2**: How should attachment access control work? (inherit from task permissions?)
- **Q3**: What RAG embedding model should be used? (configurable?)

### Affected Files
- New: `engines/orchestration/attachment/` package
- Modify: `engines/orchestration/task/task_attachments.py` (document integration)
- Modify: `engines/document/parsers/` (content extraction)
- Modify: `api/task_api.py` (attachment endpoints)

### Estimated Effort: ~28 hours

---

## Topic 12: Storage of Tokens, Instances, Context, Data Objects & Properties

### Current State
- `persistence/` package has repositories for instances, variables, events, history, tokens
- `runtime/state_manager.py` manages in-memory state
- No unified storage strategy for all runtime artifacts
- No storage optimization for time-series data

### Proposed Architecture

#### 12.1 Unified Storage Model (`engines/orchestration/storage/unified_storage.py`)
- `UnifiedStorageManager`: single interface for all runtime artifact storage
- Storage tiers: Hot (in-memory), Warm (RDBMS), Cold (object storage)
- Automatic tiering: move data between tiers based on age/access patterns
- Integration with `engines/storage/` adapters

#### 12.2 Token Storage (`engines/orchestration/storage/token_storage.py`)
- `TokenRepository`: extended with time-series storage for token lifecycle events
- Token snapshots: periodic state capture for recovery
- Token history: full audit trail of token movements
- Integration with `persistence/token_repository.py`

#### 12.3 Instance Storage (`engines/orchestration/storage/instance_storage.py`)
- `InstanceRepository`: extended with full state snapshots
- Instance archiving: move completed instances to cold storage
- Instance restoration: restore archived instances for re-execution
- Integration with `persistence/instance_repository.py`

#### 12.4 Context & Data Object Storage (`engines/orchestration/storage/context_storage.py`)
- `ContextRepository`: store/restore full process context
- `DataObjectRepository`: store data objects with versioning
- `PropertyRepository`: store process properties with type enforcement
- Integration with `persistence/variable_repository.py`

#### 12.5 Time-Series Optimization (`engines/orchestration/storage/timeseries_optimization.py`)
- Optimize time-series storage for: events, token movements, variable changes
- Downsampling: aggregate old data for efficient querying
- Retention policies: auto-cleanup based on age/compliance requirements
- Integration with `persistence/event_repository.py`, `persistence/history_repository.py`

### Key Design Decisions
- **Q1**: What should the default storage tier be for each artifact type?
- **Q2**: How long should runtime data be retained? (configurable per process type?)
- **Q3**: Should storage be pluggable (different backends for different artifact types)?

### Affected Files
- New: `engines/orchestration/storage/` package
- Modify: `persistence/token_repository.py`, `persistence/instance_repository.py`, `persistence/variable_repository.py`
- Modify: `runtime/state_manager.py` (tiered storage)
- Modify: `engines/storage/` (new storage adapters)

### Estimated Effort: ~28 hours

---

## Total Estimated Effort

| Topic | Hours | Priority |
|---|---|---|
| 1. Work & Resource Management | 40 | High |
| 2. Workflow Context & RDBMS | 32 | High |
| 3. Access Control & RBAC | 36 | High |
| 4. Model-Driven UI Forms | 40 | Medium |
| 5. Service Exposure | 36 | Medium |
| 6. Service Consumption | 32 | High |
| 7. Event Bus & Scalability | 48 | High |
| 8. Tool-Call Tasks | 24 | Medium |
| 9. Agentic System Integration | 40 | High |
| 10. Task Metadata & Attachments | 32 | Medium |
| 11. Document Integration & RAG | 28 | Medium |
| 12. Storage Optimization | 28 | Medium |
| 13. MCP Server | 40 | High |
| 14. Templates & Patterns | 48 | High |
| 15. Best Practices Library | 56 | High |
| **Total** | **~560 hours** | — |

## Execution Order Recommendation

1. **Phase 1** (Foundation): Topics 7 (Event Bus), 12 (Storage), 2 (Context)
2. **Phase 2** (Security): Topic 3 (RBAC)
3. **Phase 3** (Integration): Topics 6 (Service Consumption), 5 (Service Exposure)
4. **Phase 4** (Intelligence): Topics 8 (Tool-Call), 9 (Agentic), 11 (RAG)
5. **Phase 5** (User Experience): Topics 1 (Work Management), 4 (Forms), 10 (Task Metadata)

---

Once your notes are added, implementation will begin topic by topic.

---

# Questionnaire — Design Decisions for Extension Topics

Please answer each question with the option letter (A/B/C/...) and optionally add notes. Skip any question that doesn't apply.

---

## Topic 1: Work & Resource Management, Work Distribution and Rules

**Q1.1: Where should work distribution rules be defined?**
- (A) As BPMN extension elements in the XML definition itself
- (B) In a separate configuration file (JSON/YAML) linked to process definitions
- (C) In a database table with FEEL expressions
- (D) Combination — BPMN extensions for simple rules, separate config for complex rules

**Q1.2: What distribution strategies must be supported at launch?**
- (A) Only Direct Assignment and Round Robin
- (B) Direct Assignment, Round Robin, LeastLoaded, SkillBased
- (C) All: RoundRobin, LeastLoaded, SkillBased, PriorityBased, CustomRule
- (D) Custom rule engine only (FEEL-based rules, no built-in strategies)

**Q1.3: Should the cartable be a separate service or part of the orchestration engine?**
- (A) Integrated into the orchestration engine as a core component
- (B) Separate service with its own API, communicating via internal events
- (C) Separate service but sharing the same database
- (D) Plugin architecture — core interface with swappable implementations

**Q1.4: How should resource availability integrate with external HR/identity systems?**
- (A) Real-time sync: orchestrator queries HR system via API at task creation time
- (B) Cached sync: periodic import of resource data from HR system (e.g., every 15 min)
- (C) Event-driven: HR system pushes changes to orchestrator via webhooks/messages
- (D) Manual entry only — no external integration at this phase
- (E) Pluggable adapter system — support multiple HR backends

**Q1.5: Should admin confirmation cartables be a separate view type or a filter on the unified cartable?**
- (A) Separate view type with its own layout and permissions
- (B) Filter/view on the unified cartable with admin permissions
- (C) Both — dedicated admin cartable plus filterable unified cartable

---

## Topic 2: Workflow Context Management & BPMN 2 RDBMS Extension

**Q2.1: Should workflow context be stored in the same database as process instances?**
- (A) Same database, same schema — simplest approach
- (B) Same database, separate schema — logical separation
- (C) Separate database — physical isolation for performance
- (D) Configurable — same or separate based on deployment

**Q2.2: How should context variable versioning work for audit?**
- (A) Full history: every change creates a new version with timestamp and author
- (B) Snapshot-based: periodic snapshots with diff capability
- (C) Current value only — no versioning in the orchestrator (audit via event log)
- (D) Configurable per variable — some versioned, some current-only

**Q2.3: Should RDBMS entity operations be exposed as a new BPMN task type or as data object bindings?**
- (A) New task type: `RdbmsTask` with CRUD operations
- (B) Data object bindings: extend existing data objects to reference RDBMS entities
- (C) Service task extension: extend ServiceTask with RDBMS connector type
- (D) Both — task type for explicit operations, bindings for implicit data flow

**Q2.4: What levels of context sharing should be supported?**
- (A) Process local only — no sharing
- (B) Process local + parent-child sharing (sub-process inherits parent context)
- (C) Full: ProcessLocal, ProcessShared, CrossProcess, Global
- (D) Process local + CrossProcess only

---

## Topic 3: Access Control & Authorization (RBAC)

**Q3.1: Where should roles be defined?**
- (A) In the orchestration engine with built-in role management
- (B) Imported from an external identity provider (LDAP/Active Directory/OAuth)
- (C) Both — built-in roles + external identity provider sync
- (D) External only — orchestration engine has no role definitions

**Q3.2: How granular should permissions be?**
- (A) Process-level only — user can/cannot start/participate in a process type
- (B) Process + task level — per-process and per-task-type permissions
- (C) Process + task + activity — fine-grained per-activity-instance permissions
- (D) Full: process + task + activity + variable (field-level read/write)

**Q3.3: When should authorization be evaluated?**
- (A) Task creation time only — if unauthorized, task is never created
- (B) Task claim time — at creation and at claim
- (C) Continuous — at creation, claim, delegation, completion, and data access
- (D) At data access only — show/hide UI elements based on permissions

**Q3.4: Should authorization decisions be cached?**
- (A) No — always evaluate against identity provider
- (B) Yes — cache per session with TTL
- (C) Yes — cache per permission check with invalidation on role change
- (D) Yes — cache per user+resource with event-driven invalidation

---

## Topic 4: Model-Driven UI Forms

**Q4.1: Where should form definitions be stored?**
- (A) As BPMN extension elements in the process definition XML
- (B) In a separate form repository/database linked to process definitions
- (C) Both — simple forms in BPMN, complex forms in separate repository

**Q4.2: What should the form engine produce?**
- (A) Data model only (JSON schema) — UI layer renders independently
- (B) Server-rendered HTML forms
- (C) React/Vue component definitions
- (D) Multi-format: data model + server-rendered HTML + component definitions

**Q4.3: How should form versioning work when process definitions change?**
- (A) Forms auto-inherit process version — no independent versioning
- (B) Forms version independently — backward-compatible forms work with new process versions
- (C) Forms have compatibility range — specify which process versions they support
- (D) Forms auto-generate from process — no manual versioning needed

**Q4.4: Which form types are needed at launch?**
- (A) TaskForm and ProcessStartForm only
- (B) TaskForm, ProcessStartForm, EntityCRUDForm
- (C) All: TaskForm, ProcessStartForm, EntityCRUDForm, SubjectSpecificForm, AdminConfirmationForm

---

## Topic 5: Service Exposure

**Q5.1: Should service exposure be auto-generated from BPMN or manually configured?**
- (A) Auto-generated — every message/signal event becomes a service endpoint
- (B) Manually configured — explicit service registry per process
- (C) Opt-in annotation — BPMN extension elements mark which events to expose
- (D) Both — auto-generate scaffold, manually customize

**Q5.2: Which protocols should be supported initially?**
- (A) REST/HTTP only
- (B) REST + Message Queue (Kafka/RabbitMQ)
- (C) REST + GraphQL + Message Queue
- (D) All: REST, GraphQL, gRPC, Message Queue

**Q5.3: How should service versioning work with process versioning?**
- (A) Services version with process — new process version = new service version
- (B) Services version independently — backward-compatible services across process versions
- (C) Services have compatibility matrix — specify which process versions they support

---

## Topic 6: Service Consumption

**Q6.1: Should service consumption be synchronous or asynchronous by default?**
- (A) Synchronous (request-response) only — simpler error handling
- (B) Asynchronous (callback) only — better for long-running services
- (C) Configurable per service task — sync or async based on task configuration
- (D) Always async with optional synchronous wait

**Q6.2: How should service call timeouts interact with BPMN timer events?**
- (A) Service timeout generates BPMN error event
- (B) Service timeout and BPMN timer are independent — whichever fires first wins
- (C) BPMN timer overrides service timeout
- (D) Service timeout can be configured to trigger timer boundary event

**Q6.3: How many built-in connectors are needed at launch?**
- (A) HTTP/REST only
- (B) HTTP/REST + Database (SQL)
- (C) HTTP/REST + Database + Kafka + gRPC
- (D) Pluggable architecture — HTTP only at launch, others as plugins

---

## Topic 7: Event Bus, Message Bus, Distributed System & Scalability

**Q7.1: Should the distributed event bus use a specific technology or be abstract?**
- (A) Kafka — industry standard for event streaming
- (B) Redis Pub/Sub — simpler, lower latency
- (C) Abstract interface — pluggable backend (Kafka, Redis, RabbitMQ, NATS, etc.)
- (D) Hybrid — abstract interface with Kafka as primary, Redis for local caching

**Q7.2: What consistency model for process state?**
- (A) Strong consistency — all nodes see same state (requires consensus)
- (B) Eventual consistency — state converges after writes (better performance)
- (C) Causal consistency — related events ordered, unrelated can be concurrent
- (D) Configurable per deployment — strong for financial, eventual for analytics

**Q7.3: How should process instance migration work across cluster nodes?**
- (A) No migration — sticky routing (instance stays on same node)
- (B) Migration via state snapshot — pause, snapshot, restore on target node
- (C) Migration via event replay — replay event log on target node
- (D) Both snapshot and event replay strategies

---

## Topic 8: Tool-Call Tasks

**Q8.1: Should tool-call tasks be a new BPMN task type or an extension of ServiceTask?**
- (A) New task type: `ToolCallTask` — explicit tool semantics
- (B) Extension of ServiceTask with tool-specific attributes
- (C) Extension of ServiceTask with a `toolRef` attribute that references tool registry
- (D) New task type that extends ServiceTask (inheritance)

**Q8.2: Should tool execution be synchronous or asynchronous?**
- (A) Synchronous only — process waits for tool result
- (B) Asynchronous only — process continues, tool result arrives via callback
- (C) Configurable — sync for fast tools, async for long-running tools
- (D) Always async with optional synchronous wait period

---

## Topic 9: Agentic System Integration

**Q9.1: Should agent tasks be blocking or non-blocking?**
- (A) Blocking — process waits for agent response (agent task = user task equivalent)
- (B) Non-blocking — process continues, agent response arrives via signal/message
- (C) Configurable — blocking for short interactions, non-blocking for long-running
- (D) Always blocking with timeout — if timeout, escalate

**Q9.2: How should agent conversation context be maintained across multiple agent tasks?**
- (A) Orchestrator-managed — conversation context stored as process variable
- (B) Agent-managed — agent maintains conversation, orchestrator passes session ID
- (C) Hybrid — orchestrator stores summary, agent stores full context
- (D) External session store — dedicated conversation/session management service

**Q9.3: What protocol should be used for agent communication?**
- (A) REST/HTTP only
- (B) REST + gRPC (for performance)
- (C) Message queue (async by default)
- (D) MCP (Model Context Protocol) — standardized agent-tool interface
- (E) Pluggable — agent registry defines protocol per agent

---

## Topic 10: Task Metadata & Attachments

**Q10.1: Where should task notes be stored?**
- (A) As process variables (simple, transactional)
- (B) Separate database table with task_id foreign key
- (C) Separate document store (for rich text, mentions, etc.)
- (D) Event-sourced — notes as events in the event log

**Q10.2: What file size limit should apply to attachments?**
- (A) 5 MB per file
- (B) 25 MB per file
- (C) 100 MB per file
- (D) Configurable per process type — default 25 MB, admin-configurable

**Q10.3: Should task progress be manually set or auto-calculated?**
- (A) Manual only — user/worker sets progress
- (B) Auto-calculated from subtask completion (0%, 25%, 50%, 75%, 100%)
- (C) Both — manual override with auto-calculation as default
- (D) Neither — progress is UI-only, not persisted in engine

---

## Topic 11: Document Integration & RAG

**Q11.1: Should document ingestion be synchronous or asynchronous?**
- (A) Synchronous — upload waits for extraction and indexing
- (B) Asynchronous — upload accepted, processing happens in background
- (C) Hybrid — sync for small files (< 1MB), async for large files

**Q11.2: How should attachment access control work?**
- (A) Inherit from task permissions — if you can see the task, you can see attachments
- (B) Separate permissions per attachment — more granular control
- (C) Role-based — attachments inherit process-level role permissions

**Q11.3: What document formats should be supported at launch?**
- (A) PDF only
- (B) PDF + Word + Excel
- (C) PDF + Word + Excel + Images (OCR) + Email
- (D) All formats supported by Apache Tika

---

## Topic 12: Storage Optimization

**Q12.1: What should the default storage tier be for each artifact type?**
- (A) All in RDBMS — simplest architecture
- (B) Active instances in RDBMS, completed instances in object storage
- (C) Hot (active) in-memory, Warm (recent) in RDBMS, Cold (archived) in object storage
- (D) All in time-series storage — unified model

**Q12.2: How long should runtime data be retained?**
- (A) Forever — no deletion
- (B) Fixed period — 1 year for all data
- (C) Configurable per process type — financial: 7 years, HR: 5 years, etc.
- (D) Tiered retention — hot: 30 days, warm: 1 year, cold: 7 years

---

## Topic 13: MCP Server

**Q13.1: Should the MCP server be standalone or embedded?**
- (A) Embedded — runs in the same process as the orchestration engine
- (B) Standalone process — communicates via IPC or local HTTP
- (C) Standalone service — communicates via network (HTTP/SSE)
- (D) Both — embedded for development, standalone for production

**Q13.2: Which transport to support first?**
- (A) stdio only — for local AI tools (Claude Desktop, VS Code, etc.)
- (B) HTTP/SSE only — for remote clients and web dashboards
- (C) Both stdio and HTTP/SSE from the start

**Q13.3: Should MCP tools have their own authorization layer?**
- (A) Inherit from the engine's RBAC (single authorization system)
- (B) Separate MCP authorization — API keys for tool access, independent of engine RBAC
- (C) Both — engine RBAC for runtime tools, API keys for dev tools

**Q13.4: How should the MCP server handle long-running operations (e.g., process start)?**
- (A) Synchronous — MCP tool waits for operation completion
- (B) Async with polling — return operation ID, client polls for status
- (C) Async with SSE streaming — push updates to client as they happen
- (D) Async with webhook callback — client provides callback URL

---

## Topic 14: Templates & Patterns

**Q14.1: How should templates be stored?**
- (A) Parameterized BPMN XML with placeholder variables
- (B) Higher-level DSL (YAML/JSON) that compiles to BPMN XML
- (C) Both — DSL for simple templates, parameterized BPMN for complex ones

**Q14.2: Should the pattern library be built-in or user-extensible?**
- (A) Built-in only — curated library of standard patterns
- (B) User-extensible — anyone can register custom patterns
- (C) Both — built-in core patterns + user plugin system

**Q14.3: How should templates integrate with the best practices library (Topic 15)?**
- (A) Templates embed best practice references directly
- (B) Templates and practices are separate — linked by metadata/tags
- (C) Best practices generate template recommendations — practices recommends patterns

**Q14.4: How many control patterns should be implemented at launch?**
- (A) Core 5: Sequence, Parallel Split, Synchronization, Exclusive Choice, Simple Merge
- (B) Core 10: + Multi-Choice, Synchronizing Merge, Multi-Merge, Discriminator, Deferred Choice
- (C) All 16 control patterns from the workflow patterns initiative
- (D) Start with core 5, add others incrementally based on demand

---

## Topic 15: Best Practices Library

**Q15.1: How should the 17,000 existing best practices be imported?**
- (A) Batch import — one-time bulk import with transformation
- (B) Incremental import — import domain by domain (Finance first, then HR, etc.)
- (C) On-demand import — import domains as they are needed
- (D) External reference — practices stored externally, engine references them

**Q15.2: What knowledge representation format?**
- (A) Structured metadata (relational database with domain/module/category tables)
- (B) Vector embeddings (semantic search via embeddings)
- (C) Knowledge graph (graph database with relationships between practices)
- (D) Hybrid — structured metadata + vector embeddings for search

**Q15.3: How should the knowledge base stay updated?**
- (A) Manual curation — knowledge engineers update practices
- (B) Semi-automated — AI suggests updates, humans approve
- (C) Automated — AI analyzes process execution data to update practices
- (D) External sync — practices managed in external system, synced to orchestrator

**Q15.4: Should recommendations be mandatory or advisory?**
- (A) Mandatory — non-compliant processes cannot be deployed
- (B) Advisory — recommendations shown, but deployment is not blocked
- (C) Configurable per domain — mandatory for regulatory, advisory for others
- (D) Enforcement level per rule — Error/Warning/Advisory per practice

**Q15.5: How should domain-specific practices be organized across 23 ERP modules?**
- (A) Flat list — all practices in one namespace with domain tags
- (B) Hierarchical — Domain > Module > Category > Practice
- (C) Separate namespace per module — Finance.Practices, HR.Practices, etc.
- (D) Hierarchical + cross-module — practices can belong to multiple modules (e.g., Approval workflows span Finance and Procurement)

**Q15.6: For the infrastructural practices — should they be injected into business processes automatically?**
- (A) Yes — infrastructural patterns (audit trail, error handling, etc.) auto-injected
- (B) No — infrastructural patterns are recommended but manually added
- (C) Semi-auto — recommended with one-click injection
- (D) Policy-based — admin configures which infrastructural practices are mandatory

---

## Execution Priority

**Which topic should be implemented FIRST?**
Rank your top 5 topics in order of priority (1 = highest):
- [ ] Topic 1: Work & Resource Management
- [ ] Topic 2: Workflow Context & RDBMS
- [ ] Topic 3: Access Control & RBAC
- [ ] Topic 4: Model-Driven UI Forms
- [ ] Topic 5: Service Exposure
- [ ] Topic 6: Service Consumption
- [ ] Topic 7: Event Bus & Scalability
- [ ] Topic 8: Tool-Call Tasks
- [ ] Topic 9: Agentic System Integration
- [ ] Topic 10: Task Metadata & Attachments
- [ ] Topic 11: Document Integration & RAG
- [ ] Topic 12: Storage Optimization
- [ ] Topic 13: MCP Server
- [ ] Topic 14: Templates & Patterns
- [ ] Topic 15: Best Practices Library

---

## Topic 13: MCP Server for Orchestration Definitions, Runtime & Logs

### Current State
- No MCP (Model Context Protocol) server exists
- Process definitions are managed via internal APIs only
- No standardized interface for AI agents or external tools to discover, deploy, query, or monitor orchestration definitions
- Logs and runtime data are stored but not exposed via a structured protocol

### Proposed Architecture

#### 13.1 MCP Server Core (`engines/orchestration/mcp/mcp_server.py`)
- MCP protocol server implementing the JSON-RPC 2.0 transport (stdio + HTTP/SSE)
- `McpOrchestrationServer`: tools, resources, and prompts registrations
- Authentication: API key + OAuth 2.0
- Session management: per-client session state with tool call context
- Integration with `core/engine.py` for runtime operations

#### 13.2 MCP Tools — Orchestration Definitions (`engines/orchestration/mcp/tools/definition_tools.py`)
Tools for managing process definitions:
- `list_definitions(engine_type, filter) → list[DefinitionSummary]` — List all deployed definitions
- `get_definition(definition_id) → DefinitionDetail` — Get full definition with BPMN/CMMN/DMN XML
- `deploy_definition(xml_content, engine_type) → DeploymentResult` — Deploy a new definition
- `update_definition(definition_id, xml_content) → UpdateResult` — Update existing definition
- `undeploy_definition(definition_id, force) → UndeployResult` — Remove definition
- `get_definition_versions(definition_id) → list[VersionInfo]` — List all versions
- `migrate_definition(source_id, target_id, migration_plan) → MigrationResult` — Migrate instances between versions
- `validate_definition(xml_content) → ValidationResult` — Validate BPMN/CMMN/DMN XML
- `get_definition_dependencies(definition_id) → DependencyGraph` — Show called processes, decisions, BKMs

#### 13.3 MCP Tools — Orchestration Runtime (`engines/orchestration/mcp/tools/runtime_tools.py`)
Tools for managing running instances:
- `start_instance(definition_key, variables, business_key) → InstanceRef`
- `get_instance(instance_id) → InstanceDetail` — Full instance state with tokens, variables, activities
- `list_instances(filter, pagination) → list[InstanceSummary]` — Query running instances
- `signal_instance(instance_id, signal_name, variables) → SignalResult`
- `message_instance(instance_id, message_name, correlation_keys, variables) → MessageResult`
- `suspend_instance(instance_id) → SuspendResult`
- `resume_instance(instance_id) → ResumeResult`
- `terminate_instance(instance_id, reason) → TerminateResult`
- `migrate_instance(instance_id, target_definition_id, activity_mapping) → MigrationResult`
- `get_instance_tokens(instance_id) → list[TokenState]` — Token positions and states
- `get_instance_variables(instance_id, scope) → dict` — Process variables
- `set_variable(instance_id, variable_name, value, scope) → SetResult`
- `complete_task(task_id, variables) → CompleteResult` — Complete a user task
- `claim_task(task_id, user_id) → ClaimResult`
- `delegate_task(task_id, from_user, to_user) → DelegateResult`
- `get_instance_history(instance_id, filter) → list[HistoryEntry]` — Audit trail

#### 13.4 MCP Tools — Logs & Monitoring (`engines/orchestration/mcp/tools/log_tools.py`)
Tools for querying logs and runtime data:
- `query_events(filter, pagination) → list[EventRecord]` — Query event log
- `get_activity_log(instance_id, activity_id) → list[ActivityLogEntry]` — Per-activity execution log
- `query_incidents(filter) → list[Incident]` — Query incidents with filtering
- `get_instance_metrics(instance_id) → Metrics` — Execution metrics (duration, wait times, etc.)
- `get_engine_metrics(time_range) → EngineMetrics` — Aggregate engine performance
- `subscribe_events(filter, callback_url) → Subscription` — Webhook-style event subscription
- `get_error_log(instance_id) → list[ErrorEntry]` — Error details for failed instances

#### 13.5 MCP Resources (`engines/orchestration/mcp/resources/orchestration_resources.py`)
Resources for reading orchestration data:
- `orchestration://definitions/{id}` — Process definition XML/JSON
- `orchestration://instances/{id}` — Instance state snapshot
- `orchestration://instances/{id}/tokens` — Token positions
- `orchestration://instances/{id}/variables` — Variable values
- `orchestration://instances/{id}/history` — Audit trail
- `orchestration://deployments/{id}` — Deployment metadata
- `orchestration://events/{event_id}` — Individual event details
- Content type: `application/json` for state, `application/xml` for definitions

#### 13.6 MCP Prompts (`engines/orchestration/mcp/prompts/orchestration_prompts.py`)
Pre-defined prompts for AI agents:
- `analyze-process` — Analyze a BPMN process definition for bottlenecks, unused paths, error handling gaps
- `generate-process` — Generate a BPMN process from natural language description
- `migrate-process` — Generate migration plan between two process versions
- `debug-instance` — Analyze a stuck/failed process instance and suggest remediation
- `optimize-process` — Suggest optimizations for an existing process (parallelization, error handling)

#### 13.7 Developer Tools Integration (`engines/orchestration/mcp/tools/dev_tools.py`)
Tools for development-time operations:
- `validate_bpmn(xml) → ValidationResult` — BPMN 2.0 structural + semantic validation
- `validate_cmmn(xml) → ValidationResult` — CMMN 1.1 validation
- `validate_dmn(xml) → ValidationResult` — DMN 1.3 validation
- `simulate_process(xml, input_variables) → SimulationResult` — Step-through simulation
- `generate_test_cases(definition_id) → list[TestCase]` — Auto-generate test scenarios
- `compare_definitions(id_a, id_b) → DiffResult` — Structural diff between versions
- `export_definition(id, format) → ExportResult` — Export to BPMN XML, PDF, PNG, JSON

### Key Design Decisions
- **Q1**: Should the MCP server be a standalone process or embedded in the orchestration engine?
- **Q2**: Which transport to support first? (stdio for local AI tools, HTTP/SSE for remote)
- **Q3**: Should MCP tools have their own authorization layer or inherit from the engine's RBAC?
- **Q4**: How should the MCP server handle long-running operations (process start with async completion)?

### Affected Files
- New: `engines/orchestration/mcp/` package (server, tools, resources, prompts)
- Modify: `core/engine.py` (expose operations for MCP)
- Modify: `persistence/` repositories (add query methods for MCP tools)
- Modify: `deployment/deployer.py` (expose deploy/undeploy for MCP)
- Modify: `bpmn/validation/bpmn_validator.py` (integrate with validate tool)

### Estimated Effort: ~40 hours

---

## Topic 14: Orchestration Templates, Schemas & Workflow Patterns

### Current State
- No template system exists — each process is defined from scratch
- No library of reusable workflow patterns
- No schema system for validating process structure against best practices
- No differentiation between process-specific and cross-cutting concerns

### Proposed Architecture

#### 14.1 Template Engine (`engines/orchestration/template/template_engine.py`)
- `OrchestrationTemplate`: template_id, template_type, base_definition, parameters[], constraints[]
- Template types: ProcessTemplate, CaseTemplate, DecisionTemplate, ChoreographyTemplate
- `TemplateParameter`: name, type, default_value, required, description
- `TemplateInstance`: ground a template with specific parameter values
- Template composition: templates can include other templates
- Versioning: templates versioned independently of process definitions

#### 14.2 Workflow Control Patterns (`engines/orchestration/template/patterns/control_patterns.py`)
Implementation of standard workflow control patterns:
- **Sequence**: A → B → C (linear flow)
- **Parallel Split**: A → B, C, D (parallel gateway fork)
- **Synchronization**: B, C, D → A (parallel gateway join)
- **Exclusive Choice**: A → B | C (exclusive gateway based on condition)
- **Simple Merge**: B | C → A (exclusive gateway merge)
- **Multi-Choice**: A → B, C, D (subset selection, inclusive gateway)
- **Synchronizing Merge**: B, C, D → A (inclusive gateway join with tracking)
- **Multi-Merge**: B | C → A (multiple tokens merge without synchronization)
- **Discriminator**: B, C, D → A (first token passes, others discarded)
- **Arbitrary Cycles**: Loops with structured exit conditions
- **Implicit Termination**: Process ends when no more work items
- **Deferred Choice**: Choice determined by first available event
- **Interleaved Parallel**: Parallel execution with mutual exclusion
- **Milestone**: Enable until milestone is reached
- **Cancel Activity**: Boundary event cancels specific activity
- **Cancel Case**: Terminates entire process/case

Each pattern as a reusable sub-process template with configurable parameters.

#### 14.3 Workflow Resource Patterns (`engines/orchestration/template/patterns/resource_patterns.py`)
Standard patterns for work distribution:
- **Direct Assignment**: Task assigned to specific user/role
- **Capability-Based**: Task assigned based on required skills/capabilities
- **Round Robin**: Distribute evenly across a resource pool
- **Shortest Queue**: Assign to resource with fewest pending tasks
- **Precedence-Based**: Task cannot start until predecessor is complete
- **First Available**: Assign to first resource that claims it
- **Four-Eyes Principle**: Task requires approval from two different roles
- **Separation of Duties**: Same user cannot perform two related tasks
- **Case Handling**: All tasks for a case assigned to same resource
- **Retain Familiar**: Prefer resource that handled previous task in same case
- **Organizational Assignment**: Assign based on org hierarchy (manager, peer, subordinate)
- **Escalation**: Auto-reassign if not completed within deadline
- **Delegation**: Reassign with audit trail

#### 14.4 Workflow Data Patterns (`engines/orchestration/template/patterns/data_patterns.py`)
Standard patterns for data flow in workflows:
- **Task-to-Task Data**: Output variables of one task → input of next
- **Data Object Flow**: Data objects passed between activities via associations
- **Data Store Access**: Read/write to persistent data stores
- **Case File Pattern**: Centralized case file with typed items
- **Global Variables**: Process-level variables accessible to all activities
- **Local Variables**: Activity-scoped variables
- **Data Transformation**: Transform data at gateway/activity boundaries
- **Data Validation**: Validate data before/after transformation
- **Composite Data**: Complex data structures with nested properties
- **Data Views**: Different activities see different subsets of data

#### 14.5 Workflow Business Rules Patterns (`engines/orchestration/template/patterns/business_rules_patterns.py`)
Standard patterns for business rule integration:
- **Decision Table Routing**: Exclusive gateway conditions evaluated via DMN decision table
- **Policy-Based**: Complex policies evaluated via DMN with multiple decisions
- **Rule Chaining**: Output of one decision feeds into next
- **Rule Exception Handling**: Exception path when no rules match
- **Rule Validation**: Input validation via DMN before process execution
- **Rule Calculation**: Financial/operational calculations via DMN
- **Rule Classification**: Classify case/work item using DMN decision tree
- **Rule Eligibility**: Determine eligibility for process/case path

#### 14.6 Pattern Library (`engines/orchestration/template/patterns/pattern_library.py`)
- `PatternLibrary`: categorized, searchable collection of patterns
- Pattern categories: Control, Resource, Data, Business Rules
- Pattern metadata: name, description, category, complexity, use cases, references
- Pattern combination: compose patterns into larger templates
- Pattern validation: validate that a pattern is used correctly in a process
- Integration with `engines/document/parsers/` for pattern detection in existing processes

#### 14.7 Schema Validation (`engines/orchestration/template/schema/schema_validator.py`)
- `ProcessSchema`: defines structural constraints for process definitions
- Schema rules: naming conventions, required elements, optional elements, forbidden patterns
- Example schemas: "All processes must have error handling", "All user tasks must have deadlines"
- `validate_against_schema(definition_id, schema_id) → SchemaValidationResult`
- Schema inheritance: extend base schemas for specific process types

### Key Design Decisions
- **Q1**: Should templates be stored as parameterized BPMN XML or as a higher-level DSL?
- **Q2**: How should pattern instances be tracked separately from their template definitions?
- **Q3**: Should the pattern library be built-in or user-extensible (plugin system)?
- **Q4**: How should templates integrate with the best practices library (Topic 15)?

### Affected Files
- New: `engines/orchestration/template/` package (engine, patterns, schema, library)
- Modify: `bpmn/engine.py` (template-aware deployment)
- Modify: `deployment/deployer.py` (template instantiation)
- Modify: `bpmn/validation/bpmn_validator.py` (schema validation)
- Modify: `dmn/engine.py` (decision table pattern integration)

### Estimated Effort: ~48 hours

---

## Topic 15: Business Knowledge — Best Practices Library

### Current State
- No best practices library exists
- No domain-specific workflow knowledge base
- No mechanism to recommend patterns based on business domain
- No integration between business knowledge and orchestration design

### Proposed Architecture

#### 15.1 Best Practices Knowledge Base (`engines/orchestration/knowledge/best_practices_kb.py`)
- `BestPracticeEntry`: practice_id, name, description, domain, module, category, version
- Domain hierarchy: 23 ERP modules (e.g., Finance, HR, Procurement, Sales, Inventory, Manufacturing, etc.)
- Categories: Infrastructural (cross-cutting) vs Business-specific
- Practice metadata: applicable BPMN elements, required patterns, anti-patterns, compliance requirements
- Practice relationships: requires, recommends, conflicts_with, supersedes
- Versioning: practices evolve with business/regulatory changes
- Source: import from existing 17,000 workflow best practices

#### 15.2 Practice Import & Transformation (`engines/orchestration/knowledge/practice_importer.py`)
- Import from existing workflow definitions (17,000 best practices across 23 ERP modules)
- Transform concrete workflow definitions into abstract patterns
- Extract common patterns across similar workflows
- Identify domain-specific variations
- Map to OSDM model classes (Process, Activity, Gateway, etc.)
- Classification: auto-classify imported practices by domain, module, category

#### 15.3 Context-Aware Recommendation Engine (`engines/orchestration/knowledge/recommendation_engine.py`)
- `recommend_practices(domain, module, process_context) → list[PracticeRecommendation]`
- Input: current process definition state + business context
- Output: ranked list of applicable best practices with relevance scoring
- Recommendation types:
  - **Process Structure**: "Add error handling to this service task"
  - **Pattern Application**: "This sequence matches the Four-Eyes approval pattern"
  - **Resource Assignment**: "This task type typically requires Finance role"
  - **Data Flow**: "Missing data validation before this gateway"
  - **Compliance**: "This process path lacks required approval step per SOX"
  - **Optimization**: "These parallel tasks can be synchronized earlier"
  - **Anti-Pattern Detection**: "This loop has no structured exit condition"

#### 15.4 Domain Knowledge Graph (`engines/orchestration/knowledge/domain_knowledge_graph.py`)
- `DomainKnowledgeGraph`: graph of business domains, modules, practices, patterns
- Nodes: Domains, Modules, Practices, Patterns, BPMN Elements, Resources
- Edges: contains, requires, recommends, conflicts_with, implements
- Query: "Show all approval workflows in Finance module for amounts > 10000"
- Integration with RAG for semantic search across knowledge base

#### 15.5 Compliance & Governance Rules (`engines/orchestration/knowledge/compliance_rules.py`)
- `ComplianceRule`: rule_id, rule_type, domain, condition, enforcement_level
- Rule types: Regulatory (SOX, GDPR, HIPAA), Organizational, Industry-standard
- Enforcement: Error (block deployment), Warning (flag for review), Advisory (suggest improvement)
- `check_compliance(definition_id) → ComplianceReport`
- Integration with `validation/` package

#### 15.6 Infrastructural vs Business-Specific Separation (`engines/orchestration/knowledge/knowledge_taxonomy.py`)
- **Infrastructural Practices** (cross-cutting):
  - Authentication/authorization flows
  - Audit trail patterns
  - Error handling and compensation
  - Notification and escalation
  - Document attachment and management
  - Approval workflows (multi-level, Four-Eyes)
  - Data validation and transformation
  - Reporting and analytics hooks

- **Business-Specific Practices** (per ERP module):
  - Finance: Invoice processing, Payment approval, Budget control
  - HR: Recruitment, Onboarding, Performance review, Payroll
  - Procurement: Purchase request, Vendor selection, Goods receipt
  - Sales: Order management, Quotation, Contract management
  - Inventory: Stock transfer, Cycle counting, Reorder
  - Manufacturing: Production order, Quality control, Maintenance
  - ... (and 17 more modules)

### Key Design Decisions
- **Q1**: How should the 17,000 existing best practices be imported? (Batch import vs. incremental?)
- **Q2**: What knowledge representation format? (Graph DB, vector embeddings, structured metadata?)
- **Q3**: How should the knowledge base stay updated as business practices evolve?
- **Q4**: Should recommendations be mandatory (enforced) or advisory?
- **Q5**: How should domain-specific practices be organized across 23 ERP modules? Should each module have its own namespace?

### Affected Files
- New: `engines/orchestration/knowledge/` package (kb, importer, recommendations, graph, compliance, taxonomy)
- New: Data models for best practices in `engines/document/models/` (or dedicated knowledge model)
- Modify: `bpmn/validation/bpmn_validator.py` (compliance checking)
- Modify: `deployment/deployer.py` (compliance gate before deployment)
- Modify: `engines/orchestration/template/pattern_library.py` (link patterns to practices)
- Modify: MCP server tools (Topic 13) — expose knowledge queries via MCP

### Estimated Effort: ~56 hours

---

## Updated Total Estimated Effort

| Topic | Hours | Priority |
|---|---|---|
| 1. Work & Resource Management | 40 | High |
| 2. Workflow Context & RDBMS | 32 | High |
| 3. Access Control & RBAC | 36 | High |
| 4. Model-Driven UI Forms | 40 | Medium |
| 5. Service Exposure | 36 | Medium |
| 6. Service Consumption | 32 | High |
| 7. Event Bus & Scalability | 48 | High |
| 8. Tool-Call Tasks | 24 | Medium |
| 9. Agentic System Integration | 40 | High |
| 10. Task Metadata & Attachments | 32 | Medium |
| 11. Document Integration & RAG | 28 | Medium |
| 12. Storage Optimization | 28 | Medium |
| 13. MCP Server | 40 | High |
| 14. Templates & Patterns | 48 | High |
| 15. Best Practices Library | 56 | High |
| **Total** | **~560 hours** | — |

## Updated Execution Order Recommendation

1. **Phase 1** (Foundation): Topics 7 (Event Bus), 12 (Storage), 2 (Context)
2. **Phase 2** (Knowledge & Intelligence): Topics 15 (Best Practices), 14 (Templates & Patterns)
3. **Phase 3** (Security & Access): Topic 3 (RBAC)
4. **Phase 4** (Integration): Topics 6 (Service Consumption), 5 (Service Exposure), 13 (MCP Server)
5. **Phase 5** (AI & Automation): Topics 8 (Tool-Call), 9 (Agentic), 11 (RAG)
6. **Phase 6** (User Experience): Topics 1 (Work Management), 4 (Forms), 10 (Task Metadata)
