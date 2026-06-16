# engines/communication/models/writers/communication_config_writer.py
from __future__ import annotations

from ..communication_models import ChannelConfig


def write_channel_config(config: ChannelConfig) -> dict:
    return {
        "name": config.name,
        "type": config.channel_type.value,
        "backend": config.backend,
        "settings": config.settings,
    }
