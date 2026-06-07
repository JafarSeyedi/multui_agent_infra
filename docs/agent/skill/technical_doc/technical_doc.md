# Skill Engine Technical Documentation

## Architecture
The Skill Engine consists of the following components:

1. **SkillLoader** (`engines/skill/skill.py`): Responsible for discovering and loading skill definitions from the filesystem.
2. **Skill Model** (`engines/skill/models.py`): Pydantic models representing a skill, its inputs, outputs, and steps.
3. **BatchSkillExecutor** (`engines/skill/executor.py`): Executes a skill in a single LLM call, providing the entire skill context.
4. **StepWiseSkillExecutor** (`engines/skill/executor.py`): Executes a skill step-by-step, allowing for intermediate processing and human-in-the-loop scenarios.
5. **LLMClient** (`engines/skill/executor.py`): An abstract interface for interacting with a language model. Users must provide an implementation.
6. **MCPClient** (`engines/skill/mcp_client.py`): A client for connecting to MCP servers and invoking tools.
7. **AgentInterpreter** (`engines/skill/agent_interpreter.py`): A stub for interpreting agent state diagrams and executing skills accordingly.

## Data Flow
### Skill Loading
1. The `SkillLoader` is initialized with a root directory containing skills.
2. It recursively walks the directory, looking for `SKILL.md` files.
3. For each file, it parses the YAML frontmatter and loads the skill content and references.
4. Loaded skills are stored in a dictionary keyed by their relative path from the root directory.

### Batch Execution
1. The executor receives a skill identifier and a dictionary of inputs.
2. It loads the skill and its reference files.
3. It constructs a prompt that includes:
   - Skill metadata (name, description, version)
   - Skill content
   - Reference contents
   - The provided inputs
   - Instructions to generate output according to the skill's output schema
4. The prompt is sent to the LLM client's `generate_structured_output` method with a JSON schema derived from the skill's outputs.
5. If structured output fails, falls back to text generation and attempts to parse the response as JSON.
6. The LLM's structured output is returned to the caller.

### Step-Wise Execution
1. Similar to batch execution, but the skill is divided into steps.
2. For each step, a prompt is constructed that includes:
   - Skill metadata and content (optional, but currently included for context)
   - Reference contents
   - The inputs and the accumulated context from previous steps
   - Step-specific instructions
   - Instructions to generate output according to the step's output schema (or the skill's outputs if not defined)
3. The LLM is called for each step, and the result is added to the accumulated context for the next step.
4. If structured output fails for a step, falls back to text generation and attempts to parse the response as JSON.
5. The final result is a list of outputs from each step.

## Extension Points
### Custom LLM Client
To use the skill engine with a specific LLM provider (e.g., OpenAI, Anthropic), implement the `LLMClient` interface:
```python
class MyLLMClient(LLMClient):
    def generate_structured_output(self, prompt, output_schema, **kwargs):
        # Call your LLM API with prompt and output_schema
        # Return the parsed structured output
        pass
    
    def generate_text(self, prompt, **kwargs):
        # Call your LLM API for text generation
        pass
```

### MCP Client Usage
The MCP client can be used to connect to an MCP server and call tools:
```python
import asyncio
from engines.agent.skill.mcp_client import MCPClient

async def example():
    client = MCPClient(server_command=["mcp-server", "--arg"])
    await client.connect()
    tools = await client.list_tools()
    result = await client.call_tool("tool_name", {"arg": "value"})
    await client.disconnect()
```

### Agent Interpreter
To interpret agent state diagrams, extend the `AgentInterpreter` class and implement the `interpret_agent_definition` method. The method should:
1. Parse the agent definition (e.g., a state diagram format).
2. For each state, determine the skill to execute and the mode (batch or step-wise).
3. Use the appropriate executor to run the skill.
4. Handle transitions based on the skill output.

### Execution Mode Configuration
Skills can declare their preferred execution mode via the `execution_mode` field in the skill definition:
```yaml
---
name: Example Skill
execution_mode: step-wise
---
```
If not specified, the engine infers the mode: if the skill has steps, it defaults to step-wise; otherwise, batch.

## Dependencies
- pydantic (for skill modeling)
- MCP Python SDK (for MCP client) - install via `pip install mcp`

## Thread Safety
The skill engine is designed to be used in a single-threaded context or with external synchronization. The `SkillLoader` loads skills once at initialization and is immutable thereafter. Executors are stateless and can be used concurrently if the LLM client is thread-safe.

## Performance Considerations
- Skill loading is performed once at startup.
- Reference files are loaded on each skill execution; consider caching if references are large and static.
- The LLM call is the primary latency factor; batch execution minimizes the number of LLM calls.

## Logging
The engine uses the standard `logging` module. Loggers are named after the module (e.g., `engines.agent.skill.executor`). Configure logging in your application to control verbosity.
