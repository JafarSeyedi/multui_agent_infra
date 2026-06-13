"""Bridge pattern: separates ProcessEngine abstraction from concrete engine implementations.

Allows the abstraction (execution, validation, lifecycle) to vary independently
from the implementation (how each engine type actually executes instances).
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any

from .event_bus import Event, EventBus, EventType
from .instance import ProcessInstance
from ..core.engine import EngineConfig, ProcessDefinition

logger = logging.getLogger(__name__)


# ── Implementor hierarchy ──────────────────────────────────────────


class EngineImplementor(ABC):
    """Implementor interface for process engines.

    Each concrete implementor wraps one engine type (BPMN, MultiAgent, etc.)
    and knows only how to execute a single instance — no lifecycle or
    cross-cutting concerns.
    """

    def __init__(self, raw_engine: Any = None) -> None:
        self._raw = raw_engine

    @abstractmethod
    async def execute_instance(self, instance: ProcessInstance, definition: ProcessDefinition) -> None:
        ...

    @abstractmethod
    def engine_type(self) -> str:
        ...

    async def validate(self, definition: ProcessDefinition) -> list[str]:
        return []

    async def cancel(self, instance_id: str) -> None:
        pass

    async def get_status(self, instance: ProcessInstance) -> str | None:
        return None


class BPMNImplementor(EngineImplementor):
    """Wraps a BPMNEngine as an EngineImplementor."""

    def __init__(self, raw_engine: Any) -> None:
        self._raw = raw_engine

    async def execute_instance(self, instance: ProcessInstance, definition: ProcessDefinition) -> None:
        await self._raw.execute_instance(instance, definition)

    def engine_type(self) -> str:
        return "bpmn"


class MultiAgentImplementor(EngineImplementor):
    """Wraps a MultiAgentEngine as an EngineImplementor."""

    def __init__(self, raw_engine: Any) -> None:
        self._raw = raw_engine

    async def execute_instance(self, instance: ProcessInstance, definition: ProcessDefinition) -> None:
        await self._raw.execute_instance(instance, definition)

    def engine_type(self) -> str:
        return "multi_agent"


class StateMachineImplementor(EngineImplementor):
    """Wraps a StateMachineEngine as an EngineImplementor."""

    def __init__(self, raw_engine: Any) -> None:
        self._raw = raw_engine

    async def execute_instance(self, instance: ProcessInstance, definition: ProcessDefinition) -> None:
        await self._raw.execute_instance(instance, definition)

    def engine_type(self) -> str:
        return "state_machine"


class CMMNImplementor(EngineImplementor):
    """Wraps a CMMNEngine as an EngineImplementor."""

    def __init__(self, raw_engine: Any) -> None:
        self._raw = raw_engine

    async def execute_instance(self, instance: ProcessInstance, definition: ProcessDefinition) -> None:
        await self._raw.execute_instance(instance, definition)

    def engine_type(self) -> str:
        return "cmmn"


class DMNImplementor(EngineImplementor):
    """Wraps a DMNEngine as an EngineImplementor."""

    def __init__(self, raw_engine: Any) -> None:
        self._raw = raw_engine

    async def execute_instance(self, instance: ProcessInstance, definition: ProcessDefinition) -> None:
        await self._raw.execute_instance(instance, definition)

    def engine_type(self) -> str:
        return "dmn"


class CEPImplementor(EngineImplementor):
    """Wraps a CEPEngine as an EngineImplementor."""

    def __init__(self, raw_engine: Any) -> None:
        self._raw = raw_engine

    async def execute_instance(self, instance: ProcessInstance, definition: ProcessDefinition) -> None:
        await self._raw.execute_instance(instance, definition)

    def engine_type(self) -> str:
        return "cep"


class BAMImplementor(EngineImplementor):
    """Wraps a BamEngine as an EngineImplementor."""

    def __init__(self, raw_engine: Any) -> None:
        self._raw = raw_engine

    async def execute_instance(self, instance: ProcessInstance, definition: ProcessDefinition) -> None:
        await self._raw.execute_instance(instance, definition)

    def engine_type(self) -> str:
        return "bam"


# ── Abstraction hierarchy ─────────────────────────────────────────


class ProcessEngine(ABC):
    """Abstraction for process engine operations.

    High-level interface that clients interact with. Delegates
    to an EngineImplementor for engine-specific logic.
    """

    def __init__(self, implementor: EngineImplementor) -> None:
        self._impl = implementor

    @abstractmethod
    async def execute(self, instance: ProcessInstance, definition: ProcessDefinition) -> Any:
        ...

    async def validate(self, definition: ProcessDefinition) -> list[str]:
        return await self._impl.validate(definition)

    async def cancel(self, instance_id: str) -> None:
        await self._impl.cancel(instance_id)

    async def get_status(self, instance: ProcessInstance) -> str | None:
        return await self._impl.get_status(instance)

    @property
    def implementor(self) -> EngineImplementor:
        return self._impl

    @property
    def engine_type(self) -> str:
        return self._impl.engine_type()


class EngineBridge(ProcessEngine):
    """Standard bridge: delegates directly to the implementor.

    This is the simplest refinement — it adds no cross-cutting concerns.
    """

    async def execute(self, instance: ProcessInstance, definition: ProcessDefinition) -> Any:
        return await self._impl.execute_instance(instance, definition)


class ObservableEngineBridge(EngineBridge):
    """Refined abstraction that adds event publishing around execution.

    Fires lifecycle events (started / completed / terminated) so that
    subscribers can react without the implementor knowing about events.
    """

    def __init__(self, implementor: EngineImplementor, event_bus: EventBus) -> None:
        super().__init__(implementor)
        self._event_bus = event_bus

    async def execute(self, instance: ProcessInstance, definition: ProcessDefinition) -> Any:
        engine_type = self._impl.engine_type()
        await self._event_bus.publish(
            Event(
                type=EventType.PROCESS_INSTANCE_STARTED,
                data={"instance_id": instance.id, "definition_key": definition.key, "engine_type": engine_type},
            )
        )
        try:
            await self._impl.execute_instance(instance, definition)
        except Exception as exc:
            await self._event_bus.publish(
                Event(
                    type=EventType.PROCESS_INSTANCE_TERMINATED,
                    data={
                        "instance_id": instance.id,
                        "definition_key": definition.key,
                        "engine_type": engine_type,
                        "error": str(exc),
                    },
                )
            )
            raise
        await self._event_bus.publish(
            Event(
                type=EventType.PROCESS_INSTANCE_COMPLETED,
                data={"instance_id": instance.id, "definition_key": definition.key, "engine_type": engine_type},
            )
        )


class LoggingEngineBridge(EngineBridge):
    """Refined abstraction that adds structured logging around execution."""

    async def execute(self, instance: ProcessInstance, definition: ProcessDefinition) -> Any:
        engine_type = self._impl.engine_type()
        logger.info("Bridge executing instance %s on %s engine", instance.id, engine_type)
        try:
            await self._impl.execute_instance(instance, definition)
        except Exception as exc:
            logger.exception("Bridge failed instance %s on %s engine: %s", instance.id, engine_type, exc)
            raise
        logger.info("Bridge completed instance %s on %s engine", instance.id, engine_type)


# ── Factory helpers ───────────────────────────────────────────────


def create_engine_bridge(
    implementor: EngineImplementor,
    event_bus: EventBus | None = None,
    enable_logging: bool = True,
) -> ProcessEngine:
    """Create an appropriate bridge for the given implementor.

    Wraps in ObservableEngineBridge when an event_bus is provided,
    and LoggingEngineBridge when enable_logging is True.
    """
    bridge: ProcessEngine
    if enable_logging and event_bus is not None:
        bridge = ObservableEngineBridge(implementor, event_bus)
    elif enable_logging:
        bridge = LoggingEngineBridge(implementor)
    elif event_bus is not None:
        bridge = ObservableEngineBridge(implementor, event_bus)
    else:
        bridge = EngineBridge(implementor)
    return bridge

# ── Bridge registry ───────────────────────────────────────────────


class EngineBridgeRegistry:
    """Registry that maps definition types to bridged ProcessEngines.

    Wraps raw engine handlers in the Bridge pattern so that downstream
    consumers (e.g. InstanceService) interact only with ProcessEngine.
    """

    def __init__(self, event_bus: EventBus | None = None, config: EngineConfig | None = None) -> None:
        self._bridges: dict[str, ProcessEngine] = {}
        self._event_bus = event_bus
        self._config = config or EngineConfig()

    def register(self, definition_type: str, raw_engine: Any) -> ProcessEngine:
        implementor = _implementor_for(raw_engine)
        bridge = create_engine_bridge(
            implementor,
            event_bus=self._event_bus,
            enable_logging=True,
        )
        self._bridges[definition_type] = bridge
        return bridge

    def get(self, definition_type: str) -> ProcessEngine | None:
        return self._bridges.get(definition_type)

    def all_types(self) -> list[str]:
        return list(self._bridges.keys())

    def all_bridges(self) -> list[ProcessEngine]:
        return list(self._bridges.values())


def _implementor_for(raw_engine: Any) -> EngineImplementor:
    """Auto-detect and create an implementor for a raw engine instance."""
    engine_cls_name = type(raw_engine).__name__
    mapping: dict[str, type[EngineImplementor]] = {
        "BPMNEngine": BPMNImplementor,
        "MultiAgentEngine": MultiAgentImplementor,
        "StateMachineEngine": StateMachineImplementor,
        "CMMNEngine": CMMNImplementor,
        "DMNEngine": DMNImplementor,
        "CEPEngine": CEPImplementor,
        "BamEngine": BAMImplementor,
    }
    impl_cls = mapping.get(engine_cls_name)
    if impl_cls is None:
        logger.warning("Unknown engine class %s, using generic implementor", engine_cls_name)
        return _GenericImplementor(raw_engine)
    return impl_cls(raw_engine)


class _GenericImplementor(EngineImplementor):
    """Fallback implementor for unrecognized engine classes."""

    def __init__(self, raw_engine: Any) -> None:
        self._raw = raw_engine

    async def execute_instance(self, instance: ProcessInstance, definition: ProcessDefinition) -> None:
        execute = getattr(self._raw, "execute_instance", None)
        if execute is None:
            raise TypeError(f"Engine {type(self._raw).__name__} lacks execute_instance")
        await execute(instance, definition)

    def engine_type(self) -> str:
        return getattr(type(self._raw), "__name__", "unknown").lower().replace("engine", "")
