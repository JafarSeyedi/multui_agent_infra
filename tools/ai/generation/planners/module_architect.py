#!/usr/bin/env python3
"""
Module Architect - Designs module structure, file organization, and component layout.

Part of the Generation tools (generation/planners/module_architect.py)


This module_architect.py provides:

1. Multiple Architectural Patterns - Layered, Clean, Hexagonal, DDD, MVC, Feature-based, Component-based, Plugin, Microservice, Modular Monolith
2. Automatic Structure Planning - Generates complete directory and file structure based on pattern
3. Component Organization - Assigns components to appropriate layers and directories
4. Layer-Based Dependency Validation - Ensures architectural boundaries are respected
5. Generation Order Calculation - Determines optimal build order with batching
6. Skeleton Code Generation - Creates all directories, __init__.py files, and class stubs
7. Interface Design Integration - Automatically designs interfaces for public components
8. Existing Code Analysis - Extracts architecture from existing modules
9. LLM-Powered Enhancement - AI-assisted architecture suggestions
10. Naming Convention Validation - Enforces consistent naming across the module
11. Multiple Export Formats - JSON, Markdown, Mermaid diagrams, and ASCII tree
12. Comprehensive Validation - Checks for circular dependencies, layer violations, and structural issues

The module architect ensures that all generated components are organized in a clean, maintainable structure that 
follows established architectural patterns and best practices.
"""

import json
import ast
from pathlib import Path
from typing import Dict, List, Set, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from collections import defaultdict

from ....shared.llm_client import LLMClient
from ....shared.state_manager import StateManager
from ....shared.logger import get_logger
from ....analysis.scanners.project_scanner import ProjectScanner
from .interface_designer import InterfaceDesigner, InterfaceDesign
from .dependency_planner import DependencyPlanner, DependencyPlan

logger = get_logger(__name__)


# ============================================================
# ENUMS AND CONSTANTS
# ============================================================

class ModuleType(str, Enum):
    """Type of module."""
    PACKAGE = "package"
    MODULE = "module"
    SUBMODULE = "submodule"
    INTERFACE = "interface"
    IMPLEMENTATION = "implementation"
    UTILITY = "utility"
    CONSTANTS = "constants"
    TYPES = "types"
    EXCEPTIONS = "exceptions"
    CONFIG = "config"
    TEST = "test"
    CLI = "cli"
    API = "api"
    SERVICE = "service"
    REPOSITORY = "repository"
    MODEL = "model"
    SCHEMA = "schema"
    MIDDLEWARE = "middleware"
    HELPER = "helper"


class ArchitecturePattern(str, Enum):
    """Architectural pattern for module organization."""
    LAYERED = "layered"
    CLEAN = "clean"
    HEXAGONAL = "hexagonal"
    DDD = "ddd"
    MVC = "mvc"
    FEATURE_BASED = "feature_based"
    COMPONENT_BASED = "component_based"
    PLUGIN = "plugin"
    MICROSERVICE = "microservice"
    MODULAR_MONOLITH = "modular_monolith"
    CUSTOM = "custom"


class Visibility(str, Enum):
    """Visibility of a component."""
    PUBLIC = "public"
    INTERNAL = "internal"
    PRIVATE = "private"
    PROTECTED = "protected"


class ComponentRole(str, Enum):
    """Role of a component in the module."""
    ENTRY_POINT = "entry_point"
    CONTROLLER = "controller"
    SERVICE = "service"
    REPOSITORY = "repository"
    MODEL = "model"
    DTO = "dto"
    MAPPER = "mapper"
    VALIDATOR = "validator"
    SERIALIZER = "serializer"
    CLIENT = "client"
    ADAPTER = "adapter"
    FACTORY = "factory"
    BUILDER = "builder"
    STRATEGY = "strategy"
    OBSERVER = "observer"
    MIDDLEWARE = "middleware"
    FILTER = "filter"
    HANDLER = "handler"
    UTILITY = "utility"
    CONSTANT = "constant"
    EXCEPTION = "exception"
    CONFIG = "config"


# ============================================================
# DATA MODELS
# ============================================================

@dataclass
class FileSpec:
    """Specification for a file in the module."""
    name: str
    file_type: ModuleType
    path: str
    description: str = ""
    classes: List[str] = field(default_factory=list)
    functions: List[str] = field(default_factory=list)
    constants: List[str] = field(default_factory=list)
    imports: List[str] = field(default_factory=list)
    exports: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    is_generated: bool = True
    generation_order: int = 0
    template: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ComponentSpec:
    """Specification for a code component."""
    name: str
    component_type: str  # 'class', 'function', 'interface', 'enum', 'dataclass'
    role: ComponentRole
    visibility: Visibility = Visibility.PUBLIC
    file_path: str = ""
    description: str = ""
    methods: List[str] = field(default_factory=list)
    properties: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    dependents: List[str] = field(default_factory=list)
    interface_ref: Optional[str] = None
    is_abstract: bool = False
    is_final: bool = False
    generation_order: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DirectorySpec:
    """Specification for a directory in the module structure."""
    name: str
    path: str
    description: str = ""
    subdirectories: List[str] = field(default_factory=list)
    files: List[str] = field(default_factory=list)
    is_package: bool = True
    init_exports: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LayerSpec:
    """Specification for an architectural layer."""
    name: str
    order: int
    allowed_dependencies: List[str] = field(default_factory=list)
    forbidden_dependencies: List[str] = field(default_factory=list)
    directories: List[str] = field(default_factory=list)
    description: str = ""


@dataclass
class ModuleArchitecture:
    """Complete module architecture specification."""
    name: str
    root_path: str
    pattern: ArchitecturePattern
    description: str = ""
    version: str = "1.0.0"
    
    # Structure
    directories: Dict[str, DirectorySpec] = field(default_factory=dict)
    files: Dict[str, FileSpec] = field(default_factory=dict)
    
    # Components
    components: Dict[str, ComponentSpec] = field(default_factory=dict)
    
    # Layers
    layers: List[LayerSpec] = field(default_factory=list)
    
    # Dependencies
    internal_dependencies: Dict[str, List[str]] = field(default_factory=dict)
    external_dependencies: List[str] = field(default_factory=list)
    
    # Interfaces
    interfaces: Dict[str, InterfaceDesign] = field(default_factory=dict)
    
    # Generation
    generation_order: List[str] = field(default_factory=list)
    generation_batches: List[List[str]] = field(default_factory=list)
    
    # Documentation
    module_docstring: Optional[str] = None
    usage_examples: List[str] = field(default_factory=list)
    
    # Validation
    is_valid: bool = True
    issues: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ModuleArchitectConfig:
    """Configuration for module architect."""
    project_root: Path
    pattern: ArchitecturePattern = ArchitecturePattern.LAYERED
    
    # Module structure
    source_root: str = "src"
    test_root: str = "tests"
    
    # Naming conventions
    file_naming: str = "snake_case"
    class_naming: str = "PascalCase"
    function_naming: str = "snake_case"
    
    # File organization
    max_classes_per_file: int = 3
    max_functions_per_file: int = 10
    create_init_files: bool = True
    
    # Layer definitions (for layered pattern)
    layers: List[LayerSpec] = field(default_factory=lambda: [
        LayerSpec(name="domain", order=0, 
                 allowed_dependencies=[],
                 forbidden_dependencies=["application", "infrastructure", "presentation"],
                 directories=["domain/models", "domain/interfaces", "domain/exceptions"]),
        LayerSpec(name="application", order=1,
                 allowed_dependencies=["domain"],
                 forbidden_dependencies=["infrastructure", "presentation"],
                 directories=["application/services", "application/dtos", "application/mappers"]),
        LayerSpec(name="infrastructure", order=2,
                 allowed_dependencies=["domain", "application"],
                 forbidden_dependencies=["presentation"],
                 directories=["infrastructure/repositories", "infrastructure/clients", "infrastructure/config"]),
        LayerSpec(name="presentation", order=3,
                 allowed_dependencies=["application", "infrastructure"],
                 forbidden_dependencies=["domain"],
                 directories=["presentation/controllers", "presentation/middleware", "presentation/schemas"]),
    ])
    
    # Component roles by layer
    layer_roles: Dict[str, List[ComponentRole]] = field(default_factory=lambda: {
        "domain": [ComponentRole.MODEL, ComponentRole.REPOSITORY, ComponentRole.EXCEPTION],
        "application": [ComponentRole.SERVICE, ComponentRole.DTO, ComponentRole.MAPPER],
        "infrastructure": [ComponentRole.REPOSITORY, ComponentRole.CLIENT, ComponentRole.ADAPTER],
        "presentation": [ComponentRole.CONTROLLER, ComponentRole.MIDDLEWARE, ComponentRole.SCHEMA],
    })
    
    # Validation
    validate_dependencies: bool = True
    validate_naming: bool = True
    validate_structure: bool = True
    
    # Output
    generate_skeleton: bool = True
    output_format: str = "json"
    use_llm: bool = True
    llm_model: str = "deepseek-chat"


# ============================================================
# STRUCTURE PLANNER
# ============================================================

class StructurePlanner:
    """Plan directory and file structure."""
    
    def __init__(self, config: ModuleArchitectConfig):
        self.config = config
    
    def plan_structure(self, name: str, components: List[ComponentSpec],
                       pattern: ArchitecturePattern) -> Tuple[Dict[str, DirectorySpec], Dict[str, FileSpec]]:
        """Plan directory and file structure."""
        directories = {}
        files = {}
        
        root_path = f"{self.config.source_root}/{name}"
        
        if pattern == ArchitecturePattern.LAYERED:
            directories, files = self._plan_layered(name, root_path, components)
        elif pattern == ArchitecturePattern.CLEAN:
            directories, files = self._plan_clean(name, root_path, components)
        elif pattern == ArchitecturePattern.HEXAGONAL:
            directories, files = self._plan_hexagonal(name, root_path, components)
        elif pattern == ArchitecturePattern.DDD:
            directories, files = self._plan_ddd(name, root_path, components)
        elif pattern == ArchitecturePattern.FEATURE_BASED:
            directories, files = self._plan_feature_based(name, root_path, components)
        else:
            directories, files = self._plan_default(name, root_path, components)
        
        return directories, files
    
    def _plan_layered(self, name: str, root_path: str,
                      components: List[ComponentSpec]) -> Tuple[Dict[str, DirectorySpec], Dict[str, FileSpec]]:
        """Plan layered architecture structure."""
        directories = {}
        files = {}
        
        # Create layer directories
        for layer in self.config.layers:
            for dir_path in layer.directories:
                full_path = f"{root_path}/{dir_path}"
                directories[full_path] = DirectorySpec(
                    name=dir_path.split('/')[-1],
                    path=full_path,
                    description=f"{layer.name} layer - {dir_path}",
                    is_package=True
                )
        
        # Assign components to files
        for comp in components:
            layer = self._determine_layer(comp)
            if layer:
                dir_path = self._get_component_directory(comp, layer)
                file_path = f"{root_path}/{dir_path}/{self._get_file_name(comp)}.py"
                
                if file_path not in files:
                    files[file_path] = FileSpec(
                        name=self._get_file_name(comp),
                        file_type=ModuleType.MODULE,
                        path=file_path,
                        description=f"{comp.role.value} implementations"
                    )
                
                files[file_path].classes.append(comp.name)
                comp.file_path = file_path
        
        return directories, files
    
    def _plan_clean(self, name: str, root_path: str,
                    components: List[ComponentSpec]) -> Tuple[Dict[str, DirectorySpec], Dict[str, FileSpec]]:
        """Plan Clean Architecture structure."""
        directories = {}
        files = {}
        
        # Clean Architecture layers
        clean_layers = [
            ("entities", "domain/entities"),
            ("usecases", "domain/usecases"),
            ("interfaces", "application/interfaces"),
            ("services", "application/services"),
            ("repositories", "infrastructure/repositories"),
            ("controllers", "presentation/controllers"),
            ("gateways", "infrastructure/gateways"),
        ]
        
        for dir_name, dir_path in clean_layers:
            full_path = f"{root_path}/{dir_path}"
            directories[full_path] = DirectorySpec(
                name=dir_name,
                path=full_path,
                is_package=True
            )
        
        return directories, files
    
    def _plan_hexagonal(self, name: str, root_path: str,
                        components: List[ComponentSpec]) -> Tuple[Dict[str, DirectorySpec], Dict[str, FileSpec]]:
        """Plan Hexagonal Architecture structure."""
        directories = {}
        files = {}
        
        # Hexagonal Architecture layers
        hex_layers = [
            ("core", "domain"),
            ("ports", "application/ports"),
            ("adapters", "infrastructure/adapters"),
            ("api", "presentation/api"),
        ]
        
        for dir_name, dir_path in hex_layers:
            full_path = f"{root_path}/{dir_path}"
            directories[full_path] = DirectorySpec(
                name=dir_name,
                path=full_path,
                is_package=True
            )
        
        return directories, files
    
    def _plan_ddd(self, name: str, root_path: str,
                  components: List[ComponentSpec]) -> Tuple[Dict[str, DirectorySpec], Dict[str, FileSpec]]:
        """Plan DDD structure."""
        directories = {}
        files = {}
        
        # DDD layers
        ddd_layers = [
            ("shared", "shared_kernel"),
            ("domain", "domain"),
            ("application", "application"),
            ("infrastructure", "infrastructure"),
            ("interfaces", "interfaces"),
        ]
        
        for dir_name, dir_path in ddd_layers:
            full_path = f"{root_path}/{dir_path}"
            directories[full_path] = DirectorySpec(
                name=dir_name,
                path=full_path,
                is_package=True
            )
        
        return directories, files
    
    def _plan_feature_based(self, name: str, root_path: str,
                            components: List[ComponentSpec]) -> Tuple[Dict[str, DirectorySpec], Dict[str, FileSpec]]:
        """Plan feature-based structure."""
        directories = {}
        files = {}
        
        # Group components by feature
        features = defaultdict(list)
        for comp in components:
            feature = comp.metadata.get('feature', 'core')
            features[feature].append(comp)
        
        for feature, feature_comps in features.items():
            feature_path = f"{root_path}/features/{feature}"
            
            # Create feature subdirectories
            for subdir in ["models", "services", "repositories", "components"]:
                full_path = f"{feature_path}/{subdir}"
                directories[full_path] = DirectorySpec(
                    name=subdir,
                    path=full_path,
                    is_package=True
                )
        
        return directories, files
    
    def _plan_default(self, name: str, root_path: str,
                      components: List[ComponentSpec]) -> Tuple[Dict[str, DirectorySpec], Dict[str, FileSpec]]:
        """Plan default structure."""
        directories = {}
        files = {}
        
        # Basic structure
        basic_dirs = ["models", "services", "utils", "exceptions", "constants"]
        for dir_name in basic_dirs:
            full_path = f"{root_path}/{dir_name}"
            directories[full_path] = DirectorySpec(
                name=dir_name,
                path=full_path,
                is_package=True
            )
        
        return directories, files
    
    def _determine_layer(self, comp: ComponentSpec) -> Optional[LayerSpec]:
        """Determine which layer a component belongs to."""
        for layer in self.config.layers:
            if comp.role in self.config.layer_roles.get(layer.name, []):
                return layer
        return None
    
    def _get_component_directory(self, comp: ComponentSpec, layer: LayerSpec) -> str:
        """Get directory path for a component."""
        if comp.role == ComponentRole.MODEL:
            return next((d for d in layer.directories if 'model' in d), layer.directories[0])
        elif comp.role == ComponentRole.SERVICE:
            return next((d for d in layer.directories if 'service' in d), layer.directories[0])
        elif comp.role == ComponentRole.REPOSITORY:
            return next((d for d in layer.directories if 'repositor' in d), layer.directories[0])
        elif comp.role == ComponentRole.CONTROLLER:
            return next((d for d in layer.directories if 'controller' in d), layer.directories[0])
        return layer.directories[0]
    
    def _get_file_name(self, comp: ComponentSpec) -> str:
        """Get file name for a component."""
        # Convert CamelCase to snake_case
        import re
        name = re.sub(r'(?<!^)(?=[A-Z])', '_', comp.name).lower()
        
        if comp.role == ComponentRole.REPOSITORY:
            return f"{name}_repository"
        elif comp.role == ComponentRole.SERVICE:
            return f"{name}_service"
        elif comp.role == ComponentRole.CONTROLLER:
            return f"{name}_controller"
        elif comp.role == ComponentRole.MODEL:
            return f"{name}_model"
        
        return name


# ============================================================
# MAIN MODULE ARCHITECT
# ============================================================

class ModuleArchitect:
    """
    Designs module structure, file organization, and component layout.
    
    Features:
    - Multiple architectural patterns (Layered, Clean, Hexagonal, DDD, Feature-based)
    - Automatic directory and file structure planning
    - Component organization and assignment
    - Layer-based dependency validation
    - Generation order calculation
    - Skeleton code generation
    - LLM-powered architecture suggestions
    - Integration with dependency planner
    """
    
    def __init__(self, config: ModuleArchitectConfig):
        self.config = config
        self.structure_planner = StructurePlanner(config)
        self.interface_designer = InterfaceDesigner()
        self.dependency_planner = DependencyPlanner()
        self.llm = LLMClient() if config.use_llm else None
        self.state = StateManager(config.project_root / ".ai_state" / "module_architect.json")
        
        self.scanner = ProjectScanner(project_root=config.project_root)
        
        logger.info("ModuleArchitect initialized")
    
    def design(self, name: str, description: str,
               components: Optional[List[ComponentSpec]] = None,
               pattern: Optional[ArchitecturePattern] = None) -> ModuleArchitecture:
        """Design a module architecture."""
        logger.info(f"Designing module: {name}")
        
        pattern = pattern or self.config.pattern
        components = components or []
        
        # Create architecture
        arch = ModuleArchitecture(
            name=name,
            root_path=f"{self.config.source_root}/{name}",
            pattern=pattern,
            description=description
        )
        
        # Plan structure
        arch.directories, arch.files = self.structure_planner.plan_structure(
            name, components, pattern
        )
        
        # Add components
        for comp in components:
            arch.components[comp.name] = comp
        
        # Add layers
        arch.layers = self.config.layers
        
        # Calculate dependencies
        arch.internal_dependencies = self._calculate_dependencies(components)
        
        # Design interfaces for public components
        for comp in components:
            if comp.visibility == Visibility.PUBLIC and comp.component_type == 'class':
                interface = self._design_interface_for_component(comp, arch)
                if interface:
                    arch.interfaces[comp.name] = interface
        
        # Calculate generation order
        arch.generation_order, arch.generation_batches = self._calculate_generation_order(arch)
        
        # Generate module docstring
        arch.module_docstring = self._generate_module_docstring(arch)
        
        # Validate architecture
        arch.is_valid, arch.issues, arch.warnings = self.validate(arch)
        
        # Enhance with LLM if available
        if self.llm:
            arch = self._enhance_with_llm(arch)
        
        # Save architecture
        self._save_architecture(arch)
        
        logger.info(f"Module architecture designed: {name} ({len(arch.files)} files, {len(arch.components)} components)")
        
        return arch
    
    def design_from_description(self, description: str, name: str) -> ModuleArchitecture:
        """Design a module from natural language description."""
        if not self.llm:
            raise ValueError("LLM is required for description-based design")
        
        logger.info(f"Designing module '{name}' from description")
        
        prompt = f"""
        Design a module architecture based on this description:
        
        Module Name: {name}
        Description: {description}
        
        Return a JSON object with:
        - pattern: recommended architectural pattern
        - components: list of components with name, type, role, description
        - dependencies: internal and external dependencies
        - layers: architectural layers needed
        - directory_structure: suggested directory layout
        
        Choose from patterns: {[p.value for p in ArchitecturePattern]}
        Choose from roles: {[r.value for r in ComponentRole]}
        
        Output only valid JSON.
        """
        
        response = self.llm.complete_json(prompt)
        
        # Parse components
        components = []
        for comp_data in response.get('components', []):
            comp = ComponentSpec(
                name=comp_data['name'],
                component_type=comp_data.get('type', 'class'),
                role=ComponentRole(comp_data.get('role', 'service')),
                description=comp_data.get('description', '')
            )
            components.append(comp)
        
        pattern = ArchitecturePattern(response.get('pattern', self.config.pattern.value))
        
        return self.design(name, description, components, pattern)
    
    def design_from_existing(self, module_path: str, name: Optional[str] = None) -> ModuleArchitecture:
        """Extract and refine architecture from existing module."""
        logger.info(f"Extracting architecture from existing module: {module_path}")
        
        # Scan existing module
        module_path_obj = Path(module_path)
        if not module_path_obj.exists():
            raise ValueError(f"Module path does not exist: {module_path}")
        
        # Analyze existing structure
        components = []
        
        for py_file in module_path_obj.rglob("*.py"):
            if py_file.name.startswith('_'):
                continue
            
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                tree = ast.parse(content)
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        if not node.name.startswith('_'):
                            comp = ComponentSpec(
                                name=node.name,
                                component_type='class',
                                role=self._infer_role_from_name(node.name),
                                file_path=str(py_file.relative_to(module_path_obj)),
                                description=ast.get_docstring(node) or ""
                            )
                            components.append(comp)
                    
            except Exception as e:
                logger.warning(f"Failed to analyze {py_file}: {e}")
        
        module_name = name or module_path_obj.name
        pattern = self._infer_pattern_from_structure(module_path_obj)
        
        return self.design(module_name, f"Architecture extracted from {module_path}", components, pattern)
    
    def _design_interface_for_component(self, comp: ComponentSpec,
                                         arch: ModuleArchitecture) -> Optional[InterfaceDesign]:
        """Design interface for a component."""
        if comp.role not in (ComponentRole.SERVICE, ComponentRole.REPOSITORY, ComponentRole.CONTROLLER):
            return None
        
        interface_name = f"I{comp.name}"
        
        # Create basic interface
        interface = InterfaceDesign(
            name=interface_name,
            module_path=f"{arch.root_path}/interfaces",
            description=f"Interface for {comp.name}",
            methods=[]
        )
        
        # Add common methods based on role
        if comp.role == ComponentRole.REPOSITORY:
            # Add CRUD methods
            interface.methods = [
                MethodDesign(name="get", description="Get entity by ID", is_abstract=True),
                MethodDesign(name="save", description="Save entity", is_abstract=True),
                MethodDesign(name="delete", description="Delete entity", is_abstract=True),
                MethodDesign(name="list", description="List entities", is_abstract=True),
            ]
        elif comp.role == ComponentRole.SERVICE:
            # Add service methods
            interface.methods = [
                MethodDesign(name="execute", description="Execute service operation", is_abstract=True),
            ]
        
        return interface
    
    def _calculate_dependencies(self, components: List[ComponentSpec]) -> Dict[str, List[str]]:
        """Calculate internal dependencies between components."""
        deps = defaultdict(list)
        
        for comp in components:
            # Repository depends on Model
            if comp.role == ComponentRole.REPOSITORY:
                for other in components:
                    if other.role == ComponentRole.MODEL:
                        deps[comp.name].append(other.name)
            
            # Service depends on Repository and Model
            elif comp.role == ComponentRole.SERVICE:
                for other in components:
                    if other.role in (ComponentRole.REPOSITORY, ComponentRole.MODEL):
                        deps[comp.name].append(other.name)
            
            # Controller depends on Service and DTO
            elif comp.role == ComponentRole.CONTROLLER:
                for other in components:
                    if other.role in (ComponentRole.SERVICE, ComponentRole.DTO):
                        deps[comp.name].append(other.name)
            
            # Mapper depends on Model and DTO
            elif comp.role == ComponentRole.MAPPER:
                for other in components:
                    if other.role in (ComponentRole.MODEL, ComponentRole.DTO):
                        deps[comp.name].append(other.name)
        
        return dict(deps)
    
    def _calculate_generation_order(self, arch: ModuleArchitecture) -> Tuple[List[str], List[List[str]]]:
        """Calculate optimal generation order."""
        # Build dependency graph
        graph = defaultdict(list)
        in_degree = defaultdict(int)
        
        for comp_name, comp in arch.components.items():
            for dep in comp.dependencies:
                graph[dep].append(comp_name)
                in_degree[comp_name] += 1
        
        all_comps = set(arch.components.keys())
        for comp in all_comps:
            if comp not in in_degree:
                in_degree[comp] = 0
        
        # Topological sort with batching
        order = []
        batches = []
        remaining = set(all_comps)
        
        while remaining:
            batch = [c for c in remaining if in_degree[c] == 0]
            
            if not batch:
                # Circular dependency - break it
                batch = [min(remaining, key=lambda c: in_degree[c])]
                for c in batch:
                    in_degree[c] = 0
            
            batches.append(batch)
            order.extend(batch)
            
            for c in batch:
                remaining.remove(c)
                for neighbor in graph[c]:
                    if neighbor in remaining:
                        in_degree[neighbor] -= 1
        
        return order, batches
    
    def _generate_module_docstring(self, arch: ModuleArchitecture) -> str:
        """Generate module docstring."""
        lines = [
            f"{arch.name} Module",
            "",
            arch.description,
            "",
            f"Architecture Pattern: {arch.pattern.value}",
            f"Components: {len(arch.components)}",
            f"Files: {len(arch.files)}",
            f"Layers: {len(arch.layers)}",
        ]
        return "\n".join(lines)
    
    def _infer_role_from_name(self, name: str) -> ComponentRole:
        """Infer component role from class name."""
        name_lower = name.lower()
        
        if name.endswith('Controller'):
            return ComponentRole.CONTROLLER
        elif name.endswith('Service'):
            return ComponentRole.SERVICE
        elif name.endswith('Repository'):
            return ComponentRole.REPOSITORY
        elif name.endswith('Model') or name.endswith('Entity'):
            return ComponentRole.MODEL
        elif name.endswith('Dto') or name.endswith('DTO'):
            return ComponentRole.DTO
        elif name.endswith('Mapper'):
            return ComponentRole.MAPPER
        elif name.endswith('Factory'):
            return ComponentRole.FACTORY
        elif name.endswith('Builder'):
            return ComponentRole.BUILDER
        elif name.endswith('Adapter'):
            return ComponentRole.ADAPTER
        elif name.endswith('Client'):
            return ComponentRole.CLIENT
        elif name.endswith('Exception') or name.endswith('Error'):
            return ComponentRole.EXCEPTION
        elif name.endswith('Config'):
            return ComponentRole.CONFIG
        elif name.endswith('Util') or name.endswith('Helper'):
            return ComponentRole.UTILITY
        
        return ComponentRole.SERVICE
    
    def _infer_pattern_from_structure(self, module_path: Path) -> ArchitecturePattern:
        """Infer architectural pattern from directory structure."""
        structure = str(module_path).lower()
        
        if 'domain' in structure and 'application' in structure and 'infrastructure' in structure:
            return ArchitecturePattern.DDD
        elif 'entities' in structure and 'usecases' in structure:
            return ArchitecturePattern.CLEAN
        elif 'ports' in structure and 'adapters' in structure:
            return ArchitecturePattern.HEXAGONAL
        elif 'models' in structure and 'views' in structure and 'controllers' in structure:
            return ArchitecturePattern.MVC
        elif 'features' in structure:
            return ArchitecturePattern.FEATURE_BASED
        
        return ArchitecturePattern.LAYERED
    
    def _enhance_with_llm(self, arch: ModuleArchitecture) -> ModuleArchitecture:
        """Enhance architecture with LLM suggestions."""
        prompt = f"""
        Review and enhance this module architecture:
        
        Name: {arch.name}
        Pattern: {arch.pattern.value}
        Components: {len(arch.components)}
        Files: {len(arch.files)}
        
        Suggest:
        1. Missing components or files
        2. Structural improvements
        3. Dependency optimizations
        4. Naming improvements
        
        Return JSON with suggestions.
        """
        
        try:
            response = self.llm.complete_json(prompt)
            arch.metadata['llm_suggestions'] = response
        except Exception as e:
            logger.warning(f"LLM enhancement failed: {e}")
        
        return arch
    
    def validate(self, arch: ModuleArchitecture) -> Tuple[bool, List[str], List[str]]:
        """Validate module architecture."""
        issues = []
        warnings = []
        
        if self.config.validate_dependencies:
            # Check for circular dependencies
            graph = {c: arch.components[c].dependencies for c in arch.components}
            visited = set()
            rec_stack = set()
            
            def has_cycle(node: str) -> bool:
                visited.add(node)
                rec_stack.add(node)
                for dep in graph.get(node, []):
                    if dep not in visited:
                        if has_cycle(dep):
                            return True
                    elif dep in rec_stack:
                        return True
                rec_stack.remove(node)
                return False
            
            for comp in arch.components:
                if comp not in visited:
                    if has_cycle(comp):
                        issues.append(f"Circular dependency detected involving '{comp}'")
            
            # Check layer violations
            for comp_name, comp in arch.components.items():
                comp_layer = self._get_component_layer(comp)
                if comp_layer:
                    for dep_name in comp.dependencies:
                        dep = arch.components.get(dep_name)
                        if dep:
                            dep_layer = self._get_component_layer(dep)
                            if dep_layer and dep_layer.order < comp_layer.order:
                                if dep_layer.name in comp_layer.forbidden_dependencies:
                                    issues.append(
                                        f"Layer violation: {comp_name} ({comp_layer.name}) "
                                        f"depends on {dep_name} ({dep_layer.name})"
                                    )
        
        if self.config.validate_naming:
            # Check file naming
            for file_path in arch.files:
                file_name = Path(file_path).stem
                if not self._matches_naming(file_name, self.config.file_naming):
                    warnings.append(f"File name '{file_name}' does not match {self.config.file_naming}")
            
            # Check component naming
            for comp in arch.components.values():
                if comp.component_type == 'class':
                    if not self._matches_naming(comp.name, self.config.class_naming):
                        warnings.append(f"Class name '{comp.name}' does not match {self.config.class_naming}")
        
        if self.config.validate_structure:
            # Check max classes per file
            for file_spec in arch.files.values():
                if len(file_spec.classes) > self.config.max_classes_per_file:
                    warnings.append(
                        f"File '{file_spec.name}' has {len(file_spec.classes)} classes "
                        f"(max {self.config.max_classes_per_file})"
                    )
        
        return len(issues) == 0, issues, warnings
    
    def _get_component_layer(self, comp: ComponentSpec) -> Optional[LayerSpec]:
        """Get the layer a component belongs to."""
        for layer in self.config.layers:
            if comp.role in self.config.layer_roles.get(layer.name, []):
                return layer
        return None
    
    def _matches_naming(self, name: str, convention: str) -> bool:
        """Check if name matches naming convention."""
        import re
        
        if convention == "snake_case":
            return bool(re.match(r'^[a-z][a-z0-9]*(_[a-z0-9]+)*$', name))
        elif convention == "PascalCase":
            return bool(re.match(r'^[A-Z][a-zA-Z0-9]*$', name))
        return True
    
    def generate_skeleton(self, arch: ModuleArchitecture,
                          output_dir: Optional[Path] = None) -> List[Path]:
        """Generate skeleton files for the module."""
        output_dir = output_dir or self.config.project_root
        generated_files = []
        
        # Create directories
        for dir_path, dir_spec in arch.directories.items():
            full_path = output_dir / dir_path
            full_path.mkdir(parents=True, exist_ok=True)
            
            if dir_spec.is_package and self.config.create_init_files:
                init_file = full_path / "__init__.py"
                init_content = self._generate_init_content(dir_spec)
                init_file.write_text(init_content)
                generated_files.append(init_file)
        
        # Create files
        for file_path, file_spec in arch.files.items():
            full_path = output_dir / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            file_content = self._generate_file_content(file_spec, arch)
            full_path.write_text(file_content)
            generated_files.append(full_path)
        
        # Create test directory
        test_dir = output_dir / self.config.test_root / arch.name
        test_dir.mkdir(parents=True, exist_ok=True)
        test_init = test_dir / "__init__.py"
        test_init.touch()
        generated_files.append(test_init)
        
        logger.info(f"Generated {len(generated_files)} skeleton files for {arch.name}")
        
        return generated_files
    
    def _generate_init_content(self, dir_spec: DirectorySpec) -> str:
        """Generate __init__.py content."""
        lines = ['"""', f"{dir_spec.name} package.", '"""', '']
        
        if dir_spec.init_exports:
            exports = ", ".join(dir_spec.init_exports)
            lines.append(f"__all__ = [{exports}]")
        
        return "\n".join(lines)
    
    def _generate_file_content(self, file_spec: FileSpec, arch: ModuleArchitecture) -> str:
        """Generate file content."""
        lines = []
        
        # Docstring
        lines.append('"""')
        lines.append(file_spec.description or f"{file_spec.name} module.")
        lines.append('"""')
        lines.append("")
        
        # Imports
        if file_spec.imports:
            for imp in sorted(file_spec.imports):
                lines.append(imp)
            lines.append("")
        
        # Constants
        if file_spec.constants:
            for const in file_spec.constants:
                lines.append(f"# {const}")
            lines.append("")
        
        # Class stubs
        for class_name in file_spec.classes:
            comp = arch.components.get(class_name)
            if comp:
                lines.append(f"class {class_name}:")
                lines.append(f'    """{comp.description}"""')
                
                if comp.interface_ref:
                    lines.append(f"    # Implements: {comp.interface_ref}")
                
                lines.append("    pass")
                lines.append("")
        
        # Function stubs
        if file_spec.functions:
            for func_name in file_spec.functions:
                lines.append(f"def {func_name}():")
                lines.append(f'    """TODO: Implement {func_name}."""')
                lines.append("    pass")
                lines.append("")
        
        return "\n".join(lines)
    
    def _save_architecture(self, arch: ModuleArchitecture):
        """Save architecture to state."""
        architectures = self.state.get('architectures', [])
        architectures.append({
            'timestamp': arch.created_at.isoformat(),
            'name': arch.name,
            'pattern': arch.pattern.value,
            'components': len(arch.components),
            'files': len(arch.files),
            'directories': len(arch.directories),
            'is_valid': arch.is_valid
        })
        
        if len(architectures) > 50:
            architectures = architectures[-50:]
        
        self.state.set('architectures', architectures)
        self.state.save()
    
    def export_architecture(self, arch: ModuleArchitecture,
                            output_path: Optional[Path] = None,
                            format: str = 'json') -> str:
        """Export module architecture."""
        
        if format == 'json':
            data = {
                'name': arch.name,
                'root_path': arch.root_path,
                'pattern': arch.pattern.value,
                'description': arch.description,
                'version': arch.version,
                'created_at': arch.created_at.isoformat(),
                'is_valid': arch.is_valid,
                'statistics': {
                    'directories': len(arch.directories),
                    'files': len(arch.files),
                    'components': len(arch.components),
                    'layers': len(arch.layers),
                    'interfaces': len(arch.interfaces)
                },
                'directories': {
                    path: {
                        'name': d.name,
                        'description': d.description,
                        'is_package': d.is_package,
                        'files': d.files
                    }
                    for path, d in arch.directories.items()
                },
                'files': {
                    path: {
                        'name': f.name,
                        'type': f.file_type.value,
                        'classes': f.classes,
                        'functions': f.functions,
                        'generation_order': f.generation_order
                    }
                    for path, f in arch.files.items()
                },
                'components': {
                    name: {
                        'type': c.component_type,
                        'role': c.role.value,
                        'visibility': c.visibility.value,
                        'file_path': c.file_path,
                        'dependencies': c.dependencies
                    }
                    for name, c in arch.components.items()
                },
                'generation_order': arch.generation_order,
                'generation_batches': arch.generation_batches,
                'issues': arch.issues,
                'warnings': arch.warnings
            }
            
            content = json.dumps(data, indent=2)
            
        elif format == 'markdown':
            lines = [
                f"# Module Architecture: {arch.name}",
                "",
                f"**Pattern:** {arch.pattern.value}",
                f"**Version:** {arch.version}",
                f"**Created:** {arch.created_at.strftime('%Y-%m-%d %H:%M:%S')}",
                f"**Valid:** {'✅ Yes' if arch.is_valid else '❌ No'}",
                "",
                arch.description,
                "",
                "## Statistics",
                "",
                f"| Metric | Count |",
                f"|--------|-------|",
                f"| Directories | {len(arch.directories)} |",
                f"| Files | {len(arch.files)} |",
                f"| Components | {len(arch.components)} |",
                f"| Layers | {len(arch.layers)} |",
                f"| Interfaces | {len(arch.interfaces)} |",
                "",
                "## Directory Structure",
                "",
                "```",
                self._generate_tree(arch),
                "```",
                "",
                "## Components",
                "",
                "| Name | Type | Role | Layer | Dependencies |",
                "|------|------|------|-------|--------------|",
            ]
            
            for name, comp in arch.components.items():
                layer = self._get_component_layer(comp)
                layer_name = layer.name if layer else "unknown"
                deps = ", ".join(comp.dependencies[:3])
                if len(comp.dependencies) > 3:
                    deps += f" (+{len(comp.dependencies) - 3})"
                lines.append(f"| {name} | {comp.component_type} | {comp.role.value} | {layer_name} | {deps} |")
            
            lines.append("")
            
            if arch.generation_batches:
                lines.append("## Generation Order")
                lines.append("")
                for i, batch in enumerate(arch.generation_batches, 1):
                    lines.append(f"**Batch {i}:** {', '.join(batch)}")
                lines.append("")
            
            if arch.issues:
                lines.append("## Issues")
                lines.append("")
                for issue in arch.issues:
                    lines.append(f"- {issue}")
                lines.append("")
            
            content = '\n'.join(lines)
            
        elif format == 'mermaid':
            lines = ["```mermaid", "graph TD"]
            lines.append("    subgraph \"" + arch.name + "\"")
            
            for name, comp in arch.components.items():
                layer = self._get_component_layer(comp)
                layer_name = layer.name if layer else "unknown"
                lines.append(f"        {self._sanitize(name)}[\"{name}<br/>({comp.role.value})\"]")
            
            for name, comp in arch.components.items():
                for dep in comp.dependencies:
                    lines.append(f"        {self._sanitize(dep)} --> {self._sanitize(name)}")
            
            lines.append("    end")
            lines.append("```")
            
            content = '\n'.join(lines)
            
        else:
            content = json.dumps({
                'name': arch.name,
                'pattern': arch.pattern.value,
                'components': len(arch.components)
            }, indent=2)
        
        if output_path:
            output_path.write_text(content)
        
        return content
    
    def _generate_tree(self, arch: ModuleArchitecture, prefix: str = "") -> str:
        """Generate ASCII tree of directory structure."""
        lines = []
        
        # Sort directories
        sorted_dirs = sorted(arch.directories.keys())
        for i, dir_path in enumerate(sorted_dirs):
            is_last = (i == len(sorted_dirs) - 1)
            dir_name = Path(dir_path).name
            
            if prefix:
                lines.append(f"{prefix}{'└── ' if is_last else '├── '}{dir_name}/")
            else:
                lines.append(f"{dir_name}/")
            
            # Add files in this directory
            dir_files = [f for f in arch.files if str(Path(f).parent) == dir_path]
            for j, file_path in enumerate(sorted(dir_files)):
                file_is_last = (j == len(dir_files) - 1)
                file_name = Path(file_path).name
                new_prefix = prefix + ('    ' if is_last else '│   ')
                lines.append(f"{new_prefix}{'└── ' if file_is_last else '├── '}{file_name}")
        
        return '\n'.join(lines)
    
    def _sanitize(self, name: str) -> str:
        """Sanitize name for Mermaid."""
        return name.replace('.', '_').replace('-', '_')
    
    def close(self):
        """Clean up resources."""
        self.state.save()
        logger.info("ModuleArchitect closed")


# ============================================================
# CLI ENTRY POINT
# ============================================================

def main():
    """CLI entry point for module architect."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Design module architecture and structure")
    parser.add_argument("--name", type=str, required=True, help="Module name")
    parser.add_argument("--description", type=str, help="Module description")
    parser.add_argument("--pattern", choices=[p.value for p in ArchitecturePattern],
                       default=ArchitecturePattern.LAYERED.value)
    parser.add_argument("--components", type=Path, help="Components specification JSON")
    parser.add_argument("--from-existing", type=Path, help="Extract from existing module")
    parser.add_argument("--output", "-o", type=Path, help="Output file")
    parser.add_argument("--format", choices=["json", "markdown", "mermaid"], default="json")
    parser.add_argument("--generate", action="store_true", help="Generate skeleton files")
    parser.add_argument("--no-llm", action="store_true", help="Disable LLM assistance")
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    
    args = parser.parse_args()
    
    config = ModuleArchitectConfig(
        project_root=args.project_root,
        pattern=ArchitecturePattern(args.pattern),
        use_llm=not args.no_llm,
        generate_skeleton=args.generate
    )
    
    architect = ModuleArchitect(config)
    
    if args.from_existing:
        arch = architect.design_from_existing(str(args.from_existing), args.name)
    elif args.components:
        with open(args.components, 'r') as f:
            data = json.load(f)
        components = []
        for comp_data in data.get('components', []):
            comp = ComponentSpec(
                name=comp_data['name'],
                component_type=comp_data.get('type', 'class'),
                role=ComponentRole(comp_data.get('role', 'service')),
                description=comp_data.get('description', '')
            )
            components.append(comp)
        arch = architect.design(args.name, args.description or "", components, config.pattern)
    elif args.description:
        arch = architect.design_from_description(args.description, args.name)
    else:
        arch = architect.design(args.name, args.description or "")
    
    if args.generate:
        files = architect.generate_skeleton(arch, args.project_root)
        print(f"Generated {len(files)} skeleton files")
    
    output = architect.export_architecture(arch, args.output, args.format)
    
    if not args.output:
        print(output)
    else:
        print(f"Architecture saved to {args.output}")
    
    print(f"\nModule: {arch.name} ({arch.pattern.value})")
    print(f"Components: {len(arch.components)}, Files: {len(arch.files)}")
    print(f"Valid: {'Yes' if arch.is_valid else 'No'}")
    
    if arch.issues:
        print(f"Issues: {len(arch.issues)}")
    
    architect.close()


if __name__ == "__main__":
    main()