"""Primary orchestration API facade around core engine control."""

from __future__ import annotations

from dataclasses import dataclass

from ..core.engine import OrchestrationEngine


@dataclass(frozen=True)
class EngineAPI:
    engine: OrchestrationEngine

    async def start(self) -> None:
        await self.engine.start()

    async def stop(self) -> None:
        await self.engine.stop()

    async def pause(self) -> None:
        await self.engine.pause()

    async def resume(self) -> None:
        await self.engine.resume()

    def is_running(self) -> bool:
        return self.engine.state.name == "RUNNING"
