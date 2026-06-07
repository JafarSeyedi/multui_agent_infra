# Skill Engine Plan

## Overview
The Skill Engine is responsible for loading, managing, and executing skills based on the Agent Skills standard. It supports both batch and step-wise execution modes, integrates with MCP (Model Context Protocol) for tool usage, and provides an interpreter for agent state diagrams.

## Goals
1. Provide a lightweight skill library that can be integrated into existing orchestration layers.
2. Support progressive disclosure of skill references.
3. Enable batch execution (single LLM call) for low-latency, low-cost scenarios.
4. Enable step-wise execution for skills requiring human interaction or intermediate processing.
5. Expose existing orchestration and RAG capabilities as MCP tools.
6. Interpret declarative agent definitions to execute skills in the appropriate mode.

## Scope
- Skill definition parsing (YAML frontmatter in SKILL.md files)
- Skill registry and loader
- Batch skill executor
- Step-wise skill executor
- MCP client for connecting to MCP servers
- Agent interpreter for executing agent state diagrams (stubbed for future implementation)

## Non-Goals
- Providing a full-fledged agent framework with built-in memory, planning, etc. (these are handled by other layers)
- Implementing a graphical skill editor (though the skill definition format is designed to be human-readable and editable)

## Milestones
1. Basic skill loader and registry (complete)
2. Batch and step-wise executors with LLM client abstraction (complete)
3. MCP client implementation (complete)
4. Agent interpreter stub (complete)
5. Comprehensive test suite (in progress)
6. Documentation (in progress)

## Resources
- [Agent Skills Standard](https://example.com/agent-skills-standard) (placeholder)
- [MCP Specification](https://example.com/mcp) (placeholder)
