#!/usr/bin/env python3
"""
Module Generator - AI Development Framework
Generates complete Python modules with classes, functions, and documentation.

Part of the Level 3 Generation tools (generators/module_generator.py)

This module_generator.py provides:

1. Complete Module Generation - Generate entire Python modules with classes, functions, and constants
2. Multiple Module Types - Standard, package init, interface, utility, constants, types, exceptions, service, repository, controller, model, schema, test, CLI, config
3. Template System - Pre-defined templates for common patterns (class-based, function-based, dataclasses, enums, API routes, CRUD)
4. Package Generation - Generate complete packages with init.py and submodules
5. Import Management - Automatic import organization (stdlib, third-party, local)
6. Test Generation - Automatic unit test file creation
7. Iterative Refinement - Validation and improvement cycle
8. LLM-Powered Generation - Generate from natural language descriptions
9. py.typed Support - Optional PEP 561 type marker file
10. Export/Import - JSON serialization for specifications
11. Validation Integration - mypy and ruff validation built-in
12. Batch Package Generation - Generate entire packages from specifications

The module generator produces production-ready, well-structured Python modules with minimal effort, following best practices and PEP standards.

"""

import ast
import json
import shutil
from pathlib import Path
from typing import Dict, List, Set, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from ...shared.llm_client import LLMClient
from ...shared.state_manager import StateManager
from ...shared.logger import get_logger
from ...quality.validators.mypy_validator import MypyValidator
from ...quality.validators.ruff_validator import RuffValidator
from ..refiners.iterative_refiner import IterativeRefiner
from .class_generator import ClassGenerator, ClassSpec, ClassType
from .function_generator import FunctionGenerator, FunctionSpec, FunctionType
from .docstring_generator import DocstringGenerator, DocstringStyle

logger = get_logger(__name__)


# ============================================================
# ENUMS AND CONSTANTS
# ============================================================

class ModuleType(str, Enum):
    """Type of module to generate."""
    STANDARD = "standard"
    PACKAGE_INIT = "package_init"
    INTERFACE = "interface"
    ABSTRACT = "abstract"
    UTILITY = "utility"
    CONSTANTS = "constants"
    TYPES = "types"
    EXCEPTIONS = "exceptions"
    SERVICE = "service"
    REPOSITORY = "repository"
    CONTROLLER = "controller"
    MODEL = "model"
    SCHEMA = "schema"
    TEST = "test"
    CLI = "cli"
    CONFIG = "config"


class ModuleTemplate(str, Enum):
    """Pre-defined module templates."""
    EMPTY = "empty"
    CLASS_BASED = "class_based"
    FUNCTION_BASED = "function_based"
    MIXED = "mixed"
    DATA_CLASSES = "data_classes"
    ENUMS = "enums"
    API_ROUTES = "api_routes"
    CRUD = "crud"
    FACTORY = "factory"
    BUILDER = "builder"
    SINGLETON = "singleton"
    OBSERVER = "observer"
    STRATEGY = "strategy"


# ============================================================
# DATA MODELS
# ============================================================

@dataclass
class ConstantSpec:
    """Specification for a module constant."""
    name: str
    value: str
    type_hint: str = "Any"
    description: Optional[str] = None
    is_private: bool = False


@dataclass
class ImportSpec:
    """Specification for an import."""
    module: str
    names: List[str] = field(default_factory=list)
    alias: Optional[str] = None
    is_from: bool = False
    is_relative: bool = False
    relative_level: int = 0


@dataclass
class TypeAliasSpec:
    """Specification for a type alias."""
    name: str
    type_definition: str
    description: Optional[str] = None


@dataclass
class ModuleSpec:
    """Complete specification for a module."""
    name: str
    module_type: ModuleType = ModuleType.STANDARD
    template: ModuleTemplate = ModuleTemplate.MIXED
    description: str = ""
    docstring: Optional[str] = None
    imports: List[ImportSpec] = field(default_factory=list)
    constants: List[ConstantSpec] = field(default_factory=list)
    type_aliases: List[TypeAliasSpec] = field(default_factory=list)
    classes: List[ClassSpec] = field(default_factory=list)
    functions: List[FunctionSpec] = field(default_factory=list)
    exports: List[str] = field(default_factory=list)
    is_package: bool = False
    init_imports: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GeneratedModule:
    """Result of module generation."""
    module_spec: ModuleSpec
    code: str
    file_path: Optional[Path] = None
    validation_passed: bool = False
    mypy_errors: List[str] = field(default_factory=list)
    ruff_errors: List[str] = field(default_factory=list)
    generated_files: List[Path] = field(default_factory=list)
    iterations: int = 0
    generated_at: datetime = field(default_factory=datetime.now)


@dataclass
class ModuleGeneratorConfig:
    """Configuration for module generator."""
    use_llm: bool = True
    llm_model: str = "deepseek-chat"
    max_iterations: int = 5
    validate_mypy: bool = True
    validate_ruff: bool = True
    generate_docstring: bool = True
    generate_tests: bool = False
    docstring_style: DocstringStyle = DocstringStyle.GOOGLE
    include_type_hints: bool = True
    use_future_annotations: bool = True
    create_init_files: bool = True
    create_py_typed: bool = False
    line_length: int = 88
    indent_size: int = 4
    output_dir: Optional[Path] = None


# ============================================================
# CODE GENERATORS
# ============================================================

class ModuleCodeGenerator:
    """Generate Python module code from specifications."""
    
    def __init__(self, config: ModuleGeneratorConfig):
        self.config = config
        self.indent = " " * config.indent_size
        self.class_generator = ClassGenerator()
        self.function_generator = FunctionGenerator()
    
    def generate(self, spec: ModuleSpec) -> str:
        """Generate complete module code."""
        lines = []
        
        # Shebang for CLI modules
        if spec.module_type == ModuleType.CLI:
            lines.append("#!/usr/bin/env python3")
            lines.append("")
        
        # Module docstring
        lines.extend(self._generate_module_docstring(spec))
        
        # Future imports
        if self.config.use_future_annotations:
            lines.append("from __future__ import annotations")
            lines.append("")
        
        # Standard imports
        lines.extend(self._generate_imports(spec))
        
        # Constants
        if spec.constants:
            lines.extend(self._generate_constants(spec.constants))
        
        # Type aliases
        if spec.type_aliases:
            lines.extend(self._generate_type_aliases(spec.type_aliases))
        
        # Classes
        if spec.classes:
            for class_spec in spec.classes:
                class_spec.module_path = spec.name
                class_code = self.class_generator.code_generator.generate(class_spec)
                # Remove imports from class code
                code_lines = class_code.split("\n")
                class_start = 0
                for i, line in enumerate(code_lines):
                    if line.startswith("class "):
                        class_start = i
                        break
                lines.extend(code_lines[class_start:])
                lines.append("")
        
        # Functions
        if spec.functions:
            for func_spec in spec.functions:
                func_spec.module_path = spec.name
                func_code = self.function_generator.code_generator.generate(func_spec)
                # Remove imports from function code
                code_lines = func_code.split("\n")
                func_start = 0
                for i, line in enumerate(code_lines):
                    if line.startswith("def ") or line.startswith("async def ") or line.startswith("@"):
                        func_start = i
                        break
                lines.extend(code_lines[func_start:])
                lines.append("")
        
        # Exports
        if spec.exports:
            lines.append(f"__all__ = {spec.exports}")
        
        return "\n".join(lines).rstrip() + "\n"
    
    def _generate_module_docstring(self, spec: ModuleSpec) -> List[str]:
        """Generate module docstring."""
        lines = []
        lines.append('"""')
        
        if spec.docstring:
            lines.append(spec.docstring)
        else:
            lines.append(f"{spec.name} module.")
            lines.append("")
            if spec.description:
                lines.append(spec.description)
                lines.append("")
            
            if spec.module_type == ModuleType.CLI:
                lines.append("Command-line interface module.")
            elif spec.module_type == ModuleType.SERVICE:
                lines.append("Service layer module.")
            elif spec.module_type == ModuleType.MODEL:
                lines.append("Data model definitions.")
        
        lines.append('"""')
        lines.append("")
        return lines
    
    def _generate_imports(self, spec: ModuleSpec) -> List[str]:
        """Generate import statements."""
        lines = []
        
        # Group imports
        stdlib_imports = []
        third_party_imports = []
        local_imports = []
        
        for imp in spec.imports:
            if imp.is_relative or imp.module.startswith('.'):
                local_imports.append(imp)
            elif imp.module in self._get_stdlib_modules():
                stdlib_imports.append(imp)
            else:
                third_party_imports.append(imp)
        
        # Add typing imports
        if self._needs_typing_imports(spec):
            stdlib_imports.append(ImportSpec(module="typing", names=["Optional", "List", "Dict", "Any", "Union"]))
        
        # Generate each group
        for group in [stdlib_imports, third_party_imports, local_imports]:
            for imp in group:
                if imp.is_from:
                    if imp.names:
                        names_str = ", ".join(imp.names)
                        if len(names_str) > 80:
                            lines.append(f"from {imp.module} import (")
                            for name in imp.names:
                                lines.append(f"    {name},")
                            lines.append(")")
                        else:
                            lines.append(f"from {imp.module} import {names_str}")
                    else:
                        lines.append(f"from {imp.module} import *")
                else:
                    if imp.alias:
                        lines.append(f"import {imp.module} as {imp.alias}")
                    else:
                        lines.append(f"import {imp.module}")
            
            if group:
                lines.append("")
        
        return lines
    
    def _get_stdlib_modules(self) -> Set[str]:
        """Get set of standard library modules."""
        return {
            'abc', 'argparse', 'ast', 'asyncio', 'base64', 'collections', 'contextlib',
            'copy', 'dataclasses', 'datetime', 'decimal', 'enum', 'functools', 'hashlib',
            'inspect', 'io', 'itertools', 'json', 'logging', 'math', 'os', 'pathlib',
            'pickle', 'random', 're', 'shutil', 'signal', 'socket', 'sqlite3', 'string',
            'subprocess', 'sys', 'tempfile', 'threading', 'time', 'traceback', 'typing',
            'unittest', 'urllib', 'uuid', 'warnings', 'weakref', 'xml', 'yaml', 'zipfile'
        }
    
    def _needs_typing_imports(self, spec: ModuleSpec) -> bool:
        """Check if typing imports are needed."""
        # Check constants for type hints
        for const in spec.constants:
            if any(t in const.type_hint for t in ['Optional', 'List', 'Dict', 'Union']):
                return True
        
        # Check classes
        for cls in spec.classes:
            for field in cls.fields:
                if any(t in field.type_hint for t in ['Optional', 'List', 'Dict', 'Union']):
                    return True
        
        # Check functions
        for func in spec.functions:
            for param in func.parameters:
                if any(t in param.type_hint for t in ['Optional', 'List', 'Dict', 'Union']):
                    return True
            if any(t in func.return_spec.type_hint for t in ['Optional', 'List', 'Dict', 'Union']):
                return True
        
        return False
    
    def _generate_constants(self, constants: List[ConstantSpec]) -> List[str]:
        """Generate constant definitions."""
        lines = []
        
        for const in constants:
            name = f"_{const.name}" if const.is_private else const.name
            
            if self.config.include_type_hints:
                lines.append(f"{name}: {const.type_hint} = {const.value}")
            else:
                lines.append(f"{name} = {const.value}")
            
            if const.description:
                lines.append(f'"""{const.description}"""')
        
        if constants:
            lines.append("")
        
        return lines
    
    def _generate_type_aliases(self, aliases: List[TypeAliasSpec]) -> List[str]:
        """Generate type alias definitions."""
        lines = []
        
        for alias in aliases:
            lines.append(f"{alias.name} = {alias.type_definition}")
            
            if alias.description:
                lines.append(f'"""{alias.description}"""')
        
        if aliases:
            lines.append("")
        
        return lines
    
    def generate_init_file(self, spec: ModuleSpec) -> str:
        """Generate __init__.py file."""
        lines = []
        
        lines.append('"""')
        lines.append(f"{spec.name} package.")
        if spec.description:
            lines.append("")
            lines.append(spec.description)
        lines.append('"""')
        lines.append("")
        
        # Add imports
        for imp in spec.init_imports:
            lines.append(imp)
        
        if spec.init_imports:
            lines.append("")
        
        # Add exports
        if spec.exports:
            lines.append(f"__all__ = {spec.exports}")
        
        return "\n".join(lines)


# ============================================================
# MAIN MODULE GENERATOR
# ============================================================

class ModuleGenerator:
    """
    Generates complete Python modules from specifications.
    
    Features:
    - Generate full modules with classes, functions, constants
    - Multiple module types and templates
    - Package structure generation
    - Import management
    - Automatic __init__.py generation
    - Test file generation
    - Iterative refinement with validation
    - LLM-powered generation from descriptions
    - Batch package generation
    """
    
    def __init__(self, config: Optional[ModuleGeneratorConfig] = None):
        self.config = config or ModuleGeneratorConfig()
        self.code_generator = ModuleCodeGenerator(self.config)
        self.llm = LLMClient() if self.config.use_llm else None
        self.state = StateManager(Path(".ai_state") / "module_generator.json")
        
        self.mypy_validator = MypyValidator() if self.config.validate_mypy else None
        self.ruff_validator = RuffValidator() if self.config.validate_ruff else None
        self.refiner = IterativeRefiner(self.llm) if self.llm else None
        
        self.class_generator = ClassGenerator()
        self.function_generator = FunctionGenerator()
        
        logger.info("ModuleGenerator initialized")
    
    # ============================================================
    # GENERATION
    # ============================================================
    
    def generate(self, spec: ModuleSpec, output_dir: Optional[Path] = None) -> GeneratedModule:
        """
        Generate a module from specification.
        
        Args:
            spec: Module specification
            output_dir: Optional output directory
        """
        logger.info(f"Generating module: {spec.name}")
        
        output_dir = output_dir or self.config.output_dir or Path.cwd()
        module_path = self._get_module_path(spec, output_dir)
        
        # Generate initial code
        code = self.code_generator.generate(spec)
        
        # Iterative refinement
        iteration = 0
        mypy_errors = []
        ruff_errors = []
        
        if self.refiner and self.config.max_iterations > 1:
            for iteration in range(1, self.config.max_iterations):
                if self.mypy_validator:
                    mypy_errors = self.mypy_validator.validate_string(code)
                if self.ruff_validator:
                    ruff_errors = self.ruff_validator.validate_string(code)
                
                if not mypy_errors and not ruff_errors:
                    logger.info(f"Validation passed at iteration {iteration}")
                    break
                
                logger.info(f"Iteration {iteration}: {len(mypy_errors)} mypy, {len(ruff_errors)} ruff errors")
                
                code = self.refiner.refine_module(
                    code=code,
                    spec=spec,
                    mypy_errors=mypy_errors,
                    ruff_errors=ruff_errors
                )
        
        # Final validation
        if self.mypy_validator:
            mypy_errors = self.mypy_validator.validate_string(code)
        if self.ruff_validator:
            ruff_errors = self.ruff_validator.validate_string(code)
        
        # Write files
        generated_files = []
        
        module_path.parent.mkdir(parents=True, exist_ok=True)
        module_path.write_text(code)
        generated_files.append(module_path)
        
        # Create __init__.py if it's a package
        if spec.is_package and self.config.create_init_files:
            init_path = module_path.parent / "__init__.py"
            if not init_path.exists():
                init_code = self.code_generator.generate_init_file(spec)
                init_path.write_text(init_code)
                generated_files.append(init_path)
        
        # Create py.typed if configured
        if self.config.create_py_typed:
            py_typed_path = module_path.parent / "py.typed"
            if not py_typed_path.exists():
                py_typed_path.touch()
                generated_files.append(py_typed_path)
        
        # Generate test file if configured
        if self.config.generate_tests:
            test_path = self._generate_test_file(spec, output_dir)
            if test_path:
                generated_files.append(test_path)
        
        result = GeneratedModule(
            module_spec=spec,
            code=code,
            file_path=module_path,
            validation_passed=not (mypy_errors or ruff_errors),
            mypy_errors=mypy_errors,
            ruff_errors=ruff_errors,
            generated_files=generated_files,
            iterations=iteration
        )
        
        self._save_result(result)
        
        logger.info(f"Generated module {spec.name} with {len(generated_files)} files")
        return result
    
    def generate_from_description(self,
                                   description: str,
                                   module_name: str,
                                   output_dir: Optional[Path] = None) -> GeneratedModule:
        """
        Generate a module from natural language description.
        
        Args:
            description: Natural language description
            module_name: Name of the module
            output_dir: Optional output directory
        """
        if not self.llm:
            raise ValueError("LLM is required for description-based generation")
        
        logger.info(f"Generating module '{module_name}' from description")
        
        spec = self._parse_description(description, module_name)
        
        return self.generate(spec, output_dir)
    
    def _parse_description(self, description: str, module_name: str) -> ModuleSpec:
        """Parse natural language description into ModuleSpec."""
        prompt = f"""
        Parse this module description into a structured specification:
        
        Module Name: {module_name}
        Description: {description}
        
        Return a JSON object with:
        - module_type: one of {[t.value for t in ModuleType]}
        - template: one of {[t.value for t in ModuleTemplate]}
        - description: brief description
        - docstring: detailed module docstring
        - classes: list of class specifications with name, class_type, description, fields, methods
        - functions: list of function specifications with name, parameters, return_type, description
        - constants: list of constants with name, value, type_hint
        - imports: list of required imports
        - exports: list of public exports for __all__
        
        Output only valid JSON.
        """
        
        response = self.llm.complete_json(prompt)
        
        # Build ModuleSpec
        spec = ModuleSpec(
            name=module_name,
            module_type=ModuleType(response.get('module_type', 'standard')),
            template=ModuleTemplate(response.get('template', 'mixed')),
            description=response.get('description', ''),
            docstring=response.get('docstring'),
            exports=response.get('exports', [])
        )
        
        # Parse imports
        for imp_data in response.get('imports', []):
            imp = ImportSpec(
                module=imp_data['module'],
                names=imp_data.get('names', []),
                is_from=imp_data.get('is_from', False)
            )
            spec.imports.append(imp)
        
        # Parse constants
        for const_data in response.get('constants', []):
            const = ConstantSpec(
                name=const_data['name'],
                value=const_data['value'],
                type_hint=const_data.get('type_hint', 'Any'),
                description=const_data.get('description')
            )
            spec.constants.append(const)
        
        # Parse classes
        for cls_data in response.get('classes', []):
            cls = ClassSpec(
                name=cls_data['name'],
                class_type=ClassType(cls_data.get('class_type', 'regular')),
                description=cls_data.get('description', '')
            )
            spec.classes.append(cls)
        
        # Parse functions
        for func_data in response.get('functions', []):
            func = FunctionSpec(
                name=func_data['name'],
                function_type=FunctionType(func_data.get('function_type', 'function')),
                description=func_data.get('description', ''),
                return_spec=ReturnSpec(type_hint=func_data.get('return_type', 'None'))
            )
            spec.functions.append(func)
        
        return spec
    
    def _get_module_path(self, spec: ModuleSpec, output_dir: Path) -> Path:
        """Get the file path for a module."""
        parts = spec.name.split('.')
        
        if spec.is_package:
            path = output_dir
            for part in parts:
                path = path / part
            path.mkdir(parents=True, exist_ok=True)
            return path / "__init__.py"
        else:
            if len(parts) > 1:
                path = output_dir
                for part in parts[:-1]:
                    path = path / part
                path.mkdir(parents=True, exist_ok=True)
                return path / f"{parts[-1]}.py"
            else:
                return output_dir / f"{spec.name}.py"
    
    def _generate_test_file(self, spec: ModuleSpec, output_dir: Path) -> Optional[Path]:
        """Generate test file for module."""
        test_dir = output_dir / "tests"
        test_dir.mkdir(parents=True, exist_ok=True)
        
        test_path = test_dir / f"test_{spec.name.replace('.', '_')}.py"
        
        lines = [
            '"""',
            f'Unit tests for {spec.name} module.',
            '"""',
            '',
            'import pytest',
            f'from {spec.name} import *',
            '',
            '',
        ]
        
        # Generate test class
        class_name = f"Test{spec.name.replace('.', '_').title().replace('_', '')}"
        lines.append(f"class {class_name}:")
        lines.append(f'    """Tests for {spec.name} module."""')
        lines.append("")
        
        # Test imports
        lines.append("    def test_imports(self):")
        lines.append('        """Test that all imports work."""')
        lines.append("        assert True")
        lines.append("")
        
        # Test constants
        if spec.constants:
            lines.append("    def test_constants(self):")
            lines.append('        """Test module constants."""')
            for const in spec.constants:
                if not const.is_private:
                    lines.append(f"        assert {const.name} is not None")
            lines.append("")
        
        # Test functions
        for func in spec.functions:
            if not func.name.startswith('_'):
                lines.append(f"    def test_{func.name}(self):")
                lines.append(f'        """Test {func.name} function."""')
                lines.append(f"        # TODO: Implement test for {func.name}")
                lines.append("        pass")
                lines.append("")
        
        # Test classes
        for cls in spec.classes:
            if not cls.name.startswith('_'):
                lines.append(f"    def test_{cls.name}(self):")
                lines.append(f'        """Test {cls.name} class."""')
                lines.append(f"        obj = {cls.name}()")
                lines.append(f"        assert obj is not None")
                lines.append("")
        
        test_code = "\n".join(lines)
        test_path.write_text(test_code)
        
        return test_path
    
    # ============================================================
    # PACKAGE GENERATION
    # ============================================================
    
    def generate_package(self,
                          package_name: str,
                          modules: List[ModuleSpec],
                          output_dir: Optional[Path] = None) -> List[GeneratedModule]:
        """Generate a complete package with multiple modules."""
        output_dir = output_dir or self.config.output_dir or Path.cwd()
        package_dir = output_dir / package_name.replace('.', '/')
        
        results = []
        
        # Create package __init__.py
        init_spec = ModuleSpec(
            name=package_name,
            module_type=ModuleType.PACKAGE_INIT,
            is_package=True,
            description=f"{package_name} package",
            exports=self._collect_exports(modules),
            init_imports=self._generate_init_imports(modules)
        )
        
        init_result = self.generate(init_spec, package_dir.parent)
        results.append(init_result)
        
        # Generate submodules
        for module_spec in modules:
            module_spec.name = f"{package_name}.{module_spec.name}"
            result = self.generate(module_spec, package_dir.parent)
            results.append(result)
        
        logger.info(f"Generated package {package_name} with {len(results)} modules")
        return results
    
    def _collect_exports(self, modules: List[ModuleSpec]) -> List[str]:
        """Collect exports from all modules."""
        exports = []
        for module in modules:
            exports.extend(module.exports)
        return list(set(exports))
    
    def _generate_init_imports(self, modules: List[ModuleSpec]) -> List[str]:
        """Generate import statements for __init__.py."""
        imports = []
        for module in modules:
            module_base = module.name.split('.')[-1]
            if module.exports:
                exports_str = ", ".join(module.exports)
                imports.append(f"from .{module_base} import {exports_str}")
        return imports
    
    # ============================================================
    # TEMPLATES
    # ============================================================
    
    def create_template_spec(self, template: ModuleTemplate, name: str) -> ModuleSpec:
        """Create a module specification from a template."""
        
        if template == ModuleTemplate.CLASS_BASED:
            return self._create_class_based_spec(name)
        elif template == ModuleTemplate.FUNCTION_BASED:
            return self._create_function_based_spec(name)
        elif template == ModuleTemplate.DATA_CLASSES:
            return self._create_dataclasses_spec(name)
        elif template == ModuleTemplate.ENUMS:
            return self._create_enums_spec(name)
        elif template == ModuleTemplate.API_ROUTES:
            return self._create_api_routes_spec(name)
        elif template == ModuleTemplate.CRUD:
            return self._create_crud_spec(name)
        else:
            return ModuleSpec(name=name, template=template)
    
    def _create_class_based_spec(self, name: str) -> ModuleSpec:
        """Create a class-based module specification."""
        spec = ModuleSpec(
            name=name,
            template=ModuleTemplate.CLASS_BASED,
            description=f"{name} module - class-based implementation."
        )
        
        # Add a main service class
        main_class = ClassSpec(
            name=name.title().replace('_', ''),
            class_type=ClassType.REGULAR,
            description=f"Main {name} service class."
        )
        spec.classes.append(main_class)
        
        return spec
    
    def _create_function_based_spec(self, name: str) -> ModuleSpec:
        """Create a function-based module specification."""
        spec = ModuleSpec(
            name=name,
            template=ModuleTemplate.FUNCTION_BASED,
            description=f"{name} module - functional implementation."
        )
        
        # Add utility functions
        for func_name in [f"process_{name}", f"validate_{name}", f"transform_{name}"]:
            func = FunctionSpec(
                name=func_name,
                description=f"{func_name.replace('_', ' ').title()}.",
                return_spec=ReturnSpec(type_hint="Any")
            )
            spec.functions.append(func)
        
        return spec
    
    def _create_dataclasses_spec(self, name: str) -> ModuleSpec:
        """Create a dataclasses module specification."""
        spec = ModuleSpec(
            name=name,
            template=ModuleTemplate.DATA_CLASSES,
            description=f"{name} data models.",
            imports=[ImportSpec(module="dataclasses", names=["dataclass", "field"])]
        )
        
        # Add a main dataclass
        main_class = ClassSpec(
            name=name.title().replace('_', ''),
            class_type=ClassType.DATACLASS,
            description=f"{name} data model."
        )
        spec.classes.append(main_class)
        
        return spec
    
    def _create_enums_spec(self, name: str) -> ModuleSpec:
        """Create an enums module specification."""
        spec = ModuleSpec(
            name=name,
            template=ModuleTemplate.ENUMS,
            description=f"{name} enumeration definitions.",
            imports=[ImportSpec(module="enum", names=["Enum"])]
        )
        
        # Add a main enum
        main_enum = ClassSpec(
            name=name.title().replace('_', ''),
            class_type=ClassType.ENUM,
            description=f"{name} enumeration."
        )
        spec.classes.append(main_enum)
        
        return spec
    
    def _create_api_routes_spec(self, name: str) -> ModuleSpec:
        """Create an API routes module specification."""
        spec = ModuleSpec(
            name=name,
            template=ModuleTemplate.API_ROUTES,
            description=f"{name} API routes.",
            imports=[
                ImportSpec(module="fastapi", names=["APIRouter", "HTTPException"]),
                ImportSpec(module="typing", names=["Optional", "List"])
            ]
        )
        
        # Add router constant
        spec.constants.append(ConstantSpec(
            name="router",
            value="APIRouter()",
            type_hint="APIRouter"
        ))
        
        # Add route functions
        for method in ["get", "post", "put", "delete"]:
            func = FunctionSpec(
                name=f"{method}_{name}",
                function_type=FunctionType.ASYNC_FUNCTION,
                description=f"{method.upper()} endpoint for {name}.",
                decorators=[DecoratorSpec(name=f'router.{method}("/{name}")')]
            )
            spec.functions.append(func)
        
        return spec
    
    def _create_crud_spec(self, name: str) -> ModuleSpec:
        """Create a CRUD module specification."""
        spec = ModuleSpec(
            name=name,
            template=ModuleTemplate.CRUD,
            description=f"{name} CRUD operations."
        )
        
        # Add CRUD functions
        functions = self.function_generator.create_crud_functions(name, [
            ("id", "str"),
            ("name", "str"),
            ("created_at", "datetime"),
            ("updated_at", "datetime")
        ])
        spec.functions.extend(functions)
        
        return spec
    
    # ============================================================
    # VALIDATION AND EXPORT
    # ============================================================
    
    def validate_spec(self, spec: ModuleSpec) -> List[str]:
        """Validate a module specification."""
        errors = []
        
        if not spec.name:
            errors.append("Module name is required")
        elif not spec.name.islower() or not spec.name.replace('_', '').isalnum():
            errors.append("Module name should be snake_case (PEP 8)")
        
        # Validate classes
        for cls in spec.classes:
            if not cls.name[0].isupper():
                errors.append(f"Class '{cls.name}' should start with uppercase (PEP 8)")
        
        # Validate functions
        for func in spec.functions:
            if not func.name.islower():
                errors.append(f"Function '{func.name}' should be snake_case (PEP 8)")
        
        return errors
    
    def _save_result(self, result: GeneratedModule):
        """Save generation result to state."""
        history = self.state.get('history', [])
        history.append({
            'module_name': result.module_spec.name,
            'file_path': str(result.file_path) if result.file_path else None,
            'validation_passed': result.validation_passed,
            'iterations': result.iterations,
            'generated_at': result.generated_at.isoformat(),
            'mypy_error_count': len(result.mypy_errors),
            'ruff_error_count': len(result.ruff_errors),
            'generated_files': [str(f) for f in result.generated_files]
        })
        
        if len(history) > 100:
            history = history[-100:]
        
        self.state.set('history', history)
        self.state.save()
    
    def export_spec(self, spec: ModuleSpec, output_path: Optional[Path] = None) -> str:
        """Export module specification as JSON."""
        data = {
            'name': spec.name,
            'module_type': spec.module_type.value,
            'template': spec.template.value,
            'description': spec.description,
            'docstring': spec.docstring,
            'is_package': spec.is_package,
            'exports': spec.exports,
            'constants': [
                {
                    'name': c.name,
                    'value': c.value,
                    'type_hint': c.type_hint,
                    'description': c.description,
                    'is_private': c.is_private
                }
                for c in spec.constants
            ],
            'imports': [
                {
                    'module': i.module,
                    'names': i.names,
                    'alias': i.alias,
                    'is_from': i.is_from
                }
                for i in spec.imports
            ],
            'classes': len(spec.classes),
            'functions': len(spec.functions),
            'metadata': spec.metadata
        }
        
        content = json.dumps(data, indent=2)
        
        if output_path:
            output_path.write_text(content)
        
        return content
    
    def import_spec(self, input_path: Path) -> ModuleSpec:
        """Import module specification from JSON."""
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        spec = ModuleSpec(
            name=data['name'],
            module_type=ModuleType(data.get('module_type', 'standard')),
            template=ModuleTemplate(data.get('template', 'mixed')),
            description=data.get('description', ''),
            docstring=data.get('docstring'),
            is_package=data.get('is_package', False),
            exports=data.get('exports', []),
            metadata=data.get('metadata', {})
        )
        
        for const_data in data.get('constants', []):
            const = ConstantSpec(
                name=const_data['name'],
                value=const_data['value'],
                type_hint=const_data.get('type_hint', 'Any'),
                description=const_data.get('description'),
                is_private=const_data.get('is_private', False)
            )
            spec.constants.append(const)
        
        for imp_data in data.get('imports', []):
            imp = ImportSpec(
                module=imp_data['module'],
                names=imp_data.get('names', []),
                alias=imp_data.get('alias'),
                is_from=imp_data.get('is_from', False)
            )
            spec.imports.append(imp)
        
        return spec
    
    def close(self):
        """Clean up resources."""
        self.state.save()
        logger.info("ModuleGenerator closed")


# ============================================================
# CLI ENTRY POINT
# ============================================================

def main():
    """CLI entry point for module generator."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate Python modules from specifications")
    parser.add_argument("--name", type=str, required=True, help="Module name")
    parser.add_argument("--type", choices=[t.value for t in ModuleType],
                       default=ModuleType.STANDARD.value, help="Module type")
    parser.add_argument("--template", choices=[t.value for t in ModuleTemplate],
                       default=ModuleTemplate.MIXED.value, help="Module template")
    parser.add_argument("--description", type=str, help="Module description")
    parser.add_argument("--spec", type=Path, help="Import specification from JSON")
    parser.add_argument("--output", "-o", type=Path, help="Output directory")
    parser.add_argument("--package", action="store_true", help="Generate as package")
    parser.add_argument("--no-llm", action="store_true", help="Disable LLM assistance")
    parser.add_argument("--generate-tests", action="store_true", help="Generate unit tests")
    parser.add_argument("--export-spec", type=Path, help="Export specification to JSON")
    
    args = parser.parse_args()
    
    config = ModuleGeneratorConfig(
        use_llm=not args.no_llm,
        generate_tests=args.generate_tests,
        output_dir=args.output
    )
    
    generator = ModuleGenerator(config)
    
    if args.spec:
        spec = generator.import_spec(args.spec)
        spec.name = args.name
    else:
        spec = generator.create_template_spec(ModuleTemplate(args.template), args.name)
        spec.module_type = ModuleType(args.type)
        spec.description = args.description or ""
        spec.is_package = args.package
    
    if args.export_spec:
        generator.export_spec(spec, args.export_spec)
        print(f"Specification exported to {args.export_spec}")
    
    result = generator.generate(spec, args.output)
    
    if args.output:
        print(f"Module generated at {result.file_path}")
        if len(result.generated_files) > 1:
            print(f"Additional files generated:")
            for f in result.generated_files[1:]:
                print(f"  - {f}")
    else:
        print(result.code)
    
    if not result.validation_passed:
        print("\nValidation issues:")
        for error in result.mypy_errors[:5]:
            print(f"  [mypy] {error}")
        for error in result.ruff_errors[:5]:
            print(f"  [ruff] {error}")
    
    generator.close()


if __name__ == "__main__":
    main()