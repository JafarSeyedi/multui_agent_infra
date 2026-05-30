"""Message routing for inter-agent communication."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Message:
    sender: str
    recipient: str
    topic: str
    payload: dict


class MessageRouter:
    def __init__(self) -> None:
        self._messages: list[Message] = []

    def route(self, message: Message) -> Message:
        self._messages.append(message)
        return message

    def inbox(self, recipient: str) -> list[Message]:
        return [msg for msg in self._messages if msg.recipient == recipient]
