# Apache Kafka (aiokafka)
# مناسب برای: event streaming، replay، audit log، throughput بالا

# agents/buses/kafka_bus.py
import asyncio
import logging
from typing import Dict, Set
from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
from .base import MessageBus, HandlerType
from config.models.system.interaction_models import AgentMessage

logger = logging.getLogger(__name__)


class KafkaMessageBus(MessageBus):
    """Kafka-backed event streaming bus."""

    def __init__(self, bootstrap_servers: str, group_id: str = "agents") -> None:
        self._servers = bootstrap_servers
        self._group_id = group_id
        self._producer: AIOKafkaProducer | None = None
        self._consumers: Dict[str, asyncio.Task] = {}
        self._handlers: Dict[str, Set[HandlerType]] = {}

    async def start(self) -> None:
        self._producer = AIOKafkaProducer(bootstrap_servers=self._servers)
        await self._producer.start()

    async def stop(self) -> None:
        if self._producer:
            await self._producer.stop()
        for task in self._consumers.values():
            task.cancel()
        await asyncio.gather(*self._consumers.values(), return_exceptions=True)

    async def subscribe(self, recipient: str, handler: HandlerType) -> None:
        if recipient not in self._handlers:
            self._handlers[recipient] = set()
            self._consumers[recipient] = asyncio.create_task(self._consume(recipient))
        self._handlers[recipient].add(handler)

    async def unsubscribe(self, recipient: str, handler: HandlerType) -> None:
        if recipient not in self._handlers:
            return
        self._handlers[recipient].discard(handler)
        if not self._handlers[recipient]:
            del self._handlers[recipient]
            task = self._consumers.pop(recipient, None)
            if task:
                task.cancel()

    async def publish(self, message: AgentMessage) -> None:
        if not self._producer:
            raise RuntimeError("Call start() before publish()")
        await self._producer.send(topic=message.recipient, value=message.model_dump_json().encode())

    async def _consume(self, topic: str) -> None:
        consumer = AIOKafkaConsumer(
            topic, bootstrap_servers=self._servers, group_id=self._group_id, auto_offset_reset="earliest"
        )
        await consumer.start()
        try:
            async for record in consumer:
                handlers = list(self._handlers.get(topic, []))
                msg = AgentMessage.model_validate_json(record.value)
                await asyncio.gather(*[h(msg) for h in handlers], return_exceptions=True)
        except asyncio.CancelledError:
            pass
        finally:
            await consumer.stop()
