"""Collaboration and message-flow handling for BPMN collaborations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class MessageFlow:
    source: str
    target: str
    payload: dict[str, Any]


class CollaborationHandler:
    def route(self, message_flow: MessageFlow) -> str:
        return f"{message_flow.source}->{message_flow.target}"

    def validate(self, message_flow: MessageFlow) -> bool:
        return bool(message_flow.source and message_flow.target)
