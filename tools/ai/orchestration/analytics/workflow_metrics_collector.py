"""
Workflow Metrics Collector for Orchestration Analytics

Collects, aggregates, and analyzes metrics from workflow execution including:
- Workflow duration and throughput
- Step execution times
- Success/failure rates
- Resource consumption
- Queue waiting times
- Dependency resolution times
- Parallel execution efficiency


This implementation provides:

    Workflow Tracking: Track entire workflow executions with start/end times, status, and step counts
    Step Tracking: Monitor individual workflow steps with execution times and retries
    Throughput Metrics: Measure workflows and steps per minute with success rates
    Resource Monitoring: Track CPU, memory, disk, and network usage (via psutil)
    Statistical Aggregation: Group metrics by workflow type and step type
    Performance Analysis: Identify slowest workflows and most failed steps
    Trend Analysis: Historical data for throughput and resource usage (24-hour retention)
    Background Collection: Automatic metrics collection every minute
    Persistence: Save to state_manager with 7-day retention
    Comprehensive Reporting: Generate performance reports with actionable insights

The collector integrates with your orchestration system to provide real-time 
visibility into workflow performance and resource utilization.
"""

import time
import threading
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from collections import defaultdict, deque
from contextlib import contextmanager

from ....shared.logger import get_logger
from ....shared.state_manager import state_manager
from ....shared.config import config

logger = get_logger(__name__)


class WorkflowStatus(Enum):
    """Status of a workflow execution"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class StepStatus(Enum):
    """Status of a workflow step"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    RETRYING = "retrying"


@dataclass
class WorkflowMetrics:
    """Metrics collected for a single workflow execution"""
    workflow_id: str
    workflow_name: str
    status: WorkflowStatus
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    total_steps: int = 0
    completed_steps: int = 0
    failed_steps: int = 0
    skipped_steps: int = 0
    total_retries: int = 0
    resource_usage: Dict[str, float] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def duration_seconds(self) -> float:
        """Calculate workflow duration in seconds"""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        elif self.start_time:
            return (datetime.now() - self.start_time).total_seconds()
        return 0.0
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate (0-100)"""
        if self.total_steps == 0:
            return 100.0
        return (self.completed_steps / self.total_steps) * 100
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "workflow_id": self.workflow_id,
            "workflow_name": self.workflow_name,
            "status": self.status.value,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_seconds": self.duration_seconds,
            "total_steps": self.total_steps,
            "completed_steps": self.completed_steps,
            "failed_steps": self.failed_steps,
            "skipped_steps": self.skipped_steps,
            "total_retries": self.total_retries,
            "success_rate": self.success_rate,
            "resource_usage": self.resource_usage,
            "metadata": self.metadata
        }


@dataclass
class StepMetrics:
    """Metrics collected for a workflow step"""
    step_id: str
    step_name: str
    workflow_id: str
    step_type: str
    status: StepStatus
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    retry_count: int = 0
    input_size: int = 0
    output_size: int = 0
    agent_id: Optional[str] = None
    queue_wait_time: float = 0.0
    dependencies: List[str] = field(default_factory=list)
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def execution_time(self) -> float:
        """Calculate step execution time in seconds"""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        elif self.start_time:
            return (datetime.now() - self.start_time).total_seconds()
        return 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "step_id": self.step_id,
            "step_name": self.step_name,
            "workflow_id": self.workflow_id,
            "step_type": self.step_type,
            "status": self.status.value,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "execution_time": self.execution_time,
            "retry_count": self.retry_count,
            "input_size": self.input_size,
            "output_size": self.output_size,
            "agent_id": self.agent_id,
            "queue_wait_time": self.queue_wait_time,
            "dependencies": self.dependencies,
            "error_message": self.error_message,
            "metadata": self.metadata
        }


@dataclass
class ThroughputMetric:
    """Throughput metrics over a time window"""
    timestamp: datetime
    window_seconds: int
    workflows_started: int
    workflows_completed: int
    steps_executed: int
    average_step_duration: float
    average_workflow_duration: float
    success_rate: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "window_seconds": self.window_seconds,
            "workflows_started": self.workflows_started,
            "workflows_completed": self.workflows_completed,
            "steps_executed": self.steps_executed,
            "average_step_duration": self.average_step_duration,
            "average_workflow_duration": self.average_workflow_duration,
            "success_rate": self.success_rate
        }


@dataclass
class ResourceMetric:
    """Resource usage metrics"""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    disk_io_bytes: int
    network_io_bytes: int
    active_workflows: int
    queued_steps: int
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "cpu_percent": self.cpu_percent,
            "memory_percent": self.memory_percent,
            "disk_io_bytes": self.disk_io_bytes,
            "network_io_bytes": self.network_io_bytes,
            "active_workflows": self.active_workflows,
            "queued_steps": self.queued_steps
        }


class WorkflowMetricsCollector:
    """
    Collects and aggregates metrics from workflow executions.
    
    Features:
    - Real-time workflow and step tracking
    - Throughput analysis
    - Resource monitoring
    - Performance trending
    - SLA tracking
    - Export for visualization
    """
    
    def __init__(self, storage_key: str = "workflow_metrics"):
        self.storage_key = storage_key
        self.workflows: Dict[str, WorkflowMetrics] = {}
        self.steps: Dict[str, StepMetrics] = {}
        self.throughput_history: List[ThroughputMetric] = []
        self.resource_history: List[ResourceMetric] = []
        
        # Aggregated statistics
        self.workflow_type_stats: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            "total_executions": 0,
            "total_duration": 0.0,
            "success_count": 0,
            "failure_count": 0,
            "avg_duration": 0.0,
            "min_duration": float('inf'),
            "max_duration": 0.0
        })
        
        self.step_type_stats: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            "total_executions": 0,
            "total_duration": 0.0,
            "success_count": 0,
            "failure_count": 0,
            "avg_duration": 0.0,
            "min_duration": float('inf'),
            "max_duration": 0.0,
            "total_retries": 0
        })
        
        # Real-time tracking
        self.active_workflows: Set[str] = set()
        self.queued_steps: Set[str] = set()
        self._lock = threading.RLock()
        self._collection_thread: Optional[threading.Thread] = None
        self._stop_collection = threading.Event()
        
        # Load historical data
        self._load_data()
        
        # Start background collection
        self._start_collection()
        
        logger.info("WorkflowMetricsCollector initialized")
    
    def _load_data(self) -> None:
        """Load historical metrics from state manager"""
        try:
            workflows_data = state_manager.get(f"{self.storage_key}.workflows", {})
            for wf_id, wf_data in workflows_data.items():
                # Only load recent workflows (last 7 days)
                if wf_data.get("start_time"):
                    start_time = datetime.fromisoformat(wf_data["start_time"])
                    if (datetime.now() - start_time).days <= 7:
                        self.workflows[wf_id] = self._dict_to_workflow_metrics(wf_data)
            
            throughput_data = state_manager.get(f"{self.storage_key}.throughput", [])
            self.throughput_history = [
                self._dict_to_throughput_metric(t) for t in throughput_data[-1000:]
            ]
            
            resource_data = state_manager.get(f"{self.storage_key}.resources", [])
            self.resource_history = [
                self._dict_to_resource_metric(r) for r in resource_data[-1000:]
            ]
            
            # Rebuild statistics
            self._rebuild_statistics()
            
        except Exception as e:
            logger.warning(f"Failed to load historical data: {e}")
    
    def _dict_to_workflow_metrics(self, data: Dict[str, Any]) -> WorkflowMetrics:
        """Convert dict to WorkflowMetrics"""
        return WorkflowMetrics(
            workflow_id=data["workflow_id"],
            workflow_name=data["workflow_name"],
            status=WorkflowStatus(data["status"]),
            start_time=datetime.fromisoformat(data["start_time"]) if data.get("start_time") else None,
            end_time=datetime.fromisoformat(data["end_time"]) if data.get("end_time") else None,
            total_steps=data.get("total_steps", 0),
            completed_steps=data.get("completed_steps", 0),
            failed_steps=data.get("failed_steps", 0),
            skipped_steps=data.get("skipped_steps", 0),
            total_retries=data.get("total_retries", 0),
            resource_usage=data.get("resource_usage", {}),
            metadata=data.get("metadata", {})
        )
    
    def _dict_to_step_metrics(self, data: Dict[str, Any]) -> StepMetrics:
        """Convert dict to StepMetrics"""
        return StepMetrics(
            step_id=data["step_id"],
            step_name=data["step_name"],
            workflow_id=data["workflow_id"],
            step_type=data["step_type"],
            status=StepStatus(data["status"]),
            start_time=datetime.fromisoformat(data["start_time"]) if data.get("start_time") else None,
            end_time=datetime.fromisoformat(data["end_time"]) if data.get("end_time") else None,
            retry_count=data.get("retry_count", 0),
            input_size=data.get("input_size", 0),
            output_size=data.get("output_size", 0),
            agent_id=data.get("agent_id"),
            queue_wait_time=data.get("queue_wait_time", 0.0),
            dependencies=data.get("dependencies", []),
            error_message=data.get("error_message"),
            metadata=data.get("metadata", {})
        )
    
    def _dict_to_throughput_metric(self, data: Dict[str, Any]) -> ThroughputMetric:
        """Convert dict to ThroughputMetric"""
        return ThroughputMetric(
            timestamp=datetime.fromisoformat(data["timestamp"]),
            window_seconds=data["window_seconds"],
            workflows_started=data["workflows_started"],
            workflows_completed=data["workflows_completed"],
            steps_executed=data["steps_executed"],
            average_step_duration=data["average_step_duration"],
            average_workflow_duration=data["average_workflow_duration"],
            success_rate=data["success_rate"]
        )
    
    def _dict_to_resource_metric(self, data: Dict[str, Any]) -> ResourceMetric:
        """Convert dict to ResourceMetric"""
        return ResourceMetric(
            timestamp=datetime.fromisoformat(data["timestamp"]),
            cpu_percent=data["cpu_percent"],
            memory_percent=data["memory_percent"],
            disk_io_bytes=data["disk_io_bytes"],
            network_io_bytes=data["network_io_bytes"],
            active_workflows=data["active_workflows"],
            queued_steps=data["queued_steps"]
        )
    
    def _rebuild_statistics(self) -> None:
        """Rebuild aggregated statistics from historical data"""
        self.workflow_type_stats.clear()
        self.step_type_stats.clear()
        
        for workflow in self.workflows.values():
            if workflow.status in [WorkflowStatus.COMPLETED, WorkflowStatus.FAILED]:
                self._update_workflow_stats(workflow)
        
        for step in self.steps.values():
            if step.status in [StepStatus.COMPLETED, StepStatus.FAILED]:
                self._update_step_stats(step)
    
    def _start_collection(self) -> None:
        """Start background metrics collection"""
        def collect():
            while not self._stop_collection.is_set():
                try:
                    self._collect_throughput_metrics()
                    self._collect_resource_metrics()
                    self._save_data()
                except Exception as e:
                    logger.error(f"Error in metrics collection: {e}")
                self._stop_collection.wait(60)  # Collect every minute
        
        self._collection_thread = threading.Thread(target=collect, daemon=True)
        self._collection_thread.start()
    
    def _collect_throughput_metrics(self) -> None:
        """Collect throughput metrics for current window"""
        window_seconds = 60
        cutoff = datetime.now() - timedelta(seconds=window_seconds)
        
        workflows_started = sum(1 for w in self.workflows.values() 
                               if w.start_time and w.start_time >= cutoff)
        workflows_completed = sum(1 for w in self.workflows.values() 
                                 if w.end_time and w.end_time >= cutoff)
        
        steps_executed = sum(1 for s in self.steps.values() 
                            if s.end_time and s.end_time >= cutoff)
        
        # Calculate average durations
        recent_workflows = [w for w in self.workflows.values() 
                           if w.end_time and w.end_time >= cutoff]
        avg_workflow_duration = sum(w.duration_seconds for w in recent_workflows) / len(recent_workflows) if recent_workflows else 0
        
        recent_steps = [s for s in self.steps.values() 
                       if s.end_time and s.end_time >= cutoff]
        avg_step_duration = sum(s.execution_time for s in recent_steps) / len(recent_steps) if recent_steps else 0
        
        completed_workflows = [w for w in recent_workflows if w.status == WorkflowStatus.COMPLETED]
        success_rate = (len(completed_workflows) / len(recent_workflows) * 100) if recent_workflows else 100
        
        metric = ThroughputMetric(
            timestamp=datetime.now(),
            window_seconds=window_seconds,
            workflows_started=workflows_started,
            workflows_completed=workflows_completed,
            steps_executed=steps_executed,
            average_step_duration=avg_step_duration,
            average_workflow_duration=avg_workflow_duration,
            success_rate=success_rate
        )
        
        self.throughput_history.append(metric)
        
        # Keep last 24 hours of throughput data
        cutoff_24h = datetime.now() - timedelta(hours=24)
        self.throughput_history = [m for m in self.throughput_history if m.timestamp >= cutoff_24h]
    
    def _collect_resource_metrics(self) -> None:
        """Collect system resource metrics"""
        try:
            import psutil
            
            metric = ResourceMetric(
                timestamp=datetime.now(),
                cpu_percent=psutil.cpu_percent(interval=0.1),
                memory_percent=psutil.virtual_memory().percent,
                disk_io_bytes=psutil.disk_io_counters().read_bytes if psutil.disk_io_counters() else 0,
                network_io_bytes=psutil.net_io_counters().bytes_sent + psutil.net_io_counters().bytes_recv if psutil.net_io_counters() else 0,
                active_workflows=len(self.active_workflows),
                queued_steps=len(self.queued_steps)
            )
            
            self.resource_history.append(metric)
            
            # Keep last 24 hours
            cutoff_24h = datetime.now() - timedelta(hours=24)
            self.resource_history = [m for m in self.resource_history if m.timestamp >= cutoff_24h]
            
        except ImportError:
            logger.debug("psutil not available, skipping resource metrics")
        except Exception as e:
            logger.error(f"Failed to collect resource metrics: {e}")
    
    def _save_data(self) -> None:
        """Save metrics to state manager"""
        try:
            # Save recent workflows (last 7 days)
            cutoff = datetime.now() - timedelta(days=7)
            recent_workflows = {
                wf_id: wf.to_dict() for wf_id, wf in self.workflows.items()
                if wf.start_time and wf.start_time >= cutoff
            }
            state_manager.set(f"{self.storage_key}.workflows", recent_workflows)
            
            # Save throughput and resource history
            state_manager.set(f"{self.storage_key}.throughput", 
                            [t.to_dict() for t in self.throughput_history[-1000:]])
            state_manager.set(f"{self.storage_key}.resources", 
                            [r.to_dict() for r in self.resource_history[-1000:]])
            
        except Exception as e:
            logger.error(f"Failed to save metrics: {e}")
    
    def start_workflow(self, workflow_id: str, workflow_name: str, 
                      metadata: Dict[str, Any] = None) -> None:
        """Start tracking a workflow"""
        with self._lock:
            self.workflows[workflow_id] = WorkflowMetrics(
                workflow_id=workflow_id,
                workflow_name=workflow_name,
                status=WorkflowStatus.RUNNING,
                start_time=datetime.now(),
                metadata=metadata or {}
            )
            self.active_workflows.add(workflow_id)
            logger.debug(f"Started tracking workflow: {workflow_id}")
    
    def complete_workflow(self, workflow_id: str, 
                         status: WorkflowStatus = WorkflowStatus.COMPLETED,
                         resource_usage: Dict[str, float] = None) -> None:
        """Complete workflow tracking"""
        with self._lock:
            if workflow_id not in self.workflows:
                logger.warning(f"Workflow {workflow_id} not found")
                return
            
            workflow = self.workflows[workflow_id]
            workflow.end_time = datetime.now()
            workflow.status = status
            if resource_usage:
                workflow.resource_usage.update(resource_usage)
            
            self.active_workflows.discard(workflow_id)
            
            # Update statistics
            self._update_workflow_stats(workflow)
            
            logger.debug(f"Completed workflow: {workflow_id} in {workflow.duration_seconds:.2f}s")
    
    def _update_workflow_stats(self, workflow: WorkflowMetrics) -> None:
        """Update aggregated workflow statistics"""
        stats = self.workflow_type_stats[workflow.workflow_name]
        stats["total_executions"] += 1
        stats["total_duration"] += workflow.duration_seconds
        stats["avg_duration"] = stats["total_duration"] / stats["total_executions"]
        stats["min_duration"] = min(stats["min_duration"], workflow.duration_seconds)
        stats["max_duration"] = max(stats["max_duration"], workflow.duration_seconds)
        
        if workflow.status == WorkflowStatus.COMPLETED:
            stats["success_count"] += 1
        elif workflow.status == WorkflowStatus.FAILED:
            stats["failure_count"] += 1
    
    def start_step(self, step_id: str, step_name: str, workflow_id: str,
                  step_type: str, dependencies: List[str] = None,
                  metadata: Dict[str, Any] = None) -> None:
        """Start tracking a workflow step"""
        with self._lock:
            self.steps[step_id] = StepMetrics(
                step_id=step_id,
                step_name=step_name,
                workflow_id=workflow_id,
                step_type=step_type,
                status=StepStatus.RUNNING,
                start_time=datetime.now(),
                dependencies=dependencies or [],
                metadata=metadata or {}
            )
            
            # Update workflow step count
            if workflow_id in self.workflows:
                self.workflows[workflow_id].total_steps += 1
            
            self.queued_steps.discard(step_id)
            
            logger.debug(f"Started step: {step_id} in workflow {workflow_id}")
    
    def complete_step(self, step_id: str, status: StepStatus = StepStatus.COMPLETED,
                     output_size: int = 0, agent_id: str = None,
                     error_message: str = None) -> None:
        """Complete step tracking"""
        with self._lock:
            if step_id not in self.steps:
                logger.warning(f"Step {step_id} not found")
                return
            
            step = self.steps[step_id]
            step.end_time = datetime.now()
            step.status = status
            step.output_size = output_size
            step.agent_id = agent_id
            step.error_message = error_message
            
            # Update workflow counters
            workflow = self.workflows.get(step.workflow_id)
            if workflow:
                if status == StepStatus.COMPLETED:
                    workflow.completed_steps += 1
                elif status == StepStatus.FAILED:
                    workflow.failed_steps += 1
                elif status == StepStatus.SKIPPED:
                    workflow.skipped_steps += 1
                workflow.total_retries += step.retry_count
            
            # Update statistics
            self._update_step_stats(step)
            
            logger.debug(f"Completed step: {step_id} in {step.execution_time:.2f}s")
    
    def _update_step_stats(self, step: StepMetrics) -> None:
        """Update aggregated step statistics"""
        stats = self.step_type_stats[step.step_type]
        stats["total_executions"] += 1
        stats["total_duration"] += step.execution_time
        stats["avg_duration"] = stats["total_duration"] / stats["total_executions"]
        stats["min_duration"] = min(stats["min_duration"], step.execution_time)
        stats["max_duration"] = max(stats["max_duration"], step.execution_time)
        stats["total_retries"] += step.retry_count
        
        if step.status == StepStatus.COMPLETED:
            stats["success_count"] += 1
        elif step.status == StepStatus.FAILED:
            stats["failure_count"] += 1
    
    def fail_step(self, step_id: str, error_message: str, retry: bool = False) -> None:
        """Mark a step as failed"""
        with self._lock:
            if step_id not in self.steps:
                return
            
            step = self.steps[step_id]
            step.status = StepStatus.FAILED
            step.error_message = error_message
            
            if retry:
                step.retry_count += 1
                step.status = StepStatus.RETRYING
                step.start_time = datetime.now()  # Reset start time for retry
    
    def record_queue_wait(self, step_id: str, wait_time: float) -> None:
        """Record queue wait time for a step"""
        with self._lock:
            if step_id in self.steps:
                self.steps[step_id].queue_wait_time = wait_time
                self.queued_steps.add(step_id)
    
    def get_workflow_metrics(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get metrics for a specific workflow"""
        with self._lock:
            if workflow_id not in self.workflows:
                return None
            return self.workflows[workflow_id].to_dict()
    
    def get_step_metrics(self, step_id: str) -> Optional[Dict[str, Any]]:
        """Get metrics for a specific step"""
        with self._lock:
            if step_id not in self.steps:
                return None
            return self.steps[step_id].to_dict()
    
    def get_workflow_summary(self) -> Dict[str, Any]:
        """Get summary of all workflow metrics"""
        with self._lock:
            completed = [w for w in self.workflows.values() if w.status == WorkflowStatus.COMPLETED]
            failed = [w for w in self.workflows.values() if w.status == WorkflowStatus.FAILED]
            running = [w for w in self.workflows.values() if w.status == WorkflowStatus.RUNNING]
            
            return {
                "total_workflows": len(self.workflows),
                "completed": len(completed),
                "failed": len(failed),
                "running": len(running),
                "overall_success_rate": (len(completed) / len(self.workflows) * 100) if self.workflows else 100,
                "average_workflow_duration": sum(w.duration_seconds for w in completed) / len(completed) if completed else 0,
                "total_steps_executed": sum(w.total_steps for w in self.workflows.values()),
                "active_workflows": len(self.active_workflows)
            }
    
    def get_workflow_type_stats(self) -> Dict[str, Any]:
        """Get statistics grouped by workflow type"""
        with self._lock:
            return {
                workflow_name: {
                    "total_executions": stats["total_executions"],
                    "success_rate": (stats["success_count"] / stats["total_executions"] * 100) if stats["total_executions"] > 0 else 100,
                    "avg_duration_seconds": stats["avg_duration"],
                    "min_duration_seconds": stats["min_duration"] if stats["min_duration"] != float('inf') else 0,
                    "max_duration_seconds": stats["max_duration"]
                }
                for workflow_name, stats in self.workflow_type_stats.items()
            }
    
    def get_step_type_stats(self) -> Dict[str, Any]:
        """Get statistics grouped by step type"""
        with self._lock:
            return {
                step_type: {
                    "total_executions": stats["total_executions"],
                    "success_rate": (stats["success_count"] / stats["total_executions"] * 100) if stats["total_executions"] > 0 else 100,
                    "avg_duration_seconds": stats["avg_duration"],
                    "min_duration_seconds": stats["min_duration"] if stats["min_duration"] != float('inf') else 0,
                    "max_duration_seconds": stats["max_duration"],
                    "total_retries": stats["total_retries"],
                    "retry_rate": (stats["total_retries"] / stats["total_executions"]) if stats["total_executions"] > 0 else 0
                }
                for step_type, stats in self.step_type_stats.items()
            }
    
    def get_throughput_trend(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get throughput trend for last N hours"""
        cutoff = datetime.now() - timedelta(hours=hours)
        recent = [m for m in self.throughput_history if m.timestamp >= cutoff]
        return [m.to_dict() for m in recent]
    
    def get_resource_trend(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get resource usage trend for last N hours"""
        cutoff = datetime.now() - timedelta(hours=hours)
        recent = [m for m in self.resource_history if m.timestamp >= cutoff]
        return [m.to_dict() for m in recent]
    
    def get_slowest_workflows(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get the slowest completed workflows"""
        completed = [w for w in self.workflows.values() 
                    if w.status == WorkflowStatus.COMPLETED and w.duration_seconds > 0]
        completed.sort(key=lambda w: w.duration_seconds, reverse=True)
        
        return [w.to_dict() for w in completed[:limit]]
    
    def get_most_failed_steps(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get steps with most failures"""
        failed_steps = [s for s in self.steps.values() if s.status == StepStatus.FAILED]
        failed_steps.sort(key=lambda s: s.retry_count, reverse=True)
        
        return [s.to_dict() for s in failed_steps[:limit]]
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report"""
        with self._lock:
            report = {
                "timestamp": datetime.now().isoformat(),
                "summary": self.get_workflow_summary(),
                "workflow_types": self.get_workflow_type_stats(),
                "step_types": self.get_step_type_stats(),
                "throughput": {
                    "current_rate": self.throughput_history[-1].workflows_completed_per_minute if self.throughput_history else 0,
                    "peak_rate": max((t.workflows_completed for t in self.throughput_history), default=0),
                    "average_rate": sum(t.workflows_completed for t in self.throughput_history) / len(self.throughput_history) if self.throughput_history else 0
                },
                "resources": {
                    "avg_cpu": sum(r.cpu_percent for r in self.resource_history) / len(self.resource_history) if self.resource_history else 0,
                    "avg_memory": sum(r.memory_percent for r in self.resource_history) / len(self.resource_history) if self.resource_history else 0,
                    "peak_cpu": max((r.cpu_percent for r in self.resource_history), default=0),
                    "peak_memory": max((r.memory_percent for r in self.resource_history), default=0)
                },
                "slowest_workflows": self.get_slowest_workflows(5),
                "most_failed_steps": self.get_most_failed_steps(5)
            }
            
            return report
    
    def export_metrics(self) -> Dict[str, Any]:
        """Export all collected metrics"""
        with self._lock:
            return {
                "timestamp": datetime.now().isoformat(),
                "workflows": [w.to_dict() for w in self.workflows.values()],
                "steps": [s.to_dict() for s in self.steps.values()],
                "throughput_history": [t.to_dict() for t in self.throughput_history],
                "resource_history": [r.to_dict() for r in self.resource_history],
                "workflow_type_stats": self.get_workflow_type_stats(),
                "step_type_stats": self.get_step_type_stats(),
                "summary": self.get_workflow_summary()
            }
    
    def reset(self) -> None:
        """Reset all collected metrics"""
        with self._lock:
            self.workflows.clear()
            self.steps.clear()
            self.throughput_history.clear()
            self.resource_history.clear()
            self.workflow_type_stats.clear()
            self.step_type_stats.clear()
            self.active_workflows.clear()
            self.queued_steps.clear()
            logger.info("WorkflowMetricsCollector reset")
    
    def stop(self) -> None:
        """Stop background collection"""
        self._stop_collection.set()
        if self._collection_thread:
            self._collection_thread.join(timeout=5)
        self._save_data()
        logger.info("WorkflowMetricsCollector stopped")


# Singleton instance
_workflow_metrics_collector: Optional[WorkflowMetricsCollector] = None


def get_workflow_metrics_collector() -> WorkflowMetricsCollector:
    """Get global WorkflowMetricsCollector instance"""
    global _workflow_metrics_collector
    if _workflow_metrics_collector is None:
        _workflow_metrics_collector = WorkflowMetricsCollector()
    return _workflow_metrics_collector