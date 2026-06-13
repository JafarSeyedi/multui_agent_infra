"""State pattern — orchestrates engine lifecycle state transitions."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .engine import OrchestrationEngine


class EngineState(ABC):
    """Base state for engine lifecycle."""

    @abstractmethod
    async def start(self, engine: OrchestrationEngine) -> None:
        ...

    @abstractmethod
    async def stop(self, engine: OrchestrationEngine) -> None:
        ...

    @abstractmethod
    async def pause(self, engine: OrchestrationEngine) -> None:
        ...

    @abstractmethod
    async def resume(self, engine: OrchestrationEngine) -> None:
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        ...


class StoppedState(EngineState):
    async def start(self, engine: OrchestrationEngine) -> None:
        engine._lifecycle_state = StartingState()

    async def stop(self, engine: OrchestrationEngine) -> None:
        pass

    async def pause(self, engine: OrchestrationEngine) -> None:
        raise RuntimeError("Cannot pause a stopped engine")

    async def resume(self, engine: OrchestrationEngine) -> None:
        raise RuntimeError("Cannot resume a stopped engine")

    @property
    def name(self) -> str:
        return "stopped"


class StartingState(EngineState):
    async def start(self, engine: OrchestrationEngine) -> None:
        pass

    async def stop(self, engine: OrchestrationEngine) -> None:
        engine._lifecycle_state = StoppedState()

    async def pause(self, engine: OrchestrationEngine) -> None:
        raise RuntimeError("Cannot pause an engine that is starting")

    async def resume(self, engine: OrchestrationEngine) -> None:
        raise RuntimeError("Cannot resume an engine that is starting")

    @property
    def name(self) -> str:
        return "starting"


class RunningState(EngineState):
    async def start(self, engine: OrchestrationEngine) -> None:
        pass

    async def stop(self, engine: OrchestrationEngine) -> None:
        engine._lifecycle_state = StoppingState()

    async def pause(self, engine: OrchestrationEngine) -> None:
        engine._lifecycle_state = PausedState()

    async def resume(self, engine: OrchestrationEngine) -> None:
        pass

    @property
    def name(self) -> str:
        return "running"


class PausedState(EngineState):
    async def start(self, engine: OrchestrationEngine) -> None:
        engine._lifecycle_state = RunningState()

    async def stop(self, engine: OrchestrationEngine) -> None:
        engine._lifecycle_state = StoppingState()

    async def pause(self, engine: OrchestrationEngine) -> None:
        pass

    async def resume(self, engine: OrchestrationEngine) -> None:
        engine._lifecycle_state = RunningState()

    @property
    def name(self) -> str:
        return "paused"


class StoppingState(EngineState):
    async def start(self, engine: OrchestrationEngine) -> None:
        pass

    async def stop(self, engine: OrchestrationEngine) -> None:
        pass

    async def pause(self, engine: OrchestrationEngine) -> None:
        raise RuntimeError("Cannot pause an engine that is stopping")

    async def resume(self, engine: OrchestrationEngine) -> None:
        raise RuntimeError("Cannot resume an engine that is stopping")

    @property
    def name(self) -> str:
        return "stopping"


class ErrorState(EngineState):
    async def start(self, engine: OrchestrationEngine) -> None:
        engine._lifecycle_state = StartingState()

    async def stop(self, engine: OrchestrationEngine) -> None:
        engine._lifecycle_state = StoppingState()

    async def pause(self, engine: OrchestrationEngine) -> None:
        pass

    async def resume(self, engine: OrchestrationEngine) -> None:
        pass

    @property
    def name(self) -> str:
        return "error"
