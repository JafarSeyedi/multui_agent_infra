from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class VoiceSpec:
    id: str
    name: str
    gender: str = ""
    language: str = "en"
    description: str = ""


class TTSEngine:
    def __init__(self):
        self._backends: dict[str, Any] = {}
        self._default_backend: str = ""

    def register_backend(self, name: str, backend: Any, set_default: bool = False) -> None:
        self._backends[name] = backend
        if set_default or not self._default_backend:
            self._default_backend = name

    async def synthesize(self, text: str, voice: str, backend: str = "", **options: Any) -> bytes:
        backend_name = backend or self._default_backend
        if not backend_name or backend_name not in self._backends:
            raise RuntimeError(f"No TTS backend available (tried: '{backend_name}')")
        return await self._backends[backend_name].synthesize(text, voice, **options)

    async def list_voices(self, backend: str = "") -> list[VoiceSpec]:
        backend_name = backend or self._default_backend
        if not backend_name or backend_name not in self._backends:
            return []
        return await self._backends[backend_name].list_voices()
