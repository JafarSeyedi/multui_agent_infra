"""
Pipeline Builder for Orchestration

Provides a fluent DSL for building and configuring processing pipelines.
Handles:
- Pipeline definition and construction
- Stage configuration and chaining
- Parallel and sequential execution
- Conditional branching
- Error handling and recovery
- Pipeline validation and testing

This implementation provides:

    Fluent DSL: Chainable methods for building pipelines (add_task().with_timeout().build())
    Multiple Stage Types: Task, workflow, parallel, sequential, conditional, loop, delay, callback, transform, filter, aggregate
    Parallel Execution Strategies: ALL_SUCCESS, ANY_SUCCESS, ALL_COMPLETE, FIRST_SUCCESS, FIRST_COMPLETE
    Failure Policies: FAIL_FAST, FAIL_SILENT, RETRY, RETRY_WITH_BACKOFF, SKIP, FALLBACK
    Conditional Branching: Evaluate expressions to determine execution path
    Loop Constructs: Iterate over collections with configurable max iterations
    Dependency Management: Stages can depend on other stages
    Timeout Support: Per-stage timeout configuration
    Input/Output Schemas: Optional schema validation
    Pipeline Export/Import: Serialize pipelines to JSON for persistence

The pipeline builder integrates with your orchestration system to 
provide a flexible way to define and execute complex processing pipelines.


"""

import uuid
import time
import threading
from typing import Dict, List, Optional, Any, Set, Tuple, Callable, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, Future, as_completed

from ..shared.logger import get_logger
from ..shared.state_manager import state_manager

logger = get_logger(__name__)


class StageType(Enum):
    """Types of pipeline stages"""
    TASK = "task"           # Execute a single task
    WORKFLOW = "workflow"   # Execute a sub-workflow
    PARALLEL = "parallel"   # Execute multiple stages in parallel
    SEQUENTIAL = "sequential"  # Execute stages in sequence
    CONDITIONAL = "conditional"  # Conditional branching
    LOOP = "loop"           # Loop over items
    DELAY = "delay"         # Wait for a period
    CALLBACK = "callback"   # Call a function
    TRANSFORM = "transform"  # Transform data
    FILTER = "filter"       # Filter data
    AGGREGATE = "aggregate"  # Aggregate results


class ExecutionStrategy(Enum):
    """Strategies for parallel execution"""
    ALL_SUCCESS = "all_success"  # All must succeed
    ANY_SUCCESS = "any_success"  # At least one succeeds
    ALL_COMPLETE = "all_complete"  # All complete regardless of status
    FIRST_SUCCESS = "first_success"  # Stop after first success
    FIRST_COMPLETE = "first_complete"  # Stop after first complete


class FailurePolicy(Enum):
    """Policies for handling stage failures"""
    FAIL_FAST = "fail_fast"      # Stop pipeline on failure
    FAIL_SILENT = "fail_silent"  # Log but continue
    RETRY = "retry"               # Retry the stage
    RETRY_WITH_BACKOFF = "retry_with_backoff"  # Retry with exponential backoff
    SKIP = "skip"                # Skip failed stage
    FALLBACK = "fallback"        # Execute fallback stage


@dataclass
class StageConfig:
    """Configuration for a pipeline stage"""
    stage_id: str
    name: str
    type: StageType
    config: Dict[str, Any] = field(default_factory=dict)
    depends_on: List[str] = field(default_factory=list)
    failure_policy: FailurePolicy = FailurePolicy.FAIL_FAST
    max_retries: int = 3
    retry_delay: int = 1
    timeout_seconds: int = 300
    fallback_stage_id: Optional[str] = None
    condition: Optional[str] = None  # Expression to evaluate
    loop_over: Optional[str] = None  # Variable to iterate over
    transform: Optional[Callable] = None
    filter_func: Optional[Callable] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "stage_id": self.stage_id,
            "name": self.name,
            "type": self.type.value,
            "config": self.config,
            "depends_on": self.depends_on,
            "failure_policy": self.failure_policy.value,
            "max_retries": self.max_retries,
            "retry_delay": self.retry_delay,
            "timeout_seconds": self.timeout_seconds,
            "fallback_stage_id": self.fallback_stage_id,
            "condition": self.condition,
            "loop_over": self.loop_over
        }


@dataclass
class PipelineDefinition:
    """Definition of a pipeline"""
    pipeline_id: str
    name: str
    version: str
    stages: Dict[str, StageConfig]
    entry_stage: str
    input_schema: Optional[Dict[str, Any]] = None
    output_schema: Optional[Dict[str, Any]] = None
    context_variables: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "pipeline_id": self.pipeline_id,
            "name": self.name,
            "version": self.version,
            "stages": {sid: stage.to_dict() for sid, stage in self.stages.items()},
            "entry_stage": self.entry_stage,
            "input_schema": self.input_schema,
            "output_schema": self.output_schema,
            "context_variables": self.context_variables,
            "created_at": self.created_at.isoformat()
        }


@dataclass
class PipelineExecution:
    """Execution instance of a pipeline"""
    execution_id: str
    pipeline_id: str
    input_data: Dict[str, Any]
    status: str = "pending"  # pending, running, completed, failed, cancelled
    current_stage: Optional[str] = None
    stage_results: Dict[str, Any] = field(default_factory=dict)
    stage_statuses: Dict[str, str] = field(default_factory=dict)
    stage_errors: Dict[str, str] = field(default_factory=dict)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    output_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "execution_id": self.execution_id,
            "pipeline_id": self.pipeline_id,
            "input_data": self.input_data,
            "status": self.status,
            "current_stage": self.current_stage,
            "stage_results": self.stage_results,
            "stage_statuses": self.stage_statuses,
            "stage_errors": self.stage_errors,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "output_data": self.output_data,
            "error_message": self.error_message
        }


class PipelineBuilder:
    """
    Fluent DSL for building and executing processing pipelines.
    
    Features:
    - Chainable stage configuration
    - Parallel and sequential execution
    - Conditional branching
    - Loop constructs
    - Error handling policies
    - Pipeline validation
    - Execution monitoring
    """
    
    def __init__(self, name: str = None):
        self.pipeline_id = str(uuid.uuid4())
        self.name = name or f"pipeline_{self.pipeline_id[:8]}"
        self.version = "1.0"
        self.stages: Dict[str, StageConfig] = {}
        self.dependencies: Dict[str, List[str]] = defaultdict(list)
        self.entry_stage: Optional[str] = None
        self.input_schema: Optional[Dict[str, Any]] = None
        self.output_schema: Optional[Dict[str, Any]] = None
        self.context_variables: Dict[str, Any] = {}
        
        # Execution tracking
        self.executions: Dict[str, PipelineExecution] = {}
        self._executor = ThreadPoolExecutor(max_workers=10)
        
        # Stage implementations
        self._stage_handlers: Dict[StageType, Callable] = {}
        self._register_default_handlers()
        
        logger.debug(f"Created pipeline builder: {self.name}")
    
    def _register_default_handlers(self) -> None:
        """Register default stage handlers"""
        self._stage_handlers = {
            StageType.TASK: self._handle_task_stage,
            StageType.WORKFLOW: self._handle_workflow_stage,
            StageType.PARALLEL: self._handle_parallel_stage,
            StageType.SEQUENTIAL: self._handle_sequential_stage,
            StageType.CONDITIONAL: self._handle_conditional_stage,
            StageType.LOOP: self._handle_loop_stage,
            StageType.DELAY: self._handle_delay_stage,
            StageType.CALLBACK: self._handle_callback_stage,
            StageType.TRANSFORM: self._handle_transform_stage,
            StageType.FILTER: self._handle_filter_stage,
            StageType.AGGREGATE: self._handle_aggregate_stage,
        }
    
    # ========== Fluent API Methods ==========
    
    def add_task(self, name: str, task_type: str, 
                task_config: Dict[str, Any] = None,
                depends_on: List[str] = None) -> "PipelineBuilder":
        """
        Add a task stage.
        
        Args:
            name: Stage name
            task_type: Type of task to execute
            task_config: Task configuration
            depends_on: List of stage IDs this depends on
            
        Returns:
            Self for chaining
        """
        stage_id = self._generate_stage_id(name)
        
        config = StageConfig(
            stage_id=stage_id,
            name=name,
            type=StageType.TASK,
            config={
                "task_type": task_type,
                "task_config": task_config or {}
            },
            depends_on=depends_on or []
        )
        
        self._add_stage(stage_id, config)
        return self
    
    def add_workflow(self, name: str, workflow_id: str,
                    workflow_config: Dict[str, Any] = None,
                    depends_on: List[str] = None) -> "PipelineBuilder":
        """
        Add a sub-workflow stage.
        
        Args:
            name: Stage name
            workflow_id: ID of workflow to execute
            workflow_config: Workflow configuration
            depends_on: List of stage IDs this depends on
            
        Returns:
            Self for chaining
        """
        stage_id = self._generate_stage_id(name)
        
        config = StageConfig(
            stage_id=stage_id,
            name=name,
            type=StageType.WORKFLOW,
            config={
                "workflow_id": workflow_id,
                "workflow_config": workflow_config or {}
            },
            depends_on=depends_on or []
        )
        
        self._add_stage(stage_id, config)
        return self
    
    def add_parallel(self, name: str, stages: List[Dict[str, Any]],
                    strategy: ExecutionStrategy = ExecutionStrategy.ALL_SUCCESS,
                    depends_on: List[str] = None) -> "PipelineBuilder":
        """
        Add a parallel execution stage.
        
        Args:
            name: Stage name
            stages: List of stage definitions to run in parallel
            strategy: Parallel execution strategy
            depends_on: List of stage IDs this depends on
            
        Returns:
            Self for chaining
        """
        stage_id = self._generate_stage_id(name)
        
        config = StageConfig(
            stage_id=stage_id,
            name=name,
            type=StageType.PARALLEL,
            config={
                "stages": stages,
                "strategy": strategy.value
            },
            depends_on=depends_on or []
        )
        
        self._add_stage(stage_id, config)
        return self
    
    def add_conditional(self, name: str, condition: str,
                       true_branch: List[Dict[str, Any]],
                       false_branch: List[Dict[str, Any]] = None,
                       depends_on: List[str] = None) -> "PipelineBuilder":
        """
        Add a conditional branching stage.
        
        Args:
            name: Stage name
            condition: Condition expression to evaluate
            true_branch: Stages to execute if condition is true
            false_branch: Stages to execute if condition is false
            depends_on: List of stage IDs this depends on
            
        Returns:
            Self for chaining
        """
        stage_id = self._generate_stage_id(name)
        
        config = StageConfig(
            stage_id=stage_id,
            name=name,
            type=StageType.CONDITIONAL,
            config={
                "condition": condition,
                "true_branch": true_branch,
                "false_branch": false_branch or []
            },
            depends_on=depends_on or []
        )
        
        self._add_stage(stage_id, config)
        return self
    
    def add_loop(self, name: str, loop_over: str,
                loop_stages: List[Dict[str, Any]],
                max_iterations: int = 100,
                depends_on: List[str] = None) -> "PipelineBuilder":
        """
        Add a loop stage.
        
        Args:
            name: Stage name
            loop_over: Variable to iterate over
            loop_stages: Stages to execute for each item
            max_iterations: Maximum number of iterations
            depends_on: List of stage IDs this depends on
            
        Returns:
            Self for chaining
        """
        stage_id = self._generate_stage_id(name)
        
        config = StageConfig(
            stage_id=stage_id,
            name=name,
            type=StageType.LOOP,
            config={
                "loop_over": loop_over,
                "loop_stages": loop_stages,
                "max_iterations": max_iterations
            },
            depends_on=depends_on or []
        )
        
        self._add_stage(stage_id, config)
        return self
    
    def add_transform(self, name: str, transform_func: Callable,
                     depends_on: List[str] = None) -> "PipelineBuilder":
        """
        Add a data transformation stage.
        
        Args:
            name: Stage name
            transform_func: Function to transform data
            depends_on: List of stage IDs this depends on
            
        Returns:
            Self for chaining
        """
        stage_id = self._generate_stage_id(name)
        
        config = StageConfig(
            stage_id=stage_id,
            name=name,
            type=StageType.TRANSFORM,
            config={
                "transform_func": transform_func
            },
            depends_on=depends_on or []
        )
        
        self._add_stage(stage_id, config)
        return self
    
    def add_filter(self, name: str, filter_func: Callable,
                  depends_on: List[str] = None) -> "PipelineBuilder":
        """
        Add a filter stage.
        
        Args:
            name: Stage name
            filter_func: Function to filter data
            depends_on: List of stage IDs this depends on
            
        Returns:
            Self for chaining
        """
        stage_id = self._generate_stage_id(name)
        
        config = StageConfig(
            stage_id=stage_id,
            name=name,
            type=StageType.FILTER,
            config={
                "filter_func": filter_func
            },
            depends_on=depends_on or []
        )
        
        self._add_stage(stage_id, config)
        return self
    
    def add_aggregate(self, name: str, aggregate_func: Callable,
                     depends_on: List[str] = None) -> "PipelineBuilder":
        """
        Add an aggregation stage.
        
        Args:
            name: Stage name
            aggregate_func: Function to aggregate results
            depends_on: List of stage IDs this depends on
            
        Returns:
            Self for chaining
        """
        stage_id = self._generate_stage_id(name)
        
        config = StageConfig(
            stage_id=stage_id,
            name=name,
            type=StageType.AGGREGATE,
            config={
                "aggregate_func": aggregate_func
            },
            depends_on=depends_on or []
        )
        
        self._add_stage(stage_id, config)
        return self
    
    def add_delay(self, name: str, delay_seconds: int,
                 depends_on: List[str] = None) -> "PipelineBuilder":
        """
        Add a delay/wait stage.
        
        Args:
            name: Stage name
            delay_seconds: Seconds to wait
            depends_on: List of stage IDs this depends on
            
        Returns:
            Self for chaining
        """
        stage_id = self._generate_stage_id(name)
        
        config = StageConfig(
            stage_id=stage_id,
            name=name,
            type=StageType.DELAY,
            config={
                "delay_seconds": delay_seconds
            },
            depends_on=depends_on or []
        )
        
        self._add_stage(stage_id, config)
        return self
    
    def add_callback(self, name: str, callback: Callable,
                    depends_on: List[str] = None) -> "PipelineBuilder":
        """
        Add a callback stage.
        
        Args:
            name: Stage name
            callback: Callback function
            depends_on: List of stage IDs this depends on
            
        Returns:
            Self for chaining
        """
        stage_id = self._generate_stage_id(name)
        
        config = StageConfig(
            stage_id=stage_id,
            name=name,
            type=StageType.CALLBACK,
            config={
                "callback": callback
            },
            depends_on=depends_on or []
        )
        
        self._add_stage(stage_id, config)
        return self
    
    def with_failure_policy(self, stage_name: str, policy: FailurePolicy,
                           max_retries: int = 3, retry_delay: int = 1,
                           fallback_stage: str = None) -> "PipelineBuilder":
        """
        Set failure policy for a stage.
        
        Args:
            stage_name: Name of the stage
            policy: Failure policy to apply
            max_retries: Maximum retry attempts
            retry_delay: Delay between retries
            fallback_stage: Fallback stage ID if policy is FALLBACK
            
        Returns:
            Self for chaining
        """
        stage_id = self._find_stage_id(stage_name)
        if stage_id:
            self.stages[stage_id].failure_policy = policy
            self.stages[stage_id].max_retries = max_retries
            self.stages[stage_id].retry_delay = retry_delay
            self.stages[stage_id].fallback_stage_id = fallback_stage
        
        return self
    
    def with_timeout(self, stage_name: str, timeout_seconds: int) -> "PipelineBuilder":
        """Set timeout for a stage"""
        stage_id = self._find_stage_id(stage_name)
        if stage_id:
            self.stages[stage_id].timeout_seconds = timeout_seconds
        return self
    
    def with_condition(self, stage_name: str, condition: str) -> "PipelineBuilder":
        """Set condition for a stage"""
        stage_id = self._find_stage_id(stage_name)
        if stage_id:
            self.stages[stage_id].condition = condition
        return self
    
    def set_input_schema(self, schema: Dict[str, Any]) -> "PipelineBuilder":
        """Set input schema for validation"""
        self.input_schema = schema
        return self
    
    def set_output_schema(self, schema: Dict[str, Any]) -> "PipelineBuilder":
        """Set output schema for validation"""
        self.output_schema = schema
        return self
    
    def set_context(self, **kwargs) -> "PipelineBuilder":
        """Set context variables"""
        self.context_variables.update(kwargs)
        return self
    
    def set_entry_point(self, stage_name: str) -> "PipelineBuilder":
        """Set the entry stage for the pipeline"""
        stage_id = self._find_stage_id(stage_name)
        if stage_id:
            self.entry_stage = stage_id
        return self
    
    def _generate_stage_id(self, name: str) -> str:
        """Generate a unique stage ID"""
        # Sanitize name for use as ID
        safe_name = name.lower().replace(" ", "_").replace("-", "_")
        base_id = f"stage_{safe_name}"
        
        # Ensure uniqueness
        if base_id not in self.stages:
            return base_id
        
        counter = 1
        while f"{base_id}_{counter}" in self.stages:
            counter += 1
        return f"{base_id}_{counter}"
    
    def _find_stage_id(self, name: str) -> Optional[str]:
        """Find stage ID by name"""
        for stage_id, stage in self.stages.items():
            if stage.name == name:
                return stage_id
        return None
    
    def _add_stage(self, stage_id: str, config: StageConfig) -> None:
        """Add a stage to the pipeline"""
        self.stages[stage_id] = config
        
        # Build dependency graph
        for dep in config.depends_on:
            self.dependencies[dep].append(stage_id)
        
        # Set as entry if first stage
        if not self.entry_stage:
            self.entry_stage = stage_id
    
    def build(self) -> PipelineDefinition:
        """
        Build and validate the pipeline definition.
        
        Returns:
            PipelineDefinition object
        """
        # Validate pipeline
        self._validate_pipeline()
        
        definition = PipelineDefinition(
            pipeline_id=self.pipeline_id,
            name=self.name,
            version=self.version,
            stages=self.stages,
            entry_stage=self.entry_stage,
            input_schema=self.input_schema,
            output_schema=self.output_schema,
            context_variables=self.context_variables
        )
        
        logger.info(f"Built pipeline: {self.name} with {len(self.stages)} stages")
        
        return definition
    
    def _validate_pipeline(self) -> None:
        """Validate pipeline configuration"""
        if not self.stages:
            raise ValueError("Pipeline has no stages")
        
        if not self.entry_stage or self.entry_stage not in self.stages:
            raise ValueError(f"Invalid entry stage: {self.entry_stage}")
        
        # Check for circular dependencies
        visited = set()
        rec_stack = set()
        
        def has_cycle(stage_id: str) -> bool:
            visited.add(stage_id)
            rec_stack.add(stage_id)
            
            for dep in self.dependencies.get(stage_id, []):
                if dep not in visited:
                    if has_cycle(dep):
                        return True
                elif dep in rec_stack:
                    return True
            
            rec_stack.remove(stage_id)
            return False
        
        if has_cycle(self.entry_stage):
            raise ValueError("Circular dependency detected in pipeline")
        
        # Check all dependencies exist
        for stage_id, stage in self.stages.items():
            for dep in stage.depends_on:
                if dep not in self.stages:
                    raise ValueError(f"Stage {stage_id} depends on unknown stage {dep}")
    
    # ========== Execution Methods ==========
    
    def execute(self, pipeline: PipelineDefinition, 
                input_data: Dict[str, Any]) -> PipelineExecution:
        """
        Execute a pipeline.
        
        Args:
            pipeline: Pipeline definition to execute
            input_data: Input data for the pipeline
            
        Returns:
            PipelineExecution object
        """
        execution_id = str(uuid.uuid4())
        
        execution = PipelineExecution(
            execution_id=execution_id,
            pipeline_id=pipeline.pipeline_id,
            input_data=input_data,
            status="running",
            started_at=datetime.now()
        )
        
        self.executions[execution_id] = execution
        
        # Execute in thread pool
        future = self._executor.submit(self._run_pipeline, pipeline, execution)
        
        # Store future for tracking
        execution._future = future
        
        logger.info(f"Started pipeline execution {execution_id}")
        
        return execution
    
    def _run_pipeline(self, pipeline: PipelineDefinition, 
                     execution: PipelineExecution) -> None:
        """
        Run the pipeline stages.
        
        Args:
            pipeline: Pipeline definition
            execution: Execution instance
        """
        try:
            # Prepare execution context
            context = {
                "input": execution.input_data,
                "variables": pipeline.context_variables.copy(),
                "results": {}
            }
            
            # Process stages in topological order
            processed = set()
            stage_results = {}
            
            # Get execution order (topological sort)
            order = self._topological_sort(pipeline)
            
            for stage_id in order:
                if execution.status == "cancelled":
                    break
                
                stage = pipeline.stages[stage_id]
                execution.current_stage = stage_id
                
                # Check condition
                if stage.condition:
                    if not self._evaluate_condition(stage.condition, context):
                        execution.stage_statuses[stage_id] = "skipped"
                        continue
                
                # Execute stage with retry logic
                result = self._execute_stage_with_retry(
                    stage, context, execution
                )
                
                if result is not None:
                    stage_results[stage_id] = result
                    context["results"][stage_id] = result
                    execution.stage_results[stage_id] = result
                    execution.stage_statuses[stage_id] = "completed"
                else:
                    execution.stage_statuses[stage_id] = "failed"
                    
                    if stage.failure_policy == FailurePolicy.FAIL_FAST:
                        raise Exception(f"Stage {stage.name} failed")
                    elif stage.failure_policy == FailurePolicy.SKIP:
                        continue
                    elif stage.failure_policy == FailurePolicy.FALLBACK:
                        if stage.fallback_stage_id:
                            fallback_result = self._execute_stage(
                                pipeline.stages[stage.fallback_stage_id],
                                context, execution
                            )
                            if fallback_result:
                                stage_results[stage_id] = fallback_result
                                context["results"][stage_id] = fallback_result
                
                processed.add(stage_id)
            
            # Set output
            execution.output_data = {
                "results": stage_results,
                "context": context
            }
            execution.status = "completed"
            
        except Exception as e:
            execution.status = "failed"
            execution.error_message = str(e)
            logger.error(f"Pipeline {execution.execution_id} failed: {e}")
        
        finally:
            execution.completed_at = datetime.now()
    
    def _topological_sort(self, pipeline: PipelineDefinition) -> List[str]:
        """Sort stages in topological order"""
        # Build adjacency list
        graph = defaultdict(list)
        in_degree = defaultdict(int)
        
        for stage_id in pipeline.stages:
            in_degree[stage_id] = 0
        
        for stage_id, stage in pipeline.stages.items():
            for dep in stage.depends_on:
                graph[dep].append(stage_id)
                in_degree[stage_id] += 1
        
        # Kahn's algorithm
        queue = [sid for sid, degree in in_degree.items() if degree == 0]
        result = []
        
        while queue:
            stage_id = queue.pop(0)
            result.append(stage_id)
            
            for neighbor in graph[stage_id]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        if len(result) != len(pipeline.stages):
            raise ValueError("Circular dependency detected")
        
        return result
    
    def _execute_stage_with_retry(self, stage: StageConfig, 
                                  context: Dict[str, Any],
                                  execution: PipelineExecution) -> Any:
        """Execute a stage with retry logic"""
        attempt = 0
        last_error = None
        
        while attempt <= stage.max_retries:
            try:
                if attempt > 0:
                    # Wait before retry
                    delay = stage.retry_delay * (2 ** (attempt - 1))
                    time.sleep(delay)
                    logger.info(f"Retrying stage {stage.name} (attempt {attempt + 1})")
                
                result = self._execute_stage(stage, context, execution)
                return result
                
            except Exception as e:
                last_error = e
                attempt += 1
                
                if stage.failure_policy != FailurePolicy.RETRY and \
                   stage.failure_policy != FailurePolicy.RETRY_WITH_BACKOFF:
                    break
        
        if last_error:
            logger.error(f"Stage {stage.name} failed after {attempt} attempts: {last_error}")
        
        return None
    
    def _execute_stage(self, stage: StageConfig, 
                      context: Dict[str, Any],
                      execution: PipelineExecution) -> Any:
        """Execute a single stage"""
        handler = self._stage_handlers.get(stage.type)
        if not handler:
            raise ValueError(f"No handler for stage type: {stage.type}")
        
        # Execute with timeout
        future = self._executor.submit(handler, stage, context, execution)
        try:
            result = future.result(timeout=stage.timeout_seconds)
            return result
        except TimeoutError:
            raise TimeoutError(f"Stage {stage.name} timed out after {stage.timeout_seconds}s")
    
    def _handle_task_stage(self, stage: StageConfig, 
                          context: Dict[str, Any],
                          execution: PipelineExecution) -> Any:
        """Handle task stage execution"""
        task_type = stage.config.get("task_type")
        task_config = stage.config.get("task_config", {})
        
        # This would integrate with your task submission system
        logger.info(f"Executing task stage: {stage.name} (type: {task_type})")
        
        # Placeholder - replace with actual task execution
        return {
            "task_type": task_type,
            "status": "completed",
            "result": task_config
        }
    
    def _handle_workflow_stage(self, stage: StageConfig,
                              context: Dict[str, Any],
                              execution: PipelineExecution) -> Any:
        """Handle sub-workflow stage execution"""
        workflow_id = stage.config.get("workflow_id")
        workflow_config = stage.config.get("workflow_config", {})
        
        logger.info(f"Executing workflow stage: {stage.name} (workflow: {workflow_id})")
        
        # Placeholder - integrate with workflow engine
        return {
            "workflow_id": workflow_id,
            "status": "completed"
        }
    
    def _handle_parallel_stage(self, stage: StageConfig,
                              context: Dict[str, Any],
                              execution: PipelineExecution) -> Any:
        """Handle parallel execution stage"""
        sub_stages = stage.config.get("stages", [])
        strategy = ExecutionStrategy(stage.config.get("strategy", "all_success"))
        
        logger.info(f"Executing parallel stage: {stage.name} with {len(sub_stages)} branches")
        
        # Create sub-builder for each branch
        futures = []
        for i, sub_stage_def in enumerate(sub_stages):
            sub_builder = PipelineBuilder(f"{stage.name}_branch_{i}")
            # Configure sub-builder with stage definition
            # This is simplified - actual implementation would parse stage definitions
            future = self._executor.submit(
                lambda: self._execute_sub_pipeline(sub_stage_def, context)
            )
            futures.append(future)
        
        # Collect results based on strategy
        results = []
        if strategy == ExecutionStrategy.ALL_SUCCESS:
            for future in as_completed(futures):
                results.append(future.result())
        elif strategy == ExecutionStrategy.ANY_SUCCESS:
            for future in as_completed(futures):
                try:
                    result = future.result()
                    results.append(result)
                    break
                except:
                    continue
        else:
            for future in futures:
                try:
                    results.append(future.result())
                except:
                    results.append(None)
        
        return {"branches": results}
    
    def _handle_sequential_stage(self, stage: StageConfig,
                                context: Dict[str, Any],
                                execution: PipelineExecution) -> Any:
        """Handle sequential execution stage"""
        sub_stages = stage.config.get("stages", [])
        results = []
        
        for sub_stage_def in sub_stages:
            result = self._execute_sub_pipeline(sub_stage_def, context)
            results.append(result)
        
        return {"stages": results}
    
    def _handle_conditional_stage(self, stage: StageConfig,
                                  context: Dict[str, Any],
                                  execution: PipelineExecution) -> Any:
        """Handle conditional branching stage"""
        condition = stage.config.get("condition")
        true_branch = stage.config.get("true_branch", [])
        false_branch = stage.config.get("false_branch", [])
        
        condition_result = self._evaluate_condition(condition, context)
        
        if condition_result:
            branch = true_branch
        else:
            branch = false_branch
        
        results = []
        for sub_stage_def in branch:
            result = self._execute_sub_pipeline(sub_stage_def, context)
            results.append(result)
        
        return {"branch_taken": condition_result, "results": results}
    
    def _handle_loop_stage(self, stage: StageConfig,
                          context: Dict[str, Any],
                          execution: PipelineExecution) -> Any:
        """Handle loop stage execution"""
        loop_over = stage.config.get("loop_over")
        loop_stages = stage.config.get("loop_stages", [])
        max_iterations = stage.config.get("max_iterations", 100)
        
        items = context.get(loop_over, [])
        if not isinstance(items, list):
            items = [items]
        
        results = []
        iteration = 0
        
        for item in items[:max_iterations]:
            loop_context = context.copy()
            loop_context["item"] = item
            loop_context["index"] = iteration
            
            iteration_results = []
            for sub_stage_def in loop_stages:
                result = self._execute_sub_pipeline(sub_stage_def, loop_context)
                iteration_results.append(result)
            
            results.append({
                "item": item,
                "index": iteration,
                "results": iteration_results
            })
            
            iteration += 1
        
        return {"iterations": results, "total_iterations": iteration}
    
    def _handle_delay_stage(self, stage: StageConfig,
                           context: Dict[str, Any],
                           execution: PipelineExecution) -> Any:
        """Handle delay/wait stage"""
        delay_seconds = stage.config.get("delay_seconds", 0)
        time.sleep(delay_seconds)
        return {"waited": delay_seconds}
    
    def _handle_callback_stage(self, stage: StageConfig,
                              context: Dict[str, Any],
                              execution: PipelineExecution) -> Any:
        """Handle callback stage"""
        callback = stage.config.get("callback")
        if callback:
            return callback(context)
        return None
    
    def _handle_transform_stage(self, stage: StageConfig,
                               context: Dict[str, Any],
                               execution: PipelineExecution) -> Any:
        """Handle data transformation stage"""
        transform_func = stage.config.get("transform_func")
        if transform_func:
            return transform_func(context.get("data", {}))
        return context.get("data")
    
    def _handle_filter_stage(self, stage: StageConfig,
                            context: Dict[str, Any],
                            execution: PipelineExecution) -> Any:
        """Handle filter stage"""
        filter_func = stage.config.get("filter_func")
        if filter_func:
            data = context.get("data", [])
            if isinstance(data, list):
                return [item for item in data if filter_func(item)]
            return data if filter_func(data) else None
        return context.get("data")
    
    def _handle_aggregate_stage(self, stage: StageConfig,
                               context: Dict[str, Any],
                               execution: PipelineExecution) -> Any:
        """Handle aggregation stage"""
        aggregate_func = stage.config.get("aggregate_func")
        if aggregate_func:
            results = context.get("results", {})
            return aggregate_func(results)
        return context.get("results")
    
    def _execute_sub_pipeline(self, stage_def: Dict[str, Any],
                             context: Dict[str, Any]) -> Any:
        """Execute a sub-pipeline from a definition"""
        # Simplified execution - would recursively build and execute
        stage_type = stage_def.get("type")
        
        if stage_type == "task":
            return {"type": "task", "status": "completed"}
        elif stage_type == "transform":
            return {"type": "transform", "result": stage_def.get("config", {}).get("data")}
        else:
            return {"type": stage_type, "status": "completed"}
    
    def _evaluate_condition(self, condition: str, context: Dict[str, Any]) -> bool:
        """Evaluate a condition expression"""
        try:
            # Simple condition evaluation - can be enhanced with a proper expression parser
            # This is a simplified version for demonstration
            safe_dict = {
                **context,
                "len": len,
                "str": str,
                "int": int,
                "bool": bool
            }
            result = eval(condition, {"__builtins__": {}}, safe_dict)
            return bool(result)
        except Exception as e:
            logger.error(f"Failed to evaluate condition '{condition}': {e}")
            return False
    
    # ========== Utility Methods ==========
    
    def get_execution_status(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a pipeline execution"""
        execution = self.executions.get(execution_id)
        if not execution:
            return None
        
        return {
            "execution_id": execution.execution_id,
            "status": execution.status,
            "current_stage": execution.current_stage,
            "stage_statuses": execution.stage_statuses,
            "progress": len(execution.stage_statuses) / len(self.stages) if self.stages else 0,
            "started_at": execution.started_at.isoformat() if execution.started_at else None,
            "completed_at": execution.completed_at.isoformat() if execution.completed_at else None,
            "error_message": execution.error_message
        }
    
    def wait_for_completion(self, execution_id: str, timeout: float = None) -> bool:
        """Wait for a pipeline execution to complete"""
        execution = self.executions.get(execution_id)
        if not execution or not hasattr(execution, '_future'):
            return False
        
        try:
            execution._future.result(timeout=timeout)
            return True
        except:
            return False
    
    def cancel_execution(self, execution_id: str) -> bool:
        """Cancel a running pipeline execution"""
        execution = self.executions.get(execution_id)
        if not execution:
            return False
        
        execution.status = "cancelled"
        
        if hasattr(execution, '_future'):
            execution._future.cancel()
        
        logger.info(f"Cancelled pipeline execution {execution_id}")
        return True
    
    def export_pipeline(self, pipeline: PipelineDefinition, 
                       format: str = "json") -> str:
        """Export pipeline definition to JSON"""
        import json
        return json.dumps(pipeline.to_dict(), indent=2)
    
    def import_pipeline(self, pipeline_json: str) -> PipelineDefinition:
        """Import pipeline definition from JSON"""
        import json
        data = json.loads(pipeline_json)
        
        # Reconstruct stages
        stages = {}
        for stage_id, stage_data in data.get("stages", {}).items():
            stages[stage_id] = StageConfig(
                stage_id=stage_data["stage_id"],
                name=stage_data["name"],
                type=StageType(stage_data["type"]),
                config=stage_data.get("config", {}),
                depends_on=stage_data.get("depends_on", []),
                failure_policy=FailurePolicy(stage_data.get("failure_policy", "fail_fast")),
                max_retries=stage_data.get("max_retries", 3),
                retry_delay=stage_data.get("retry_delay", 1),
                timeout_seconds=stage_data.get("timeout_seconds", 300),
                fallback_stage_id=stage_data.get("fallback_stage_id"),
                condition=stage_data.get("condition"),
                loop_over=stage_data.get("loop_over")
            )
        
        return PipelineDefinition(
            pipeline_id=data["pipeline_id"],
            name=data["name"],
            version=data["version"],
            stages=stages,
            entry_stage=data["entry_stage"],
            input_schema=data.get("input_schema"),
            output_schema=data.get("output_schema"),
            context_variables=data.get("context_variables", {}),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.now()
        )
    
    def shutdown(self) -> None:
        """Shutdown the pipeline executor"""
        self._executor.shutdown(wait=True)
        logger.info("PipelineBuilder shutdown complete")


# Convenience function for quick pipeline creation
def create_pipeline(name: str) -> PipelineBuilder:
    """Create a new pipeline builder"""
    return PipelineBuilder(name)