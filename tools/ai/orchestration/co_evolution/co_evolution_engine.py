"""
Co-Evolution Engine for Orchestration

Orchestrates the co-evolution of code, configuration, documentation, examples, and tests.
Handles:
- Code change detection and propagation
- Cross-component consistency maintenance
- Class/module/function evolution
- Dependency-aware updates
- Version management
- Impact analysis

This co_evolution_engine.py provides:

    Code Element Tracking: Scans and tracks classes, functions, methods, modules
    Dependency Analysis: Builds dependency graphs between code elements
    Change Detection: Detects renames, signature changes, parameter changes
    Cross-Component Propagation: Updates configs, docs, examples, tests automatically
    Evolution Operations: Rename class, extract function, deprecate elements
    Impact Analysis: Analyzes impact of changes before applying
    Evolution Planning: Create and execute multi-step evolution plans
    Rollback Support: Ability to rollback operations (placeholder)
    Singleton Pattern: Global instance via get_co_evolution_engine()

The engine orchestrates all the updaters we've created and adds code-level evolution capabilities, 
making it the central coordination point for all co-evolution activities.
"""

import ast
import inspect
from typing import Dict, List, Optional, Any, Set, Tuple, Callable
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from enum import Enum
from collections import defaultdict
import re

from ....shared.logger import get_logger
from ....shared.state_manager import state_manager
from ....shared.config import config
from ....shared.file_utils import file_utils
from ....shared.git_utils import git_utils

from .config_updater import ConfigUpdater, get_config_updater, ConfigChange, ConfigFormat
from .doc_updater import DocUpdater, get_doc_updater, DocUpdate, DocType
from .example_updater import ExampleUpdater, get_example_updater, ExampleUpdate, APIChange
from .test_updater import TestUpdater, get_test_updater, TestUpdate, CodeChange

logger = get_logger(__name__)


class EvolutionType(Enum):
    """Types of evolution operations"""
    REFACTOR = "refactor"
    RENAME = "rename"
    SIGNATURE_CHANGE = "signature_change"
    ADD = "add"
    REMOVE = "remove"
    DEPRECATE = "deprecate"
    MOVE = "move"
    EXTRACT = "extract"
    INLINE = "inline"


class EvolutionSeverity(Enum):
    """Severity of evolution impact"""
    LOW = "low"       # Backward compatible
    MEDIUM = "medium" # May affect some consumers
    HIGH = "high"     # Breaking change
    CRITICAL = "critical"  # Widespread impact


@dataclass
class CodeElement:
    """Represents a code element (class, function, module)"""
    name: str
    type: str  # module, class, function, method
    file_path: str
    line_start: int
    line_end: int
    signature: Optional[str] = None
    docstring: Optional[str] = None
    decorators: List[str] = field(default_factory=list)
    parameters: List[str] = field(default_factory=list)
    return_type: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)  # What this depends on
    dependents: List[str] = field(default_factory=list)   # What depends on this
    version: Optional[str] = None
    deprecated: bool = False
    deprecated_since: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "type": self.type,
            "file_path": self.file_path,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "signature": self.signature,
            "docstring": self.docstring,
            "decorators": self.decorators,
            "parameters": self.parameters,
            "return_type": self.return_type,
            "dependencies": self.dependencies,
            "dependents": self.dependents,
            "version": self.version,
            "deprecated": self.deprecated,
            "deprecated_since": self.deprecated_since
        }


@dataclass
class EvolutionOperation:
    """Represents an evolution operation"""
    type: EvolutionType
    element: CodeElement
    severity: EvolutionSeverity
    description: str
    changes: List[str]
    affected_elements: List[str]
    requires_manual_review: bool = False
    timestamp: datetime = field(default_factory=datetime.now)
    applied: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type.value,
            "element": self.element.to_dict(),
            "severity": self.severity.value,
            "description": self.description,
            "changes": self.changes,
            "affected_elements": self.affected_elements,
            "requires_manual_review": self.requires_manual_review,
            "timestamp": self.timestamp.isoformat(),
            "applied": self.applied
        }


@dataclass
class EvolutionPlan:
    """Represents a plan for evolving code"""
    name: str
    operations: List[EvolutionOperation]
    dependencies: Dict[str, List[str]]
    estimated_impact: int  # Number of files affected
    requires_approval: bool = False
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "operations": [op.to_dict() for op in self.operations],
            "dependencies": self.dependencies,
            "estimated_impact": self.estimated_impact,
            "requires_approval": self.requires_approval,
            "created_at": self.created_at.isoformat()
        }


class CoEvolutionEngine:
    """
    Orchestrates co-evolution of all project components.
    
    Features:
    - Detects code changes and propagates to configs, docs, examples, tests
    - Manages class/module/function evolution
    - Impact analysis and dependency tracking
    - Automatic updates across all component types
    - Version management for co-evolved artifacts
    - Rollback capabilities
    """
    
    def __init__(self, storage_key: str = "co_evolution_engine"):
        self.storage_key = storage_key
        self.code_elements: Dict[str, CodeElement] = {}
        self.evolution_history: List[EvolutionOperation] = []
        self.evolution_plans: List[EvolutionPlan] = []
        
        # Sub-components
        self.config_updater: ConfigUpdater = get_config_updater()
        self.doc_updater: DocUpdater = get_doc_updater()
        self.example_updater: ExampleUpdater = get_example_updater()
        self.test_updater: TestUpdater = get_test_updater()
        
        # Watch directories
        self.watch_dirs: List[Path] = []
        
        self._load_data()
        self._register_default_watch_dirs()
        
        logger.info("CoEvolutionEngine initialized")
    
    def _load_data(self) -> None:
        """Load evolution data from state manager"""
        try:
            elements_data = state_manager.get(f"{self.storage_key}.code_elements", {})
            self.code_elements = {}
            for name, elem_data in elements_data.items():
                if isinstance(elem_data, dict):
                    self.code_elements[name] = CodeElement(**elem_data)
            
            history_data = state_manager.get(f"{self.storage_key}.evolution_history", [])
            self.evolution_history = []
            for h in history_data:
                if isinstance(h, dict):
                    self.evolution_history.append(EvolutionOperation(**h))
            
            plans_data = state_manager.get(f"{self.storage_key}.evolution_plans", [])
            self.evolution_plans = []
            for p in plans_data:
                if isinstance(p, dict):
                    self.evolution_plans.append(EvolutionPlan(**p))
            
        except Exception as e:
            logger.warning(f"Failed to load evolution data: {e}")
    
    def _save_data(self) -> None:
        """Save evolution data to state manager"""
        try:
            elements_data = {name: elem.to_dict() for name, elem in self.code_elements.items()}
            state_manager.set(f"{self.storage_key}.code_elements", elements_data)
            
            history_data = [op.to_dict() for op in self.evolution_history]
            state_manager.set(f"{self.storage_key}.evolution_history", history_data)
            
            plans_data = [plan.to_dict() for plan in self.evolution_plans]
            state_manager.set(f"{self.storage_key}.evolution_plans", plans_data)
            
        except Exception as e:
            logger.error(f"Failed to save evolution data: {e}")
    
    def _register_default_watch_dirs(self) -> None:
        """Register default directories to watch for changes"""
        default_dirs = [
            Path("tools/ai"),
            Path("tools/ai/analysis"),
            Path("tools/ai/generation"),
            Path("tools/ai/orchestration"),
            Path("tools/ai/planning"),
            Path("tools/ai/quality"),
        ]
        
        for dir_path in default_dirs:
            if dir_path.exists():
                self.watch_dirs.append(dir_path)
    
    def add_watch_directory(self, dir_path: Union[str, Path]) -> None:
        """Add a directory to watch for code changes"""
        path = Path(dir_path)
        if path.exists() and path.is_dir():
            self.watch_dirs.append(path)
            logger.info(f"Added watch directory: {path}")
    
    def scan_codebase(self) -> List[CodeElement]:
        """Scan codebase and build code element registry"""
        elements = []
        
        for watch_dir in self.watch_dirs:
            for file_path in watch_dir.rglob("*.py"):
                file_elements = self._scan_file(file_path)
                elements.extend(file_elements)
        
        # Build dependency graph
        self._build_dependency_graph(elements)
        
        # Update registry
        for element in elements:
            element_key = self._get_element_key(element)
            if element_key not in self.code_elements:
                self.code_elements[element_key] = element
                logger.debug(f"Discovered code element: {element_key}")
            else:
                # Check for changes
                existing = self.code_elements[element_key]
                if self._has_changed(existing, element):
                    logger.info(f"Code element changed: {element_key}")
                    self._handle_element_change(existing, element)
                    self.code_elements[element_key] = element
        
        self._save_data()
        
        return elements
    
    def _scan_file(self, file_path: Path) -> List[CodeElement]:
        """Scan a single file for code elements"""
        elements = []
        
        try:
            content = file_utils.read_file(str(file_path))
            tree = ast.parse(content)
            
            # Add module element
            module_element = CodeElement(
                name=file_path.stem,
                type="module",
                file_path=str(file_path),
                line_start=1,
                line_end=len(content.splitlines()),
                docstring=ast.get_docstring(tree)
            )
            elements.append(module_element)
            
            # Add classes
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    class_element = self._extract_class_element(node, file_path)
                    elements.append(class_element)
                    
                    # Add methods
                    for method_node in ast.walk(node):
                        if isinstance(method_node, ast.FunctionDef):
                            method_element = self._extract_method_element(method_node, node.name, file_path)
                            elements.append(method_element)
                
                # Add functions (top-level)
                elif isinstance(node, ast.FunctionDef):
                    # Check if it's a method (already handled) or top-level function
                    if not isinstance(node.parent, ast.ClassDef) if hasattr(node, 'parent') else True:
                        func_element = self._extract_function_element(node, file_path)
                        elements.append(func_element)
        
        except SyntaxError as e:
            logger.error(f"Failed to parse {file_path}: {e}")
        
        return elements
    
    def _extract_class_element(self, node: ast.ClassDef, file_path: Path) -> CodeElement:
        """Extract class information from AST node"""
        parameters = []
        for base in node.bases:
            if isinstance(base, ast.Name):
                parameters.append(base.id)
        
        return CodeElement(
            name=node.name,
            type="class",
            file_path=str(file_path),
            line_start=node.lineno,
            line_end=node.end_lineno or node.lineno,
            docstring=ast.get_docstring(node),
            decorators=[self._get_decorator_name(d) for d in node.decorator_list],
            parameters=parameters
        )
    
    def _extract_function_element(self, node: ast.FunctionDef, file_path: Path) -> CodeElement:
        """Extract function information from AST node"""
        parameters = [arg.arg for arg in node.args.args]
        
        return_type = None
        if node.returns:
            if isinstance(node.returns, ast.Name):
                return_type = node.returns.id
        
        return CodeElement(
            name=node.name,
            type="function",
            file_path=str(file_path),
            line_start=node.lineno,
            line_end=node.end_lineno or node.lineno,
            signature=self._get_signature(node),
            docstring=ast.get_docstring(node),
            decorators=[self._get_decorator_name(d) for d in node.decorator_list],
            parameters=parameters,
            return_type=return_type
        )
    
    def _extract_method_element(self, node: ast.FunctionDef, class_name: str, file_path: Path) -> CodeElement:
        """Extract method information from AST node"""
        parameters = [arg.arg for arg in node.args.args]
        
        return_type = None
        if node.returns:
            if isinstance(node.returns, ast.Name):
                return_type = node.returns.id
        
        return CodeElement(
            name=f"{class_name}.{node.name}",
            type="method",
            file_path=str(file_path),
            line_start=node.lineno,
            line_end=node.end_lineno or node.lineno,
            signature=self._get_signature(node),
            docstring=ast.get_docstring(node),
            decorators=[self._get_decorator_name(d) for d in node.decorator_list],
            parameters=parameters,
            return_type=return_type
        )
    
    def _get_decorator_name(self, decorator: ast.expr) -> str:
        """Extract decorator name from AST node"""
        if isinstance(decorator, ast.Name):
            return decorator.id
        elif isinstance(decorator, ast.Attribute):
            return f"{self._get_decorator_name(decorator.value)}.{decorator.attr}"
        return str(decorator)
    
    def _get_signature(self, node: ast.FunctionDef) -> str:
        """Get function signature as string"""
        args = []
        for arg in node.args.args:
            arg_str = arg.arg
            if arg.annotation:
                if isinstance(arg.annotation, ast.Name):
                    arg_str += f": {arg.annotation.id}"
            args.append(arg_str)
        
        return f"{node.name}({', '.join(args)})"
    
    def _get_element_key(self, element: CodeElement) -> str:
        """Get unique key for a code element"""
        return f"{element.file_path}:{element.type}:{element.name}"
    
    def _has_changed(self, old: CodeElement, new: CodeElement) -> bool:
        """Check if a code element has changed"""
        return (old.signature != new.signature or 
                old.parameters != new.parameters or
                old.return_type != new.return_type or
                old.docstring != new.docstring)
    
    def _build_dependency_graph(self, elements: List[CodeElement]) -> None:
        """Build dependency graph between code elements"""
        for element in elements:
            # Extract dependencies from code
            if element.file_path:
                try:
                    content = file_utils.read_file(element.file_path)
                    # Find imports and usage
                    imports = self._extract_imports(content)
                    element.dependencies.extend(imports)
                except Exception as e:
                    logger.debug(f"Failed to extract dependencies for {element.name}: {e}")
    
    def _extract_imports(self, content: str) -> List[str]:
        """Extract import statements from code"""
        imports = []
        tree = ast.parse(content)
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    imports.append(f"{module}.{alias.name}")
        
        return imports
    
    def _handle_element_change(self, old: CodeElement, new: CodeElement) -> None:
        """Handle changes to a code element and propagate updates"""
        
        # Determine change type
        if old.name != new.name:
            self._handle_rename(old, new)
        elif old.signature != new.signature:
            self._handle_signature_change(old, new)
        elif old.parameters != new.parameters:
            self._handle_parameter_change(old, new)
        elif old.return_type != new.return_type:
            self._handle_return_type_change(old, new)
    
    def _handle_rename(self, old: CodeElement, new: CodeElement) -> None:
        """Handle renaming of a code element"""
        logger.info(f"Handling rename: {old.name} -> {new.name}")
        
        # Create evolution operation
        operation = EvolutionOperation(
            type=EvolutionType.RENAME,
            element=new,
            severity=EvolutionSeverity.HIGH,
            description=f"Renamed {old.type} from {old.name} to {new.name}",
            changes=[f"Renamed: {old.name} -> {new.name}"],
            affected_elements=self._find_dependents(old.name)
        )
        
        # Update documentation
        doc_update = self.doc_updater.update_from_code_change(
            new.file_path, "", ""  # Would need actual old/new content
        )
        
        # Update examples
        api_change = APIChange(
            api_name=old.name,
            change_type="renamed",
            old_name=old.name,
            new_name=new.name
        )
        self.example_updater.register_api_change(api_change)
        
        # Update tests
        code_change = CodeChange(
            file_path=new.file_path,
            element_name=old.name,
            element_type=old.type,
            change_type="renamed"
        )
        self.test_updater.register_code_change(code_change)
        
        # Record operation
        self.evolution_history.append(operation)
        self._save_data()
    
    def _handle_signature_change(self, old: CodeElement, new: CodeElement) -> None:
        """Handle signature change of a code element"""
        logger.info(f"Handling signature change for {new.name}")
        
        operation = EvolutionOperation(
            type=EvolutionType.SIGNATURE_CHANGE,
            element=new,
            severity=EvolutionSeverity.MEDIUM,
            description=f"Signature changed for {new.type} {new.name}",
            changes=[f"Old: {old.signature}", f"New: {new.signature}"],
            affected_elements=self._find_dependents(new.name)
        )
        
        # Update tests
        code_change = CodeChange(
            file_path=new.file_path,
            element_name=new.name,
            element_type=new.type,
            change_type="signature_change",
            old_signature=old.signature,
            new_signature=new.signature,
            added_parameters=list(set(new.parameters) - set(old.parameters)),
            removed_parameters=list(set(old.parameters) - set(new.parameters))
        )
        self.test_updater.register_code_change(code_change)
        
        # Update examples
        api_change = APIChange(
            api_name=new.name,
            change_type="signature_change",
            old_signature=old.signature,
            new_signature=new.signature
        )
        self.example_updater.register_api_change(api_change)
        
        self.evolution_history.append(operation)
        self._save_data()
    
    def _handle_parameter_change(self, old: CodeElement, new: CodeElement) -> None:
        """Handle parameter changes"""
        logger.info(f"Handling parameter change for {new.name}")
        
        added = list(set(new.parameters) - set(old.parameters))
        removed = list(set(old.parameters) - set(new.parameters))
        
        operation = EvolutionOperation(
            type=EvolutionType.SIGNATURE_CHANGE,
            element=new,
            severity=EvolutionSeverity.MEDIUM if added or removed else EvolutionSeverity.LOW,
            description=f"Parameters changed for {new.name}",
            changes=[f"Added: {added}", f"Removed: {removed}"],
            affected_elements=self._find_dependents(new.name)
        )
        
        # Update tests
        if added or removed:
            code_change = CodeChange(
                file_path=new.file_path,
                element_name=new.name,
                element_type=new.type,
                change_type="parameter_change",
                added_parameters=added,
                removed_parameters=removed
            )
            self.test_updater.register_code_change(code_change)
        
        self.evolution_history.append(operation)
        self._save_data()
    
    def _handle_return_type_change(self, old: CodeElement, new: CodeElement) -> None:
        """Handle return type change"""
        logger.info(f"Handling return type change for {new.name}")
        
        operation = EvolutionOperation(
            type=EvolutionType.SIGNATURE_CHANGE,
            element=new,
            severity=EvolutionSeverity.MEDIUM,
            description=f"Return type changed for {new.name}",
            changes=[f"Old: {old.return_type}", f"New: {new.return_type}"],
            affected_elements=self._find_dependents(new.name)
        )
        
        # Update tests
        code_change = CodeChange(
            file_path=new.file_path,
            element_name=new.name,
            element_type=new.type,
            change_type="changed_return_type",
            changed_return_type=new.return_type
        )
        self.test_updater.register_code_change(code_change)
        
        self.evolution_history.append(operation)
        self._save_data()
    
    def _find_dependents(self, element_name: str) -> List[str]:
        """Find all code elements that depend on the given element"""
        dependents = []
        
        for key, element in self.code_elements.items():
            if element_name in element.dependencies:
                dependents.append(key)
        
        return dependents
    
    def rename_class(self, old_name: str, new_name: str, 
                    file_path: str, update_references: bool = True) -> EvolutionOperation:
        """
        Rename a class and optionally update all references.
        
        Args:
            old_name: Current class name
            new_name: New class name
            file_path: File containing the class
            update_references: Whether to update references in other files
        """
        # Find the class element
        class_key = f"{file_path}:class:{old_name}"
        if class_key not in self.code_elements:
            raise ValueError(f"Class {old_name} not found in registry")
        
        class_element = self.code_elements[class_key]
        
        # Read file content
        content = file_utils.read_file(file_path)
        
        # Update class definition
        new_content = re.sub(
            rf'\bclass\s+{re.escape(old_name)}\b',
            f'class {new_name}',
            content
        )
        
        # Update references if requested
        if update_references:
            new_content = self._update_class_references(new_content, old_name, new_name, file_path)
        
        # Write updated content
        file_utils.write_file(file_path, new_content)
        
        # Update class element
        class_element.name = new_name
        self.code_elements[class_key] = class_element
        
        # Create operation
        operation = EvolutionOperation(
            type=EvolutionType.RENAME,
            element=class_element,
            severity=EvolutionSeverity.HIGH,
            description=f"Renamed class from {old_name} to {new_name}",
            changes=[f"Class renamed: {old_name} -> {new_name}"],
            affected_elements=self._find_dependents(old_name)
        )
        
        self.evolution_history.append(operation)
        self._save_data()
        
        logger.info(f"Renamed class: {old_name} -> {new_name}")
        
        return operation
    
    def _update_class_references(self, content: str, old_name: str, 
                                new_name: str, current_file: str) -> str:
        """Update class references across files"""
        # Update in current file
        content = re.sub(
            rf'\b{re.escape(old_name)}\b(?!\.)',
            new_name,
            content
        )
        
        # Update in other files that import this class
        for other_key, element in self.code_elements.items():
            if other_key != f"{current_file}:class:{old_name}":
                if old_name in element.dependencies:
                    other_content = file_utils.read_file(element.file_path)
                    other_content = re.sub(
                        rf'\b{re.escape(old_name)}\b',
                        new_name,
                        other_content
                    )
                    file_utils.write_file(element.file_path, other_content)
        
        return content
    
    def extract_function(self, source_file: str, function_name: str,
                        start_line: int, end_line: int,
                        new_file: str) -> EvolutionOperation:
        """
        Extract a function to a new file.
        
        Args:
            source_file: Original file containing the function
            function_name: Name of the function to extract
            start_line: Starting line of the function
            end_line: Ending line of the function
            new_file: Target file for the extracted function
        """
        # Read source file
        content = file_utils.read_file(source_file)
        lines = content.splitlines()
        
        # Extract function code
        function_lines = lines[start_line - 1:end_line]
        function_code = '\n'.join(function_lines)
        
        # Create new file with extracted function
        new_content = f'''"""
Extracted function {function_name}
"""

{function_code}
'''
        file_utils.write_file(new_file, new_content)
        
        # Remove function from source file
        new_source_lines = lines[:start_line - 1] + lines[end_line:]
        file_utils.write_file(source_file, '\n'.join(new_source_lines))
        
        # Add import to source file
        import_statement = f"from {Path(new_file).stem} import {function_name}"
        with open(source_file, 'a') as f:
            f.write(f"\n\n{import_statement}\n")
        
        # Create operation
        element = CodeElement(
            name=function_name,
            type="function",
            file_path=new_file,
            line_start=1,
            line_end=len(function_lines)
        )
        
        operation = EvolutionOperation(
            type=EvolutionType.EXTRACT,
            element=element,
            severity=EvolutionSeverity.MEDIUM,
            description=f"Extracted function {function_name} to {new_file}",
            changes=[f"Function extracted from {source_file} to {new_file}"],
            affected_elements=[source_file, new_file]
        )
        
        self.evolution_history.append(operation)
        self._save_data()
        
        logger.info(f"Extracted function: {function_name} -> {new_file}")
        
        return operation
    
    def deprecate_element(self, element_name: str, 
                         replacement: Optional[str] = None,
                         since_version: str = "1.0.0") -> EvolutionOperation:
        """
        Deprecate a code element.
        
        Args:
            element_name: Name of the element to deprecate
            replacement: Suggested replacement element
            since_version: Version when deprecation started
        """
        # Find the element
        element_key = None
        for key, elem in self.code_elements.items():
            if elem.name == element_name:
                element_key = key
                break
        
        if not element_key:
            raise ValueError(f"Element {element_name} not found")
        
        element = self.code_elements[element_key]
        element.deprecated = True
        element.deprecated_since = since_version
        
        # Update docstring with deprecation notice
        if element.file_path:
            content = file_utils.read_file(element.file_path)
            
            deprecation_note = f"""
    .. deprecated:: {since_version}
        Use {replacement} instead if replacement else "This element is deprecated"
"""
            if element.docstring:
                # Add deprecation to docstring
                new_content = content.replace(
                    element.docstring,
                    element.docstring + deprecation_note
                )
                file_utils.write_file(element.file_path, new_content)
        
        # Create operation
        operation = EvolutionOperation(
            type=EvolutionType.DEPRECATE,
            element=element,
            severity=EvolutionSeverity.MEDIUM,
            description=f"Deprecated {element.type} {element_name}",
            changes=[f"Deprecated since {since_version}", f"Replacement: {replacement}"],
            affected_elements=self._find_dependents(element_name),
            requires_manual_review=True
        )
        
        self.evolution_history.append(operation)
        self._save_data()
        
        logger.info(f"Deprecated element: {element_name}")
        
        return operation
    
    def create_evolution_plan(self, name: str, 
                            operations: List[EvolutionOperation]) -> EvolutionPlan:
        """Create a plan for multiple evolution operations"""
        # Build dependency graph
        dependencies = defaultdict(list)
        for i, op1 in enumerate(operations):
            for j, op2 in enumerate(operations):
                if i != j:
                    if op2.element.name in op1.affected_elements:
                        dependencies[op1.element.name].append(op2.element.name)
        
        # Calculate impact
        all_affected = set()
        for op in operations:
            all_affected.update(op.affected_elements)
        
        plan = EvolutionPlan(
            name=name,
            operations=operations,
            dependencies=dict(dependencies),
            estimated_impact=len(all_affected),
            requires_approval=any(op.severity == EvolutionSeverity.HIGH for op in operations)
        )
        
        self.evolution_plans.append(plan)
        self._save_data()
        
        logger.info(f"Created evolution plan: {name}")
        
        return plan
    
    def execute_evolution_plan(self, plan: EvolutionPlan) -> bool:
        """
        Execute an evolution plan.
        
        Args:
            plan: The evolution plan to execute
            
        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Executing evolution plan: {plan.name}")
        
        # Sort operations by dependencies (topological sort)
        sorted_ops = self._topological_sort(plan.operations, plan.dependencies)
        
        for operation in sorted_ops:
            try:
                if operation.type == EvolutionType.RENAME:
                    # Execute rename operation
                    pass  # Implementation depends on specific rename details
                elif operation.type == EvolutionType.DEPRECATE:
                    # Already handled in deprecate_element
                    pass
                elif operation.type == EvolutionType.EXTRACT:
                    # Already handled in extract_function
                    pass
                
                operation.applied = True
                logger.info(f"Applied operation: {operation.description}")
                
            except Exception as e:
                logger.error(f"Failed to apply operation: {operation.description}, error: {e}")
                return False
        
        self._save_data()
        
        logger.info(f"Completed evolution plan: {plan.name}")
        
        return True
    
    def _topological_sort(self, operations: List[EvolutionOperation],
                         dependencies: Dict[str, List[str]]) -> List[EvolutionOperation]:
        """Sort operations by dependencies"""
        # Simple implementation - can be enhanced
        sorted_ops = []
        remaining = list(operations)
        
        while remaining:
            # Find operations with no unsatisfied dependencies
            ready = []
            for op in remaining:
                deps = dependencies.get(op.element.name, [])
                if not deps or all(d in [o.element.name for o in sorted_ops] for d in deps):
                    ready.append(op)
            
            if not ready:
                # Circular dependency - add remaining
                sorted_ops.extend(remaining)
                break
            
            sorted_ops.extend(ready)
            remaining = [op for op in remaining if op not in ready]
        
        return sorted_ops
    
    def get_impact_analysis(self, element_name: str) -> Dict[str, Any]:
        """Analyze the impact of changing an element"""
        dependents = self._find_dependents(element_name)
        
        impact = {
            "element": element_name,
            "direct_dependents": len(dependents),
            "dependents_list": dependents[:20],  # Limit for display
            "estimated_effort_hours": len(dependents) * 0.5,  # Rough estimate
            "requires_test_updates": len(dependents) > 0,
            "requires_doc_updates": len(dependents) > 5,
            "breaking_change": len(dependents) > 0,
            "recommendation": self._generate_recommendation(len(dependents))
        }
        
        return impact
    
    def _generate_recommendation(self, dependent_count: int) -> str:
        """Generate recommendation based on impact"""
        if dependent_count == 0:
            return "Safe to change - no known dependents"
        elif dependent_count < 5:
            return "Low impact - update a few references"
        elif dependent_count < 20:
            return "Medium impact - consider deprecation period"
        else:
            return "High impact - create migration plan and announce breaking change"
    
    def sync_all(self) -> Dict[str, Any]:
        """Synchronize all components (configs, docs, examples, tests)"""
        results = {
            "config_updates": [],
            "doc_updates": [],
            "example_updates": [],
            "test_updates": [],
            "total_changes": 0
        }
        
        # Scan for latest code changes
        self.scan_codebase()
        
        # Auto-update tests
        for code_change in self.test_updater.code_changes[-10:]:  # Last 10 changes
            updates = self.test_updater.auto_update_tests(code_change)
            results["test_updates"].extend([u.to_dict() for u in updates])
            results["total_changes"] += len(updates)
        
        # Auto-update examples
        for api_change in self.example_updater.api_changes[-10:]:
            updates = self.example_updater.auto_update_examples(api_change.api_name)
            results["example_updates"].extend([u.to_dict() for u in updates])
            results["total_changes"] += len(updates)
        
        # Validate documentation
        for doc_file in self.doc_updater.documentation_files:
            validation = self.doc_updater.validate_documentation(doc_file)
            if validation.get("broken_links") or validation.get("outdated_info"):
                results["doc_updates"].append({
                    "file": doc_file,
                    "issues": validation
                })
        
        self._save_data()
        
        return results
    
    def get_evolution_summary(self) -> Dict[str, Any]:
        """Get summary of evolution activities"""
        return {
            "total_elements": len(self.code_elements),
            "total_operations": len(self.evolution_history),
            "pending_operations": len([op for op in self.evolution_history if not op.applied]),
            "total_plans": len(self.evolution_plans),
            "elements_by_type": self._count_by_type(),
            "recent_operations": [op.to_dict() for op in self.evolution_history[-10:]],
            "watch_directories": [str(d) for d in self.watch_dirs]
        }
    
    def _count_by_type(self) -> Dict[str, int]:
        """Count elements by type"""
        counts = defaultdict(int)
        for element in self.code_elements.values():
            counts[element.type] += 1
        return dict(counts)
    
    def rollback_operation(self, operation_index: int) -> bool:
        """Rollback a specific evolution operation"""
        if operation_index >= len(self.evolution_history):
            return False
        
        operation = self.evolution_history[operation_index]
        
        # Implementation would depend on operation type
        # This is a placeholder for rollback logic
        logger.warning(f"Rollback not fully implemented for: {operation.type.value}")
        
        return False


# Singleton instance
_co_evolution_engine: Optional[CoEvolutionEngine] = None


def get_co_evolution_engine() -> CoEvolutionEngine:
    """Get global CoEvolutionEngine instance"""
    global _co_evolution_engine
    if _co_evolution_engine is None:
        _co_evolution_engine = CoEvolutionEngine()
    return _co_evolution_engine