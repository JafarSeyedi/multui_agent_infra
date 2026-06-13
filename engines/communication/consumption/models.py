"""Shared models for service invocation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ...document.models.ssdm_models import Transport
from ..common.transport.base import TransportRequest, TransportResponse


@dataclass
class InvocationResult:
    operation_id: str
    transport: Transport
    request: TransportRequest | None
    response: TransportResponse | None
    payload: Any
    metadata: dict[str, Any] = field(default_factory=dict)
