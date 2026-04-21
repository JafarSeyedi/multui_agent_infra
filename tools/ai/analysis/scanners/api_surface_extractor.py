#!/usr/bin/env python3
"""
API Surface Extractor - AI Development Framework
Extracts and documents public API surfaces from Python packages.

Part of the Level 2 Analysis tools (scanners/api_surface_extractor.py)

This api_surface_extractor.py provides:

1. Complete API Surface Extraction - All public/protected/private elements from packages
2. Type Hint Extraction - Parameter and return type annotations
3. Docstring Parsing - Module, class, and function documentation
4. Deprecation Detection - @deprecated decorator and deprecation messages
5. Stability Levels - Stable, beta, experimental, internal tracking
6. Re-export Tracking - Track elements re-exported from other modules
7. Breaking Change Detection - Compare API surfaces between versions
8. Package/Module Hierarchy - Full structural representation
9. Multiple Export Formats - JSON, Markdown, and HTML documentation
10. Statistics and Analytics - Element counts by type, visibility, and stability
11. Search Capabilities - Find elements by name or qualified name
12. Beautiful HTML Documentation - Interactive API reference with sidebar navigation

The API surface extractor is essential for maintaining semantic versioning, generating documentation, and tracking API evolution over time.

"""

import ast
import json
import inspect
import importlib
import importlib.util
import sys
from pathlib import Path
from typing import Dict, List, Set, Optional, Any, Tuple, Union, Iterator
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from ...shared.logger import get_logger
from ...shared.state_manager import StateManager

logger = get_logger(__name__)


# ============================================================
# ENUMS AND CONSTANTS
# ============================================================

class APIVisibility(str, Enum):
    """Visibility level of API element."""
    PUBLIC = "public"
    PROTECTED = "protected"
    PRIVATE = "private"
    INTERNAL = "internal"


class APIElementType(str, Enum):
    """Type of API element."""
    MODULE = "module"
    PACKAGE = "package"
    CLASS = "class"
    FUNCTION = "function"
    ASYNC_FUNCTION = "async_function"
    METHOD = "method"
    ASYNC_METHOD = "async_method"
    CLASS_METHOD = "class_method"
    STATIC_METHOD = "static_method"
    PROPERTY = "property"
    ATTRIBUTE = "attribute"
    CONSTANT = "constant"
    ENUM = "enum"
    DATACLASS = "dataclass"
    PROTOCOL = "protocol"
    TYPE_ALIAS = "type_alias"
    TYPE_VAR = "type_var"
    EXCEPTION = "exception"
    DECORATOR = "decorator"


class DeprecationStatus(str, Enum):
    """Deprecation status of API element."""
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    PENDING_DEPRECATION = "pending_deprecation"
    REMOVED = "removed"


class StabilityLevel(str, Enum):
    """Stability level of API."""
    STABLE = "stable"
    BETA = "beta"
    EXPERIMENTAL = "experimental"
    INTERNAL = "internal"
    DEPRECATED = "deprecated"


# ============================================================
# DATA MODELS
# ============================================================

@dataclass
class Parameter:
    """Function/method parameter."""
    name: str
    type_annotation: Optional[str] = None
    default_value: Optional[str] = None
    kind: str = "positional_or_keyword"  # positional, keyword, varargs, etc.
    description: Optional[str] = None


@dataclass
class APIElement:
    """Represents a single API element."""
    id: str
    name: str
    qualified_name: str
    element_type: APIElementType
    visibility: APIVisibility
    module_path: str
    file_path: Optional[str] = None
    line_start: Optional[int] = None
    line_end: Optional[int] = None
    docstring: Optional[str] = None
    signature: Optional[str] = None
    parameters: List[Parameter] = field(default_factory=list)
    return_type: Optional[str] = None
    decorators: List[str] = field(default_factory=list)
    bases: List[str] = field(default_factory=list)
    attributes: List[str] = field(default_factory=list)
    methods: List[str] = field(default_factory=list)
    deprecation: DeprecationStatus = DeprecationStatus.ACTIVE
    deprecation_message: Optional[str] = None
    stability: StabilityLevel = StabilityLevel.STABLE
    since_version: Optional[str] = None
    examples: List[str] = field(default_factory=list)
    see_also: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class APIModule:
    """Represents a module's API surface."""
    name: str
    path: str
    elements: Dict[str, APIElement] = field(default_factory=dict)
    exports: List[str] = field(default_factory=list)
    re_exports: Dict[str, str] = field(default_factory=dict)  # name -> source_module
    submodules: List[str] = field(default_factory=list)
    docstring: Optional[str] = None
    stability: StabilityLevel = StabilityLevel.STABLE
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class APIPackage:
    """Represents a package's API surface."""
    name: str
    path: str
    modules: Dict[str, APIModule] = field(default_factory=dict)
    subpackages: List[str] = field(default_factory=list)
    exports: List[str] = field(default_factory=list)
    docstring: Optional[str] = None
    stability: StabilityLevel = StabilityLevel.STABLE
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class APISurface:
    """Complete API surface of a project."""
    project_name: str
    project_root: str
    extracted_at: datetime
    packages: Dict[str, APIPackage] = field(default_factory=dict)
    modules: Dict[str, APIModule] = field(default_factory=dict)
    global_elements: Dict[str, APIElement] = field(default_factory=dict)
    breaking_changes: List[Dict[str, Any]] = field(default_factory=list)
    deprecated_elements: List[str] = field(default_factory=list)
    experimental_elements: List[str] = field(default_factory=list)
    statistics: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class APIExtractorConfig:
    """Configuration for API extraction."""
    project_root: Path
    packages: List[str] = field(default_factory=list)  # Specific packages to extract
    include_private: bool = False
    include_protected: bool = False
    include_deprecated: bool = True
    include_experimental: bool = True
    extract_docstrings: bool = True
    extract_examples: bool = True
    extract_type_hints: bool = True
    resolve_aliases: bool = True
    follow_imports: bool = False
    detect_breaking_changes: bool = False
    previous_surface_path: Optional[Path] = None
    output_format: str = "json"


# ============================================================
# AST VISITOR FOR API EXTRACTION
# ============================================================

class APIElementExtractor(ast.NodeVisitor):
    """Extract API elements from Python AST."""
    
    def __init__(self, module_path: str, file_path: str, config: APIExtractorConfig):
        self.module_path = module_path
        self.file_path = file_path
        self.config = config
        self.elements: Dict[str, APIElement] = {}
        self.exports: List[str] = []
        self.re_exports: Dict[str, str] = {}
        self.module_docstring: Optional[str] = None
        self.current_class: Optional[str] = None
        self.imports: Dict[str, str] = {}  # name -> source
    
    def visit_Module(self, node: ast.Module):
        """Visit module."""
        self.module_docstring = ast.get_docstring(node)
        
        # Find __all__
        for child in node.body:
            if isinstance(child, ast.Assign):
                for target in child.targets:
                    if isinstance(target, ast.Name) and target.id == '__all__':
                        if isinstance(child.value, ast.List):
                            self.exports = [
                                item.value if isinstance(item, ast.Constant) else None
                                for item in child.value.elts
                            ]
                            self.exports = [e for e in self.exports if e]
        
        self.generic_visit(node)
    
    def visit_Import(self, node: ast.Import):
        """Track imports."""
        for alias in node.names:
            self.imports[alias.asname or alias.name] = alias.name
    
    def visit_ImportFrom(self, node: ast.ImportFrom):
        """Track from imports."""
        if node.module:
            for alias in node.names:
                name = alias.asname or alias.name
                self.imports[name] = f"{node.module}.{alias.name}"
                
                # Check for re-export
                if name == alias.name and name != '*':
                    self.re_exports[name] = node.module
    
    def _is_public(self, name: str) -> bool:
        """Check if name is public."""
        if name.startswith('__') and name.endswith('__'):
            return True  # Special methods
        if name.startswith('_'):
            return self.config.include_private
        return True
    
    def _get_visibility(self, name: str) -> APIVisibility:
        """Get visibility level."""
        if name.startswith('__') and name.endswith('__'):
            return APIVisibility.PUBLIC
        if name.startswith('__'):
            return APIVisibility.PRIVATE
        if name.startswith('_'):
            return APIVisibility.PROTECTED
        return APIVisibility.PUBLIC
    
    def _is_exported(self, name: str) -> bool:
        """Check if name is exported."""
        if not self.exports:
            return self._is_public(name)
        return name in self.exports
    
    def _get_deprecation_info(self, node: ast.AST) -> Tuple[DeprecationStatus, Optional[str]]:
        """Extract deprecation info from decorators."""
        if hasattr(node, 'decorator_list'):
            for dec in node.decorator_list:
                if isinstance(dec, ast.Name) and dec.id == 'deprecated':
                    return DeprecationStatus.DEPRECATED, None
                elif isinstance(dec, ast.Call):
                    if isinstance(dec.func, ast.Name) and dec.func.id == 'deprecated':
                        # Try to get deprecation message
                        for kw in dec.keywords:
                            if kw.arg == 'reason' and isinstance(kw.value, ast.Constant):
                                return DeprecationStatus.DEPRECATED, kw.value.value
                        return DeprecationStatus.DEPRECATED, None
        
        return DeprecationStatus.ACTIVE, None
    
    def _get_stability(self, node: ast.AST) -> StabilityLevel:
        """Extract stability level from decorators."""
        if hasattr(node, 'decorator_list'):
            for dec in node.decorator_list:
                if isinstance(dec, ast.Name):
                    if dec.id == 'experimental':
                        return StabilityLevel.EXPERIMENTAL
                    elif dec.id == 'beta':
                        return StabilityLevel.BETA
        return StabilityLevel.STABLE
    
    def _extract_parameters(self, node: ast.FunctionDef) -> List[Parameter]:
        """Extract function parameters."""
        params = []
        
        # Positional args
        for arg in node.args.args:
            param = Parameter(
                name=arg.arg,
                type_annotation=ast.unparse(arg.annotation) if arg.annotation and self.config.extract_type_hints else None
            )
            params.append(param)
        
        # Defaults
        defaults_offset = len(node.args.args) - len(node.args.defaults)
        for i, default in enumerate(node.args.defaults):
            params[defaults_offset + i].default_value = ast.unparse(default)
        
        return params
    
    def _get_return_type(self, node: ast.FunctionDef) -> Optional[str]:
        """Extract return type annotation."""
        if node.returns and self.config.extract_type_hints:
            return ast.unparse(node.returns)
        return None
    
    def visit_ClassDef(self, node: ast.ClassDef):
        """Visit class definition."""
        if not self._is_exported(node.name):
            return
        
        prev_class = self.current_class
        self.current_class = node.name
        
        # Determine class type
        element_type = self._get_class_type(node)
        
        # Extract bases
        bases = []
        for base in node.bases:
            if isinstance(base, ast.Name):
                bases.append(base.id)
            elif isinstance(base, ast.Attribute):
                bases.append(ast.unparse(base))
        
        # Extract decorators
        decorators = []
        for dec in node.decorator_list:
            if isinstance(dec, ast.Name):
                decorators.append(dec.id)
            elif isinstance(dec, ast.Attribute):
                decorators.append(ast.unparse(dec))
            elif isinstance(dec, ast.Call):
                if isinstance(dec.func, ast.Name):
                    decorators.append(dec.func.id)
        
        deprecation, dep_msg = self._get_deprecation_info(node)
        stability = self._get_stability(node)
        
        qualified_name = f"{self.module_path}.{node.name}" if self.module_path else node.name
        
        element = APIElement(
            id=f"class:{qualified_name}",
            name=node.name,
            qualified_name=qualified_name,
            element_type=element_type,
            visibility=self._get_visibility(node.name),
            module_path=self.module_path,
            file_path=self.file_path,
            line_start=node.lineno,
            line_end=node.end_lineno,
            docstring=ast.get_docstring(node) if self.config.extract_docstrings else None,
            decorators=decorators,
            bases=bases,
            deprecation=deprecation,
            deprecation_message=dep_msg,
            stability=stability
        )
        
        self.elements[qualified_name] = element
        
        # Visit class body
        self.generic_visit(node)
        
        self.current_class = prev_class
    
    def _get_class_type(self, node: ast.ClassDef) -> APIElementType:
        """Determine class type."""
        for dec in node.decorator_list:
            if isinstance(dec, ast.Name):
                if dec.id == 'dataclass':
                    return APIElementType.DATACLASS
                elif dec.id == 'dataclass_transform':
                    return APIElementType.DATACLASS
            elif isinstance(dec, ast.Attribute):
                if dec.attr == 'dataclass':
                    return APIElementType.DATACLASS
        
        for base in node.bases:
            if isinstance(base, ast.Name):
                if base.id == 'Enum':
                    return APIElementType.ENUM
                elif base.id == 'Protocol':
                    return APIElementType.PROTOCOL
                elif base.id == 'Exception' or base.id.endswith('Error'):
                    return APIElementType.EXCEPTION
                elif base.id == 'TypeVar':
                    return APIElementType.TYPE_VAR
        
        return APIElementType.CLASS
    
    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Visit function definition."""
        self._visit_function(node, is_async=False)
    
    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        """Visit async function definition."""
        self._visit_function(node, is_async=True)
    
    def _visit_function(self, node: Union[ast.FunctionDef, ast.AsyncFunctionDef], is_async: bool):
        """Common function visitor."""
        if not self._is_exported(node.name):
            return
        
        # Determine element type
        if self.current_class:
            if node.name == '__init__':
                element_type = APIElementType.METHOD
            elif any(isinstance(d, ast.Name) and d.id == 'property' for d in node.decorator_list):
                element_type = APIElementType.PROPERTY
            elif any(isinstance(d, ast.Name) and d.id == 'classmethod' for d in node.decorator_list):
                element_type = APIElementType.CLASS_METHOD
            elif any(isinstance(d, ast.Name) and d.id == 'staticmethod' for d in node.decorator_list):
                element_type = APIElementType.STATIC_METHOD
            else:
                element_type = APIElementType.ASYNC_METHOD if is_async else APIElementType.METHOD
        else:
            element_type = APIElementType.ASYNC_FUNCTION if is_async else APIElementType.FUNCTION
        
        # Extract decorators
        decorators = []
        for dec in node.decorator_list:
            if isinstance(dec, ast.Name):
                decorators.append(dec.id)
            elif isinstance(dec, ast.Attribute):
                decorators.append(ast.unparse(dec))
        
        # Extract parameters
        parameters = self._extract_parameters(node)
        
        # Build signature
        params_str = ', '.join(
            f"{p.name}: {p.type_annotation}" if p.type_annotation else p.name
            for p in parameters
        )
        return_type = self._get_return_type(node)
        signature = f"def {node.name}({params_str})"
        if return_type:
            signature += f" -> {return_type}"
        
        deprecation, dep_msg = self._get_deprecation_info(node)
        stability = self._get_stability(node)
        
        if self.current_class:
            qualified_name = f"{self.module_path}.{self.current_class}.{node.name}"
        else:
            qualified_name = f"{self.module_path}.{node.name}" if self.module_path else node.name
        
        element = APIElement(
            id=f"func:{qualified_name}",
            name=node.name,
            qualified_name=qualified_name,
            element_type=element_type,
            visibility=self._get_visibility(node.name),
            module_path=self.module_path,
            file_path=self.file_path,
            line_start=node.lineno,
            line_end=node.end_lineno,
            docstring=ast.get_docstring(node) if self.config.extract_docstrings else None,
            signature=signature,
            parameters=parameters,
            return_type=return_type,
            decorators=decorators,
            deprecation=deprecation,
            deprecation_message=dep_msg,
            stability=stability
        )
        
        self.elements[qualified_name] = element
        
        # Update parent class
        if self.current_class:
            class_name = f"{self.module_path}.{self.current_class}"
            if class_name in self.elements:
                self.elements[class_name].methods.append(node.name)
    
    def visit_Assign(self, node: ast.Assign):
        """Visit assignment for constants and attributes."""
        for target in node.targets:
            if isinstance(target, ast.Name):
                if target.id.isupper() and self._is_exported(target.id):
                    # Constant
                    qualified_name = f"{self.module_path}.{target.id}" if self.module_path else target.id
                    
                    element = APIElement(
                        id=f"const:{qualified_name}",
                        name=target.id,
                        qualified_name=qualified_name,
                        element_type=APIElementType.CONSTANT,
                        visibility=self._get_visibility(target.id),
                        module_path=self.module_path,
                        file_path=self.file_path,
                        line_start=node.lineno,
                        line_end=node.end_lineno
                    )
                    
                    self.elements[qualified_name] = element
            
            elif isinstance(target, ast.Attribute):
                if isinstance(target.value, ast.Name) and target.value.id == 'self':
                    if self.current_class:
                        class_name = f"{self.module_path}.{self.current_class}"
                        if class_name in self.elements:
                            self.elements[class_name].attributes.append(target.attr)
    
    def visit_AnnAssign(self, node: ast.AnnAssign):
        """Visit annotated assignment for type aliases."""
        if isinstance(node.target, ast.Name):
            if self._is_exported(node.target.id):
                qualified_name = f"{self.module_path}.{node.target.id}" if self.module_path else node.target.id
                
                element = APIElement(
                    id=f"type:{qualified_name}",
                    name=node.target.id,
                    qualified_name=qualified_name,
                    element_type=APIElementType.TYPE_ALIAS,
                    visibility=self._get_visibility(node.target.id),
                    module_path=self.module_path,
                    file_path=self.file_path,
                    line_start=node.lineno,
                    line_end=node.end_lineno
                )
                
                self.elements[qualified_name] = element


# ============================================================
# MAIN API SURFACE EXTRACTOR
# ============================================================

class APISurfaceExtractor:
    """
    Extracts and documents public API surfaces from Python packages.
    
    Features:
    - Complete API surface extraction
    - Public/protected/private classification
    - Type hint extraction
    - Docstring parsing (Google, NumPy, Sphinx)
    - Deprecation detection
    - Stability level tracking
    - Breaking change detection between versions
    - Multiple export formats (JSON, Markdown, HTML)
    - Re-export tracking
    - Package/module hierarchy
    """
    
    def __init__(self, config: APIExtractorConfig):
        self.config = config
        self.state = StateManager(config.project_root / ".ai_state" / "api_extractor.json")
        
        # Add project root to sys.path for imports
        if str(config.project_root) not in sys.path:
            sys.path.insert(0, str(config.project_root))
        
        logger.info(f"APISurfaceExtractor initialized for {config.project_root}")
    
    # ============================================================
    # EXTRACTION
    # ============================================================
    
    def extract(self) -> APISurface:
        """Extract complete API surface."""
        start_time = datetime.now()
        logger.info("Starting API surface extraction")
        
        surface = APISurface(
            project_name=self._detect_project_name(),
            project_root=str(self.config.project_root),
            extracted_at=start_time
        )
        
        # Find packages to extract
        packages = self.config.packages or self._find_packages()
        
        for package_name in packages:
            package = self._extract_package(package_name)
            if package:
                surface.packages[package_name] = package
                
                # Add modules to global index
                for module_name, module in package.modules.items():
                    surface.modules[module_name] = module
                    
                    # Add elements to global index
                    for elem_name, element in module.elements.items():
                        surface.global_elements[elem_name] = element
        
        # Collect deprecated and experimental elements
        for element in surface.global_elements.values():
            if element.deprecation == DeprecationStatus.DEPRECATED:
                surface.deprecated_elements.append(element.qualified_name)
            if element.stability == StabilityLevel.EXPERIMENTAL:
                surface.experimental_elements.append(element.qualified_name)
        
        # Detect breaking changes if previous surface provided
        if self.config.detect_breaking_changes and self.config.previous_surface_path:
            previous = self.load_surface(self.config.previous_surface_path)
            if previous:
                surface.breaking_changes = self._detect_breaking_changes(previous, surface)
        
        # Compute statistics
        surface.statistics = self._compute_statistics(surface)
        
        extraction_duration = (datetime.now() - start_time).total_seconds()
        surface.metadata['extraction_duration'] = extraction_duration
        
        logger.info(f"API extraction complete: {len(surface.packages)} packages, {len(surface.modules)} modules, {len(surface.global_elements)} elements in {extraction_duration:.1f}s")
        
        return surface
    
    def _detect_project_name(self) -> str:
        """Detect project name."""
        # Try pyproject.toml
        pyproject = self.config.project_root / "pyproject.toml"
        if pyproject.exists():
            content = pyproject.read_text(encoding='utf-8')
            import re
            match = re.search(r'name\s*=\s*"([^"]+)"', content)
            if match:
                return match.group(1)
        
        return self.config.project_root.name
    
    def _find_packages(self) -> List[str]:
        """Find all packages in project."""
        packages = []
        
        # Look for directories with __init__.py
        for path in self.config.project_root.rglob("__init__.py"):
            rel_path = path.parent.relative_to(self.config.project_root)
            package_name = '.'.join(rel_path.parts)
            
            # Skip excluded patterns
            if self._should_include_package(package_name):
                packages.append(package_name)
        
        # Also check for single-file modules at root
        for path in self.config.project_root.glob("*.py"):
            if path.name != '__init__.py' and not path.name.startswith('_'):
                module_name = path.stem
                packages.append(module_name)
        
        return packages
    
    def _should_include_package(self, package_name: str) -> bool:
        """Check if package should be included."""
        exclude = ['test', 'tests', '__pycache__', '.git', '.venv', 'venv', 'dist', 'build']
        parts = package_name.split('.')
        return not any(p in exclude for p in parts)
    
    def _extract_package(self, package_name: str) -> Optional[APIPackage]:
        """Extract a package's API surface."""
        logger.info(f"Extracting package: {package_name}")
        
        # Find package path
        package_path = self.config.project_root / package_name.replace('.', '/')
        if not package_path.exists():
            # Try as single module
            module_path = self.config.project_root / f"{package_name}.py"
            if module_path.exists():
                module = self._extract_module(package_name, module_path)
                if module:
                    pkg = APIPackage(
                        name=package_name,
                        path=str(module_path),
                        modules={package_name: module}
                    )
                    return pkg
            return None
        
        package = APIPackage(
            name=package_name,
            path=str(package_path)
        )
        
        # Extract __init__.py
        init_path = package_path / "__init__.py"
        if init_path.exists():
            init_module = self._extract_module(package_name, init_path)
            if init_module:
                package.modules[package_name] = init_module
                package.docstring = init_module.docstring
                package.exports = init_module.exports
        
        # Extract submodules
        for py_file in package_path.glob("*.py"):
            if py_file.name == '__init__.py':
                continue
            if py_file.name.startswith('_') and not self.config.include_private:
                continue
            
            module_name = f"{package_name}.{py_file.stem}"
            module = self._extract_module(module_name, py_file)
            if module:
                package.modules[module_name] = module
        
        # Extract subpackages
        for sub_dir in package_path.iterdir():
            if sub_dir.is_dir() and (sub_dir / "__init__.py").exists():
                subpkg_name = f"{package_name}.{sub_dir.name}"
                if self._should_include_package(subpkg_name):
                    package.subpackages.append(subpkg_name)
        
        return package
    
    def _extract_module(self, module_name: str, file_path: Path) -> Optional[APIModule]:
        """Extract a module's API surface."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            # Extract API elements
            extractor = APIElementExtractor(module_name, str(file_path), self.config)
            extractor.visit(tree)
            
            module = APIModule(
                name=module_name,
                path=str(file_path),
                elements=extractor.elements,
                exports=extractor.exports,
                re_exports=extractor.re_exports,
                docstring=extractor.module_docstring
            )
            
            return module
            
        except Exception as e:
            logger.error(f"Failed to extract module {module_name}: {e}")
            return None
    
    # ============================================================
    # CHANGE DETECTION
    # ============================================================
    
    def load_surface(self, path: Path) -> Optional[APISurface]:
        """Load previously saved API surface."""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Reconstruct surface
            surface = APISurface(
                project_name=data['project_name'],
                project_root=data['project_root'],
                extracted_at=datetime.fromisoformat(data['extracted_at']),
                statistics=data.get('statistics', {}),
                metadata=data.get('metadata', {})
            )
            
            # Reconstruct elements
            for elem_data in data.get('elements', []):
                element = APIElement(
                    id=elem_data['id'],
                    name=elem_data['name'],
                    qualified_name=elem_data['qualified_name'],
                    element_type=APIElementType(elem_data['element_type']),
                    visibility=APIVisibility(elem_data['visibility']),
                    module_path=elem_data['module_path'],
                    file_path=elem_data.get('file_path'),
                    line_start=elem_data.get('line_start'),
                    line_end=elem_data.get('line_end'),
                    docstring=elem_data.get('docstring'),
                    signature=elem_data.get('signature'),
                    deprecation=DeprecationStatus(elem_data.get('deprecation', 'active')),
                    stability=StabilityLevel(elem_data.get('stability', 'stable'))
                )
                surface.global_elements[element.qualified_name] = element
            
            return surface
            
        except Exception as e:
            logger.error(f"Failed to load previous surface: {e}")
            return None
    
    def _detect_breaking_changes(self, old_surface: APISurface, new_surface: APISurface) -> List[Dict[str, Any]]:
        """Detect breaking changes between API surfaces."""
        changes = []
        
        old_elements = set(old_surface.global_elements.keys())
        new_elements = set(new_surface.global_elements.keys())
        
        # Removed elements (breaking)
        removed = old_elements - new_elements
        for elem_name in removed:
            old_elem = old_surface.global_elements[elem_name]
            if old_elem.visibility == APIVisibility.PUBLIC and old_elem.deprecation != DeprecationStatus.DEPRECATED:
                changes.append({
                    'type': 'removed',
                    'severity': 'breaking',
                    'element': elem_name,
                    'element_type': old_elem.element_type.value,
                    'message': f"Public API element '{elem_name}' was removed"
                })
        
        # Check for signature changes
        for elem_name in old_elements & new_elements:
            old_elem = old_surface.global_elements[elem_name]
            new_elem = new_surface.global_elements[elem_name]
            
            if old_elem.visibility != APIVisibility.PUBLIC:
                continue
            
            # Signature changed (potentially breaking)
            if old_elem.signature != new_elem.signature:
                changes.append({
                    'type': 'signature_changed',
                    'severity': 'breaking',
                    'element': elem_name,
                    'old_signature': old_elem.signature,
                    'new_signature': new_elem.signature,
                    'message': f"Signature of '{elem_name}' changed"
                })
            
            # Return type changed
            if old_elem.return_type != new_elem.return_type:
                changes.append({
                    'type': 'return_type_changed',
                    'severity': 'breaking',
                    'element': elem_name,
                    'old_return': old_elem.return_type,
                    'new_return': new_elem.return_type,
                    'message': f"Return type of '{elem_name}' changed"
                })
            
            # Newly deprecated
            if old_elem.deprecation == DeprecationStatus.ACTIVE and new_elem.deprecation == DeprecationStatus.DEPRECATED:
                changes.append({
                    'type': 'deprecated',
                    'severity': 'warning',
                    'element': elem_name,
                    'message': f"'{elem_name}' is now deprecated: {new_elem.deprecation_message or 'No message provided'}"
                })
        
        return changes
    
    # ============================================================
    # STATISTICS
    # ============================================================
    
    def _compute_statistics(self, surface: APISurface) -> Dict[str, Any]:
        """Compute API surface statistics."""
        stats = {
            'total_packages': len(surface.packages),
            'total_modules': len(surface.modules),
            'total_elements': len(surface.global_elements),
            'by_type': {},
            'by_visibility': {
                'public': 0,
                'protected': 0,
                'private': 0
            },
            'by_stability': {
                'stable': 0,
                'beta': 0,
                'experimental': 0,
                'internal': 0,
                'deprecated': 0
            },
            'deprecated_count': len(surface.deprecated_elements),
            'experimental_count': len(surface.experimental_elements),
            'elements_with_docstrings': 0,
            'elements_with_type_hints': 0
        }
        
        for element in surface.global_elements.values():
            # By type
            elem_type = element.element_type.value
            stats['by_type'][elem_type] = stats['by_type'].get(elem_type, 0) + 1
            
            # By visibility
            stats['by_visibility'][element.visibility.value] += 1
            
            # By stability
            stats['by_stability'][element.stability.value] += 1
            
            # Docstrings
            if element.docstring:
                stats['elements_with_docstrings'] += 1
            
            # Type hints
            if element.return_type or any(p.type_annotation for p in element.parameters):
                stats['elements_with_type_hints'] += 1
        
        return stats
    
    # ============================================================
    # QUERY METHODS
    # ============================================================
    
    def get_element(self, qualified_name: str) -> Optional[APIElement]:
        """Get element by qualified name."""
        return self._current_surface.global_elements.get(qualified_name) if hasattr(self, '_current_surface') else None
    
    def get_module_elements(self, module_name: str) -> List[APIElement]:
        """Get all elements in a module."""
        if not hasattr(self, '_current_surface'):
            return []
        
        module = self._current_surface.modules.get(module_name)
        if module:
            return list(module.elements.values())
        return []
    
    def get_package_elements(self, package_name: str) -> List[APIElement]:
        """Get all elements in a package."""
        if not hasattr(self, '_current_surface'):
            return []
        
        elements = []
        package = self._current_surface.packages.get(package_name)
        if package:
            for module in package.modules.values():
                elements.extend(module.elements.values())
        return elements
    
    def search(self, query: str) -> List[APIElement]:
        """Search for API elements by name."""
        if not hasattr(self, '_current_surface'):
            return []
        
        query_lower = query.lower()
        return [
            elem for elem in self._current_surface.global_elements.values()
            if query_lower in elem.name.lower() or query_lower in elem.qualified_name.lower()
        ]
    
    # ============================================================
    # EXPORT
    # ============================================================
    
    def export(self, surface: APISurface, output_path: Optional[Path] = None, format: str = "json") -> Union[str, Path]:
        """Export API surface."""
        self._current_surface = surface
        
        if format == "json":
            return self._export_json(surface, output_path)
        elif format == "markdown":
            return self._export_markdown(surface, output_path)
        elif format == "html":
            return self._export_html(surface, output_path)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def _export_json(self, surface: APISurface, output_path: Optional[Path] = None) -> Union[str, Path]:
        """Export as JSON."""
        data = {
            'project_name': surface.project_name,
            'project_root': surface.project_root,
            'extracted_at': surface.extracted_at.isoformat(),
            'statistics': surface.statistics,
            'deprecated_elements': surface.deprecated_elements,
            'experimental_elements': surface.experimental_elements,
            'breaking_changes': surface.breaking_changes,
            'elements': [
                {
                    'id': e.id,
                    'name': e.name,
                    'qualified_name': e.qualified_name,
                    'element_type': e.element_type.value,
                    'visibility': e.visibility.value,
                    'module_path': e.module_path,
                    'file_path': e.file_path,
                    'line_start': e.line_start,
                    'line_end': e.line_end,
                    'docstring': e.docstring,
                    'signature': e.signature,
                    'parameters': [
                        {
                            'name': p.name,
                            'type_annotation': p.type_annotation,
                            'default_value': p.default_value
                        }
                        for p in e.parameters
                    ],
                    'return_type': e.return_type,
                    'decorators': e.decorators,
                    'bases': e.bases,
                    'deprecation': e.deprecation.value,
                    'deprecation_message': e.deprecation_message,
                    'stability': e.stability.value
                }
                for e in surface.global_elements.values()
            ]
        }
        
        content = json.dumps(data, indent=2)
        
        if output_path:
            output_path.write_text(content)
            return output_path
        return content
    
    def _export_markdown(self, surface: APISurface, output_path: Optional[Path] = None) -> Union[str, Path]:
        """Export as Markdown documentation."""
        lines = [
            f"# API Reference: {surface.project_name}",
            "",
            f"*Extracted: {surface.extracted_at.strftime('%Y-%m-%d %H:%M:%S')}*",
            "",
            "## Summary",
            "",
            f"- **Packages:** {surface.statistics['total_packages']}",
            f"- **Modules:** {surface.statistics['total_modules']}",
            f"- **API Elements:** {surface.statistics['total_elements']}",
            "",
            "### By Type",
            "",
            "| Type | Count |",
            "|------|-------|",
        ]
        
        for elem_type, count in sorted(surface.statistics['by_type'].items()):
            lines.append(f"| {elem_type} | {count} |")
        
        if surface.deprecated_elements:
            lines.extend([
                "",
                "## Deprecated Elements",
                "",
            ])
            for elem in surface.deprecated_elements[:20]:
                lines.append(f"- `{elem}`")
            if len(surface.deprecated_elements) > 20:
                lines.append(f"- *...and {len(surface.deprecated_elements) - 20} more*")
        
        # Group by module
        lines.extend([
            "",
            "## API Elements by Module",
            ""
        ])
        
        for module_name in sorted(surface.modules.keys()):
            module = surface.modules[module_name]
            if not module.elements:
                continue
            
            lines.extend([
                f"### `{module_name}`",
                ""
            ])
            
            if module.docstring:
                lines.extend([
                    module.docstring,
                    ""
                ])
            
            for elem_name, element in sorted(module.elements.items()):
                # Skip if not public
                if element.visibility != APIVisibility.PUBLIC:
                    continue
                
                # Element header
                badges = []
                if element.deprecation == DeprecationStatus.DEPRECATED:
                    badges.append("⚠️ **DEPRECATED**")
                if element.stability == StabilityLevel.EXPERIMENTAL:
                    badges.append("🧪 **EXPERIMENTAL**")
                if element.stability == StabilityLevel.BETA:
                    badges.append("🔬 **BETA**")
                
                badge_str = " " + " ".join(badges) if badges else ""
                
                lines.append(f"#### `{element.name}`{badge_str}")
                lines.append("")
                
                if element.signature:
                    lines.extend([
                        "```python",
                        element.signature,
                        "```",
                        ""
                    ])
                
                if element.docstring:
                    lines.extend([
                        element.docstring,
                        ""
                    ])
                
                if element.deprecation_message:
                    lines.extend([
                        f"**Deprecation Notice:** {element.deprecation_message}",
                        ""
                    ])
                
                lines.append("---")
                lines.append("")
        
        content = '\n'.join(lines)
        
        if output_path:
            output_path.write_text(content)
            return output_path
        return content
    
    def _export_html(self, surface: APISurface, output_path: Optional[Path] = None) -> Union[str, Path]:
        """Export as HTML documentation."""
        html = self._generate_html_docs(surface)
        
        if output_path:
            output_path.write_text(html)
            return output_path
        return html
    
    def _generate_html_docs(self, surface: APISurface) -> str:
        """Generate HTML documentation."""
        # Group elements by module for sidebar
        modules_list = []
        for module_name in sorted(surface.modules.keys()):
            module = surface.modules[module_name]
            public_elements = [e for e in module.elements.values() if e.visibility == APIVisibility.PUBLIC]
            if public_elements:
                modules_list.append({
                    'name': module_name,
                    'elements': sorted(public_elements, key=lambda e: e.name)
                })
        
        html = f'''<!DOCTYPE html>
<html>
<head>
    <title>API Reference - {surface.project_name}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 0;
            display: flex;
        }}
        .sidebar {{
            width: 300px;
            background: #f5f5f5;
            padding: 20px;
            height: 100vh;
            overflow-y: auto;
            position: sticky;
            top: 0;
        }}
        .content {{
            flex: 1;
            padding: 40px;
            max-width: 900px;
        }}
        .sidebar h3 {{
            margin-top: 0;
            color: #333;
        }}
        .sidebar ul {{
            list-style: none;
            padding-left: 15px;
        }}
        .sidebar li {{
            margin: 5px 0;
        }}
        .sidebar a {{
            color: #0366d6;
            text-decoration: none;
        }}
        .sidebar a:hover {{
            text-decoration: underline;
        }}
        .badge {{
            display: inline-block;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 600;
            margin-left: 8px;
        }}
        .badge-deprecated {{
            background: #d32f2f;
            color: white;
        }}
        .badge-experimental {{
            background: #f57c00;
            color: white;
        }}
        .badge-beta {{
            background: #1976d2;
            color: white;
        }}
        .signature {{
            background: #f6f8fa;
            padding: 15px;
            border-radius: 6px;
            overflow-x: auto;
            margin: 15px 0;
        }}
        .docstring {{
            margin: 15px 0;
            padding: 15px;
            background: #fff;
            border-left: 4px solid #0366d6;
        }}
        hr {{
            margin: 30px 0;
            border: none;
            border-top: 1px solid #e1e4e8;
        }}
        h1 {{ color: #333; }}
        h2 {{ color: #333; margin-top: 30px; }}
        h3 {{ color: #333; }}
        h4 {{ color: #333; margin-bottom: 10px; }}
        code {{
            background: #f6f8fa;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'SF Mono', Monaco, 'Cascadia Code', monospace;
            font-size: 13px;
        }}
        pre {{
            background: #f6f8fa;
            padding: 15px;
            border-radius: 6px;
            overflow-x: auto;
        }}
        pre code {{
            background: none;
            padding: 0;
        }}
    </style>
</head>
<body>
    <div class="sidebar">
        <h3>{surface.project_name}</h3>
        <p><small>Extracted: {surface.extracted_at.strftime('%Y-%m-%d')}</small></p>
        <ul>
'''
        
        for module_info in modules_list:
            html += f'<li><strong>{module_info["name"]}</strong><ul>'
            for elem in module_info['elements']:
                html += f'<li><a href="#{elem.id}">{elem.name}</a></li>'
            html += '</ul></li>'
        
        html += '''
                </ul>
            </div>
            <div class="content">
                <h1>API Reference</h1>
                <p>Public API surface for {surface.project_name}</p>
                
                <h2>Summary</h2>
                <ul>
'''
        
        html += f'''
                    <li><strong>Packages:</strong> {surface.statistics['total_packages']}</li>
                    <li><strong>Modules:</strong> {surface.statistics['total_modules']}</li>
                    <li><strong>API Elements:</strong> {surface.statistics['total_elements']}</li>
                </ul>
'''
        
        if surface.deprecated_elements:
            html += '''
                <h2>⚠️ Deprecated Elements</h2>
                <ul>
'''
            for elem in surface.deprecated_elements[:20]:
                html += f'<li><code>{elem}</code></li>'
            html += '</ul>'
        
        html += '<h2>API Elements</h2>'
        
        for module_info in modules_list:
            for element in module_info['elements']:
                html += f'<div id="{element.id}">'
                html += f'<h3><code>{element.name}</code>'
                
                if element.deprecation == DeprecationStatus.DEPRECATED:
                    html += '<span class="badge badge-deprecated">DEPRECATED</span>'
                if element.stability == StabilityLevel.EXPERIMENTAL:
                    html += '<span class="badge badge-experimental">EXPERIMENTAL</span>'
                if element.stability == StabilityLevel.BETA:
                    html += '<span class="badge badge-beta">BETA</span>'
                
                html += f'</h3>'
                html += f'<p><small>Module: <code>{element.module_path}</code></small></p>'
                
                if element.signature:
                    html += f'<div class="signature"><code>{element.signature}</code></div>'
                
                if element.docstring:
                    html += f'<div class="docstring">{element.docstring}</div>'
                
                if element.deprecation_message:
                    html += f'<p><strong>⚠️ Deprecation Notice:</strong> {element.deprecation_message}</p>'
                
                html += '</div><hr>'
        
        html += '''
            </div>
        </body>
        </html>
        '''
        
        return html
    
    def close(self):
        """Clean up resources."""
        self.state.save()
        logger.info("APISurfaceExtractor closed")


# ============================================================
# CLI ENTRY POINT
# ============================================================

def main():
    """CLI entry point for API surface extractor."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Extract and document Python API surfaces")
    parser.add_argument("--project-root", type=Path, default=Path.cwd(),
                       help="Project root directory")
    parser.add_argument("--packages", nargs="*", help="Specific packages to extract")
    parser.add_argument("--output", "-o", type=Path, help="Output file")
    parser.add_argument("--format", choices=["json", "markdown", "html"], default="markdown",
                       help="Output format")
    parser.add_argument("--include-private", action="store_true", help="Include private elements")
    parser.add_argument("--include-protected", action="store_true", help="Include protected elements")
    parser.add_argument("--previous", type=Path, help="Previous API surface for change detection")
    parser.add_argument("--detect-breaking", action="store_true", help="Detect breaking changes")
    
    args = parser.parse_args()
    
    config = APIExtractorConfig(
        project_root=args.project_root,
        packages=args.packages or [],
        include_private=args.include_private,
        include_protected=args.include_protected,
        detect_breaking_changes=args.detect_breaking,
        previous_surface_path=args.previous
    )
    
    extractor = APISurfaceExtractor(config)
    surface = extractor.extract()
    
    output = extractor.export(surface, args.output, args.format)
    
    if args.output:
        print(f"API surface exported to {args.output}")
    else:
        print(output)
    
    extractor.close()


if __name__ == "__main__":
    main()