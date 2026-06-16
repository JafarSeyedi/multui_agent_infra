# engines/communication/tests/test_communication_models.py
from engines.communication.models.communication_models import ChannelMessage, ChannelConfig, ChannelType, Endpoint
from engines.communication.models.parsers.communication_config_parser import parse_channel_config
from engines.communication.models.writers.communication_config_writer import write_channel_config


def test_channel_message_defaults():
    msg = ChannelMessage(id="1", source="s", type="t")
    assert msg.priority.value == 5


def test_channel_config_roundtrip():
    config = ChannelConfig(name="test", channel_type=ChannelType.PUB_SUB, backend="in_memory")
    data = write_channel_config(config)
    parsed = parse_channel_config(data)
    assert parsed.name == config.name
    assert parsed.channel_type == config.channel_type
    assert parsed.backend == config.backend


def test_endpoint():
    ep = Endpoint(host="localhost", port=8080, transport="http")
    assert ep.host == "localhost"
    assert ep.port == 8080
