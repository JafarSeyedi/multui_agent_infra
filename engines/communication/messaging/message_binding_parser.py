"""Parse message-binding payloads into SSDM `MessageBinding` models."""

from __future__ import annotations

from typing import Any

from ...document.models.ssdm_models import MessageBinding, MessageFormat, SubscriptionType, Transport


def parse_message_binding(raw: dict[str, Any]) -> MessageBinding:
    transport_raw = raw.get("transport", Transport.AMQP.value)
    try:
        transport = transport_raw if isinstance(transport_raw, Transport) else Transport(str(transport_raw))
    except ValueError:
        transport = Transport.AMQP

    format_raw = raw.get("message_format", MessageFormat.JSON.value)
    try:
        message_format = format_raw if isinstance(format_raw, MessageFormat) else MessageFormat(str(format_raw).upper())
    except ValueError:
        message_format = MessageFormat.JSON

    subscription_raw = raw.get("subscription_type", SubscriptionType.PUB_SUB.value)
    try:
        subscription_type = (
            subscription_raw
            if isinstance(subscription_raw, SubscriptionType)
            else SubscriptionType(str(subscription_raw))
        )
    except ValueError:
        subscription_type = SubscriptionType.PUB_SUB

    return MessageBinding(
        transport=transport,
        topic=raw.get("topic"),
        queue=raw.get("queue"),
        message_format=message_format,
        subscription_type=subscription_type,
        group_id=raw.get("group_id"),
        routing_key=raw.get("routing_key"),
        reply_to=raw.get("reply_to"),
    )
