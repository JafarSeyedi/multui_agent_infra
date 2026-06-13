"""Tests for Bridge pattern (M10) — ProcessEngine abstraction / EngineImplementor."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from engines.orchestration.core.engine_bridge import (
    BPMNImplementor,
    CMMNImplementor,
    DMNImplementor,
    EngineBridge,
    EngineBridgeRegistry,
    EngineImplementor,
    LoggingEngineBridge,
    MultiAgentImplementor,
    ObservableEngineBridge,
    ProcessEngine,
    StateMachineImplementor,
    _GenericImplementor,
    create_engine_bridge,
)
from engines.orchestration.core.event_bus import EventBus, EventType


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
    dfn.definition_type = "bpmn"
    return dfn


class TestImplementors:
    """EngineImplementor hierarchy wraps raw engines correctly."""

    def test_engine_type(self):
        assert BPMNImplementor(MagicMock()).engine_type() == "bpmn"
        assert MultiAgentImplementor(MagicMock()).engine_type() == "multi_agent"
        assert StateMachineImplementor(MagicMock()).engine_type() == "state_machine"
        assert CMMNImplementor(MagicMock()).engine_type() == "cmmn"
        assert DMNImplementor(MagicMock()).engine_type() == "dmn"

    @pytest.mark.asyncio
    async def test_bpmn_implementor_delegates(self, mock_instance, mock_definition):
        raw = AsyncMock()
        impl = BPMNImplementor(raw)
        await impl.execute_instance(mock_instance, mock_definition)
        raw.execute_instance.assert_awaited_once_with(mock_instance, mock_definition)

    @pytest.mark.asyncio
    async def test_generic_implementor(self, mock_instance, mock_definition):
        raw = AsyncMock()
        impl = _GenericImplementor(raw)
        assert "mock" in impl.engine_type()
        await impl.execute_instance(mock_instance, mock_definition)
        raw.execute_instance.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_generic_implementor_missing_execute(self, mock_instance, mock_definition):
        impl = _GenericImplementor(object())
        with pytest.raises(TypeError, match="lacks execute_instance"):
            await impl.execute_instance(mock_instance, mock_definition)

    @pytest.mark.asyncio
    async def test_validate_and_cancel_defaults(self):
        impl = BPMNImplementor(MagicMock())
        assert impl.engine_type() == "bpmn"
        assert await impl.validate(MagicMock()) == []
        await impl.cancel("x")


class TestProcessEngine:
    """ProcessEngine abstraction delegates to implementor."""

    @pytest.mark.asyncio
    async def test_engine_bridge_execute(self, mock_instance, mock_definition):
        impl = AsyncMock(spec=EngineImplementor)
        impl.engine_type.return_value = "bpmn"
        bridge = EngineBridge(impl)
        await bridge.execute(mock_instance, mock_definition)
        impl.execute_instance.assert_awaited_once_with(mock_instance, mock_definition)

    def test_engine_type_property(self):
        impl = MagicMock(spec=EngineImplementor)
        impl.engine_type.return_value = "bpmn"
        bridge = EngineBridge(impl)
        assert bridge.engine_type == "bpmn"
        assert bridge.implementor is impl

    @pytest.mark.asyncio
    async def test_validate_and_cancel_delegate(self):
        impl = AsyncMock(spec=EngineImplementor)
        impl.validate.return_value = []
        bridge = EngineBridge(impl)
        assert await bridge.validate(MagicMock()) == []
        assert await bridge.cancel("x") is None


class TestObservableEngineBridge:
    """ObservableEngineBridge fires lifecycle events."""

    @pytest.mark.asyncio
    async def test_execute_emits_started_and_completed(self, mock_instance, mock_definition):
        event_bus = EventBus()
        await event_bus.start()
        events = []

        async def collect(event):
            events.append(event.type)

        event_bus.subscribe([EventType.PROCESS_INSTANCE_STARTED, EventType.PROCESS_INSTANCE_COMPLETED], collect)

        impl = AsyncMock(spec=EngineImplementor)
        impl.engine_type.return_value = "bpmn"
        bridge = ObservableEngineBridge(impl, event_bus)
        await bridge.execute(mock_instance, mock_definition)

        await asyncio.sleep(0.05)
        assert EventType.PROCESS_INSTANCE_STARTED in events
        assert EventType.PROCESS_INSTANCE_COMPLETED in events
        await event_bus.stop()

    @pytest.mark.asyncio
    async def test_execute_failure_emits_terminated(self, mock_instance, mock_definition):
        event_bus = EventBus()
        await event_bus.start()
        events = []

        async def collect(event):
            events.append(event.type)

        event_bus.subscribe([EventType.PROCESS_INSTANCE_TERMINATED], collect)

        impl = AsyncMock(spec=EngineImplementor)
        impl.engine_type.return_value = "bpmn"
        impl.execute_instance.side_effect = RuntimeError("boom")
        bridge = ObservableEngineBridge(impl, event_bus)

        with pytest.raises(RuntimeError, match="boom"):
            await bridge.execute(mock_instance, mock_definition)

        await asyncio.sleep(0.05)
        assert EventType.PROCESS_INSTANCE_TERMINATED in events
        await event_bus.stop()


class TestLoggingEngineBridge:
    """LoggingEngineBridge wraps execution with structured logs."""

    @pytest.mark.asyncio
    async def test_execute_logs_success(self, mock_instance, mock_definition, caplog):
        import logging
        caplog.set_level(logging.INFO)
        impl = AsyncMock(spec=EngineImplementor)
        impl.engine_type.return_value = "bpmn"
        bridge = LoggingEngineBridge(impl)

        await bridge.execute(mock_instance, mock_definition)

        assert "Bridge executing instance" in caplog.text
        assert "Bridge completed instance" in caplog.text

    @pytest.mark.asyncio
    async def test_execute_logs_failure(self, mock_instance, mock_definition, caplog):
        import logging
        caplog.set_level(logging.INFO)
        impl = AsyncMock(spec=EngineImplementor)
        impl.engine_type.return_value = "bpmn"
        impl.execute_instance.side_effect = RuntimeError("boom")
        bridge = LoggingEngineBridge(impl)

        with pytest.raises(RuntimeError):
            await bridge.execute(mock_instance, mock_definition)

        assert "Bridge failed instance" in caplog.text


class TestCreateEngineBridge:
    """Factory selects correct bridge type."""

    def test_basic_bridge(self):
        impl = MagicMock(spec=EngineImplementor)
        bridge = create_engine_bridge(impl, enable_logging=False)
        assert isinstance(bridge, EngineBridge)

    def test_with_logging(self):
        impl = MagicMock(spec=EngineImplementor)
        bridge = create_engine_bridge(impl, enable_logging=True)
        assert isinstance(bridge, (LoggingEngineBridge, EngineBridge))

    def test_with_event_bus(self):
        impl = MagicMock(spec=EngineImplementor)
        bridge = create_engine_bridge(impl, event_bus=MagicMock(), enable_logging=False)
        assert isinstance(bridge, ObservableEngineBridge)


class TestEngineBridgeRegistry:
    """Registry wraps raw engines in bridge pattern."""

    def test_register_and_get(self):
        registry = EngineBridgeRegistry()
        raw = MagicMock(spec=['execute_instance', 'engine_type'])
        type(raw).__name__ = "BPMNEngine"
        bridge = registry.register("bpmn", raw)
        assert isinstance(bridge, ProcessEngine)
        assert registry.get("bpmn") is bridge

    def test_get_unknown(self):
        registry = EngineBridgeRegistry()
        assert registry.get("nonexistent") is None

    def test_all_types_and_bridges(self):
        registry = EngineBridgeRegistry()
        raw = MagicMock(spec=['execute_instance', 'engine_type'])
        type(raw).__name__ = "BPMNEngine"
        registry.register("bpmn", raw)
        assert registry.all_types() == ["bpmn"]
        assert len(registry.all_bridges()) == 1
