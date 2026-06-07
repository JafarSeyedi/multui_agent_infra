# Orchestration Engine

A comprehensive orchestration layer engine supporting multiple workflow and process standards including BPMN 2.0, CMMN, State Machines, DMN, CEP, and Multi-Agent Interactions.

## Overview

This orchestration engine provides a unified runtime for executing various types of orchestration definitions based on the OSDM (Orchestration Standard Definition Model). The engine is designed to handle complex workflow scenarios with support for:

- **BPMN 2.0**: Business Process Model and Notation for workflow automation
- **CMMN**: Case Management Model and Notation for adaptive case management
- **State Machines**: Hierarchical and parallel state machine execution
- **DMN**: Decision Model and Notation for business rule execution
- **CEP**: Complex Event Processing for real-time event pattern matching
- **Multi-Agent**: Multi-agent interaction and coordination protocols

## Architecture

### Core Components

The engine is organized into several layers:

1. **Core Layer** (`core/`): Fundamental orchestration primitives
   - Engine orchestration and lifecycle management
   - Execution context and token-based tracking
   - Event bus for pub/sub messaging
   - Correlation and transaction management

2. **Runtime Layer** (`runtime/`): Execution infrastructure
   - State management and persistence
   - Variable scoping and data flow
   - Error handling and compensation
   - Timer and resource management

3. **Engine-Specific Layers**: Specialized engines for each standard
   - `bpmn/`: BPMN 2.0 process execution
   - `cmmn/`: Case management execution
   - `state_machine/`: State machine runtime
   - `dmn/`: Decision table and expression evaluation
   - `cep/`: Event stream processing
   - `multi_agent/`: Agent coordination

4. **Supporting Layers**:
   - `integration/`: External system connectors
   - `persistence/`: Data storage abstraction
   - `monitoring/`: Observability and metrics
   - `validation/`: Definition validation
   - `expression/`: Expression language evaluation
   - `deployment/`: Definition deployment and versioning
   - `api/`: Public API interfaces
   - `utils/`: Common utilities

## Module Structure

### BPMN Engine (`bpmn/`)

Handles BPMN 2.0 process execution with support for:
- All activity types (tasks, subprocesses, call activities)
- All gateway types (exclusive, parallel, inclusive, event-based, complex)
- All event types (start, end, intermediate, boundary)
- Collaboration and message flows
- Choreography execution
- Transaction and ad-hoc subprocesses
- Loop and multi-instance patterns

**Key Files:**
- `engine.py`: BPMN engine coordinator
- `process_executor.py`: Process instance execution
- `activity_handler.py`: Activity lifecycle management
- `gateway_handler.py`: Gateway routing logic
- `event_handler.py`: Event processing
- `sequence_flow.py`: Flow evaluation and token movement

### CMMN Engine (`cmmn/`)

Implements case management with:
- Case instance lifecycle
- Stage and task management
- Milestone tracking
- Sentry-based activation/completion
- Case file item management
- Discretionary items and planning tables

**Key Files:**
- `engine.py`: CMMN engine coordinator
- `case_executor.py`: Case instance execution
- `sentry_evaluator.py`: Sentry condition evaluation
- `case_file_manager.py`: Case data management

### State Machine Engine (`state_machine/`)

Supports hierarchical and parallel state machines:
- State entry/exit actions
- Transition guards and actions
- History states (shallow and deep)
- Parallel/orthogonal regions
- Hierarchical state nesting

**Key Files:**
- `engine.py`: State machine engine
- `state_executor.py`: State execution logic
- `transition_handler.py`: Transition evaluation
- `guard_evaluator.py`: Guard condition checking

### DMN Engine (`dmn/`)

Decision management with:
- Decision table evaluation
- FEEL expression language
- Business knowledge models
- Decision service invocation
- All hit policies (unique, first, priority, collect, etc.)

**Key Files:**
- `engine.py`: DMN engine
- `decision_table_evaluator.py`: Table evaluation
- `feel_engine.py`: FEEL expression engine
- `hit_policy_handler.py`: Hit policy implementation

### CEP Engine (`cep/`)

Complex event processing with:
- Event pattern matching
- Temporal and sliding windows
- Event aggregation
- Stream processing
- Rule-based event correlation

**Key Files:**
- `engine.py`: CEP engine
- `pattern_matcher.py`: Pattern matching logic
- `window_manager.py`: Window management
- `stream_processor.py`: Stream processing

### Multi-Agent Engine (`multi_agent/`)

Agent interaction and coordination:
- Agent behavior execution
- Interaction protocols
- Message routing
- Coordination patterns
- Negotiation protocols

**Key Files:**
- `engine.py`: Multi-agent engine
- `agent_executor.py`: Agent execution
- `protocol_handler.py`: Protocol management
- `coordination_handler.py`: Coordination logic

## Design Principles

### File Size Constraint
Each file is designed to contain no more than 800 lines of code, ensuring:
- Maintainability and readability
- Clear separation of concerns
- Easy testing and debugging
- Modular architecture

### Token-Based Execution
The engine uses token-based execution semantics for:
- Process flow tracking
- Parallel execution management
- Synchronization points
- State transitions

### Event-Driven Architecture
Core event bus enables:
- Loose coupling between components
- Extensibility through event listeners
- Audit trail and monitoring
- Integration with external systems

### Pluggable Components
The architecture supports:
- Custom expression evaluators
- External service connectors
- Persistence backends
- Monitoring integrations

## Usage

### Starting the Engine

```python
from engines.orchestration.core.engine import OrchestrationEngine
from engines.orchestration.bpmn.engine import BPMNEngine

# Initialize the main engine
engine = OrchestrationEngine()

# Register BPMN engine
bpmn_engine = BPMNEngine(engine)
engine.register_engine('bpmn', bpmn_engine)

# Deploy a process definition
process_def = load_bpmn_definition('process.bpmn')
engine.deploy(process_def)

# Start a process instance
instance = engine.start_process('process_id', variables={'key': 'value'})
```

### Executing Different Engine Types

```python
# CMMN Case
from engines.orchestration.cmmn.engine import CMMNEngine
cmmn_engine = CMMNEngine(engine)
case_instance = cmmn_engine.create_case('case_def_id', data={})

# State Machine
from engines.orchestration.state_machine.engine import StateMachineEngine
sm_engine = StateMachineEngine(engine)
sm_instance = sm_engine.start('state_machine_id', context={})

# DMN Decision
from engines.orchestration.dmn.engine import DMNEngine
dmn_engine = DMNEngine(engine)
result = dmn_engine.evaluate_decision('decision_id', input_data={})
```

## Integration Points

### Service Tasks
Service tasks integrate with external systems through:
- REST/HTTP connectors
- Message queue adapters
- Database connectors
- Custom connector implementations

### User Tasks
User tasks integrate with:
- Form engines
- Task management systems
- Identity providers
- Notification services

### Data Mapping
Data flows between:
- Process variables
- External services
- Case file items
- State machine context

## Monitoring and Observability

The engine provides:
- Execution metrics (duration, throughput, errors)
- Distributed tracing
- Structured logging
- Health checks
- Performance monitoring

## Testing

Each module has corresponding tests in the `tests/` directory:
- Unit tests for individual components
- Integration tests for engine interactions
- End-to-end workflow tests
- Performance benchmarks

## Extension Points

The engine can be extended through:
- Custom activity handlers
- Expression evaluators
- Event listeners
- Persistence providers
- Monitoring integrations

## Dependencies

Core dependencies:
- Python 3.9+
- OSDM models (from `engines.document.models`)
- Expression evaluation libraries
- Persistence layer

## Future Enhancements

Planned features:
- Distributed execution
- Horizontal scaling
- Advanced compensation patterns
- Machine learning integration
- Real-time analytics dashboard

## License

[To be determined based on project requirements]
