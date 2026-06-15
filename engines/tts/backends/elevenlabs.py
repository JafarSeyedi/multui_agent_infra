from __future__ import annotations

import os
from typing import Any

from ..engine import VoiceSpec
from ..plugin import TTSPlugin


class ElevenLabsTTSPlugin(TTSPlugin):
    def __init__(self, api_key: str = ""):
        self._api_key = api_key or os.environ.get("ELEVENLABS_API_KEY", "")

    def plugin_id(self) -> str:
        return "tts-elevenlabs"

    def activate(self, registry: Any) -> None:
        from engines.tts import TTSEngine
        engine = TTSEngine()
        engine.register_backend("elevenlabs", self)

    async def synthesize(self, text: str, voice: str, **options: Any) -> bytes:
        if not self._api_key:
            raise ValueError("ElevenLabs API key is required")
        import aiohttp
        async with aiohttp.ClientSession() as session:
            payload = {
                "text": text,
                "model_id": options.get("model_id", "eleven_monolingual_v1"),
                "voice_settings": {
                    "stability": options.get("stability", 0.5),
                    "similarity_boost": options.get("similarity_boost", 0.75),
                },
            }
            headers = {"xi-api-key": self._api_key, "Content-Type": "application/json"}
            async with session.post(
                f"https://api.elevenlabs.io/v1/text-to-speech/{voice}", json=payload, headers=headers
            ) as resp:
                if resp.status != 200:
                    raise RuntimeError(f"ElevenLabs API error: {resp.status}")
                return await resp.read()

    async def list_voices(self) -> list[VoiceSpec]:
        if not self._api_key:
            return []
        import aiohttp
        async with aiohttp.ClientSession() as session:
            headers = {"xi-api-key": self._api_key}
            async with session.get("https://api.elevenlabs.io/v1/voices", headers=headers) as resp:
                if resp.status != 200:
                    return []
                data = await resp.json()
                return [
                    VoiceSpec(id=v["voice_id"], name=v.get("name", v["voice_id"]))
                    for v in data.get("voices", [])
                ]
