# Agent Engine Enhancement Plan

## Overview
This document outlines the planned enhancements to bring the Agent Engine to 100% conformance with the design requirements and industry best practices.

## Current Status
As per the conformance document, the Agent Engine has:
- 54% fully implemented requirements
- 87% when counting partial implementations as half

The main gaps are in the Interaction Agent (circular import), State Machine Agent (orchestration, safe expression evaluation, entry/exit actions), and Production Readiness (error handling, logging, unit tests).

## Enhancement Areas

### 1. Fix Interaction Agent Circular Import
**Problem**: The InteractionAgent causes a circular import between `engines.communication.buses.base_message_bus` and `engines.interaction.interaction_models`.
**Solution**: 
   - Refactor the interaction layer to break the circular dependency.
   - Options:
        a) Use dependency injection: pass the MessageBus to the InteractionAgent via constructor rather than importing it at the module level in the agent.
        b) Use lazy imports: import the MessageBus inside the method where it is needed (e.g., in the `__init__` or `execute` method).
   - We will choose option (b) for minimal changes, as the InteractionAgent is existing and we want to avoid large refactors.
   - Update the InteractionAgent to import MessageBus inside the `__init__` method.

### 2. Enhance State Machine Agent
**Problem**: The StateMachineAgent has basic orchestration, uses unsafe `eval()` for transition conditions, and lacks entry/exit action handling.
**Solutions**:
   a) **Implement proper state machine semantics**:
        - Define clear semantics for states: entry actions, exit actions, and the state's main activity (skill execution).
        - The agent should execute entry actions upon entering a state, then the state's main activity, then evaluate transitions, and if a transition is taken, execute exit actions of the source state and entry actions of the target state.
   b) **Replace unsafe eval() with a safe expression evaluator**:
        - Use a library like `simpleeval` or implement a simple DSL for conditions.
        - The condition should be able to access the context variable safely.
   c) **Implement entry and exit actions as skills**:
        - Allow state documentation to specify entry and exit skills, similar to how the main skill is specified.
        - Map context to skill inputs for these actions.
   d) **Enhance transition evaluation**:
        - Support for complex conditions (AND, OR, NOT) and possibly event-based transitions.
        - Allow transitions to be triggered by events (from the interaction layer) in addition to context conditions.

### 3. Improve Error Handling and Logging
**Problem**: Basic error handling and lack of logging in the agent engine.
**Solutions**:
   a) **Error Handling**:
        - Add specific exceptions for different error conditions (e.g., StateMachineError, SkillExecutionError).
        - Provide meaningful error messages that include the agent name, state ID (if applicable), and skill ID.
        - Ensure that errors are caught and logged appropriately, and where possible, provide fallback or recovery mechanisms.
   b) **Logging**:
        - Add logging throughout the agent engine using the standard `logging` module.
        - Log important events: agent initialization, skill execution (start, end, result), state transitions, errors.
        - Configure loggers per module (e.g., `engines.agent.base_agents.skill_agent`).
        - Ensure that logs do not contain sensitive information.

### 4. Expand Unit Tests
**Problem**: Incomplete unit test coverage.
**Solutions**:
   a) **StateMachineAgent**:
        - Write tests for the initialization with a properly mocked StateMachineDocument (without triggering the circular import in OSDM models by mocking at a higher level).
        - Write tests for the execution of a simple state machine (one state, no transitions).
        - Write tests for state transitions based on context.
        - Write tests for entry and exit actions (once implemented).
        - Write tests for error conditions (e.g., missing initial state, invalid state machine document).
   b) **AgentRegistry**:
        - Write tests for registering and retrieving multiple agents.
        - Write tests for running agents with different input types.
        - Write tests for error conditions (e.g., agent not found).
   c) **SkillAgent** (already has tests, but can be expanded):
        - Test error conditions (e.g., skill not found, LLM execution failure).
        - Test both batch and step-wise execution modes.
   d) **InteractionAgent** (once the circular import is fixed):
        - Write tests for the InteractionAgent (if we decide to keep it in the agent engine; note that the interaction layer might be better suited as a separate engine).

### 5. Consider Adding Configuration for the Agent Engine
**Problem**: No centralized configuration for the agent engine.
**Solution**:
   - Consider adding a configuration mechanism (e.g., YAML/JSON file) to set up agents, especially for complex state machines.
   - This could be a separate initiative and might be better handled at the application level.
   - For now, we will note that agents can be configured programmatically via the AgentDefinition and agent constructors.

## Implementation Order
We recommend implementing the enhancements in the following order to minimize disruption and allow for incremental testing:

1. Fix Interaction Agent Circular Import
2. Improve Error Handling and Logging (across all agent types)
3. Enhance State Machine Agent (starting with safe expression evaluation, then entry/exit actions, then proper orchestration)
4. Expand Unit Tests (as we implement each feature, write tests for it)
5. Consider Adding Configuration (lower priority, can be done later)

## Expected Outcome
After implementing these enhancements, we expect the Agent Engine to reach:
- 100% fully implemented requirements (or as close as possible given the pre-existing constraints in the OSDM models).
- Improved reliability, security, and maintainability.
- Better test coverage and documentation.

## Note on OSDM Models
The StateMachineAgent enhancement is partially blocked by the pre-existing circular import in the OSDM models (specifically, importing `StateMachineDocument` triggers a circular import with `ssdm_models`). We cannot fix this without modifying the OSDM models, which is outside the scope of the agent engine. However, we can work around it by:
   - Using mocks in tests that avoid the actual import (as we have done in the test for StateMachineAgent initialization).
   - In production, we hope that the OSDM models are fixed or that we can isolate the import in a way that does not cause the circular import (if the circular import is due to a specific dependency that we can avoid).

We will proceed with the StateMachineAgent enhancements assuming that the OSDM models will be fixed separately or that we can find a workaround.

## Conclusion
This enhancement plan addresses the gaps identified in the conformance document and will bring the Agent Engine to a production-ready state that is fully compliant with the Agent Skills standard and capable of orchestrating complex workflows via state machines.

