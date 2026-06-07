"""Event persistence repository used for audit and replay."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from .runtime_records import EVENT_RECORD
from .repository import PersistentRuntimeRepository


class EventRepository(PersistentRuntimeRepository):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(
            record_type=EVENT_RECORD,
            key_prefix="orchestration:events:",
            measurement="orchestration_events",
            **kwargs,
        )

    def append(self, event: dict[str, Any]) -> None:
        payload = dict(event)
        payload.setdefault("recorded_at", datetime.utcnow().isoformat())
        key = payload.get("event_id") or f"{payload.get('type', 'event')}:{payload['recorded_at']}"
        super().save(str(key), payload)

    async def append_persisted(self, event: dict[str, Any]) -> dict[str, Any]:
        payload = dict(event)
        payload.setdefault("recorded_at", datetime.utcnow().isoformat())
        payload.setdefault("event_type", payload.get("type", "event"))
        key = str(payload.get("event_id") or f"{payload.get('event_type', 'event')}:{payload['recorded_at']}")
        return await self.save_persisted(key, payload)

    def by_correlation(self, correlation_id: str) -> list[dict[str, Any]]:
        """Get events by correlation ID (basic correlation support)."""
        return self.list(predicate=lambda row: row.get("correlation_id") == correlation_id)

    def by_correlation_osdm(self, correlation_key: dict[str, Any]) -> list[dict[str, Any]]:
        """Get events by OSDM correlation key (advanced correlation support).
        
        This method supports OSDM-style correlation where events are correlated
        based on matching property values in the payload, similar to OSDM
        CorrelationRule evaluation.
        """
        def _matches_osdm_correlation(event: dict[str, Any]) -> bool:
            # Check if event has the correlation_id field (basic support)
            if event.get("correlation_id"):
                # In a full OSDM implementation, we would check if the correlation_id
                # matches the OSDM correlation key. For now, we'll do a simple string match
                # if the correlation_key is a simple string, or check payload properties
                # if it's a more complex structure.
                if isinstance(correlation_key, str):
                    return event.get("correlation_id") == correlation_key
                elif isinstance(correlation_key, dict):
                    # Check if all key-value pairs in correlation_key match the event payload
                    payload = event.get("payload", {})
                    for key, expected_value in correlation_key.items():
                        if payload.get(key) != expected_value:
                            return False
                    return True
            return False
            
        return self.list(predicate=_matches_osdm_correlation)

    def by_instance_and_time_ordered(self, instance_id: str) -> list[dict[str, Any]]:
        """Get events for a specific instance, ordered by timestamp (oldest first)."""
        events = self.list(predicate=lambda row: row.get("instance_id") == instance_id)
        # Sort by created_at timestamp
        return sorted(events, key=lambda x: x.get("created_at", ""))

    def by_instance_and_time_ordered_desc(self, instance_id: str) -> list[dict[str, Any]]:
        """Get events for a specific instance, ordered by timestamp (newest first)."""
        events = self.list(predicate=lambda row: row.get("instance_id") == instance_id)
        # Sort by created_at timestamp, descending
        return sorted(events, key=lambda x: x.get("created_at", ""), reverse=True)

    def by_time_range(self, start_time: str, end_time: str) -> list[dict[str, Any]]:
        """Get events within a specific time range, ordered by timestamp."""
        events = self.list(predicate=lambda row: 
                          row.get("created_at", "") >= start_time and 
                          row.get("created_at", "") <= end_time)
        # Sort by created_at timestamp
        return sorted(events, key=lambda x: x.get("created_at", ""))
