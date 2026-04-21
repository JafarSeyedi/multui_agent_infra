#!/usr/bin/env python3
"""
Naming & Spellcheck Validator - Validates naming conventions and spelling in code.

Part of the Quality tools (validators/naming_spellcheck_validator.py)

This naming_spellcheck_validator.py provides:

1. PEP 8 Naming Validation - Enforces Python naming conventions (snake_case, PascalCase, UPPER_CASE)
2. Per-Entity Type Rules - Different conventions for modules, classes, functions, variables, etc.
3. Spell Checking - Validates spelling in identifiers, comments, and docstrings
4. Multiple Language Support - English (US/GB), German, French, Spanish, Italian, Dutch, Portuguese, Russian
5. Common Misspelling Detection - Built-in dictionary of frequent misspellings
6. Banned Name Detection - Flags problematic names like 'Manager', 'Util', 'Helper'
7. Intelligent Word Extraction - Splits camelCase and snake_case for spell checking
8. Custom Dictionary Support - Add project-specific terms
9. Technical Term Recognition - Pre-loaded with common tech terms (API, JSON, async, etc.)
10. Auto-Suggestions - Provides corrected names for violations
11. Length Validation - Enforces min/max name lengths
12. Prefix/Suffix Rules - Enforces patterns like 'T' for TypeVars, 'Error' for exceptions

The naming and spellcheck validator ensures your codebase maintains consistent, readable, and professional naming standards.

"""

import ast
import re
import enchant
from pathlib import Path
from typing import Dict, List, Set, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from collections import defaultdict

from ...shared.logger import get_logger
from ...shared.state_manager import StateManager

logger = get_logger(__name__)


# ============================================================
# ENUMS AND CONSTANTS
# ============================================================

class NamingConvention(str, Enum):
    """Naming convention type."""
    SNAKE_CASE = "snake_case"
    CAMEL_CASE = "camelCase"
    PASCAL_CASE = "PascalCase"
    UPPER_SNAKE_CASE = "UPPER_SNAKE_CASE"
    KEBAB_CASE = "kebab-case"
    FLAT_CASE = "flatcase"
    HUNGARIAN = "hungarian"


class EntityType(str, Enum):
    """Type of code entity."""
    MODULE = "module"
    PACKAGE = "package"
    CLASS = "class"
    EXCEPTION = "exception"
    FUNCTION = "function"
    METHOD = "method"
    VARIABLE = "variable"
    CONSTANT = "constant"
    ARGUMENT = "argument"
    ATTRIBUTE = "attribute"
    PROPERTY = "property"
    TYPE_VAR = "type_var"
    TYPE_ALIAS = "type_alias"
    ENUM = "enum"
    ENUM_VALUE = "enum_value"


class Severity(str, Enum):
    """Severity of naming/spelling issue."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class SpellcheckLanguage(str, Enum):
    """Language for spell checking."""
    ENGLISH_US = "en_US"
    ENGLISH_GB = "en_GB"
    GERMAN = "de_DE"
    FRENCH = "fr_FR"
    SPANISH = "es_ES"
    ITALIAN = "it_IT"
    DUTCH = "nl_NL"
    PORTUGUESE = "pt_PT"
    RUSSIAN = "ru_RU"


# ============================================================
# DATA MODELS
# ============================================================

@dataclass
class NamingRule:
    """Naming convention rule for an entity type."""
    entity_type: EntityType
    convention: NamingConvention
    prefix: Optional[str] = None
    suffix: Optional[str] = None
    allow_private_prefix: bool = True
    allow_dunder: bool = True
    min_length: int = 2
    max_length: int = 50
    banned_names: List[str] = field(default_factory=list)
    required_patterns: List[str] = field(default_factory=list)


@dataclass
class NamingViolation:
    """A naming convention violation."""
    entity_type: EntityType
    entity_name: str
    file_path: str
    line_number: Optional[int] = None
    expected_convention: NamingConvention = NamingConvention.SNAKE_CASE
    severity: Severity = Severity.WARNING
    reason: str = ""
    suggestion: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SpellingViolation:
    """A spelling violation."""
    word: str
    file_path: str
    line_number: Optional[int] = None
    context: Optional[str] = None
    suggestions: List[str] = field(default_factory=list)
    severity: Severity = Severity.INFO
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class NamingSpellcheckReport:
    """Complete naming and spellcheck validation report."""
    validated_at: datetime = field(default_factory=datetime.now)
    project_name: str = ""
    
    # Statistics
    total_entities: int = 0
    naming_violations: int = 0
    spelling_violations: int = 0
    
    # Violations
    naming_issues: List[NamingViolation] = field(default_factory=list)
    spelling_issues: List[SpellingViolation] = field(default_factory=list)
    
    # Common misspellings
    common_misspellings: Dict[str, int] = field(default_factory=dict)
    
    # Banned names found
    banned_names_found: List[Tuple[str, str]] = field(default_factory=list)
    
    # Validation
    is_valid: bool = True
    overall_score: float = 0.0
    grade: str = "A"
    summary: str = ""
    recommendations: List[str] = field(default_factory=list)
    
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class NamingSpellcheckConfig:
    """Configuration for naming and spellcheck validator."""
    project_root: Path
    
    # Naming rules by entity type
    naming_rules: Dict[EntityType, NamingRule] = field(default_factory=lambda: {
        EntityType.MODULE: NamingRule(
            entity_type=EntityType.MODULE,
            convention=NamingConvention.SNAKE_CASE,
            max_length=30
        ),
        EntityType.PACKAGE: NamingRule(
            entity_type=EntityType.PACKAGE,
            convention=NamingConvention.SNAKE_CASE,
            max_length=30
        ),
        EntityType.CLASS: NamingRule(
            entity_type=EntityType.CLASS,
            convention=NamingConvention.PASCAL_CASE,
            banned_names=['Manager', 'Util', 'Helper', 'Common', 'Base']
        ),
        EntityType.EXCEPTION: NamingRule(
            entity_type=EntityType.EXCEPTION,
            convention=NamingConvention.PASCAL_CASE,
            suffix='Error'
        ),
        EntityType.FUNCTION: NamingRule(
            entity_type=EntityType.FUNCTION,
            convention=NamingConvention.SNAKE_CASE,
            banned_names=['do', 'make', 'get', 'set', 'create', 'update', 'delete']
        ),
        EntityType.METHOD: NamingRule(
            entity_type=EntityType.METHOD,
            convention=NamingConvention.SNAKE_CASE,
            allow_private_prefix=True
        ),
        EntityType.VARIABLE: NamingRule(
            entity_type=EntityType.VARIABLE,
            convention=NamingConvention.SNAKE_CASE,
            min_length=1,
            banned_names=['l', 'O', 'I']
        ),
        EntityType.CONSTANT: NamingRule(
            entity_type=EntityType.CONSTANT,
            convention=NamingConvention.UPPER_SNAKE_CASE
        ),
        EntityType.ARGUMENT: NamingRule(
            entity_type=EntityType.ARGUMENT,
            convention=NamingConvention.SNAKE_CASE
        ),
        EntityType.ATTRIBUTE: NamingRule(
            entity_type=EntityType.ATTRIBUTE,
            convention=NamingConvention.SNAKE_CASE,
            allow_private_prefix=True
        ),
        EntityType.TYPE_VAR: NamingRule(
            entity_type=EntityType.TYPE_VAR,
            convention=NamingConvention.PASCAL_CASE,
            prefix='T'
        ),
        EntityType.ENUM: NamingRule(
            entity_type=EntityType.ENUM,
            convention=NamingConvention.PASCAL_CASE
        ),
        EntityType.ENUM_VALUE: NamingRule(
            entity_type=EntityType.ENUM_VALUE,
            convention=NamingConvention.UPPER_SNAKE_CASE
        ),
    })
    
    # Spellcheck configuration
    check_spelling: bool = True
    spellcheck_language: SpellcheckLanguage = SpellcheckLanguage.ENGLISH_US
    check_comments: bool = True
    check_docstrings: bool = True
    check_strings: bool = False
    custom_dictionary: List[str] = field(default_factory=list)
    technical_terms: List[str] = field(default_factory=lambda: [
        'api', 'json', 'xml', 'html', 'css', 'http', 'https', 'url', 'uri',
        'uuid', 'sql', 'nosql', 'redis', 'mongodb', 'postgres', 'mysql',
        'docker', 'kubernetes', 'aws', 'azure', 'gcp', 'ci', 'cd', 'devops',
        'async', 'await', 'coroutine', 'future', 'promise', 'callback',
        'dataclass', 'enum', 'decorator', 'generator', 'iterator', 'iterable',
        'serializer', 'deserializer', 'validator', 'middleware', 'backend',
        'frontend', 'fullstack', 'microservice', 'serverless', 'lambda'
    ])
    
    # Ignore patterns
    ignore_patterns: List[str] = field(default_factory=lambda: [
        "__pycache__", "*.pyc", ".git", ".venv", "venv", "dist", "build",
        ".pytest_cache", ".mypy_cache", ".ruff_cache", "test_*.py", "*_test.py",
        "migrations", "alembic"
    ])
    ignore_names: List[str] = field(default_factory=lambda: [
        'self', 'cls', 'args', 'kwargs', 'mcs', '__class__', '__dict__',
        '__doc__', '__file__', '__name__', '__package__', '__path__'
    ])
    
    # Common misspellings (can be extended)
    common_misspellings: Dict[str, str] = field(default_factory=lambda: {
        'accomodate': 'accommodate',
        'acheive': 'achieve',
        'adress': 'address',
        'begining': 'beginning',
        'calback': 'callback',
        'colum': 'column',
        'comming': 'coming',
        'commited': 'committed',
        'conatiner': 'container',
        'deamon': 'daemon',
        'dependancy': 'dependency',
        'destory': 'destroy',
        'develope': 'develop',
        'enviroment': 'environment',
        'excecute': 'execute',
        'exeption': 'exception',
        'fucntion': 'function',
        'funtion': 'function',
        'handeler': 'handler',
        'implemnt': 'implement',
        'initalize': 'initialize',
        'intialize': 'initialize',
        'langauge': 'language',
        'libary': 'library',
        'mesage': 'message',
        'metod': 'method',
        'occurance': 'occurrence',
        'paramater': 'parameter',
        'prameter': 'parameter',
        'recieve': 'receive',
        'reponse': 'response',
        'responce': 'response',
        'seperate': 'separate',
        'seralize': 'serialize',
        'succeded': 'succeeded',
        'sucess': 'success',
        'thier': 'their',
        'treshold': 'threshold',
        'unittest': 'unit test',
        'usefull': 'useful',
        'varable': 'variable',
        'varient': 'variant',
        'verison': 'version',
        'widht': 'width',
    })
    
    # Validation
    fail_on_error: bool = True
    fail_on_warning: bool = False
    fail_on_spelling: bool = False
    
    # Reporting
    generate_report: bool = True
    output_format: str = "markdown"


# ============================================================
# NAMING VALIDATOR
# ============================================================

class NamingValidator(ast.NodeVisitor):
    """Validate naming conventions in Python code."""
    
    def __init__(self, config: NamingSpellcheckConfig, file_path: str):
        self.config = config
        self.file_path = file_path
        self.violations: List[NamingViolation] = []
        self.current_class: Optional[str] = None
        self.total_entities: int = 0
    
    def validate(self, tree: ast.AST) -> Tuple[List[NamingViolation], int]:
        """Validate naming conventions in AST."""
        self.visit(tree)
        return self.violations, self.total_entities
    
    def visit_Module(self, node: ast.Module):
        """Visit module."""
        # Module name comes from file path
        module_name = Path(self.file_path).stem
        if module_name != '__init__':
            self._validate_name(module_name, EntityType.MODULE, 1)
        
        self.generic_visit(node)
    
    def visit_ClassDef(self, node: ast.ClassDef):
        """Visit class definition."""
        self.total_entities += 1
        
        # Determine if this is an exception
        is_exception = self._is_exception_class(node)
        entity_type = EntityType.EXCEPTION if is_exception else EntityType.CLASS
        
        self._validate_name(node.name, entity_type, node.lineno)
        
        prev_class = self.current_class
        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = prev_class
    
    def _is_exception_class(self, node: ast.ClassDef) -> bool:
        """Check if class is an exception."""
        for base in node.bases:
            if isinstance(base, ast.Name) and base.id in ('Exception', 'BaseException', 'Error'):
                return True
            elif isinstance(base, ast.Attribute) and base.attr in ('Exception', 'BaseException', 'Error'):
                return True
        return False
    
    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Visit function definition."""
        self.total_entities += 1
        
        entity_type = EntityType.METHOD if self.current_class else EntityType.FUNCTION
        self._validate_name(node.name, entity_type, node.lineno)
        
        # Validate arguments
        for arg in node.args.args:
            self.total_entities += 1
            self._validate_name(arg.arg, EntityType.ARGUMENT, node.lineno)
        
        self.generic_visit(node)
    
    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        """Visit async function definition."""
        self.visit_FunctionDef(node)
    
    def visit_Assign(self, node: ast.Assign):
        """Visit assignment."""
        for target in node.targets:
            if isinstance(target, ast.Name):
                self.total_entities += 1
                
                # Determine if constant (all caps)
                if target.id.isupper():
                    entity_type = EntityType.CONSTANT
                else:
                    entity_type = EntityType.VARIABLE
                
                self._validate_name(target.id, entity_type, node.lineno)
            
            elif isinstance(target, ast.Attribute):
                if isinstance(target.value, ast.Name) and target.value.id == 'self':
                    self.total_entities += 1
                    self._validate_name(target.attr, EntityType.ATTRIBUTE, node.lineno)
        
        self.generic_visit(node)
    
    def visit_AnnAssign(self, node: ast.AnnAssign):
        """Visit annotated assignment."""
        if isinstance(node.target, ast.Name):
            self.total_entities += 1
            self._validate_name(node.target.id, EntityType.VARIABLE, node.lineno)
        elif isinstance(node.target, ast.Attribute):
            if isinstance(node.target.value, ast.Name) and node.target.value.id == 'self':
                self.total_entities += 1
                self._validate_name(node.target.attr, EntityType.ATTRIBUTE, node.lineno)
        
        self.generic_visit(node)
    
    def visit_TypeVar(self, node):
        """Visit TypeVar."""
        if hasattr(node, 'name'):
            self.total_entities += 1
            self._validate_name(node.name, EntityType.TYPE_VAR, getattr(node, 'lineno', 0))
    
    def _validate_name(self, name: str, entity_type: EntityType, line_number: int):
        """Validate a name against naming rules."""
        # Check ignored names
        if name in self.config.ignore_names:
            return
        
        rule = self.config.naming_rules.get(entity_type)
        if not rule:
            return
        
        # Check private/dunder
        if name.startswith('__') and name.endswith('__'):
            if not rule.allow_dunder:
                self._add_violation(entity_type, name, line_number, rule,
                                    "Dunder names not allowed for this entity type")
            return
        
        if name.startswith('_') and not name.startswith('__'):
            if not rule.allow_private_prefix:
                self._add_violation(entity_type, name, line_number, rule,
                                    "Private prefix not allowed")
            # Strip prefix for convention check
            name = name.lstrip('_')
        
        # Check length
        if len(name) < rule.min_length:
            self._add_violation(entity_type, name, line_number, rule,
                                f"Name too short (min {rule.min_length} characters)")
            return
        
        if len(name) > rule.max_length:
            self._add_violation(entity_type, name, line_number, rule,
                                f"Name too long (max {rule.max_length} characters)")
            return
        
        # Check banned names
        if name in rule.banned_names:
            self._add_violation(entity_type, name, line_number, rule,
                                f"'{name}' is a banned name")
            return
        
        # Check prefix/suffix
        if rule.prefix and not name.startswith(rule.prefix):
            self._add_violation(entity_type, name, line_number, rule,
                                f"Name should start with '{rule.prefix}'",
                                f"{rule.prefix}{name}")
            return
        
        if rule.suffix and not name.endswith(rule.suffix):
            self._add_violation(entity_type, name, line_number, rule,
                                f"Name should end with '{rule.suffix}'",
                                f"{name}{rule.suffix}")
            return
        
        # Check convention
        if not self._matches_convention(name, rule.convention):
            suggestion = self._convert_to_convention(name, rule.convention, rule)
            self._add_violation(entity_type, name, line_number, rule,
                                f"Name should be {rule.convention.value}",
                                suggestion)
    
    def _matches_convention(self, name: str, convention: NamingConvention) -> bool:
        """Check if name matches naming convention."""
        if convention == NamingConvention.SNAKE_CASE:
            return bool(re.match(r'^[a-z][a-z0-9]*(_[a-z0-9]+)*$', name))
        elif convention == NamingConvention.CAMEL_CASE:
            return bool(re.match(r'^[a-z][a-zA-Z0-9]*$', name))
        elif convention == NamingConvention.PASCAL_CASE:
            return bool(re.match(r'^[A-Z][a-zA-Z0-9]*$', name))
        elif convention == NamingConvention.UPPER_SNAKE_CASE:
            return bool(re.match(r'^[A-Z][A-Z0-9]*(_[A-Z0-9]+)*$', name))
        elif convention == NamingConvention.KEBAB_CASE:
            return bool(re.match(r'^[a-z][a-z0-9]*(-[a-z0-9]+)*$', name))
        return True
    
    def _convert_to_convention(self, name: str, convention: NamingConvention,
                               rule: NamingRule) -> str:
        """Convert name to target convention."""
        # Split into words
        words = self._split_words(name)
        
        if convention == NamingConvention.SNAKE_CASE:
            converted = '_'.join(w.lower() for w in words)
        elif convention == NamingConvention.CAMEL_CASE:
            converted = words[0].lower() + ''.join(w.capitalize() for w in words[1:])
        elif convention == NamingConvention.PASCAL_CASE:
            converted = ''.join(w.capitalize() for w in words)
        elif convention == NamingConvention.UPPER_SNAKE_CASE:
            converted = '_'.join(w.upper() for w in words)
        elif convention == NamingConvention.KEBAB_CASE:
            converted = '-'.join(w.lower() for w in words)
        else:
            converted = name
        
        # Apply prefix/suffix
        if rule.prefix and not converted.startswith(rule.prefix):
            converted = rule.prefix + converted
        if rule.suffix and not converted.endswith(rule.suffix):
            converted = converted + rule.suffix
        
        return converted
    
    def _split_words(self, name: str) -> List[str]:
        """Split name into words."""
        # Handle different cases
        if '_' in name:
            return name.split('_')
        elif '-' in name:
            return name.split('-')
        else:
            # Split camel/pascal case
            words = []
            current = []
            for char in name:
                if char.isupper() and current:
                    words.append(''.join(current))
                    current = [char]
                else:
                    current.append(char)
            if current:
                words.append(''.join(current))
            return words
    
    def _add_violation(self, entity_type: EntityType, name: str, line_number: int,
                       rule: NamingRule, reason: str, suggestion: Optional[str] = None):
        """Add a naming violation."""
        self.violations.append(NamingViolation(
            entity_type=entity_type,
            entity_name=name,
            file_path=self.file_path,
            line_number=line_number,
            expected_convention=rule.convention,
            severity=Severity.ERROR,
            reason=reason,
            suggestion=suggestion
        ))


# ============================================================
# SPELLCHECK VALIDATOR
# ============================================================

class SpellcheckValidator(ast.NodeVisitor):
    """Validate spelling in Python code."""
    
    def __init__(self, config: NamingSpellcheckConfig, file_path: str):
        self.config = config
        self.file_path = file_path
        self.violations: List[SpellingViolation] = []
        self.common_misspellings: Dict[str, int] = defaultdict(int)
        
        # Initialize spellchecker
        self.dict_available = False
        try:
            self.spellchecker = enchant.Dict(self.config.spellcheck_language.value)
            self.dict_available = True
            
            # Add custom words
            for word in self.config.custom_dictionary:
                self.spellchecker.add(word)
            for word in self.config.technical_terms:
                self.spellchecker.add(word)
                
        except enchant.errors.DictNotFoundError:
            logger.warning(f"Spellcheck dictionary not found for {self.config.spellcheck_language.value}")
            self.spellchecker = None
    
    def validate(self, tree: ast.AST, source_lines: List[str]) -> Tuple[List[SpellingViolation], Dict[str, int]]:
        """Validate spelling in AST."""
        # Check docstring
        if self.config.check_docstrings:
            docstring = ast.get_docstring(tree)
            if docstring:
                self._check_text(docstring, 1, "module docstring")
        
        # Check comments
        if self.config.check_comments:
            self._check_comments(source_lines)
        
        self.visit(tree)
        
        return self.violations, dict(self.common_misspellings)
    
    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Visit function definition."""
        self._check_name(node.name, node.lineno, "function")
        
        if self.config.check_docstrings:
            docstring = ast.get_docstring(node)
            if docstring:
                self._check_text(docstring, node.lineno, "docstring")
        
        self.generic_visit(node)
    
    def visit_ClassDef(self, node: ast.ClassDef):
        """Visit class definition."""
        self._check_name(node.name, node.lineno, "class")
        
        if self.config.check_docstrings:
            docstring = ast.get_docstring(node)
            if docstring:
                self._check_text(docstring, node.lineno, "docstring")
        
        self.generic_visit(node)
    
    def visit_Assign(self, node: ast.Assign):
        """Visit assignment."""
        for target in node.targets:
            if isinstance(target, ast.Name):
                self._check_name(target.id, node.lineno, "variable")
        
        self.generic_visit(node)
    
    def visit_Constant(self, node: ast.Constant):
        """Visit constant (for string checking)."""
        if self.config.check_strings and isinstance(node.value, str):
            if len(node.value) > 3:  # Skip short strings
                self._check_text(node.value, node.lineno, "string")
        
        self.generic_visit(node)
    
    def _check_name(self, name: str, line_number: int, context: str):
        """Check spelling of a name."""
        # Skip ignored names
        if name in self.config.ignore_names:
            return
        
        # Skip names with underscores/camelCase - check individual words
        words = self._extract_words(name)
        
        for word in words:
            if len(word) <= 2:  # Skip short words
                continue
            
            if word.isupper():  # Skip acronyms
                continue
            
            self._check_word(word, line_number, f"{context} '{name}'")
    
    def _check_text(self, text: str, line_number: int, context: str):
        """Check spelling in text."""
        words = self._extract_words(text)
        
        for word in words:
            if len(word) <= 2:
                continue
            if word.isupper():
                continue
            
            self._check_word(word, line_number, context)
    
    def _check_comments(self, source_lines: List[str]):
        """Check spelling in comments."""
        for i, line in enumerate(source_lines, 1):
            # Find comments
            comment_match = re.search(r'#\s*(.*)$', line)
            if comment_match:
                comment = comment_match.group(1)
                self._check_text(comment, i, "comment")
    
    def _check_word(self, word: str, line_number: int, context: str):
        """Check a single word for spelling."""
        if not self.dict_available or not self.spellchecker:
            return
        
        # Check common misspellings first
        word_lower = word.lower()
        if word_lower in self.config.common_misspellings:
            self.common_misspellings[word_lower] += 1
            correction = self.config.common_misspellings[word_lower]
            self.violations.append(SpellingViolation(
                word=word,
                file_path=self.file_path,
                line_number=line_number,
                context=context,
                suggestions=[correction],
                severity=Severity.WARNING
            ))
            return
        
        # Check dictionary
        if not self.spellchecker.check(word):
            suggestions = self.spellchecker.suggest(word)[:5]
            self.violations.append(SpellingViolation(
                word=word,
                file_path=self.file_path,
                line_number=line_number,
                context=context,
                suggestions=suggestions,
                severity=Severity.INFO
            ))
    
    def _extract_words(self, text: str) -> List[str]:
        """Extract words from text (handling camelCase, snake_case, etc.)."""
        # Replace separators with spaces
        text = re.sub(r'[_\-.]', ' ', text)
        
        # Split camelCase
        text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)
        text = re.sub(r'([A-Z])([A-Z][a-z])', r'\1 \2', text)
        
        # Extract words (letters only)
        words = re.findall(r'[A-Za-z]+', text)
        
        return words


# ============================================================
# MAIN NAMING & SPELLCHECK VALIDATOR
# ============================================================

class NamingSpellcheckValidator:
    """
    Validates naming conventions and spelling in Python code.
    
    Features:
    - PEP 8 naming convention validation
    - Custom naming rules per entity type
    - Spell checking for identifiers, comments, and docstrings
    - Common misspelling detection
    - Banned name detection
    - Intelligent word extraction from camelCase/snake_case
    - Custom dictionary support
    - Technical term recognition
    """
    
    def __init__(self, config: NamingSpellcheckConfig):
        self.config = config
        self.state = StateManager(config.project_root / ".ai_state" / "naming_spellcheck_validator.json")
        
        logger.info("NamingSpellcheckValidator initialized")
    
    def validate(self) -> NamingSpellcheckReport:
        """Run complete naming and spellcheck validation."""
        logger.info("Starting naming and spellcheck validation...")
        
        report = NamingSpellcheckReport(
            project_name=self.config.project_root.name
        )
        
        # Find Python files
        python_files = list(self.config.project_root.rglob("*.py"))
        
        for file_path in python_files:
            if self._should_ignore(file_path):
                continue
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    source_lines = content.split('\n')
                
                tree = ast.parse(content)
                
                # Validate naming
                naming_validator = NamingValidator(self.config, str(file_path))
                naming_violations, entities = naming_validator.validate(tree)
                
                report.total_entities += entities
                report.naming_violations += len(naming_violations)
                report.naming_issues.extend(naming_violations)
                
                # Validate spelling
                if self.config.check_spelling:
                    spellcheck_validator = SpellcheckValidator(self.config, str(file_path))
                    spelling_violations, common = spellcheck_validator.validate(tree, source_lines)
                    
                    report.spelling_violations += len(spelling_violations)
                    report.spelling_issues.extend(spelling_violations)
                    
                    for word, count in common.items():
                        report.common_misspellings[word] = report.common_misspellings.get(word, 0) + count
                
                # Check banned names
                self._check_banned_names(report)
                
            except Exception as e:
                logger.warning(f"Failed to validate {file_path}: {e}")
        
        # Calculate overall score and grade
        report.overall_score = self._calculate_overall_score(report)
        report.grade = self._calculate_grade(report.overall_score)
        
        # Determine validity
        report.is_valid = self._determine_validity(report)
        
        # Generate summary and recommendations
        report.summary = self._generate_summary(report)
        report.recommendations = self._generate_recommendations(report)
        
        # Save report
        self._save_report(report)
        
        logger.info(f"Naming/spellcheck validation complete: {report.naming_violations} naming, {report.spelling_violations} spelling issues")
        
        return report
    
    def _check_banned_names(self, report: NamingSpellcheckReport):
        """Check for banned names across the project."""
        for violation in report.naming_issues:
            for entity_type, rule in self.config.naming_rules.items():
                if violation.entity_name in rule.banned_names:
                    report.banned_names_found.append((violation.file_path, violation.entity_name))
    
    def _should_ignore(self, file_path: Path) -> bool:
        """Check if file should be ignored."""
        path_str = str(file_path)
        for pattern in self.config.ignore_patterns:
            if pattern.replace('*', '') in path_str:
                return True
        return False
    
    def _calculate_overall_score(self, report: NamingSpellcheckReport) -> float:
        """Calculate overall naming/spelling score."""
        score = 100.0
        
        # Deduct for naming violations
        if report.total_entities > 0:
            naming_rate = (report.naming_violations / report.total_entities) * 100
            score -= naming_rate * 1.5
        
        # Deduct for spelling violations
        score -= report.spelling_violations * 0.5
        
        # Deduct for banned names
        score -= len(report.banned_names_found) * 5
        
        return max(0, min(100, score))
    
    def _calculate_grade(self, score: float) -> str:
        """Calculate letter grade from score."""
        if score >= 90:
            return "A"
        elif score >= 80:
            return "B"
        elif score >= 70:
            return "C"
        elif score >= 60:
            return "D"
        else:
            return "F"
    
    def _determine_validity(self, report: NamingSpellcheckReport) -> bool:
        """Determine if validation passes."""
        if self.config.fail_on_error and report.naming_violations > 0:
            return False
        if self.config.fail_on_spelling and report.spelling_violations > 0:
            return False
        if report.banned_names_found:
            return False
        return True
    
    def _generate_summary(self, report: NamingSpellcheckReport) -> str:
        """Generate validation summary."""
        if report.is_valid:
            return f"✅ Naming/spellcheck passed. Score: {report.overall_score:.1f} (Grade: {report.grade})"
        else:
            return f"❌ Issues found: {report.naming_violations} naming, {report.spelling_violations} spelling"
    
    def _generate_recommendations(self, report: NamingSpellcheckReport) -> List[str]:
        """Generate recommendations."""
        recommendations = []
        
        if report.naming_violations > 0:
            # Group by entity type
            by_type = defaultdict(int)
            for v in report.naming_issues:
                by_type[v.entity_type.value] += 1
            
            for entity_type, count in sorted(by_type.items(), key=lambda x: x[1], reverse=True)[:3]:
                recommendations.append(f"Fix {count} naming violations in {entity_type}s")
        
        if report.spelling_violations > 0:
            recommendations.append(f"Correct {report.spelling_violations} spelling errors")
        
        if report.common_misspellings:
            top_misspelling = sorted(report.common_misspellings.items(), key=lambda x: x[1], reverse=True)[0]
            recommendations.append(f"Common misspelling: '{top_misspelling[0]}' → '{self.config.common_misspellings.get(top_misspelling[0], '')}' ({top_misspelling[1]} occurrences)")
        
        if report.banned_names_found:
            recommendations.append(f"Replace {len(report.banned_names_found)} banned names")
        
        return recommendations[:5]
    
    def _save_report(self, report: NamingSpellcheckReport):
        """Save report to state."""
        reports = self.state.get('reports', [])
        reports.append({
            'timestamp': report.validated_at.isoformat(),
            'project': report.project_name,
            'is_valid': report.is_valid,
            'score': report.overall_score,
            'grade': report.grade,
            'naming_violations': report.naming_violations,
            'spelling_violations': report.spelling_violations,
            'banned_names': len(report.banned_names_found)
        })
        
        if len(reports) > 50:
            reports = reports[-50:]
        
        self.state.set('reports', reports)
        self.state.save()
    
    def export_report(self, report: NamingSpellcheckReport,
                      output_path: Optional[Path] = None,
                      format: str = 'markdown') -> str:
        """Export validation report."""
        
        if format == 'json':
            data = {
                'validated_at': report.validated_at.isoformat(),
                'project': report.project_name,
                'is_valid': report.is_valid,
                'score': report.overall_score,
                'grade': report.grade,
                'summary': report.summary,
                'statistics': {
                    'total_entities': report.total_entities,
                    'naming_violations': report.naming_violations,
                    'spelling_violations': report.spelling_violations,
                    'banned_names': len(report.banned_names_found)
                },
                'naming_issues': [
                    {
                        'entity_type': v.entity_type.value,
                        'entity_name': v.entity_name,
                        'file': v.file_path,
                        'line': v.line_number,
                        'expected': v.expected_convention.value,
                        'reason': v.reason,
                        'suggestion': v.suggestion
                    }
                    for v in report.naming_issues[:50]
                ],
                'spelling_issues': [
                    {
                        'word': s.word,
                        'file': s.file_path,
                        'line': s.line_number,
                        'context': s.context,
                        'suggestions': s.suggestions
                    }
                    for s in report.spelling_issues[:50]
                ],
                'common_misspellings': report.common_misspellings,
                'banned_names_found': report.banned_names_found,
                'recommendations': report.recommendations
            }
            
            content = json.dumps(data, indent=2)
            
        else:  # markdown
            lines = [
                f"# Naming & Spellcheck Validation Report",
                "",
                f"**Project:** {report.project_name}",
                f"**Validated:** {report.validated_at.strftime('%Y-%m-%d %H:%M:%S')}",
                f"**Score:** {report.overall_score:.1f} (Grade: {report.grade})",
                f"**Status:** {report.summary}",
                "",
                "## Summary",
                "",
                f"| Metric | Value |",
                f"|--------|-------|",
                f"| Total Entities | {report.total_entities} |",
                f"| Naming Violations | {report.naming_violations} |",
                f"| Spelling Violations | {report.spelling_violations} |",
                f"| Banned Names Found | {len(report.banned_names_found)} |",
                "",
            ]
            
            if report.naming_issues:
                lines.extend([
                    "## 📝 Naming Violations",
                    "",
                    "| Type | Name | File | Expected | Suggestion |",
                    "|------|------|------|----------|------------|",
                ])
                
                # Group by convention
                by_convention = defaultdict(list)
                for v in report.naming_issues:
                    by_convention[v.expected_convention.value].append(v)
                
                for convention, violations in by_convention.items():
                    for v in violations[:10]:
                        file_name = Path(v.file_path).name
                        lines.append(f"| {v.entity_type.value} | `{v.entity_name}` | {file_name}:{v.line_number} | {convention} | {v.suggestion or '-'} |")
                
                lines.append("")
            
            if report.spelling_issues:
                lines.extend([
                    "## 🔤 Spelling Issues",
                    "",
                    "| Word | File | Context | Suggestions |",
                    "|------|------|---------|-------------|",
                ])
                for s in report.spelling_issues[:20]:
                    file_name = Path(s.file_path).name
                    suggestions = ', '.join(s.suggestions[:3]) if s.suggestions else '-'
                    lines.append(f"| {s.word} | {file_name}:{s.line_number} | {s.context} | {suggestions} |")
                lines.append("")
            
            if report.common_misspellings:
                lines.extend([
                    "## 📊 Common Misspellings",
                    "",
                    "| Misspelling | Correction | Occurrences |",
                    "|-------------|------------|-------------|",
                ])
                for word, count in sorted(report.common_misspellings.items(), key=lambda x: x[1], reverse=True)[:10]:
                    correction = self.config.common_misspellings.get(word, '')
                    lines.append(f"| {word} | {correction} | {count} |")
                lines.append("")
            
            if report.banned_names_found:
                lines.extend([
                    "## 🚫 Banned Names Found",
                    "",
                ])
                for file_path, name in report.banned_names_found[:10]:
                    lines.append(f"- `{name}` in {Path(file_path).name}")
                lines.append("")
            
            if report.recommendations:
                lines.extend([
                    "## Recommendations",
                    "",
                ])
                for rec in report.recommendations:
                    lines.append(f"- {rec}")
                lines.append("")
            
            content = '\n'.join(lines)
        
        if output_path:
            output_path.write_text(content)
        
        return content
    
    def close(self):
        """Clean up resources."""
        self.state.save()
        logger.info("NamingSpellcheckValidator closed")


# ============================================================
# CLI ENTRY POINT
# ============================================================

def main():
    """CLI entry point for naming and spellcheck validator."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate naming conventions and spelling")
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--output", "-o", type=Path, help="Output report path")
    parser.add_argument("--format", choices=["json", "markdown"], default="markdown")
    parser.add_argument("--no-spellcheck", action="store_true", help="Disable spell checking")
    parser.add_argument("--language", choices=[l.value for l in SpellcheckLanguage],
                       default=SpellcheckLanguage.ENGLISH_US.value)
    parser.add_argument("--fail-on-spelling", action="store_true")
    parser.add_argument("--custom-dict", type=Path, help="Custom dictionary file (one word per line)")
    
    args = parser.parse_args()
    
    config = NamingSpellcheckConfig(
        project_root=args.project_root,
        check_spelling=not args.no_spellcheck,
        spellcheck_language=SpellcheckLanguage(args.language),
        fail_on_spelling=args.fail_on_spelling
    )
    
    if args.custom_dict and args.custom_dict.exists():
        config.custom_dictionary = args.custom_dict.read_text().strip().split('\n')
    
    validator = NamingSpellcheckValidator(config)
    
    report = validator.validate()
    
    output = validator.export_report(report, args.output, args.format)
    
    if not args.output:
        print(output)
    else:
        print(f"Report saved to {args.output}")
    
    print(f"\n{report.summary}")
    
    if config.fail_on_error and not report.is_valid:
        exit(1)
    
    validator.close()


if __name__ == "__main__":
    main()