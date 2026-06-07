from typing import Any

from pydantic import Field

from .base_agent import BaseAgent
from ..models import AgentInput, AgentOutput
from engines.agent.skill.skill import SkillLoader
from engines.agent.skill.executor import BatchSkillExecutor, StepWiseSkillExecutor, LLMClient, SkillExecutor


class SkillAgentInput(AgentInput):
    """Input for a skill call agent."""
    # The input to the skill
    skill_input: dict[str, Any] = Field(default_factory=dict)


class SkillAgentOutput(AgentOutput):
    """Output from a skill call agent."""
    # The output from the skill
    skill_output: dict[str, Any] = Field(default_factory=dict)


class SkillAgent(BaseAgent[SkillAgentInput, SkillAgentOutput]):
    """
    An agent that executes a single skill.
    """

    input_model_class = SkillAgentInput
    output_model_class = SkillAgentOutput

    def __init__(
        self,
        agent_id: str,
        agent_name: str,
        skill_id: str,
        skill_loader: SkillLoader,
        llm_client: LLMClient,
        execution_mode: str = "batch",  # or "step-wise"
        vector_db: Any = None,
        storage: Any = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        # We'll use a generic BaseAgent with our input/output models
        super().__init__(
            agent_id=agent_id,
            agent_name=agent_name,
            vector_db=vector_db,
            storage=storage,
            metadata=metadata,
        )
        self.skill_id = skill_id
        self.skill_loader = skill_loader
        self.llm_client = llm_client
        self.execution_mode = execution_mode
        self.executor: SkillExecutor
        if execution_mode == "batch":
            self.executor = BatchSkillExecutor(llm_client, skill_loader)
        else:
            self.executor = StepWiseSkillExecutor(llm_client, skill_loader)

    async def execute(self, input_model: SkillAgentInput) -> SkillAgentOutput:
        # Execute the skill
        skill_result = self.executor.execute(
            skill_identifier=self.skill_id,
            inputs=input_model.skill_input
        )
        
        # If step-wise, the result is a list; we'll take the last step's output as the agent output
        if isinstance(skill_result, list) and len(skill_result) > 0:
            # For step-wise, we assume the last step produces the final output
            final_skill_output = skill_result[-1]
        else:
            final_skill_output = skill_result
        
        return SkillAgentOutput(
            agent_name=self.agent_name,
            payload={},
            skill_output=final_skill_output
        )

    # We don't need to override run because the base agent's run will call our execute
    # However, note that the base agent expects AgentInput and AgentOutput, but we have subclasses.
    # The base agent is generic, so it should work.
