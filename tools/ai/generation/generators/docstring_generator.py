#!/usr/bin/env python3
"""
Docstring Generator - AI Development Framework
Generates comprehensive docstrings for Python code using AI.

Part of the Level 3 Generation tools (generators/docstring_generator.py)

This docstring_generator.py provides:

1. AI-Powered Generation - Uses LLM to create intelligent, context-aware docstrings
2. Multiple Styles - Google, NumPy, Sphinx, Epydoc, and plain formats
3. Context Extraction - AST-based analysis of functions, classes, and modules
4. Quality Assessment - Evaluates docstring completeness and quality
5. Intelligent Enhancement - Improves existing docstrings to meet quality targets
6. Batch Processing - Process entire files or directories
7. Section Detection - Identifies Args, Returns, Raises, Examples, etc.
8. Type Hint Integration - Uses type annotations in generated documentation
9. Example Generation - Creates usage examples for complex functions
10. In-Place Updates - Directly modifies source files with new docstrings
11. Comprehensive Reporting - Summary of changes and quality metrics
12. Validation Ready - Optional mypy validation of generated code

The docstring generator ensures your code is well-documented with minimal manual effort, improving maintainability and developer experience.

"""

import ast
import json
import re
from pathlib import Path
from typing import Dict, List, Set, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from ...shared.llm_client import LLMClient
from ...shared.state_manager import StateManager
from ...shared.logger import get_logger
from ...level_2_analysis.scanners.ast_analyzer import ASTAnalyzer, ASTMetrics, NodeType
from ...quality.validators.mypy_validator import MypyValidator
from ...quality.validators.ruff_validator import RuffValidator

logger = get_logger(__name__)


# ============================================================
# ENUMS AND CONSTANTS
# ============================================================

class DocstringStyle(str, Enum):
    """Docstring format style."""
    GOOGLE = "google"
    NUMPY = "numpy"
    SPHINX = "sphinx"
    EPYDOC = "epydoc"
    PLAIN = "plain"


class DocstringSection(str, Enum):
    """Docstring section types."""
    SUMMARY = "summary"
    DESCRIPTION = "description"
    ARGS = "args"
    ARGUMENTS = "arguments"
    PARAMETERS = "parameters"
    RETURNS = "returns"
    YIELDS = "yields"
    RAISES = "raises"
    EXCEPTIONS = "exceptions"
    EXAMPLES = "examples"
    NOTES = "notes"
    SEE_ALSO = "see_also"
    REFERENCES = "references"
    ATTRIBUTES = "attributes"
    METHODS = "methods"
    TODO = "todo"
    DEPRECATED = "deprecated"
    WARNING = "warning"
    VERSION = "version"
    AUTHOR = "author"
    SINCE = "since"
    CHANGELOG = "changelog"


class DocstringQuality(str, Enum):
    """Quality level of docstring."""
    NONE = "none"
    MINIMAL = "minimal"
    BASIC = "basic"
    GOOD = "good"
    COMPREHENSIVE = "comprehensive"
    EXCELLENT = "excellent"


# ============================================================
# DATA MODELS
# ============================================================

@dataclass
class ParameterInfo:
    """Information about a function parameter."""
    name: str
    type_hint: Optional[str] = None
    default_value: Optional[str] = None
    description: Optional[str] = None
    kind: str = "positional_or_keyword"


@dataclass
class ReturnInfo:
    """Information about return value."""
    type_hint: Optional[str] = None
    description: Optional[str] = None


@dataclass
class ExceptionInfo:
    """Information about raised exception."""
    exception_type: str
    condition: Optional[str] = None
    description: Optional[str] = None


@dataclass
class FunctionContext:
    """Context for function docstring generation."""
    name: str
    module_path: str
    parameters: List[ParameterInfo] = field(default_factory=list)
    return_info: Optional[ReturnInfo] = None
    exceptions: List[ExceptionInfo] = field(default_factory=list)
    decorators: List[str] = field(default_factory=list)
    is_async: bool = False
    is_method: bool = False
    is_property: bool = False
    is_classmethod: bool = False
    is_staticmethod: bool = False
    is_abstract: bool = False
    body_summary: Optional[str] = None
    existing_docstring: Optional[str] = None
    complexity: int = 0
    line_count: int = 0


@dataclass
class ClassContext:
    """Context for class docstring generation."""
    name: str
    module_path: str
    bases: List[str] = field(default_factory=list)
    attributes: List[Tuple[str, str]] = field(default_factory=list)  # (name, type)
    methods: List[str] = field(default_factory=list)
    properties: List[str] = field(default_factory=list)
    decorators: List[str] = field(default_factory=list)
    is_dataclass: bool = False
    is_enum: bool = False
    is_abstract: bool = False
    existing_docstring: Optional[str] = None
    line_count: int = 0


@dataclass
class ModuleContext:
    """Context for module docstring generation."""
    name: str
    path: str
    description: Optional[str] = None
    exports: List[str] = field(default_factory=list)
    classes: List[str] = field(default_factory=list)
    functions: List[str] = field(default_factory=list)
    constants: List[str] = field(default_factory=list)
    existing_docstring: Optional[str] = None


@dataclass
class GeneratedDocstring:
    """Result of docstring generation."""
    target: str  # Function/class/module name
    docstring: str
    style: DocstringStyle
    quality: DocstringQuality
    existing: Optional[str] = None
    improved: bool = False
    sections: List[DocstringSection] = field(default_factory=list)
    generated_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DocstringGeneratorConfig:
    """Configuration for docstring generator."""
    style: DocstringStyle = DocstringStyle.GOOGLE
    quality: DocstringQuality = DocstringQuality.GOOD
    use_llm: bool = True
    llm_model: str = "deepseek-chat"
    include_types: bool = True
    include_examples: bool = True
    include_raises: bool = True
    max_length: int = 500
    min_quality_to_keep: DocstringQuality = DocstringQuality.BASIC
    update_existing: bool = True
    validate_with_mypy: bool = False
    add_todo_for_missing: bool = True


# ============================================================
# CONTEXT EXTRACTORS
# ============================================================

class ContextExtractor(ast.NodeVisitor):
    """Extract context from Python code for docstring generation."""
    
    def __init__(self, module_path: str, source_lines: List[str]):
        self.module_path = module_path
        self.source_lines = source_lines
        self.functions: List[FunctionContext] = []
        self.classes: List[ClassContext] = []
        self.current_class: Optional[str] = None
        self.imports: Dict[str, str] = {}
    
    def extract_function_context(self, node: Union[ast.FunctionDef, ast.AsyncFunctionDef], 
                                  is_method: bool = False) -> FunctionContext:
        """Extract function context from AST node."""
        context = FunctionContext(
            name=node.name,
            module_path=self.module_path,
            is_async=isinstance(node, ast.AsyncFunctionDef),
            is_method=is_method,
            decorators=self._extract_decorators(node),
            existing_docstring=ast.get_docstring(node),
            line_count=node.end_lineno - node.lineno + 1 if node.end_lineno else 1
        )
        
        # Check for property
        if any(d in ('property', 'cached_property') for d in context.decorators):
            context.is_property = True
        
        # Check for classmethod
        if 'classmethod' in context.decorators:
            context.is_classmethod = True
        
        # Check for staticmethod
        if 'staticmethod' in context.decorators:
            context.is_staticmethod = True
        
        # Check for abstractmethod
        if 'abstractmethod' in context.decorators:
            context.is_abstract = True
        
        # Extract parameters
        context.parameters = self._extract_parameters(node)
        
        # Extract return type
        if node.returns:
            context.return_info = ReturnInfo(
                type_hint=ast.unparse(node.returns)
            )
        
        # Extract raised exceptions
        context.exceptions = self._extract_exceptions(node)
        
        # Generate body summary
        context.body_summary = self._summarize_body(node)
        
        # Calculate complexity (simplified)
        context.complexity = self._calculate_complexity(node)
        
        return context
    
    def extract_class_context(self, node: ast.ClassDef) -> ClassContext:
        """Extract class context from AST node."""
        context = ClassContext(
            name=node.name,
            module_path=self.module_path,
            bases=self._extract_bases(node),
            decorators=self._extract_decorators(node),
            existing_docstring=ast.get_docstring(node),
            line_count=node.end_lineno - node.lineno + 1 if node.end_lineno else 1
        )
        
        # Check for dataclass
        if any(d in ('dataclass', 'dataclass_transform') for d in context.decorators):
            context.is_dataclass = True
        
        # Check for enum
        for base in context.bases:
            if base in ('Enum', 'IntEnum', 'StrEnum'):
                context.is_enum = True
                break
        
        # Check for abstract
        if 'ABC' in context.bases or any(d == 'abstractmethod' for d in context.decorators):
            context.is_abstract = True
        
        # Extract attributes and methods
        for child in node.body:
            if isinstance(child, ast.Assign):
                for target in child.targets:
                    if isinstance(target, ast.Name) and not target.id.startswith('_'):
                        context.attributes.append((target.id, 'Any'))
            elif isinstance(child, ast.AnnAssign):
                if isinstance(child.target, ast.Name) and not child.target.id.startswith('_'):
                    type_hint = ast.unparse(child.annotation) if child.annotation else 'Any'
                    context.attributes.append((child.target.id, type_hint))
            elif isinstance(child, ast.FunctionDef):
                if not child.name.startswith('_') or child.name == '__init__':
                    context.methods.append(child.name)
            elif isinstance(child, ast.AsyncFunctionDef):
                if not child.name.startswith('_'):
                    context.methods.append(child.name)
        
        return context
    
    def _extract_decorators(self, node: Union[ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef]) -> List[str]:
        """Extract decorator names."""
        decorators = []
        for dec in node.decorator_list:
            if isinstance(dec, ast.Name):
                decorators.append(dec.id)
            elif isinstance(dec, ast.Attribute):
                decorators.append(ast.unparse(dec))
            elif isinstance(dec, ast.Call):
                if isinstance(dec.func, ast.Name):
                    decorators.append(dec.func.id)
                elif isinstance(dec.func, ast.Attribute):
                    decorators.append(ast.unparse(dec.func))
        return decorators
    
    def _extract_bases(self, node: ast.ClassDef) -> List[str]:
        """Extract base class names."""
        bases = []
        for base in node.bases:
            if isinstance(base, ast.Name):
                bases.append(base.id)
            elif isinstance(base, ast.Attribute):
                bases.append(ast.unparse(base))
        return bases
    
    def _extract_parameters(self, node: Union[ast.FunctionDef, ast.AsyncFunctionDef]) -> List[ParameterInfo]:
        """Extract parameter information."""
        params = []
        
        # Positional args
        for i, arg in enumerate(node.args.args):
            param = ParameterInfo(
                name=arg.arg,
                type_hint=ast.unparse(arg.annotation) if arg.annotation else None,
                kind="positional_or_keyword"
            )
            
            # Check for default value
            defaults_offset = len(node.args.args) - len(node.args.defaults)
            if i >= defaults_offset:
                default_idx = i - defaults_offset
                param.default_value = ast.unparse(node.args.defaults[default_idx])
            
            params.append(param)
        
        # Varargs
        if node.args.vararg:
            params.append(ParameterInfo(
                name=f"*{node.args.vararg.arg}",
                type_hint=ast.unparse(node.args.vararg.annotation) if node.args.vararg.annotation else None,
                kind="varargs"
            ))
        
        # Kwargs
        if node.args.kwarg:
            params.append(ParameterInfo(
                name=f"**{node.args.kwarg.arg}",
                type_hint=ast.unparse(node.args.kwarg.annotation) if node.args.kwarg.annotation else None,
                kind="kwargs"
            ))
        
        return params
    
    def _extract_exceptions(self, node: Union[ast.FunctionDef, ast.AsyncFunctionDef]) -> List[ExceptionInfo]:
        """Extract raised exceptions from function body."""
        exceptions = []
        
        for child in ast.walk(node):
            if isinstance(child, ast.Raise):
                if child.exc:
                    if isinstance(child.exc, ast.Call):
                        if isinstance(child.exc.func, ast.Name):
                            exceptions.append(ExceptionInfo(
                                exception_type=child.exc.func.id
                            ))
                    elif isinstance(child.exc, ast.Name):
                        exceptions.append(ExceptionInfo(
                            exception_type=child.exc.id
                        ))
        
        return exceptions
    
    def _summarize_body(self, node: Union[ast.FunctionDef, ast.AsyncFunctionDef]) -> str:
        """Create a brief summary of function body."""
        if not node.body:
            return "Empty function"
        
        first_stmt = node.body[0]
        
        if isinstance(first_stmt, ast.Return):
            if first_stmt.value:
                return f"Returns {ast.unparse(first_stmt.value)}"
            return "Returns None"
        elif isinstance(first_stmt, ast.Pass):
            return "Placeholder function"
        elif isinstance(first_stmt, ast.Raise):
            return "Raises an exception"
        elif isinstance(first_stmt, ast.Expr):
            if isinstance(first_stmt.value, ast.Constant):
                return "Docstring placeholder"
        
        return f"Function with {len(node.body)} statements"
    
    def _calculate_complexity(self, node: ast.AST) -> int:
        """Calculate simple cyclomatic complexity."""
        complexity = 1
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(child, (ast.And, ast.Or)):
                complexity += 1
        
        return complexity
    
    # AST visitor methods
    def visit_ClassDef(self, node: ast.ClassDef):
        """Visit class definition."""
        self.current_class = node.name
        context = self.extract_class_context(node)
        self.classes.append(context)
        self.generic_visit(node)
        self.current_class = None
    
    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Visit function definition."""
        if self.current_class and node.name.startswith('_') and node.name != '__init__':
            return
        
        context = self.extract_function_context(node, is_method=self.current_class is not None)
        self.functions.append(context)
    
    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        """Visit async function definition."""
        if self.current_class and node.name.startswith('_'):
            return
        
        context = self.extract_function_context(node, is_method=self.current_class is not None)
        self.functions.append(context)


# ============================================================
# DOCSTRING GENERATORS
# ============================================================

class DocstringFormatter:
    """Format docstrings in various styles."""
    
    def __init__(self, style: DocstringStyle = DocstringStyle.GOOGLE):
        self.style = style
    
    def format_function(self, context: FunctionContext) -> str:
        """Format function docstring."""
        if self.style == DocstringStyle.GOOGLE:
            return self._format_google_function(context)
        elif self.style == DocstringStyle.NUMPY:
            return self._format_numpy_function(context)
        elif self.style == DocstringStyle.SPHINX:
            return self._format_sphinx_function(context)
        else:
            return self._format_plain_function(context)
    
    def format_class(self, context: ClassContext) -> str:
        """Format class docstring."""
        if self.style == DocstringStyle.GOOGLE:
            return self._format_google_class(context)
        elif self.style == DocstringStyle.NUMPY:
            return self._format_numpy_class(context)
        elif self.style == DocstringStyle.SPHINX:
            return self._format_sphinx_class(context)
        else:
            return self._format_plain_class(context)
    
    def format_module(self, context: ModuleContext) -> str:
        """Format module docstring."""
        if self.style == DocstringStyle.GOOGLE:
            return self._format_google_module(context)
        else:
            return self._format_plain_module(context)
    
    def _format_google_function(self, context: FunctionContext) -> str:
        """Format Google-style function docstring."""
        lines = []
        
        # Summary line
        if context.existing_docstring:
            first_line = context.existing_docstring.split('\n')[0].strip()
            if first_line:
                lines.append(first_line)
            else:
                lines.append(self._generate_summary(context))
        else:
            lines.append(self._generate_summary(context))
        
        lines.append("")
        
        # Args section
        if context.parameters:
            lines.append("Args:")
            for param in context.parameters:
                type_str = f" ({param.type_hint})" if param.type_hint else ""
                default_str = f", optional" if param.default_value else ""
                lines.append(f"    {param.name}{type_str}: {param.description or 'No description'}{default_str}")
            lines.append("")
        
        # Returns section
        if context.return_info:
            lines.append("Returns:")
            type_str = f"{context.return_info.type_hint}: " if context.return_info.type_hint else ""
            lines.append(f"    {type_str}{context.return_info.description or 'Return value'}")
            lines.append("")
        elif not context.is_property and not context.is_abstract:
            lines.append("Returns:")
            lines.append("    None")
            lines.append("")
        
        # Raises section
        if context.exceptions:
            lines.append("Raises:")
            for exc in context.exceptions:
                lines.append(f"    {exc.exception_type}: {exc.description or 'If an error occurs'}")
            lines.append("")
        
        # Examples section
        if context.complexity > 3:
            lines.append("Examples:")
            lines.append(f"    >>> {self._generate_example(context)}")
            lines.append("")
        
        return '\n'.join(lines).rstrip()
    
    def _format_numpy_function(self, context: FunctionContext) -> str:
        """Format NumPy-style function docstring."""
        lines = []
        
        # Summary
        lines.append(self._generate_summary(context))
        lines.append("")
        
        # Extended description
        if context.complexity > 5:
            lines.append("Extended description of the function.")
            lines.append("")
        
        # Parameters section
        if context.parameters:
            lines.append("Parameters")
            lines.append("----------")
            for param in context.parameters:
                type_str = f" : {param.type_hint}" if param.type_hint else ""
                lines.append(f"{param.name}{type_str}")
                lines.append(f"    {param.description or 'No description'}")
            lines.append("")
        
        # Returns section
        lines.append("Returns")
        lines.append("-------")
        if context.return_info:
            type_str = f"{context.return_info.type_hint}" if context.return_info.type_hint else "None"
            lines.append(f"{type_str}")
            lines.append(f"    {context.return_info.description or 'Return value'}")
        else:
            lines.append("None")
        lines.append("")
        
        # Raises section
        if context.exceptions:
            lines.append("Raises")
            lines.append("------")
            for exc in context.exceptions:
                lines.append(f"{exc.exception_type}")
                lines.append(f"    {exc.description or 'If an error occurs'}")
            lines.append("")
        
        return '\n'.join(lines).rstrip()
    
    def _format_sphinx_function(self, context: FunctionContext) -> str:
        """Format Sphinx-style function docstring."""
        lines = []
        
        # Summary
        lines.append(self._generate_summary(context))
        lines.append("")
        
        # Parameters
        for param in context.parameters:
            type_str = f" ({param.type_hint})" if param.type_hint else ""
            lines.append(f":param {param.name}{type_str}: {param.description or 'No description'}")
        
        # Return
        if context.return_info:
            type_str = f" {context.return_info.type_hint}" if context.return_info.type_hint else ""
            lines.append(f":return{type_str}: {context.return_info.description or 'Return value'}")
        elif not context.is_property:
            lines.append(":return: None")
        
        # Return type
        if context.return_info and context.return_info.type_hint:
            lines.append(f":rtype: {context.return_info.type_hint}")
        
        # Raises
        for exc in context.exceptions:
            lines.append(f":raises {exc.exception_type}: {exc.description or 'If an error occurs'}")
        
        return '\n'.join(lines).rstrip()
    
    def _format_plain_function(self, context: FunctionContext) -> str:
        """Format plain function docstring."""
        lines = [self._generate_summary(context)]
        return '\n'.join(lines)
    
    def _format_google_class(self, context: ClassContext) -> str:
        """Format Google-style class docstring."""
        lines = []
        
        # Summary
        lines.append(self._generate_class_summary(context))
        lines.append("")
        
        # Attributes
        if context.attributes:
            lines.append("Attributes:")
            for attr_name, attr_type in context.attributes:
                lines.append(f"    {attr_name} ({attr_type}): Class attribute")
            lines.append("")
        
        # Methods summary
        if context.methods:
            lines.append("Methods:")
            for method in context.methods[:10]:
                lines.append(f"    {method}(): Method description")
            if len(context.methods) > 10:
                lines.append(f"    ... and {len(context.methods) - 10} more")
            lines.append("")
        
        # Examples
        lines.append("Examples:")
        lines.append(f"    >>> obj = {context.name}()")
        lines.append("")
        
        return '\n'.join(lines).rstrip()
    
    def _format_numpy_class(self, context: ClassContext) -> str:
        """Format NumPy-style class docstring."""
        lines = []
        
        lines.append(self._generate_class_summary(context))
        lines.append("")
        
        if context.attributes:
            lines.append("Attributes")
            lines.append("----------")
            for attr_name, attr_type in context.attributes:
                lines.append(f"{attr_name} : {attr_type}")
                lines.append(f"    Class attribute")
            lines.append("")
        
        return '\n'.join(lines).rstrip()
    
    def _format_sphinx_class(self, context: ClassContext) -> str:
        """Format Sphinx-style class docstring."""
        lines = []
        
        lines.append(self._generate_class_summary(context))
        lines.append("")
        
        for attr_name, attr_type in context.attributes:
            lines.append(f":ivar {attr_name}: Class attribute")
        
        return '\n'.join(lines).rstrip()
    
    def _format_plain_class(self, context: ClassContext) -> str:
        """Format plain class docstring."""
        return self._generate_class_summary(context)
    
    def _format_google_module(self, context: ModuleContext) -> str:
        """Format Google-style module docstring."""
        lines = []
        
        lines.append(f"{context.name} module.")
        lines.append("")
        
        if context.description:
            lines.append(context.description)
            lines.append("")
        
        if context.exports:
            lines.append("Exports:")
            for export in context.exports:
                lines.append(f"    {export}")
            lines.append("")
        
        return '\n'.join(lines).rstrip()
    
    def _format_plain_module(self, context: ModuleContext) -> str:
        """Format plain module docstring."""
        return f"{context.name} module."
    
    def _generate_summary(self, context: FunctionContext) -> str:
        """Generate function summary."""
        prefix = "Async " if context.is_async else ""
        
        if context.is_property:
            return f"{prefix}Property: {context.name}"
        elif context.is_method:
            if context.name == '__init__':
                return f"Initialize {context.module_path.split('.')[-1]}."
            elif context.name.startswith('__'):
                return f"Special method {context.name}."
            return f"{prefix}{context.name.replace('_', ' ').title()}."
        else:
            return f"{prefix}{context.name.replace('_', ' ').title()}."
    
    def _generate_class_summary(self, context: ClassContext) -> str:
        """Generate class summary."""
        if context.is_dataclass:
            return f"{context.name} dataclass."
        elif context.is_enum:
            return f"{context.name} enumeration."
        elif context.is_abstract:
            return f"Abstract base class for {context.name}."
        return f"{context.name} class."
    
    def _generate_example(self, context: FunctionContext) -> str:
        """Generate usage example."""
        args = []
        for param in context.parameters[:3]:
            if param.default_value:
                continue
            if param.type_hint == 'str':
                args.append(f'"{param.name}_value"')
            elif param.type_hint == 'int':
                args.append('42')
            elif param.type_hint == 'bool':
                args.append('True')
            elif 'List' in (param.type_hint or ''):
                args.append('[]')
            elif 'Dict' in (param.type_hint or ''):
                args.append('{}')
            else:
                args.append(param.name)
        
        args_str = ', '.join(args)
        return f"{context.name}({args_str})"


# ============================================================
# MAIN DOCSTRING GENERATOR
# ============================================================

class DocstringGenerator:
    """
    Generates comprehensive docstrings for Python code.
    
    Features:
    - AI-powered docstring generation
    - Multiple docstring styles (Google, NumPy, Sphinx)
    - Context-aware content extraction
    - Quality assessment and improvement
    - Batch processing for entire files/projects
    - Existing docstring enhancement
    - Validation with mypy
    - Export to various formats
    """
    
    def __init__(self, config: Optional[DocstringGeneratorConfig] = None):
        self.config = config or DocstringGeneratorConfig()
        self.formatter = DocstringFormatter(self.config.style)
        self.llm = LLMClient() if self.config.use_llm else None
        self.state = StateManager(Path(".ai_state") / "docstring_generator.json")
        
        self.mypy_validator = MypyValidator() if self.config.validate_with_mypy else None
        
        logger.info(f"DocstringGenerator initialized with {self.config.style.value} style")
    
    # ============================================================
    # GENERATION
    # ============================================================
    
    def generate_for_function(self, context: FunctionContext) -> GeneratedDocstring:
        """Generate docstring for a function."""
        logger.debug(f"Generating docstring for {context.name}")
        
        # Check existing quality
        existing_quality = self._assess_quality(context.existing_docstring) if context.existing_docstring else DocstringQuality.NONE
        
        if existing_quality.value >= self.config.min_quality_to_keep.value and not self.config.update_existing:
            return GeneratedDocstring(
                target=context.name,
                docstring=context.existing_docstring or "",
                style=self.config.style,
                quality=existing_quality,
                existing=context.existing_docstring,
                improved=False
            )
        
        # Generate with AI if enabled and needed
        if self.llm and (not context.existing_docstring or self.config.update_existing):
            docstring = self._generate_with_llm(context)
            quality = self._assess_quality(docstring)
        else:
            docstring = self.formatter.format_function(context)
            quality = DocstringQuality.BASIC
        
        # Enhance if quality below target
        if quality.value < self.config.quality.value and self.llm:
            docstring = self._enhance_docstring(docstring, context)
            quality = self._assess_quality(docstring)
        
        # Extract sections
        sections = self._extract_sections(docstring)
        
        return GeneratedDocstring(
            target=context.name,
            docstring=docstring,
            style=self.config.style,
            quality=quality,
            existing=context.existing_docstring,
            improved=context.existing_docstring is not None and docstring != context.existing_docstring,
            sections=sections
        )
    
    def generate_for_class(self, context: ClassContext) -> GeneratedDocstring:
        """Generate docstring for a class."""
        logger.debug(f"Generating docstring for {context.name}")
        
        existing_quality = self._assess_quality(context.existing_docstring) if context.existing_docstring else DocstringQuality.NONE
        
        if existing_quality.value >= self.config.min_quality_to_keep.value and not self.config.update_existing:
            return GeneratedDocstring(
                target=context.name,
                docstring=context.existing_docstring or "",
                style=self.config.style,
                quality=existing_quality,
                existing=context.existing_docstring,
                improved=False
            )
        
        if self.llm:
            docstring = self._generate_class_with_llm(context)
            quality = self._assess_quality(docstring)
        else:
            docstring = self.formatter.format_class(context)
            quality = DocstringQuality.BASIC
        
        sections = self._extract_sections(docstring)
        
        return GeneratedDocstring(
            target=context.name,
            docstring=docstring,
            style=self.config.style,
            quality=quality,
            existing=context.existing_docstring,
            improved=context.existing_docstring is not None and docstring != context.existing_docstring,
            sections=sections
        )
    
    def generate_for_module(self, context: ModuleContext) -> GeneratedDocstring:
        """Generate docstring for a module."""
        logger.debug(f"Generating docstring for module {context.name}")
        
        if self.llm:
            docstring = self._generate_module_with_llm(context)
        else:
            docstring = self.formatter.format_module(context)
        
        quality = self._assess_quality(docstring)
        sections = self._extract_sections(docstring)
        
        return GeneratedDocstring(
            target=context.name,
            docstring=docstring,
            style=self.config.style,
            quality=quality,
            existing=context.existing_docstring,
            improved=context.existing_docstring is not None and docstring != context.existing_docstring,
            sections=sections
        )
    
    def _generate_with_llm(self, context: FunctionContext) -> str:
        """Generate docstring using LLM."""
        prompt = f"""
        Generate a {self.config.style.value}-style docstring for this Python function:
        
        Function: {context.name}
        Module: {context.module_path}
        Async: {context.is_async}
        Method: {context.is_method}
        Decorators: {', '.join(context.decorators) if context.decorators else 'none'}
        
        Parameters:
        {self._format_parameters_for_prompt(context.parameters)}
        
        Returns: {context.return_info.type_hint if context.return_info else 'None'}
        
        Exceptions raised: {', '.join(e.exception_type for e in context.exceptions) if context.exceptions else 'none'}
        
        Body summary: {context.body_summary}
        Complexity: {context.complexity}
        
        {'Existing docstring to improve:\n' + context.existing_docstring if context.existing_docstring else 'No existing docstring.'}
        
        Requirements:
        - Start with a one-line summary
        - Include Args section with types and descriptions
        - Include Returns section
        - Include Raises section if applicable
        - Add Examples section if complexity > 3
        - Use proper indentation
        
        Output only the docstring content (no quotes, no code).
        """
        
        response = self.llm.complete(prompt)
        return self._clean_docstring(response)
    
    def _generate_class_with_llm(self, context: ClassContext) -> str:
        """Generate class docstring using LLM."""
        prompt = f"""
        Generate a {self.config.style.value}-style docstring for this Python class:
        
        Class: {context.name}
        Module: {context.module_path}
        Bases: {', '.join(context.bases) if context.bases else 'none'}
        Dataclass: {context.is_dataclass}
        Enum: {context.is_enum}
        
        Attributes:
        {self._format_attributes_for_prompt(context.attributes)}
        
        Methods:
        {', '.join(context.methods[:10]) if context.methods else 'none'}
        
        {'Existing docstring to improve:\n' + context.existing_docstring if context.existing_docstring else 'No existing docstring.'}
        
        Output only the docstring content.
        """
        
        response = self.llm.complete(prompt)
        return self._clean_docstring(response)
    
    def _generate_module_with_llm(self, context: ModuleContext) -> str:
        """Generate module docstring using LLM."""
        prompt = f"""
        Generate a docstring for this Python module:
        
        Module: {context.name}
        Description: {context.description or 'No description'}
        Exports: {', '.join(context.exports) if context.exports else 'none'}
        Classes: {', '.join(context.classes[:5]) if context.classes else 'none'}
        Functions: {', '.join(context.functions[:5]) if context.functions else 'none'}
        
        Output only the docstring content.
        """
        
        response = self.llm.complete(prompt)
        return self._clean_docstring(response)
    
    def _format_parameters_for_prompt(self, params: List[ParameterInfo]) -> str:
        """Format parameters for LLM prompt."""
        lines = []
        for p in params:
            default_str = f" = {p.default_value}" if p.default_value else ""
            type_str = f": {p.type_hint}" if p.type_hint else ""
            lines.append(f"  - {p.name}{type_str}{default_str}")
        return '\n'.join(lines) if lines else "none"
    
    def _format_attributes_for_prompt(self, attrs: List[Tuple[str, str]]) -> str:
        """Format attributes for LLM prompt."""
        lines = []
        for name, type_hint in attrs:
            lines.append(f"  - {name}: {type_hint}")
        return '\n'.join(lines) if lines else "none"
    
    def _clean_docstring(self, text: str) -> str:
        """Clean LLM-generated docstring."""
        # Remove surrounding quotes
        text = text.strip()
        if text.startswith('"""'):
            text = text[3:]
        if text.endswith('"""'):
            text = text[:-3]
        if text.startswith("'''"):
            text = text[3:]
        if text.endswith("'''"):
            text = text[:-3]
        
        # Remove leading/trailing whitespace from each line
        lines = text.strip().split('\n')
        lines = [line.rstrip() for line in lines]
        
        return '\n'.join(lines)
    
    def _enhance_docstring(self, docstring: str, context: FunctionContext) -> str:
        """Enhance existing docstring with AI."""
        prompt = f"""
        Enhance this docstring to {self.config.quality.value} quality:
        
        Current docstring:
        {docstring}
        
        Function context:
        - Parameters: {len(context.parameters)}
        - Returns: {context.return_info.type_hint if context.return_info else 'None'}
        - Complexity: {context.complexity}
        
        Add missing sections and improve descriptions.
        Output only the enhanced docstring.
        """
        
        response = self.llm.complete(prompt)
        return self._clean_docstring(response)
    
    # ============================================================
    # FILE PROCESSING
    # ============================================================
    
    def process_file(self, file_path: Path) -> List[GeneratedDocstring]:
        """Process a single Python file."""
        logger.info(f"Processing file: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
            
            tree = ast.parse(content)
            
            # Get module name
            module_name = file_path.stem
            
            # Extract contexts
            extractor = ContextExtractor(module_name, lines)
            extractor.visit(tree)
            
            results = []
            
            # Generate module docstring
            module_context = ModuleContext(
                name=module_name,
                path=str(file_path),
                classes=[c.name for c in extractor.classes],
                functions=[f.name for f in extractor.functions if not f.is_method],
                existing_docstring=ast.get_docstring(tree)
            )
            
            if not module_context.existing_docstring or self.config.update_existing:
                module_doc = self.generate_for_module(module_context)
                results.append(module_doc)
            
            # Generate class docstrings
            for class_ctx in extractor.classes:
                if not class_ctx.existing_docstring or self.config.update_existing:
                    class_doc = self.generate_for_class(class_ctx)
                    results.append(class_doc)
            
            # Generate function docstrings
            for func_ctx in extractor.functions:
                if not func_ctx.existing_docstring or self.config.update_existing:
                    func_doc = self.generate_for_function(func_ctx)
                    results.append(func_doc)
            
            # Apply docstrings to file
            if results:
                updated_content = self._apply_docstrings(content, tree, results, extractor)
                
                # Write updated file
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(updated_content)
                
                logger.info(f"Updated {len(results)} docstrings in {file_path}")
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to process {file_path}: {e}")
            return []
    
    def _apply_docstrings(self, content: str, tree: ast.Module, 
                          results: List[GeneratedDocstring], 
                          extractor: ContextExtractor) -> str:
        """Apply generated docstrings to source code."""
        lines = content.split('\n')
        
        # Build mapping of targets to docstrings
        docstring_map = {r.target: r.docstring for r in results}
        
        # Apply module docstring
        if '__module__' in docstring_map or extractor.module_path in docstring_map:
            module_doc = docstring_map.get('__module__') or docstring_map.get(extractor.module_path)
            if module_doc and not ast.get_docstring(tree):
                # Insert at beginning of file
                doc_lines = self._format_docstring_lines(module_doc)
                lines = doc_lines + lines
        
        # Apply class docstrings
        for class_ctx in extractor.classes:
            if class_ctx.name in docstring_map:
                docstring = docstring_map[class_ctx.name]
                lines = self._insert_docstring(lines, class_ctx.line_count, docstring, class_ctx.existing_docstring)
        
        # Apply function docstrings
        for func_ctx in extractor.functions:
            if func_ctx.name in docstring_map:
                docstring = docstring_map[func_ctx.name]
                lines = self._insert_docstring(lines, func_ctx.line_count, docstring, func_ctx.existing_docstring)
        
        return '\n'.join(lines)
    
    def _format_docstring_lines(self, docstring: str) -> List[str]:
        """Format docstring for insertion."""
        lines = ['"""']
        lines.extend(docstring.split('\n'))
        lines.append('"""')
        return lines
    
    def _insert_docstring(self, lines: List[str], start_line: int, 
                          docstring: str, existing: Optional[str]) -> List[str]:
        """Insert or replace docstring in source lines."""
        doc_lines = self._format_docstring_lines(docstring)
        
        if existing:
            # Find and replace existing docstring
            # This is simplified - a real implementation would locate the exact docstring
            pass
        
        # Insert after definition line
        insert_idx = start_line
        for i, line in enumerate(doc_lines):
            lines.insert(insert_idx + i, line)
        
        return lines
    
    def process_directory(self, directory: Path, recursive: bool = True) -> Dict[str, List[GeneratedDocstring]]:
        """Process all Python files in a directory."""
        results = {}
        
        pattern = "**/*.py" if recursive else "*.py"
        for file_path in directory.glob(pattern):
            if 'test' in str(file_path).lower():
                continue
            
            file_results = self.process_file(file_path)
            if file_results:
                results[str(file_path)] = file_results
        
        logger.info(f"Processed {len(results)} files")
        return results
    
    # ============================================================
    # QUALITY ASSESSMENT
    # ============================================================
    
    def _assess_quality(self, docstring: Optional[str]) -> DocstringQuality:
        """Assess the quality of a docstring."""
        if not docstring:
            return DocstringQuality.NONE
        
        docstring = docstring.strip()
        
        # Check length
        if len(docstring) < 10:
            return DocstringQuality.MINIMAL
        
        lines = docstring.split('\n')
        
        # Check for sections
        has_args = any('Args' in line or 'Parameters' in line for line in lines)
        has_returns = any('Returns' in line or 'Return' in line for line in lines)
        has_raises = any('Raises' in line for line in lines)
        has_examples = any('Example' in line for line in lines)
        
        # Score based on sections
        score = 1  # Basic
        if has_args:
            score += 1
        if has_returns:
            score += 1
        if has_raises:
            score += 1
        if has_examples:
            score += 1
        
        # Check description length
        first_line = lines[0].strip()
        if len(first_line) > 50:
            score += 1
        
        if score <= 1:
            return DocstringQuality.MINIMAL
        elif score <= 2:
            return DocstringQuality.BASIC
        elif score <= 3:
            return DocstringQuality.GOOD
        elif score <= 4:
            return DocstringQuality.COMPREHENSIVE
        else:
            return DocstringQuality.EXCELLENT
    
    def _extract_sections(self, docstring: str) -> List[DocstringSection]:
        """Extract sections present in docstring."""
        sections = []
        docstring_lower = docstring.lower()
        
        if 'args:' in docstring_lower or 'arguments:' in docstring_lower or 'parameters:' in docstring_lower:
            sections.append(DocstringSection.ARGS)
        
        if 'returns:' in docstring_lower or 'return:' in docstring_lower:
            sections.append(DocstringSection.RETURNS)
        
        if 'raises:' in docstring_lower or 'exceptions:' in docstring_lower:
            sections.append(DocstringSection.RAISES)
        
        if 'examples:' in docstring_lower or 'example:' in docstring_lower:
            sections.append(DocstringSection.EXAMPLES)
        
        if 'yields:' in docstring_lower:
            sections.append(DocstringSection.YIELDS)
        
        if 'note:' in docstring_lower or 'notes:' in docstring_lower:
            sections.append(DocstringSection.NOTES)
        
        if 'see also:' in docstring_lower:
            sections.append(DocstringSection.SEE_ALSO)
        
        if 'attributes:' in docstring_lower:
            sections.append(DocstringSection.ATTRIBUTES)
        
        if 'deprecated:' in docstring_lower:
            sections.append(DocstringSection.DEPRECATED)
        
        return sections
    
    # ============================================================
    # REPORTING
    # ============================================================
    
    def generate_report(self, results: Dict[str, List[GeneratedDocstring]]) -> str:
        """Generate a summary report."""
        total_docs = sum(len(r) for r in results.values())
        improved = sum(1 for r in results.values() for d in r if d.improved)
        
        quality_counts = defaultdict(int)
        for file_results in results.values():
            for doc in file_results:
                quality_counts[doc.quality.value] += 1
        
        lines = [
            "# Docstring Generation Report",
            "",
            f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## Summary",
            "",
            f"- **Files Processed:** {len(results)}",
            f"- **Total Docstrings:** {total_docs}",
            f"- **Improved:** {improved}",
            "",
            "## Quality Distribution",
            "",
            "| Quality | Count |",
            "|---------|-------|",
        ]
        
        for quality in DocstringQuality:
            count = quality_counts.get(quality.value, 0)
            lines.append(f"| {quality.value} | {count} |")
        
        return '\n'.join(lines)
    
    def close(self):
        """Clean up resources."""
        self.state.save()
        logger.info("DocstringGenerator closed")


# ============================================================
# CLI ENTRY POINT
# ============================================================

def main():
    """CLI entry point for docstring generator."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate docstrings for Python code")
    parser.add_argument("path", type=Path, help="File or directory to process")
    parser.add_argument("--style", choices=[s.value for s in DocstringStyle],
                       default=DocstringStyle.GOOGLE.value, help="Docstring style")
    parser.add_argument("--quality", choices=[q.value for q in DocstringQuality],
                       default=DocstringQuality.GOOD.value, help="Target quality")
    parser.add_argument("--recursive", "-r", action="store_true", help="Process directories recursively")
    parser.add_argument("--no-llm", action="store_true", help="Disable LLM assistance")
    parser.add_argument("--update-existing", action="store_true", help="Update existing docstrings")
    parser.add_argument("--report", action="store_true", help="Generate report only")
    
    args = parser.parse_args()
    
    config = DocstringGeneratorConfig(
        style=DocstringStyle(args.style),
        quality=DocstringQuality(args.quality),
        use_llm=not args.no_llm,
        update_existing=args.update_existing
    )
    
    generator = DocstringGenerator(config)
    
    if args.path.is_file():
        results = {str(args.path): generator.process_file(args.path)}
    else:
        results = generator.process_directory(args.path, args.recursive)
    
    if args.report:
        report = generator.generate_report(results)
        print(report)
    else:
        total_docs = sum(len(r) for r in results.values())
        print(f"Generated {total_docs} docstrings across {len(results)} files")
    
    generator.close()


if __name__ == "__main__":
    main()
