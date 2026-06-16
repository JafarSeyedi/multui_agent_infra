# engines/communication/models/parsers/communication_config_parser.py
from __future__ import annotations

from ..communication_models import ChannelConfig, ChannelType


def parse_channel_config(data: dict) -> ChannelConfig:
    return ChannelConfig(
        name=data["name"],
        channel_type=ChannelType(data.get("type", "pub_sub")),
        backend=data["backend"],
        settings=data.get("settings", {}),
    )
