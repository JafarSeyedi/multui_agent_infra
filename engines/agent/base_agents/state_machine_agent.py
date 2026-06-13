from typing import Any, Optional

from ..._types import MessagePayload, Metadata
import json
from pydantic import Field
from .base_agent import BaseAgent
from ..models import AgentInput, AgentOutput
from engines.agent.skill.skill import SkillLoader
from engines.agent.skill.executor import BatchSkillExecutor, StepWiseSkillExecutor, LLMClient, SkillExecutor


class StateMachineAgentInput(AgentInput):
    """Input for a state machine agent."""
    # Initial context to start the state machine with
    initial_context: Metadata = Field(default_factory=dict)


class StateMachineAgentOutput(AgentOutput):
    """Output from a state machine agent."""
    # Final context after state machine execution
    final_context: Metadata = Field(default_factory=dict)
    # The ID of the final state reached
    final_state_id: str | None = None


class StateMachineAgent(BaseAgent[StateMachineAgentInput, StateMachineAgentOutput]):
    """
    An agent that executes a state machine defined by an OSDM StateMachineDocument.
    The state machine orchestrates the execution of skills.
    """

    def __init__(
        self,
        agent_id: str,
        agent_name: str,
        state_machine_doc: Any,  # We'll import StateMachineDocument inside the method to avoid circular import
        skill_loader: SkillLoader,
        llm_client: LLMClient,
        vector_db: Any = None,
        storage: Any = None,
        metadata: Metadata | None = None,
    ) -> None:
        # Import StateMachineDocument here to avoid circular import issues
        try:
            from engines.orchestration.models.osdm_models import StateMachineDocument
            if not isinstance(state_machine_doc, StateMachineDocument):
                raise ValueError("state_machine_doc must be an instance of StateMachineDocument")
        except ImportError as e:
            raise ImportError("Could not import StateMachineDocument from engines.orchestration.models.osdm_models") from e

        super().__init__(
            agent_id=agent_id,
            agent_name=agent_name,
            vector_db=vector_db,
            storage=storage,
            metadata=metadata,
        )
        self.state_machine_doc = state_machine_doc
        self.skill_loader = skill_loader
        self.llm_client = llm_client

        # We'll assume the state machine document has exactly one state machine
        # In the future, we could support multiple by name.
        if not self.state_machine_doc.state_machines:
            raise ValueError("StateMachineDocument must contain at least one state machine")
        self.state_machine: Any = self.state_machine_doc.state_machines[0]  # Type Any to avoid import

        # Prepare executors for skills (we'll create them on demand)
        self._batch_executor = BatchSkillExecutor(llm_client, skill_loader)
        self._stepwise_executor = StepWiseSkillExecutor(llm_client, skill_loader)

    async def execute(self, input_model: StateMachineAgentInput) -> StateMachineAgentOutput:
        # Initialize context with the initial context from input
        context: Metadata = dict(input_model.initial_context)
        
        # Find the initial state
        initial_state = self._find_initial_state()
        if initial_state is None:
            raise ValueError("Could not find initial state in state machine")
        
        # Execute the state machine
        final_state_id, final_context = await self._execute_state_machine(initial_state, context)
        
        return StateMachineAgentOutput(
            agent_name=self.agent_name,
            payload={},
            final_context=final_context,
            final_state_id=final_state_id
        )

    def _find_initial_state(self) -> Any | None:
        """
        Find the initial state of the state machine.
        Looks for a pseudo_state of kind INITIAL, or uses the region's initial_state if set.
        """
        # Import PseudoStateKind here to avoid circular import issues
        from engines.orchestration.models.osdm_models import PseudoStateKind
        # We'll use Any for state and region types to avoid importing
        region = self.state_machine.top_region
        # First, look for an initial pseudo state
        for pseudo_state in self.state_machine.pseudo_states:
            if pseudo_state.kind == PseudoStateKind.INITIAL:
                if pseudo_state.outgoing and len(pseudo_state.outgoing) > 0:
                    # The outgoing transition's target is the initial state
                    # We need to resolve the target state from the transition
                    # For simplicity, we assume the transition.target is set
                    # In the OSDM model, the transition has a target_ref which is resolved later.
                    # We'll assume that the model has been resolved and target is set.
                    # If not, we'll need to resolve it ourselves.
                    # We'll do a simple search by name or id later.
                    # For now, we'll return the first state we find that is targeted by an initial pseudo state.
                    # This is a simplification.
                    # We'll try to get the target state from the transition
                    if hasattr(pseudo_state.outgoing[0], 'target') and pseudo_state.outgoing[0].target is not None:
                        return pseudo_state.outgoing[0].target
        # If we didn't find via pseudo state, check if the region has an initial_state set
        if hasattr(region, 'initial_state') and region.initial_state is not None:
            return region.initial_state
        
        # Fallback: look for a state with no incoming transitions (not reliable)
        # Instead, we'll just return the first state in the region for now.
        # This is a placeholder; proper implementation requires resolving the state machine graph.
        if hasattr(region, 'states') and region.states:
            return region.states[0]
        return None

    async def _execute_state_machine(self, initial_state: Any, initial_context: Metadata) -> tuple[str | None, Metadata]:
        """
        Execute the state machine starting from the given state.
        Returns (final_state_id, final_context).
        """
        current_state = initial_state
        context = dict(initial_context)
        
        # We'll keep track of visited states to detect loops (simplistic)
        visited_states = set()
        
        while current_state is not None:
            state_id = getattr(current_state, 'id', None)
            if state_id in visited_states:
                # Prevent infinite loops
                break
            visited_states.add(state_id)
            
            # Execute entry actions of the state (if any are skills)
            await self._execute_entry_actions(current_state, context)
            
            # Execute the state's main activity (if it is a skill)
            # We'll assume that if the state's documentation indicates a skill, we run it.
            skill_result = await self._execute_state_skill(current_state, context)
            if skill_result is not None:
                # Update context with the skill result
                if isinstance(skill_result, dict):
                    context.update(skill_result)
                elif isinstance(skill_result, list) and len(skill_result) > 0:
                    # Assume the last element is the output
                    context.update(skill_result[-1])
            
            # Check if this is a final state
            if getattr(current_state, 'is_final', False):
                break
            
            # Evaluate transitions to find the next state
            next_state = self._evaluate_transitions(current_state, context)
            if next_state is None:
                # No transition taken, we stop
                break
            
            current_state = next_state
        
        final_state_id = getattr(current_state, 'id', None) if current_state else None
        return final_state_id, context

    async def _execute_entry_actions(self, state: Any, context: Metadata) -> None:
        """
        Execute entry actions of the state. We assume entry actions are scripts that may invoke skills.
        For simplicity, we'll only handle if the entry action is a skill call.
        We'll look for skill_id in the documentation.
        """
        # We'll skip complex entry actions for now and focus on the state's main skill.
        pass

    async def _execute_state_skill(self, state: Any, context: Metadata) -> Any | None:
        """
        Execute the skill associated with this state, if any.
        Returns the skill result.
        """
        # Check if the state's documentation contains a skill ID
        documentation = getattr(state, 'documentation', None)
        if documentation:
            try:
                doc_data = json.loads(documentation)
                skill_id = doc_data.get('skill_id')
                if skill_id:
                    # Prepare inputs for the skill
                    skill_inputs = {}
                    # We'll allow mapping from context to skill inputs via a 'skill_inputs' map
                    skill_input_map = doc_data.get('skill_inputs', {})
                    for skill_input_name, value_or_ref in skill_input_map.items():
                        if isinstance(value_or_ref, str) and value_or_ref.startswith('context:'):
                            # Reference to context
                            ref_key = value_or_ref[8:]  # remove 'context:'
                            skill_inputs[skill_input_name] = context.get(ref_key)
                        else:
                            # Literal value
                            skill_inputs[skill_input_name] = value_or_ref
                    
                    # Determine execution mode
                    execution_mode = doc_data.get('execution_mode', 'batch')
                    executor: SkillExecutor
                    if execution_mode == 'batch':
                        executor = self._batch_executor
                    else:
                        executor = self._stepwise_executor
                    
                    # Execute the skill
                    skill_result = executor.execute(
                        skill_identifier=skill_id,
                        inputs=skill_inputs
                    )
                    return skill_result
            except (json.JSONDecodeError, KeyError, ValueError) as _:
                # If documentation is not valid JSON or missing required fields, we skip skill execution
                # In a real system, we would log this.
                pass
        
        # No skill to execute in this state
        return None

    def _evaluate_transitions(self, state: Any, context: Metadata) -> Any | None:
        """
        Evaluate the outgoing transitions of the state to determine the next state.
        Returns the next state if a transition is taken, otherwise None.
        """
        # Sort transitions by priority? We'll just take the first one that evaluates to True.
        for transition in getattr(state, 'outgoing_transitions', []) or []:
            if self._evaluate_transition_condition(transition, context):
                # Return the target state of the transition
                return getattr(transition, 'target', None)
        return None

    def _evaluate_transition_condition(self, transition: Any, context: Metadata) -> bool:
        """
        Evaluate the condition (guard) of a transition.
        Returns True if the transition should be taken.
        """
        condition = getattr(transition, 'condition', None)
        if condition is None:
            return True

        body = getattr(condition, 'body', '')
        if not body.strip():
            return True

        try:
            from engines.agent.base_agents.safe_eval import safe_expr_eval
            result = safe_expr_eval(body, {"context": context})
            return bool(result)
        except Exception:
            return False
