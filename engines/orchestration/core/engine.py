"""
Core Orchestration Engine

Main coordinator for all orchestration activities. Manages engine lifecycle,
process deployment, instance execution, and coordination between different
orchestration standards (BPMN, CMMN, DMN, State Machines, CEP).
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Type
from enum import Enum
from dataclasses import dataclass, field
from uuid import uuid4

from .context import ExecutionContext, ContextScope
from .instance import ProcessInstance, InstanceState
from .event_bus import EventBus, Event, EventType
from .correlation import CorrelationEngine
from .transaction import TransactionManager
from .scheduler import Scheduler


logger = logging.getLogger(__name__)


class EngineState(Enum):
    """Engine lifecycle states"""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPING = "stopping"
    ERROR = "error"


class DeploymentMode(Enum):
    """Deployment modes for process definitions"""
    REPLACE = "replace"  # Replace existing version
    VERSION = "version"  # Create new version
    PARALLEL = "parallel"  # Run in parallel with existing


@dataclass
class EngineConfig:
    """Engine configuration"""
    max_concurrent_instances: int = 1000
    enable_persistence: bool = True
    enable_monitoring: bool = True
    enable_clustering: bool = False
    job_executor_threads: int = 10
    async_executor_threads: int = 5
    history_level: str = "full"  # none, activity, audit, full
    deployment_mode: DeploymentMode = DeploymentMode.VERSION
    enable_optimistic_locking: bool = True
    enable_metrics: bool = True
    metrics_interval_seconds: int = 60
    
    # BPMN specific
    enable_bpmn: bool = True
    bpmn_validation: bool = True
    
    # CMMN specific
    enable_cmmn: bool = True
    cmmn_validation: bool = True
    
    # DMN specific
    enable_dmn: bool = True
    dmn_validation: bool = True
    
    # State Machine specific
    enable_state_machine: bool = True
    
    # CEP specific
    enable_cep: bool = True
    cep_buffer_size: int = 10000
    
    # Multi-Agent specific
    enable_multi_agent: bool = True
    agent_timeout_seconds: int = 300


@dataclass
class ProcessDefinition:
    """Process definition metadata"""
    id: str
    key: str
    name: str
    version: int
    deployment_id: str
    resource_name: str
    diagram_resource_name: Optional[str]
    has_start_form_key: bool
    has_graphical_notation: bool
    is_suspended: bool
    tenant_id: Optional[str]
    version_tag: Optional[str]
    history_time_to_live: Optional[int]
    is_startable_in_tasklist: bool
    definition_type: str  # bpmn, cmmn, dmn, state_machine, cep, multi_agent
    definition_xml: str
    deployed_at: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Deployment:
    """Deployment information"""
    id: str
    name: str
    deployment_time: datetime
    source: str
    tenant_id: Optional[str]
    definitions: List[ProcessDefinition] = field(default_factory=list)


class OrchestrationEngine:
    """
    Main orchestration engine coordinating all workflow execution.
    
    Responsibilities:
    - Engine lifecycle management (start, stop, pause, resume)
    - Process definition deployment and versioning
    - Process instance creation and management
    - Event routing and correlation
    - Transaction coordination
    - Job scheduling and execution
    - Monitoring and metrics collection
    """
    
    def __init__(self, config: Optional[EngineConfig] = None):
        self.config = config or EngineConfig()
        self.state = EngineState.STOPPED
        self.engine_id = str(uuid4())
        
        # Core components
        self.event_bus = EventBus()
        self.correlation_engine = CorrelationEngine(self.event_bus)
        self.transaction_manager = TransactionManager()
        self.scheduler = Scheduler()
        
        # Storage
        self.deployments: Dict[str, Deployment] = {}
        self.definitions: Dict[str, ProcessDefinition] = {}  # key -> definition
        self.definition_versions: Dict[str, List[ProcessDefinition]] = {}  # key -> versions
        self.instances: Dict[str, ProcessInstance] = {}
        
        # Engine registries
        self.engine_handlers: Dict[str, Any] = {}  # definition_type -> engine handler
        
        # Execution management
        self.active_instances: Set[str] = set()
        self.suspended_instances: Set[str] = set()
        
        # Async execution
        self._executor_tasks: List[asyncio.Task] = []
        self._shutdown_event = asyncio.Event()
        
        logger.info(f"Orchestration engine created: {self.engine_id}")
    
    async def start(self) -> None:
        """Start the orchestration engine"""
        if self.state == EngineState.RUNNING:
            logger.warning("Engine already running")
            return
        
        logger.info(f"Starting orchestration engine {self.engine_id}")
        self.state = EngineState.STARTING
        
        try:
            # Start core components
            await self.event_bus.start()
            await self.scheduler.start()
            
            # Start job executors
            for i in range(self.config.job_executor_threads):
                task = asyncio.create_task(self._job_executor_loop(i))
                self._executor_tasks.append(task)
            
            # Start async executors
            for i in range(self.config.async_executor_threads):
                task = asyncio.create_task(self._async_executor_loop(i))
                self._executor_tasks.append(task)
            
            # Start monitoring if enabled
            if self.config.enable_monitoring:
                task = asyncio.create_task(self._monitoring_loop())
                self._executor_tasks.append(task)
            
            self.state = EngineState.RUNNING
            logger.info(f"Orchestration engine started: {self.engine_id}")
            
            # Publish engine started event
            await self.event_bus.publish(Event(
                type=EventType.ENGINE_STARTED,
                data={"engine_id": self.engine_id, "timestamp": datetime.utcnow()}
            ))
            
        except Exception as e:
            self.state = EngineState.ERROR
            logger.error(f"Failed to start engine: {e}", exc_info=True)
            raise
    
    async def stop(self) -> None:
        """Stop the orchestration engine"""
        if self.state == EngineState.STOPPED:
            logger.warning("Engine already stopped")
            return
        
        logger.info(f"Stopping orchestration engine {self.engine_id}")
        self.state = EngineState.STOPPING
        
        try:
            # Signal shutdown
            self._shutdown_event.set()
            
            # Wait for all executor tasks to complete
            if self._executor_tasks:
                await asyncio.gather(*self._executor_tasks, return_exceptions=True)
                self._executor_tasks.clear()
            
            # Stop core components
            await self.scheduler.stop()
            await self.event_bus.stop()
            
            self.state = EngineState.STOPPED
            logger.info(f"Orchestration engine stopped: {self.engine_id}")
            
        except Exception as e:
            self.state = EngineState.ERROR
            logger.error(f"Error stopping engine: {e}", exc_info=True)
            raise
    
    async def pause(self) -> None:
        """Pause the orchestration engine"""
        if self.state != EngineState.RUNNING:
            raise RuntimeError(f"Cannot pause engine in state: {self.state}")
        
        logger.info(f"Pausing orchestration engine {self.engine_id}")
        self.state = EngineState.PAUSED
        await self.scheduler.pause()
    
    async def resume(self) -> None:
        """Resume the orchestration engine"""
        if self.state != EngineState.PAUSED:
            raise RuntimeError(f"Cannot resume engine in state: {self.state}")
        
        logger.info(f"Resuming orchestration engine {self.engine_id}")
        self.state = EngineState.RUNNING
        await self.scheduler.resume()
    
    def register_engine_handler(self, definition_type: str, handler: Any) -> None:
        """Register an engine handler for a specific definition type"""
        self.engine_handlers[definition_type] = handler
        logger.info(f"Registered engine handler for type: {definition_type}")
    
    async def deploy(
        self,
        name: str,
        resources: Dict[str, str],
        source: str = "api",
        tenant_id: Optional[str] = None
    ) -> Deployment:
        """
        Deploy process definitions
        
        Args:
            name: Deployment name
            resources: Dict of resource_name -> content (XML, JSON, etc.)
            source: Deployment source identifier
            tenant_id: Optional tenant identifier for multi-tenancy
        
        Returns:
            Deployment object with deployed definitions
        """
        deployment_id = str(uuid4())
        deployment = Deployment(
            id=deployment_id,
            name=name,
            deployment_time=datetime.utcnow(),
            source=source,
            tenant_id=tenant_id
        )
        
        logger.info(f"Deploying: {name} (id: {deployment_id})")
        
        # Parse and validate each resource
        for resource_name, content in resources.items():
            try:
                definition = await self._parse_definition(
                    resource_name, content, deployment_id, tenant_id
                )
                deployment.definitions.append(definition)
                
                # Store definition
                self.definitions[definition.key] = definition
                
                # Track versions
                if definition.key not in self.definition_versions:
                    self.definition_versions[definition.key] = []
                self.definition_versions[definition.key].append(definition)
                
                logger.info(f"Deployed definition: {definition.key} v{definition.version}")
                
            except Exception as e:
                logger.error(f"Failed to deploy resource {resource_name}: {e}")
                raise
        
        self.deployments[deployment_id] = deployment
        
        # Publish deployment event
        await self.event_bus.publish(Event(
            type=EventType.DEPLOYMENT_CREATED,
            data={"deployment_id": deployment_id, "name": name}
        ))
        
        return deployment
    
    async def _parse_definition(
        self,
        resource_name: str,
        content: str,
        deployment_id: str,
        tenant_id: Optional[str]
    ) -> ProcessDefinition:
        """Parse a process definition from content"""
        # Determine definition type from resource name or content
        definition_type = self._detect_definition_type(resource_name, content)
        
        # Generate definition metadata
        key = self._extract_definition_key(content, definition_type)
        version = self._calculate_next_version(key)
        
        definition = ProcessDefinition(
            id=str(uuid4()),
            key=key,
            name=self._extract_definition_name(content, definition_type),
            version=version,
            deployment_id=deployment_id,
            resource_name=resource_name,
            diagram_resource_name=None,
            has_start_form_key=False,
            has_graphical_notation=True,
            is_suspended=False,
            tenant_id=tenant_id,
            version_tag=None,
            history_time_to_live=None,
            is_startable_in_tasklist=True,
            definition_type=definition_type,
            definition_xml=content,
            deployed_at=datetime.utcnow()
        )
        
        return definition
    
    def _detect_definition_type(self, resource_name: str, content: str) -> str:
        """Detect the type of process definition"""
        if ".bpmn" in resource_name.lower() or "bpmn" in content[:200].lower():
            return "bpmn"
        elif ".cmmn" in resource_name.lower() or "cmmn" in content[:200].lower():
            return "cmmn"
        elif ".dmn" in resource_name.lower() or "dmn" in content[:200].lower():
            return "dmn"
        elif "statemachine" in resource_name.lower():
            return "state_machine"
        elif "cep" in resource_name.lower():
            return "cep"
        elif "agent" in resource_name.lower():
            return "multi_agent"
        else:
            return "bpmn"  # Default to BPMN
    
    def _extract_definition_key(self, content: str, definition_type: str) -> str:
        """Extract process definition key from content"""
        # Simplified extraction - in production, use proper XML/JSON parsing
        import re
        
        if definition_type == "bpmn":
            match = re.search(r'id="([^"]+)"', content)
            if match:
                return match.group(1)
        
        return f"process_{uuid4().hex[:8]}"
    
    def _extract_definition_name(self, content: str, definition_type: str) -> str:
        """Extract process definition name from content"""
        import re
        
        match = re.search(r'name="([^"]+)"', content)
        if match:
            return match.group(1)
        
        return "Unnamed Process"
    
    def _calculate_next_version(self, key: str) -> int:
        """Calculate the next version number for a definition key"""
        if key in self.definition_versions:
            return len(self.definition_versions[key]) + 1
        return 1
    
    async def start_process_instance(
        self,
        process_definition_key: str,
        business_key: Optional[str] = None,
        variables: Optional[Dict[str, Any]] = None,
        tenant_id: Optional[str] = None
    ) -> ProcessInstance:
        """
        Start a new process instance
        
        Args:
            process_definition_key: Key of the process definition
            business_key: Optional business key for correlation
            variables: Initial process variables
            tenant_id: Optional tenant identifier
        
        Returns:
            Created process instance
        """
        # Get latest version of definition
        definition = self.definitions.get(process_definition_key)
        if not definition:
            raise ValueError(f"Process definition not found: {process_definition_key}")
        
        if definition.is_suspended:
            raise RuntimeError(f"Process definition is suspended: {process_definition_key}")
        
        # Create process instance
        instance = ProcessInstance(
            id=str(uuid4()),
            definition_id=definition.id,
            definition_key=definition.key,
            definition_version=definition.version,
            business_key=business_key,
            tenant_id=tenant_id,
            state=InstanceState.ACTIVE,
            start_time=datetime.utcnow(),
            variables=variables or {}
        )
        
        self.instances[instance.id] = instance
        self.active_instances.add(instance.id)
        
        logger.info(f"Started process instance: {instance.id} (definition: {definition.key})")
        
        # Publish instance started event
        await self.event_bus.publish(Event(
            type=EventType.PROCESS_INSTANCE_STARTED,
            data={
                "instance_id": instance.id,
                "definition_key": definition.key,
                "business_key": business_key
            }
        ))
        
        # Delegate to appropriate engine handler
        handler = self.engine_handlers.get(definition.definition_type)
        if handler:
            await handler.execute_instance(instance, definition)
        else:
            logger.warning(f"No handler registered for type: {definition.definition_type}")
        
        return instance
    
    async def _job_executor_loop(self, executor_id: int) -> None:
        """Job executor loop for processing scheduled jobs"""
        logger.info(f"Job executor {executor_id} started")
        
        while not self._shutdown_event.is_set():
            try:
                if self.state == EngineState.RUNNING:
                    # Process scheduled jobs
                    await self.scheduler.process_due_jobs()
                
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Error in job executor {executor_id}: {e}", exc_info=True)
        
        logger.info(f"Job executor {executor_id} stopped")
    
    async def _async_executor_loop(self, executor_id: int) -> None:
        """Async executor loop for asynchronous continuations"""
        logger.info(f"Async executor {executor_id} started")
        
        while not self._shutdown_event.is_set():
            try:
                if self.state == EngineState.RUNNING:
                    # Process async continuations
                    pass  # Implementation depends on persistence layer
                
                await asyncio.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Error in async executor {executor_id}: {e}", exc_info=True)
        
        logger.info(f"Async executor {executor_id} stopped")
    
    async def _monitoring_loop(self) -> None:
        """Monitoring loop for collecting metrics"""
        logger.info("Monitoring loop started")
        
        while not self._shutdown_event.is_set():
            try:
                if self.state == EngineState.RUNNING and self.config.enable_metrics:
                    # Collect metrics
                    metrics = {
                        "active_instances": len(self.active_instances),
                        "suspended_instances": len(self.suspended_instances),
                        "total_definitions": len(self.definitions),
                        "total_deployments": len(self.deployments)
                    }
                    
                    await self.event_bus.publish(Event(
                        type=EventType.METRICS_COLLECTED,
                        data=metrics
                    ))
                
                await asyncio.sleep(self.config.metrics_interval_seconds)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}", exc_info=True)
        
        logger.info("Monitoring loop stopped")
    
    def get_instance(self, instance_id: str) -> Optional[ProcessInstance]:
        """Get a process instance by ID"""
        return self.instances.get(instance_id)
    
    def get_definition(self, key: str, version: Optional[int] = None) -> Optional[ProcessDefinition]:
        """Get a process definition by key and optional version"""
        if version is None:
            return self.definitions.get(key)
        
        versions = self.definition_versions.get(key, [])
        for definition in versions:
            if definition.version == version:
                return definition
        
        return None
    
    async def delete_deployment(self, deployment_id: str, cascade: bool = False) -> None:
        """Delete a deployment and optionally cascade to instances"""
        deployment = self.deployments.get(deployment_id)
        if not deployment:
            raise ValueError(f"Deployment not found: {deployment_id}")
        
        if cascade:
            # Delete all instances of definitions in this deployment
            for definition in deployment.definitions:
                instances_to_delete = [
                    inst_id for inst_id, inst in self.instances.items()
                    if inst.definition_id == definition.id
                ]
                for inst_id in instances_to_delete:
                    await self.delete_instance(inst_id, "Deployment deleted")
        
        # Remove definitions
        for definition in deployment.definitions:
            self.definitions.pop(definition.key, None)
            if definition.key in self.definition_versions:
                self.definition_versions[definition.key] = [
                    d for d in self.definition_versions[definition.key]
                    if d.id != definition.id
                ]
        
        # Remove deployment
        del self.deployments[deployment_id]
        
        logger.info(f"Deleted deployment: {deployment_id}")
    
    async def delete_instance(self, instance_id: str, reason: str = "Deleted") -> None:
        """Delete a process instance"""
        instance = self.instances.get(instance_id)
        if not instance:
            raise ValueError(f"Instance not found: {instance_id}")
        
        instance.state = InstanceState.TERMINATED
        instance.end_time = datetime.utcnow()
        
        self.active_instances.discard(instance_id)
        self.suspended_instances.discard(instance_id)
        
        await self.event_bus.publish(Event(
            type=EventType.PROCESS_INSTANCE_TERMINATED,
            data={"instance_id": instance_id, "reason": reason}
        ))
        
        logger.info(f"Deleted instance: {instance_id} - {reason}")
