from __future__ import annotations

import pytest

from engines.agent.models import AgentInput, AgentOutput
from engines.session.service import InMemorySessionService


class FakeAgent:
    def __init__(self):
        self.last_input: AgentInput | None = None

    async def run(self, input_data: AgentInput) -> AgentOutput:
        self.last_input = input_data
        return AgentOutput(
            agent_name="fake_agent",
            message=f"echo: {input_data.message}",
            payload={"echo": input_data.message},
        )


class TestRunner:

    @pytest.fixture
    def runner(self):
        from engines.orchestration.multi_agent.runner import Runner
        agent = FakeAgent()
        session_service = InMemorySessionService()
        return Runner(
            agent=agent,
            app_name="test_app",
            session_service=session_service,
        )

    async def test_run_creates_session(self, runner):
        events = []
        async for event in runner.run_async(
            user_id="user1",
            session_id="sess1",
            new_message="hello",
        ):
            events.append(event)

        assert len(events) > 0
        session = await runner.session_service.get_session(
            "test_app", "user1", "sess1",
        )
        assert session is not None
        assert len(session.events) > 0

    async def test_run_yields_user_event_first(self, runner):
        events = []
        async for event in runner.run_async(
            user_id="user1", session_id="sess1", new_message="hello",
        ):
            events.append(event)

        assert events[0].author == "user"
        assert events[0].content == {"text": "hello"}

    async def test_run_yields_agent_event(self, runner):
        events = []
        async for event in runner.run_async(
            user_id="user1", session_id="sess1", new_message="hello",
        ):
            events.append(event)

        agent_events = [e for e in events if e.author == "agent"]
        assert len(agent_events) >= 1

    async def test_run_multiple_turns_same_session(self, runner):
        events_1 = []
        async for e in runner.run_async("user1", "sess1", "turn1"):
            events_1.append(e)

        events_2 = []
        async for e in runner.run_async("user1", "sess1", "turn2"):
            events_2.append(e)

        session = await runner.session_service.get_session(
            "test_app", "user1", "sess1",
        )
        assert session is not None
        assert len(session.events) >= 4

    async def test_run_different_sessions_isolated(self, runner):
        async for _ in runner.run_async("user1", "sess_a", "msg"):
            pass
        async for _ in runner.run_async("user1", "sess_b", "msg"):
            pass

        sess_a = await runner.session_service.get_session(
            "test_app", "user1", "sess_a",
        )
        sess_b = await runner.session_service.get_session(
            "test_app", "user1", "sess_b",
        )
        assert sess_a is not None
        assert sess_b is not None
        assert sess_a.id != sess_b.id

    async def test_run_passes_message_to_agent(self, runner):
        async for _ in runner.run_async("user1", "sess1", "hello world"):
            pass
        assert runner._agent.last_input is not None
        assert runner._agent.last_input.message == "hello world"

    async def test_run_agent_output_in_event(self, runner):
        events = []
        async for e in runner.run_async("user1", "sess1", "ping"):
            events.append(e)
        agent_event = [e for e in events if e.author == "agent"][0]
        assert agent_event.content is not None
        assert "echo" in str(agent_event.content)
