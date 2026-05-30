"""Serialize SSDM `MessageBinding` models into simple dict payloads."""

from __future__ import annotations

from typing import Any

from ...document.models.ssdm_models import MessageBinding


def write_message_binding(binding: MessageBinding) -> dict[str, Any]:
    return {
        "transport": binding.transport.value,
        "topic": binding.topic,
        "queue": binding.queue,
        "message_format": binding.message_format.value,
        "subscription_type": binding.subscription_type.value,
        "group_id": binding.group_id,
        "routing_key": binding.routing_key,
        "reply_to": binding.reply_to,
    }
