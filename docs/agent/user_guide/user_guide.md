# Agent Engine User Guide

## Introduction
The Agent Engine is a lightweight library for defining, creating, and managing agents that can execute skills, orchestrate workflows via state machines, and interact with other systems. It builds upon the Skill Engine to provide higher-level agent capabilities.

## Installation
Assuming you have the agent engine as part of your project, you can install the required dependencies:
```bash
pip install pydantic
```
The engine also depends on the Skill Engine, which should be available in your project.

## Defining an Agent
An agent is defined using the `AgentDefinition` model, which can be instantiated directly or loaded from a configuration file (e.g., YAML, JSON).

### Example: Skill Call Agent
```python
from engines.agent.models import AgentDefinition, AgentType

agent_def = AgentDefinition(
    name="text_reverser",
    description="An agent that reverses input text using a skill.",
    type=AgentType.SKILL,
    skill_id="skills/reverse_text/SKILL.md"  # Relative path to the skill
)
```

### Example: State Machine Agent
```python
from engines.agent.models import AgentDefinition, AgentType
from engines.document.models.osdm_models import StateMachineDocument

# Assume you have a StateMachineDocument instance (e.g., loaded from a file)
state_machine_doc = ...  # Load your OSDM state machine document

agent_def = AgentDefinition(
    name="workflow_orchestrator",
    description="An agent that orchestrates a workflow using a state machine.",
    type=AgentType.STATE_MACHINE,
    state_machine=state_machine_doc
)
```

## Creating and Managing Agents
### Using the Agent Registry
The `AgentRegistry` is used to register, retrieve, and run agents.

```python
from engines.agent.agent_registry import AgentRegistry
from engines.storage.vector.base import VectorDBAdapter  # Optional
from engines.storage.event_log.base import LogStorage    # Optional

# Initialize the registry (optional: pass vector DB and storage for memory)
registry = AgentRegistry(
    vector_db=my_vector_db,  # Can be None
    storage=my_storage       # Can be None
)

# Create an agent instance (example: skill call agent)
from engines.agent.base_agents.skill_agent import SkillAgent
from engines.agent.skill.skill import SkillLoader
from engines.agent.skill.executor import LLMClient

skill_loader = SkillLoader("/path/to/skills")
llm_client = MyLLMClient()  # Your implementation of LLMClient

skill_agent = SkillAgent(
    agent_id="skill_agent_1",
    agent_name="text_reverser",
    skill_id="skills/reverse_text/SKILL.md",
    skill_loader=skill_loader,
    llm_client=llm_client,
    execution_mode="batch"
)

# Register the agent
registry.register(skill_agent)

# Retrieve the agent
agent = registry.get("text_reverser")
if agent is None:
    raise ValueError("Agent not found")

# Run the agent
import asyncio
input_data = {
    "agent_name": "text_reverser",
    "skill_input": {"text": "hello world"}
}
# Note: The registry.run method expects the input data to match the agent's input model.
output = asyncio.run(registry.run("text_reverser", input_data))
print(output)  # Should contain the reversed text
```

### Direct Instantiation
You can also instantiate and use agents directly without the registry:

```python
# Create the agent
agent = SkillAgent(
    agent_id="skill_agent_1",
    agent_name="text_reverser",
    skill_id="skills/reverse_text/SKILL.md",
    skill_loader=skill_loader,
    llm_client=llm_client,
    execution_mode="batch"
)

# Prepare input
input_data = SkillAgentInput(
    agent_name="text_reverser",
    skill_input={"text": "hello world"}
)

# Run the agent
output = asyncio.run(agent.execute(input_data))
print(output.skill_output)  # {'reversed_text': 'dlrow olleh'}
```

## Developing Custom Agents
To create a custom agent type, follow these steps:

1. **Define Input and Output Models** (if needed):
   ```python
   from pydantic import BaseModel
   from engines.agent.models import AgentInput, AgentOutput

   class MyAgentInput(AgentInput):
       # Add custom fields
       my_field: str = Field(default="default")

   class MyAgentOutput(AgentOutput):
       # Add custom fields
       my_result: str = Field(default="")
   ```

2. **Extend the BaseAgent**:
   ```python
   from engines.agent.base_agents.base_agent import BaseAgent

   class MyAgent(BaseAgent[MyAgentInput, MyAgentOutput]):
       async def execute(self, input_model: MyAgentInput) -> MyAgentOutput:
           # Implement your agent's logic here
           result = ...  # Compute result based on input_model
           return MyAgentOutput(
               agent_name=self.agent_name,
               payload={},
               my_result=result
           )
   ```

3. **Register and Use**:
   ```python
   # Instantiate your agent
   my_agent = MyAgent(
       agent_id="my_agent_1",
       agent_name="My Custom Agent",
       # ... other dependencies ...
   )

   # Register with the registry (optional)
   registry.register(my_agent)

   # Run the agent
   input_data = MyAgentInput(agent_name="My Custom Agent", my_field="test")
   output = asyncio.run(registry.run("My Custom Agent", input_data))
   ```

## Best Practices
1. Keep agents focused on a single responsibility.
2. Use the Skill Engine for reusable, atomic skills.
3. Use state machines for complex workflows with conditional logic.
4. Handle errors gracefully in your agent's `execute` method.
5. Register agents with the registry for easy lookup and execution.
6. For state machine agents, design your state machine document carefully:
   - Use state documentation to specify which skill to execute and how to map context to skill inputs.
   - Use transition conditions to determine the flow based on context.
7. Secure your agents: if using `eval()` for conditions (as in the current StateMachineAgent), ensure the context does not contain untrusted data. Consider replacing `eval()` with a safe expression evaluator.

## Troubleshooting
- **Agent not found**: Check that the agent name passed to `registry.get()` or `registry.run()` matches the name used during registration.
- **Skill not found**: Verify that the `skill_id` in the agent definition matches the relative path to a valid SKILL.md file.
- **State machine execution issues**: Ensure that the state machine document is valid and that state documentation is correctly formatted JSON if you are using skill execution in states.
- **Circular import errors**: If you encounter circular imports, consider refactoring to use dependency injection or lazy imports (e.g., import inside a method rather than at the top of the file).

## Further Reading
- [Skill Engine User Guide](../skill/user_guide/user_guide.md) - For defining and using skills.
- [OSDM Specification](https://example.com/osdm) - For defining state machines (placeholder).
