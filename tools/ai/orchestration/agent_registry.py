"""
Agent Registry for Orchestration

Manages the registration, discovery, and lifecycle of agents in the multi-agent system.
Handles:
- Agent registration and deregistration
- Agent capabilities and skill discovery
- Agent health monitoring
- Agent communication routing
- Load balancing and failover
- Agent versioning and compatibility

This implementation provides:

    Agent Registration: Register/deregister agents with complete metadata
    Capability Management: Track agent capabilities and versions
    Health Monitoring: Heartbeat-based health checks with automatic offline detection
    Agent Discovery: Query agents by type, capability, status, version, tags
    Load Balancing: Score-based agent selection with load and performance metrics
    Task Assignment: Assign tasks to agents with capacity management
    Status Tracking: Track agent status (REGISTERED, ACTIVE, BUSY, IDLE, DEGRADED, OFFLINE)
    Performance Metrics: Track response times, error rates, task counts
    Event Callbacks: Register callbacks for registration, deregistration, status changes
    Singleton Pattern: Global instance via get_agent_registry()
    

"""

import uuid
import threading
import time
from typing import Dict, List, Optional, Any, Set, Tuple, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from collections import defaultdict
from queue import Queue, PriorityQueue

from ..shared.logger import get_logger
from ..shared.state_manager import state_manager
from ..shared.config import config

logger = get_logger(__name__)


class AgentStatus(Enum):
    """Status of an agent"""
    REGISTERED = "registered"
    ACTIVE = "active"
    BUSY = "busy"
    IDLE = "idle"
    DEGRADED = "degraded"
    OFFLINE = "offline"
    MAINTENANCE = "maintenance"
    UNKNOWN = "unknown"


class AgentType(Enum):
    """Types of agents in the system"""
    ORCHESTRATOR = "orchestrator"
    ANALYZER = "analyzer"
    GENERATOR = "generator"
    PLANNER = "planner"
    REFINER = "refiner"
    VALIDATOR = "validator"
    TESTER = "tester"
    DOCUMENTER = "documenter"
    HUMAN_INTERFACE = "human_interface"
    MONITOR = "monitor"
    COORDINATOR = "coordinator"
    WORKER = "worker"


class Capability(Enum):
    """Agent capabilities"""
    CODE_ANALYSIS = "code_analysis"
    CODE_GENERATION = "code_generation"
    TEST_GENERATION = "test_generation"
    DOCUMENTATION = "documentation"
    CODE_REVIEW = "code_review"
    REFACTORING = "refactoring"
    DEBUGGING = "debugging"
    PERFORMANCE_OPT = "performance_optimization"
    SECURITY_SCAN = "security_scan"
    DEPENDENCY_MGMT = "dependency_management"
    WORKFLOW_EXECUTION = "workflow_execution"
    HUMAN_INTERACTION = "human_interaction"
    DATA_ANALYSIS = "data_analysis"
    PLANNING = "planning"
    VALIDATION = "validation"


@dataclass
class AgentCapability:
    """Represents an agent's capability with metadata"""
    name: Capability
    version: str
    supported_features: List[str] = field(default_factory=list)
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name.value,
            "version": self.version,
            "supported_features": self.supported_features,
            "performance_metrics": self.performance_metrics
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentCapability":
        return cls(
            name=Capability(data["name"]),
            version=data["version"],
            supported_features=data.get("supported_features", []),
            performance_metrics=data.get("performance_metrics", {})
        )


@dataclass
class AgentInfo:
    """Complete information about an agent"""
    agent_id: str
    name: str
    type: AgentType
    status: AgentStatus
    capabilities: List[AgentCapability]
    endpoint: Optional[str] = None  # For remote agents
    version: str = "1.0.0"
    metadata: Dict[str, Any] = field(default_factory=dict)
    registered_at: datetime = field(default_factory=datetime.now)
    last_heartbeat: datetime = field(default_factory=datetime.now)
    current_task_id: Optional[str] = None
    task_queue_size: int = 0
    max_concurrent_tasks: int = 1
    active_tasks: int = 0
    total_tasks_processed: int = 0
    error_rate: float = 0.0
    avg_response_time: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "type": self.type.value,
            "status": self.status.value,
            "capabilities": [c.to_dict() for c in self.capabilities],
            "endpoint": self.endpoint,
            "version": self.version,
            "metadata": self.metadata,
            "registered_at": self.registered_at.isoformat(),
            "last_heartbeat": self.last_heartbeat.isoformat(),
            "current_task_id": self.current_task_id,
            "task_queue_size": self.task_queue_size,
            "max_concurrent_tasks": self.max_concurrent_tasks,
            "active_tasks": self.active_tasks,
            "total_tasks_processed": self.total_tasks_processed,
            "error_rate": self.error_rate,
            "avg_response_time": self.avg_response_time
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentInfo":
        capabilities = [AgentCapability.from_dict(c) for c in data.get("capabilities", [])]
        return cls(
            agent_id=data["agent_id"],
            name=data["name"],
            type=AgentType(data["type"]),
            status=AgentStatus(data["status"]),
            capabilities=capabilities,
            endpoint=data.get("endpoint"),
            version=data.get("version", "1.0.0"),
            metadata=data.get("metadata", {}),
            registered_at=datetime.fromisoformat(data["registered_at"]) if data.get("registered_at") else datetime.now(),
            last_heartbeat=datetime.fromisoformat(data["last_heartbeat"]) if data.get("last_heartbeat") else datetime.now(),
            current_task_id=data.get("current_task_id"),
            task_queue_size=data.get("task_queue_size", 0),
            max_concurrent_tasks=data.get("max_concurrent_tasks", 1),
            active_tasks=data.get("active_tasks", 0),
            total_tasks_processed=data.get("total_tasks_processed", 0),
            error_rate=data.get("error_rate", 0.0),
            avg_response_time=data.get("avg_response_time", 0.0)
        )


@dataclass
class AgentHeartbeat:
    """Heartbeat information from an agent"""
    agent_id: str
    timestamp: datetime
    status: AgentStatus
    current_task_id: Optional[str] = None
    metrics: Dict[str, float] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "timestamp": self.timestamp.isoformat(),
            "status": self.status.value,
            "current_task_id": self.current_task_id,
            "metrics": self.metrics
        }


@dataclass
class AgentQuery:
    """Query for finding agents"""
    agent_type: Optional[AgentType] = None
    capability: Optional[Capability] = None
    status: Optional[AgentStatus] = None
    min_version: Optional[str] = None
    tags: Dict[str, str] = field(default_factory=dict)
    max_load: Optional[float] = None  # 0-1, max allowed load


class AgentRegistry:
    """
    Registry for managing agents in the multi-agent system.
    
    Features:
    - Agent registration and discovery
    - Capability-based routing
    - Health monitoring with heartbeats
    - Load balancing across agents
    - Failover and redundancy
    - Agent version management
    """
    
    def __init__(self, storage_key: str = "agent_registry"):
        self.storage_key = storage_key
        self.agents: Dict[str, AgentInfo] = {}
        self.heartbeat_history: Dict[str, List[AgentHeartbeat]] = defaultdict(list)
        self._lock = threading.RLock()
        
        # Health monitoring
        self._monitor_thread: Optional[threading.Thread] = None
        self._stop_monitoring = threading.Event()
        self.heartbeat_timeout_seconds = 30
        self.health_check_interval = 10
        
        # Load balancing
        self.task_assignments: Dict[str, str] = {}  # task_id -> agent_id
        self.agent_scores: Dict[str, float] = {}  # agent_id -> score for load balancing
        
        # Callbacks
        self._on_agent_register: List[Callable] = []
        self._on_agent_deregister: List[Callable] = []
        self._on_agent_status_change: List[Callable] = []
        
        self._load_data()
        self._start_health_monitor()
        
        logger.info("AgentRegistry initialized")
    
    def _load_data(self) -> None:
        """Load agent data from state manager"""
        try:
            agents_data = state_manager.get(f"{self.storage_key}.agents", {})
            for agent_id, agent_data in agents_data.items():
                if isinstance(agent_data, dict):
                    self.agents[agent_id] = AgentInfo.from_dict(agent_data)
            
            history_data = state_manager.get(f"{self.storage_key}.heartbeats", {})
            for agent_id, heartbeats in history_data.items():
                self.heartbeat_history[agent_id] = [
                    AgentHeartbeat(**h) for h in heartbeats if isinstance(h, dict)
                ]
            
            assignments_data = state_manager.get(f"{self.storage_key}.assignments", {})
            self.task_assignments = assignments_data
            
        except Exception as e:
            logger.warning(f"Failed to load agent data: {e}")
    
    def _save_data(self) -> None:
        """Save agent data to state manager"""
        try:
            agents_data = {aid: agent.to_dict() for aid, agent in self.agents.items()}
            state_manager.set(f"{self.storage_key}.agents", agents_data)
            
            heartbeats_data = {
                aid: [h.to_dict() for h in heartbeats[-100:]]  # Keep last 100
                for aid, heartbeats in self.heartbeat_history.items()
            }
            state_manager.set(f"{self.storage_key}.heartbeats", heartbeats_data)
            
            state_manager.set(f"{self.storage_key}.assignments", self.task_assignments)
            
        except Exception as e:
            logger.error(f"Failed to save agent data: {e}")
    
    def _start_health_monitor(self) -> None:
        """Start background health monitoring thread"""
        def monitor():
            while not self._stop_monitoring.is_set():
                try:
                    self._check_agent_health()
                    self._update_agent_scores()
                except Exception as e:
                    logger.error(f"Error in health monitor: {e}")
                self._stop_monitoring.wait(self.health_check_interval)
        
        self._monitor_thread = threading.Thread(target=monitor, daemon=True)
        self._monitor_thread.start()
    
    def _check_agent_health(self) -> None:
        """Check health of all registered agents"""
        now = datetime.now()
        
        with self._lock:
            for agent_id, agent in list(self.agents.items()):
                time_since_heartbeat = (now - agent.last_heartbeat).total_seconds()
                
                if time_since_heartbeat > self.heartbeat_timeout_seconds:
                    if agent.status != AgentStatus.OFFLINE:
                        old_status = agent.status
                        agent.status = AgentStatus.OFFLINE
                        self._notify_status_change(agent, old_status, agent.status)
                        logger.warning(f"Agent {agent.name} ({agent_id}) marked OFFLINE - no heartbeat")
    
    def _update_agent_scores(self) -> None:
        """Update load balancing scores for agents"""
        with self._lock:
            for agent_id, agent in self.agents.items():
                if agent.status == AgentStatus.ACTIVE or agent.status == AgentStatus.IDLE:
                    # Calculate score based on load and performance
                    load_factor = agent.active_tasks / agent.max_concurrent_tasks if agent.max_concurrent_tasks > 0 else 1.0
                    error_factor = 1 - agent.error_rate
                    response_factor = 1 / (agent.avg_response_time + 0.1)
                    
                    # Weighted score
                    score = (0.4 * (1 - load_factor) + 
                            0.3 * error_factor + 
                            0.3 * response_factor)
                    
                    self.agent_scores[agent_id] = score
                else:
                    self.agent_scores[agent_id] = 0.0
    
    def register_agent(self, agent_info: AgentInfo) -> bool:
        """
        Register a new agent in the registry.
        
        Args:
            agent_info: Agent information
            
        Returns:
            True if registered successfully
        """
        with self._lock:
            if agent_info.agent_id in self.agents:
                logger.warning(f"Agent {agent_info.agent_id} already registered, updating...")
                self.update_agent_heartbeat(agent_info.agent_id, agent_info.status)
                return True
            
            self.agents[agent_info.agent_id] = agent_info
            self._save_data()
            
            self._notify_agent_register(agent_info)
            
            logger.info(f"Registered agent: {agent_info.name} ({agent_info.agent_id}) of type {agent_info.type.value}")
            return True
    
    def deregister_agent(self, agent_id: str) -> bool:
        """
        Deregister an agent from the registry.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            True if deregistered successfully
        """
        with self._lock:
            if agent_id not in self.agents:
                logger.warning(f"Agent {agent_id} not found")
                return False
            
            agent = self.agents[agent_id]
            del self.agents[agent_id]
            
            # Clean up assignments
            tasks_to_clean = [tid for tid, aid in self.task_assignments.items() if aid == agent_id]
            for tid in tasks_to_clean:
                del self.task_assignments[tid]
            
            self._save_data()
            
            self._notify_agent_deregister(agent)
            
            logger.info(f"Deregistered agent: {agent.name} ({agent_id})")
            return True
    
    def update_agent_heartbeat(self, agent_id: str, status: AgentStatus = None,
                              current_task_id: str = None, metrics: Dict[str, float] = None) -> bool:
        """
        Update heartbeat for an agent.
        
        Args:
            agent_id: Agent identifier
            status: Current status (optional)
            current_task_id: Current task being processed (optional)
            metrics: Performance metrics (optional)
            
        Returns:
            True if updated successfully
        """
        with self._lock:
            if agent_id not in self.agents:
                logger.warning(f"Agent {agent_id} not found for heartbeat")
                return False
            
            agent = self.agents[agent_id]
            old_status = agent.status
            
            # Update heartbeat
            agent.last_heartbeat = datetime.now()
            
            if status:
                agent.status = status
            
            if current_task_id:
                agent.current_task_id = current_task_id
            
            if metrics:
                # Update performance metrics
                if "response_time" in metrics:
                    # Exponential moving average
                    agent.avg_response_time = (
                        0.7 * agent.avg_response_time + 
                        0.3 * metrics["response_time"]
                    )
                if "error" in metrics and metrics["error"]:
                    agent.error_rate = (
                        0.9 * agent.error_rate + 
                        0.1 * 1.0
                    )
                else:
                    agent.error_rate = (
                        0.9 * agent.error_rate + 
                        0.1 * 0.0
                    )
            
            # Record heartbeat
            heartbeat = AgentHeartbeat(
                agent_id=agent_id,
                timestamp=datetime.now(),
                status=agent.status,
                current_task_id=current_task_id,
                metrics=metrics or {}
            )
            self.heartbeat_history[agent_id].append(heartbeat)
            
            # Trim history
            if len(self.heartbeat_history[agent_id]) > 1000:
                self.heartbeat_history[agent_id] = self.heartbeat_history[agent_id][-1000:]
            
            # Notify status change
            if old_status != agent.status:
                self._notify_status_change(agent, old_status, agent.status)
            
            self._save_data()
            
            return True
    
    def update_task_status(self, agent_id: str, task_id: str, 
                          completed: bool, duration: float = None) -> bool:
        """
        Update task processing status for an agent.
        
        Args:
            agent_id: Agent identifier
            task_id: Task identifier
            completed: Whether task completed successfully
            duration: Task duration in seconds
        """
        with self._lock:
            if agent_id not in self.agents:
                return False
            
            agent = self.agents[agent_id]
            
            if completed:
                agent.total_tasks_processed += 1
                if agent.current_task_id == task_id:
                    agent.current_task_id = None
                agent.active_tasks = max(0, agent.active_tasks - 1)
                
                if duration:
                    # Update average response time
                    agent.avg_response_time = (
                        0.8 * agent.avg_response_time + 
                        0.2 * duration
                    )
                
                # Clear assignment
                if task_id in self.task_assignments:
                    del self.task_assignments[task_id]
            
            else:
                # Task failed
                agent.error_rate = (
                    0.8 * agent.error_rate + 
                    0.2 * 1.0
                )
            
            # Update status based on load
            if agent.active_tasks >= agent.max_concurrent_tasks:
                agent.status = AgentStatus.BUSY
            elif agent.active_tasks > 0:
                agent.status = AgentStatus.ACTIVE
            else:
                agent.status = AgentStatus.IDLE
            
            self._save_data()
            return True
    
    def find_agent(self, query: AgentQuery) -> Optional[AgentInfo]:
        """
        Find a single agent matching the query (best match).
        
        Args:
            query: Query criteria
            
        Returns:
            Best matching agent or None
        """
        matches = self.find_agents(query)
        if matches:
            # Return best score
            return max(matches, key=lambda a: self.agent_scores.get(a.agent_id, 0))
        return None
    
    def find_agents(self, query: AgentQuery) -> List[AgentInfo]:
        """
        Find all agents matching the query.
        
        Args:
            query: Query criteria
            
        Returns:
            List of matching agents
        """
        matches = []
        
        with self._lock:
            for agent in self.agents.values():
                # Check type
                if query.agent_type and agent.type != query.agent_type:
                    continue
                
                # Check status
                if query.status and agent.status != query.status:
                    continue
                
                # Check capability
                if query.capability:
                    has_capability = any(c.name == query.capability for c in agent.capabilities)
                    if not has_capability:
                        continue
                
                # Check version
                if query.min_version:
                    if not self._version_greater_equal(agent.version, query.min_version):
                        continue
                
                # Check load
                if query.max_load is not None:
                    load = agent.active_tasks / agent.max_concurrent_tasks if agent.max_concurrent_tasks > 0 else 1.0
                    if load > query.max_load:
                        continue
                
                # Check tags
                if query.tags:
                    matches_tags = all(agent.metadata.get(k) == v for k, v in query.tags.items())
                    if not matches_tags:
                        continue
                
                matches.append(agent)
        
        return matches
    
    def _version_greater_equal(self, version: str, min_version: str) -> bool:
        """Compare version strings"""
        try:
            v_parts = [int(x) for x in version.split('.')]
            min_parts = [int(x) for x in min_version.split('.')]
            
            for v, m in zip(v_parts, min_parts):
                if v < m:
                    return False
                elif v > m:
                    return True
            
            return len(v_parts) >= len(min_parts)
        except:
            return True
    
    def select_agent_for_task(self, capability: Capability, 
                             preferred_type: AgentType = None) -> Optional[AgentInfo]:
        """
        Select the best agent for a task based on capability and load.
        
        Args:
            capability: Required capability
            preferred_type: Preferred agent type (optional)
            
        Returns:
            Best agent for the task
        """
        query = AgentQuery(
            capability=capability,
            status=AgentStatus.ACTIVE,
            max_load=0.8  # Don't assign to overloaded agents
        )
        
        if preferred_type:
            query.agent_type = preferred_type
        
        candidates = self.find_agents(query)
        
        if not candidates:
            # Try with IDLE status as well
            query.status = None
            candidates = self.find_agents(query)
        
        if not candidates:
            # Try with any status except OFFLINE
            candidates = [a for a in self.agents.values() 
                         if a.status != AgentStatus.OFFLINE and
                         any(c.name == capability for c in a.capabilities)]
        
        if candidates:
            # Sort by score and pick best
            best = max(candidates, key=lambda a: self.agent_scores.get(a.agent_id, 0))
            return best
        
        return None
    
    def assign_task_to_agent(self, task_id: str, agent_id: str) -> bool:
        """
        Assign a task to a specific agent.
        
        Args:
            task_id: Task identifier
            agent_id: Agent identifier
            
        Returns:
            True if assignment successful
        """
        with self._lock:
            if agent_id not in self.agents:
                return False
            
            agent = self.agents[agent_id]
            
            # Check capacity
            if agent.active_tasks >= agent.max_concurrent_tasks:
                logger.warning(f"Agent {agent_id} at capacity, cannot assign task {task_id}")
                return False
            
            # Assign task
            self.task_assignments[task_id] = agent_id
            agent.active_tasks += 1
            
            # Update status
            if agent.active_tasks >= agent.max_concurrent_tasks:
                agent.status = AgentStatus.BUSY
            else:
                agent.status = AgentStatus.ACTIVE
            
            agent.current_task_id = task_id
            
            self._save_data()
            
            logger.debug(f"Assigned task {task_id} to agent {agent.name} ({agent_id})")
            return True
    
    def get_agent_task(self, agent_id: str) -> Optional[str]:
        """Get the current task assigned to an agent"""
        with self._lock:
            if agent_id not in self.agents:
                return None
            return self.agents[agent_id].current_task_id
    
    def get_agent_by_id(self, agent_id: str) -> Optional[AgentInfo]:
        """Get agent information by ID"""
        with self._lock:
            return self.agents.get(agent_id)
    
    def get_all_agents(self, status: AgentStatus = None) -> List[AgentInfo]:
        """Get all registered agents, optionally filtered by status"""
        with self._lock:
            agents = list(self.agents.values())
            if status:
                agents = [a for a in agents if a.status == status]
            return agents
    
    def get_agents_by_type(self, agent_type: AgentType) -> List[AgentInfo]:
        """Get all agents of a specific type"""
        with self._lock:
            return [a for a in self.agents.values() if a.type == agent_type]
    
    def get_agents_by_capability(self, capability: Capability) -> List[AgentInfo]:
        """Get all agents with a specific capability"""
        with self._lock:
            return [a for a in self.agents.values() 
                    if any(c.name == capability for c in a.capabilities)]
    
    def get_agent_statistics(self) -> Dict[str, Any]:
        """Get statistics about all agents"""
        with self._lock:
            if not self.agents:
                return {"status": "no_agents"}
            
            total_agents = len(self.agents)
            active_agents = len([a for a in self.agents.values() if a.status == AgentStatus.ACTIVE])
            idle_agents = len([a for a in self.agents.values() if a.status == AgentStatus.IDLE])
            busy_agents = len([a for a in self.agents.values() if a.status == AgentStatus.BUSY])
            offline_agents = len([a for a in self.agents.values() if a.status == AgentStatus.OFFLINE])
            
            total_capacity = sum(a.max_concurrent_tasks for a in self.agents.values())
            total_active_tasks = sum(a.active_tasks for a in self.agents.values())
            
            avg_response_time = sum(a.avg_response_time for a in self.agents.values()) / total_agents
            total_tasks_processed = sum(a.total_tasks_processed for a in self.agents.values())
            avg_error_rate = sum(a.error_rate for a in self.agents.values()) / total_agents
            
            # Group by type
            by_type = defaultdict(int)
            for agent in self.agents.values():
                by_type[agent.type.value] += 1
            
            return {
                "total_agents": total_agents,
                "active_agents": active_agents,
                "idle_agents": idle_agents,
                "busy_agents": busy_agents,
                "offline_agents": offline_agents,
                "total_capacity": total_capacity,
                "total_active_tasks": total_active_tasks,
                "system_load": total_active_tasks / total_capacity if total_capacity > 0 else 0,
                "avg_response_time": avg_response_time,
                "total_tasks_processed": total_tasks_processed,
                "avg_error_rate": avg_error_rate,
                "agents_by_type": dict(by_type)
            }
    
    def get_agent_details(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific agent"""
        with self._lock:
            if agent_id not in self.agents:
                return None
            
            agent = self.agents[agent_id]
            
            # Get recent heartbeats
            recent_heartbeats = self.heartbeat_history.get(agent_id, [])[-10:]
            
            return {
                "agent": agent.to_dict(),
                "recent_heartbeats": [h.to_dict() for h in recent_heartbeats],
                "assigned_tasks": [tid for tid, aid in self.task_assignments.items() if aid == agent_id],
                "score": self.agent_scores.get(agent_id, 0)
            }
    
    def on_agent_register(self, callback: Callable) -> None:
        """Register callback for agent registration events"""
        self._on_agent_register.append(callback)
    
    def on_agent_deregister(self, callback: Callable) -> None:
        """Register callback for agent deregistration events"""
        self._on_agent_deregister.append(callback)
    
    def on_agent_status_change(self, callback: Callable) -> None:
        """Register callback for agent status change events"""
        self._on_agent_status_change.append(callback)
    
    def _notify_agent_register(self, agent: AgentInfo) -> None:
        """Notify callbacks of agent registration"""
        for callback in self._on_agent_register:
            try:
                callback(agent)
            except Exception as e:
                logger.error(f"Error in agent register callback: {e}")
    
    def _notify_agent_deregister(self, agent: AgentInfo) -> None:
        """Notify callbacks of agent deregistration"""
        for callback in self._on_agent_deregister:
            try:
                callback(agent)
            except Exception as e:
                logger.error(f"Error in agent deregister callback: {e}")
    
    def _notify_status_change(self, agent: AgentInfo, old_status: AgentStatus, 
                             new_status: AgentStatus) -> None:
        """Notify callbacks of agent status change"""
        for callback in self._on_agent_status_change:
            try:
                callback(agent, old_status, new_status)
            except Exception as e:
                logger.error(f"Error in status change callback: {e}")
    
    def create_agent_info(self, name: str, agent_type: AgentType,
                         capabilities: List[Capability],
                         endpoint: str = None,
                         version: str = "1.0.0",
                         max_concurrent_tasks: int = 1,
                         metadata: Dict[str, Any] = None) -> AgentInfo:
        """
        Helper method to create agent info with standard fields.
        
        Args:
            name: Agent name
            agent_type: Type of agent
            capabilities: List of capabilities
            endpoint: Endpoint URL for remote agent
            version: Agent version
            max_concurrent_tasks: Maximum concurrent tasks
            metadata: Additional metadata
            
        Returns:
            AgentInfo instance
        """
        agent_id = str(uuid.uuid4())
        
        agent_capabilities = [
            AgentCapability(name=cap, version=version)
            for cap in capabilities
        ]
        
        return AgentInfo(
            agent_id=agent_id,
            name=name,
            type=agent_type,
            status=AgentStatus.REGISTERED,
            capabilities=agent_capabilities,
            endpoint=endpoint,
            version=version,
            metadata=metadata or {},
            max_concurrent_tasks=max_concurrent_tasks
        )
    
    def stop(self) -> None:
        """Stop the health monitor"""
        self._stop_monitoring.set()
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)
        logger.info("AgentRegistry stopped")
    
    def reset(self) -> None:
        """Reset the registry (clear all agents)"""
        with self._lock:
            self.agents.clear()
            self.heartbeat_history.clear()
            self.task_assignments.clear()
            self.agent_scores.clear()
            self._save_data()
            logger.info("AgentRegistry reset")


# Singleton instance
_agent_registry: Optional[AgentRegistry] = None


def get_agent_registry() -> AgentRegistry:
    """Get global AgentRegistry instance"""
    global _agent_registry
    if _agent_registry is None:
        _agent_registry = AgentRegistry()
    return _agent_registry