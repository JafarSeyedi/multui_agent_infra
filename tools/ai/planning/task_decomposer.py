#!/usr/bin/env python3

"""
Task Decomposer - AI Development Framework
Breaks down epics and features into actionable, well-defined tasks.

Part of the Level 1 Planning tools (t1_1_2_2_task_decomposer.py)

This task_decomposer.py provides:

1. AI-Powered Decomposition - Uses LLM to break down epics into actionable tasks
2. Rule-Based Decomposition - Pattern matching for common development patterns
3. Task Templates - Reusable templates for common task types
4. Dependency Detection - Automatically identifies task dependencies
5. Sprint Planning - Suggests sprint/work allocations
6. Work Breakdown Structure - Hierarchical task organization
7. Risk Identification - Flags potential issues in the plan
8. Historical Learning - Uses past task data to improve estimates
9. Validation - Ensures task completeness and validity
10. Multiple Export Formats - Markdown reports, JSON, WBS diagrams

The tool integrates with ProgressTracker and can be used standalone or as part of the larger AI development framework.
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Set, Optional, Any, Tuple, DefaultDict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from collections import defaultdict

from ..shared.llm_client import LLMClient
from ..shared.state_manager import StateManager
from ..shared.logger import get_logger
from .progress_tracker import ProgressTracker, Task, Epic, Priority, TaskStatus

logger = get_logger(__name__)


# ============================================================
# ENUMS AND CONSTANTS
# ============================================================

class TaskComplexity(str, Enum):
    """Complexity level of a task."""
    TRIVIAL = "trivial"      # < 1 hour
    SIMPLE = "simple"        # 1-4 hours
    MODERATE = "moderate"    # 4-8 hours
    COMPLEX = "complex"      # 8-16 hours
    EPIC = "epic"            # > 16 hours, needs further decomposition


class TaskCategory(str, Enum):
    """Category of task."""
    SETUP = "setup"                  # Environment, dependencies, configuration
    MODEL = "model"                  # Data models, schemas, DTOs
    LOGIC = "logic"                  # Business logic, algorithms
    API = "api"                      # Endpoints, controllers, routes
    PARSER = "parser"                # Parsing logic
    CONVERTER = "converter"          # Format conversion
    VALIDATION = "validation"        # Validation logic
    UTILITY = "utility"              # Helper functions, utilities
    TEST = "test"                    # Unit/integration tests
    DOCUMENTATION = "documentation"  # Docstrings, markdown docs
    REFACTOR = "refactor"            # Code improvement
    BUGFIX = "bugfix"                # Bug fixes
    INTEGRATION = "integration"      # Third-party integration
    UI = "ui"                        # User interface
    DATABASE = "database"            # Database operations
    SECURITY = "security"            # Authentication, authorization
    PERFORMANCE = "performance"      # Optimization
    DEVOPS = "devops"                # CI/CD, deployment


class DependencyType(str, Enum):
    """Type of task dependency."""
    BLOCKS = "blocks"                # Must complete before another
    REQUIRES = "requires"            # Depends on another
    RELATES_TO = "relates_to"        # Related but not blocking
    DUPLICATES = "duplicates"        # Duplicates another task


# ============================================================
# DATA MODELS
# ============================================================

@dataclass
class TaskTemplate:
    """Template for generating similar tasks."""
    name: str
    category: TaskCategory
    description_template: str
    estimated_hours: float
    complexity: TaskComplexity
    required_files: List[str] = field(default_factory=list)
    test_files: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    checklist: List[str] = field(default_factory=list)


@dataclass
class DecompositionRule:
    """Rule for automatically decomposing certain patterns."""
    pattern: str  # Regex pattern for epic/feature description
    category: TaskCategory
    template_tasks: List[TaskTemplate]
    priority: int = 0


@dataclass
class TaskDependency:
    """Dependency relationship between tasks."""
    source_id: str
    target_id: str
    dep_type: DependencyType
    reason: str = ""
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class DecompositionResult:
    """Result of task decomposition."""
    epic: Epic
    tasks: List[Task]
    dependencies: List[TaskDependency]
    estimated_total_hours: float
    suggested_sprint_allocation: Dict[str, List[str]]  # sprint -> task IDs
    risks: List[str]
    assumptions: List[str]
    generated_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkBreakdownStructure:
    """Hierarchical work breakdown structure."""
    root: 'WBSNode'
    max_depth: int = 0
    total_tasks: int = 0
    total_hours: float = 0.0


@dataclass
class WBSNode:
    """Node in work breakdown structure."""
    id: str
    title: str
    level: int
    category: Optional[TaskCategory] = None
    estimated_hours: float = 0.0
    children: List['WBSNode'] = field(default_factory=list)
    task_id: Optional[str] = None  # Reference to created task


# ============================================================
# MAIN DECOMPOSER CLASS
# ============================================================

class TaskDecomposer:
    """
    AI-powered task decomposition engine.
    
    Features:
    - Break down epics into manageable tasks
    - Estimate task complexity and hours
    - Identify dependencies between tasks
    - Generate sprint/work allocation suggestions
    - Apply decomposition rules and templates
    - Create work breakdown structure (WBS)
    - Validate task completeness
    - Integrate with progress tracker
    - Learn from historical task data
    """
    
    def __init__(self, project_root: Path, progress_tracker: Optional[ProgressTracker] = None):
        self.project_root = project_root
        self.progress_tracker = progress_tracker or ProgressTracker(project_root)
        self.llm = LLMClient()
        self.state = StateManager(project_root / ".ai_state" / "task_decomposer.json")
        
        # Load templates and rules
        self.templates: Dict[str, TaskTemplate] = {}
        self.rules: List[DecompositionRule] = []
        self._load_templates()
        self._load_rules()
        
        # Historical data for learning
        self.historical_tasks: List[Task] = []
        self._load_historical_data()
    
    # ============================================================
    # INITIALIZATION
    # ============================================================
    
    def _load_templates(self):
        """Load task templates."""
        default_templates = self._get_default_templates()
        
        saved_templates = self.state.get('templates', {})
        for name, data in saved_templates.items():
            self.templates[name] = TaskTemplate(**data)
        
        # Add defaults if not present
        for name, template in default_templates.items():
            if name not in self.templates:
                self.templates[name] = template
        
        self._save_templates()
    
    def _save_templates(self):
        """Save task templates."""
        data = {name: t.__dict__ for name, t in self.templates.items()}
        self.state.set('templates', data)
        self.state.save()
    
    def _get_default_templates(self) -> Dict[str, TaskTemplate]:
        """Get default task templates."""
        return {
            "create_model": TaskTemplate(
                name="create_model",
                category=TaskCategory.MODEL,
                description_template="Create {name} data model with fields: {fields}. Include validation and serialization.",
                estimated_hours=1.0,
                complexity=TaskComplexity.SIMPLE,
                required_files=["models/{module_name}/{name}.py"],
                test_files=["tests/test_models/test_{name}.py"],
                tags=["model", "dataclass", "validation"],
                checklist=[
                    "Define all required fields",
                    "Add type hints",
                    "Include docstrings",
                    "Add validation logic",
                    "Write unit tests"
                ]
            ),
            "create_parser": TaskTemplate(
                name="create_parser",
                category=TaskCategory.PARSER,
                description_template="Implement {format} parser for {target_model}. Extract: {extract_fields}",
                estimated_hours=4.0,
                complexity=TaskComplexity.MODERATE,
                required_files=["parsers/{format}_parser.py"],
                test_files=["tests/test_parsers/test_{format}_parser.py"],
                tags=["parser", "{format}"],
                checklist=[
                    "Parse file structure",
                    "Extract all required fields",
                    "Handle edge cases",
                    "Add error handling",
                    "Write unit tests with sample files"
                ]
            ),
            "create_converter": TaskTemplate(
                name="create_converter",
                category=TaskCategory.CONVERTER,
                description_template="Convert {source_model} to {target_model}. Handle: {conversion_rules}",
                estimated_hours=3.0,
                complexity=TaskComplexity.MODERATE,
                required_files=["converters/{source}_to_{target}_converter.py"],
                test_files=["tests/test_converters/test_{source}_to_{target}.py"],
                tags=["converter", "transformation"],
                checklist=[
                    "Map all fields",
                    "Handle type conversions",
                    "Preserve metadata",
                    "Add bidirectional conversion",
                    "Write round-trip tests"
                ]
            ),
            "create_reader": TaskTemplate(
                name="create_reader",
                category=TaskCategory.PARSER,
                description_template="Create {name} reader for {source}. Read and parse: {elements}",
                estimated_hours=2.0,
                complexity=TaskComplexity.SIMPLE,
                required_files=["readers/{name}_reader.py"],
                test_files=["tests/test_readers/test_{name}_reader.py"],
                tags=["reader", "xml", "{source}"],
                checklist=[
                    "Implement read() method",
                    "Parse XML elements",
                    "Handle missing elements",
                    "Add namespace support",
                    "Write tests with sample XML"
                ]
            ),
            "create_writer": TaskTemplate(
                name="create_writer",
                category=TaskCategory.CONVERTER,
                description_template="Create {format} writer for {source_model}. Output: {output_spec}",
                estimated_hours=4.0,
                complexity=TaskComplexity.MODERATE,
                required_files=["writers/{format}_writer.py"],
                test_files=["tests/test_writers/test_{format}_writer.py"],
                tags=["writer", "{format}"],
                checklist=[
                    "Generate correct format structure",
                    "Preserve all content",
                    "Handle styling",
                    "Optimize output size",
                    "Write validation tests"
                ]
            ),
            "add_validation": TaskTemplate(
                name="add_validation",
                category=TaskCategory.VALIDATION,
                description_template="Add validation for {target}. Validate: {validation_rules}",
                estimated_hours=1.5,
                complexity=TaskComplexity.SIMPLE,
                required_files=["validators/{target}_validator.py"],
                test_files=["tests/test_validators/test_{target}_validator.py"],
                tags=["validation", "pydantic"],
                checklist=[
                    "Define validation rules",
                    "Implement custom validators",
                    "Add error messages",
                    "Test edge cases",
                    "Document validation rules"
                ]
            ),
            "write_tests": TaskTemplate(
                name="write_tests",
                category=TaskCategory.TEST,
                description_template="Write comprehensive tests for {target}. Coverage target: {coverage}%",
                estimated_hours=2.0,
                complexity=TaskComplexity.MODERATE,
                required_files=[],
                test_files=["tests/test_{target}.py"],
                tags=["testing", "pytest"],
                checklist=[
                    "Test happy path",
                    "Test edge cases",
                    "Test error conditions",
                    "Mock external dependencies",
                    "Achieve coverage target"
                ]
            ),
            "add_documentation": TaskTemplate(
                name="add_documentation",
                category=TaskCategory.DOCUMENTATION,
                description_template="Add comprehensive documentation for {target}",
                estimated_hours=1.0,
                complexity=TaskComplexity.TRIVIAL,
                required_files=[],
                test_files=[],
                tags=["documentation", "docstrings"],
                checklist=[
                    "Add module docstring",
                    "Document all public APIs",
                    "Include usage examples",
                    "Update README if needed",
                    "Generate API docs"
                ]
            ),
            "setup_module": TaskTemplate(
                name="setup_module",
                category=TaskCategory.SETUP,
                description_template="Setup {module_name} module structure and imports",
                estimated_hours=0.5,
                complexity=TaskComplexity.TRIVIAL,
                required_files=["{module_path}/__init__.py"],
                test_files=[],
                tags=["setup", "structure"],
                checklist=[
                    "Create directory structure",
                    "Add __init__.py files",
                    "Setup imports",
                    "Define __all__ exports",
                    "Add module docstring"
                ]
            ),
            "implement_interface": TaskTemplate(
                name="implement_interface",
                category=TaskCategory.API,
                description_template="Implement {interface_name} with methods: {methods}",
                estimated_hours=2.0,
                complexity=TaskComplexity.MODERATE,
                required_files=["interfaces/{interface_name}.py"],
                test_files=["tests/test_interfaces/test_{interface_name}.py"],
                tags=["interface", "abc", "abstract"],
                checklist=[
                    "Define abstract base class",
                    "Add abstract methods",
                    "Implement concrete class",
                    "Add type hints",
                    "Write interface tests"
                ]
            ),
        }
    
    def _load_rules(self):
        """Load decomposition rules."""
        default_rules = self._get_default_rules()
        
        saved_rules = self.state.get('rules', [])
        for rule_data in saved_rules:
            # Reconstruct templates
            templates = [TaskTemplate(**t) for t in rule_data.get('template_tasks', [])]
            rule = DecompositionRule(
                pattern=rule_data['pattern'],
                category=TaskCategory(rule_data['category']),
                template_tasks=templates,
                priority=rule_data.get('priority', 0)
            )
            self.rules.append(rule)
        
        # Add defaults if none
        if not self.rules:
            self.rules = default_rules
            self._save_rules()
    
    def _save_rules(self):
        """Save decomposition rules."""
        data = []
        for rule in self.rules:
            data.append({
                'pattern': rule.pattern,
                'category': rule.category.value,
                'template_tasks': [t.__dict__ for t in rule.template_tasks],
                'priority': rule.priority
            })
        self.state.set('rules', data)
        self.state.save()
    
    def _get_default_rules(self) -> List[DecompositionRule]:
        """Get default decomposition rules."""
        return [
            DecompositionRule(
                pattern=r"(?i)pars(e|ing).*docx",
                category=TaskCategory.PARSER,
                template_tasks=[
                    self.templates["setup_module"],
                    self.templates["create_reader"],
                    self.templates["create_parser"],
                    self.templates["write_tests"],
                    self.templates["add_documentation"],
                ],
                priority=10
            ),
            DecompositionRule(
                pattern=r"(?i)convert.*to.*usdm",
                category=TaskCategory.CONVERTER,
                template_tasks=[
                    self.templates["create_converter"],
                    self.templates["add_validation"],
                    self.templates["write_tests"],
                ],
                priority=10
            ),
            DecompositionRule(
                pattern=r"(?i)new.*model|create.*schema",
                category=TaskCategory.MODEL,
                template_tasks=[
                    self.templates["create_model"],
                    self.templates["add_validation"],
                    self.templates["write_tests"],
                ],
                priority=5
            ),
        ]
    
    def _load_historical_data(self):
        """Load historical task data for learning."""
        # Load from progress tracker
        for task in self.progress_tracker.tasks.values():
            if task.status == TaskStatus.COMPLETED:
                self.historical_tasks.append(task)
        
        logger.info(f"Loaded {len(self.historical_tasks)} historical tasks")
    
    # ============================================================
    # AI-POWERED DECOMPOSITION
    # ============================================================
    
    def decompose_epic(self, 
                       epic: Epic,
                       use_ai: bool = True,
                       max_tasks: int = 20) -> DecompositionResult:
        """
        Decompose an epic into actionable tasks.
        
        Args:
            epic: The epic to decompose
            use_ai: Whether to use AI for decomposition
            max_tasks: Maximum number of tasks to generate
            
        Returns:
            DecompositionResult with tasks and dependencies
        """
        logger.info(f"Decomposing epic: {epic.title}")
        
        # Try rule-based decomposition first
        tasks, dependencies = self._apply_rules(epic)
        
        if not tasks and use_ai:
            # Use AI for decomposition
            tasks, dependencies = self._ai_decompose(epic, max_tasks)
        
        if not tasks:
            # Fallback to manual template
            tasks, dependencies = self._fallback_decompose(epic)
        
        # Post-process tasks
        tasks = self._post_process_tasks(tasks, epic)
        
        # Estimate hours
        total_hours = sum(t.estimated_hours for t in tasks)
        
        # Suggest sprint allocation
        sprint_allocation = self._suggest_sprint_allocation(tasks, dependencies)
        
        # Identify risks
        risks = self._identify_risks(tasks, dependencies)
        
        # Document assumptions
        assumptions = self._document_assumptions(epic, tasks)
        
        result = DecompositionResult(
            epic=epic,
            tasks=tasks,
            dependencies=dependencies,
            estimated_total_hours=total_hours,
            suggested_sprint_allocation=sprint_allocation,
            risks=risks,
            assumptions=assumptions
        )
        
        # Save to progress tracker
        self._save_to_tracker(result)
        
        logger.info(f"Decomposed into {len(tasks)} tasks, estimated {total_hours:.1f}h")
        return result
    
    def _apply_rules(self, epic: Epic) -> Tuple[List[Task], List[TaskDependency]]:
        """Apply decomposition rules to epic."""
        tasks = []
        dependencies = []
        
        # Sort rules by priority (highest first)
        sorted_rules = sorted(self.rules, key=lambda r: -r.priority)
        
        for rule in sorted_rules:
            if re.search(rule.pattern, epic.title) or re.search(rule.pattern, epic.description):
                logger.debug(f"Matched rule: {rule.pattern}")
                
                # Apply templates
                prev_task_id = None
                for template in rule.template_tasks:
                    task = self._instantiate_template(template, epic)
                    tasks.append(task)
                    
                    if prev_task_id:
                        dependencies.append(TaskDependency(
                            source_id=prev_task_id,
                            target_id=task.id,
                            dep_type=DependencyType.REQUIRES,
                            reason=f"Generated from rule: {rule.pattern}"
                        ))
                    prev_task_id = task.id
                
                break  # Only apply first matching rule
        
        return tasks, dependencies
    
    def _ai_decompose(self, epic: Epic, max_tasks: int) -> Tuple[List[Task], List[TaskDependency]]:
        """Use AI to decompose epic."""
        prompt = f"""
        Decompose this development epic into specific, actionable tasks:
        
        Epic Title: {epic.title}
        Epic Description: {epic.description}
        
        Available task templates:
        {json.dumps([{'name': n, 'category': t.category.value, 'description': t.description_template} 
                     for n, t in self.templates.items()], indent=2)}
        
        Historical similar tasks:
        {self._get_similar_historical_tasks(epic.title, limit=5)}
        
        Requirements:
        1. Each task should be completable in 1-8 hours
        2. Tasks should have clear acceptance criteria
        3. Identify dependencies between tasks
        4. Maximum {max_tasks} tasks
        5. Use appropriate task categories
        
        Return a JSON object with:
        - tasks: List of tasks with title, description, category, estimated_hours, priority (1-5)
        - dependencies: List of {{source_task_index, target_task_index, reason}}
        """
        
        response = self.llm.complete_json(prompt)
        
        tasks = []
        dependencies = []
        
        for task_data in response.get('tasks', []):
            task = Task(
                id=self._generate_task_id(task_data['title'], epic.title),
                title=task_data['title'],
                description=task_data['description'],
                module_name=self._infer_module_name(epic),
                priority=Priority.MEDIUM if task_data.get('priority', 3) >= 3 else Priority.HIGH,
                estimated_hours=task_data.get('estimated_hours', 2.0),
                tags=task_data.get('tags', [])
            )
            tasks.append(task)
        
        for dep_data in response.get('dependencies', []):
            if dep_data['source_task_index'] < len(tasks) and dep_data['target_task_index'] < len(tasks):
                dependencies.append(TaskDependency(
                    source_id=tasks[dep_data['source_task_index']].id,
                    target_id=tasks[dep_data['target_task_index']].id,
                    dep_type=DependencyType.REQUIRES,
                    reason=dep_data.get('reason', '')
                ))
        
        return tasks, dependencies
    
    def _fallback_decompose(self, epic: Epic) -> Tuple[List[Task], List[TaskDependency]]:
        """Fallback decomposition when rules and AI fail."""
        tasks = []
        
        # Create at least one task
        task = Task(
            id=self._generate_task_id(f"Implement {epic.title}", self._infer_module_name(epic)),
            title=f"Implement {epic.title}",
            description=epic.description or f"Implementation task for {epic.title}",
            module_name=self._infer_module_name(epic),
            priority=Priority.MEDIUM,
            estimated_hours=4.0
        )
        tasks.append(task)
        
        return tasks, []
    
    def _instantiate_template(self, template: TaskTemplate, epic: Epic) -> Task:
        """Create a task from a template."""
        # Extract variables from epic
        variables = self._extract_variables(epic)
        
        # Format description
        description = template.description_template.format(**variables)
        
        # Generate task ID
        task_id = self._generate_task_id(template.name, epic.title)
        
        return Task(
            id=task_id,
            title=f"[{template.category.value}] {template.name.replace('_', ' ').title()}",
            description=description,
            module_name=self._infer_module_name(epic),
            priority=Priority.MEDIUM,
            estimated_hours=template.estimated_hours,
            tags=template.tags.copy(),
            metadata={
                'template': template.name,
                'checklist': template.checklist,
                'required_files': template.required_files,
                'test_files': template.test_files
            }
        )
    
    def _extract_variables(self, epic: Epic) -> Dict[str, str]:
        """Extract variables from epic for template filling."""
        variables = {
            'name': epic.title.lower().replace(' ', '_'),
            'module_name': self._infer_module_name(epic),
            'format': 'unknown',
            'target_model': 'UnknownModel',
            'source_model': 'UnknownSource',
            'fields': 'all fields',
            'extract_fields': 'all elements',
            'conversion_rules': 'standard mapping',
            'elements': 'all XML elements',
            'source': 'document',
            'output_spec': 'standard format',
            'target': epic.title,
            'validation_rules': 'required fields and types',
            'coverage': '90',
            'module_path': f"modules/{self._infer_module_name(epic)}",
            'interface_name': f"I{epic.title.replace(' ', '')}",
            'methods': 'defined methods'
        }
        
        # Try to extract format from title
        format_match = re.search(r'(?i)(docx|pdf|html|markdown|json|xml|csv|excel)', epic.title)
        if format_match:
            variables['format'] = format_match.group(1).lower()
        
        return variables
    
    def _infer_module_name(self, epic: Epic) -> str:
        """Infer module name from epic."""
        # Try to extract from tags
        for tag in epic.tags:
            if tag.startswith('module:'):
                return tag[7:]
        
        # Default based on title
        return epic.title.lower().replace(' ', '_').replace('-', '_')[:30]
    
    def _generate_task_id(self, base: str, context: str) -> str:
        """Generate unique task ID."""
        clean_base = re.sub(r'[^a-zA-Z0-9_]', '_', base.lower())[:20]
        clean_context = re.sub(r'[^a-zA-Z0-9_]', '_', context.lower())[:10]
        task_id = f"TASK_{clean_context}_{clean_base}"
        
        # Ensure uniqueness
        counter = 1
        original_id = task_id
        while task_id in self.progress_tracker.tasks:
            task_id = f"{original_id}_{counter}"
            counter += 1
        
        return task_id
    
    def _post_process_tasks(self, tasks: List[Task], epic: Epic) -> List[Task]:
        """Post-process generated tasks."""
        for task in tasks:
            # Add epic reference
            task.metadata['epic_id'] = epic.id
            
            # Set default priority if not set
            if not task.priority:
                task.priority = Priority.MEDIUM
            
            # Add to epic's task list
            if task.id not in epic.tasks:
                epic.tasks.append(task.id)
        
        return tasks
    
    def _suggest_sprint_allocation(self, tasks: List[Task], dependencies: List[TaskDependency]) -> Dict[str, List[str]]:
        """Suggest how to allocate tasks across sprints."""
        if not tasks:
            return {}
        
        # Build dependency graph
        graph = defaultdict(list)
        in_degree = defaultdict(int)
        
        for dep in dependencies:
            graph[dep.source_id].append(dep.target_id)
            in_degree[dep.target_id] += 1
        
        # Topological sort
        sprints = {}
        sprint_num = 1
        sprint_hours = 0
        MAX_SPRINT_HOURS = 40  # 1 week sprint
        
        # Tasks with no dependencies can go first
        ready = [t for t in tasks if in_degree[t.id] == 0]
        completed = set()
        
        while ready:
            sprint_tasks = []
            
            for task in sorted(ready, key=lambda t: t.priority.value):
                if sprint_hours + task.estimated_hours <= MAX_SPRINT_HOURS:
                    sprint_tasks.append(task.id)
                    sprint_hours += task.estimated_hours
                    completed.add(task.id)
            
            if sprint_tasks:
                sprints[f"Sprint {sprint_num}"] = sprint_tasks
                sprint_num += 1
                sprint_hours = 0
            
            # Find next ready tasks
            ready = []
            for task in tasks:
                if task.id in completed:
                    continue
                if all(dep.source_id in completed for dep in dependencies if dep.target_id == task.id):
                    ready.append(task)
        
        # Any remaining tasks go to final sprint
        remaining = [t.id for t in tasks if t.id not in completed]
        if remaining:
            sprints[f"Sprint {sprint_num}"] = remaining
        
        return sprints
    
    def _identify_risks(self, tasks: List[Task], dependencies: List[TaskDependency]) -> List[str]:
        """Identify risks in the task plan."""
        risks = []
        
        # Check for circular dependencies
        graph = defaultdict(list)
        for dep in dependencies:
            graph[dep.source_id].append(dep.target_id)
        
        visited = set()
        rec_stack = set()
        
        def has_cycle(node: str) -> bool:
            visited.add(node)
            rec_stack.add(node)
            for neighbor in graph[node]:
                if neighbor not in visited:
                    if has_cycle(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True
            rec_stack.remove(node)
            return False
        
        for task in tasks:
            if task.id not in visited:
                if has_cycle(task.id):
                    risks.append("Circular dependency detected in task dependencies")
                    break
        
        # Check for high-complexity tasks
        high_complexity = [t for t in tasks if t.estimated_hours > 8]
        if high_complexity:
            risks.append(f"{len(high_complexity)} tasks estimated over 8 hours - consider further decomposition")
        
        # Check for too many dependencies
        dep_counts = defaultdict(int)
        for dep in dependencies:
            dep_counts[dep.target_id] += 1
        
        highly_dependent = [tid for tid, count in dep_counts.items() if count > 3]
        if highly_dependent:
            risks.append(f"{len(highly_dependent)} tasks have more than 3 dependencies - may cause bottlenecks")
        
        # Check for unestimated tasks
        unestimated = [t for t in tasks if t.estimated_hours == 0]
        if unestimated:
            risks.append(f"{len(unestimated)} tasks have no time estimate")
        
        return risks
    
    def _document_assumptions(self, epic: Epic, tasks: List[Task]) -> List[str]:
        """Document assumptions made during decomposition."""
        assumptions = [
            f"Tasks are based on current understanding of '{epic.title}'",
            f"All dependencies can be resolved within the project",
            f"Team has necessary skills to complete all tasks",
            f"No external blockers will delay task execution",
            f"Estimated hours are approximate and may vary",
        ]
        
        # Add category-specific assumptions
        categories = set()
        for task in tasks:
            # Infer category from metadata
            if 'template' in task.metadata:
                template = self.templates.get(task.metadata['template'])
                if template:
                    categories.add(template.category)
        
        if TaskCategory.PARSER in categories:
            assumptions.append("Input document format is well-formed and follows specification")
        
        if TaskCategory.TEST in categories:
            assumptions.append("Test environment and fixtures are available")
        
        return assumptions
    
    def _get_similar_historical_tasks(self, query: str, limit: int = 5) -> str:
        """Get similar historical tasks for context."""
        if not self.historical_tasks:
            return "No historical tasks available"
        
        # Simple keyword matching for now
        query_words = set(query.lower().split())
        scored_tasks = []
        
        for task in self.historical_tasks:
            task_text = f"{task.title} {task.description}".lower()
            score = sum(1 for word in query_words if word in task_text)
            if score > 0:
                scored_tasks.append((score, task))
        
        scored_tasks.sort(key=lambda x: -x[0])
        
        result = []
        for score, task in scored_tasks[:limit]:
            result.append(f"- {task.title}: {task.estimated_hours}h, completed in {task.actual_hours:.1f}h")
        
        return "\n".join(result) if result else "No similar tasks found"
    
    # ============================================================
    # WORK BREAKDOWN STRUCTURE
    # ============================================================
    
    def create_wbs(self, epic: Epic, decomposition: Optional[DecompositionResult] = None) -> WorkBreakdownStructure:
        """Create a hierarchical work breakdown structure."""
        if decomposition is None:
            decomposition = self.decompose_epic(epic)
        
        root = WBSNode(
            id="WBS_ROOT",
            title=epic.title,
            level=0,
            category=None,
            estimated_hours=decomposition.estimated_total_hours
        )
        
        # Group tasks by category
        tasks_by_category = defaultdict(list)
        for task in decomposition.tasks:
            category = self._infer_task_category(task)
            tasks_by_category[category].append(task)
        
        max_depth = 0
        total_tasks = 0
        
        # Create category nodes
        for category, category_tasks in tasks_by_category.items():
            category_node = WBSNode(
                id=f"WBS_CAT_{category.value}",
                title=category.value.replace('_', ' ').title(),
                level=1,
                category=category,
                estimated_hours=sum(t.estimated_hours for t in category_tasks)
            )
            
            # Add task nodes
            for task in category_tasks:
                task_node = WBSNode(
                    id=f"WBS_TASK_{task.id}",
                    title=task.title,
                    level=2,
                    category=category,
                    estimated_hours=task.estimated_hours,
                    task_id=task.id
                )
                category_node.children.append(task_node)
                total_tasks += 1
            
            root.children.append(category_node)
            max_depth = max(max_depth, 2)
        
        return WorkBreakdownStructure(
            root=root,
            max_depth=max_depth,
            total_tasks=total_tasks,
            total_hours=decomposition.estimated_total_hours
        )
    
    def _infer_task_category(self, task: Task) -> TaskCategory:
        """Infer task category from task data."""
        # Check metadata
        if 'template' in task.metadata:
            template = self.templates.get(task.metadata['template'])
            if template:
                return template.category
        
        # Infer from tags
        for tag in task.tags:
            try:
                return TaskCategory(tag)
            except ValueError:
                pass
        
        # Infer from title
        title_lower = task.title.lower()
        if 'test' in title_lower:
            return TaskCategory.TEST
        elif 'doc' in title_lower:
            return TaskCategory.DOCUMENTATION
        elif 'model' in title_lower or 'schema' in title_lower:
            return TaskCategory.MODEL
        elif 'parse' in title_lower:
            return TaskCategory.PARSER
        elif 'convert' in title_lower:
            return TaskCategory.CONVERTER
        elif 'validate' in title_lower:
            return TaskCategory.VALIDATION
        
        return TaskCategory.LOGIC
    
    # ============================================================
    # VALIDATION
    # ============================================================
    
    def validate_decomposition(self, result: DecompositionResult) -> Tuple[bool, List[str]]:
        """Validate a decomposition result."""
        issues = []
        
        # Check for tasks
        if not result.tasks:
            issues.append("No tasks generated")
            return False, issues
        
        # Check task completeness
        for task in result.tasks:
            if not task.title:
                issues.append(f"Task {task.id} has no title")
            if not task.description:
                issues.append(f"Task {task.id} has no description")
            if task.estimated_hours <= 0:
                issues.append(f"Task {task.id} has invalid estimated hours: {task.estimated_hours}")
            if task.estimated_hours > 16:
                issues.append(f"Task {task.id} is too large ({task.estimated_hours}h) - consider splitting")
        
        # Check dependency validity
        task_ids = {t.id for t in result.tasks}
        for dep in result.dependencies:
            if dep.source_id not in task_ids:
                issues.append(f"Dependency source {dep.source_id} not in tasks")
            if dep.target_id not in task_ids:
                issues.append(f"Dependency target {dep.target_id} not in tasks")
            if dep.source_id == dep.target_id:
                issues.append(f"Self-dependency detected for {dep.source_id}")
        
        # Check for orphaned tasks (no dependencies and not depended on)
        has_dependency = set()
        for dep in result.dependencies:
            has_dependency.add(dep.source_id)
            has_dependency.add(dep.target_id)
        
        orphans = [t.id for t in result.tasks if t.id not in has_dependency]
        if len(orphans) == len(result.tasks) and len(result.tasks) > 1:
            issues.append("No dependencies defined between tasks - tasks may be too isolated")
        
        return len(issues) == 0, issues
    
    # ============================================================
    # INTEGRATION
    # ============================================================
    
    def _save_to_tracker(self, result: DecompositionResult):
        """Save decomposition result to progress tracker."""
        # Add tasks to tracker
        for task in result.tasks:
            if task.id not in self.progress_tracker.tasks:
                self.progress_tracker.tasks[task.id] = task
        
        # Update epic with tasks
        if result.epic.id in self.progress_tracker.epics:
            epic = self.progress_tracker.epics[result.epic.id]
            for task in result.tasks:
                if task.id not in epic.tasks:
                    epic.tasks.append(task.id)
        
        self.progress_tracker._save_state()
    
    def import_from_architecture(self, modules: List[Dict[str, Any]]):
        """Import tasks from architecture module plans."""
        for module_data in modules:
            module_name = module_data.get('name', '')
            
            for task_data in module_data.get('tasks', []):
                task = Task(
                    id=self._generate_task_id(task_data.get('title', 'Task'), module_name),
                    title=task_data.get('title', 'Untitled Task'),
                    description=task_data.get('description', ''),
                    module_name=module_name,
                    priority=Priority(task_data.get('priority', 'medium').lower()),
                    estimated_hours=task_data.get('estimated_hours', 1.0),
                    dependencies=task_data.get('dependencies', []),
                    tags=task_data.get('tags', [])
                )
                
                if task.id not in self.progress_tracker.tasks:
                    self.progress_tracker.tasks[task.id] = task
                    logger.info(f"Imported task: {task.id}")
        
        self.progress_tracker._save_state()
    
    # ============================================================
    # EXPORT AND REPORTING
    # ============================================================
    
    def export_wbs_markdown(self, wbs: WorkBreakdownStructure) -> str:
        """Export WBS as markdown."""
        lines = [
            f"# Work Breakdown Structure: {wbs.root.title}",
            "",
            f"**Total Tasks:** {wbs.total_tasks}",
            f"**Total Estimated Hours:** {wbs.total_hours:.1f}h",
            "",
            "## Structure",
            ""
        ]
        
        def render_node(node: WBSNode, indent: int = 0) -> List[str]:
            result = []
            prefix = "  " * indent + "- "
            
            if node.task_id:
                task = self.progress_tracker.tasks.get(node.task_id)
                status = task.status.value if task else "unknown"
                result.append(f"{prefix}**{node.title}** ({node.estimated_hours:.1f}h) - *{status}*")
            else:
                result.append(f"{prefix}**{node.title}** ({node.estimated_hours:.1f}h)")
            
            for child in node.children:
                result.extend(render_node(child, indent + 1))
            
            return result
        
        lines.extend(render_node(wbs.root))
        
        return "\n".join(lines)
    
    def export_decomposition_json(self, result: DecompositionResult) -> str:
        """Export decomposition as JSON."""
        data = {
            'epic': {
                'id': result.epic.id,
                'title': result.epic.title,
                'description': result.epic.description
            },
            'tasks': [
                {
                    'id': t.id,
                    'title': t.title,
                    'description': t.description,
                    'module_name': t.module_name,
                    'priority': t.priority.value,
                    'estimated_hours': t.estimated_hours,
                    'dependencies': t.dependencies,
                    'tags': t.tags,
                    'metadata': t.metadata
                }
                for t in result.tasks
            ],
            'dependencies': [
                {
                    'source': d.source_id,
                    'target': d.target_id,
                    'type': d.dep_type.value,
                    'reason': d.reason
                }
                for d in result.dependencies
            ],
            'estimated_total_hours': result.estimated_total_hours,
            'sprint_allocation': result.suggested_sprint_allocation,
            'risks': result.risks,
            'assumptions': result.assumptions,
            'generated_at': result.generated_at.isoformat()
        }
        
        return json.dumps(data, indent=2)
    
    def generate_decomposition_report(self, result: DecompositionResult) -> str:
        """Generate a comprehensive decomposition report."""
        valid, issues = self.validate_decomposition(result)
        
        lines = [
            f"# Task Decomposition Report",
            f"",
            f"**Epic:** {result.epic.title}",
            f"**Generated:** {result.generated_at.strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Validation:** {'✓ PASSED' if valid else '✗ FAILED'}",
            f"",
            f"## Summary",
            f"",
            f"- **Total Tasks:** {len(result.tasks)}",
            f"- **Total Estimated Hours:** {result.estimated_total_hours:.1f}h",
            f"- **Suggested Sprints:** {len(result.suggested_sprint_allocation)}",
            f"",
            f"## Tasks by Sprint",
            f"",
        ]
        
        for sprint, task_ids in result.suggested_sprint_allocation.items():
            lines.append(f"### {sprint}")
            lines.append("")
            sprint_hours = 0
            for task_id in task_ids:
                task = next((t for t in result.tasks if t.id == task_id), None)
                if task:
                    lines.append(f"- [{task.priority.value.upper()}] **{task.title}** - {task.estimated_hours:.1f}h")
                    sprint_hours += task.estimated_hours
            lines.append(f"\n*Sprint Total: {sprint_hours:.1f}h*")
            lines.append("")
        
        if result.risks:
            lines.append("## Risks")
            lines.append("")
            for risk in result.risks:
                lines.append(f"- ⚠️ {risk}")
            lines.append("")
        
        if result.assumptions:
            lines.append("## Assumptions")
            lines.append("")
            for assumption in result.assumptions:
                lines.append(f"- {assumption}")
            lines.append("")
        
        if issues:
            lines.append("## Validation Issues")
            lines.append("")
            for issue in issues:
                lines.append(f"- ❌ {issue}")
            lines.append("")
        
        lines.append("## All Tasks")
        lines.append("")
        lines.append("| ID | Title | Category | Hours | Dependencies |")
        lines.append("|----|-------|----------|-------|--------------|")
        
        for task in result.tasks:
            category = self._infer_task_category(task).value
            deps = ", ".join(d.target_id[:8] for d in result.dependencies if d.source_id == task.id) or "-"
            lines.append(f"| {task.id[:12]} | {task.title[:30]} | {category} | {task.estimated_hours:.1f} | {deps} |")
        
        return "\n".join(lines)


# ============================================================
# CLI ENTRY POINT
# ============================================================

def main():
    """CLI entry point for task decomposer."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Decompose epics into actionable tasks")
    parser.add_argument("--project-root", type=Path, default=Path.cwd(),
                       help="Project root directory")
    parser.add_argument("--epic-title", type=str, required=True,
                       help="Title of the epic to decompose")
    parser.add_argument("--epic-description", type=str, default="",
                       help="Description of the epic")
    parser.add_argument("--output", "-o", type=Path,
                       help="Output report path")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown",
                       help="Output format")
    parser.add_argument("--no-ai", action="store_true",
                       help="Disable AI-powered decomposition")
    parser.add_argument("--max-tasks", type=int, default=20,
                       help="Maximum number of tasks to generate")
    parser.add_argument("--wbs", action="store_true",
                       help="Generate Work Breakdown Structure")
    
    args = parser.parse_args()
    
    decomposer = TaskDecomposer(args.project_root)
    
    # Create epic
    epic = Epic(
        id=f"EPIC_{args.epic_title.lower().replace(' ', '_')[:30]}",
        title=args.epic_title,
        description=args.epic_description
    )
    
    # Decompose
    result = decomposer.decompose_epic(
        epic,
        use_ai=not args.no_ai,
        max_tasks=args.max_tasks
    )
    
    if args.wbs:
        wbs = decomposer.create_wbs(epic, result)
        output = decomposer.export_wbs_markdown(wbs)
    elif args.format == "json":
        output = decomposer.export_decomposition_json(result)
    else:
        output = decomposer.generate_decomposition_report(result)
    
    if args.output:
        args.output.write_text(output)
        print(f"Report saved to {args.output}")
    else:
        print(output)


if __name__ == "__main__":
    main()