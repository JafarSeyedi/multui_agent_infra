"""
Bottleneck Detector for Workflow Analysis

Identifies performance bottlenecks in workflow execution by analyzing:
- Task duration patterns
- Resource contention
- Agent response times
- Queue buildup
- Sequential dependencies that could be parallelized

This implementation provides:

    Bottleneck Detection Types: Task duration, agent response, queue wait, sequential blocks, resource contention
    Severity Levels: LOW, MEDIUM, HIGH, CRITICAL
    Metrics Collection: Tracks tasks, agents, queues, and resource usage
    Detection Algorithms:
        Statistical analysis (deviation from historical averages)
        Threshold-based detection
        Dependency graph analysis for sequential blocks
        Resource utilization monitoring
    Suggestions Generation: Actionable optimization recommendations
    Persistence: Saves to state_manager for historical analysis
    Thread-Safe: Uses locks for concurrent access

The detector integrates with your existing shared modules (logger, config, state_manager) and 
provides real-time bottleneck identification for your workflow orchestration.

"""

import time
import threading
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from collections import defaultdict, deque
import json

from ...shared.logger import get_logger
from ...shared.state_manager import state_manager
from ...shared.config import config

logger = get_logger(__name__)


class BottleneckType(Enum):
    """Types of bottlenecks that can be detected"""
    TASK_DURATION = "task_duration"
    AGENT_RESPONSE = "agent_response"
    QUEUE_WAIT = "queue_wait"
    RESOURCE_CONTENTION = "resource_contention"
    SEQUENTIAL_BLOCK = "sequential_block"
    MEMORY_PRESSURE = "memory_pressure"
    IO_BOUND = "io_bound"
    CPU_BOUND = "cpu_bound"
    LOCK_CONTENTION = "lock_contention"
    NETWORK_LATENCY = "network_latency"


class Severity(Enum):
    """Bottleneck severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Bottleneck:
    """Represents a detected bottleneck"""
    type: BottleneckType
    severity: Severity
    location: str  # Task ID, agent ID, or resource name
    description: str
    duration_seconds: float
    impact_score: float  # 0-100, higher means more impact
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type.value,
            "severity": self.severity.value,
            "location": self.location,
            "description": self.description,
            "duration_seconds": self.duration_seconds,
            "impact_score": self.impact_score,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }


@dataclass
class TaskMetrics:
    """Metrics collected for a single task"""
    task_id: str
    task_type: str
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    agent_id: Optional[str] = None
    queue_wait_time: float = 0.0
    execution_time: float = 0.0
    retry_count: int = 0
    resource_usage: Dict[str, float] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    status: str = "pending"
    
    @property
    def total_time(self) -> float:
        return self.queue_wait_time + self.execution_time
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "task_type": self.task_type,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "queue_wait_time": self.queue_wait_time,
            "execution_time": self.execution_time,
            "retry_count": self.retry_count,
            "resource_usage": self.resource_usage,
            "dependencies": self.dependencies,
            "status": self.status
        }


@dataclass
class AgentMetrics:
    """Metrics collected for an agent"""
    agent_id: str
    agent_type: str
    total_tasks: int = 0
    total_execution_time: float = 0.0
    avg_response_time: float = 0.0
    error_count: int = 0
    current_queue_size: int = 0
    max_concurrent_tasks: int = 1
    active_tasks: int = 0
    last_heartbeat: Optional[datetime] = None
    
    @property
    def utilization(self) -> float:
        """Calculate agent utilization (0-100)"""
        if self.max_concurrent_tasks == 0:
            return 0.0
        return (self.active_tasks / self.max_concurrent_tasks) * 100
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "total_tasks": self.total_tasks,
            "total_execution_time": self.total_execution_time,
            "avg_response_time": self.avg_response_time,
            "error_count": self.error_count,
            "current_queue_size": self.current_queue_size,
            "max_concurrent_tasks": self.max_concurrent_tasks,
            "active_tasks": self.active_tasks,
            "utilization": self.utilization,
            "last_heartbeat": self.last_heartbeat.isoformat() if self.last_heartbeat else None
        }


class BottleneckDetector:
    """
    Detects performance bottlenecks in workflow execution.
    
    Monitors task execution, agent performance, and resource usage
    to identify bottlenecks and suggest optimizations.
    """
    
    def __init__(self, storage_key: str = "bottleneck_detector"):
        self.storage_key = storage_key
        self.tasks: Dict[str, TaskMetrics] = {}
        self.agents: Dict[str, AgentMetrics] = {}
        self.bottlenecks: List[Bottleneck] = []
        
        # Historical data for trend analysis
        self.historical_task_times: Dict[str, List[float]] = defaultdict(list)
        self.historical_queue_times: Dict[str, List[float]] = defaultdict(list)
        
        # Real-time monitoring
        self.task_queue: deque = deque()
        self.lock = threading.RLock()
        
        # Thresholds (configurable)
        self.bottleneck_thresholds = {
            BottleneckType.TASK_DURATION: 30.0,  # 30 seconds
            BottleneckType.QUEUE_WAIT: 10.0,     # 10 seconds
            BottleneckType.AGENT_RESPONSE: 5.0,  # 5 seconds
            BottleneckType.RESOURCE_CONTENTION: 80.0,  # 80% utilization
        }
        
        # Load thresholds from config if available
        self._load_thresholds()
        
        logger.info("BottleneckDetector initialized")
    
    def _load_thresholds(self) -> None:
        """Load bottleneck thresholds from configuration"""
        try:
            thresholds_config = config.get("orchestration.analytics.bottleneck_thresholds", {})
            for key, value in thresholds_config.items():
                for bt in BottleneckType:
                    if bt.value == key:
                        self.bottleneck_thresholds[bt] = float(value)
                        break
        except Exception as e:
            logger.warning(f"Failed to load bottleneck thresholds: {e}")
    
    def register_task(self, task_id: str, task_type: str, 
                      dependencies: List[str] = None) -> None:
        """Register a new task for monitoring"""
        with self.lock:
            self.tasks[task_id] = TaskMetrics(
                task_id=task_id,
                task_type=task_type,
                dependencies=dependencies or []
            )
            logger.debug(f"Registered task: {task_id} ({task_type})")
    
    def start_task(self, task_id: str, agent_id: Optional[str] = None) -> None:
        """Mark task as started"""
        with self.lock:
            if task_id not in self.tasks:
                logger.warning(f"Task {task_id} not registered, registering now")
                self.register_task(task_id, "unknown")
            
            task = self.tasks[task_id]
            task.start_time = datetime.now()
            task.agent_id = agent_id
            task.status = "running"
            
            # Track queue wait time if task was queued
            if task_id in self.task_queue:
                self.task_queue.remove(task_id)
            
            # Update agent metrics if agent specified
            if agent_id and agent_id in self.agents:
                agent = self.agents[agent_id]
                agent.active_tasks += 1
                agent.current_queue_size = max(0, agent.current_queue_size - 1)
            
            logger.debug(f"Started task: {task_id} on agent: {agent_id}")
    
    def complete_task(self, task_id: str, success: bool = True,
                     resource_usage: Dict[str, float] = None) -> None:
        """Mark task as completed and record metrics"""
        with self.lock:
            if task_id not in self.tasks:
                logger.warning(f"Task {task_id} not found")
                return
            
            task = self.tasks[task_id]
            task.end_time = datetime.now()
            task.status = "completed" if success else "failed"
            task.resource_usage = resource_usage or {}
            
            # Calculate execution time
            if task.start_time:
                task.execution_time = (task.end_time - task.start_time).total_seconds()
            
            # Update historical data
            self.historical_task_times[task.task_type].append(task.execution_time)
            self.historical_queue_times[task.task_type].append(task.queue_wait_time)
            
            # Keep only last 1000 entries
            if len(self.historical_task_times[task.task_type]) > 1000:
                self.historical_task_times[task.task_type].pop(0)
            if len(self.historical_queue_times[task.task_type]) > 1000:
                self.historical_queue_times[task.task_type].pop(0)
            
            # Update agent metrics
            if task.agent_id and task.agent_id in self.agents:
                agent = self.agents[task.agent_id]
                agent.active_tasks = max(0, agent.active_tasks - 1)
                agent.total_tasks += 1
                agent.total_execution_time += task.execution_time
                agent.avg_response_time = (agent.total_execution_time / agent.total_tasks)
                
                if not success:
                    agent.error_count += 1
            
            logger.debug(f"Completed task: {task_id} in {task.execution_time:.2f}s")
    
    def register_agent(self, agent_id: str, agent_type: str,
                      max_concurrent_tasks: int = 1) -> None:
        """Register an agent for monitoring"""
        with self.lock:
            self.agents[agent_id] = AgentMetrics(
                agent_id=agent_id,
                agent_type=agent_type,
                max_concurrent_tasks=max_concurrent_tasks
            )
            logger.debug(f"Registered agent: {agent_id} ({agent_type})")
    
    def update_agent_heartbeat(self, agent_id: str) -> None:
        """Update agent's last heartbeat timestamp"""
        with self.lock:
            if agent_id in self.agents:
                self.agents[agent_id].last_heartbeat = datetime.now()
    
    def update_queue_size(self, agent_id: str, queue_size: int) -> None:
        """Update agent's current queue size"""
        with self.lock:
            if agent_id in self.agents:
                self.agents[agent_id].current_queue_size = queue_size
    
    def record_queue_wait(self, task_id: str, wait_time: float) -> None:
        """Record how long a task waited in queue"""
        with self.lock:
            if task_id in self.tasks:
                self.tasks[task_id].queue_wait_time = wait_time
            self.task_queue.append(task_id)
    
    def detect_bottlenecks(self) -> List[Bottleneck]:
        """
        Analyze collected metrics and detect bottlenecks.
        
        Returns:
            List of detected bottlenecks
        """
        with self.lock:
            bottlenecks = []
            
            # 1. Detect slow tasks
            bottlenecks.extend(self._detect_slow_tasks())
            
            # 2. Detect agent bottlenecks
            bottlenecks.extend(self._detect_agent_bottlenecks())
            
            # 3. Detect queue bottlenecks
            bottlenecks.extend(self._detect_queue_bottlenecks())
            
            # 4. Detect sequential blockages
            bottlenecks.extend(self._detect_sequential_blocks())
            
            # 5. Detect resource contention
            bottlenecks.extend(self._detect_resource_contention())
            
            # Sort by impact score (highest first)
            bottlenecks.sort(key=lambda b: b.impact_score, reverse=True)
            
            # Store for later reference
            self.bottlenecks = bottlenecks
            
            # Save to state manager
            self._save_bottlenecks(bottlenecks)
            
            logger.info(f"Detected {len(bottlenecks)} bottlenecks")
            return bottlenecks
    
    def _detect_slow_tasks(self) -> List[Bottleneck]:
        """Detect tasks that take abnormally long to complete"""
        bottlenecks = []
        
        for task_id, task in self.tasks.items():
            if task.status != "completed":
                continue
            
            # Get historical average for this task type
            historical_times = self.historical_task_times.get(task.task_type, [])
            avg_time = sum(historical_times) / len(historical_times) if historical_times else task.execution_time
            
            # Calculate deviation
            if avg_time > 0:
                deviation_ratio = task.execution_time / avg_time
                
                # Check if significantly slower than average
                if deviation_ratio > 3.0:  # 3x slower
                    severity = Severity.HIGH if deviation_ratio > 5.0 else Severity.MEDIUM
                    impact = min(100, deviation_ratio * 20)
                    
                    bottlenecks.append(Bottleneck(
                        type=BottleneckType.TASK_DURATION,
                        severity=severity,
                        location=task_id,
                        description=f"Task {task.task_type} took {task.execution_time:.2f}s "
                                   f"({deviation_ratio:.1f}x longer than average)",
                        duration_seconds=task.execution_time,
                        impact_score=impact,
                        timestamp=datetime.now(),
                        metadata={
                            "task_type": task.task_type,
                            "avg_time": avg_time,
                            "deviation_ratio": deviation_ratio,
                            "agent_id": task.agent_id
                        }
                    ))
                elif task.execution_time > self.bottleneck_thresholds[BottleneckType.TASK_DURATION]:
                    severity = Severity.LOW
                    impact = min(100, (task.execution_time / self.bottleneck_thresholds[BottleneckType.TASK_DURATION]) * 50)
                    
                    bottlenecks.append(Bottleneck(
                        type=BottleneckType.TASK_DURATION,
                        severity=severity,
                        location=task_id,
                        description=f"Task {task.task_type} exceeded duration threshold "
                                   f"({task.execution_time:.2f}s > {self.bottleneck_thresholds[BottleneckType.TASK_DURATION]}s)",
                        duration_seconds=task.execution_time,
                        impact_score=impact,
                        timestamp=datetime.now(),
                        metadata={
                            "task_type": task.task_type,
                            "threshold": self.bottleneck_thresholds[BottleneckType.TASK_DURATION]
                        }
                    ))
        
        return bottlenecks
    
    def _detect_agent_bottlenecks(self) -> List[Bottleneck]:
        """Detect agents that are overloaded or underperforming"""
        bottlenecks = []
        
        for agent_id, agent in self.agents.items():
            # Check agent utilization
            if agent.utilization > self.bottleneck_thresholds[BottleneckType.RESOURCE_CONTENTION]:
                severity = Severity.HIGH if agent.utilization > 95 else Severity.MEDIUM
                impact = agent.utilization
                
                bottlenecks.append(Bottleneck(
                    type=BottleneckType.RESOURCE_CONTENTION,
                    severity=severity,
                    location=agent_id,
                    description=f"Agent {agent.agent_type} at {agent.utilization:.1f}% utilization",
                    duration_seconds=0,
                    impact_score=impact,
                    timestamp=datetime.now(),
                    metadata={
                        "agent_type": agent.agent_type,
                        "utilization": agent.utilization,
                        "active_tasks": agent.active_tasks,
                        "max_concurrent": agent.max_concurrent_tasks,
                        "queue_size": agent.current_queue_size
                    }
                ))
            
            # Check agent response time
            if agent.avg_response_time > self.bottleneck_thresholds[BottleneckType.AGENT_RESPONSE]:
                severity = Severity.MEDIUM if agent.avg_response_time > 10 else Severity.LOW
                impact = min(100, (agent.avg_response_time / self.bottleneck_thresholds[BottleneckType.AGENT_RESPONSE]) * 50)
                
                bottlenecks.append(Bottleneck(
                    type=BottleneckType.AGENT_RESPONSE,
                    severity=severity,
                    location=agent_id,
                    description=f"Agent {agent.agent_type} slow response: {agent.avg_response_time:.2f}s avg",
                    duration_seconds=agent.avg_response_time,
                    impact_score=impact,
                    timestamp=datetime.now(),
                    metadata={
                        "agent_type": agent.agent_type,
                        "avg_response_time": agent.avg_response_time,
                        "error_count": agent.error_count
                    }
                ))
            
            # Check for stale agents (no heartbeat)
            if agent.last_heartbeat:
                time_since_heartbeat = (datetime.now() - agent.last_heartbeat).total_seconds()
                if time_since_heartbeat > 60:  # 1 minute
                    bottlenecks.append(Bottleneck(
                        type=BottleneckType.AGENT_RESPONSE,
                        severity=Severity.HIGH,
                        location=agent_id,
                        description=f"Agent {agent.agent_type} not responding (last heartbeat {time_since_heartbeat:.0f}s ago)",
                        duration_seconds=time_since_heartbeat,
                        impact_score=80,
                        timestamp=datetime.now(),
                        metadata={"time_since_heartbeat": time_since_heartbeat}
                    ))
        
        return bottlenecks
    
    def _detect_queue_bottlenecks(self) -> List[Bottleneck]:
        """Detect queue buildup issues"""
        bottlenecks = []
        
        for agent_id, agent in self.agents.items():
            if agent.current_queue_size > 10:  # Queue threshold
                severity = Severity.HIGH if agent.current_queue_size > 50 else Severity.MEDIUM
                impact = min(100, agent.current_queue_size * 2)
                
                bottlenecks.append(Bottleneck(
                    type=BottleneckType.QUEUE_WAIT,
                    severity=severity,
                    location=agent_id,
                    description=f"Agent {agent.agent_type} has {agent.current_queue_size} tasks queued",
                    duration_seconds=0,
                    impact_score=impact,
                    timestamp=datetime.now(),
                    metadata={
                        "agent_type": agent.agent_type,
                        "queue_size": agent.current_queue_size,
                        "active_tasks": agent.active_tasks
                    }
                ))
        
        # Check queue wait times for tasks
        for task_id, task in self.tasks.items():
            if task.queue_wait_time > self.bottleneck_thresholds[BottleneckType.QUEUE_WAIT]:
                severity = Severity.MEDIUM if task.queue_wait_time > 30 else Severity.LOW
                impact = min(100, (task.queue_wait_time / self.bottleneck_thresholds[BottleneckType.QUEUE_WAIT]) * 50)
                
                bottlenecks.append(Bottleneck(
                    type=BottleneckType.QUEUE_WAIT,
                    severity=severity,
                    location=task_id,
                    description=f"Task {task.task_type} waited {task.queue_wait_time:.2f}s in queue",
                    duration_seconds=task.queue_wait_time,
                    impact_score=impact,
                    timestamp=datetime.now(),
                    metadata={
                        "task_type": task.task_type,
                        "queue_wait": task.queue_wait_time,
                        "agent_id": task.agent_id
                    }
                ))
        
        return bottlenecks
    
    def _detect_sequential_blocks(self) -> List[Bottleneck]:
        """Detect sequential dependencies that could be parallelized"""
        bottlenecks = []
        
        # Build dependency graph
        task_graph: Dict[str, List[str]] = {}
        for task_id, task in self.tasks.items():
            task_graph[task_id] = task.dependencies
        
        # Find long sequential chains
        visited = set()
        
        def find_chain_length(task_id: str, depth: int = 0) -> int:
            if task_id in visited:
                return depth
            visited.add(task_id)
            
            # Find tasks that depend on this one
            dependent_tasks = [t for t, deps in task_graph.items() if task_id in deps]
            if not dependent_tasks:
                return depth
            
            # Return max chain length
            return max(find_chain_length(dep, depth + 1) for dep in dependent_tasks)
        
        for task_id in task_graph:
            chain_length = find_chain_length(task_id)
            if chain_length > 5:  # Long sequential chain
                # Check if any tasks in chain took significant time
                total_time = 0
                current = task_id
                while current in self.tasks and self.tasks[current].execution_time > 0:
                    total_time += self.tasks[current].execution_time
                    # Find next in chain
                    next_tasks = [t for t, deps in task_graph.items() if current in deps]
                    if not next_tasks:
                        break
                    current = next_tasks[0]
                
                if total_time > 60:  # More than 1 minute of sequential work
                    bottlenecks.append(Bottleneck(
                        type=BottleneckType.SEQUENTIAL_BLOCK,
                        severity=Severity.MEDIUM,
                        location=task_id,
                        description=f"Long sequential dependency chain ({chain_length} tasks, {total_time:.2f}s total)",
                        duration_seconds=total_time,
                        impact_score=min(100, (chain_length / 10) * 100),
                        timestamp=datetime.now(),
                        metadata={
                            "chain_length": chain_length,
                            "total_time": total_time,
                            "chain_start": task_id
                        }
                    ))
        
        return bottlenecks
    
    def _detect_resource_contention(self) -> List[Bottleneck]:
        """Detect resource contention issues"""
        bottlenecks = []
        
        # Analyze resource usage across tasks
        resource_usage: Dict[str, List[float]] = defaultdict(list)
        
        for task in self.tasks.values():
            for resource, usage in task.resource_usage.items():
                resource_usage[resource].append(usage)
        
        for resource, usages in resource_usage.items():
            avg_usage = sum(usages) / len(usages) if usages else 0
            max_usage = max(usages) if usages else 0
            
            if max_usage > 90:  # Resource spike
                bottlenecks.append(Bottleneck(
                    type=BottleneckType.RESOURCE_CONTENTION,
                    severity=Severity.HIGH if max_usage > 95 else Severity.MEDIUM,
                    location=resource,
                    description=f"Resource {resource} spiked to {max_usage:.1f}% usage",
                    duration_seconds=0,
                    impact_score=max_usage,
                    timestamp=datetime.now(),
                    metadata={
                        "resource": resource,
                        "avg_usage": avg_usage,
                        "max_usage": max_usage,
                        "sample_count": len(usages)
                    }
                ))
            elif avg_usage > 70:  # Sustained high usage
                bottlenecks.append(Bottleneck(
                    type=BottleneckType.RESOURCE_CONTENTION,
                    severity=Severity.LOW,
                    location=resource,
                    description=f"Resource {resource} sustained high usage: {avg_usage:.1f}% average",
                    duration_seconds=0,
                    impact_score=avg_usage,
                    timestamp=datetime.now(),
                    metadata={
                        "resource": resource,
                        "avg_usage": avg_usage,
                        "max_usage": max_usage
                    }
                ))
        
        return bottlenecks
    
    def get_bottleneck_summary(self) -> Dict[str, Any]:
        """Get a summary of detected bottlenecks"""
        with self.lock:
            if not self.bottlenecks:
                return {"status": "no_bottlenecks_detected"}
            
            by_type = defaultdict(list)
            by_severity = defaultdict(list)
            
            for bottleneck in self.bottlenecks:
                by_type[bottleneck.type.value].append(bottleneck)
                by_severity[bottleneck.severity.value].append(bottleneck)
            
            return {
                "total_bottlenecks": len(self.bottlenecks),
                "by_type": {k: len(v) for k, v in by_type.items()},
                "by_severity": {k: len(v) for k, v in by_severity.items()},
                "critical_count": len(by_severity.get("critical", [])),
                "high_count": len(by_severity.get("high", [])),
                "top_bottlenecks": [
                    {
                        "type": b.type.value,
                        "severity": b.severity.value,
                        "location": b.location,
                        "impact": b.impact_score
                    }
                    for b in self.bottlenecks[:5]
                ]
            }
    
    def get_suggestions(self) -> List[str]:
        """
        Generate optimization suggestions based on detected bottlenecks.
        
        Returns:
            List of actionable suggestions
        """
        suggestions = []
        
        for bottleneck in self.bottlenecks[:10]:  # Top 10 bottlenecks
            if bottleneck.type == BottleneckType.TASK_DURATION:
                suggestions.append(
                    f"Optimize task '{bottleneck.location}' - consider breaking into smaller tasks "
                    f"or optimizing the implementation (took {bottleneck.duration_seconds:.2f}s)"
                )
            elif bottleneck.type == BottleneckType.AGENT_RESPONSE:
                suggestions.append(
                    f"Scale agent '{bottleneck.metadata.get('agent_type', bottleneck.location)}' - "
                    f"increase max_concurrent_tasks or add more instances"
                )
            elif bottleneck.type == BottleneckType.QUEUE_WAIT:
                suggestions.append(
                    f"Reduce queue size for {bottleneck.location} - increase processing capacity "
                    f"or optimize task distribution"
                )
            elif bottleneck.type == BottleneckType.SEQUENTIAL_BLOCK:
                suggestions.append(
                    f"Parallelize dependency chain starting at '{bottleneck.location}' - "
                    f"identify independent tasks that can run concurrently"
                )
            elif bottleneck.type == BottleneckType.RESOURCE_CONTENTION:
                suggestions.append(
                    f"Address resource contention on '{bottleneck.location}' - "
                    f"consider resource pooling or increasing capacity"
                )
        
        return suggestions
    
    def reset(self) -> None:
        """Reset all collected metrics"""
        with self.lock:
            self.tasks.clear()
            self.agents.clear()
            self.bottlenecks.clear()
            self.task_queue.clear()
            logger.info("BottleneckDetector reset")
    
    def _save_bottlenecks(self, bottlenecks: List[Bottleneck]) -> None:
        """Save bottlenecks to state manager"""
        try:
            data = {
                "timestamp": datetime.now().isoformat(),
                "bottlenecks": [b.to_dict() for b in bottlenecks],
                "summary": self.get_bottleneck_summary()
            }
            state_manager.set(f"{self.storage_key}.latest", data)
            
            # Keep history (last 100)
            history = state_manager.get(f"{self.storage_key}.history", [])
            history.append(data)
            if len(history) > 100:
                history = history[-100:]
            state_manager.set(f"{self.storage_key}.history", history)
        except Exception as e:
            logger.error(f"Failed to save bottlenecks: {e}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive statistics about task execution"""
        with self.lock:
            if not self.tasks:
                return {"status": "no_data"}
            
            completed_tasks = [t for t in self.tasks.values() if t.status == "completed"]
            if not completed_tasks:
                return {"status": "no_completed_tasks"}
            
            execution_times = [t.execution_time for t in completed_tasks if t.execution_time > 0]
            queue_times = [t.queue_wait_time for t in completed_tasks]
            
            stats = {
                "total_tasks": len(self.tasks),
                "completed_tasks": len(completed_tasks),
                "failed_tasks": len([t for t in self.tasks.values() if t.status == "failed"]),
                "avg_execution_time": sum(execution_times) / len(execution_times) if execution_times else 0,
                "max_execution_time": max(execution_times) if execution_times else 0,
                "min_execution_time": min(execution_times) if execution_times else 0,
                "avg_queue_wait": sum(queue_times) / len(queue_times) if queue_times else 0,
                "total_queue_wait": sum(queue_times),
                "task_types": defaultdict(int),
                "agent_performance": {}
            }
            
            # Count by task type
            for task in completed_tasks:
                stats["task_types"][task.task_type] += 1
            
            # Agent performance
            for agent_id, agent in self.agents.items():
                if agent.total_tasks > 0:
                    stats["agent_performance"][agent_id] = {
                        "total_tasks": agent.total_tasks,
                        "avg_response_time": agent.avg_response_time,
                        "error_rate": (agent.error_count / agent.total_tasks) * 100,
                        "utilization": agent.utilization
                    }
            
            return dict(stats)