"""
Event Bus for Pub/Sub Messaging

Provides event-driven communication between orchestration components.
Supports synchronous and asynchronous event handling, event filtering,
and subscription management.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Callable, Set
from enum import Enum
from dataclasses import dataclass, field
from uuid import uuid4
from collections import defaultdict


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


@dataclass
class Subscription:
    """Event subscription"""
    subscription_id: str
    event_types: Set[EventType]
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
    
    def __init__(self, max_history_size: int = 10000):
        self.max_history_size = max_history_size
        
        # Subscriptions
        self.subscriptions: dict[str, Subscription] = {}
        self.type_subscriptions: dict[EventType, Set[str]] = defaultdict(set)
        
        # Event queue
        self.event_queue: asyncio.Queue = asyncio.Queue()
        
        # Event history
        self.event_history: list[Event] = []
        
        # Statistics
        self.published_count = 0
        self.processed_count = 0
        self.failed_count = 0
        
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
        self.event_history.append(event)
        if len(self.event_history) > self.max_history_size:
            self.event_history.pop(0)
        
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
        self.event_history.append(event)
        if len(self.event_history) > self.max_history_size:
            self.event_history.pop(0)
        
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
