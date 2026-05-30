"""Kafka transport for command and event style service bindings."""

from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass
from typing import Any

from .base import AbstractTransport, TransportRequest, TransportResponse


@dataclass
class KafkaMessage:
    payload: bytes
    headers: dict[str, str]


class KafkaTransport(AbstractTransport):
    """Thin wrapper over :mod:`aiokafka` with response correlation support."""

    name = "KAFKA"

    def __init__(
        self,
        *,
        bootstrap_servers: str | list[str] = "localhost:9092",
        group_id: str | None = None,
        request_timeout_ms: int = 30000,
    ) -> None:
        self.bootstrap_servers = bootstrap_servers
        self.group_id = group_id or f"comm-{uuid.uuid4().hex[:8]}"
        self.request_timeout_ms = request_timeout_ms
        self._producer: Any | None = None
        self._consumer: Any | None = None

    async def _get_producer(self):
        if self._producer is not None:
            return self._producer
        try:
            from aiokafka import AIOKafkaProducer  # type: ignore[import-not-found,import-untyped]
        except Exception as exc:
            raise RuntimeError("aiokafka is required for KafkaTransport") from exc

        self._producer = AIOKafkaProducer(bootstrap_servers=self.bootstrap_servers)
        await self._producer.start()
        return self._producer

    async def _get_consumer(self, *, group_id: str, topics: list[str]):
        if self._consumer is not None:
            return self._consumer
        try:
            from aiokafka import AIOKafkaConsumer  # type: ignore[import-not-found,import-untyped]
        except Exception as exc:
            raise RuntimeError("aiokafka is required for KafkaTransport") from exc

        self._consumer = AIOKafkaConsumer(
            *topics,
            bootstrap_servers=self.bootstrap_servers,
            group_id=group_id,
            auto_offset_reset="earliest",
            enable_auto_commit=True,
        )
        await self._consumer.start()
        return self._consumer

    async def send(
        self,
        request: TransportRequest,
        *,
        payload_serializer=None,
        content_type: str | None = None,
    ) -> TransportResponse:
        body = _coerce_payload(request.body, payload_serializer)
        topic = request.params.get("topic") or request.url or request.params.get("queue")
        if not topic:
            raise ValueError("Kafka send requires request.url or params['topic'] as topic name")

        headers = dict(request.headers)
        key = request.params.get("key")
        partition = request.params.get("partition")
        reply_to = request.params.get("reply_to")
        timeout_ms = int(request.params.get("timeout_ms", self.request_timeout_ms))

        producer = await self._get_producer()

        correlation_id = str(uuid.uuid4())
        if reply_to:
            headers["x-correlation-id"] = correlation_id
            await producer.send_and_wait(topic, value=body, key=_coerce_key(key), partition=partition, headers=_encode_headers(headers))
            response = await self._consume_reply(topic=reply_to, correlation_id=correlation_id, timeout_ms=timeout_ms)
            return TransportResponse(
                status_code=200,
                headers={},
                body=response,
                elapsed_ms=0,
                transport="KAFKA",
                metadata={"topic": topic, "reply_to": reply_to, "correlation_id": correlation_id},
            )

        await producer.send_and_wait(topic, value=body, key=_coerce_key(key), partition=partition, headers=_encode_headers(headers))
        return TransportResponse(
            status_code=200,
            headers={},
            body=b"",
            elapsed_ms=0,
            transport="KAFKA",
            metadata={"topic": topic},
        )

    async def _consume_reply(self, topic: str, correlation_id: str, timeout_ms: int) -> bytes:
        consumer = await self._get_consumer(group_id=f"{self.group_id}-reply", topics=[topic])
        deadline = asyncio.get_running_loop().time() + timeout_ms / 1000
        while asyncio.get_running_loop().time() < deadline:
            timeout = max(0.05, deadline - asyncio.get_running_loop().time())
            try:
                records = await consumer.getmany(timeout_ms=int(timeout * 1000), max_records=4)
            except TypeError:
                # older aiokafka versions
                records = await consumer.getmany(timeout_ms=max(1, int(timeout * 1000)), max_records=4)

            for _, msgs in records.items():
                for msg in msgs:
                    msg_headers = dict(msg.headers or [])
                    msg_corr = msg_headers.get("x-correlation-id")
                    if _normalize_header(msg_corr) == correlation_id:
                        return msg.value
            await asyncio.sleep(0.01)
        raise TimeoutError(f"Timeout waiting for Kafka reply on topic '{topic}'")

    async def close(self) -> None:
        if self._producer is not None:
            await self._producer.stop()
            self._producer = None
        if self._consumer is not None:
            await self._consumer.stop()
            self._consumer = None


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


def _coerce_key(value: Any) -> bytes | None:
    if value is None:
        return None
    if isinstance(value, bytes):
        return value
    if isinstance(value, bytearray):
        return bytes(value)
    return str(value).encode("utf-8")


def _encode_headers(headers: dict[str, str]) -> list[tuple[bytes, bytes]]:
    return [(k.encode("utf-8"), str(v).encode("utf-8")) for k, v in headers.items()]


def _normalize_header(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="ignore")
    return str(value)
