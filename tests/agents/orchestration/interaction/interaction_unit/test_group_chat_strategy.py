# tests/agents/orchestration/interaction/unit/test_group_chat_strategy.py

import pytest
from agents.orchestration.interaction.group_chat_strategy import GroupChatStrategy
from agents.orchestration.models import OrchestrationRequest, TaskDefinition

from tests.agents.orchestration.interaction.interaction_unit.conftest import TestAgent


@pytest.mark.asyncio
async def test_group_chat_rounds_and_done_flag(registry, message_bus):
    def make_agent(name, message, done=False):
        async def responder(payload):
            content = f"{name}-{payload['messages'][-1]['content'] if payload['messages'] else 'start'}"
            data = {"message": content}
            if done:
                data["done"] = True
            return data
        return TestAgent(name, responder)

    registry.register(make_agent("alice", "hello"))
    registry.register(make_agent("bob", "world", done=True))

    tasks = [
        TaskDefinition(task_id="alice", agent_name="alice", payload={"display_name": "Alice"}),
        TaskDefinition(task_id="bob", agent_name="bob", payload={"display_name": "Bob"}),
    ]

    strategy = GroupChatStrategy(registry=registry, message_bus=message_bus, storage=None)
    result = await strategy.execute(OrchestrationRequest(tasks=tasks, context={}, metadata={"max_rounds": 5, "stop_on_done": True}))

    assert result.success
    assert result.final_context["messages"]
    assert any(m["role"] == "assistant" for m in result.final_context["messages"])
