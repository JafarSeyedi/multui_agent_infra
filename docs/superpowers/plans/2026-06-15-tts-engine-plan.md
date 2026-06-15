# TTS Engine Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `engines/tts/` — a text-to-speech engine with pluggable backends (Cartesia, ElevenLabs) and a unified `TTSEngine` interface for agent use.

**Architecture:** `TTSEngine` provides `synthesize()` and `list_voices()`. Backends implement `TTSPlugin(AgentPlugin)` and register with the engine. Agents call `TTSEngine.synthesize()` regardless of which backend is active.

**Tech Stack:** Python 3.12+, aiohttp, Cartesia REST API, ElevenLabs REST API

---

### Task 1: Create TTS engine core

**Files:**
- Create: `engines/tts/__init__.py`
- Create: `engines/tts/engine.py`
- Create: `engines/tts/plugin.py`

- [ ] **Step 1: Write failing test**

```python
# engines/tts/tests/test_engine.py
import pytest
from engines.tts.engine import TTSEngine, VoiceSpec


def test_voice_spec_defaults():
    vs = VoiceSpec(id="voice-1", name="Test Voice")
    assert vs.id == "voice-1"
    assert vs.name == "Test Voice"


@pytest.mark.asyncio
async def test_tts_engine_rejects_no_backend():
    engine = TTSEngine()
    with pytest.raises(RuntimeError, match="No TTS backend"):
        await engine.synthesize("hello", "default")
```

Run: `python3 -m pytest engines/tts/tests/test_engine.py -v`
Expected: FAIL

- [ ] **Step 2: Create engines/tts/ directory**

```bash
mkdir -p engines/tts/tests engines/tts/backends
```

- [ ] **Step 3: Create engine.py**

```python
"""Unified TTS engine with pluggable backends."""
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
    """Text-to-speech engine with pluggable backends."""

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
```

- [ ] **Step 4: Create plugin.py**

```python
"""TTS plugin ABC."""
from __future__ import annotations

from abc import ABC, abstractmethod

from engines.agent.plugins import AgentPlugin
from .engine import VoiceSpec


class TTSPlugin(AgentPlugin, ABC):
    """Base plugin for TTS backends."""

    def plugin_type(self) -> str:
        return "SKILL"

    @abstractmethod
    async def synthesize(self, text: str, voice: str, **options: Any) -> bytes:
        ...

    @abstractmethod
    async def list_voices(self) -> list[VoiceSpec]:
        ...


from typing import Any
TTSPlugin.__abstractmethods__  # ensure ABC works
```

- [ ] **Step 5: Create __init__.py**

```python
from .engine import TTSEngine, VoiceSpec
from .plugin import TTSPlugin

__all__ = ["TTSEngine", "TTSPlugin", "VoiceSpec"]
```

- [ ] **Step 6: Run test**

Run: `python3 -m pytest engines/tts/tests/test_engine.py -v`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add engines/tts/__init__.py engines/tts/engine.py engines/tts/plugin.py engines/tts/tests/test_engine.py
git commit -m "feat(tts): add TTSEngine core with pluggable backend interface"
```

---

### Task 2: Create Cartesia TTS backend

**Files:**
- Create: `engines/tts/backends/__init__.py`
- Create: `engines/tts/backends/cartesia.py`

- [ ] **Step 1: Write failing test**

```python
# engines/tts/tests/test_cartesia_backend.py
import pytest
from engines.tts.backends.cartesia import CartesiaTTSPlugin


def test_cartesia_plugin_identity():
    plugin = CartesiaTTSPlugin(api_key="test")
    assert plugin.plugin_id() == "tts-cartesia"
    assert plugin.plugin_type() == "SKILL"


@pytest.mark.asyncio
async def test_cartesia_synthesize_no_api_key():
    plugin = CartesiaTTSPlugin(api_key="")
    with pytest.raises(ValueError, match="API key"):
        await plugin.synthesize("hello", "default")
```

Run: `python3 -m pytest engines/tts/tests/test_cartesia_backend.py -v`
Expected: FAIL

- [ ] **Step 2: Create backends/__init__.py**

```python
from .cartesia import CartesiaTTSPlugin

__all__ = ["CartesiaTTSPlugin"]
```

- [ ] **Step 3: Create cartesia.py**

```python
"""Cartesia TTS backend."""
from __future__ import annotations

import os
from typing import Any

from ..engine import VoiceSpec
from ..plugin import TTSPlugin


class CartesiaTTSPlugin(TTSPlugin):
    """Text-to-speech via Cartesia API."""

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
```

- [ ] **Step 4: Run test**

Run: `python3 -m pytest engines/tts/tests/test_cartesia_backend.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add engines/tts/backends/cartesia.py
git commit -m "feat(tts): add Cartesia TTS backend"
```

---

### Task 3: Create ElevenLabs TTS backend

**Files:**
- Create: `engines/tts/backends/elevenlabs.py`

- [ ] **Step 1: Write failing test**

```python
# engines/tts/tests/test_elevenlabs_backend.py
import pytest
from engines.tts.backends.elevenlabs import ElevenLabsTTSPlugin


def test_elevenlabs_plugin_identity():
    plugin = ElevenLabsTTSPlugin(api_key="test")
    assert plugin.plugin_id() == "tts-elevenlabs"
    assert plugin.plugin_type() == "SKILL"


@pytest.mark.asyncio
async def test_elevenlabs_synthesize_no_api_key():
    plugin = ElevenLabsTTSPlugin(api_key="")
    with pytest.raises(ValueError, match="API key"):
        await plugin.synthesize("hello", "default")
```

Run: `python3 -m pytest engines/tts/tests/test_elevenlabs_backend.py -v`
Expected: FAIL

- [ ] **Step 2: Create elevenlabs.py**

```python
"""ElevenLabs TTS backend."""
from __future__ import annotations

import os
from typing import Any

from ..engine import VoiceSpec
from ..plugin import TTSPlugin


class ElevenLabsTTSPlugin(TTSPlugin):
    """Text-to-speech via ElevenLabs API."""

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
```

- [ ] **Step 3: Update backends/__init__.py**

```python
from .cartesia import CartesiaTTSPlugin
from .elevenlabs import ElevenLabsTTSPlugin

__all__ = ["CartesiaTTSPlugin", "ElevenLabsTTSPlugin"]
```

- [ ] **Step 4: Run test**

Run: `python3 -m pytest engines/tts/tests/test_elevenlabs_backend.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add engines/tts/backends/elevenlabs.py
git commit -m "feat(tts): add ElevenLabs TTS backend"
```

---

### Task 4: Final verification

- [ ] **Step 1: Run all TTS tests**

```bash
python3 -m pytest engines/tts/tests/ -v
```

Expected: All pass.

- [ ] **Step 2: Run mypy**

```bash
python3 -m mypy engines/tts/ --no-error-summary
```

Expected: No errors.

- [ ] **Step 3: Verify integration**

```bash
python3 -c "
from engines.tts import TTSEngine, TTSPlugin, VoiceSpec
engine = TTSEngine()
print(f'TTSEngine created: {engine}')
print('All TTS imports OK')
"
```

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "feat(tts): complete TTS engine with Cartesia and ElevenLabs backends"
```
