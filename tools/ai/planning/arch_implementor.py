"""
Architecture Implementation Tool
Creates folder structure, module skeletons, and task lists from finalized architecture.

Workflow:
1. Load finalized architecture document
2. Create directory structure
3. Generate module skeleton files with docstrings
4. Create feature plan documents
5. Generate task lists for each module
6. Create tracking state for implementation progress
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import shutil

from ..shared.llm_client import LLMClient
from ..shared.state_manager import StateManager
from ..shared.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ModuleTask:
    """A single implementation task."""
    id: str
    module_name: str
    title: str
    description: str
    priority: int  # 1-5
    estimated_hours: float
    dependencies: List[str] = field(default_factory=list)
    status: str = 'pending'  # pending, in_progress, completed, blocked
    assigned_to: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    notes: List[str] = field(default_factory=list)


@dataclass
class ModulePlan:
    """Implementation plan for a single module."""
    module_name: str
    module_path: Path
    description: str
    responsibilities: List[str]
    public_api: List[Dict[str, str]]  # name, type, signature, description
    dependencies: List[str]
    tasks: List[ModuleTask]
    status: str = 'planned'
    progress: float = 0.0


class ArchitectureImplementor:
    """
    Implements architecture by creating structure and task plans.
    
    Features:
    - Parse finalized architecture document
    - Create directory structure with __init__.py files
    - Generate module skeletons with proper imports
    - Create feature plan documents (markdown)
    - Generate detailed task lists with AI assistance
    - Track implementation progress
    - Validate against architecture
    """
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.llm = LLMClient()
        self.state = StateManager(project_root / ".ai_state" / "arch_implementor.json")
        
        self.arch_path = project_root / "project_doc" / "architecture" / "current" / "architecture.json"
        self.plans_path = project_root / "project_doc" / "modules"
        self.plans_path.mkdir(parents=True, exist_ok=True)
        
        self.architecture: Optional[Dict[str, Any]] = None
        self.module_plans: Dict[str, ModulePlan] = {}
    
    def load_architecture(self) -> Dict[str, Any]:
        """Load finalized architecture document."""
        if not self.arch_path.exists():
            raise FileNotFoundError(f"Architecture document not found: {self.arch_path}")
        
        with open(self.arch_path, 'r') as f:
            self.architecture = json.load(f)
        
        logger.info(f"Loaded architecture v{self.architecture.get('version')}")
        return self.architecture
    
    def create_directory_structure(self) -> List[Path]:
        """Create all directories defined in architecture."""
        created = []
        
        # Create main source directory if specified
        source_root = self.architecture.get('source_root', 'engines/document')
        source_path = self.project_root / source_root
        source_path.mkdir(parents=True, exist_ok=True)
        
        # Create package directories
        for package in self.architecture.get('packages', []):
            package_path = source_path / package['name'].replace('.', '/')
            package_path.mkdir(parents=True, exist_ok=True)
            
            # Create __init__.py
            init_file = package_path / "__init__.py"
            if not init_file.exists():
                init_content = self._generate_init_content(package)
                init_file.write_text(init_content)
            
            created.append(package_path)
            logger.info(f"Created package: {package_path}")
        
        # Create module directories (subpackages within packages)
        for module in self.architecture.get('modules', []):
            module_path = self._resolve_module_path(module['name'], source_path)
            if module_path:
                module_path.mkdir(parents=True, exist_ok=True)
                
                # Create __init__.py
                init_file = module_path / "__init__.py"
                if not init_file.exists():
                    init_content = self._generate_module_init(module)
                    init_file.write_text(init_content)
                
                created.append(module_path)
                logger.info(f"Created module: {module_path}")
        
        return created
    
    def _resolve_module_path(self, module_name: str, source_root: Path) -> Optional[Path]:
        """Resolve module name to filesystem path."""
        # Handle nested modules (e.g., 'parsers.docx_parser.readers')
        parts = module_name.split('.')
        
        # Find which package this belongs to
        for package in self.architecture.get('packages', []):
            if module_name.startswith(package['name']):
                relative_path = module_name[len(package['name'])+1:].replace('.', '/')
                return source_root / package['name'].replace('.', '/') / relative_path
        
        return None
    
    def _generate_init_content(self, package: Dict[str, Any]) -> str:
        """Generate __init__.py content for a package."""
        prompt = f"""
        Generate a Python __init__.py file for package: {package['name']}
        
        Description: {package.get('description', '')}
        Modules in package: {package.get('modules', [])}
        
        Include:
        1. Module docstring describing package purpose
        2. Imports for key modules (if appropriate)
        3. __all__ list defining public exports
        
        Output only valid Python code.
        """
        
        return self.llm.complete(prompt)
    
    def _generate_module_init(self, module: Dict[str, Any]) -> str:
        """Generate __init__.py content for a module."""
        prompt = f"""
        Generate a Python __init__.py file for module: {module['name']}
        
        Description: {module.get('description', '')}
        Responsibilities: {module.get('responsibilities', [])}
        Public API: {module.get('public_api', [])}
        
        Include:
        1. Module docstring describing module purpose and responsibilities
        2. Imports for internal submodules
        3. __all__ list defining public exports
        
        Output only valid Python code.
        """
        
        return self.llm.complete(prompt)
    
    def generate_module_plan(self, module: Dict[str, Any]) -> ModulePlan:
        """Generate detailed implementation plan for a module."""
        prompt = f"""
        Create a detailed implementation plan for this Python module:
        
        Module: {module['name']}
        Description: {module.get('description', '')}
        Responsibilities: {module.get('responsibilities', [])}
        Dependencies: {module.get('dependencies', [])}
        
        Architecture context: {json.dumps(self.architecture.get('overview', ''), indent=2)}
        
        Generate:
        1. Clear module description (2-3 sentences)
        2. List of responsibilities (bullet points)
        3. Public API specification (list of classes/functions with signatures)
        4. Detailed task list with:
           - Task ID
           - Title
           - Description
           - Priority (1-5)
           - Estimated hours
           - Dependencies on other tasks
        5. Suggested implementation order
        
        Return as JSON with keys: description, responsibilities, public_api, tasks.
        """
        
        response = self.llm.complete(prompt, response_format="json")
        data = json.loads(response)
        
        # Convert tasks to ModuleTask objects
        tasks = []
        for task_data in data.get('tasks', []):
            task = ModuleTask(
                id=f"{module['name']}_task_{len(tasks)+1:03d}",
                module_name=module['name'],
                title=task_data.get('title', ''),
                description=task_data.get('description', ''),
                priority=task_data.get('priority', 3),
                estimated_hours=task_data.get('estimated_hours', 1.0),
                dependencies=task_data.get('dependencies', [])
            )
            tasks.append(task)
        
        module_path = self._resolve_module_path(module['name'], self.project_root)
        
        plan = ModulePlan(
            module_name=module['name'],
            module_path=module_path or Path(),
            description=data.get('description', ''),
            responsibilities=data.get('responsibilities', []),
            public_api=data.get('public_api', []),
            dependencies=module.get('dependencies', []),
            tasks=tasks
        )
        
        self.module_plans[module['name']] = plan
        return plan
    
    def generate_all_module_plans(self) -> Dict[str, ModulePlan]:
        """Generate plans for all modules in architecture."""
        for module in self.architecture.get('modules', []):
            plan = self.generate_module_plan(module)
            self._save_module_plan(plan)
        
        return self.module_plans
    
    def _save_module_plan(self, plan: ModulePlan):
        """Save module plan to markdown file."""
        plan_file = self.plans_path / f"{plan.module_name.replace('.', '_')}_plan.md"
        
        content = f"""# {plan.module_name} Implementation Plan

## Description
{plan.description}

## Responsibilities
{chr(10).join(f'- {r}' for r in plan.responsibilities)}

## Public API
{chr(10).join(f'- `{api["name"]}`: {api.get("description", "")}' for api in plan.public_api)}

## Dependencies
{chr(10).join(f'- {d}' for d in plan.dependencies) if plan.dependencies else '- None'}

## Tasks

| ID | Title | Priority | Hours | Dependencies | Status |
|----|-------|----------|-------|--------------|--------|
{chr(10).join(f"| {t.id} | {t.title} | {t.priority} | {t.estimated_hours} | {', '.join(t.dependencies) or '-'} | {t.status} |" for t in plan.tasks)}

## Progress
- Total Tasks: {len(plan.tasks)}
- Completed: {sum(1 for t in plan.tasks if t.status == 'completed')}
- Progress: {plan.progress * 100:.1f}%

---
*Generated: {datetime.now().isoformat()}*
"""
        
        plan_file.write_text(content)
        logger.info(f"Saved module plan: {plan_file}")
    
    def generate_skeleton_code(self, module: Dict[str, Any]) -> List[Path]:
        """Generate skeleton Python files for a module."""
        created = []
        
        prompt = f"""
        Generate skeleton Python code for module: {module['name']}
        
        Description: {module.get('description', '')}
        Public API: {module.get('public_api', [])}
        Dependencies: {module.get('dependencies', [])}
        
        For each file needed in this module, provide:
        1. File path (relative to module)
        2. Complete file content with:
           - Module docstring
           - Import statements
           - Class/function stubs with docstrings and type hints
           - TODO comments for implementation
        
        Return as JSON with keys: files (list of {{path, content}}).
        """
        
        response = self.llm.complete(prompt, response_format="json")
        data = json.loads(response)
        
        module_path = self._resolve_module_path(module['name'], self.project_root)
        if not module_path:
            return created
        
        for file_info in data.get('files', []):
            file_path = module_path / file_info['path']
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            if not file_path.exists():
                file_path.write_text(file_info['content'])
                created.append(file_path)
                logger.info(f"Created skeleton: {file_path}")
        
        return created
    
    def generate_feature_plan_document(self) -> Path:
        """Generate comprehensive feature plan document from architecture."""
        prompt = f"""
        Generate a comprehensive feature plan document from this architecture:
        
        {json.dumps(self.architecture, indent=2)}
        
        Include:
        1. Executive summary
        2. Feature breakdown by module
        3. Implementation phases with timeline estimates
        4. Dependencies between features
        5. Success criteria for each feature
        6. Testing strategy
        
        Format as well-structured markdown.
        """
        
        content = self.llm.complete(prompt)
        
        doc_path = self.project_root / "project_doc" / "feature_plan.md"
        doc_path.write_text(content)
        
        logger.info(f"Generated feature plan: {doc_path}")
        return doc_path
    
    def update_task_status(self, module_name: str, task_id: str, status: str, notes: Optional[str] = None):
        """Update status of a specific task."""
        if module_name not in self.module_plans:
            raise ValueError(f"Module {module_name} not found")
        
        plan = self.module_plans[module_name]
        for task in plan.tasks:
            if task.id == task_id:
                task.status = status
                if notes:
                    task.notes.append(notes)
                if status == 'completed':
                    task.completed_at = datetime.now()
                
                # Recalculate progress
                completed = sum(1 for t in plan.tasks if t.status == 'completed')
                plan.progress = completed / len(plan.tasks) if plan.tasks else 0
                
                self._save_module_plan(plan)
                self.state.save()
                return
        
        raise ValueError(f"Task {task_id} not found in module {module_name}")
    
    def execute(self):
        """Main execution method - creates everything from architecture."""
        print("\n" + "="*60)
        print("Architecture Implementation Tool")
        print("="*60)
        
        self.load_architecture()
        print(f"\nLoaded: {self.architecture.get('project_name')} v{self.architecture.get('version')}")
        
        print("\nCreating directory structure...")
        dirs = self.create_directory_structure()
        print(f"Created {len(dirs)} directories")
        
        print("\nGenerating module plans...")
        plans = self.generate_all_module_plans()
        print(f"Generated plans for {len(plans)} modules")
        
        print("\nGenerating skeleton code...")
        total_files = 0
        for module in self.architecture.get('modules', []):
            files = self.generate_skeleton_code(module)
            total_files += len(files)
        print(f"Generated {total_files} skeleton files")
        
        print("\nGenerating feature plan document...")
        doc = self.generate_feature_plan_document()
        print(f"Generated: {doc}")
        
        print("\n" + "="*60)
        print("Implementation setup complete!")
        print("="*60)
        print(f"\nNext steps:")
        print(f"1. Review feature plan: {doc}")
        print(f"2. Check module plans in: {self.plans_path}")
        print(f"3. Start implementing tasks (use t1_1_4_1_progress_tracker.py)")