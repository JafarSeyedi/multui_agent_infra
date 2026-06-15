"""Protocol abstraction layer for agent-to-agent communication.

Supports in-process, A2A, and FIPA protocol backends.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class AgentMessage:
    """Universal agent message envelope."""
    sender: str
    recipient: str
    payload: Any = None
    message_id: str = ""
    message_type: str = "request"
    correlation_id: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)


class AgentProtocol(ABC):
    """Abstract protocol for agent-to-agent communication."""

    @abstractmethod
    async def connect(self) -> None:
        """Establish the protocol connection."""

    @abstractmethod
    async def send_message(self, message: AgentMessage) -> AgentMessage | None:
        """Send a message and optionally return a response."""

    @abstractmethod
    async def receive_message(self, timeout: float | None = None) -> AgentMessage | None:
        """Receive a message (blocking with optional timeout)."""

    @abstractmethod
    async def disconnect(self) -> None:
        """Tear down the protocol connection."""


class InMemoryProtocol(AgentProtocol):
    """Direct in-process message passing (default protocol)."""

    def __init__(self):
        self._connected = False

    async def connect(self) -> None:
        self._connected = True

    async def send_message(self, message: AgentMessage) -> AgentMessage | None:
        from .agent_mediator import AgentMediator
        mediator = AgentMediator()
        result = await mediator.send(message.sender, message.recipient, message.payload)
        if result is not None:
            return AgentMessage(
                sender=message.recipient,
                recipient=message.sender,
                payload=result,
                correlation_id=message.message_id,
            )
        return None

    async def receive_message(self, timeout: float | None = None) -> AgentMessage | None:
        return None

    async def disconnect(self) -> None:
        self._connected = False


class A2AProtocol(AgentProtocol):
    """Google A2A (Agent-to-Agent) protocol adapter.

    Communicates with remote agents via HTTP+JSON following the A2A specification.
    """

    def __init__(self, base_url: str = "", api_key: str = ""):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self._session: Any = None

    async def connect(self) -> None:
        import aiohttp
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        self._session = aiohttp.ClientSession(headers=headers)

    async def send_message(self, message: AgentMessage) -> AgentMessage | None:
        if self._session is None:
            raise RuntimeError("A2AProtocol not connected. Call connect() first.")
        payload = {
            "jsonrpc": "2.0",
            "method": "agents.send",
            "params": {
                "sender": message.sender,
                "message": message.payload,
                "session_id": message.correlation_id,
            },
            "id": message.message_id or "1",
        }
        async with self._session.post(f"{self.base_url}/rpc", json=payload) as resp:
            data = await resp.json()
        result = data.get("result", {})
        return AgentMessage(
            sender=message.recipient,
            recipient=message.sender,
            payload=result,
            correlation_id=message.message_id,
        )

    async def receive_message(self, timeout: float | None = None) -> AgentMessage | None:
        return None

    async def disconnect(self) -> None:
        if self._session:
            await self._session.close()
            self._session = None


class FIPAProtocol(AgentProtocol):
    """FIPA ACL protocol adapter.

    Wraps the existing FIPA protocol handler from the orchestration engine.
    """

    def __init__(self, protocol_handler=None):
        self._handler = protocol_handler
        self._connected = False

    async def connect(self) -> None:
        self._connected = True

    async def send_message(self, message: AgentMessage) -> AgentMessage | None:
        if self._handler is None:
            inmem = InMemoryProtocol()
            return await inmem.send_message(message)

        protocol = {
            "protocol_id": message.message_id or "auto",
            "protocol_type": "FIPA_REQUEST",
            "participants": [message.sender, message.recipient],
        }
        await self._handler.execute(protocol, None)
        return AgentMessage(
            sender=message.recipient,
            recipient=message.sender,
            payload={"status": "sent_via_fipa"},
            correlation_id=message.message_id,
        )

    async def receive_message(self, timeout: float | None = None) -> AgentMessage | None:
        return None

    async def disconnect(self) -> None:
        self._connected = False
