# Skill Engine User Guide

## Introduction
The Skill Engine is a lightweight library for defining, loading, and executing skills according to the Agent Skills standard. It supports both batch and step-wise execution modes, complex types, fallback mechanisms, and integrates with the Model Context Protocol (MCP) for tool usage.

## Installation
Assuming you have the skill engine as part of your project, you can install the required dependencies:
```bash
pip install pydantic mcp
```
The engine itself is imported from your project's `engines.skill` package.

## Defining a Skill
A skill is defined in a file named `SKILL.md` with YAML frontmatter and markdown content.

### Example: Simple Text Reversal Skill
Create a file `skills/reverse_text/SKILL.md` with the following content:
```yaml
---
name: Reverse Text
description: Reverses the input string.
version: "1.0.0"
author: You
tags: [text, example]
inputs:
  - name: text
    description: The string to reverse.
    type: string
    required: true
outputs:
  - name: reversed_text
    description: The reversed string.
    type: string
---
# Reverse Text Skill

This skill takes a string and returns its reverse.

## How it works
The skill simply reverses the characters in the input string.
```
### Example: Skill with Complex Output
Create a file `skills/person_info/SKILL.md` with the following content:
```yaml
---
name: Person Info
description: Extracts person information from text.
version: "1.0.0"
author: You
tags: [nlp, example]
inputs:
  - name: bio_text
    description: A biography text.
    type: string
    required: true
outputs:
  - name: person
    description: Information about the person.
    type: object
    output_schema:
      type: object
      properties:
        name:
          type: string
          description: The person's name.
        age:
          type: integer
          description: The person's age.
        occupation:
          type: string
          description: The person's occupation.
      required: [name]
---
# Person Info Skill

This skill extracts structured person information from a biography text.
```
### Inputs and Outputs
Each input and output has:
- `name`: The identifier used in the inputs/outputs dictionary.
- `description`: A human-readable description.
- `type`: The data type (e.g., "string", "number", "boolean", "object", "array"). 
- `output_schema` (optional): A JSON schema defining the exact structure of the output. Required for complex types (object, array) and recommended for precise validation.
- `required` (inputs only): Whether the input must be provided.

### Steps (Optional)
If you want to break the skill into multiple steps, define a `steps` list. Each step can have:
- `name`: Step identifier.
- `description`: What the step does.
- `instructions`: Specific instructions for the LLM at this step.
- `output_schema`: A JSON schema defining the expected output of this step (optional). If omitted, the step's output is not constrained by the engine (but you can still describe it in the instructions).

### Execution Mode (Optional)
You can explicitly set the execution mode for a skill:
```yaml
---
name: My Skill
execution_mode: step-wise   # or "batch"
---
```
If not specified, the engine infers the mode: if the skill has steps, it defaults to step-wise; otherwise, batch.

## Loading Skills
Create a `SkillLoader` instance pointing to the directory containing your skills:
```python
from engines.agent.skill.skill import SkillLoader

loader = SkillLoader("/path/to/skills")
```
The loader will automatically discover all `SKILL.md` files in subdirectories.

To get a list of loaded skill identifiers:
```python
skill_ids = loader.list_skills()
```
To retrieve a specific skill:
```python
skill = loader.get_skill("reverse_text/SKILL.md")  # identifier is relative path
```
Note: The identifier is the relative path from the skills directory to the SKILL.md file.

## Executing a Skill (Batch Mode)
For skills that can be executed in a single LLM call, use the `BatchSkillExecutor`.

### Step 1: Implement the LLM Client
You must provide an implementation of the `LLMClient` abstract class. Here is an example using a hypothetical LLM provider:
```python
from engines.agent.skill.executor import LLMClient

class MyLLMClient(LLMClient):
    def generate_structured_output(self, prompt, output_schema, **kwargs):
        # Call your LLM's structured output endpoint
        # For example, using OpenAI's API with the `response_format` parameter
        # Parse the response and return the structured data.
        pass
    
    def generate_text(self, prompt, **kwargs):
        # Call your LLM's text generation endpoint
        pass
```

### Step 2: Create the Executor
```python
from engines.agent.skill.executor import BatchSkillExecutor

llm_client = MyLLMClient()
executor = BatchSkillExecutor(llm_client, loader)
```

### Step 3: Execute the Skill
```python
inputs = {"text": "hello world"}
result = executor.execute("reverse_text/SKILL.md", inputs)
print(result)  # {'reversed_text': 'dlrow olleh'}
```

## Executing a Skill (Step-Wise Mode)
For skills that require intermediate steps or human interaction, use the `StepWiseSkillExecutor`.

The setup is the same as for batch execution, but you use `StepWiseSkillExecutor`:
```python
from engines.agent.skill.executor import StepWiseSkillExecutor

executor = StepWiseSkillExecutor(llm_client, loader)
```
The `execute` method returns a list of results, one for each step.

## Using the MCP Client
To expose your orchestration or RAG capabilities as MCP tools, or to call external MCP tools, use the `MCPClient`.

### Connecting to an MCP Server
```python
import asyncio
from engines.agent.skill.mcp_client import MCPClient

async def mcp_example():
    # For a server that runs via stdio
    client = MCPClient(server_command=["mcp-server-executable", "--arg"])
    await client.connect()
    
    # List available tools
    tools = await client.list_tools()
    print("Available tools:", tools)
    
    # Call a tool
    result = await client.call_tool("some_tool", {"param": "value"})
    print("Tool result:", result)
    
    await client.disconnect()

asyncio.run(mcp_example())
```
Note: The MCP client is asynchronous; you must run it in an async context.

## Agent Interpretation (Advanced)
If you have a visual modeler that produces agent state diagrams, you can use the `AgentInterpreter` to execute them. Currently, the interpreter is a stub and must be extended to understand your specific agent definition format.

```python
from engines.agent.skill.agent_interpreter import AgentInterpreter

class MyAgentInterpreter(AgentInterpreter):
    def interpret_agent_definition(self, agent_definition):
        # Implement parsing of your agent definition format
        # For each state, determine the skill and mode
        # Execute the skill using the appropriate executor
        # Handle transitions based on output
        pass

interpreter = MyAgentInterpreter(skill_loader, llm_client)
result = interpreter.interpret_agent_definition(my_agent_def)
```

## Best Practices
1. Keep skills focused on a single, well-defined task.
2. Use references to avoid duplicating large prompts or data in every skill.
3. For batch skills, design the skill to produce a complete output in one LLM call.
4. For step-wise skills, ensure each step has a clear purpose and that the output of one step serves as input to the next.
5. For complex outputs, always provide an `output_schema` to ensure proper validation.
6. Handle errors from the LLM client appropriately in your application.
7. Cache the `SkillLoader` if you need to create multiple executors, as loading skills can be I/O intensive.
8. Configure logging in your application to monitor skill execution.

## Troubleshooting
- **Skill not found**: Check that the identifier you pass to `get_skill` or `execute` matches the relative path from the skills directory.
- **Reference file not found**: Ensure that the reference paths in the skill's `references` list are relative to the directory containing the SKILL.md file.
- **LLM client errors**: Verify that your LLM client implementation correctly handles the structured output request and returns data matching the expected schema.
- **JSON parsing errors**: If the LLM returns invalid JSON in text fallback mode, check the prompt and LLM configuration.
- **MCP connection errors**: Make sure the MCP server is running and accessible via the provided command or URL.

## Further Reading
- [Agent Skills Standard](https://example.com/agent-skills-standard)
- [MCP Specification](https://example.com/mcp)
