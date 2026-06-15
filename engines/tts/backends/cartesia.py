from __future__ import annotations

import os
from typing import Any

from ..engine import VoiceSpec
from ..plugin import TTSPlugin


class CartesiaTTSPlugin(TTSPlugin):
    def __init__(self, api_key: str = ""):
        self._api_key = api_key or os.environ.get("CARTESIA_API_KEY", "")

    def plugin_id(self) -> str:
        return "tts-cartesia"

    def activate(self, registry: Any) -> None:
        from engines.tts import TTSEngine
        engine = TTSEngine()
        engine.register_backend("cartesia", self, set_default=True)

    async def synthesize(self, text: str, voice: str, **options: Any) -> bytes:
        if not self._api_key:
            raise ValueError("Cartesia API key is required")
        import aiohttp
        async with aiohttp.ClientSession() as session:
            payload = {
                "text": text,
                "voice": voice,
                "model_id": options.get("model_id", "sonic-2"),
                "output_format": options.get("output_format", "wav"),
            }
            headers = {"Authorization": f"Bearer {self._api_key}", "Content-Type": "application/json"}
            async with session.post("https://api.cartesia.ai/tts", json=payload, headers=headers) as resp:
                if resp.status != 200:
                    raise RuntimeError(f"Cartesia API error: {resp.status}")
                return await resp.read()

    async def list_voices(self) -> list[VoiceSpec]:
        if not self._api_key:
            return []
        import aiohttp
        async with aiohttp.ClientSession() as session:
            headers = {"Authorization": f"Bearer {self._api_key}"}
            async with session.get("https://api.cartesia.ai/voices", headers=headers) as resp:
                if resp.status != 200:
                    return []
                data = await resp.json()
                return [VoiceSpec(id=v["id"], name=v.get("name", v["id"])) for v in data]
