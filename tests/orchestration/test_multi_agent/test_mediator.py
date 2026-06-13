"""Tests for MultiAgentMediator."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, PropertyMock

import pytest

from engines.orchestration.multi_agent.mediator import MultiAgentMediator
from engines.orchestration.multi_agent.message_router import AgentMessage


@pytest.fixture
def orchestration_engine():
    engine = MagicMock()
    engine.event_bus = AsyncMock()
    engine.state_manager = AsyncMock()
    return engine


@pytest.fixture
def mediator(orchestration_engine):
    return MultiAgentMediator(orchestration_engine)


@pytest.fixture
def mock_instance():
    inst = MagicMock()
    inst.id = "inst-1"
    inst.variables = {}
    return inst


@pytest.fixture
def mock_definition():
    dfn = MagicMock()
    dfn.id = "def-1"
    dfn.key = "process-1"
    return dfn


class TestAgentRegistration:
    """register_agent and get_agent."""

    def test_register_and_get(self, mediator):
        mediator.register_agent("agent-1", {"name": "Alice"})
        assert mediator.get_agent("agent-1") == {"name": "Alice"}

    def test_get_unknown(self, mediator):
        assert mediator.get_agent("nobody") is None

    def test_register_overwrites(self, mediator):
        mediator.register_agent("agent-1", {"name": "Alice"})
        mediator.register_agent("agent-1", {"name": "Bob"})
        assert mediator.get_agent("agent-1") == {"name": "Bob"}


class TestNotify:
    """notify publishes events through the engine's event bus."""

    @pytest.mark.asyncio
    async def test_notify_publishes_event(self, mediator, orchestration_engine):
        await mediator.notify("test_sender", "test_event", {"key": "val"})
        orchestration_engine.event_bus.publish.assert_awaited_once()
        args = orchestration_engine.event_bus.publish.await_args[0][0]
        assert args.data.get("sender") == "test_sender"
        assert args.data.get("event") == "test_event"


class TestSendMessage:
    """send_message delegates to message_router."""

    @pytest.mark.asyncio
    async def test_send_message(self, mediator):
        mediator.message_router = AsyncMock()
        msg = AgentMessage(sender="a1", receiver="a2", content="hi")
        await mediator.send_message(msg)
        mediator.message_router.route.assert_called_once()

    @pytest.mark.asyncio
    async def test_broadcast(self, mediator):
        mediator.message_router = AsyncMock()
        msg = AgentMessage(sender="a1", receiver="all", content="hi")
        await mediator.broadcast(msg, ["a1", "a2"])
        mediator.message_router.broadcast.assert_called_once()


class TestAgentExecution:
    """execute_agent delegates to agent_executor and notifies."""

    @pytest.mark.asyncio
    async def test_execute_agent(self, mediator, mock_instance):
        mediator.agent_executor = AsyncMock()
        mediator.agent_executor.execute.return_value = MagicMock(success=True, result="done")
        agent = {"id": "agent-1", "name": "Alice"}
        result = await mediator.execute_agent(agent, mock_instance)
        assert result.success is True


class TestCoordinate:
    """coordinate delegates to CoordinationHandler."""

    @pytest.mark.asyncio
    async def test_coordinate(self, mediator, mock_instance):
        mediator.coordinator = AsyncMock()
        mediator.coordinator.coordinate.return_value = {"status": "ok"}
        plan = MagicMock()
        plan.coordination_pattern = "orchestration"
        result = await mediator.coordinate("inst-1", plan, mock_instance)
        assert result == {"status": "ok"}


class TestExecuteWorkflow:
    """execute_workflow orchestrates the full multi-agent lifecycle."""

    @pytest.mark.asyncio
    async def test_full_workflow_success(self, mediator, mock_instance, mock_definition):
        mediator.coordinator = AsyncMock()
        mediator.coordinator.coordinate.return_value = {"coordinated": True}
        mediator.interaction_handler = AsyncMock()
        mediator.interaction_handler.handle.return_value = {"handled": True}
        mediator.protocol_handler = AsyncMock()
        mediator.protocol_handler.execute.return_value = {"executed": True}
        mediator.negotiation_handler = AsyncMock()
        mediator.negotiation_handler.negotiate.return_value = {"negotiated": True}
        mediator.agent_executor = AsyncMock()
        mediator.agent_executor.execute.return_value = MagicMock(success=True, result="ok")

        plan = MagicMock()
        plan.coordination_pattern = "orchestration"
        plan.agents = [{"id": "agent-1", "name": "Alice"}]
        plan.interactions = [{"id": "interact-1", "type": "chat"}]
        plan.protocols = [{"id": "proto-1", "type": "fipa"}]
        plan.negotiation_config = {"strategy": "cooperative"}

        result = await mediator.execute_workflow(mock_instance, mock_definition, plan)
        assert result.success is True
        assert "coordination" in result.results

    @pytest.mark.asyncio
    async def test_workflow_failure_returns_error(self, mediator, mock_instance, mock_definition):
        mediator.coordinator = AsyncMock()
        mediator.coordinator.coordinate.side_effect = RuntimeError("coordination failed")

        plan = MagicMock()
        plan.coordination_pattern = "orchestration"
        plan.agents = []
        plan.interactions = []
        plan.protocols = []
        plan.negotiation_config = {}

        result = await mediator.execute_workflow(mock_instance, mock_definition, plan)
        assert result.success is False
        assert len(result.errors) > 0
