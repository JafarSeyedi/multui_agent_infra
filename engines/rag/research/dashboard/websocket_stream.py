from __future__ import annotations

import asyncio
from typing import List

from fastapi import WebSocket

from .schema import TelemetryEventResponse


class WebSocketStream:
    def __init__(self, observability) -> None:
        self.obs = observability
        self.clients: set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.clients.add(websocket)

    def disconnect(self, websocket: WebSocket):
        self.clients.discard(websocket)

    def snapshot(self, limit: int = 20) -> List[TelemetryEventResponse]:
        events = self.obs.collector.get_recent(limit)
        return [
            TelemetryEventResponse(
                name=getattr(event, "name", "unknown"),
                payload=getattr(event, "payload", {}),
                timestamp=float(getattr(event, "timestamp", 0.0)),
            )
            for event in events
        ]

    async def stream_client(self, websocket: WebSocket, poll_interval: float = 1.0):
        while True:
            payload = [event.model_dump() for event in self.snapshot()]
            await websocket.send_json(payload)
            await asyncio.sleep(poll_interval)
