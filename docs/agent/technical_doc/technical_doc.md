# Agent Engine Technical Documentation

## Architecture
The Agent Engine consists of the following components:

1. **AgentDefinition** (`engines/agents/models.py`): Pydantic model defining an agent's metadata and configuration.
2. **BaseAgent** (`engines/agents/base_agents/base_agent.py`): Generic base class for all agents, providing execution lifecycle, validation, and logging.
3. **SkillCallAgent** (`engines/agents/base_agents/skill_agent.py`): Agent that executes a single skill using the Skill Engine.
4. **StateMachineAgent** (`engines/agents/base_agents/state_machine_agent.py`): Agent that orchestrates skill execution via an OSDM StateMachineDocument.
5. **AgentRegistry** (`engines/agents/agent_registry.py`): Registry for managing agent instances.

## Data Flow
### Agent Instantiation
1. An `AgentDefinition` is created (either manually or from a configuration file).
2. Based on the `type` field in the definition, the appropriate agent class is instantiated:
   - `SkillCallAgent` for type `skill_call_agent`
   - `StateMachineAgent` for type `state_machine_agent`
   - `InteractionAgent` for type `interaction_agent` (existing)
3. The agent is registered with the `AgentRegistry` (optional).

### Agent Execution
1. When `AgentRegistry.run(agent_name, input_data)` is called:
   - The registry retrieves the agent instance by name.
   - The agent's `run` method (inherited from `BaseAgent`) is called with the input data.
   - The base agent validates the input against the agent's input model.
   - The agent's `execute` method is called (which is implemented by the specific agent type).
   - The base agent validates the output and logs the execution.

### Skill Call Agent Execution
1. The agent receives input data containing a `skill_input` field.
2. The agent uses the `SkillLoader` to load the skill specified by `skill_id`.
3. Depending on the agent's `execution_mode` (batch or step-wise), it uses the appropriate executor.
4. The executor loads the skill and its references, constructs a prompt, and calls the LLM.
5. The executor returns the skill result, which the agent wraps in its output model.

### State Machine Agent Execution
1. The agent receives input data containing an `initial_context` field.
2. The agent finds the initial state of the state machine.
3. The agent enters a loop:
   - Executes entry actions of the current state (if any are skills).
   - Executes the state's main skill (if defined in the state's documentation).
   - Evaluates outgoing transitions based on the current context.
   - If a transition is taken, moves to the target state and repeats.
   - If no transition is taken or the state is final, breaks the loop.
4. The agent returns the final context and the ID of the final state.

## Extension Points
### Custom Agent Types
To create a new agent type, extend the `BaseAgent` class and implement the `execute` method. Then, update the `AgentType` enum and the agent instantiation logic (if using a factory).

### Safe Expression Evaluation
The `StateMachineAgent` currently uses `eval()` for transition conditions, which is unsafe. To improve security, replace this with a safe expression evaluator (e.g., `simpleeval` or a custom DSL).

### Agent Definition Format
The `AgentDefinition` model can be extended to include additional fields (e.g., version, tags) as needed.

## Dependencies
- pydantic (for agent definition modeling)
- Skill Engine (for skill execution)
- OSDM Models (for state machine definition) - accessed via `engines.document.models.osdm_models`

## Thread Safety
The agent engine is designed to be used in a single-threaded context or with external synchronization. The `AgentRegistry` is not thread-safe; external synchronization is required for concurrent access.

## Performance Considerations
- Agent definition loading is performed once at instantiation.
- Skill execution is the primary latency factor; batch execution minimizes the number of LLM calls.
- State machine execution involves multiple skill executions; the latency is proportional to the number of states visited.

## Logging
The engine uses the standard `logging` module. The `BaseAgent` logs execution success and failure. Configure logging in your application to control verbosity.
