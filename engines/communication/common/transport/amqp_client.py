"""AMQP transport support built on :mod:`aio_pika`."""

from __future__ import annotations

import asyncio
import uuid
from typing import Any

from .base import AbstractTransport, TransportRequest, TransportResponse


class AMQPTransport(AbstractTransport):
    """AMQP transport for queues, exchanges and request/reply interactions."""

    name = "AMQP"

    def __init__(
        self,
        *,
        url: str = "amqp://guest:guest@localhost:5672/",
        request_timeout_ms: int = 30000,
        exchange_name: str = "",
        max_retries: int = 0,
    ) -> None:
        self.url = url
        self.request_timeout_ms = request_timeout_ms
        self.exchange_name = exchange_name
        self.max_retries = max_retries
        self._connection = None
        self._channel = None

    async def _ensure_channel(self):
        if self._channel is not None:
            return self._channel

        try:
            import aio_pika  # type: ignore[import-not-found]
        except Exception as exc:
            raise RuntimeError("aio-pika is required for AMQPTransport") from exc

        connection = await aio_pika.connect_robust(self.url)
        channel = await connection.channel()
        if self.exchange_name:
            await channel.declare_exchange(self.exchange_name, type=aio_pika.ExchangeType.TOPIC, durable=True)
        self._connection = connection
        self._channel = channel
        return channel

    async def send(
        self,
        request: TransportRequest,
        *,
        payload_serializer=None,
        content_type: str | None = None,
    ) -> TransportResponse:
        body = _coerce_payload(request.body, payload_serializer)
        params = dict(request.params)
        topic = params.get("exchange") or params.get("topic") or request.url
        queue = params.get("queue")
        routing_key = params.get("routing_key") or topic or ""
        reply_to = params.get("reply_to")

        key = params.get("correlation_id") or str(uuid.uuid4())
        timeout_ms = int(params.get("timeout_ms", self.request_timeout_ms))

        channel = await self._ensure_channel()
        try:
            import aio_pika  # type: ignore[import-not-found]
            exchange = await self._get_exchange(channel)
            message = aio_pika.Message(
                body=body,
                content_type=content_type,
                correlation_id=key,
                headers=dict(request.headers),
            )
            if reply_to:
                message.reply_to = reply_to
            await exchange.publish(message, routing_key=routing_key)

            if queue is not None:
                await _ensure_queue(channel, queue)

            if not reply_to:
                return TransportResponse(
                    status_code=200,
                    headers={},
                    body=b"",
                    elapsed_ms=0,
                    transport="AMQP",
                    metadata={"exchange": self.exchange_name or "default", "routing_key": routing_key},
                )

            response_body = await self._wait_reply(channel, reply_to, key, timeout_ms)
            return TransportResponse(
                status_code=200,
                headers={},
                body=response_body,
                elapsed_ms=0,
                transport="AMQP",
                metadata={"routing_key": routing_key, "reply_to": reply_to, "correlation_id": key},
            )
        except Exception:
            if self.max_retries <= 0:
                raise
            # simple retry with short backoff
            self.max_retries -= 1
            await asyncio.sleep(0.1)
            return await self.send(request, payload_serializer=payload_serializer, content_type=content_type)

    async def _get_exchange(self, channel):
        if self.exchange_name:
            return await channel.get_exchange(self.exchange_name)
        return channel.default_exchange

    async def _wait_reply(self, channel, reply_queue: str, correlation_id: str, timeout_ms: int) -> bytes:
        import aio_pika  # type: ignore[import-not-found]

        queue = await channel.declare_queue(reply_queue, durable=False, auto_delete=True)
        result: asyncio.Future[bytes] = asyncio.get_running_loop().create_future()

        async def on_message(message: aio_pika.IncomingMessage) -> None:
            async with message.process(ignore_processed=True):
                if message.correlation_id == correlation_id:
                    if not result.done():
                        result.set_result(message.body)
                else:
                    await queue.put(message)

        await queue.consume(on_message, no_ack=False)
        try:
            return await asyncio.wait_for(result, timeout_ms / 1000)
        except asyncio.TimeoutError as exc:
            raise TimeoutError(f"Timeout waiting for AMQP response on queue '{reply_queue}'") from exc

    async def close(self) -> None:
        if self._channel is not None:
            try:
                await self._channel.close()
            except Exception:
                pass
            self._channel = None
        if self._connection is not None:
            try:
                await self._connection.close()
            except Exception:
                pass
            self._connection = None


def _coerce_payload(body: Any, serializer: Any) -> bytes:
    if serializer is not None and body is not None and not isinstance(body, (bytes, bytearray)):
        return serializer(body)
    if body is None:
        return b""
    if isinstance(body, bytes):
        return body
    if isinstance(body, bytearray):
        return bytes(body)
    if isinstance(body, str):
        return body.encode("utf-8")
    return str(body).encode("utf-8")


async def _ensure_queue(channel, queue_name: str):
    try:
        await channel.declare_queue(queue_name, durable=False, auto_delete=True)
    except Exception:
        return
