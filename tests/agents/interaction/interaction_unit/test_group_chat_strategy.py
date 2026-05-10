# tests/agents/orchestration/interaction/unit/test_group_chat_strategy.py
import pytest

from engines.agents.base_agents.base_agent import BaseAgent
from engines.interaction.group_chat_strategy import GroupChatStrategy
from engines.interaction.interaction_models import InteractionRequest
from tests.agents.interaction.interaction_unit.conftest import TestAgent


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

    agents = [
        BaseAgent(agent_id="alice", agent_name="alice", payload={"display_name": "Alice"}),
        BaseAgent(agent_id="bob", agent_name="bob", payload={"display_name": "Bob"}),
    ]

    strategy = GroupChatStrategy(registry=registry, message_bus=message_bus, storage=None)
    result = await strategy.execute(InteractionRequest(agents=agents, context={}, metadata={"max_rounds": 5, "stop_on_done": True}))

    assert result.success
    assert result.final_context["messages"]
    assert any(m["role"] == "assistant" for m in result.final_context["messages"])
