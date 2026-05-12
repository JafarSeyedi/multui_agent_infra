"""
Correlation Engine

Handles message and event correlation for process instances.
Supports correlation keys, message matching, and event subscription.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from uuid import uuid4
from collections import defaultdict


logger = logging.getLogger(__name__)


@dataclass
class CorrelationKey:
    """Correlation key for message/event matching"""
    name: str
    value: str
    
    def __hash__(self):
        return hash((self.name, self.value))
    
    def __eq__(self, other):
        if not isinstance(other, CorrelationKey):
            return False
        return self.name == other.name and self.value == other.value


@dataclass
class CorrelationKeySet:
    """Set of correlation keys"""
    keys: List[CorrelationKey] = field(default_factory=list)
    
    def add_key(self, name: str, value: str) -> None:
        """Add a correlation key"""
        self.keys.append(CorrelationKey(name, value))
    
    def matches(self, other: 'CorrelationKeySet') -> bool:
        """Check if this key set matches another"""
        if len(self.keys) != len(other.keys):
            return False
        
        self_dict = {k.name: k.value for k in self.keys}
        other_dict = {k.name: k.value for k in other.keys}
        
        return self_dict == other_dict
    
    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary"""
        return {k.name: k.value for k in self.keys}
    
    def __hash__(self):
        return hash(tuple(sorted((k.name, k.value) for k in self.keys)))
    
    def __eq__(self, other):
        if not isinstance(other, CorrelationKeySet):
            return False
        return self.to_dict() == other.to_dict()


@dataclass
class Message:
    """Message for correlation"""
    message_id: str
    message_name: str
    correlation_keys: CorrelationKeySet
    payload: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    ttl_seconds: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MessageSubscription:
    """Subscription for message correlation"""
    subscription_id: str
    message_name: str
    correlation_keys: CorrelationKeySet
    instance_id: str
    activity_id: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EventSubscription:
    """Subscription for event correlation"""
    subscription_id: str
    event_name: str
    instance_id: str
    activity_id: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


class CorrelationEngine:
    """
    Correlation engine for message and event matching.
    
    Handles:
    - Message correlation using correlation keys
    - Event subscription and matching
    - Message buffering for unmatched messages
    - Subscription management
    """
    
    def __init__(self, event_bus) -> None:
        self.event_bus = event_bus
        
        # Message subscriptions
        self.message_subscriptions: Dict[str, MessageSubscription] = {}
        self.message_name_index: Dict[str, Set[str]] = defaultdict(set)
        self.instance_message_subs: Dict[str, Set[str]] = defaultdict(set)
        
        # Event subscriptions
        self.event_subscriptions: Dict[str, EventSubscription] = {}
        self.event_name_index: Dict[str, Set[str]] = defaultdict(set)
        self.instance_event_subs: Dict[str, Set[str]] = defaultdict(set)
        
        # Buffered messages (waiting for subscription)
        self.buffered_messages: List[Message] = []
        self.max_buffer_size = 10000
        
        logger.info("Correlation engine created")
    
    def subscribe_message(
        self,
        message_name: str,
        correlation_keys: CorrelationKeySet,
        instance_id: str,
        activity_id: str,
        subscription_id: Optional[str] = None
    ) -> str:
        """
        Subscribe to a message.
        
        Args:
            message_name: Name of the message to subscribe to
            correlation_keys: Correlation keys for matching
            instance_id: Process instance ID
            activity_id: Activity ID waiting for message
            subscription_id: Optional subscription ID
        
        Returns:
            Subscription ID
        """
        if subscription_id is None:
            subscription_id = str(uuid4())
        
        subscription = MessageSubscription(
            subscription_id=subscription_id,
            message_name=message_name,
            correlation_keys=correlation_keys,
            instance_id=instance_id,
            activity_id=activity_id
        )
        
        self.message_subscriptions[subscription_id] = subscription
        self.message_name_index[message_name].add(subscription_id)
        self.instance_message_subs[instance_id].add(subscription_id)
        
        logger.debug(
            f"Created message subscription {subscription_id} for "
            f"message '{message_name}' in instance {instance_id}"
        )
        
        # Check buffered messages for match
        self._check_buffered_messages(subscription)
        
        return subscription_id
    
    def unsubscribe_message(self, subscription_id: str) -> bool:
        """Unsubscribe from a message"""
        subscription = self.message_subscriptions.pop(subscription_id, None)
        if not subscription:
            return False
        
        self.message_name_index[subscription.message_name].discard(subscription_id)
        self.instance_message_subs[subscription.instance_id].discard(subscription_id)
        
        logger.debug(f"Removed message subscription {subscription_id}")
        return True
    
    def subscribe_event(
        self,
        event_name: str,
        instance_id: str,
        activity_id: str,
        subscription_id: Optional[str] = None
    ) -> str:
        """
        Subscribe to an event.
        
        Args:
            event_name: Name of the event to subscribe to
            instance_id: Process instance ID
            activity_id: Activity ID waiting for event
            subscription_id: Optional subscription ID
        
        Returns:
            Subscription ID
        """
        if subscription_id is None:
            subscription_id = str(uuid4())
        
        subscription = EventSubscription(
            subscription_id=subscription_id,
            event_name=event_name,
            instance_id=instance_id,
            activity_id=activity_id
        )
        
        self.event_subscriptions[subscription_id] = subscription
        self.event_name_index[event_name].add(subscription_id)
        self.instance_event_subs[instance_id].add(subscription_id)
        
        logger.debug(
            f"Created event subscription {subscription_id} for "
            f"event '{event_name}' in instance {instance_id}"
        )
        
        return subscription_id
    
    def unsubscribe_event(self, subscription_id: str) -> bool:
        """Unsubscribe from an event"""
        subscription = self.event_subscriptions.pop(subscription_id, None)
        if not subscription:
            return False
        
        self.event_name_index[subscription.event_name].discard(subscription_id)
        self.instance_event_subs[subscription.instance_id].discard(subscription_id)
        
        logger.debug(f"Removed event subscription {subscription_id}")
        return True
    
    async def correlate_message(
        self,
        message_name: str,
        correlation_keys: CorrelationKeySet,
        payload: Optional[Dict[str, Any]] = None,
        ttl_seconds: Optional[int] = None
    ) -> List[Tuple[str, str]]:
        """
        Correlate a message with subscriptions.
        
        Args:
            message_name: Name of the message
            correlation_keys: Correlation keys
            payload: Message payload
            ttl_seconds: Time to live for buffered message
        
        Returns:
            List of (instance_id, activity_id) tuples that matched
        """
        message = Message(
            message_id=str(uuid4()),
            message_name=message_name,
            correlation_keys=correlation_keys,
            payload=payload or {},
            ttl_seconds=ttl_seconds
        )
        
        # Find matching subscriptions
        matches = self._find_message_matches(message)
        
        if matches:
            # Notify matched subscriptions
            for subscription_id in matches:
                subscription = self.message_subscriptions.get(subscription_id)
                if subscription:
                    await self._notify_message_match(subscription, message)
            
            # Return matched instances
            result = [
                (self.message_subscriptions[sid].instance_id,
                 self.message_subscriptions[sid].activity_id)
                for sid in matches
                if sid in self.message_subscriptions
            ]
            
            logger.info(
                f"Correlated message '{message_name}' to {len(result)} subscriptions"
            )
            return result
        else:
            # Buffer message for later matching
            self._buffer_message(message)
            logger.debug(f"Buffered message '{message_name}' (no matching subscriptions)")
            return []
    
    async def throw_event(
        self,
        event_name: str,
        payload: Optional[Dict[str, Any]] = None
    ) -> List[Tuple[str, str]]:
        """
        Throw an event (signal).
        
        Args:
            event_name: Name of the event
            payload: Event payload
        
        Returns:
            List of (instance_id, activity_id) tuples that caught the event
        """
        # Find matching subscriptions
        subscription_ids = self.event_name_index.get(event_name, set())
        
        if not subscription_ids:
            logger.debug(f"No subscriptions for event '{event_name}'")
            return []
        
        # Notify all matching subscriptions
        result = []
        for subscription_id in subscription_ids:
            subscription = self.event_subscriptions.get(subscription_id)
            if subscription:
                await self._notify_event_match(subscription, event_name, payload or {})
                result.append((subscription.instance_id, subscription.activity_id))
        
        logger.info(f"Event '{event_name}' caught by {len(result)} subscriptions")
        return result
    
    def _find_message_matches(self, message: Message) -> Set[str]:
        """Find subscriptions matching a message"""
        # Get subscriptions for this message name
        candidate_ids = self.message_name_index.get(message.message_name, set())
        
        matches = set()
        for subscription_id in candidate_ids:
            subscription = self.message_subscriptions.get(subscription_id)
            if not subscription:
                continue
            
            # Check if correlation keys match
            if subscription.correlation_keys.matches(message.correlation_keys):
                matches.add(subscription_id)
        
        return matches
    
    def _buffer_message(self, message: Message) -> None:
        """Buffer a message for later matching"""
        self.buffered_messages.append(message)
        
        # Limit buffer size
        if len(self.buffered_messages) > self.max_buffer_size:
            self.buffered_messages.pop(0)
    
    def _check_buffered_messages(self, subscription: MessageSubscription) -> None:
        """Check buffered messages for a new subscription"""
        matched_messages = []
        
        for message in self.buffered_messages:
            if message.message_name != subscription.message_name:
                continue
            
            if subscription.correlation_keys.matches(message.correlation_keys):
                matched_messages.append(message)
        
        # Process matches asynchronously
        if matched_messages:
            import asyncio
            for message in matched_messages:
                asyncio.create_task(self._notify_message_match(subscription, message))
                self.buffered_messages.remove(message)
    
    async def _notify_message_match(
        self,
        subscription: MessageSubscription,
        message: Message
    ) -> None:
        """Notify about a message match"""
        from .event_bus import Event, EventType
        
        await self.event_bus.publish(Event(
            type=EventType.MESSAGE_CORRELATED,
            data={
                "subscription_id": subscription.subscription_id,
                "instance_id": subscription.instance_id,
                "activity_id": subscription.activity_id,
                "message_id": message.message_id,
                "message_name": message.message_name,
                "payload": message.payload
            }
        ))
    
    async def _notify_event_match(
        self,
        subscription: EventSubscription,
        event_name: str,
        payload: Dict[str, Any]
    ) -> None:
        """Notify about an event match"""
        from .event_bus import Event, EventType
        
        await self.event_bus.publish(Event(
            type=EventType.SIGNAL_CAUGHT,
            data={
                "subscription_id": subscription.subscription_id,
                "instance_id": subscription.instance_id,
                "activity_id": subscription.activity_id,
                "event_name": event_name,
                "payload": payload
            }
        ))
    
    def cleanup_instance_subscriptions(self, instance_id: str) -> int:
        """Clean up all subscriptions for an instance"""
        # Message subscriptions
        message_subs = list(self.instance_message_subs.get(instance_id, set()))
        for sub_id in message_subs:
            self.unsubscribe_message(sub_id)
        
        # Event subscriptions
        event_subs = list(self.instance_event_subs.get(instance_id, set()))
        for sub_id in event_subs:
            self.unsubscribe_event(sub_id)
        
        total = len(message_subs) + len(event_subs)
        logger.info(f"Cleaned up {total} subscriptions for instance {instance_id}")
        return total
    
    def cleanup_expired_messages(self) -> int:
        """Clean up expired buffered messages"""
        now = datetime.utcnow()
        expired = []
        
        for message in self.buffered_messages:
            if message.ttl_seconds:
                age = (now - message.timestamp).total_seconds()
                if age > message.ttl_seconds:
                    expired.append(message)
        
        for message in expired:
            self.buffered_messages.remove(message)
        
        if expired:
            logger.info(f"Cleaned up {len(expired)} expired messages")
        
        return len(expired)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get correlation engine statistics"""
        return {
            "message_subscriptions": len(self.message_subscriptions),
            "event_subscriptions": len(self.event_subscriptions),
            "buffered_messages": len(self.buffered_messages),
            "message_names": len(self.message_name_index),
            "event_names": len(self.event_name_index),
            "instances_with_subscriptions": len(
                set(self.instance_message_subs.keys()) |
                set(self.instance_event_subs.keys())
            )
        }
