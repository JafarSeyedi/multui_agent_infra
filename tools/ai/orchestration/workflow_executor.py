"""
Workflow Executor for Orchestration

Executes declarative workflow definitions (JSON) with full orchestration capabilities.
Integrates all system components to run workflows that can:
- Execute analysis tasks (scanners, chunkers, encoders, indexers)
- Run generation tasks (generators, planners, refiners)
- Perform quality checks (validators, testers, debuggers)
- Handle human-in-the-loop tasks
- Manage sessions and contexts
- Publish events and track metrics


This workflow_executor.py provides:

Full Integration with all system components (analysis, generation, quality, human tasks)
JSON Workflow Loading - Load declarative workflow definitions
Dynamic Task Execution - Route to appropriate components via registry
Session Management - Create and validate sessions
Context Management - Track execution context
Event Publishing - Emit workflow events
Human Task Creation - Create and assign human tasks
Workflow Control - Pause, resume, cancel executions
Component Registry - All components registered for dynamic dispatch
Parameter Resolution - Resolve {{context.path}} references
"""

import json
import uuid
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from pathlib import Path

from ..shared.logger import get_logger
from ..shared.state_manager import state_manager
from ..shared.config import config
from ..shared.git_utils import git_utils

from .workflow_engine import WorkflowEngine, WorkflowDefinition, TaskDefinition, TaskType, get_workflow_engine
from .pipeline_executer import PipelineExecutor, PipelineDefinition, get_pipeline_executor
from .session.session_manager import SessionManager, SessionType, get_session_manager
from .context_manager import ContextManager, get_context_manager
from .event_bus import EventBus, EventType, get_event_bus
from .agent_registry import AgentRegistry, AgentType, Capability, get_agent_registry

# Human task components
from .human_task.core.assignment_engine import AssignmentEngine, get_assignment_engine
from .human_task.core.feedback_collector import FeedbackCollector, get_feedback_collector
from .human_task.core.skill_registry import SkillRegistry, get_skill_registry
from .human_task.core.work_queue import WorkQueue, get_work_queue
from .human_task.core.work_item_types import WorkItemType, WorkItem

# Analysis components
from ..analysis.scanners.project_scanner import ProjectScanner
from ..analysis.scanners.ast_analyzer import ASTAnalyzer
from ..analysis.scanners.import_graph import ImportGraph
from ..analysis.scanners.api_surface_extractor import APISurfaceExtractor
from ..analysis.chunkers.code_chunker import CodeChunker
from ..analysis.chunkers.doc_chunker import DocChunker
from ..analysis.chunkers.semantic_chunker import SemanticChunker
from ..analysis.encoders.batch_encoder import BatchEncoder
from ..analysis.encoders.embedding_store import EmbeddingStore
from ..analysis.encoders.ollama_encoder import OllamaEncoder
from ..analysis.indexers.code_indexer import CodeIndexer
from ..analysis.indexers.doc_indexer import DocIndexer

# Generation components
from ..generation.generators.class_generator import ClassGenerator
from ..generation.generators.function_generator import FunctionGenerator
from ..generation.generators.module_generator import ModuleGenerator
from ..generation.generators.docstring_generator import DocstringGenerator
from ..generation.generators.test_generator import TestGenerator
from ..generation.generators.performance_test_generator import PerformanceTestGenerator
from ..generation.planners.dependency_planner import DependencyPlanner
from ..generation.planners.module_architect import ModuleArchitect
from ..generation.planners.skeleton_generator import SkeletonGenerator
from ..generation.planners.contract_generator import ContractGenerator
from ..generation.refiners.feedback_loop import FeedbackLoop
from ..generation.refiners.iterative_refiner import IterativeRefiner
from ..generation.refiners.impact_analyzer import ImpactAnalyzer

# Quality components
from ..quality.validators.architecture_validator import ArchitectureValidator
from ..quality.validators.dependency_validator import DependencyValidator
from ..quality.validators.docstring_validator import DocstringValidator
from ..quality.validators.security_validator import SecurityValidator
from ..quality.validators.performance_validator import PerformanceValidator
from ..quality.validators.mypy_validator import MypyValidator
from ..quality.validators.ruff_validator import RuffValidator
from ..quality.validators.pytest_validator import PytestValidator
from ..quality.validators.coverage_validator import CoverageValidator
from ..quality.testers.test_runner import TestRunner
from ..quality.testers.mutation_tester import MutationTester
from ..quality.debuggers.error_analyzer import ErrorAnalyzer
from ..quality.debuggers.runtime_inspector import RuntimeInspector

logger = get_logger(__name__)


class WorkflowExecutor:
    """
    Executes declarative workflow definitions with full orchestration capabilities.
    
    Features:
    - Load workflow definitions from JSON files
    - Execute complex DAG-based workflows
    - Integrate all system components (analysis, generation, quality, human tasks)
    - Session and context management
    - Event-driven execution
    - Metrics and monitoring
    """
    
    def __init__(self):
        # Core orchestration components
        self.workflow_engine: WorkflowEngine = get_workflow_engine()
        self.pipeline_executor: PipelineExecutor = get_pipeline_executor()
        self.session_manager: SessionManager = get_session_manager()
        self.context_manager: ContextManager = get_context_manager()
        self.event_bus: EventBus = get_event_bus()
        self.agent_registry: AgentRegistry = get_agent_registry()
        
        # Human task components
        self.assignment_engine: AssignmentEngine = get_assignment_engine()
        self.feedback_collector: FeedbackCollector = get_feedback_collector()
        self.skill_registry: SkillRegistry = get_skill_registry()
        self.work_queue: WorkQueue = get_work_queue()
        
        # Analysis components
        self._init_analysis_components()
        
        # Generation components
        self._init_generation_components()
        
        # Quality components
        self._init_quality_components()
        
        # Component registry for dynamic dispatch
        self._component_registry: Dict[str, Any] = {}
        self._register_components()
        
        # Custom task handlers
        self._custom_handlers: Dict[str, Callable] = {}
        
        logger.info("WorkflowExecutor initialized")
    
    def _init_analysis_components(self) -> None:
        """Initialize analysis components"""
        self.project_scanner = ProjectScanner()
        self.ast_analyzer = ASTAnalyzer()
        self.import_graph = ImportGraph()
        self.api_extractor = APISurfaceExtractor()
        self.code_chunker = CodeChunker()
        self.doc_chunker = DocChunker()
        self.semantic_chunker = SemanticChunker()
        self.batch_encoder = BatchEncoder()
        self.embedding_store = EmbeddingStore()
        self.ollama_encoder = OllamaEncoder()
        self.code_indexer = CodeIndexer()
        self.doc_indexer = DocIndexer()
    
    def _init_generation_components(self) -> None:
        """Initialize generation components"""
        self.class_generator = ClassGenerator()
        self.function_generator = FunctionGenerator()
        self.module_generator = ModuleGenerator()
        self.docstring_generator = DocstringGenerator()
        self.test_generator = TestGenerator()
        self.performance_test_generator = PerformanceTestGenerator()
        self.dependency_planner = DependencyPlanner()
        self.module_architect = ModuleArchitect()
        self.skeleton_generator = SkeletonGenerator()
        self.contract_generator = ContractGenerator()
        self.feedback_loop = FeedbackLoop()
        self.iterative_refiner = IterativeRefiner()
        self.impact_analyzer = ImpactAnalyzer()
    
    def _init_quality_components(self) -> None:
        """Initialize quality components"""
        self.architecture_validator = ArchitectureValidator()
        self.dependency_validator = DependencyValidator()
        self.docstring_validator = DocstringValidator()
        self.security_validator = SecurityValidator()
        self.performance_validator = PerformanceValidator()
        self.mypy_validator = MypyValidator()
        self.ruff_validator = RuffValidator()
        self.pytest_validator = PytestValidator()
        self.coverage_validator = CoverageValidator()
        self.test_runner = TestRunner()
        self.mutation_tester = MutationTester()
        self.error_analyzer = ErrorAnalyzer()
        self.runtime_inspector = RuntimeInspector()
    
    def _register_components(self) -> None:
        """Register all components for dynamic dispatch"""
        # Analysis
        self._component_registry.update({
            "project_scanner": self.project_scanner,
            "ast_analyzer": self.ast_analyzer,
            "import_graph": self.import_graph,
            "api_extractor": self.api_extractor,
            "code_chunker": self.code_chunker,
            "doc_chunker": self.doc_chunker,
            "semantic_chunker": self.semantic_chunker,
            "batch_encoder": self.batch_encoder,
            "embedding_store": self.embedding_store,
            "ollama_encoder": self.ollama_encoder,
            "code_indexer": self.code_indexer,
            "doc_indexer": self.doc_indexer,
        })
        
        # Generation
        self._component_registry.update({
            "class_generator": self.class_generator,
            "function_generator": self.function_generator,
            "module_generator": self.module_generator,
            "docstring_generator": self.docstring_generator,
            "test_generator": self.test_generator,
            "performance_test_generator": self.performance_test_generator,
            "dependency_planner": self.dependency_planner,
            "module_architect": self.module_architect,
            "skeleton_generator": self.skeleton_generator,
            "contract_generator": self.contract_generator,
            "feedback_loop": self.feedback_loop,
            "iterative_refiner": self.iterative_refiner,
            "impact_analyzer": self.impact_analyzer,
        })
        
        # Quality
        self._component_registry.update({
            "architecture_validator": self.architecture_validator,
            "dependency_validator": self.dependency_validator,
            "docstring_validator": self.docstring_validator,
            "security_validator": self.security_validator,
            "performance_validator": self.performance_validator,
            "mypy_validator": self.mypy_validator,
            "ruff_validator": self.ruff_validator,
            "pytest_validator": self.pytest_validator,
            "coverage_validator": self.coverage_validator,
            "test_runner": self.test_runner,
            "mutation_tester": self.mutation_tester,
            "error_analyzer": self.error_analyzer,
            "runtime_inspector": self.runtime_inspector,
        })
    
    def load_definition(self, file_path: str) -> Dict[str, Any]:
        """
        Load workflow definition from JSON file.
        
        Args:
            file_path: Path to JSON workflow definition
            
        Returns:
            Workflow definition dictionary
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Workflow definition not found: {file_path}")
        
        with open(path, 'r') as f:
            definition = json.load(f)
        
        # Validate definition
        self._validate_definition(definition)
        
        logger.info(f"Loaded workflow definition: {definition.get('name', file_path)}")
        return definition
    
    def _validate_definition(self, definition: Dict[str, Any]) -> None:
        """Validate workflow definition structure"""
        required_fields = ["name", "version", "tasks"]
        for field in required_fields:
            if field not in definition:
                raise ValueError(f"Workflow definition missing required field: {field}")
        
        tasks = definition.get("tasks", [])
        if not tasks:
            raise ValueError("Workflow must have at least one task")
        
        # Validate each task
        for task in tasks:
            if "id" not in task:
                raise ValueError("Each task must have an 'id' field")
            if "type" not in task:
                raise ValueError(f"Task {task.get('id')} missing 'type' field")
    
    def execute(self, definition: Dict[str, Any],
                session_id: str = None,
                input_data: Dict[str, Any] = None,
                context_data: Dict[str, Any] = None) -> str:
        """
        Execute a workflow definition.
        
        Args:
            definition: Workflow definition dictionary
            session_id: Optional session ID (creates new if not provided)
            input_data: Input data for the workflow
            context_data: Initial context data
            
        Returns:
            Workflow execution ID
        """
        # Create or validate session
        if not session_id:
            session = self.session_manager.create_session(
                session_type=SessionType.WORKFLOW,
                user_id=context_data.get("user_id") if context_data else None,
                metadata={"workflow_name": definition.get("name")}
            )
            session_id = session.session_id
        else:
            if not self.session_manager.validate_session(session_id):
                raise ValueError(f"Invalid or expired session: {session_id}")
        
        # Create execution context
        context = self.context_manager.create_context(
            workflow_id=definition.get("name", "unknown"),
            initial_data=context_data or {}
        )
        
        # Convert declarative tasks to WorkflowEngine tasks
        workflow_tasks = self._convert_to_workflow_tasks(definition["tasks"])
        
        # Create workflow definition for engine
        workflow_def = WorkflowDefinition(
            workflow_id=str(uuid.uuid4()),
            name=definition["name"],
            version=definition.get("version", "1.0"),
            description=definition.get("description", ""),
            tasks=workflow_tasks,
            entry_task_id=definition["tasks"][0]["id"] if definition["tasks"] else "",
            variables=definition.get("variables", {})
        )
        
        # Register workflow
        self.workflow_engine.register_workflow(workflow_def)
        
        # Attach to session
        self.session_manager.attach_workflow(session_id, workflow_def.workflow_id)
        
        # Start execution
        execution_id = self.workflow_engine.start_workflow(
            workflow_def.workflow_id,
            initial_variables={
                "input": input_data or {},
                "session_id": session_id,
                "context_id": context.context_id
            }
        )
        
        # Emit event
        self.event_bus.emit(
            event_type=EventType.WORKFLOW_STARTED,
            source="workflow_executor",
            data={
                "execution_id": execution_id,
                "workflow_name": definition["name"],
                "session_id": session_id
            }
        )
        
        logger.info(f"Started workflow execution {execution_id} for {definition['name']}")
        
        return execution_id
    
    def _convert_to_workflow_tasks(self, task_defs: List[Dict]) -> Dict[str, TaskDefinition]:
        """
        Convert declarative task definitions to WorkflowEngine TaskDefinitions.
        
        Args:
            task_defs: List of declarative task definitions
            
        Returns:
            Dictionary of TaskDefinition objects
        """
        tasks = {}
        
        for task_def in task_defs:
            task_type = self._map_task_type(task_def.get("type"))
            
            task = TaskDefinition(
                task_id=task_def["id"],
                name=task_def.get("name", task_def["id"]),
                type=task_type,
                config={
                    "component": task_def.get("component"),
                    "method": task_def.get("method"),
                    "parameters": task_def.get("parameters", {}),
                    "timeout": task_def.get("timeout", 300),
                    "retry": task_def.get("retry", {"max": 3, "delay": 5})
                },
                depends_on=task_def.get("depends_on", []),
                timeout_seconds=task_def.get("timeout", 300),
                max_retries=task_def.get("retry", {}).get("max", 3),
                retry_delay=task_def.get("retry", {}).get("delay", 5)
            )
            
            tasks[task.task_id] = task
        
        return tasks
    
    def _map_task_type(self, type_str: str) -> TaskType:
        """Map declarative task type to TaskType enum"""
        type_mapping = {
            "function": TaskType.FUNCTION,
            "transform": TaskType.TRANSFORM,
            "condition": TaskType.CONDITION,
            "wait": TaskType.WAIT,
            "notify": TaskType.NOTIFY,
            "sub_workflow": TaskType.SUB_WORKFLOW,
            "human": TaskType.HUMAN,
            "analysis": TaskType.FUNCTION,
            "generation": TaskType.FUNCTION,
            "quality": TaskType.FUNCTION,
            "validation": TaskType.FUNCTION,
        }
        return type_mapping.get(type_str, TaskType.FUNCTION)
    
    def execute_task(self, task_def: Dict[str, Any], context: Dict[str, Any]) -> Any:
        """
        Execute a single task dynamically.
        
        Args:
            task_def: Task definition with component, method, parameters
            context: Execution context
            
        Returns:
            Task result
        """
        component_name = task_def.get("component")
        method_name = task_def.get("method")
        parameters = task_def.get("parameters", {})
        
        if not component_name or not method_name:
            raise ValueError(f"Task missing component or method: {task_def}")
        
        # Get component from registry
        component = self._component_registry.get(component_name)
        if not component:
            raise ValueError(f"Unknown component: {component_name}")
        
        # Get method
        method = getattr(component, method_name, None)
        if not method or not callable(method):
            raise ValueError(f"Unknown method {method_name} on component {component_name}")
        
        # Resolve parameter references
        resolved_params = self._resolve_parameters(parameters, context)
        
        # Execute
        try:
            result = method(**resolved_params)
            return result
        except Exception as e:
            logger.error(f"Task execution failed: {e}")
            raise
    
    def _resolve_parameters(self, parameters: Dict, context: Dict) -> Dict:
        """
        Resolve parameter references (e.g., {{context.input.file}}).
        
        Args:
            parameters: Parameter dictionary with possible references
            context: Execution context
            
        Returns:
            Resolved parameters
        """
        resolved = {}
        
        for key, value in parameters.items():
            if isinstance(value, str) and value.startswith("{{") and value.endswith("}}"):
                # Resolve reference
                path = value[2:-2].strip().split(".")
                resolved_value = context
                for part in path:
                    if isinstance(resolved_value, dict):
                        resolved_value = resolved_value.get(part)
                    else:
                        resolved_value = getattr(resolved_value, part, None)
                    if resolved_value is None:
                        break
                resolved[key] = resolved_value
            elif isinstance(value, dict):
                resolved[key] = self._resolve_parameters(value, context)
            elif isinstance(value, list):
                resolved[key] = [
                    self._resolve_parameters(v, context) if isinstance(v, dict) else v
                    for v in value
                ]
            else:
                resolved[key] = value
        
        return resolved
    
    def create_human_task(self, task_config: Dict[str, Any], context: Dict) -> str:
        """
        Create and assign a human task.
        
        Args:
            task_config: Human task configuration
            context: Execution context
            
        Returns:
            Work item ID
        """
        work_item_type = WorkItemType.from_id(task_config.get("type", "review"))
        title = task_config.get("title", "Human Task Required")
        description = task_config.get("description", "")
        assignee = task_config.get("assignee")
        required_skills = task_config.get("required_skills", [])
        priority = task_config.get("priority", 2)
        
        # Find suitable human if not specified
        if not assignee and required_skills:
            # Convert skill names to required format
            required = {skill: 3 for skill in required_skills}  # Intermediate level
            matches = self.skill_registry.search_humans_by_skills(required, limit=1)
            if matches:
                assignee = matches[0]["human_id"]
        
        # Create work item using factory method
        if work_item_type == WorkItemType.APPROVAL:
            work_item = WorkItem.create_approval(
                title=title,
                description=description,
                approver=assignee or "system",
                target_id=task_config.get("target_id", context.get("workflow_id"))
            )
        elif work_item_type == WorkItemType.REVIEW:
            work_item = WorkItem.create_code_review(
                pr_id=task_config.get("target_id", "unknown"),
                title=title,
                author=context.get("user_id", "system"),
                reviewers=[assignee] if assignee else []
            )
        elif work_item_type == WorkItemType.BUG_TRIAGE:
            work_item = WorkItem.create_bug_triage(
                bug_id=task_config.get("bug_id", "unknown"),
                title=title,
                severity=task_config.get("severity", "medium"),
                reporter=context.get("user_id", "system")
            )
        else:
            # Generic work item
            work_item = WorkItem(
                item_id=str(uuid.uuid4()),
                type=work_item_type,
                title=title,
                description=description,
                payload=task_config,
                created_by=context.get("user_id", "system"),
                assigned_to=assignee,
                priority=priority
            )
        
        # Enqueue work item
        self.work_queue.enqueue(work_item)
        
        # Emit event
        self.event_bus.emit(
            event_type=EventType.HUMAN_TASK_CREATED,
            source="workflow_executor",
            data={
                "work_item_id": work_item.item_id,
                "type": work_item_type.id,
                "assignee": assignee
            }
        )
        
        return work_item.item_id
    
    def get_execution_status(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get workflow execution status"""
        return self.workflow_engine.get_workflow_status(execution_id)
    
    def get_execution_result(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get workflow execution results"""
        return self.workflow_engine.get_execution_result(execution_id)
    
    def pause(self, execution_id: str) -> bool:
        """Pause a running workflow"""
        return self.workflow_engine.pause_workflow(execution_id)
    
    def resume(self, execution_id: str) -> bool:
        """Resume a paused workflow"""
        return self.workflow_engine.resume_workflow(execution_id)
    
    def cancel(self, execution_id: str) -> bool:
        """Cancel a running workflow"""
        return self.workflow_engine.cancel_workflow(execution_id)
    
    def register_custom_handler(self, task_type: str, handler: Callable) -> None:
        """
        Register a custom task handler.
        
        Args:
            task_type: Task type identifier
            handler: Handler function
        """
        self._custom_handlers[task_type] = handler
        logger.info(f"Registered custom handler for task type: {task_type}")
    
    def list_available_workflows(self, workflows_dir: str = None) -> List[Dict[str, Any]]:
        """
        List all available workflow definitions.
        
        Args:
            workflows_dir: Directory containing workflow JSON files
            
        Returns:
            List of workflow metadata
        """
        if not workflows_dir:
            workflows_dir = str(Path(__file__).parent / "workflows")
        
        workflows = []
        path = Path(workflows_dir)
        
        if path.exists():
            for json_file in path.glob("*.json"):
                try:
                    with open(json_file, 'r') as f:
                        definition = json.load(f)
                    workflows.append({
                        "file": json_file.name,
                        "name": definition.get("name", json_file.stem),
                        "version": definition.get("version", "1.0"),
                        "description": definition.get("description", ""),
                        "task_count": len(definition.get("tasks", []))
                    })
                except Exception as e:
                    logger.warning(f"Failed to load {json_file}: {e}")
        
        return workflows
    
    def get_workflow_template(self) -> Dict[str, Any]:
        """Get a template for creating new workflow definitions"""
        return {
            "name": "my_workflow",
            "version": "1.0",
            "description": "Workflow description",
            "variables": {},
            "tasks": [
                {
                    "id": "task_1",
                    "name": "First Task",
                    "type": "function",
                    "component": "ast_analyzer",
                    "method": "analyze",
                    "parameters": {
                        "file_path": "{{input.file_path}}"
                    },
                    "depends_on": []
                },
                {
                    "id": "task_2",
                    "name": "Second Task",
                    "type": "human",
                    "component": None,
                    "method": None,
                    "parameters": {
                        "type": "review",
                        "title": "Review Required",
                        "required_skills": ["code_review"]
                    },
                    "depends_on": ["task_1"]
                }
            ]
        }


# Singleton instance
_workflow_executor: Optional[WorkflowExecutor] = None


def get_workflow_executor() -> WorkflowExecutor:
    """Get global WorkflowExecutor instance"""
    global _workflow_executor
    if _workflow_executor is None:
        _workflow_executor = WorkflowExecutor()
    return _workflow_executor