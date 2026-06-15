from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from engines.agent.plugins import AgentPlugin
from .engine import VoiceSpec


class TTSPlugin(AgentPlugin, ABC):
    def plugin_type(self) -> str:
        return "SKILL"

    @abstractmethod
    async def synthesize(self, text: str, voice: str, **options: Any) -> bytes:
        ...

    @abstractmethod
    async def list_voices(self) -> list[VoiceSpec]:
        ...
