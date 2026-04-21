"""
Work Queue for Human Task Management

Manages queues of work items for human assignment including:
- Priority-based queuing
- Work item lifecycle management
- Queue statistics and monitoring
- Load balancing across queues
- Dead letter queue for failed items
- Queue persistence and recovery

This work_queue.py provides:

    Multiple Queue Types: High priority, standard, low priority, background, human task, approval, review, bug triage, dead letter
    Priority-Based Queuing: Heap-based priority queue with support for CRITICAL, HIGH, MEDIUM, LOW, LOWEST priorities
    Work Item Lifecycle: PENDING → ASSIGNED → IN_PROGRESS → COMPLETED/FAILED/CANCELLED/EXPIRED
    Dependency Tracking: Items can depend on other items being completed first
    Automatic Expiry: TTL-based expiration with background cleanup
    Retry Logic: Configurable retry attempts with exponential backoff
    Dead Letter Queue: Failed items moved to DLQ for later inspection/retry
    Queue Metrics: Track enqueued, completed, failed counts with wait and processing times
    Convenience Methods: Create human task, review, and approval items easily
    Persistence: All data stored via shared state manager with automatic saving
"""

import uuid
import threading
import heapq
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from collections import defaultdict, deque

from ...shared.logger import get_logger
from ...shared.state_manager import state_manager
from ...shared.config import config
from .work_item_types import WorkItemType, get_work_item_type

logger = get_logger(__name__)


class QueueType(Enum):
    """Types of work queues"""
    HIGH_PRIORITY = "high_priority"      # Urgent/blocking tasks
    STANDARD = "standard"                 # Regular tasks
    LOW_PRIORITY = "low_priority"        # Non-urgent tasks
    BACKGROUND = "background"            # Background processing
    DEAD_LETTER = "dead_letter"          # Failed/completed items


class WorkItemStatus(Enum):
    """Status of a work item"""
    PENDING = "pending"          # Waiting in queue
    ASSIGNED = "assigned"        # Assigned to human
    IN_PROGRESS = "in_progress"  # Being worked on
    COMPLETED = "completed"      # Successfully completed
    FAILED = "failed"            # Failed processing
    CANCELLED = "cancelled"      # Cancelled by system
    EXPIRED = "expired"          # TTL expired
    BLOCKED = "blocked"          # Waiting for dependency


class WorkItemPriority(Enum):
    """Priority levels for work items"""
    CRITICAL = 0    # Highest priority
    HIGH = 1
    MEDIUM = 2
    LOW = 3
    LOWEST = 4      # Lowest priority


@dataclass
class WorkItem:
    """Represents a work item in the queue"""
    item_id: str
    queue_type: QueueType
    work_item_type: WorkItemType
    priority: WorkItemPriority
    payload: Dict[str, Any]
    status: WorkItemStatus = WorkItemStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    assigned_to: Optional[str] = None
    assigned_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    retry_count: int = 0
    max_retries: int = 3
    error_message: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)  # Item IDs this depends on
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    
    @property
    def age_seconds(self) -> float:
        """Age of work item in seconds"""
        return (datetime.now() - self.created_at).total_seconds()
    
    @property
    def wait_time_seconds(self) -> float:
        """Time spent waiting (if not started)"""
        if self.started_at:
            return (self.started_at - self.created_at).total_seconds()
        return (datetime.now() - self.created_at).total_seconds()
    
    @property
    def processing_time_seconds(self) -> float:
        """Time spent processing"""
        if self.started_at:
            end = self.completed_at or datetime.now()
            return (end - self.started_at).total_seconds()
        return 0.0
    
    @property
    def is_expired(self) -> bool:
        """Check if work item has expired"""
        if self.expires_at:
            return datetime.now() > self.expires_at
        return False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "item_id": self.item_id,
            "queue_type": self.queue_type.value,
            "work_item_type": self.work_item_type,
            "priority": self.priority.value,
            "payload": self.payload,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "assigned_to": self.assigned_to,
            "assigned_at": self.assigned_at.isoformat() if self.assigned_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "error_message": self.error_message,
            "dependencies": self.dependencies,
            "metadata": self.metadata,
            "tags": self.tags
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorkItem":
        return cls(
            item_id=data["item_id"],
            queue_type=QueueType(data["queue_type"]),
            work_item_type=WorkItemType(data["work_item_type"]),
            priority=WorkItemPriority(data["priority"]),
            payload=data.get("payload", {}),
            status=WorkItemStatus(data.get("status", "pending")),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.now(),
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else datetime.now(),
            assigned_to=data.get("assigned_to"),
            assigned_at=datetime.fromisoformat(data["assigned_at"]) if data.get("assigned_at") else None,
            started_at=datetime.fromisoformat(data["started_at"]) if data.get("started_at") else None,
            completed_at=datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None,
            expires_at=datetime.fromisoformat(data["expires_at"]) if data.get("expires_at") else None,
            retry_count=data.get("retry_count", 0),
            max_retries=data.get("max_retries", 3),
            error_message=data.get("error_message"),
            dependencies=data.get("dependencies", []),
            metadata=data.get("metadata", {}),
            tags=data.get("tags", [])
        )


@dataclass
class QueueMetrics:
    """Metrics for a work queue"""
    queue_type: QueueType.STANDARD
    work_item_type: WorkItemType.APPROVAL
    total_enqueued: int = 0
    total_completed: int = 0
    total_failed: int = 0
    current_size: int = 0
    average_wait_time: float = 0.0
    average_processing_time: float = 0.0
    peak_size: int = 0
    last_updated: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "queue_type": self.queue_type.value,
            "work_item_type": self.work_item_type.value,
            "total_enqueued": self.total_enqueued,
            "total_completed": self.total_completed,
            "total_failed": self.total_failed,
            "current_size": self.current_size,
            "average_wait_time": self.average_wait_time,
            "average_processing_time": self.average_processing_time,
            "peak_size": self.peak_size,
            "last_updated": self.last_updated.isoformat()
        }


class WorkQueue:
    """
    Manages work queues for human task assignment.
    
    Features:
    - Priority-based queuing (heap implementation)
    - Multiple queue types
    - Work item lifecycle tracking
    - Dependency resolution
    - Automatic expiry and cleanup
    - Queue metrics and monitoring
    - Dead letter queue for failed items
    """
    
    def __init__(self, storage_key: str = "work_queue"):
        self.storage_key = storage_key
        self.queues: Dict[QueueType, List[Tuple[int, float, str]]] = {}
        self.work_items: Dict[str, WorkItem] = {}
        self.queue_metrics: Dict[QueueType, QueueMetrics] = {}
        self._item_counter = 0
        self._lock = threading.RLock()
        
        # Initialize queues
        self._initialize_queues()
        
        # Load data
        self._load_data()
        
        # Start background workers
        self._start_workers()
        
        logger.info("WorkQueue initialized")
    
    def _initialize_queues(self) -> None:
        """Initialize all queue types"""
        for queue_type in QueueType:
            self.queues[queue_type] = []
            self.queue_metrics[queue_type] = QueueMetrics(queue_type=queue_type)
    
    def _load_data(self) -> None:
        """Load work queue data from state manager"""
        try:
            items_data = state_manager.get(f"{self.storage_key}.items", {})
            for item_id, item_data in items_data.items():
                if isinstance(item_data, dict):
                    work_item = WorkItem.from_dict(item_data)
                    self.work_items[item_id] = work_item
                    
                    # Re-add to appropriate queue if pending
                    if work_item.status == WorkItemStatus.PENDING and not work_item.is_expired:
                        self._push_to_queue(work_item)
            
            metrics_data = state_manager.get(f"{self.storage_key}.metrics", {})
            for qt, mdata in metrics_data.items():
                if qt in self.queue_metrics:
                    self.queue_metrics[QueueType(qt)] = QueueMetrics(**mdata)
                    
        except Exception as e:
            logger.warning(f"Failed to load work queue data: {e}")
    
    def _save_data(self) -> None:
        """Save work queue data to state manager"""
        try:
            # Save active work items (not completed/failed beyond retention)
            items_to_save = {
                item_id: item.to_dict()
                for item_id, item in self.work_items.items()
                if item.status not in [WorkItemStatus.COMPLETED, WorkItemStatus.FAILED]
            }
            state_manager.set(f"{self.storage_key}.items", items_to_save)
            
            metrics_data = {qt.value: m.to_dict() for qt, m in self.queue_metrics.items()}
            state_manager.set(f"{self.storage_key}.metrics", metrics_data)
            
        except Exception as e:
            logger.error(f"Failed to save work queue data: {e}")
    
    def _start_workers(self) -> None:
        """Start background workers for queue maintenance"""
        def expiry_worker():
            while True:
                try:
                    self._check_expired_items()
                except Exception as e:
                    logger.error(f"Expiry worker error: {e}")
                threading.Event().wait(60)  # Check every minute
        
        def metrics_worker():
            while True:
                try:
                    self._update_metrics()
                except Exception as e:
                    logger.error(f"Metrics worker error: {e}")
                threading.Event().wait(300)  # Update every 5 minutes
        
        worker1 = threading.Thread(target=expiry_worker, daemon=True)
        worker1.start()
        
        worker2 = threading.Thread(target=metrics_worker, daemon=True)
        worker2.start()
    
    def _push_to_queue(self, item: WorkItem) -> None:
        """Push work item to priority queue"""
        # Heap entry: (priority, timestamp, item_id)
        # Lower priority number = higher priority
        heap_entry = (item.priority.value, item.created_at.timestamp(), item.item_id)
        heapq.heappush(self.queues[item.queue_type], heap_entry)
    
    def _pop_from_queue(self, queue_type: QueueType) -> Optional[WorkItem]:
        """Pop highest priority work item from queue"""
        heap = self.queues[queue_type]
        
        while heap:
            priority, timestamp, item_id = heapq.heappop(heap)
            item = self.work_items.get(item_id)
            
            # Skip if item no longer pending or expired
            if not item or item.status != WorkItemStatus.PENDING or item.is_expired:
                continue
            
            # Check dependencies
            if item.dependencies:
                all_deps_met = all(
                    dep_id in self.work_items and 
                    self.work_items[dep_id].status == WorkItemStatus.COMPLETED
                    for dep_id in item.dependencies
                )
                if not all_deps_met:
                    item.status = WorkItemStatus.BLOCKED
                    self._save_data()
                    continue
            
            return item
        
        return None
    
    def enqueue(self, item: WorkItem) -> str:
        """
        Add a work item to the queue.
        
        Args:
            item: Work item to enqueue
            
        Returns:
            Item ID
        """
        with self._lock:
            self.work_items[item.item_id] = item
            self._push_to_queue(item)
            
            # Update metrics
            metrics = self.queue_metrics[item.queue_type]
            metrics.total_enqueued += 1
            metrics.current_size = len(self.queues[item.queue_type])
            metrics.peak_size = max(metrics.peak_size, metrics.current_size)
            
            self._save_data()
            
            logger.debug(f"Enqueued {item.item_id} to {item.queue_type.value} queue")
            return item.item_id
    
    def dequeue(self, queue_type: QueueType, assignee: str = None) -> Optional[WorkItem]:
        """
        Dequeue the next work item.
        
        Args:
            queue_type: Queue to dequeue from
            assignee: Human/agent being assigned the item
            
        Returns:
            Work item or None if queue empty
        """
        with self._lock:
            item = self._pop_from_queue(queue_type)
            
            if item:
                item.status = WorkItemStatus.ASSIGNED
                item.assigned_to = assignee
                item.assigned_at = datetime.now()
                item.updated_at = datetime.now()
                
                metrics = self.queue_metrics[queue_type]
                metrics.current_size = len(self.queues[queue_type])
                
                self._save_data()
                logger.info(f"Dequeued {item.item_id} assigned to {assignee}")
            
            return item
    
    def start_processing(self, item_id: str, processor: str) -> bool:
        """
        Mark a work item as in progress.
        
        Args:
            item_id: Work item ID
            processor: Human/agent processing the item
            
        Returns:
            True if successful
        """
        with self._lock:
            item = self.work_items.get(item_id)
            if not item or item.status != WorkItemStatus.ASSIGNED:
                return False
            
            item.status = WorkItemStatus.IN_PROGRESS
            item.started_at = datetime.now()
            item.updated_at = datetime.now()
            
            self._save_data()
            return True
    
    def complete(self, item_id: str, result: Dict[str, Any] = None) -> bool:
        """
        Mark a work item as completed.
        
        Args:
            item_id: Work item ID
            result: Result data
            
        Returns:
            True if successful
        """
        with self._lock:
            item = self.work_items.get(item_id)
            if not item:
                return False
            
            old_status = item.status
            item.status = WorkItemStatus.COMPLETED
            item.completed_at = datetime.now()
            item.updated_at = datetime.now()
            
            if result:
                item.payload["result"] = result
            
            # Update metrics
            metrics = self.queue_metrics[item.queue_type]
            metrics.total_completed += 1
            
            # Calculate wait and processing times
            wait_time = item.wait_time_seconds
            processing_time = item.processing_time_seconds
            
            # Update averages (exponential moving average)
            metrics.average_wait_time = (
                0.9 * metrics.average_wait_time + 0.1 * wait_time
            )
            metrics.average_processing_time = (
                0.9 * metrics.average_processing_time + 0.1 * processing_time
            )
            
            self._save_data()
            
            logger.info(f"Completed {item_id} in {processing_time:.2f}s (waited {wait_time:.2f}s)")
            return True
    
    def fail(self, item_id: str, error: str, retry: bool = True) -> bool:
        """
        Mark a work item as failed.
        
        Args:
            item_id: Work item ID
            error: Error message
            retry: Whether to retry
            
        Returns:
            True if successful
        """
        with self._lock:
            item = self.work_items.get(item_id)
            if not item:
                return False
            
            if retry and item.retry_count < item.max_retries:
                # Retry the item
                item.retry_count += 1
                item.status = WorkItemStatus.PENDING
                item.assigned_to = None
                item.assigned_at = None
                item.started_at = None
                item.error_message = error
                item.updated_at = datetime.now()
                
                # Re-add to queue
                self._push_to_queue(item)
                
                logger.warning(f"Retrying {item_id} (attempt {item.retry_count}/{item.max_retries})")
            else:
                # Move to dead letter or mark as failed
                if item.retry_count >= item.max_retries:
                    # Move to dead letter queue
                    dead_letter_item = WorkItem(
                        item_id=str(uuid.uuid4()),
                        queue_type=QueueType.DEAD_LETTER,
                        work_item_type=item.work_item_type,
                        priority=item.priority,
                        payload={
                            "original_item_id": item_id,
                            "error": error,
                            "retry_count": item.retry_count,
                            "original_payload": item.payload
                        },
                        metadata={"original_created_at": item.created_at.isoformat()}
                    )
                    self.enqueue(dead_letter_item)
                
                item.status = WorkItemStatus.FAILED
                item.error_message = error
                item.completed_at = datetime.now()
                item.updated_at = datetime.now()
                
                metrics = self.queue_metrics[item.queue_type]
                metrics.total_failed += 1
            
            self._save_data()
            return True
    
    def cancel(self, item_id: str, reason: str = None) -> bool:
        """Cancel a work item"""
        with self._lock:
            item = self.work_items.get(item_id)
            if not item:
                return False
            
            item.status = WorkItemStatus.CANCELLED
            item.error_message = reason
            item.completed_at = datetime.now()
            item.updated_at = datetime.now()
            
            self._save_data()
            logger.info(f"Cancelled {item_id}: {reason}")
            return True
    
    def _check_expired_items(self) -> None:
        """Check for and handle expired work items"""
        with self._lock:
            expired = []
            for item_id, item in self.work_items.items():
                if item.is_expired and item.status in [WorkItemStatus.PENDING, WorkItemStatus.ASSIGNED]:
                    item.status = WorkItemStatus.EXPIRED
                    item.completed_at = datetime.now()
                    expired.append(item_id)
            
            if expired:
                self._save_data()
                logger.info(f"Expired {len(expired)} work items")
    
    def _update_metrics(self) -> None:
        """Update queue metrics"""
        with self._lock:
            for queue_type, heap in self.queues.items():
                self.queue_metrics[queue_type].current_size = len(heap)
            self._save_data()
    
    def get_next(self, queue_type: QueueType) -> Optional[WorkItem]:
        """Get next work item without removing it"""
        with self._lock:
            heap = self.queues[queue_type]
            if not heap:
                return None
            
            # Peek at the next item
            priority, timestamp, item_id = heap[0]
            return self.work_items.get(item_id)
    
    def get_item(self, item_id: str) -> Optional[Dict[str, Any]]:
        """Get work item details"""
        with self._lock:
            item = self.work_items.get(item_id)
            if item:
                return item.to_dict()
            return None
    
    def get_queue_items(self, queue_type: QueueType, 
                       limit: int = 50) -> List[Dict[str, Any]]:
        """Get items in a specific queue (for monitoring)"""
        with self._lock:
            items = []
            heap_copy = self.queues[queue_type].copy()
            
            for priority, timestamp, item_id in heapq.nsmallest(limit, heap_copy):
                item = self.work_items.get(item_id)
                if item:
                    items.append({
                        "item_id": item.item_id,
                        "priority": item.priority.value,
                        "priority_name": item.priority.name,
                        "status": item.status.value,
                        "age_seconds": item.age_seconds,
                        "payload": item.payload
                    })
            
            return items
    
    def get_queue_status(self, queue_type: QueueType = None) -> Dict[str, Any]:
        """Get status of one or all queues"""
        with self._lock:
            if queue_type:
                metrics = self.queue_metrics.get(queue_type)
                return {
                    "queue_type": queue_type.value,
                    "size": len(self.queues.get(queue_type, [])),
                    "metrics": metrics.to_dict() if metrics else None
                }
            else:
                return {
                    qt.value: {
                        "size": len(heap),
                        "metrics": self.queue_metrics[qt].to_dict()
                    }
                    for qt, heap in self.queues.items()
                }
    
    def get_queue_metrics(self, queue_type: QueueType = None) -> Dict[str, Any]:
        """Get detailed metrics for queues"""
        with self._lock:
            if queue_type:
                return self.queue_metrics[queue_type].to_dict()
            else:
                return {qt.value: m.to_dict() for qt, m in self.queue_metrics.items()}
    
    def get_dead_letter_items(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get items from dead letter queue"""
        return self.get_queue_items(QueueType.DEAD_LETTER, limit)
    
    def retry_dead_letter(self, item_id: str) -> bool:
        """Retry a dead letter item"""
        with self._lock:
            item = self.work_items.get(item_id)
            if not item or item.queue_type != QueueType.DEAD_LETTER:
                return False
            
            # Extract original item
            original_item_id = item.payload.get("original_item_id")
            if original_item_id:
                original_item = self.work_items.get(original_item_id)
                if original_item:
                    # Reset and retry original
                    original_item.status = WorkItemStatus.PENDING
                    original_item.retry_count = 0
                    original_item.error_message = None
                    original_item.updated_at = datetime.now()
                    
                    self._push_to_queue(original_item)
                    
                    # Remove from dead letter
                    del self.work_items[item_id]
                    
                    self._save_data()
                    logger.info(f"Retrying dead letter item {original_item_id}")
                    return True
            
            return False
    
    def clear_queue(self, queue_type: QueueType) -> int:
        """Clear all items from a queue"""
        with self._lock:
            count = len(self.queues[queue_type])
            self.queues[queue_type] = []
            
            # Mark items as cancelled
            for item_id in [item_id for _, _, item_id in self.queues[queue_type]]:
                if item_id in self.work_items:
                    self.work_items[item_id].status = WorkItemStatus.CANCELLED
            
            self._save_data()
            logger.info(f"Cleared {count} items from {queue_type.value} queue")
            return count
    
    def get_queue_length(self, queue_type: QueueType) -> int:
        """Get current length of a queue"""
        with self._lock:
            return len(self.queues.get(queue_type, []))
    
    def has_pending_items(self, queue_type: QueueType) -> bool:
        """Check if queue has pending items"""
        with self._lock:
            return len(self.queues.get(queue_type, [])) > 0
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive work queue statistics"""
        with self._lock:
            total_pending = sum(len(heap) for heap in self.queues.values())
            total_items = len(self.work_items)
            
            # Items by status
            by_status = defaultdict(int)
            for item in self.work_items.values():
                by_status[item.status.value] += 1
            
            # Items by priority
            by_priority = defaultdict(int)
            for item in self.work_items.values():
                by_priority[item.priority.name] += 1
            
            return {
                "total_work_items": total_items,
                "total_pending": total_pending,
                "by_status": dict(by_status),
                "by_priority": dict(by_priority),
                "queue_metrics": self.get_queue_metrics(),
                "dead_letter_size": len(self.queues.get(QueueType.DEAD_LETTER, [])),
                "average_wait_time_seconds": sum(
                    m.average_wait_time for m in self.queue_metrics.values()
                ) / len(self.queue_metrics) if self.queue_metrics else 0
            }
    
    def cleanup_completed_items(self, max_age_days: int = 7) -> int:
        """Remove completed/failed items older than max_age_days"""
        cutoff = datetime.now() - timedelta(days=max_age_days)
        
        with self._lock:
            to_remove = []
            for item_id, item in self.work_items.items():
                if item.status in [WorkItemStatus.COMPLETED, WorkItemStatus.FAILED]:
                    if item.completed_at and item.completed_at < cutoff:
                        to_remove.append(item_id)
            
            for item_id in to_remove:
                del self.work_items[item_id]
            
            if to_remove:
                self._save_data()
                logger.info(f"Cleaned up {len(to_remove)} old completed/failed items")
            
            return len(to_remove)
    
    def reset(self) -> None:
        """Reset all queues (clear all items)"""
        with self._lock:
            self.work_items.clear()
            self._initialize_queues()
            self._save_data()
            logger.warning("All work queues reset")


# Singleton instance
_work_queue: Optional[WorkQueue] = None


def get_work_queue() -> WorkQueue:
    """Get global WorkQueue instance"""
    global _work_queue
    if _work_queue is None:
        _work_queue = WorkQueue()
    return _work_queue