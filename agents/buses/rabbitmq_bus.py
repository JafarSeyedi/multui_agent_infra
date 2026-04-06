# RabbitMQ (aio-pika)
# مناسب برای: durability، routing پیچیده، dead-letter، retry

# agents/buses/rabbitmq_bus.py
import logging
from typing import Dict, List
import aio_pika
from aio_pika import Message, DeliveryMode
from .base import MessageBus, HandlerType
from config.models.system.interaction_models import AgentMessage

logger = logging.getLogger(__name__)


class RabbitMQMessageBus(MessageBus):
    """Durable RabbitMQ-backed bus."""

    def __init__(self, connection: aio_pika.Connection, exchange_name: str = "agents") -> None:
        self._conn = connection
        self._exchange_name = exchange_name
        self._channel: aio_pika.Channel | None = None
        self._exchange: aio_pika.Exchange | None = None
        self._consumers: Dict[str, List[aio_pika.Queue]] = {}

    async def start(self) -> None:
        self._channel = await self._conn.channel()
        self._exchange = await self._channel.declare_exchange(
            self._exchange_name, aio_pika.ExchangeType.DIRECT, durable=True
        )

    async def stop(self) -> None:
        if self._channel:
            await self._channel.close()

    async def subscribe(self, recipient: str, handler: HandlerType) -> None:
        if not self._channel or not self._exchange:
            raise RuntimeError("Call start() before subscribe()")

        queue = await self._channel.declare_queue(f"{recipient}_{id(handler)}", durable=True)
        await queue.bind(self._exchange, routing_key=recipient)

        async def on_message(raw: aio_pika.IncomingMessage):
            async with raw.process(requeue_on_timeout=True):
                try:
                    msg = AgentMessage.model_validate_json(raw.body)
                    await handler(msg)
                except Exception as e:
                    logger.error("RabbitMQ handler error: %r", e)

        await queue.consume(on_message)
        self._consumers.setdefault(recipient, []).append(queue)

    async def unsubscribe(self, recipient: str, handler: HandlerType) -> None:
        queues = self._consumers.get(recipient, [])
        for queue in queues:
            if queue.name == f"{recipient}_{id(handler)}":
                await queue.delete()
                queues.remove(queue)
                break

    async def publish(self, message: AgentMessage) -> None:
        if not self._exchange:
            raise RuntimeError("Call start() before publish()")
        await self._exchange.publish(
            Message(body=message.model_dump_json().encode(), delivery_mode=DeliveryMode.PERSISTENT),
            routing_key=message.recipient,
        )
