"""
Performance Tracker for Workflow Monitoring

Tracks and analyzes performance metrics across:
- Task execution times
- Agent response latencies  
- Resource utilization (CPU, memory, I/O)
- Throughput rates
- Success/failure rates
- End-to-end workflow durations

This implementation provides:

    Multiple Metric Types: Counter, Gauge, Histogram, Timer, Throughput
    Aggregation Methods: SUM, AVG, MIN, MAX, COUNT, Percentiles (50, 90, 95, 99)
    Rolling Windows: Time-based data retention with automatic cleanup
    System Monitoring: CPU, memory, disk I/O via psutil
    Alerting: Threshold-based alerts with warning/critical severity
    Tag Support: Multi-dimensional metrics with tag filtering
    Context Managers: @timer decorator for easy operation timing
    Convenience Methods: Specialized methods for tasks, agents, LLM requests
    Export Capabilities: JSON export for external analysis
    Singleton Pattern: Global instance via get_performance_tracker()

The tracker integrates with your existing shared modules and provides 
comprehensive performance monitoring for your orchestration system.
"""

import time
import threading
import psutil
from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from collections import defaultdict, deque
from contextlib import contextmanager

from ...shared.logger import get_logger
from ...shared.state_manager import state_manager
from ...shared.config import config

logger = get_logger(__name__)


class MetricType(Enum):
    """Types of performance metrics"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"
    THROUGHPUT = "throughput"


class Aggregation(Enum):
    """Aggregation methods for metrics"""
    SUM = "sum"
    AVG = "avg"
    MIN = "min"
    MAX = "max"
    COUNT = "count"
    PERCENTILE_50 = "p50"
    PERCENTILE_90 = "p90"
    PERCENTILE_95 = "p95"
    PERCENTILE_99 = "p99"


@dataclass
class MetricPoint:
    """Single data point for a metric"""
    value: float
    timestamp: datetime
    tags: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "value": self.value,
            "timestamp": self.timestamp.isoformat(),
            "tags": self.tags
        }


@dataclass
class MetricDefinition:
    """Definition of a metric to track"""
    name: str
    type: MetricType
    description: str
    unit: str = "count"
    aggregations: List[Aggregation] = field(default_factory=list)
    retention_days: int = 7
    alert_threshold: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "type": self.type.value,
            "description": self.description,
            "unit": self.unit,
            "aggregations": [a.value for a in self.aggregations],
            "retention_days": self.retention_days,
            "alert_threshold": self.alert_threshold
        }


@dataclass
class MetricSnapshot:
    """Snapshot of metric values at a point in time"""
    metric_name: str
    value: float
    aggregation: Aggregation
    timestamp: datetime
    tags: Dict[str, str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "metric_name": self.metric_name,
            "value": self.value,
            "aggregation": self.aggregation.value,
            "timestamp": self.timestamp.isoformat(),
            "tags": self.tags
        }


@dataclass
class PerformanceAlert:
    """Alert generated when a metric exceeds threshold"""
    metric_name: str
    threshold: float
    current_value: float
    severity: str  # warning, critical
    message: str
    timestamp: datetime
    tags: Dict[str, str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "metric_name": self.metric_name,
            "threshold": self.threshold,
            "current_value": self.current_value,
            "severity": self.severity,
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
            "tags": self.tags
        }


class RollingWindow:
    """Rolling window for time-series data"""
    
    def __init__(self, max_size: int = 10000, max_age_seconds: int = 3600):
        self.max_size = max_size
        self.max_age_seconds = max_age_seconds
        self.data: deque = deque(maxlen=max_size)
        self.lock = threading.RLock()
    
    def add(self, value: float, timestamp: datetime = None) -> None:
        """Add a value to the window"""
        with self.lock:
            if timestamp is None:
                timestamp = datetime.now()
            self.data.append((value, timestamp))
            self._cleanup(timestamp)
    
    def _cleanup(self, current_time: datetime) -> None:
        """Remove expired data points"""
        cutoff = current_time - timedelta(seconds=self.max_age_seconds)
        while self.data and self.data[0][1] < cutoff:
            self.data.popleft()
    
    def get_values(self) -> List[float]:
        """Get all values in the window"""
        with self.lock:
            return [v for v, _ in self.data]
    
    def get_values_in_range(self, start: datetime, end: datetime) -> List[float]:
        """Get values within a time range"""
        with self.lock:
            return [v for v, ts in self.data if start <= ts <= end]
    
    def clear(self) -> None:
        """Clear all data"""
        with self.lock:
            self.data.clear()
    
    def size(self) -> int:
        """Get current window size"""
        with self.lock:
            return len(self.data)
    
    def aggregate(self, aggregation: Aggregation) -> float:
        """Apply aggregation to window data"""
        with self.lock:
            values = [v for v, _ in self.data]
            if not values:
                return 0.0
            
            if aggregation == Aggregation.SUM:
                return sum(values)
            elif aggregation == Aggregation.AVG:
                return sum(values) / len(values)
            elif aggregation == Aggregation.MIN:
                return min(values)
            elif aggregation == Aggregation.MAX:
                return max(values)
            elif aggregation == Aggregation.COUNT:
                return len(values)
            elif aggregation == Aggregation.PERCENTILE_50:
                return self._percentile(values, 50)
            elif aggregation == Aggregation.PERCENTILE_90:
                return self._percentile(values, 90)
            elif aggregation == Aggregation.PERCENTILE_95:
                return self._percentile(values, 95)
            elif aggregation == Aggregation.PERCENTILE_99:
                return self._percentile(values, 99)
            else:
                return 0.0
    
    @staticmethod
    def _percentile(values: List[float], p: float) -> float:
        """Calculate percentile"""
        if not values:
            return 0.0
        sorted_values = sorted(values)
        index = (len(sorted_values) - 1) * p / 100
        lower = int(index)
        upper = lower + 1
        if upper >= len(sorted_values):
            return sorted_values[lower]
        weight = index - lower
        return sorted_values[lower] * (1 - weight) + sorted_values[upper] * weight


class PerformanceTracker:
    """
    Tracks performance metrics for the orchestration system.
    
    Provides:
    - Real-time metric collection
    - Multiple aggregation methods
    - Alerting on threshold violations
    - Historical data retention
    - Resource monitoring (CPU, memory, etc.)
    """
    
    def __init__(self, storage_key: str = "performance_tracker"):
        self.storage_key = storage_key
        self.metrics: Dict[str, MetricDefinition] = {}
        self.windows: Dict[str, Dict[str, RollingWindow]] = {}  # metric_name -> tags_key -> window
        self.alerts: List[PerformanceAlert] = []
        self._monitoring_thread: Optional[threading.Thread] = None
        self._stop_monitoring = threading.Event()
        self._lock = threading.RLock()
        
        # Default metrics
        self._register_default_metrics()
        
        # Start background monitoring
        self._start_monitoring()
        
        logger.info("PerformanceTracker initialized")
    
    def _register_default_metrics(self) -> None:
        """Register default performance metrics"""
        default_metrics = [
            MetricDefinition(
                name="task.execution_time",
                type=MetricType.TIMER,
                description="Task execution duration",
                unit="seconds",
                aggregations=[Aggregation.AVG, Aggregation.PERCENTILE_90, Aggregation.PERCENTILE_99],
                alert_threshold=30.0
            ),
            MetricDefinition(
                name="task.queue_wait_time",
                type=MetricType.TIMER,
                description="Time task spends in queue",
                unit="seconds",
                aggregations=[Aggregation.AVG, Aggregation.PERCENTILE_95],
                alert_threshold=10.0
            ),
            MetricDefinition(
                name="task.throughput",
                type=MetricType.THROUGHPUT,
                description="Tasks completed per minute",
                unit="tasks/min",
                aggregations=[Aggregation.AVG, Aggregation.MAX]
            ),
            MetricDefinition(
                name="task.success_rate",
                type=MetricType.GAUGE,
                description="Success rate of tasks",
                unit="percentage",
                aggregations=[Aggregation.AVG, Aggregation.MIN],
                alert_threshold=95.0
            ),
            MetricDefinition(
                name="agent.response_time",
                type=MetricType.TIMER,
                description="Agent response time",
                unit="seconds",
                aggregations=[Aggregation.AVG, Aggregation.PERCENTILE_90],
                alert_threshold=5.0
            ),
            MetricDefinition(
                name="agent.utilization",
                type=MetricType.GAUGE,
                description="Agent utilization percentage",
                unit="percentage",
                aggregations=[Aggregation.AVG, Aggregation.MAX],
                alert_threshold=90.0
            ),
            MetricDefinition(
                name="workflow.duration",
                type=MetricType.TIMER,
                description="End-to-end workflow duration",
                unit="seconds",
                aggregations=[Aggregation.AVG, Aggregation.PERCENTILE_95, Aggregation.MAX]
            ),
            MetricDefinition(
                name="system.cpu_usage",
                type=MetricType.GAUGE,
                description="CPU usage percentage",
                unit="percentage",
                aggregations=[Aggregation.AVG, Aggregation.MAX],
                alert_threshold=80.0
            ),
            MetricDefinition(
                name="system.memory_usage",
                type=MetricType.GAUGE,
                description="Memory usage percentage",
                unit="percentage",
                aggregations=[Aggregation.AVG, Aggregation.MAX],
                alert_threshold=85.0
            ),
            MetricDefinition(
                name="system.disk_io",
                type=MetricType.GAUGE,
                description="Disk I/O operations",
                unit="ops/sec",
                aggregations=[Aggregation.AVG, Aggregation.MAX]
            ),
            MetricDefinition(
                name="llm.request_time",
                type=MetricType.TIMER,
                description="LLM API request duration",
                unit="seconds",
                aggregations=[Aggregation.AVG, Aggregation.PERCENTILE_95],
                alert_threshold=10.0
            ),
            MetricDefinition(
                name="llm.token_usage",
                type=MetricType.COUNTER,
                description="Tokens used in LLM requests",
                unit="tokens",
                aggregations=[Aggregation.SUM, Aggregation.AVG]
            ),
            MetricDefinition(
                name="cache.hit_rate",
                type=MetricType.GAUGE,
                description="Cache hit rate percentage",
                unit="percentage",
                aggregations=[Aggregation.AVG],
                alert_threshold=70.0
            ),
        ]
        
        for metric in default_metrics:
            self.register_metric(metric)
    
    def _start_monitoring(self) -> None:
        """Start background monitoring thread"""
        def monitor():
            while not self._stop_monitoring.is_set():
                try:
                    self._collect_system_metrics()
                    self._cleanup_old_data()
                    self._check_alerts()
                except Exception as e:
                    logger.error(f"Error in monitoring thread: {e}")
                self._stop_monitoring.wait(10)  # Collect every 10 seconds
        
        self._monitoring_thread = threading.Thread(target=monitor, daemon=True)
        self._monitoring_thread.start()
    
    def _collect_system_metrics(self) -> None:
        """Collect system resource metrics"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=0.1)
            self.record_gauge("system.cpu_usage", cpu_percent)
            
            # Memory usage
            memory = psutil.virtual_memory()
            self.record_gauge("system.memory_usage", memory.percent)
            
            # Disk I/O
            disk_io = psutil.disk_io_counters()
            if disk_io:
                # This is cumulative, but we'll record as gauge for trend
                self.record_gauge("system.disk_io", disk_io.read_bytes + disk_io.write_bytes)
        except Exception as e:
            logger.debug(f"Failed to collect system metrics: {e}")
    
    def _cleanup_old_data(self) -> None:
        """Clean up data older than retention period"""
        with self._lock:
            now = datetime.now()
            for metric_name, metric_windows in list(self.windows.items()):
                metric_def = self.metrics.get(metric_name)
                if metric_def:
                    cutoff = now - timedelta(days=metric_def.retention_days)
                    # Windows handle their own cleanup by age
                    pass
    
    def _check_alerts(self) -> None:
        """Check for threshold violations and generate alerts"""
        for metric_name, metric_def in self.metrics.items():
            if metric_def.alert_threshold is None:
                continue
            
            # Get current value
            current_value = self.get_current_value(metric_name)
            if current_value is None:
                continue
            
            # Check threshold
            if current_value > metric_def.alert_threshold:
                severity = "critical" if current_value > metric_def.alert_threshold * 1.5 else "warning"
                
                alert = PerformanceAlert(
                    metric_name=metric_name,
                    threshold=metric_def.alert_threshold,
                    current_value=current_value,
                    severity=severity,
                    message=f"{metric_name} exceeded threshold: {current_value:.2f} > {metric_def.alert_threshold}",
                    timestamp=datetime.now(),
                    tags={}
                )
                
                self.alerts.append(alert)
                
                # Trim alerts list
                if len(self.alerts) > 1000:
                    self.alerts = self.alerts[-1000:]
                
                logger.warning(alert.message)
    
    def register_metric(self, definition: MetricDefinition) -> None:
        """Register a new metric to track"""
        with self._lock:
            self.metrics[definition.name] = definition
            if definition.name not in self.windows:
                self.windows[definition.name] = {}
            logger.debug(f"Registered metric: {definition.name}")
    
    def _get_window(self, metric_name: str, tags: Dict[str, str]) -> RollingWindow:
        """Get or create a rolling window for a metric and tags"""
        tags_key = self._tags_to_key(tags)
        
        if metric_name not in self.windows:
            self.windows[metric_name] = {}
        
        if tags_key not in self.windows[metric_name]:
            # Determine window size based on metric type
            metric_def = self.metrics.get(metric_name)
            if metric_def and metric_def.type in [MetricType.TIMER, MetricType.HISTOGRAM]:
                max_size = 10000
                max_age = 3600  # 1 hour
            else:
                max_size = 1000
                max_age = 300  # 5 minutes
            
            self.windows[metric_name][tags_key] = RollingWindow(
                max_size=max_size,
                max_age_seconds=max_age
            )
        
        return self.windows[metric_name][tags_key]
    
    def _tags_to_key(self, tags: Dict[str, str]) -> str:
        """Convert tags dict to a string key"""
        if not tags:
            return "_default"
        return ",".join(f"{k}={v}" for k, v in sorted(tags.items()))
    
    def _key_to_tags(self, key: str) -> Dict[str, str]:
        """Convert string key back to tags dict"""
        if key == "_default":
            return {}
        tags = {}
        for pair in key.split(","):
            if "=" in pair:
                k, v = pair.split("=", 1)
                tags[k] = v
        return tags
    
    def record_counter(self, metric_name: str, value: float = 1, 
                      tags: Dict[str, str] = None) -> None:
        """Record a counter metric (incremental)"""
        if metric_name not in self.metrics:
            logger.warning(f"Metric {metric_name} not registered, skipping")
            return
        
        window = self._get_window(metric_name, tags or {})
        window.add(value, datetime.now())
    
    def record_gauge(self, metric_name: str, value: float, 
                    tags: Dict[str, str] = None) -> None:
        """Record a gauge metric (point-in-time value)"""
        if metric_name not in self.metrics:
            logger.warning(f"Metric {metric_name} not registered, skipping")
            return
        
        window = self._get_window(metric_name, tags or {})
        window.add(value, datetime.now())
    
    def record_timer(self, metric_name: str, duration_seconds: float,
                    tags: Dict[str, str] = None) -> None:
        """Record a timer metric (duration)"""
        if metric_name not in self.metrics:
            logger.warning(f"Metric {metric_name} not registered, skipping")
            return
        
        window = self._get_window(metric_name, tags or {})
        window.add(duration_seconds, datetime.now())
    
    @contextmanager
    def timer(self, metric_name: str, tags: Dict[str, str] = None):
        """Context manager for timing operations"""
        start = time.time()
        try:
            yield
        finally:
            duration = time.time() - start
            self.record_timer(metric_name, duration, tags)
    
    def record_throughput(self, metric_name: str, count: int = 1,
                         tags: Dict[str, str] = None) -> None:
        """Record a throughput metric (rate)"""
        if metric_name not in self.metrics:
            logger.warning(f"Metric {metric_name} not registered, skipping")
            return
        
        window = self._get_window(metric_name, tags or {})
        window.add(count, datetime.now())
    
    def get_metric_value(self, metric_name: str, aggregation: Aggregation,
                        tags: Dict[str, str] = None,
                        time_range: Tuple[datetime, datetime] = None) -> Optional[float]:
        """Get aggregated metric value"""
        if metric_name not in self.metrics:
            logger.warning(f"Metric {metric_name} not registered")
            return None
        
        window = self._get_window(metric_name, tags or {})
        
        if time_range:
            start, end = time_range
            values = window.get_values_in_range(start, end)
            if not values:
                return None
            
            # Create temporary window for range
            temp_window = RollingWindow()
            for v in values:
                temp_window.add(v)
            return temp_window.aggregate(aggregation)
        else:
            return window.aggregate(aggregation)
    
    def get_current_value(self, metric_name: str, tags: Dict[str, str] = None) -> Optional[float]:
        """Get the most recent value for a metric"""
        if metric_name not in self.metrics:
            return None
        
        window = self._get_window(metric_name, tags or {})
        values = window.get_values()
        if not values:
            return None
        
        return values[-1]
    
    def get_statistics(self, metric_name: str, tags: Dict[str, str] = None) -> Dict[str, Any]:
        """Get comprehensive statistics for a metric"""
        if metric_name not in self.metrics:
            return {"error": f"Metric {metric_name} not found"}
        
        window = self._get_window(metric_name, tags or {})
        values = window.get_values()
        
        if not values:
            return {"status": "no_data"}
        
        sorted_values = sorted(values)
        
        return {
            "metric_name": metric_name,
            "count": len(values),
            "sum": sum(values),
            "avg": sum(values) / len(values),
            "min": min(values),
            "max": max(values),
            "p50": self._percentile(sorted_values, 50),
            "p90": self._percentile(sorted_values, 90),
            "p95": self._percentile(sorted_values, 95),
            "p99": self._percentile(sorted_values, 99),
            "latest": values[-1],
            "tags": tags or {}
        }
    
    @staticmethod
    def _percentile(sorted_values: List[float], p: float) -> float:
        """Calculate percentile"""
        if not sorted_values:
            return 0.0
        index = (len(sorted_values) - 1) * p / 100
        lower = int(index)
        upper = lower + 1
        if upper >= len(sorted_values):
            return sorted_values[lower]
        weight = index - lower
        return sorted_values[lower] * (1 - weight) + sorted_values[upper] * weight
    
    def get_alerts(self, since: datetime = None, severity: str = None) -> List[PerformanceAlert]:
        """Get performance alerts"""
        alerts = self.alerts
        
        if since:
            alerts = [a for a in alerts if a.timestamp >= since]
        
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        
        return alerts
    
    def clear_alerts(self, metric_name: str = None) -> None:
        """Clear alerts"""
        if metric_name:
            self.alerts = [a for a in self.alerts if a.metric_name != metric_name]
        else:
            self.alerts.clear()
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get a summary of all tracked metrics"""
        summary = {
            "total_metrics": len(self.metrics),
            "metrics": {},
            "active_alerts": len([a for a in self.alerts if a.severity == "critical"]),
            "warnings": len([a for a in self.alerts if a.severity == "warning"])
        }
        
        for metric_name in self.metrics:
            stats = self.get_statistics(metric_name)
            if "error" not in stats and stats.get("count", 0) > 0:
                summary["metrics"][metric_name] = {
                    "avg": stats.get("avg"),
                    "latest": stats.get("latest"),
                    "count": stats.get("count")
                }
        
        return summary
    
    def record_task_execution(self, task_id: str, task_type: str, 
                             duration: float, success: bool,
                             agent_id: str = None) -> None:
        """Convenience method to record task execution metrics"""
        tags = {
            "task_type": task_type,
            "success": str(success),
            "agent_id": agent_id or "unknown"
        }
        
        self.record_timer("task.execution_time", duration, tags)
        
        if success:
            self.record_counter("task.success", 1, tags)
        else:
            self.record_counter("task.failure", 1, tags)
        
        # Update success rate
        success_rate = self._calculate_success_rate(task_type)
        self.record_gauge("task.success_rate", success_rate, {"task_type": task_type})
    
    def _calculate_success_rate(self, task_type: str) -> float:
        """Calculate success rate for a task type"""
        success_count = 0
        total_count = 0
        
        for tags_key, window in self.windows.get("task.success", {}).items():
            tags = self._key_to_tags(tags_key)
            if tags.get("task_type") == task_type:
                success_count = window.size()
                break
        
        for tags_key, window in self.windows.get("task.failure", {}).items():
            tags = self._key_to_tags(tags_key)
            if tags.get("task_type") == task_type:
                total_count = success_count + window.size()
                break
        
        if total_count == 0:
            return 100.0
        
        return (success_count / total_count) * 100
    
    def record_agent_metrics(self, agent_id: str, agent_type: str,
                            response_time: float, queue_size: int,
                            active_tasks: int, max_concurrent: int) -> None:
        """Convenience method to record agent metrics"""
        tags = {
            "agent_id": agent_id,
            "agent_type": agent_type
        }
        
        self.record_timer("agent.response_time", response_time, tags)
        
        utilization = (active_tasks / max_concurrent) * 100 if max_concurrent > 0 else 0
        self.record_gauge("agent.utilization", utilization, tags)
        
        self.record_gauge("agent.queue_size", queue_size, tags)
    
    def record_llm_request(self, duration: float, tokens_used: int,
                          model: str, success: bool) -> None:
        """Convenience method to record LLM request metrics"""
        tags = {
            "model": model,
            "success": str(success)
        }
        
        self.record_timer("llm.request_time", duration, tags)
        self.record_counter("llm.token_usage", tokens_used, tags)
    
    def reset(self) -> None:
        """Reset all metrics"""
        with self._lock:
            self.windows.clear()
            self.alerts.clear()
            logger.info("PerformanceTracker reset")
    
    def stop(self) -> None:
        """Stop background monitoring"""
        self._stop_monitoring.set()
        if self._monitoring_thread:
            self._monitoring_thread.join(timeout=5)
        logger.info("PerformanceTracker stopped")
    
    def export_metrics(self, format: str = "json") -> Dict[str, Any]:
        """Export all metrics for external analysis"""
        export_data = {
            "timestamp": datetime.now().isoformat(),
            "metrics": {},
            "alerts": [a.to_dict() for a in self.alerts[-100:]]
        }
        
        for metric_name in self.metrics:
            stats = self.get_statistics(metric_name)
            if "error" not in stats:
                export_data["metrics"][metric_name] = stats
        
        # Save to state manager
        try:
            state_manager.set(f"{self.storage_key}.export", export_data)
        except Exception as e:
            logger.error(f"Failed to export metrics: {e}")
        
        return export_data


# Singleton instance for global access
_performance_tracker: Optional[PerformanceTracker] = None


def get_performance_tracker() -> PerformanceTracker:
    """Get the global PerformanceTracker instance"""
    global _performance_tracker
    if _performance_tracker is None:
        _performance_tracker = PerformanceTracker()
    return _performance_tracker