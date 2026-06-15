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
