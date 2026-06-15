from __future__ import annotations

import pytest

from engines.agent.base_agents.base_agent import BaseAgent
from engines.agent.callbacks import (
    CallbackContext,
    CallbackRegistry,
    LlmRequest,
    LlmResponse,
    ToolContext,
)
from engines.agent.models import AgentInput, AgentOutput


class EchoAgent(BaseAgent[AgentInput, AgentOutput]):
    input_model_class = AgentInput
    output_model_class = AgentOutput

    async def execute(self, input_model: AgentInput) -> AgentOutput:
        return AgentOutput(
            agent_name=self.agent_name,
            message=f"echo: {input_model.message}",
            payload={"echo": input_model.message},
        )


class TestBeforeAgentCallback:

    async def test_before_agent_skips_execution_when_returning_content(self):
        async def skip_cb(ctx: CallbackContext) -> dict | None:
            return {"agent_name": "test", "message": "skipped", "payload": {}}

        registry = CallbackRegistry(before_agent=[skip_cb])
        agent = EchoAgent(agent_id="a1", agent_name="test", callback_registry=registry)

        result = await agent.run(AgentInput(agent_name="test", message="hello"))
        assert result.message == "skipped"

    async def test_before_agent_allows_execution_when_returning_none(self):
        calls = []

        async def passthrough_cb(ctx: CallbackContext) -> dict | None:
            calls.append("before")
            return None

        registry = CallbackRegistry(before_agent=[passthrough_cb])
        agent = EchoAgent(agent_id="a1", agent_name="test", callback_registry=registry)

        result = await agent.run(AgentInput(agent_name="test", message="hello"))
        assert result.message == "echo: hello"
        assert calls == ["before"]

    async def test_multiple_before_agent_callbacks_first_wins(self):
        async def first_cb(ctx: CallbackContext) -> dict | None:
            return {"agent_name": "test", "message": "first", "payload": {}}

        async def second_cb(ctx: CallbackContext) -> dict | None:
            return {"agent_name": "test", "message": "second", "payload": {}}

        registry = CallbackRegistry(before_agent=[first_cb, second_cb])
        agent = EchoAgent(agent_id="a1", agent_name="test", callback_registry=registry)

        result = await agent.run(AgentInput(agent_name="test", message="hello"))
        assert result.message == "first"


class TestAfterAgentCallback:

    async def test_after_agent_runs_after_execution(self):
        calls = []

        async def after_cb(ctx: CallbackContext) -> None:
            calls.append("after")
            assert ctx.agent_name == "test"

        registry = CallbackRegistry(after_agent=[after_cb])
        agent = EchoAgent(agent_id="a1", agent_name="test", callback_registry=registry)

        result = await agent.run(AgentInput(agent_name="test", message="hello"))
        assert result.message == "echo: hello"
        assert calls == ["after"]

    async def test_after_agent_not_called_when_before_skips(self):
        calls = []

        async def skip_cb(ctx: CallbackContext) -> dict | None:
            return {"agent_name": "test", "message": "skipped", "payload": {}}

        async def after_cb(ctx: CallbackContext) -> None:
            calls.append("after")

        registry = CallbackRegistry(before_agent=[skip_cb], after_agent=[after_cb])
        agent = EchoAgent(agent_id="a1", agent_name="test", callback_registry=registry)

        await agent.run(AgentInput(agent_name="test", message="hello"))
        assert calls == []

    async def test_after_agent_not_called_when_execution_fails(self):
        calls = []

        class FailAgent(EchoAgent):
            async def execute(self, input_model: AgentInput) -> AgentOutput:
                raise ValueError("fail")

        async def after_cb(ctx: CallbackContext) -> None:
            calls.append("after")

        registry = CallbackRegistry(after_agent=[after_cb])
        agent = FailAgent(agent_id="a1", agent_name="fail", callback_registry=registry)

        with pytest.raises(ValueError):
            await agent.run(AgentInput(agent_name="fail", message="hello"))
        assert calls == []


class TestCallbackContext:

    async def test_context_includes_agent_info(self):
        captured = []

        async def capture_cb(ctx: CallbackContext) -> dict | None:
            captured.append(ctx)
            return None

        registry = CallbackRegistry(before_agent=[capture_cb])
        agent = EchoAgent(agent_id="a1", agent_name="test", callback_registry=registry)

        await agent.run(AgentInput(agent_name="test", message="hello"))
        assert len(captured) == 1
        assert captured[0].agent_name == "test"
        assert captured[0].agent_id == "a1"

    async def test_context_state_is_mutable(self):
        async def mutate_cb(ctx: CallbackContext) -> dict | None:
            ctx.state["key"] = "value"
            return None

        async def check_cb(ctx: CallbackContext) -> None:
            assert ctx.state.get("key") == "value"

        registry = CallbackRegistry(before_agent=[mutate_cb], after_agent=[check_cb])
        agent = EchoAgent(agent_id="a1", agent_name="test", callback_registry=registry)

        await agent.run(AgentInput(agent_name="test", message="hello"))


class TestToolContext:

    async def test_tool_context_extends_callback_context(self):
        ctx = ToolContext(
            agent_name="test",
            agent_id="a1",
            tool_name="search",
        )
        assert ctx.agent_name == "test"
        assert ctx.tool_name == "search"


class TestLlmRequestResponse:

    async def test_llm_request_defaults(self):
        req = LlmRequest()
        assert req.contents == []
        assert req.config == {}

    async def test_llm_response_defaults(self):
        resp = LlmResponse()
        assert resp.text == ""
        assert resp.content is None
