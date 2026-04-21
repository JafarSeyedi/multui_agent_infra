#!/usr/bin/env python3
"""
Ruff Validator - Validates Python code style and quality using Ruff.

Part of the Quality tools (validators/ruff_validator.py)

This ruff_validator.py provides:

1. Comprehensive Rule Support - All Ruff rules including Pyflakes, pycodestyle, isort, pydocstyle, pyupgrade, flake8-annotations, bandit, bugbear, comprehensions, simplify, and more
2. Rule Category Mapping - Categorizes violations for better reporting
3. Auto-Fix Capability - Can automatically fix many violations
4. Fix Suggestions - Provides specific suggestions for each violation
5. Configurable Rules - Enable/disable specific rules or categories
6. Per-File Ignores - Ignore specific rules in specific files
7. JSON and Text Parsing - Parses both output formats
8. Quality Scoring - A-F grade based on violation severity
9. Comprehensive Reporting - Detailed violation statistics by rule and category
10. String Validation - Validate code snippets without files
11. Historical Tracking - Tracks validation trends over time
12. Security Focus - Higher weight for security-related violations

The Ruff validator ensures your codebase maintains high code quality standards and follows Python best practices.
"""

import json
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Set, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from ...shared.logger import get_logger
from ...shared.state_manager import StateManager

logger = get_logger(__name__)


# ============================================================
# ENUMS AND CONSTANTS
# ============================================================

class RuffRuleCategory(str, Enum):
    """Category of Ruff rule."""
    # Pyflakes (F)
    UNUSED_IMPORT = "unused_import"
    UNDEFINED_NAME = "undefined_name"
    REDEFINED = "redefined"
    UNUSED_VARIABLE = "unused_variable"
    STRING_FORMAT = "string_format"
    
    # pycodestyle (E, W)
    INDENTATION = "indentation"
    WHITESPACE = "whitespace"
    BLANK_LINE = "blank_line"
    LINE_LENGTH = "line_length"
    TRAILING_WHITESPACE = "trailing_whitespace"
    NEWLINE = "newline"
    
    # mccabe (C90)
    COMPLEXITY = "complexity"
    
    # isort (I)
    IMPORT_ORDER = "import_order"
    IMPORT_SORTING = "import_sorting"
    
    # pydocstyle (D)
    DOCSTRING = "docstring"
    
    # pyupgrade (UP)
    DEPRECATED_SYNTAX = "deprecated_syntax"
    MODERN_SYNTAX = "modern_syntax"
    
    # flake8-annotations (ANN)
    TYPE_ANNOTATION = "type_annotation"
    
    # flake8-bandit (S)
    SECURITY = "security"
    
    # flake8-bugbear (B)
    BUG_RISK = "bug_risk"
    
    # flake8-comprehensions (C4)
    COMPREHENSION = "comprehension"
    
    # flake8-simplify (SIM)
    SIMPLIFY = "simplify"
    
    # pylint (PL)
    PYLINT = "pylint"
    
    # tryceratops (TRY)
    EXCEPTION_HANDLING = "exception_handling"
    
    # flynt (FLY)
    F_STRING = "f_string"
    
    # numpy (NPY)
    NUMPY = "numpy"
    
    # pandas-vet (PD)
    PANDAS = "pandas"
    
    # perflint (PERF)
    PERFORMANCE = "performance"
    
    # refurb (FURB)
    REFACTOR = "refactor"
    
    # Other
    OTHER = "other"


class Severity(str, Enum):
    """Severity of Ruff violation."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class FixAvailability(str, Enum):
    """Availability of automatic fix."""
    ALWAYS = "always"
    SOMETIMES = "sometimes"
    NEVER = "never"
    UNKNOWN = "unknown"


# ============================================================
# DATA MODELS
# ============================================================

@dataclass
class RuffViolation:
    """A single Ruff violation."""
    file_path: str
    line_number: int
    column_number: int
    rule_code: str
    category: RuffRuleCategory
    severity: Severity
    message: str
    fix_available: FixAvailability = FixAvailability.UNKNOWN
    fix_suggestion: Optional[str] = None
    context: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __str__(self) -> str:
        return f"{self.file_path}:{self.line_number}:{self.column_number}: {self.rule_code}: {self.message}"


@dataclass
class FileViolations:
    """Violations for a single file."""
    file_path: str
    violations: List[RuffViolation] = field(default_factory=list)
    error_count: int = 0
    warning_count: int = 0
    fixable_count: int = 0


@dataclass
class RuffReport:
    """Complete Ruff validation report."""
    validated_at: datetime = field(default_factory=datetime.now)
    project_name: str = ""
    ruff_version: str = ""
    
    # Statistics
    total_files: int = 0
    files_with_violations: int = 0
    total_violations: int = 0
    violations_by_rule: Dict[str, int] = field(default_factory=dict)
    violations_by_category: Dict[str, int] = field(default_factory=dict)
    violations_by_file: Dict[str, int] = field(default_factory=dict)
    
    # Violations
    violations: List[RuffViolation] = field(default_factory=list)
    errors: List[RuffViolation] = field(default_factory=list)
    warnings: List[RuffViolation] = field(default_factory=list)
    
    # Fix statistics
    fixable_violations: int = 0
    auto_fixable_violations: int = 0
    
    # File details
    file_violations: Dict[str, FileViolations] = field(default_factory=dict)
    
    # Validation
    is_valid: bool = True
    overall_score: float = 0.0
    grade: str = "A"
    summary: str = ""
    recommendations: List[str] = field(default_factory=list)
    
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RuffValidatorConfig:
    """Configuration for Ruff validator."""
    project_root: Path
    config_file: Optional[Path] = None
    
    # Ruff options
    select: List[str] = field(default_factory=list)  # Rules to enable
    ignore: List[str] = field(default_factory=list)  # Rules to ignore
    extend_select: List[str] = field(default_factory=list)
    extend_ignore: List[str] = field(default_factory=list)
    
    # Predefined rule sets
    use_default_rules: bool = True
    enable_pyflakes: bool = True
    enable_pycodestyle: bool = True
    enable_isort: bool = True
    enable_pydocstyle: bool = False
    enable_pyupgrade: bool = True
    enable_flake8_annotations: bool = False
    enable_flake8_bandit: bool = True
    enable_flake8_bugbear: bool = True
    enable_flake8_comprehensions: bool = True
    enable_flake8_simplify: bool = True
    enable_mccabe: bool = True
    enable_perflint: bool = True
    
    # Complexity thresholds
    max_line_length: int = 100
    max_complexity: int = 10
    
    # Fix options
    auto_fix: bool = False
    fix_only: bool = False
    unsafe_fixes: bool = False
    show_fixes: bool = True
    
    # Target version
    target_version: str = "py310"
    
    # Ignore patterns
    ignore_patterns: List[str] = field(default_factory=lambda: [
        "__pycache__", "*.pyc", ".git", ".venv", "venv", "dist", "build",
        ".pytest_cache", ".mypy_cache", ".ruff_cache", "migrations", "alembic"
    ])
    
    # Per-file ignores
    per_file_ignores: Dict[str, List[str]] = field(default_factory=dict)
    
    # Validation
    fail_on_error: bool = True
    fail_on_warning: bool = False
    max_violations: int = 1000
    
    # Reporting
    generate_report: bool = True
    output_format: str = "markdown"
    show_context: bool = True
    max_violations_to_show: int = 50


# ============================================================
# RULE CATEGORY MAPPER
# ============================================================

class RuleCategoryMapper:
    """Map Ruff rule codes to categories."""
    
    CATEGORY_MAP = {
        # Pyflakes
        'F': RuffRuleCategory.UNUSED_IMPORT,
        'F401': RuffRuleCategory.UNUSED_IMPORT,
        'F402': RuffRuleCategory.UNUSED_IMPORT,
        'F403': RuffRuleCategory.UNUSED_IMPORT,
        'F404': RuffRuleCategory.UNUSED_IMPORT,
        'F405': RuffRuleCategory.UNDEFINED_NAME,
        'F406': RuffRuleCategory.UNDEFINED_NAME,
        'F407': RuffRuleCategory.UNDEFINED_NAME,
        'F501': RuffRuleCategory.STRING_FORMAT,
        'F502': RuffRuleCategory.STRING_FORMAT,
        'F503': RuffRuleCategory.STRING_FORMAT,
        'F504': RuffRuleCategory.STRING_FORMAT,
        'F505': RuffRuleCategory.STRING_FORMAT,
        'F506': RuffRuleCategory.STRING_FORMAT,
        'F507': RuffRuleCategory.STRING_FORMAT,
        'F508': RuffRuleCategory.STRING_FORMAT,
        'F509': RuffRuleCategory.STRING_FORMAT,
        'F521': RuffRuleCategory.STRING_FORMAT,
        'F522': RuffRuleCategory.STRING_FORMAT,
        'F523': RuffRuleCategory.STRING_FORMAT,
        'F524': RuffRuleCategory.STRING_FORMAT,
        'F525': RuffRuleCategory.STRING_FORMAT,
        'F541': RuffRuleCategory.STRING_FORMAT,
        'F601': RuffRuleCategory.UNUSED_VARIABLE,
        'F602': RuffRuleCategory.UNUSED_VARIABLE,
        'F621': RuffRuleCategory.REDEFINED,
        'F622': RuffRuleCategory.REDEFINED,
        'F631': RuffRuleCategory.UNUSED_VARIABLE,
        'F632': RuffRuleCategory.UNUSED_VARIABLE,
        'F633': RuffRuleCategory.UNUSED_VARIABLE,
        'F634': RuffRuleCategory.UNUSED_VARIABLE,
        'F701': RuffRuleCategory.OTHER,
        'F702': RuffRuleCategory.OTHER,
        'F704': RuffRuleCategory.OTHER,
        'F706': RuffRuleCategory.OTHER,
        'F707': RuffRuleCategory.OTHER,
        'F722': RuffRuleCategory.OTHER,
        'F821': RuffRuleCategory.UNDEFINED_NAME,
        'F822': RuffRuleCategory.UNDEFINED_NAME,
        'F823': RuffRuleCategory.UNDEFINED_NAME,
        'F831': RuffRuleCategory.OTHER,
        'F841': RuffRuleCategory.UNUSED_VARIABLE,
        'F842': RuffRuleCategory.UNUSED_VARIABLE,
        'F843': RuffRuleCategory.UNUSED_VARIABLE,
        'F901': RuffRuleCategory.OTHER,
        
        # pycodestyle
        'E': RuffRuleCategory.WHITESPACE,
        'E1': RuffRuleCategory.INDENTATION,
        'E2': RuffRuleCategory.WHITESPACE,
        'E3': RuffRuleCategory.BLANK_LINE,
        'E4': RuffRuleCategory.IMPORT_SORTING,
        'E5': RuffRuleCategory.LINE_LENGTH,
        'E7': RuffRuleCategory.OTHER,
        'E9': RuffRuleCategory.OTHER,
        'W': RuffRuleCategory.WHITESPACE,
        'W1': RuffRuleCategory.INDENTATION,
        'W2': RuffRuleCategory.WHITESPACE,
        'W3': RuffRuleCategory.BLANK_LINE,
        'W5': RuffRuleCategory.LINE_LENGTH,
        'W6': RuffRuleCategory.NEWLINE,
        
        # mccabe
        'C90': RuffRuleCategory.COMPLEXITY,
        'C901': RuffRuleCategory.COMPLEXITY,
        
        # isort
        'I': RuffRuleCategory.IMPORT_ORDER,
        'I001': RuffRuleCategory.IMPORT_ORDER,
        'I002': RuffRuleCategory.IMPORT_ORDER,
        
        # pydocstyle
        'D': RuffRuleCategory.DOCSTRING,
        'D1': RuffRuleCategory.DOCSTRING,
        'D2': RuffRuleCategory.DOCSTRING,
        'D3': RuffRuleCategory.DOCSTRING,
        'D4': RuffRuleCategory.DOCSTRING,
        
        # pyupgrade
        'UP': RuffRuleCategory.DEPRECATED_SYNTAX,
        'UP001': RuffRuleCategory.DEPRECATED_SYNTAX,
        'UP003': RuffRuleCategory.DEPRECATED_SYNTAX,
        'UP004': RuffRuleCategory.DEPRECATED_SYNTAX,
        'UP005': RuffRuleCategory.DEPRECATED_SYNTAX,
        'UP006': RuffRuleCategory.DEPRECATED_SYNTAX,
        'UP007': RuffRuleCategory.DEPRECATED_SYNTAX,
        'UP008': RuffRuleCategory.DEPRECATED_SYNTAX,
        'UP009': RuffRuleCategory.DEPRECATED_SYNTAX,
        'UP010': RuffRuleCategory.DEPRECATED_SYNTAX,
        'UP011': RuffRuleCategory.DEPRECATED_SYNTAX,
        'UP012': RuffRuleCategory.DEPRECATED_SYNTAX,
        'UP013': RuffRuleCategory.DEPRECATED_SYNTAX,
        'UP014': RuffRuleCategory.DEPRECATED_SYNTAX,
        'UP015': RuffRuleCategory.DEPRECATED_SYNTAX,
        'UP017': RuffRuleCategory.DEPRECATED_SYNTAX,
        'UP018': RuffRuleCategory.DEPRECATED_SYNTAX,
        'UP019': RuffRuleCategory.DEPRECATED_SYNTAX,
        'UP020': RuffRuleCategory.DEPRECATED_SYNTAX,
        'UP021': RuffRuleCategory.DEPRECATED_SYNTAX,
        'UP022': RuffRuleCategory.DEPRECATED_SYNTAX,
        'UP023': RuffRuleCategory.DEPRECATED_SYNTAX,
        'UP024': RuffRuleCategory.DEPRECATED_SYNTAX,
        'UP025': RuffRuleCategory.DEPRECATED_SYNTAX,
        'UP026': RuffRuleCategory.DEPRECATED_SYNTAX,
        'UP027': RuffRuleCategory.DEPRECATED_SYNTAX,
        'UP028': RuffRuleCategory.DEPRECATED_SYNTAX,
        'UP029': RuffRuleCategory.DEPRECATED_SYNTAX,
        'UP030': RuffRuleCategory.DEPRECATED_SYNTAX,
        'UP031': RuffRuleCategory.F_STRING,
        'UP032': RuffRuleCategory.F_STRING,
        'UP033': RuffRuleCategory.DEPRECATED_SYNTAX,
        'UP034': RuffRuleCategory.DEPRECATED_SYNTAX,
        'UP035': RuffRuleCategory.DEPRECATED_SYNTAX,
        'UP036': RuffRuleCategory.DEPRECATED_SYNTAX,
        'UP037': RuffRuleCategory.DEPRECATED_SYNTAX,
        'UP038': RuffRuleCategory.DEPRECATED_SYNTAX,
        'UP039': RuffRuleCategory.DEPRECATED_SYNTAX,
        
        # flake8-annotations
        'ANN': RuffRuleCategory.TYPE_ANNOTATION,
        'ANN001': RuffRuleCategory.TYPE_ANNOTATION,
        'ANN002': RuffRuleCategory.TYPE_ANNOTATION,
        'ANN003': RuffRuleCategory.TYPE_ANNOTATION,
        'ANN101': RuffRuleCategory.TYPE_ANNOTATION,
        'ANN102': RuffRuleCategory.TYPE_ANNOTATION,
        'ANN201': RuffRuleCategory.TYPE_ANNOTATION,
        'ANN202': RuffRuleCategory.TYPE_ANNOTATION,
        'ANN204': RuffRuleCategory.TYPE_ANNOTATION,
        'ANN205': RuffRuleCategory.TYPE_ANNOTATION,
        'ANN206': RuffRuleCategory.TYPE_ANNOTATION,
        'ANN401': RuffRuleCategory.TYPE_ANNOTATION,
        
        # flake8-bandit
        'S': RuffRuleCategory.SECURITY,
        'S101': RuffRuleCategory.SECURITY,
        'S102': RuffRuleCategory.SECURITY,
        'S103': RuffRuleCategory.SECURITY,
        'S104': RuffRuleCategory.SECURITY,
        'S105': RuffRuleCategory.SECURITY,
        'S106': RuffRuleCategory.SECURITY,
        'S107': RuffRuleCategory.SECURITY,
        'S108': RuffRuleCategory.SECURITY,
        'S109': RuffRuleCategory.SECURITY,
        'S110': RuffRuleCategory.SECURITY,
        'S111': RuffRuleCategory.SECURITY,
        'S112': RuffRuleCategory.SECURITY,
        'S113': RuffRuleCategory.SECURITY,
        'S201': RuffRuleCategory.SECURITY,
        'S202': RuffRuleCategory.SECURITY,
        'S301': RuffRuleCategory.SECURITY,
        'S302': RuffRuleCategory.SECURITY,
        'S303': RuffRuleCategory.SECURITY,
        'S304': RuffRuleCategory.SECURITY,
        'S305': RuffRuleCategory.SECURITY,
        'S306': RuffRuleCategory.SECURITY,
        'S307': RuffRuleCategory.SECURITY,
        'S308': RuffRuleCategory.SECURITY,
        'S309': RuffRuleCategory.SECURITY,
        'S310': RuffRuleCategory.SECURITY,
        'S311': RuffRuleCategory.SECURITY,
        'S312': RuffRuleCategory.SECURITY,
        'S313': RuffRuleCategory.SECURITY,
        'S314': RuffRuleCategory.SECURITY,
        'S315': RuffRuleCategory.SECURITY,
        'S316': RuffRuleCategory.SECURITY,
        'S317': RuffRuleCategory.SECURITY,
        'S318': RuffRuleCategory.SECURITY,
        'S319': RuffRuleCategory.SECURITY,
        'S320': RuffRuleCategory.SECURITY,
        'S321': RuffRuleCategory.SECURITY,
        'S322': RuffRuleCategory.SECURITY,
        'S323': RuffRuleCategory.SECURITY,
        'S324': RuffRuleCategory.SECURITY,
        'S401': RuffRuleCategory.SECURITY,
        'S402': RuffRuleCategory.SECURITY,
        'S403': RuffRuleCategory.SECURITY,
        'S404': RuffRuleCategory.SECURITY,
        'S405': RuffRuleCategory.SECURITY,
        'S406': RuffRuleCategory.SECURITY,
        'S407': RuffRuleCategory.SECURITY,
        'S408': RuffRuleCategory.SECURITY,
        'S409': RuffRuleCategory.SECURITY,
        'S410': RuffRuleCategory.SECURITY,
        'S411': RuffRuleCategory.SECURITY,
        'S412': RuffRuleCategory.SECURITY,
        'S413': RuffRuleCategory.SECURITY,
        'S415': RuffRuleCategory.SECURITY,
        'S501': RuffRuleCategory.SECURITY,
        'S502': RuffRuleCategory.SECURITY,
        'S503': RuffRuleCategory.SECURITY,
        'S504': RuffRuleCategory.SECURITY,
        'S505': RuffRuleCategory.SECURITY,
        'S506': RuffRuleCategory.SECURITY,
        'S507': RuffRuleCategory.SECURITY,
        'S508': RuffRuleCategory.SECURITY,
        'S509': RuffRuleCategory.SECURITY,
        'S601': RuffRuleCategory.SECURITY,
        'S602': RuffRuleCategory.SECURITY,
        'S603': RuffRuleCategory.SECURITY,
        'S604': RuffRuleCategory.SECURITY,
        'S605': RuffRuleCategory.SECURITY,
        'S606': RuffRuleCategory.SECURITY,
        'S607': RuffRuleCategory.SECURITY,
        'S608': RuffRuleCategory.SECURITY,
        'S609': RuffRuleCategory.SECURITY,
        'S610': RuffRuleCategory.SECURITY,
        'S611': RuffRuleCategory.SECURITY,
        'S612': RuffRuleCategory.SECURITY,
        'S701': RuffRuleCategory.SECURITY,
        'S702': RuffRuleCategory.SECURITY,
        
        # flake8-bugbear
        'B': RuffRuleCategory.BUG_RISK,
        'B001': RuffRuleCategory.BUG_RISK,
        'B002': RuffRuleCategory.BUG_RISK,
        'B003': RuffRuleCategory.BUG_RISK,
        'B004': RuffRuleCategory.BUG_RISK,
        'B005': RuffRuleCategory.BUG_RISK,
        'B006': RuffRuleCategory.BUG_RISK,
        'B007': RuffRuleCategory.BUG_RISK,
        'B008': RuffRuleCategory.BUG_RISK,
        'B009': RuffRuleCategory.BUG_RISK,
        'B010': RuffRuleCategory.BUG_RISK,
        'B011': RuffRuleCategory.BUG_RISK,
        'B012': RuffRuleCategory.BUG_RISK,
        'B013': RuffRuleCategory.BUG_RISK,
        'B014': RuffRuleCategory.BUG_RISK,
        'B015': RuffRuleCategory.BUG_RISK,
        'B016': RuffRuleCategory.BUG_RISK,
        'B017': RuffRuleCategory.BUG_RISK,
        'B018': RuffRuleCategory.BUG_RISK,
        'B019': RuffRuleCategory.BUG_RISK,
        'B020': RuffRuleCategory.BUG_RISK,
        'B021': RuffRuleCategory.BUG_RISK,
        'B022': RuffRuleCategory.BUG_RISK,
        'B023': RuffRuleCategory.BUG_RISK,
        'B024': RuffRuleCategory.BUG_RISK,
        'B025': RuffRuleCategory.BUG_RISK,
        'B026': RuffRuleCategory.BUG_RISK,
        'B027': RuffRuleCategory.BUG_RISK,
        'B028': RuffRuleCategory.BUG_RISK,
        'B029': RuffRuleCategory.BUG_RISK,
        'B030': RuffRuleCategory.BUG_RISK,
        'B031': RuffRuleCategory.BUG_RISK,
        'B032': RuffRuleCategory.BUG_RISK,
        'B033': RuffRuleCategory.BUG_RISK,
        'B034': RuffRuleCategory.BUG_RISK,
        'B035': RuffRuleCategory.BUG_RISK,
        'B901': RuffRuleCategory.BUG_RISK,
        'B902': RuffRuleCategory.BUG_RISK,
        'B903': RuffRuleCategory.BUG_RISK,
        'B904': RuffRuleCategory.BUG_RISK,
        'B905': RuffRuleCategory.BUG_RISK,
        
        # flake8-comprehensions
        'C4': RuffRuleCategory.COMPREHENSION,
        'C400': RuffRuleCategory.COMPREHENSION,
        'C401': RuffRuleCategory.COMPREHENSION,
        'C402': RuffRuleCategory.COMPREHENSION,
        'C403': RuffRuleCategory.COMPREHENSION,
        'C404': RuffRuleCategory.COMPREHENSION,
        'C405': RuffRuleCategory.COMPREHENSION,
        'C406': RuffRuleCategory.COMPREHENSION,
        'C407': RuffRuleCategory.COMPREHENSION,
        'C408': RuffRuleCategory.COMPREHENSION,
        'C409': RuffRuleCategory.COMPREHENSION,
        'C410': RuffRuleCategory.COMPREHENSION,
        'C411': RuffRuleCategory.COMPREHENSION,
        'C412': RuffRuleCategory.COMPREHENSION,
        'C413': RuffRuleCategory.COMPREHENSION,
        'C414': RuffRuleCategory.COMPREHENSION,
        'C415': RuffRuleCategory.COMPREHENSION,
        'C416': RuffRuleCategory.COMPREHENSION,
        'C417': RuffRuleCategory.COMPREHENSION,
        'C418': RuffRuleCategory.COMPREHENSION,
        'C419': RuffRuleCategory.COMPREHENSION,
        
        # flake8-simplify
        'SIM': RuffRuleCategory.SIMPLIFY,
        'SIM101': RuffRuleCategory.SIMPLIFY,
        'SIM102': RuffRuleCategory.SIMPLIFY,
        'SIM103': RuffRuleCategory.SIMPLIFY,
        'SIM104': RuffRuleCategory.SIMPLIFY,
        'SIM105': RuffRuleCategory.SIMPLIFY,
        'SIM106': RuffRuleCategory.SIMPLIFY,
        'SIM107': RuffRuleCategory.SIMPLIFY,
        'SIM108': RuffRuleCategory.SIMPLIFY,
        'SIM109': RuffRuleCategory.SIMPLIFY,
        'SIM110': RuffRuleCategory.SIMPLIFY,
        'SIM111': RuffRuleCategory.SIMPLIFY,
        'SIM112': RuffRuleCategory.SIMPLIFY,
        'SIM113': RuffRuleCategory.SIMPLIFY,
        'SIM114': RuffRuleCategory.SIMPLIFY,
        'SIM115': RuffRuleCategory.SIMPLIFY,
        'SIM116': RuffRuleCategory.SIMPLIFY,
        'SIM117': RuffRuleCategory.SIMPLIFY,
        'SIM118': RuffRuleCategory.SIMPLIFY,
        'SIM119': RuffRuleCategory.SIMPLIFY,
        'SIM120': RuffRuleCategory.SIMPLIFY,
        'SIM121': RuffRuleCategory.SIMPLIFY,
        'SIM122': RuffRuleCategory.SIMPLIFY,
        'SIM123': RuffRuleCategory.SIMPLIFY,
        'SIM201': RuffRuleCategory.SIMPLIFY,
        'SIM202': RuffRuleCategory.SIMPLIFY,
        'SIM203': RuffRuleCategory.SIMPLIFY,
        'SIM204': RuffRuleCategory.SIMPLIFY,
        'SIM205': RuffRuleCategory.SIMPLIFY,
        'SIM206': RuffRuleCategory.SIMPLIFY,
        'SIM207': RuffRuleCategory.SIMPLIFY,
        'SIM208': RuffRuleCategory.SIMPLIFY,
        'SIM209': RuffRuleCategory.SIMPLIFY,
        'SIM210': RuffRuleCategory.SIMPLIFY,
        'SIM211': RuffRuleCategory.SIMPLIFY,
        'SIM212': RuffRuleCategory.SIMPLIFY,
        'SIM213': RuffRuleCategory.SIMPLIFY,
        'SIM214': RuffRuleCategory.SIMPLIFY,
        'SIM215': RuffRuleCategory.SIMPLIFY,
        'SIM216': RuffRuleCategory.SIMPLIFY,
        'SIM217': RuffRuleCategory.SIMPLIFY,
        'SIM218': RuffRuleCategory.SIMPLIFY,
        'SIM219': RuffRuleCategory.SIMPLIFY,
        'SIM220': RuffRuleCategory.SIMPLIFY,
        'SIM221': RuffRuleCategory.SIMPLIFY,
        'SIM222': RuffRuleCategory.SIMPLIFY,
        'SIM223': RuffRuleCategory.SIMPLIFY,
        'SIM224': RuffRuleCategory.SIMPLIFY,
        'SIM225': RuffRuleCategory.SIMPLIFY,
        'SIM226': RuffRuleCategory.SIMPLIFY,
        'SIM227': RuffRuleCategory.SIMPLIFY,
        'SIM228': RuffRuleCategory.SIMPLIFY,
        'SIM229': RuffRuleCategory.SIMPLIFY,
        'SIM230': RuffRuleCategory.SIMPLIFY,
        'SIM231': RuffRuleCategory.SIMPLIFY,
        'SIM232': RuffRuleCategory.SIMPLIFY,
        'SIM233': RuffRuleCategory.SIMPLIFY,
        'SIM234': RuffRuleCategory.SIMPLIFY,
        'SIM235': RuffRuleCategory.SIMPLIFY,
        'SIM236': RuffRuleCategory.SIMPLIFY,
        'SIM237': RuffRuleCategory.SIMPLIFY,
        'SIM238': RuffRuleCategory.SIMPLIFY,
        'SIM239': RuffRuleCategory.SIMPLIFY,
        'SIM240': RuffRuleCategory.SIMPLIFY,
        'SIM241': RuffRuleCategory.SIMPLIFY,
        'SIM242': RuffRuleCategory.SIMPLIFY,
        'SIM243': RuffRuleCategory.SIMPLIFY,
        'SIM244': RuffRuleCategory.SIMPLIFY,
        'SIM245': RuffRuleCategory.SIMPLIFY,
        'SIM246': RuffRuleCategory.SIMPLIFY,
        'SIM247': RuffRuleCategory.SIMPLIFY,
        'SIM248': RuffRuleCategory.SIMPLIFY,
        'SIM249': RuffRuleCategory.SIMPLIFY,
        'SIM250': RuffRuleCategory.SIMPLIFY,
        
        # pylint
        'PL': RuffRuleCategory.PYLINT,
        'PLC': RuffRuleCategory.PYLINT,
        'PLE': RuffRuleCategory.PYLINT,
        'PLR': RuffRuleCategory.PYLINT,
        'PLW': RuffRuleCategory.PYLINT,
        
        # tryceratops
        'TRY': RuffRuleCategory.EXCEPTION_HANDLING,
        'TRY001': RuffRuleCategory.EXCEPTION_HANDLING,
        'TRY002': RuffRuleCategory.EXCEPTION_HANDLING,
        'TRY003': RuffRuleCategory.EXCEPTION_HANDLING,
        'TRY004': RuffRuleCategory.EXCEPTION_HANDLING,
        'TRY005': RuffRuleCategory.EXCEPTION_HANDLING,
        'TRY006': RuffRuleCategory.EXCEPTION_HANDLING,
        'TRY007': RuffRuleCategory.EXCEPTION_HANDLING,
        'TRY008': RuffRuleCategory.EXCEPTION_HANDLING,
        'TRY009': RuffRuleCategory.EXCEPTION_HANDLING,
        'TRY010': RuffRuleCategory.EXCEPTION_HANDLING,
        'TRY011': RuffRuleCategory.EXCEPTION_HANDLING,
        'TRY012': RuffRuleCategory.EXCEPTION_HANDLING,
        'TRY013': RuffRuleCategory.EXCEPTION_HANDLING,
        'TRY014': RuffRuleCategory.EXCEPTION_HANDLING,
        'TRY015': RuffRuleCategory.EXCEPTION_HANDLING,
        'TRY016': RuffRuleCategory.EXCEPTION_HANDLING,
        'TRY017': RuffRuleCategory.EXCEPTION_HANDLING,
        'TRY018': RuffRuleCategory.EXCEPTION_HANDLING,
        'TRY019': RuffRuleCategory.EXCEPTION_HANDLING,
        'TRY020': RuffRuleCategory.EXCEPTION_HANDLING,
        'TRY021': RuffRuleCategory.EXCEPTION_HANDLING,
        'TRY022': RuffRuleCategory.EXCEPTION_HANDLING,
        'TRY023': RuffRuleCategory.EXCEPTION_HANDLING,
        'TRY024': RuffRuleCategory.EXCEPTION_HANDLING,
        'TRY025': RuffRuleCategory.EXCEPTION_HANDLING,
        'TRY026': RuffRuleCategory.EXCEPTION_HANDLING,
        'TRY027': RuffRuleCategory.EXCEPTION_HANDLING,
        'TRY028': RuffRuleCategory.EXCEPTION_HANDLING,
        'TRY029': RuffRuleCategory.EXCEPTION_HANDLING,
        'TRY030': RuffRuleCategory.EXCEPTION_HANDLING,
        
        # flynt
        'FLY': RuffRuleCategory.F_STRING,
        'FLY001': RuffRuleCategory.F_STRING,
        'FLY002': RuffRuleCategory.F_STRING,
        'FLY003': RuffRuleCategory.F_STRING,
        'FLY004': RuffRuleCategory.F_STRING,
        'FLY005': RuffRuleCategory.F_STRING,
        'FLY006': RuffRuleCategory.F_STRING,
        'FLY007': RuffRuleCategory.F_STRING,
        'FLY008': RuffRuleCategory.F_STRING,
        'FLY009': RuffRuleCategory.F_STRING,
        'FLY010': RuffRuleCategory.F_STRING,
        
        # numpy
        'NPY': RuffRuleCategory.NUMPY,
        'NPY001': RuffRuleCategory.NUMPY,
        'NPY002': RuffRuleCategory.NUMPY,
        'NPY003': RuffRuleCategory.NUMPY,
        
        # pandas-vet
        'PD': RuffRuleCategory.PANDAS,
        'PD001': RuffRuleCategory.PANDAS,
        'PD002': RuffRuleCategory.PANDAS,
        'PD003': RuffRuleCategory.PANDAS,
        'PD004': RuffRuleCategory.PANDAS,
        'PD005': RuffRuleCategory.PANDAS,
        'PD006': RuffRuleCategory.PANDAS,
        'PD007': RuffRuleCategory.PANDAS,
        'PD008': RuffRuleCategory.PANDAS,
        'PD009': RuffRuleCategory.PANDAS,
        'PD010': RuffRuleCategory.PANDAS,
        'PD011': RuffRuleCategory.PANDAS,
        'PD012': RuffRuleCategory.PANDAS,
        'PD013': RuffRuleCategory.PANDAS,
        'PD014': RuffRuleCategory.PANDAS,
        'PD015': RuffRuleCategory.PANDAS,
        'PD016': RuffRuleCategory.PANDAS,
        'PD017': RuffRuleCategory.PANDAS,
        'PD018': RuffRuleCategory.PANDAS,
        'PD019': RuffRuleCategory.PANDAS,
        'PD020': RuffRuleCategory.PANDAS,
        'PD021': RuffRuleCategory.PANDAS,
        'PD022': RuffRuleCategory.PANDAS,
        'PD023': RuffRuleCategory.PANDAS,
        'PD024': RuffRuleCategory.PANDAS,
        'PD025': RuffRuleCategory.PANDAS,
        'PD026': RuffRuleCategory.PANDAS,
        'PD027': RuffRuleCategory.PANDAS,
        'PD028': RuffRuleCategory.PANDAS,
        'PD029': RuffRuleCategory.PANDAS,
        'PD030': RuffRuleCategory.PANDAS,
        
        # perflint
        'PERF': RuffRuleCategory.PERFORMANCE,
        'PERF001': RuffRuleCategory.PERFORMANCE,
        'PERF002': RuffRuleCategory.PERFORMANCE,
        'PERF003': RuffRuleCategory.PERFORMANCE,
        'PERF004': RuffRuleCategory.PERFORMANCE,
        'PERF005': RuffRuleCategory.PERFORMANCE,
        'PERF006': RuffRuleCategory.PERFORMANCE,
        'PERF007': RuffRuleCategory.PERFORMANCE,
        'PERF008': RuffRuleCategory.PERFORMANCE,
        'PERF009': RuffRuleCategory.PERFORMANCE,
        'PERF010': RuffRuleCategory.PERFORMANCE,
        'PERF011': RuffRuleCategory.PERFORMANCE,
        'PERF012': RuffRuleCategory.PERFORMANCE,
        'PERF013': RuffRuleCategory.PERFORMANCE,
        'PERF014': RuffRuleCategory.PERFORMANCE,
        'PERF015': RuffRuleCategory.PERFORMANCE,
        'PERF016': RuffRuleCategory.PERFORMANCE,
        'PERF017': RuffRuleCategory.PERFORMANCE,
        'PERF018': RuffRuleCategory.PERFORMANCE,
        'PERF019': RuffRuleCategory.PERFORMANCE,
        'PERF020': RuffRuleCategory.PERFORMANCE,
        
        # refurb
        'FURB': RuffRuleCategory.REFACTOR,
        'FURB001': RuffRuleCategory.REFACTOR,
        'FURB002': RuffRuleCategory.REFACTOR,
        'FURB003': RuffRuleCategory.REFACTOR,
        'FURB004': RuffRuleCategory.REFACTOR,
        'FURB005': RuffRuleCategory.REFACTOR,
        'FURB006': RuffRuleCategory.REFACTOR,
        'FURB007': RuffRuleCategory.REFACTOR,
        'FURB008': RuffRuleCategory.REFACTOR,
        'FURB009': RuffRuleCategory.REFACTOR,
        'FURB010': RuffRuleCategory.REFACTOR,
        'FURB011': RuffRuleCategory.REFACTOR,
        'FURB012': RuffRuleCategory.REFACTOR,
        'FURB013': RuffRuleCategory.REFACTOR,
        'FURB014': RuffRuleCategory.REFACTOR,
        'FURB015': RuffRuleCategory.REFACTOR,
        'FURB016': RuffRuleCategory.REFACTOR,
        'FURB017': RuffRuleCategory.REFACTOR,
        'FURB018': RuffRuleCategory.REFACTOR,
        'FURB019': RuffRuleCategory.REFACTOR,
        'FURB020': RuffRuleCategory.REFACTOR,
        'FURB021': RuffRuleCategory.REFACTOR,
        'FURB022': RuffRuleCategory.REFACTOR,
        'FURB023': RuffRuleCategory.REFACTOR,
        'FURB024': RuffRuleCategory.REFACTOR,
        'FURB025': RuffRuleCategory.REFACTOR,
        'FURB026': RuffRuleCategory.REFACTOR,
        'FURB027': RuffRuleCategory.REFACTOR,
        'FURB028': RuffRuleCategory.REFACTOR,
        'FURB029': RuffRuleCategory.REFACTOR,
        'FURB030': RuffRuleCategory.REFACTOR,
        'FURB031': RuffRuleCategory.REFACTOR,
        'FURB032': RuffRuleCategory.REFACTOR,
        'FURB033': RuffRuleCategory.REFACTOR,
        'FURB034': RuffRuleCategory.REFACTOR,
        'FURB035': RuffRuleCategory.REFACTOR,
        'FURB036': RuffRuleCategory.REFACTOR,
        'FURB037': RuffRuleCategory.REFACTOR,
        'FURB038': RuffRuleCategory.REFACTOR,
        'FURB039': RuffRuleCategory.REFACTOR,
        'FURB040': RuffRuleCategory.REFACTOR,
        'FURB041': RuffRuleCategory.REFACTOR,
        'FURB042': RuffRuleCategory.REFACTOR,
        'FURB043': RuffRuleCategory.REFACTOR,
        'FURB044': RuffRuleCategory.REFACTOR,
        'FURB045': RuffRuleCategory.REFACTOR,
        'FURB046': RuffRuleCategory.REFACTOR,
        'FURB047': RuffRuleCategory.REFACTOR,
        'FURB048': RuffRuleCategory.REFACTOR,
        'FURB049': RuffRuleCategory.REFACTOR,
        'FURB050': RuffRuleCategory.REFACTOR,
        'FURB051': RuffRuleCategory.REFACTOR,
        'FURB052': RuffRuleCategory.REFACTOR,
        'FURB053': RuffRuleCategory.REFACTOR,
        'FURB054': RuffRuleCategory.REFACTOR,
        'FURB055': RuffRuleCategory.REFACTOR,
        'FURB056': RuffRuleCategory.REFACTOR,
        'FURB057': RuffRuleCategory.REFACTOR,
        'FURB058': RuffRuleCategory.REFACTOR,
        'FURB059': RuffRuleCategory.REFACTOR,
        'FURB060': RuffRuleCategory.REFACTOR,
        'FURB061': RuffRuleCategory.REFACTOR,
        'FURB062': RuffRuleCategory.REFACTOR,
        'FURB063': RuffRuleCategory.REFACTOR,
        'FURB064': RuffRuleCategory.REFACTOR,
        'FURB065': RuffRuleCategory.REFACTOR,
        'FURB066': RuffRuleCategory.REFACTOR,
        'FURB067': RuffRuleCategory.REFACTOR,
        'FURB068': RuffRuleCategory.REFACTOR,
        'FURB069': RuffRuleCategory.REFACTOR,
        'FURB070': RuffRuleCategory.REFACTOR,
        'FURB071': RuffRuleCategory.REFACTOR,
        'FURB072': RuffRuleCategory.REFACTOR,
        'FURB073': RuffRuleCategory.REFACTOR,
        'FURB074': RuffRuleCategory.REFACTOR,
        'FURB075': RuffRuleCategory.REFACTOR,
        'FURB076': RuffRuleCategory.REFACTOR,
        'FURB077': RuffRuleCategory.REFACTOR,
        'FURB078': RuffRuleCategory.REFACTOR,
        'FURB079': RuffRuleCategory.REFACTOR,
        'FURB080': RuffRuleCategory.REFACTOR,
        'FURB081': RuffRuleCategory.REFACTOR,
        'FURB082': RuffRuleCategory.REFACTOR,
        'FURB083': RuffRuleCategory.REFACTOR,
        'FURB084': RuffRuleCategory.REFACTOR,
        'FURB085': RuffRuleCategory.REFACTOR,
        'FURB086': RuffRuleCategory.REFACTOR,
        'FURB087': RuffRuleCategory.REFACTOR,
        'FURB088': RuffRuleCategory.REFACTOR,
        'FURB089': RuffRuleCategory.REFACTOR,
        'FURB090': RuffRuleCategory.REFACTOR,
        'FURB091': RuffRuleCategory.REFACTOR,
        'FURB092': RuffRuleCategory.REFACTOR,
        'FURB093': RuffRuleCategory.REFACTOR,
        'FURB094': RuffRuleCategory.REFACTOR,
        'FURB095': RuffRuleCategory.REFACTOR,
        'FURB096': RuffRuleCategory.REFACTOR,
        'FURB097': RuffRuleCategory.REFACTOR,
        'FURB098': RuffRuleCategory.REFACTOR,
        'FURB099': RuffRuleCategory.REFACTOR,
        'FURB100': RuffRuleCategory.REFACTOR,
    }
    
    @classmethod
    def get_category(cls, rule_code: str) -> RuffRuleCategory:
        """Get category for a rule code."""
        if rule_code in cls.CATEGORY_MAP:
            return cls.CATEGORY_MAP[rule_code]
        
        # Try prefix matching
        prefix = rule_code[0] if rule_code else ''
        if prefix in cls.CATEGORY_MAP:
            return cls.CATEGORY_MAP[prefix]
        
        if len(rule_code) >= 2:
            prefix2 = rule_code[:2]
            if prefix2 in cls.CATEGORY_MAP:
                return cls.CATEGORY_MAP[prefix2]
        
        if len(rule_code) >= 3:
            prefix3 = rule_code[:3]
            if prefix3 in cls.CATEGORY_MAP:
                return cls.CATEGORY_MAP[prefix3]
        
        return RuffRuleCategory.OTHER


# ============================================================
# RUFF OUTPUT PARSER
# ============================================================

class RuffOutputParser:
    """Parse Ruff output into structured violations."""
    
    # Suggestions for common violations
    VIOLATION_SUGGESTIONS = {
        'F401': "Remove unused import or use it in your code",
        'F403': "Replace 'from module import *' with explicit imports",
        'F405': "Import the name explicitly or define it",
        'F821': "Define the variable or import it",
        'F841': "Remove unused variable or prefix with underscore",
        'E501': f"Break long line into multiple lines",
        'E711': "Use 'is None' instead of '== None'",
        'E712': "Use 'is not None' instead of '!= None'",
        'W291': "Remove trailing whitespace",
        'W293': "Remove blank line whitespace",
        'I001': "Sort imports using isort",
        'D100': "Add module docstring",
        'D101': "Add class docstring",
        'D102': "Add method docstring",
        'D103': "Add function docstring",
        'D104': "Add package docstring",
        'D105': "Add docstring for magic method",
        'D106': "Add docstring for nested class",
        'D107': "Add docstring for __init__ method",
        'ANN001': "Add type annotation for function argument",
        'ANN002': "Add type annotation for *args",
        'ANN003': "Add type annotation for **kwargs",
        'ANN101': "Add 'self' type annotation",
        'ANN102': "Add 'cls' type annotation",
        'ANN201': "Add return type annotation",
        'ANN202': "Add return type annotation for __init__",
        'ANN204': "Add return type annotation for magic method",
        'ANN205': "Add return type annotation for staticmethod",
        'ANN206': "Add return type annotation for classmethod",
        'ANN401': "Replace 'Any' with more specific type",
        'B006': "Don't use mutable default arguments",
        'B007': "Remove unused loop control variable",
        'B008': "Don't call functions in default arguments",
        'B009': "Use 'getattr' with default instead of hasattr",
        'B010': "Use 'attr' instead of 'getattr' with constant",
        'B011': "Don't use 'assert False' - raise an exception",
        'B012': "Don't use 'return' in finally block",
        'B013': "Don't use 'except:' without exception type",
        'B014': "Use 'Exception' instead of 'BaseException'",
        'B015': "Don't compare with literals using 'is'",
        'B016': "Don't raise StopIteration in generator",
        'B017': "Don't use 'assertRaises(Exception)'",
        'B018': "Don't assign to expression",
        'B019': "Don't use 'functools.lru_cache' on methods",
        'B020': "Don't loop over 'dict.items()' and modify dict",
        'B021': "Don't use 'f-string' as docstring",
        'B022': "Don't use 'yield' in context manager",
        'B023': "Don't use 'return' in __init__",
        'B024': "Don't use 'is' to compare types",
        'B025': "Don't use 'except:' without exception type",
        'B026': "Don't use 'raise' without exception",
        'B027': "Don't use 'return' in generator",
        'B028': "Don't use 'yield' in __init__",
        'B029': "Don't use 'except:' without exception type",
        'B030': "Don't use 'is' to compare literals",
        'B031': "Don't use 'yield' in __del__",
        'B032': "Don't use 'is' to compare types",
        'B033': "Don't use 'is' to compare literals",
        'B034': "Don't use 'is' to compare types",
        'B035': "Don't use 'is' to compare literals",
        'B901': "Use 'yield from' instead of 'yield' in loop",
        'B902': "Use 'yield from' instead of 'yield' in loop",
        'B903': "Use 'yield from' instead of 'yield' in loop",
        'B904': "Use 'raise ... from ...' to chain exceptions",
        'B905': "Use 'zip' with strict=True",
        'C400': "Use list comprehension instead of for loop",
        'C401': "Use set comprehension instead of for loop",
        'C402': "Use dict comprehension instead of for loop",
        'C403': "Use set comprehension instead of for loop",
        'C404': "Use dict comprehension instead of for loop",
        'C405': "Use list comprehension instead of for loop",
        'C406': "Use dict comprehension instead of for loop",
        'C407': "Use list comprehension instead of for loop",
        'C408': "Use literal instead of constructor",
        'C409': "Use tuple instead of list for constant",
        'C410': "Use list instead of tuple for variable",
        'C411': "Use list comprehension instead of for loop",
        'C412': "Use list comprehension instead of for loop",
        'C413': "Use list comprehension instead of for loop",
        'C414': "Use list comprehension instead of for loop",
        'C415': "Use list comprehension instead of for loop",
        'C416': "Use list comprehension instead of for loop",
        'C417': "Use list comprehension instead of for loop",
        'C418': "Use list comprehension instead of for loop",
        'C419': "Use list comprehension instead of for loop",
        'SIM101': "Use 'is' instead of '==' for None",
        'SIM102': "Use 'if a:' instead of 'if a == True:'",
        'SIM103': "Use 'return a' instead of 'if a: return True else: return False'",
        'SIM104': "Use 'yield from' instead of 'for x in y: yield x'",
        'SIM105': "Use 'contextlib.suppress' instead of try/except/pass",
        'SIM106': "Use 'raise from' instead of 'raise'",
        'SIM107': "Use 'try/except/else' instead of 'try/except'",
        'SIM108': "Use ternary operator instead of if/else",
        'SIM109': "Use 'if a' instead of 'if a == True'",
        'SIM110': "Use 'any' instead of loop",
        'SIM111': "Use 'all' instead of loop",
        'SIM112': "Use 'os.environ' instead of 'os.getenv'",
        'SIM113': "Use 'enumerate' instead of range(len)",
        'SIM114': "Use 'if a:' instead of 'if a == True'",
        'SIM115': "Use 'open' context manager",
        'SIM116': "Use 'if a:' instead of 'if a == True'",
        'SIM117': "Combine 'with' statements",
        'SIM118': "Use 'key in dict' instead of 'key in dict.keys()'",
        'SIM119': "Use 'dataclass' instead of manual __init__",
        'SIM120': "Use 'isinstance' instead of 'type'",
        'SIM121': "Use 'if a:' instead of 'if a == True'",
        'SIM122': "Use 'if a:' instead of 'if a == True'",
        'SIM123': "Use 'if a:' instead of 'if a == True'",
        'SIM201': "Use 'if a:' instead of 'if a == True'",
        'SIM202': "Use 'if a:' instead of 'if a == True'",
        'SIM203': "Use 'if a:' instead of 'if a == True'",
        'SIM204': "Use 'if a:' instead of 'if a == True'",
        'SIM205': "Use 'if a:' instead of 'if a == True'",
        'SIM206': "Use 'if a:' instead of 'if a == True'",
        'SIM207': "Use 'if a:' instead of 'if a == True'",
        'SIM208': "Use 'if a:' instead of 'if a == True'",
        'SIM209': "Use 'if a:' instead of 'if a == True'",
        'SIM210': "Use 'if a:' instead of 'if a == True'",
        'TRY001': "Use 'raise' without exception type",
        'TRY002': "Use 'raise' without exception type",
        'TRY003': "Use 'raise' without exception type",
        'TRY004': "Use 'raise' without exception type",
        'PERF001': "Use 'items()' instead of 'keys()' and lookup",
        'PERF002': "Use 'list' instead of 'list copy'",
        'PERF003': "Use 'dict' instead of 'dict copy'",
        'PERF004': "Use 'set' instead of 'set copy'",
        'PERF005': "Use 'tuple' instead of 'tuple copy'",
        'PERF006': "Use 'list' instead of 'list copy'",
        'PERF007': "Use 'dict' instead of 'dict copy'",
        'PERF008': "Use 'set' instead of 'set copy'",
        'PERF009': "Use 'tuple' instead of 'tuple copy'",
        'PERF010': "Use 'list' instead of 'list copy'",
        'PERF011': "Use 'dict' instead of 'dict copy'",
        'PERF012': "Use 'set' instead of 'set copy'",
        'PERF013': "Use 'tuple' instead of 'tuple copy'",
        'PERF014': "Use 'list' instead of 'list copy'",
        'PERF015': "Use 'dict' instead of 'dict copy'",
        'PERF016': "Use 'set' instead of 'set copy'",
        'PERF017': "Use 'tuple' instead of 'tuple copy'",
        'PERF018': "Use 'list' instead of 'list copy'",
        'PERF019': "Use 'dict' instead of 'dict copy'",
        'PERF020': "Use 'set' instead of 'set copy'",
    }
    
    def parse(self, output: str) -> List[RuffViolation]:
        """Parse Ruff output into RuffViolation objects."""
        violations = []
        
        for line in output.strip().split('\n'):
            if not line.strip():
                continue
            
            violation = self._parse_line(line)
            if violation:
                violations.append(violation)
        
        return violations
    
    def parse_json(self, json_output: str) -> List[RuffViolation]:
        """Parse Ruff JSON output."""
        violations = []
        
        try:
            data = json.loads(json_output)
            
            for item in data:
                violation = RuffViolation(
                    file_path=item.get('filename', ''),
                    line_number=item.get('location', {}).get('row', 0),
                    column_number=item.get('location', {}).get('column', 0),
                    rule_code=item.get('code', ''),
                    category=RuleCategoryMapper.get_category(item.get('code', '')),
                    severity=Severity.ERROR,
                    message=item.get('message', ''),
                    fix_available=self._parse_fix_availability(item.get('fix')),
                    fix_suggestion=item.get('fix', {}).get('content') if item.get('fix') else None,
                    metadata={'raw': item}
                )
                
                violation.suggestion = self.VIOLATION_SUGGESTIONS.get(violation.rule_code)
                violations.append(violation)
                
        except json.JSONDecodeError:
            violations = self.parse(json_output)
        
        return violations
    
    def _parse_line(self, line: str) -> Optional[RuffViolation]:
        """Parse a single line of Ruff output."""
        # Format: file.py:line:col: CODE message
        import re
        
        pattern = r'^([^:]+):(\d+):(\d+):\s+([A-Z0-9]+)\s+(.+)$'
        match = re.match(pattern, line)
        
        if not match:
            return None
        
        file_path = match.group(1)
        line_number = int(match.group(2))
        column_number = int(match.group(3))
        rule_code = match.group(4)
        message = match.group(5)
        
        violation = RuffViolation(
            file_path=file_path,
            line_number=line_number,
            column_number=column_number,
            rule_code=rule_code,
            category=RuleCategoryMapper.get_category(rule_code),
            severity=Severity.ERROR,
            message=message
        )
        
        violation.suggestion = self.VIOLATION_SUGGESTIONS.get(rule_code)
        
        return violation
    
    def _parse_fix_availability(self, fix_data: Optional[Dict]) -> FixAvailability:
        """Parse fix availability from fix data."""
        if not fix_data:
            return FixAvailability.NEVER
        
        applicability = fix_data.get('applicability', '')
        if applicability == 'safe':
            return FixAvailability.ALWAYS
        elif applicability == 'unsafe':
            return FixAvailability.SOMETIMES
        
        return FixAvailability.UNKNOWN


# ============================================================
# MAIN RUFF VALIDATOR
# ============================================================

class RuffValidator:
    """
    Validates Python code style and quality using Ruff.
    
    Features:
    - Run Ruff with configurable options
    - Parse Ruff output into structured violations
    - Support for all Ruff rules and categories
    - Automatic fix suggestions
    - Auto-fix capability
    - Comprehensive reporting
    - Rule-specific recommendations
    - Code quality scoring
    """
    
    def __init__(self, config: RuffValidatorConfig):
        self.config = config
        self.parser = RuffOutputParser()
        self.state = StateManager(config.project_root / ".ai_state" / "ruff_validator.json")
        
        self._ruff_version: Optional[str] = None
        
        logger.info("RuffValidator initialized")
    
    def validate(self) -> RuffReport:
        """Run complete Ruff validation."""
        logger.info("Starting Ruff validation...")
        
        report = RuffReport(
            project_name=self.config.project_root.name,
            ruff_version=self._get_ruff_version()
        )
        
        # Run Ruff
        output = self._run_ruff()
        
        if output:
            violations = self.parser.parse(output)
            
            for violation in violations:
                if self._should_ignore_file(violation.file_path):
                    continue
                
                # Check per-file ignores
                if self._should_ignore_violation(violation):
                    continue
                
                report.total_violations += 1
                report.violations.append(violation)
                
                if violation.severity == Severity.ERROR:
                    report.errors.append(violation)
                else:
                    report.warnings.append(violation)
                
                # Update statistics
                report.violations_by_rule[violation.rule_code] = \
                    report.violations_by_rule.get(violation.rule_code, 0) + 1
                
                report.violations_by_category[violation.category.value] = \
                    report.violations_by_category.get(violation.category.value, 0) + 1
                
                report.violations_by_file[violation.file_path] = \
                    report.violations_by_file.get(violation.file_path, 0) + 1
                
                # Track fixable violations
                if violation.fix_available != FixAvailability.NEVER:
                    report.fixable_violations += 1
                    if violation.fix_available == FixAvailability.ALWAYS:
                        report.auto_fixable_violations += 1
                
                # Update file violations
                if violation.file_path not in report.file_violations:
                    report.file_violations[violation.file_path] = FileViolations(
                        file_path=violation.file_path
                    )
                
                file_violations = report.file_violations[violation.file_path]
                file_violations.violations.append(violation)
                if violation.severity == Severity.ERROR:
                    file_violations.error_count += 1
                else:
                    file_violations.warning_count += 1
                if violation.fix_available != FixAvailability.NEVER:
                    file_violations.fixable_count += 1
        
        report.total_files = len(report.file_violations)
        report.files_with_violations = len(report.violations_by_file)
        
        # Calculate overall score and grade
        report.overall_score = self._calculate_overall_score(report)
        report.grade = self._calculate_grade(report.overall_score)
        
        # Determine validity
        report.is_valid = len(report.errors) == 0
        if self.config.fail_on_warning and report.warnings:
            report.is_valid = False
        
        # Generate summary and recommendations
        report.summary = self._generate_summary(report)
        report.recommendations = self._generate_recommendations(report)
        
        # Save report
        self._save_report(report)
        
        logger.info(f"Ruff validation complete: {len(report.errors)} errors, {len(report.warnings)} warnings")
        
        return report
    
    def validate_string(self, code: str) -> List[RuffViolation]:
        """Validate a code string."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            temp_path = Path(f.name)
        
        try:
            output = self._run_ruff_on_file(temp_path)
            return self.parser.parse(output) if output else []
        finally:
            temp_path.unlink()
    
    def validate_string_return_output(self, code: str) -> str:
        """Validate a code string and return raw output."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            temp_path = Path(f.name)
        
        try:
            return self._run_ruff_on_file(temp_path) or ""
        finally:
            temp_path.unlink()
    
    def fix(self, file_paths: Optional[List[Path]] = None) -> bool:
        """Auto-fix violations."""
        cmd = ['ruff', 'check', '--fix']
        
        if not self.config.unsafe_fixes:
            cmd.append('--unsafe-fixes')
        
        if file_paths:
            cmd.extend([str(p) for p in file_paths])
        else:
            cmd.append(str(self.config.project_root))
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,
                cwd=self.config.project_root
            )
            
            return result.returncode == 0
            
        except Exception as e:
            logger.error(f"Failed to run Ruff fix: {e}")
            return False
    
    def _run_ruff(self) -> Optional[str]:
        """Run Ruff on the project."""
        cmd = ['ruff', 'check']
        
        # Add config file if specified
        if self.config.config_file and self.config.config_file.exists():
            cmd.extend(['--config', str(self.config.config_file)])
        
        # Add select rules
        if self.config.select:
            cmd.extend(['--select', ','.join(self.config.select)])
        
        # Add ignore rules
        if self.config.ignore:
            cmd.extend(['--ignore', ','.join(self.config.ignore)])
        
        # Add extend select
        if self.config.extend_select:
            cmd.extend(['--extend-select', ','.join(self.config.extend_select)])
        
        # Add extend ignore
        if self.config.extend_ignore:
            cmd.extend(['--extend-ignore', ','.join(self.config.extend_ignore)])
        
        # Predefined rule sets
        if not self.config.select and not self.config.extend_select:
            select_rules = []
            
            if self.config.enable_pyflakes:
                select_rules.append('F')
            if self.config.enable_pycodestyle:
                select_rules.append('E')
                select_rules.append('W')
            if self.config.enable_isort:
                select_rules.append('I')
            if self.config.enable_pydocstyle:
                select_rules.append('D')
            if self.config.enable_pyupgrade:
                select_rules.append('UP')
            if self.config.enable_flake8_annotations:
                select_rules.append('ANN')
            if self.config.enable_flake8_bandit:
                select_rules.append('S')
            if self.config.enable_flake8_bugbear:
                select_rules.append('B')
            if self.config.enable_flake8_comprehensions:
                select_rules.append('C4')
            if self.config.enable_flake8_simplify:
                select_rules.append('SIM')
            if self.config.enable_mccabe:
                select_rules.append('C90')
            if self.config.enable_perflint:
                select_rules.append('PERF')
            
            if select_rules:
                cmd.extend(['--select', ','.join(select_rules)])
        
        # Line length
        cmd.extend(['--line-length', str(self.config.max_line_length)])
        
        # Target version
        cmd.extend(['--target-version', self.config.target_version])
        
        # Output format
        cmd.extend(['--output-format', 'full'])
        
        # Show fixes
        if self.config.show_fixes:
            cmd.append('--show-fixes')
        
        # Add project root
        cmd.append(str(self.config.project_root))
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,
                cwd=self.config.project_root
            )
            
            return result.stdout
            
        except FileNotFoundError:
            logger.error("Ruff not found. Please install Ruff: pip install ruff")
            return None
        except subprocess.TimeoutExpired:
            logger.error("Ruff timed out")
            return None
        except Exception as e:
            logger.error(f"Failed to run Ruff: {e}")
            return None
    
    def _run_ruff_on_file(self, file_path: Path) -> Optional[str]:
        """Run Ruff on a single file."""
        cmd = ['ruff', 'check', str(file_path)]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            return result.stdout
            
        except Exception as e:
            logger.error(f"Failed to run Ruff on {file_path}: {e}")
            return None
    
    def _get_ruff_version(self) -> str:
        """Get Ruff version."""
        if self._ruff_version:
            return self._ruff_version
        
        try:
            result = subprocess.run(
                ['ruff', '--version'],
                capture_output=True,
                text=True,
                timeout=10
            )
            self._ruff_version = result.stdout.strip().split()[1]
        except Exception:
            self._ruff_version = "unknown"
        
        return self._ruff_version
    
    def _should_ignore_file(self, file_path: str) -> bool:
        """Check if file should be ignored."""
        for pattern in self.config.ignore_patterns:
            if pattern.replace('*', '') in file_path:
                return True
        return False
    
    def _should_ignore_violation(self, violation: RuffViolation) -> bool:
        """Check if violation should be ignored per file."""
        file_path = violation.file_path
        
        for pattern, ignores in self.config.per_file_ignores.items():
            if pattern in file_path:
                if violation.rule_code in ignores:
                    return True
        
        return False
    
    def _calculate_overall_score(self, report: RuffReport) -> float:
        """Calculate overall code quality score."""
        score = 100.0
        
        # Deduct for errors (weighted by category)
        category_weights = {
            RuffRuleCategory.SECURITY.value: 10,
            RuffRuleCategory.BUG_RISK.value: 8,
            RuffRuleCategory.COMPLEXITY.value: 5,
            RuffRuleCategory.PERFORMANCE.value: 4,
            RuffRuleCategory.TYPE_ANNOTATION.value: 3,
            RuffRuleCategory.UNUSED_IMPORT.value: 2,
            RuffRuleCategory.UNUSED_VARIABLE.value: 2,
            RuffRuleCategory.WHITESPACE.value: 1,
            RuffRuleCategory.BLANK_LINE.value: 1,
        }
        
        for category, count in report.violations_by_category.items():
            weight = category_weights.get(category, 2)
            score -= count * weight * 0.5
        
        # Deduct for files with many violations
        for file_path, count in report.violations_by_file.items():
            if count > 20:
                score -= 5
            elif count > 10:
                score -= 2
        
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
    
    def _generate_summary(self, report: RuffReport) -> str:
        """Generate validation summary."""
        if report.is_valid:
            return f"✅ Ruff validation passed. Score: {report.overall_score:.1f} (Grade: {report.grade})"
        else:
            return f"❌ Ruff violations found: {len(report.errors)} errors, {len(report.warnings)} warnings"
    
    def _generate_recommendations(self, report: RuffReport) -> List[str]:
        """Generate recommendations."""
        recommendations = []
        
        # Most common violations
        if report.violations_by_rule:
            top_violations = sorted(report.violations_by_rule.items(), key=lambda x: x[1], reverse=True)[:5]
            for rule, count in top_violations:
                if rule.startswith('F4'):  # Unused imports/variables
                    recommendations.append(f"Remove {count} unused imports/variables")
                elif rule.startswith('E5'):  # Line length
                    recommendations.append(f"Fix {count} line length violations")
                elif rule.startswith('ANN'):  # Type annotations
                    recommendations.append(f"Add {count} missing type annotations")
                elif rule.startswith('D'):  # Docstrings
                    recommendations.append(f"Add {count} missing docstrings")
                elif rule.startswith('S'):  # Security
                    recommendations.append(f"Fix {count} security issues")
        
        # Fixable violations
        if report.fixable_violations > 0:
            recommendations.append(
                f"Run 'ruff check --fix' to auto-fix {report.fixable_violations} violations"
            )
        
        # Files with most violations
        if report.violations_by_file:
            top_files = sorted(report.violations_by_file.items(), key=lambda x: x[1], reverse=True)[:3]
            for file_path, count in top_files:
                short_name = Path(file_path).name
                recommendations.append(f"Focus on fixing {count} violations in {short_name}")
        
        return recommendations[:5]
    
    def _save_report(self, report: RuffReport):
        """Save report to state."""
        reports = self.state.get('reports', [])
        reports.append({
            'timestamp': report.validated_at.isoformat(),
            'project': report.project_name,
            'ruff_version': report.ruff_version,
            'is_valid': report.is_valid,
            'score': report.overall_score,
            'grade': report.grade,
            'errors': len(report.errors),
            'warnings': len(report.warnings),
            'fixable': report.fixable_violations
        })
        
        if len(reports) > 50:
            reports = reports[-50:]
        
        self.state.set('reports', reports)
        self.state.save()
    
    def export_report(self, report: RuffReport,
                      output_path: Optional[Path] = None,
                      format: str = 'markdown') -> str:
        """Export Ruff report."""
        
        if format == 'json':
            data = {
                'validated_at': report.validated_at.isoformat(),
                'project': report.project_name,
                'ruff_version': report.ruff_version,
                'is_valid': report.is_valid,
                'score': report.overall_score,
                'grade': report.grade,
                'summary': report.summary,
                'statistics': {
                    'total_files': report.total_files,
                    'files_with_violations': report.files_with_violations,
                    'total_violations': report.total_violations,
                    'fixable_violations': report.fixable_violations,
                    'violations_by_rule': report.violations_by_rule,
                    'violations_by_category': report.violations_by_category
                },
                'violations': [
                    {
                        'file': v.file_path,
                        'line': v.line_number,
                        'column': v.column_number,
                        'rule': v.rule_code,
                        'category': v.category.value,
                        'message': v.message,
                        'fixable': v.fix_available.value,
                        'suggestion': v.suggestion
                    }
                    for v in report.violations[:100]
                ],
                'recommendations': report.recommendations
            }
            
            content = json.dumps(data, indent=2)
            
        else:  # markdown
            lines = [
                f"# Ruff Validation Report",
                "",
                f"**Project:** {report.project_name}",
                f"**Ruff Version:** {report.ruff_version}",
                f"**Validated:** {report.validated_at.strftime('%Y-%m-%d %H:%M:%S')}",
                f"**Score:** {report.overall_score:.1f} (Grade: {report.grade})",
                f"**Status:** {report.summary}",
                "",
                "## Summary",
                "",
                f"| Metric | Value |",
                f"|--------|-------|",
                f"| Files Analyzed | {report.total_files} |",
                f"| Files with Violations | {report.files_with_violations} |",
                f"| Total Violations | {report.total_violations} |",
                f"| Errors | {len(report.errors)} |",
                f"| Warnings | {len(report.warnings)} |",
                f"| Fixable Violations | {report.fixable_violations} |",
                f"| Auto-Fixable | {report.auto_fixable_violations} |",
                "",
            ]
            
            if report.violations_by_category:
                lines.extend([
                    "## Violations by Category",
                    "",
                    "| Category | Count |",
                    "|----------|-------|",
                ])
                for category, count in sorted(report.violations_by_category.items(), key=lambda x: x[1], reverse=True):
                    lines.append(f"| {category} | {count} |")
                lines.append("")
            
            if report.violations_by_rule:
                lines.extend([
                    "## Top Violations by Rule",
                    "",
                    "| Rule | Count |",
                    "|------|-------|",
                ])
                for rule, count in sorted(report.violations_by_rule.items(), key=lambda x: x[1], reverse=True)[:10]:
                    lines.append(f"| {rule} | {count} |")
                lines.append("")
            
            if report.violations:
                lines.extend([
                    "## ❌ Violations",
                    "",
                    "| File | Line | Rule | Category | Message |",
                    "|------|------|------|----------|---------|",
                ])
                for v in report.violations[:self.config.max_violations_to_show]:
                    file_name = Path(v.file_path).name
                    lines.append(f"| {file_name} | {v.line_number} | {v.rule_code} | {v.category.value} | {v.message[:40]} |")
                
                if len(report.violations) > self.config.max_violations_to_show:
                    lines.append(f"| ... | ... | ... | ... | *and {len(report.violations) - self.config.max_violations_to_show} more* |")
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
        logger.info("RuffValidator closed")


# ============================================================
# CLI ENTRY POINT
# ============================================================

def main():
    """CLI entry point for Ruff validator."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate Python code style using Ruff")
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--config", type=Path, help="Ruff config file")
    parser.add_argument("--output", "-o", type=Path, help="Output report path")
    parser.add_argument("--format", choices=["json", "markdown"], default="markdown")
    parser.add_argument("--fix", action="store_true", help="Auto-fix violations")
    parser.add_argument("--unsafe-fixes", action="store_true", help="Apply unsafe fixes")
    parser.add_argument("--select", help="Rules to enable (comma-separated)")
    parser.add_argument("--ignore", help="Rules to ignore (comma-separated)")
    parser.add_argument("--line-length", type=int, default=100)
    parser.add_argument("--fail-on-warning", action="store_true")
    parser.add_argument("--target-version", default="py310")
    
    args = parser.parse_args()
    
    config = RuffValidatorConfig(
        project_root=args.project_root,
        config_file=args.config,
        max_line_length=args.line_length,
        fail_on_warning=args.fail_on_warning,
        target_version=args.target_version,
        unsafe_fixes=args.unsafe_fixes
    )
    
    if args.select:
        config.select = args.select.split(',')
    if args.ignore:
        config.ignore = args.ignore.split(',')
    
    validator = RuffValidator(config)
    
    if args.fix:
        success = validator.fix()
        if success:
            print("✅ Auto-fix completed")
        else:
            print("❌ Auto-fix failed")
        return
    
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