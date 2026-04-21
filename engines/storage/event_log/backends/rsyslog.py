from __future__ import annotations

import asyncio
import socket
from datetime import datetime
from typing import Dict, List, Optional

from ..base import LogStorage


class RSyslogStorage(LogStorage):
    """Best-effort UDP syslog backend with an in-memory lookup mirror."""

    def __init__(self, host: str = "localhost", port: int = 514) -> None:
        super().__init__()
        self.host = host
        self.port = port
        self._agent_logs: Dict[str, Dict] = {}
        self._events: Dict[str, Dict] = {}

    async def connect(self) -> None:
        self._connected = True

    async def disconnect(self) -> None:
        self._connected = False

    async def health(self) -> bool:
        return True

    async def _send(self, message: str) -> None:
        def _sync_send() -> None:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            try:
                sock.sendto(message.encode("utf-8", errors="ignore"), (self.host, self.port))
            finally:
                sock.close()

        await asyncio.to_thread(_sync_send)

    async def log_agent_execution(self, agent_name: str, record: Dict) -> None:
        timestamp = record.get("timestamp", datetime.utcnow().isoformat())
        key = f"exec:{agent_name}:{timestamp}"
        self._agent_logs[key] = dict(record)
        await self._send(f"agent_execution {key} {record}")

    async def list_agent_logs(self, agent_name: str) -> List[str]:
        prefix = f"exec:{agent_name}:"
        return [key for key in self._agent_logs if key.startswith(prefix)]

    async def get_agent_log(self, key: str) -> Optional[Dict]:
        return self._agent_logs.get(key)

    async def log_event(self, event_type: str, payload: Dict) -> None:
        key = f"event:{event_type}:{datetime.utcnow().isoformat()}"
        self._events[key] = dict(payload)
        await self._send(f"event {key} {payload}")

    async def list_events(self, event_type: Optional[str] = None) -> List[str]:
        prefix = f"event:{event_type}:" if event_type else "event:"
        return [key for key in self._events if key.startswith(prefix)]

    async def get_event(self, key: str) -> Optional[Dict]:
        return self._events.get(key)
