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
