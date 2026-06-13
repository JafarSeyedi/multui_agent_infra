"""
Event Bus for Pub/Sub Messaging

Provides event-driven communication between orchestration components.
Supports synchronous and asynchronous event handling, event filtering,
and subscription management. OSDM-aligned event types for BPMN/CAMMN/DMN/CEP.
"""

from __future__ import annotations

import asyncio
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging
from typing import Any, cast
from collections.abc import Callable
from uuid import uuid4

from ..persistence.event_repository import EventRepository
from engines.orchestration.models.osdm_models import EventListenerType, EventDefinitionType, CEPOperator


logger = logging.getLogger(__name__)


class EventType(Enum):
    """Standard event types"""
    # Engine events
    ENGINE_STARTED = "engine.started"
    ENGINE_STOPPED = "engine.stopped"
    ENGINE_PAUSED = "engine.paused"
    ENGINE_RESUMED = "engine.resumed"
    
    # Deployment events
    DEPLOYMENT_CREATED = "deployment.created"
    DEPLOYMENT_DELETED = "deployment.deleted"
    
    # Process instance events
    PROCESS_INSTANCE_STARTED = "process.instance.started"
    PROCESS_INSTANCE_COMPLETED = "process.instance.completed"
    PROCESS_INSTANCE_TERMINATED = "process.instance.terminated"
    PROCESS_INSTANCE_SUSPENDED = "process.instance.suspended"
    PROCESS_INSTANCE_RESUMED = "process.instance.resumed"
    
    # Activity events
    ACTIVITY_STARTED = "activity.started"
    ACTIVITY_COMPLETED = "activity.completed"
    ACTIVITY_FAILED = "activity.failed"
    ACTIVITY_CANCELLED = "activity.cancelled"
    
    # Task events
    TASK_CREATED = "task.created"
    TASK_ASSIGNED = "task.assigned"
    TASK_COMPLETED = "task.completed"
    
    # Message events
    MESSAGE_RECEIVED = "message.received"
    MESSAGE_SENT = "message.sent"
    MESSAGE_CORRELATED = "message.correlated"
    
    # Signal events
    SIGNAL_THROWN = "signal.thrown"
    SIGNAL_CAUGHT = "signal.caught"
    
    # Timer events
    TIMER_FIRED = "timer.fired"
    TIMER_CANCELLED = "timer.cancelled"
    
    # Error events
    ERROR_THROWN = "error.thrown"
    ERROR_CAUGHT = "error.caught"
    
    # Compensation events
    COMPENSATION_TRIGGERED = "compensation.triggered"
    COMPENSATION_COMPLETED = "compensation.completed"
    
    # Job events
    JOB_CREATED = "job.created"
    JOB_EXECUTED = "job.executed"
    JOB_FAILED = "job.failed"
    
    # Incident events
    INCIDENT_CREATED = "incident.created"
    INCIDENT_RESOLVED = "incident.resolved"
    
    # Metrics events
    METRICS_COLLECTED = "metrics.collected"
    
    # Custom events
    CUSTOM = "custom"


class EventPriority(Enum):
    """Event priority levels"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class Event:
    """Event object"""
    type: EventType
    data: dict[str, Any] = field(default_factory=dict)
    event_id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = field(default_factory=datetime.utcnow)
    priority: EventPriority = EventPriority.NORMAL
    source: str | None = None
    correlation_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert event to dictionary"""
        return {
            "event_id": self.event_id,
            "type": self.type.value,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
            "priority": self.priority.value,
            "source": self.source,
            "correlation_id": self.correlation_id,
            "metadata": self.metadata
        }

    def to_record_payload(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "instance_id": self.data.get("instance_id"),
            "event_type": self.type.value,
            "type": self.type.value,
            "correlation_id": self.correlation_id,
            "created_at": self.timestamp.isoformat(),
            "recorded_at": self.timestamp.isoformat(),
            "payload": {
                "data": dict(self.data),
                "priority": self.priority.value,
                "source": self.source,
                "metadata": dict(self.metadata),
            },
        }

    @classmethod
    def from_record_payload(cls, payload: dict[str, Any]) -> Event:
        nested_payload = cast(dict[str, Any], payload.get("payload")) if isinstance(payload.get("payload"), dict) else {}
        event_type_raw = str(payload.get("event_type") or payload.get("type") or EventType.CUSTOM.value)
        try:
            event_type = EventType(event_type_raw)
        except ValueError:
            event_type = EventType.CUSTOM
        priority_raw = nested_payload.get("priority", EventPriority.NORMAL.value)
        try:
            priority = EventPriority(int(priority_raw))
        except (TypeError, ValueError):
            priority = EventPriority.NORMAL
        return cls(
            type=event_type,
            data=dict(nested_payload.get("data") or payload.get("data") or {}),
            event_id=str(payload.get("event_id", str(uuid4()))),
            timestamp=_parse_datetime(payload.get("recorded_at") or payload.get("created_at")),
            priority=priority,
            source=_optional_str(nested_payload.get("source") or payload.get("source")),
            correlation_id=_optional_str(payload.get("correlation_id")),
            metadata=dict(nested_payload.get("metadata") or payload.get("metadata") or {}),
        )

    def set_osdm_metadata(
        self,
        listener_type: Any = None,
        event_definition_type: Any = None,
        cep_operator: Any = None,
    ) -> None:
        """Set OSDM event metadata for BPMN/CEP alignment."""
        if listener_type is not None:
            self.metadata["osdm_listener_type"] = listener_type.value
        if event_definition_type is not None:
            self.metadata["osdm_event_definition_type"] = event_definition_type.value
        if cep_operator is not None:
            self.metadata["osdm_cep_operator"] = cep_operator.value


@dataclass
class Subscription:
    """Event subscription"""
    subscription_id: str
    event_types: set[EventType]
    handler: Callable
    filter_func: Callable[[Event], bool] | None = None
    is_async: bool = True
    priority: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = field(default_factory=dict)


class EventBus:
    """
    Event bus for pub/sub messaging.
    
    Provides:
    - Event publishing and subscription
    - Synchronous and asynchronous event handling
    - Event filtering and routing
    - Priority-based event processing
    - Event history and replay
    """
    
    def __init__(
        self,
        max_history_size: int = 10000,
        *,
        event_repository: EventRepository | None = None,
    ):
        self.max_history_size = max_history_size
        
        # Subscriptions
        self.subscriptions: dict[str, Subscription] = {}
        self.type_subscriptions: dict[EventType, set[str]] = defaultdict(set)
        
        # Event queue
        self.event_queue: asyncio.Queue = asyncio.Queue()
        
        # Event history
        self.event_history: list[Event] = []
        
        # Statistics
        self.published_count = 0
        self.processed_count = 0
        self.failed_count = 0
        self.event_repository = event_repository
        
        # State
        self.is_running = False
        self._processor_task: asyncio.Task | None = None
        
        logger.info("Event bus created")
    
    async def start(self) -> None:
        """Start the event bus"""
        if self.is_running:
            return
        
        self.is_running = True
        self._processor_task = asyncio.create_task(self._process_events())
        logger.info("Event bus started")
    
    async def stop(self) -> None:
        """Stop the event bus"""
        if not self.is_running:
            return
        
        self.is_running = False
        
        if self._processor_task:
            self._processor_task.cancel()
            try:
                await self._processor_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Event bus stopped")
    
    def subscribe(
        self,
        event_types: list[EventType],
        handler: Callable,
        filter_func: Callable[[Event], bool] | None = None,
        is_async: bool = True,
        priority: int = 0,
        subscription_id: str | None = None
    ) -> str:
        """
        Subscribe to events.
        
        Args:
            event_types: list of event types to subscribe to
            handler: Event handler function
            filter_func: Optional filter function
            is_async: Whether handler is async
            priority: Subscription priority (higher = processed first)
            subscription_id: Optional subscription ID
        
        Returns:
            Subscription ID
        """
        if subscription_id is None:
            subscription_id = str(uuid4())
        
        subscription = Subscription(
            subscription_id=subscription_id,
            event_types=set(event_types),
            handler=handler,
            filter_func=filter_func,
            is_async=is_async,
            priority=priority
        )
        
        self.subscriptions[subscription_id] = subscription
        
        # Index by event type
        for event_type in event_types:
            self.type_subscriptions[event_type].add(subscription_id)
        
        logger.debug(f"Created subscription {subscription_id} for {len(event_types)} event types")
        return subscription_id
    
    def unsubscribe(self, subscription_id: str) -> bool:
        """Unsubscribe from events"""
        subscription = self.subscriptions.pop(subscription_id, None)
        if not subscription:
            return False
        
        # Remove from type index
        for event_type in subscription.event_types:
            self.type_subscriptions[event_type].discard(subscription_id)
        
        logger.debug(f"Removed subscription {subscription_id}")
        return True
    
    async def publish(self, event: Event) -> None:
        """
        Publish an event.
        
        Args:
            event: Event to publish
        """
        self.published_count += 1
        
        # Add to history
        self._append_history(event)
        await self._persist_event(event)
        
        # Add to queue for async processing
        await self.event_queue.put(event)
        
        logger.debug(f"Published event: {event.type.value} (id: {event.event_id})")
    
    async def publish_sync(self, event: Event) -> None:
        """
        Publish an event synchronously (process immediately).
        
        Args:
            event: Event to publish
        """
        self.published_count += 1
        
        # Add to history
        self._append_history(event)
        await self._persist_event(event)
        
        # Process immediately
        await self._handle_event(event)
        
        logger.debug(f"Published event synchronously: {event.type.value}")
    
    async def _process_events(self) -> None:
        """Event processing loop"""
        logger.info("Event processor started")
        
        while self.is_running:
            try:
                # Get event from queue with timeout
                try:
                    event = await asyncio.wait_for(
                        self.event_queue.get(),
                        timeout=1.0
                    )
                except asyncio.TimeoutError:
                    continue
                
                # Handle event
                await self._handle_event(event)
                self.processed_count += 1
                
            except Exception as e:
                logger.error(f"Error processing event: {e}", exc_info=True)
                self.failed_count += 1
        
        logger.info("Event processor stopped")
    
    async def _handle_event(self, event: Event) -> None:
        """Handle a single event"""
        # Get subscriptions for this event type
        subscription_ids = self.type_subscriptions.get(event.type, set())
        
        if not subscription_ids:
            return
        
        # Get subscriptions and sort by priority
        subscriptions = [
            self.subscriptions[sid]
            for sid in subscription_ids
            if sid in self.subscriptions
        ]
        subscriptions.sort(key=lambda s: s.priority, reverse=True)
        
        # Execute handlers
        for subscription in subscriptions:
            try:
                # Apply filter if present
                if subscription.filter_func:
                    if not subscription.filter_func(event):
                        continue
                
                # Execute handler
                if subscription.is_async:
                    await subscription.handler(event)
                else:
                    subscription.handler(event)
                    
            except Exception as e:
                logger.error(
                    f"Error in event handler {subscription.subscription_id}: {e}",
                    exc_info=True
                )
    
    def get_event_history(
        self,
        event_type: EventType | None = None,
        limit: int = 100
    ) -> list[Event]:
        """Get event history"""
        events = self.event_history
        
        if event_type:
            events = [e for e in events if e.type == event_type]
        
        return events[-limit:]
    
    def clear_history(self) -> None:
        """Clear event history"""
        self.event_history.clear()
        logger.info("Cleared event history")

    async def reload_history(self, *, limit: int = 100) -> list[Event]:
        """Reload recent history from repository when available."""
        if self.event_repository is None:
            return self.get_event_history(limit=limit)
        rows = self.event_repository.list()[-limit:]
        self.event_history = [Event.from_record_payload(row) for row in rows]
        return list(self.event_history)

    async def replay_events(
        self,
        *,
        event_type: EventType | None = None,
        correlation_id: str | None = None,
        limit: int = 100,
        publish: bool = False,
    ) -> list[Event]:
        """Reload persisted events and optionally replay them through handlers."""
        if self.event_repository is None:
            events = self.get_event_history(event_type=event_type, limit=limit)
        else:
            rows = self.event_repository.list()
            if event_type is not None:
                rows = [row for row in rows if row.get("event_type") == event_type.value or row.get("type") == event_type.value]
            if correlation_id is not None:
                rows = [row for row in rows if row.get("correlation_id") == correlation_id]
            events = [Event.from_record_payload(row) for row in rows[-limit:]]
        if publish:
            for event in events:
                await self._handle_event(event)
        return events

    def get_statistics(self) -> dict[str, Any]:
        """Get event bus statistics"""
        type_counts: dict[str, int] = defaultdict(int)
        for event in self.event_history:
            type_counts[event.type.value] += 1
        
        return {
            "published_count": self.published_count,
            "processed_count": self.processed_count,
            "failed_count": self.failed_count,
            "queue_size": self.event_queue.qsize(),
            "history_size": len(self.event_history),
            "subscriptions": len(self.subscriptions),
            "event_type_distribution": dict(type_counts)
        }

    def get_subscriptions(self, event_type: EventType | None = None) -> list[Subscription]:
        """Get subscriptions, optionally filtered by event type"""
        if event_type is None:
            return list(self.subscriptions.values())
        
        subscription_ids = self.type_subscriptions.get(event_type, set())
        return [
            self.subscriptions[sid]
            for sid in subscription_ids
            if sid in self.subscriptions
        ]

    def _append_history(self, event: Event) -> None:
        self.event_history.append(event)
        if len(self.event_history) > self.max_history_size:
            self.event_history.pop(0)

    async def _persist_event(self, event: Event) -> None:
        if self.event_repository is None:
            return
        await self.event_repository.append_persisted(event.to_record_payload())


def _parse_datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        return datetime.fromisoformat(value)
    return datetime.utcnow()


def _optional_str(value: Any) -> str | None:
    return None if value is None else str(value)