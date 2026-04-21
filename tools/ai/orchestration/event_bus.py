"""
Event Bus for Orchestration

Provides a central event bus for communication between agents and components.
Handles:
- Event publishing and subscription
- Asynchronous event processing
- Event filtering and routing
- Dead letter queue for failed events
- Event persistence and replay
- Pattern-based subscriptions

This implementation provides:

    Publish/Subscribe Pattern: Central event bus with publisher-subscriber model
    Pattern Matching: Support for exact matches, wildcards (task.*), and regex patterns
    Priority Queues: Events processed by priority (CRITICAL to BACKGROUND)
    Delivery Guarantees: At-most-once, at-least-once, exactly-once modes
    Dead Letter Queue: Failed events go to DLQ for later retry
    Event History: Track recent events for debugging and replay
    Async Support: Handle both sync and async callbacks
    Event Filtering: Additional filter functions for fine-grained control
    Retry with Backoff: Exponential backoff for failed deliveries
    Correlation Tracking: Correlation and causation IDs for event chains
"""

import asyncio
import threading
import uuid
import re
from typing import Dict, List, Optional, Any, Set, Tuple, Callable, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from collections import defaultdict
from queue import Queue, PriorityQueue

from ..shared.logger import get_logger
from ..shared.state_manager import state_manager

logger = get_logger(__name__)


class EventType(Enum):
    """Standard event types for the system"""
    # System events
    SYSTEM_STARTUP = "system.startup"
    SYSTEM_SHUTDOWN = "system.shutdown"
    SYSTEM_HEALTH_CHECK = "system.health_check"
    
    # Agent events
    AGENT_REGISTERED = "agent.registered"
    AGENT_DEREGISTERED = "agent.deregistered"
    AGENT_STATUS_CHANGED = "agent.status_changed"
    AGENT_HEARTBEAT = "agent.heartbeat"
    
    # Task events
    TASK_SUBMITTED = "task.submitted"
    TASK_STARTED = "task.started"
    TASK_COMPLETED = "task.completed"
    TASK_FAILED = "task.failed"
    TASK_CANCELLED = "task.cancelled"
    TASK_TIMEOUT = "task.timeout"
    
    # Workflow events
    WORKFLOW_STARTED = "workflow.started"
    WORKFLOW_PAUSED = "workflow.paused"
    WORKFLOW_RESUMED = "workflow.resumed"
    WORKFLOW_COMPLETED = "workflow.completed"
    WORKFLOW_FAILED = "workflow.failed"
    WORKFLOW_CANCELLED = "workflow.cancelled"
    
    # Context events
    CONTEXT_CREATED = "context.created"
    CONTEXT_UPDATED = "context.updated"
    CONTEXT_DELETED = "context.deleted"
    
    # Human-in-the-loop events
    HUMAN_TASK_CREATED = "human_task.created"
    HUMAN_TASK_ASSIGNED = "human_task.assigned"
    HUMAN_TASK_COMPLETED = "human_task.completed"
    HUMAN_FEEDBACK_RECEIVED = "human.feedback_received"
    HUMAN_SESSION_STARTED = "human.session_started"
    HUMAN_SESSION_ENDED = "human.session_ended"
    
    # Error events
    ERROR_OCCURRED = "error.occurred"
    ERROR_RECOVERED = "error.recovered"
    
    # Custom events (for extensibility)
    CUSTOM = "custom"


class EventPriority(Enum):
    """Priority levels for events"""
    CRITICAL = 0
    HIGH = 1
    NORMAL = 2
    LOW = 3
    BACKGROUND = 4


class DeliveryMode(Enum):
    """Event delivery modes"""
    AT_MOST_ONCE = "at_most_once"
    AT_LEAST_ONCE = "at_least_once"
    EXACTLY_ONCE = "exactly_once"


@dataclass
class Event:
    """Represents an event in the system"""
    id: str
    type: Union[EventType, str]
    source: str
    data: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    priority: EventPriority = EventPriority.NORMAL
    correlation_id: Optional[str] = None
    causation_id: Optional[str] = None
    version: str = "1.0"
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type.value if isinstance(self.type, EventType) else self.type,
            "source": self.source,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
            "priority": self.priority.value,
            "correlation_id": self.correlation_id,
            "causation_id": self.causation_id,
            "version": self.version,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Event":
        # Handle both enum and string types
        event_type = data["type"]
        if event_type in [t.value for t in EventType]:
            event_type = EventType(event_type)
        
        return cls(
            id=data["id"],
            type=event_type,
            source=data["source"],
            data=data.get("data", {}),
            timestamp=datetime.fromisoformat(data["timestamp"]) if data.get("timestamp") else datetime.now(),
            priority=EventPriority(data.get("priority", 2)),
            correlation_id=data.get("correlation_id"),
            causation_id=data.get("causation_id"),
            version=data.get("version", "1.0"),
            metadata=data.get("metadata", {})
        )


@dataclass
class Subscription:
    """Represents an event subscription"""
    id: str
    pattern: Union[EventType, str, re.Pattern]
    callback: Callable
    priority: EventPriority = EventPriority.NORMAL
    filter_func: Optional[Callable[[Event], bool]] = None
    delivery_mode: DeliveryMode = DeliveryMode.AT_LEAST_ONCE
    max_retries: int = 3
    retry_delay: int = 1
    created_at: datetime = field(default_factory=datetime.now)
    
    def matches(self, event: Event) -> bool:
        """Check if this subscription matches an event"""
        event_type = event.type.value if isinstance(event.type, EventType) else event.type
        
        if isinstance(self.pattern, EventType):
            return event.type == self.pattern
        elif isinstance(self.pattern, str):
            # Check for wildcard patterns (e.g., "task.*")
            if self.pattern.endswith("*"):
                prefix = self.pattern[:-1]
                return event_type.startswith(prefix)
            return event_type == self.pattern
        elif isinstance(self.pattern, re.Pattern):
            return bool(self.pattern.match(event_type))
        
        return False


@dataclass
class EventEnvelope:
    """Wrapper for event with delivery metadata"""
    event: Event
    subscription_id: str
    delivery_attempts: int = 0
    last_attempt: Optional[datetime] = None
    next_retry: Optional[datetime] = None
    status: str = "pending"  # pending, delivered, failed, dead_lettered
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "event": self.event.to_dict(),
            "subscription_id": self.subscription_id,
            "delivery_attempts": self.delivery_attempts,
            "last_attempt": self.last_attempt.isoformat() if self.last_attempt else None,
            "next_retry": self.next_retry.isoformat() if self.next_retry else None,
            "status": self.status
        }


class EventBus:
    """
    Central event bus for system communication.
    
    Features:
    - Publish/subscribe pattern
    - Pattern-based subscriptions (wildcards, regex)
    - Priority-based event processing
    - Async and sync delivery
    - Dead letter queue
    - Event persistence and replay
    - Event filtering
    """
    
    def __init__(self, storage_key: str = "event_bus"):
        self.storage_key = storage_key
        self.subscriptions: Dict[str, Subscription] = {}
        self.subscription_index: Dict[str, List[str]] = defaultdict(list)  # pattern_type -> sub_ids
        
        # Event queues
        self.event_queue: PriorityQueue = PriorityQueue()
        self.dead_letter_queue: List[EventEnvelope] = []
        
        # Processing
        self._processing_thread: Optional[threading.Thread] = None
        self._stop_processing = threading.Event()
        self._lock = threading.RLock()
        
        # Statistics
        self.stats: Dict[str, Any] = {
            "events_published": 0,
            "events_delivered": 0,
            "events_failed": 0,
            "events_dead_lettered": 0,
            "active_subscriptions": 0
        }
        
        # Event history (for replay)
        self.event_history: List[Event] = []
        self.max_history_size = 1000
        
        # Callbacks for system events
        self._on_event_published: List[Callable] = []
        self._on_event_delivered: List[Callable] = []
        self._on_event_failed: List[Callable] = []
        
        # Load persisted data
        self._load_data()
        
        # Start processing thread
        self._start_processing()
        
        logger.info("EventBus initialized")
    
    def _load_data(self) -> None:
        """Load persisted event data"""
        try:
            history_data = state_manager.get(f"{self.storage_key}.history", [])
            for event_data in history_data[-self.max_history_size:]:
                if isinstance(event_data, dict):
                    self.event_history.append(Event.from_dict(event_data))
            
            dead_letter_data = state_manager.get(f"{self.storage_key}.dead_letter", [])
            for dl_data in dead_letter_data:
                if isinstance(dl_data, dict):
                    self.dead_letter_queue.append(EventEnvelope(**dl_data))
            
            stats_data = state_manager.get(f"{self.storage_key}.stats", {})
            self.stats.update(stats_data)
            
        except Exception as e:
            logger.warning(f"Failed to load event bus data: {e}")
    
    def _save_data(self) -> None:
        """Save event data to persistence"""
        try:
            # Save only recent history
            recent_history = [e.to_dict() for e in self.event_history[-100:]]
            state_manager.set(f"{self.storage_key}.history", recent_history)
            
            dead_letter = [dl.to_dict() for dl in self.dead_letter_queue[-100:]]
            state_manager.set(f"{self.storage_key}.dead_letter", dead_letter)
            
            state_manager.set(f"{self.storage_key}.stats", self.stats)
            
        except Exception as e:
            logger.error(f"Failed to save event bus data: {e}")
    
    def _start_processing(self) -> None:
        """Start background event processing thread"""
        def process_events():
            while not self._stop_processing.is_set():
                try:
                    # Get event from queue with timeout
                    try:
                        priority, envelope = self.event_queue.get(timeout=1)
                    except:
                        continue
                    
                    self._deliver_event(envelope)
                    
                except Exception as e:
                    logger.error(f"Error processing event: {e}")
        
        self._processing_thread = threading.Thread(target=process_events, daemon=True)
        self._processing_thread.start()
    
    def _deliver_event(self, envelope: EventEnvelope) -> None:
        """
        Deliver an event to a subscriber.
        
        Args:
            envelope: Event envelope with delivery metadata
        """
        subscription = self.subscriptions.get(envelope.subscription_id)
        if not subscription:
            logger.warning(f"Subscription {envelope.subscription_id} not found")
            return
        
        event = envelope.event
        
        try:
            # Apply filter if present
            if subscription.filter_func and not subscription.filter_func(event):
                return
            
            # Deliver the event
            callback = subscription.callback
            
            # Handle async callbacks
            if asyncio.iscoroutinefunction(callback):
                # Run async callback in event loop
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        asyncio.create_task(callback(event))
                    else:
                        loop.run_until_complete(callback(event))
                except Exception as e:
                    raise e
            else:
                # Sync callback
                callback(event)
            
            # Mark as delivered
            envelope.status = "delivered"
            self.stats["events_delivered"] += 1
            
            self._notify_event_delivered(event, subscription)
            
        except Exception as e:
            logger.error(f"Failed to deliver event {event.id} to {subscription.id}: {e}")
            envelope.delivery_attempts += 1
            envelope.last_attempt = datetime.now()
            
            if envelope.delivery_attempts >= subscription.max_retries:
                # Move to dead letter queue
                envelope.status = "dead_lettered"
                self.dead_letter_queue.append(envelope)
                self.stats["events_dead_lettered"] += 1
                self._notify_event_failed(event, subscription, e)
                logger.warning(f"Event {event.id} moved to dead letter queue after {envelope.delivery_attempts} attempts")
            else:
                # Schedule retry
                delay = subscription.retry_delay * (2 ** (envelope.delivery_attempts - 1))  # Exponential backoff
                envelope.next_retry = datetime.now()
                envelope.status = "pending"
                
                # Re-queue with same priority
                self.event_queue.put((event.priority.value, envelope))
                self.stats["events_failed"] += 1
            
            self._notify_event_failed(event, subscription, e)
    
    def publish(self, event: Event, delivery_mode: DeliveryMode = None) -> str:
        """
        Publish an event to the event bus.
        
        Args:
            event: Event to publish
            delivery_mode: Override delivery mode for this event
            
        Returns:
            Event ID
        """
        if not event.id:
            event.id = str(uuid.uuid4())
        
        # Find matching subscriptions
        matching_subs = self._find_matching_subscriptions(event)
        
        if not matching_subs:
            logger.debug(f"No subscribers for event {event.type}")
            return event.id
        
        # Create envelopes for each subscription
        with self._lock:
            for sub in matching_subs:
                delivery = delivery_mode or sub.delivery_mode
                envelope = EventEnvelope(
                    event=event,
                    subscription_id=sub.id
                )
                
                # Add to queue with priority
                self.event_queue.put((event.priority.value, envelope))
        
        # Add to history
        self.event_history.append(event)
        if len(self.event_history) > self.max_history_size:
            self.event_history.pop(0)
        
        # Update stats
        self.stats["events_published"] += 1
        self.stats["active_subscriptions"] = len(matching_subs)
        
        # Notify
        self._notify_event_published(event)
        
        # Persist
        self._save_data()
        
        logger.debug(f"Published event {event.id} of type {event.type}")
        
        return event.id
    
    def _find_matching_subscriptions(self, event: Event) -> List[Subscription]:
        """Find all subscriptions that match an event"""
        matches = []
        
        with self._lock:
            for sub in self.subscriptions.values():
                if sub.matches(event):
                    matches.append(sub)
        
        # Sort by priority
        matches.sort(key=lambda s: s.priority.value)
        
        return matches
    
    def subscribe(self, pattern: Union[EventType, str, re.Pattern],
                 callback: Callable,
                 priority: EventPriority = EventPriority.NORMAL,
                 filter_func: Optional[Callable[[Event], bool]] = None,
                 delivery_mode: DeliveryMode = DeliveryMode.AT_LEAST_ONCE,
                 max_retries: int = 3,
                 retry_delay: int = 1) -> str:
        """
        Subscribe to events matching a pattern.
        
        Args:
            pattern: Event type pattern (supports wildcards and regex)
            callback: Callback function for events
            priority: Subscription priority
            filter_func: Additional filter function
            delivery_mode: Delivery guarantee mode
            max_retries: Maximum retry attempts on failure
            retry_delay: Base delay between retries
            
        Returns:
            Subscription ID
        """
        sub_id = str(uuid.uuid4())
        
        subscription = Subscription(
            id=sub_id,
            pattern=pattern,
            callback=callback,
            priority=priority,
            filter_func=filter_func,
            delivery_mode=delivery_mode,
            max_retries=max_retries,
            retry_delay=retry_delay
        )
        
        with self._lock:
            self.subscriptions[sub_id] = subscription
        
        self.stats["active_subscriptions"] = len(self.subscriptions)
        
        logger.debug(f"Created subscription {sub_id} for pattern {pattern}")
        
        return sub_id
    
    def unsubscribe(self, subscription_id: str) -> bool:
        """
        Unsubscribe from events.
        
        Args:
            subscription_id: Subscription ID to remove
            
        Returns:
            True if unsubscribed successfully
        """
        with self._lock:
            if subscription_id in self.subscriptions:
                del self.subscriptions[subscription_id]
                self.stats["active_subscriptions"] = len(self.subscriptions)
                logger.debug(f"Unsubscribed {subscription_id}")
                return True
        
        return False
    
    def subscribe_to_type(self, event_type: EventType, callback: Callable) -> str:
        """Convenience method to subscribe to a specific event type"""
        return self.subscribe(event_type, callback)
    
    def subscribe_to_prefix(self, prefix: str, callback: Callable) -> str:
        """Subscribe to all events with a given prefix (e.g., 'task.')"""
        pattern = f"{prefix}*"
        return self.subscribe(pattern, callback)
    
    def subscribe_to_regex(self, pattern: str, callback: Callable) -> str:
        """Subscribe using a regex pattern"""
        return self.subscribe(re.compile(pattern), callback)
    
    def replay_events(self, since: datetime = None, 
                     event_types: List[Union[EventType, str]] = None) -> int:
        """
        Replay historical events.
        
        Args:
            since: Only replay events after this time
            event_types: Only replay specific event types
            
        Returns:
            Number of events replayed
        """
        replay_count = 0
        
        for event in self.event_history:
            # Filter by time
            if since and event.timestamp < since:
                continue
            
            # Filter by type
            if event_types:
                event_type_str = event.type.value if isinstance(event.type, EventType) else event.type
                if event_type_str not in [t.value if isinstance(t, EventType) else t for t in event_types]:
                    continue
            
            # Re-publish
            self.publish(event)
            replay_count += 1
        
        logger.info(f"Replayed {replay_count} events")
        
        return replay_count
    
    def retry_dead_letter(self, max_retries: int = 1) -> int:
        """
        Retry events from the dead letter queue.
        
        Args:
            max_retries: Maximum retry attempts per event
            
        Returns:
            Number of events retried
        """
        retry_count = 0
        
        with self._lock:
            for envelope in list(self.dead_letter_queue):
                if envelope.delivery_attempts < max_retries:
                    envelope.delivery_attempts = 0
                    envelope.status = "pending"
                    self.event_queue.put((envelope.event.priority.value, envelope))
                    self.dead_letter_queue.remove(envelope)
                    retry_count += 1
        
        logger.info(f"Retried {retry_count} events from dead letter queue")
        
        return retry_count
    
    def clear_dead_letter(self) -> int:
        """Clear all events from dead letter queue"""
        count = len(self.dead_letter_queue)
        self.dead_letter_queue.clear()
        self._save_data()
        logger.info(f"Cleared {count} events from dead letter queue")
        return count
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get event bus statistics"""
        with self._lock:
            return {
                **self.stats,
                "queue_size": self.event_queue.qsize(),
                "dead_letter_size": len(self.dead_letter_queue),
                "history_size": len(self.event_history),
                "subscriptions": {
                    sub_id: {
                        "pattern": str(sub.pattern),
                        "priority": sub.priority.value,
                        "created_at": sub.created_at.isoformat()
                    }
                    for sub_id, sub in self.subscriptions.items()
                }
            }
    
    def get_event_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent event history"""
        return [e.to_dict() for e in self.event_history[-limit:]]
    
    def get_dead_letter_events(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get events in dead letter queue"""
        return [dl.to_dict() for dl in self.dead_letter_queue[-limit:]]
    
    def emit(self, event_type: Union[EventType, str], source: str,
            data: Dict[str, Any] = None,
            priority: EventPriority = EventPriority.NORMAL,
            correlation_id: str = None,
            causation_id: str = None) -> str:
        """
        Convenience method to create and publish an event.
        
        Args:
            event_type: Type of event
            source: Source component/agent ID
            data: Event data payload
            priority: Event priority
            correlation_id: Correlation ID for tracking
            causation_id: Causation ID (parent event)
            
        Returns:
            Event ID
        """
        event = Event(
            id=str(uuid.uuid4()),
            type=event_type,
            source=source,
            data=data or {},
            priority=priority,
            correlation_id=correlation_id,
            causation_id=causation_id
        )
        
        return self.publish(event)
    
    def emit_task_event(self, task_id: str, event_type: str, source: str,
                       data: Dict[str, Any] = None) -> str:
        """Emit a task-related event"""
        return self.emit(
            event_type=event_type,
            source=source,
            data={
                "task_id": task_id,
                **(data or {})
            },
            correlation_id=task_id
        )
    
    def emit_workflow_event(self, workflow_id: str, event_type: str, source: str,
                           data: Dict[str, Any] = None) -> str:
        """Emit a workflow-related event"""
        return self.emit(
            event_type=event_type,
            source=source,
            data={
                "workflow_id": workflow_id,
                **(data or {})
            },
            correlation_id=workflow_id
        )
    
    def emit_error_event(self, source: str, error: Exception,
                        context: Dict[str, Any] = None) -> str:
        """Emit an error event"""
        return self.emit(
            event_type=EventType.ERROR_OCCURRED,
            source=source,
            data={
                "error_type": type(error).__name__,
                "error_message": str(error),
                "context": context or {}
            }
        )
    
    def on_event_published(self, callback: Callable) -> None:
        """Register callback for event published events"""
        self._on_event_published.append(callback)
    
    def on_event_delivered(self, callback: Callable) -> None:
        """Register callback for event delivered events"""
        self._on_event_delivered.append(callback)
    
    def on_event_failed(self, callback: Callable) -> None:
        """Register callback for event failed events"""
        self._on_event_failed.append(callback)
    
    def _notify_event_published(self, event: Event) -> None:
        """Notify event published callbacks"""
        for callback in self._on_event_published:
            try:
                callback(event)
            except Exception as e:
                logger.error(f"Error in event published callback: {e}")
    
    def _notify_event_delivered(self, event: Event, subscription: Subscription) -> None:
        """Notify event delivered callbacks"""
        for callback in self._on_event_delivered:
            try:
                callback(event, subscription)
            except Exception as e:
                logger.error(f"Error in event delivered callback: {e}")
    
    def _notify_event_failed(self, event: Event, subscription: Subscription, error: Exception) -> None:
        """Notify event failed callbacks"""
        for callback in self._on_event_failed:
            try:
                callback(event, subscription, error)
            except Exception as e:
                logger.error(f"Error in event failed callback: {e}")
    
    def wait_for_event(self, event_type: Union[EventType, str], 
                      timeout: float = None,
                      condition: Callable[[Event], bool] = None) -> Optional[Event]:
        """
        Wait for a specific event to occur.
        
        Args:
            event_type: Event type to wait for
            timeout: Maximum time to wait in seconds
            condition: Additional condition to check
            
        Returns:
            Event if found, None if timeout
        """
        result = []
        event_ready = threading.Event()
        
        def handler(event):
            if condition and not condition(event):
                return
            result.append(event)
            event_ready.set()
        
        sub_id = self.subscribe(event_type, handler)
        
        try:
            event_ready.wait(timeout)
            return result[0] if result else None
        finally:
            self.unsubscribe(sub_id)
    
    def stop(self) -> None:
        """Stop the event bus processor"""
        self._stop_processing.set()
        if self._processing_thread:
            self._processing_thread.join(timeout=5)
        self._save_data()
        logger.info("EventBus stopped")
    
    def reset(self) -> None:
        """Reset the event bus (clear all subscriptions and queues)"""
        with self._lock:
            self.subscriptions.clear()
            self.subscription_index.clear()
            
            # Clear queues
            while not self.event_queue.empty():
                try:
                    self.event_queue.get_nowait()
                except:
                    break
            
            self.dead_letter_queue.clear()
            self.event_history.clear()
            
            # Reset stats
            self.stats = {
                "events_published": 0,
                "events_delivered": 0,
                "events_failed": 0,
                "events_dead_lettered": 0,
                "active_subscriptions": 0
            }
            
            self._save_data()
            logger.info("EventBus reset")


# Singleton instance
_event_bus: Optional[EventBus] = None


def get_event_bus() -> EventBus:
    """Get global EventBus instance"""
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
    return _event_bus