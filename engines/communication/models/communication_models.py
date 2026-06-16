# engines/communication/models/communication_models.py
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class ChannelType(str, Enum):
    PUB_SUB = "pub_sub"
    REQUEST_REPLY = "request_reply"
    PRIORITY = "priority"
    STREAM = "stream"


class MessagePriority(int, Enum):
    LOW = 1
    NORMAL = 5
    HIGH = 8
    CRITICAL = 10


@dataclass
class ChannelMessage:
    id: str
    source: str
    type: str
    subject: str | None = None
    data: dict[str, Any] = field(default_factory=dict)
    data_schema: str | None = None
    content_type: str = "application/json"
    correlation_id: str | None = None
    priority: MessagePriority = MessagePriority.NORMAL
    timestamp: datetime = field(default_factory=datetime.utcnow)
    traceparent: str | None = None
    tenant_id: str | None = None
    headers: dict[str, str] = field(default_factory=dict)


@dataclass
class ChannelConfig:
    name: str
    channel_type: ChannelType
    backend: str
    settings: dict[str, Any] = field(default_factory=dict)


@dataclass
class Endpoint:
    host: str
    port: int
    transport: str
    metadata: dict[str, str] = field(default_factory=dict)
