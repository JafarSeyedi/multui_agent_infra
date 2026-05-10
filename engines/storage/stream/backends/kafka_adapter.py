from __future__ import annotations

import json
from typing import Any

from ..base import StreamStorage


class KafkaStreamAdapter(StreamStorage):
    """Kafka-based stream storage using aiokafka when installed."""

    def __init__(self, bootstrap_servers: str, consumer_group: str | None = None) -> None:
        super().__init__()
        self.bootstrap_servers = bootstrap_servers
        self.consumer_group = consumer_group or "storage-stream-group"
        self._producer: Any | None = None

    async def connect(self) -> None:
        try:
            from aiokafka import AIOKafkaProducer # type: ignore
        except ImportError as exc:
            raise RuntimeError("aiokafka is required for KafkaStreamAdapter.") from exc

        self._producer = AIOKafkaProducer(bootstrap_servers=self.bootstrap_servers)

        if self._producer:
            await self._producer.start()
            self._connected = True

    async def disconnect(self) -> None:
        if self._producer is not None:
            await self._producer.stop()
        self._producer = None
        self._connected = False

    async def health(self) -> bool:
        return self._producer is not None

    async def publish(self, topic: str, message: dict[str, Any]) -> None:
        if self._producer is None:
            await self.connect()
        payload = json.dumps(message).encode("utf-8")

        assert self._producer is not None
        await self._producer.send_and_wait(topic, payload)

    async def consume(self, topic: str, group: str) -> list[dict[str, Any]]:
        try:
            from aiokafka import AIOKafkaConsumer # type: ignore
        except ImportError as exc:
            raise RuntimeError("aiokafka is required for KafkaStreamAdapter.") from exc

        consumer = AIOKafkaConsumer(
            topic,
            bootstrap_servers=self.bootstrap_servers,
            group_id=group or self.consumer_group,
            enable_auto_commit=False,
            auto_offset_reset="earliest",
        )
        await consumer.start()
        messages: list[dict[str, Any]] = []
        try:
            batch = await consumer.getmany(timeout_ms=1000, max_records=100)
            for records in batch.values():
                for record in records:
                    messages.append(json.loads(record.value.decode("utf-8")))
            await consumer.commit()
        finally:
            await consumer.stop()
        return messages
