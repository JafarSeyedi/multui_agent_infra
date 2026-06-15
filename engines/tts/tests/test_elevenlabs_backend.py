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
