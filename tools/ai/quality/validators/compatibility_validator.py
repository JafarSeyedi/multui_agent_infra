#!/usr/bin/env python3
"""
Compatibility Validator - Validates Python version and dependency compatibility.

Part of the Quality tools (validators/compatibility_validator.py)

This compatibility_validator.py provides:

1. Python Version Compatibility - Checks code against target Python versions
2. Syntax Feature Detection - Identifies features requiring minimum Python versions
3. Dependency Validation - Verifies installed versions satisfy requirements
4. Vulnerability Scanning - Checks for known security vulnerabilities
5. Deprecated Package Detection - Identifies deprecated dependencies
6. License Compatibility - Validates licenses against allowed list
7. Outdated Dependency Detection - Finds packages that need updates
8. Python EOL Checking - Warns about end-of-life Python versions
9. Import Compatibility - Validates standard library imports
10. Multiple Target Versions - Check compatibility against multiple Python versions
11. Comprehensive Reporting - JSON and Markdown reports

Version Constraint Validation - Ensures python_requires is satisfied
"""

import ast
import json
import sys
import subprocess
import importlib.metadata
from pathlib import Path
from typing import Dict, List, Set, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from collections import defaultdict
from packaging import version
from packaging.specifiers import SpecifierSet
from packaging.requirements import Requirement

from ...shared.logger import get_logger
from ...shared.state_manager import StateManager

logger = get_logger(__name__)


# ============================================================
# ENUMS AND CONSTANTS
# ============================================================

class CompatibilityStatus(str, Enum):
    """Compatibility check status."""
    COMPATIBLE = "compatible"
    INCOMPATIBLE = "incompatible"
    WARNING = "warning"
    UNKNOWN = "unknown"
    NOT_INSTALLED = "not_installed"


class PythonVersion(str, Enum):
    """Supported Python versions."""
    PY37 = "3.7"
    PY38 = "3.8"
    PY39 = "3.9"
    PY310 = "3.10"
    PY311 = "3.11"
    PY312 = "3.12"
    PY313 = "3.13"


class IssueSeverity(str, Enum):
    """Severity of compatibility issue."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class FeatureCategory(str, Enum):
    """Category of Python feature."""
    SYNTAX = "syntax"
    STANDARD_LIBRARY = "standard_library"
    BUILTIN = "builtin"
    TYPING = "typing"
    ASYNC = "async"
    CONTEXT_MANAGER = "context_manager"
    DECORATOR = "decorator"
    METACLASS = "metaclass"
    F_STRING = "f_string"
    PATTERN_MATCHING = "pattern_matching"
    UNION_TYPES = "union_types"
    WALRUS_OPERATOR = "walrus_operator"
    TYPE_PARAMS = "type_params"
    EXCEPTION_GROUPS = "exception_groups"


# ============================================================
# PYTHON VERSION FEATURES
# ============================================================

class PythonFeatureRegistry:
    """Registry of Python features and their minimum versions."""
    
    FEATURES = {
        # Syntax features
        "f_strings": (PythonVersion.PY36, FeatureCategory.F_STRING),
        "async_await": (PythonVersion.PY35, FeatureCategory.ASYNC),
        "async_generators": (PythonVersion.PY36, FeatureCategory.ASYNC),
        "async_comprehensions": (PythonVersion.PY36, FeatureCategory.ASYNC),
        "walrus_operator": (PythonVersion.PY38, FeatureCategory.WALRUS_OPERATOR),
        "positional_only_params": (PythonVersion.PY38, FeatureCategory.SYNTAX),
        "assignment_expressions": (PythonVersion.PY38, FeatureCategory.SYNTAX),
        "pattern_matching": (PythonVersion.PY310, FeatureCategory.PATTERN_MATCHING),
        "union_types_pipe": (PythonVersion.PY310, FeatureCategory.UNION_TYPES),
        "type_alias": (PythonVersion.PY310, FeatureCategory.TYPING),
        "exception_groups": (PythonVersion.PY311, FeatureCategory.EXCEPTION_GROUPS),
        "type_param_syntax": (PythonVersion.PY312, FeatureCategory.TYPE_PARAMS),
        
        # Typing features
        "type_hints": (PythonVersion.PY35, FeatureCategory.TYPING),
        "variable_annotations": (PythonVersion.PY36, FeatureCategory.TYPING),
        "protocols": (PythonVersion.PY38, FeatureCategory.TYPING),
        "typed_dict": (PythonVersion.PY38, FeatureCategory.TYPING),
        "final_decorator": (PythonVersion.PY38, FeatureCategory.TYPING),
        "literal_types": (PythonVersion.PY38, FeatureCategory.TYPING),
        "annotated_types": (PythonVersion.PY39, FeatureCategory.TYPING),
        "type_guard": (PythonVersion.PY310, FeatureCategory.TYPING),
        "param_spec": (PythonVersion.PY310, FeatureCategory.TYPING),
        "concatenate": (PythonVersion.PY310, FeatureCategory.TYPING),
        "self_type": (PythonVersion.PY311, FeatureCategory.TYPING),
        "unpack_type": (PythonVersion.PY311, FeatureCategory.TYPING),
        
        # Standard library features
        "dataclasses": (PythonVersion.PY37, FeatureCategory.STANDARD_LIBRARY),
        "contextlib_asynccontextmanager": (PythonVersion.PY37, FeatureCategory.CONTEXT_MANAGER),
        "breakpoint": (PythonVersion.PY37, FeatureCategory.BUILTIN),
        "importlib_metadata": (PythonVersion.PY38, FeatureCategory.STANDARD_LIBRARY),
        "cached_property": (PythonVersion.PY38, FeatureCategory.STANDARD_LIBRARY),
        "singledispatchmethod": (PythonVersion.PY38, FeatureCategory.STANDARD_LIBRARY),
        "zoneinfo": (PythonVersion.PY39, FeatureCategory.STANDARD_LIBRARY),
        "graphlib": (PythonVersion.PY39, FeatureCategory.STANDARD_LIBRARY),
        "tomllib": (PythonVersion.PY311, FeatureCategory.STANDARD_LIBRARY),
    }
    
    @classmethod
    def get_minimum_version(cls, feature: str) -> Optional[PythonVersion]:
        """Get minimum Python version for a feature."""
        if feature in cls.FEATURES:
            return cls.FEATURES[feature][0]
        return None
    
    @classmethod
    def get_category(cls, feature: str) -> Optional[FeatureCategory]:
        """Get category of a feature."""
        if feature in cls.FEATURES:
            return cls.FEATURES[feature][1]
        return None
    
    @classmethod
    def get_all_features(cls) -> Dict[str, Tuple[PythonVersion, FeatureCategory]]:
        """Get all registered features."""
        return cls.FEATURES.copy()


# ============================================================
# DATA MODELS
# ============================================================

@dataclass
class VersionConstraint:
    """Version constraint for a dependency."""
    package_name: str
    constraint: str
    current_version: Optional[str] = None
    is_satisfied: bool = False
    reason: str = ""


@dataclass
class CompatibilityIssue:
    """A single compatibility issue."""
    issue_type: str
    severity: IssueSeverity
    description: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    feature: Optional[str] = None
    required_version: Optional[str] = None
    current_version: Optional[str] = None
    suggestion: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DependencyInfo:
    """Information about a dependency."""
    name: str
    required_version: str
    installed_version: Optional[str] = None
    is_compatible: bool = False
    is_latest: bool = False
    latest_version: Optional[str] = None
    has_vulnerabilities: bool = False
    vulnerabilities: List[str] = field(default_factory=list)
    is_deprecated: bool = False
    deprecation_message: Optional[str] = None
    license_type: Optional[str] = None
    python_requires: Optional[str] = None


@dataclass
class PythonVersionInfo:
    """Information about Python version."""
    version: str
    major: int
    minor: int
    micro: int
    release_level: str = "final"
    is_supported: bool = True
    eol_date: Optional[str] = None


@dataclass
class CompatibilityReport:
    """Complete compatibility validation report."""
    validated_at: datetime = field(default_factory=datetime.now)
    project_name: str = ""
    project_version: str = ""
    
    # Python version info
    current_python: PythonVersionInfo = field(default_factory=lambda: PythonVersionInfo(
        version=f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        major=sys.version_info.major,
        minor=sys.version_info.minor,
        micro=sys.version_info.micro
    ))
    target_python_versions: List[PythonVersion] = field(default_factory=list)
    
    # Compatibility results
    is_compatible: bool = True
    issues: List[CompatibilityIssue] = field(default_factory=list)
    warnings: List[CompatibilityIssue] = field(default_factory=list)
    
    # Dependency analysis
    dependencies: List[DependencyInfo] = field(default_factory=list)
    missing_dependencies: List[str] = field(default_factory=list)
    outdated_dependencies: List[DependencyInfo] = field(default_factory=list)
    vulnerable_dependencies: List[DependencyInfo] = field(default_factory=list)
    
    # Feature usage
    detected_features: Dict[str, List[str]] = field(default_factory=dict)  # feature -> files
    
    # Constraints
    python_requires: Optional[str] = None
    version_constraints: List[VersionConstraint] = field(default_factory=list)
    
    # Summary
    summary: str = ""
    recommendations: List[str] = field(default_factory=list)
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CompatibilityValidatorConfig:
    """Configuration for compatibility validator."""
    project_root: Path
    target_python_versions: List[PythonVersion] = field(default_factory=lambda: [
        PythonVersion.PY38, PythonVersion.PY39, PythonVersion.PY310, PythonVersion.PY311
    ])
    check_dependencies: bool = True
    check_syntax: bool = True
    check_imports: bool = True
    check_typing: bool = True
    check_stdlib: bool = True
    scan_vulnerabilities: bool = True
    check_deprecated: bool = True
    check_license_compatibility: bool = False
    allowed_licenses: List[str] = field(default_factory=lambda: [
        "MIT", "Apache-2.0", "BSD-3-Clause", "BSD-2-Clause", "ISC", "Python-2.0"
    ])
    ignore_missing_deps: bool = False
    ignore_patterns: List[str] = field(default_factory=list)
    fail_on_incompatible: bool = True
    generate_report: bool = True


# ============================================================
# SYNTAX FEATURE DETECTOR
# ============================================================

class SyntaxFeatureDetector(ast.NodeVisitor):
    """Detect Python syntax features used in code."""
    
    def __init__(self):
        self.features: Set[str] = set()
        self.issues: List[CompatibilityIssue] = []
        self.current_file: str = ""
    
    def detect(self, tree: ast.AST, file_path: str) -> Set[str]:
        """Detect features used in AST."""
        self.features = set()
        self.current_file = file_path
        self.visit(tree)
        return self.features
    
    # Pattern Matching (Python 3.10+)
    def visit_Match(self, node: ast.Match):
        self.features.add("pattern_matching")
        self.generic_visit(node)
    
    def visit_MatchAs(self, node: ast.MatchAs):
        self.features.add("pattern_matching")
        self.generic_visit(node)
    
    def visit_MatchOr(self, node: ast.MatchOr):
        self.features.add("pattern_matching")
        self.generic_visit(node)
    
    # Walrus Operator (Python 3.8+)
    def visit_NamedExpr(self, node: ast.NamedExpr):
        self.features.add("walrus_operator")
        self.generic_visit(node)
    
    # Union Types with | (Python 3.10+)
    def visit_BinOp(self, node: ast.BinOp):
        if isinstance(node.op, ast.BitOr):
            # Check if this is a type annotation context
            self.features.add("union_types_pipe")
        self.generic_visit(node)
    
    # F-strings
    def visit_JoinedStr(self, node: ast.JoinedStr):
        self.features.add("f_strings")
        self.generic_visit(node)
    
    # Async/Await (Python 3.5+)
    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        self.features.add("async_await")
        self.generic_visit(node)
    
    def visit_Await(self, node: ast.Await):
        self.features.add("async_await")
        self.generic_visit(node)
    
    def visit_AsyncFor(self, node: ast.AsyncFor):
        self.features.add("async_await")
        self.generic_visit(node)
    
    def visit_AsyncWith(self, node: ast.AsyncWith):
        self.features.add("async_await")
        self.generic_visit(node)
    
    # Type Hints (Python 3.5+)
    def visit_AnnAssign(self, node: ast.AnnAssign):
        self.features.add("type_hints")
        self.generic_visit(node)
    
    def visit_arg(self, node: ast.arg):
        if node.annotation:
            self.features.add("type_hints")
        self.generic_visit(node)
    
    # Positional-only parameters (Python 3.8+)
    def visit_arguments(self, node: ast.arguments):
        if node.posonlyargs:
            self.features.add("positional_only_params")
        self.generic_visit(node)
    
    # Exception Groups (Python 3.11+)
    def visit_TryStar(self, node: ast.TryStar):
        self.features.add("exception_groups")
        self.generic_visit(node)
    
    # Type Parameters (Python 3.12+)
    def visit_TypeVar(self, node):
        self.features.add("type_hints")
    
    def visit_TypeVarTuple(self, node):
        self.features.add("type_param_syntax")
    
    def visit_ParamSpec(self, node):
        self.features.add("type_param_syntax")
    
    def visit_TypeAlias(self, node):
        self.features.add("type_alias")
    
    # Subscript with multiple types (Python 3.9+ for builtins)
    def visit_Subscript(self, node: ast.Subscript):
        if isinstance(node.value, ast.Name):
            if node.value.id in ('list', 'dict', 'set', 'tuple', 'frozenset', 'type'):
                self.features.add("type_hints")
        self.generic_visit(node)


# ============================================================
# DEPENDENCY ANALYZER
# ============================================================

class DependencyAnalyzer:
    """Analyzes dependencies for compatibility issues."""
    
    def __init__(self, config: CompatibilityValidatorConfig):
        self.config = config
        self.installed_packages: Dict[str, str] = {}
        self._load_installed_packages()
    
    def _load_installed_packages(self):
        """Load installed package versions."""
        try:
            for dist in importlib.metadata.distributions():
                self.installed_packages[dist.metadata["Name"].lower()] = dist.version
        except Exception as e:
            logger.warning(f"Failed to load installed packages: {e}")
    
    def analyze_requirements(self, requirements_file: Path) -> List[DependencyInfo]:
        """Analyze requirements file."""
        dependencies = []
        
        if not requirements_file.exists():
            return dependencies
        
        content = requirements_file.read_text()
        
        for line in content.split('\n'):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            # Handle -r, -e, etc.
            if line.startswith('-'):
                continue
            
            try:
                req = Requirement(line)
                dep_info = self._analyze_dependency(req.name, str(req.specifier))
                dependencies.append(dep_info)
            except Exception as e:
                logger.warning(f"Failed to parse requirement '{line}': {e}")
        
        return dependencies
    
    def analyze_pyproject(self, pyproject_file: Path) -> List[DependencyInfo]:
        """Analyze pyproject.toml dependencies."""
        dependencies = []
        
        if not pyproject_file.exists():
            return dependencies
        
        try:
            import tomllib
        except ImportError:
            import tomli as tomllib
        
        try:
            with open(pyproject_file, 'rb') as f:
                data = tomllib.load(f)
            
            # Poetry format
            if 'tool' in data and 'poetry' in data['tool']:
                deps = data['tool']['poetry'].get('dependencies', {})
                for name, constraint in deps.items():
                    if name.lower() == 'python':
                        continue
                    if isinstance(constraint, dict):
                        constraint = constraint.get('version', '')
                    dep_info = self._analyze_dependency(name, str(constraint) if constraint else '')
                    dependencies.append(dep_info)
            
            # PEP 621 format
            if 'project' in data:
                deps = data['project'].get('dependencies', [])
                for dep in deps:
                    try:
                        req = Requirement(dep)
                        dep_info = self._analyze_dependency(req.name, str(req.specifier))
                        dependencies.append(dep_info)
                    except Exception:
                        pass
                
                # Optional dependencies
                optional_deps = data['project'].get('optional-dependencies', {})
                for group, deps in optional_deps.items():
                    for dep in deps:
                        try:
                            req = Requirement(dep)
                            dep_info = self._analyze_dependency(req.name, str(req.specifier))
                            dep_info.metadata['optional_group'] = group
                            dependencies.append(dep_info)
                        except Exception:
                            pass
            
        except Exception as e:
            logger.warning(f"Failed to parse pyproject.toml: {e}")
        
        return dependencies
    
    def analyze_setup_py(self, setup_file: Path) -> List[DependencyInfo]:
        """Analyze setup.py dependencies."""
        # This would parse setup.py - simplified for now
        return []
    
    def _analyze_dependency(self, name: str, constraint: str) -> DependencyInfo:
        """Analyze a single dependency."""
        name_lower = name.lower()
        installed = self.installed_packages.get(name_lower)
        
        info = DependencyInfo(
            name=name,
            required_version=constraint,
            installed_version=installed,
            is_compatible=False
        )
        
        # Check if installed version satisfies constraint
        if installed and constraint:
            try:
                specifier = SpecifierSet(constraint)
                info.is_compatible = specifier.contains(installed)
            except Exception:
                info.is_compatible = True
        
        # Check if latest version available
        info.latest_version = self._get_latest_version(name)
        if info.latest_version and installed:
            info.is_latest = version.parse(installed) >= version.parse(info.latest_version)
        
        # Check for vulnerabilities
        if self.config.scan_vulnerabilities:
            info.vulnerabilities = self._check_vulnerabilities(name, installed)
            info.has_vulnerabilities = len(info.vulnerabilities) > 0
        
        # Check if deprecated
        info.is_deprecated, info.deprecation_message = self._check_deprecated(name)
        
        # Get license info
        info.license_type = self._get_license(name)
        
        # Get Python requires
        info.python_requires = self._get_python_requires(name)
        
        return info
    
    def _get_latest_version(self, package_name: str) -> Optional[str]:
        """Get latest version from PyPI."""
        try:
            import requests
            response = requests.get(f"https://pypi.org/pypi/{package_name}/json", timeout=5)
            if response.status_code == 200:
                return response.json()['info']['version']
        except Exception:
            pass
        return None
    
    def _check_vulnerabilities(self, package_name: str, version: Optional[str]) -> List[str]:
        """Check for known vulnerabilities."""
        vulnerabilities = []
        
        # Check using safety or pip-audit if available
        try:
            result = subprocess.run(
                ['pip-audit', '--requirement', '/dev/null', '--package', f'{package_name}=={version}'],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode != 0:
                for line in result.stdout.split('\n'):
                    if package_name in line:
                        vulnerabilities.append(line.strip())
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        
        return vulnerabilities
    
    def _check_deprecated(self, package_name: str) -> Tuple[bool, Optional[str]]:
        """Check if package is deprecated."""
        try:
            import requests
            response = requests.get(f"https://pypi.org/pypi/{package_name}/json", timeout=5)
            if response.status_code == 200:
                info = response.json()['info']
                if info.get('deprecated'):
                    return True, info.get('deprecated_message')
        except Exception:
            pass
        return False, None
    
    def _get_license(self, package_name: str) -> Optional[str]:
        """Get package license."""
        try:
            import requests
            response = requests.get(f"https://pypi.org/pypi/{package_name}/json", timeout=5)
            if response.status_code == 200:
                return response.json()['info'].get('license')
        except Exception:
            pass
        return None
    
    def _get_python_requires(self, package_name: str) -> Optional[str]:
        """Get Python version requirement for package."""
        try:
            import requests
            response = requests.get(f"https://pypi.org/pypi/{package_name}/json", timeout=5)
            if response.status_code == 200:
                return response.json()['info'].get('requires_python')
        except Exception:
            pass
        return None


# ============================================================
# MAIN COMPATIBILITY VALIDATOR
# ============================================================

class CompatibilityValidator:
    """
    Validates Python version and dependency compatibility.
    
    Features:
    - Python version compatibility checking
    - Syntax feature detection
    - Dependency version validation
    - Vulnerability scanning
    - Deprecated package detection
    - License compatibility
    - Multiple target version support
    - Comprehensive reporting
    """
    
    def __init__(self, config: CompatibilityValidatorConfig):
        self.config = config
        self.feature_detector = SyntaxFeatureDetector()
        self.dependency_analyzer = DependencyAnalyzer(config)
        self.state = StateManager(config.project_root / ".ai_state" / "compatibility_validator.json")
        
        # Python version EOL dates
        self.python_eol = {
            "3.7": "2023-06-27",
            "3.8": "2024-10-07",
            "3.9": "2025-10-05",
            "3.10": "2026-10-04",
            "3.11": "2027-10-24",
            "3.12": "2028-10-02",
            "3.13": "2029-10-01",
        }
        
        logger.info("CompatibilityValidator initialized")
    
    def validate(self) -> CompatibilityReport:
        """Run complete compatibility validation."""
        logger.info("Starting compatibility validation...")
        
        report = CompatibilityReport(
            project_name=self._detect_project_name(),
            project_version=self._detect_project_version(),
            target_python_versions=self.config.target_python_versions
        )
        
        # Parse python_requires
        report.python_requires = self._get_python_requires()
        
        # Validate Python version compatibility
        self._validate_python_version(report)
        
        # Scan source files
        self._scan_source_files(report)
        
        # Analyze dependencies
        if self.config.check_dependencies:
            self._analyze_dependencies(report)
        
        # Check version constraints
        self._check_version_constraints(report)
        
        # Generate summary and recommendations
        report.summary = self._generate_summary(report)
        report.recommendations = self._generate_recommendations(report)
        
        # Save report
        self._save_report(report)
        
        logger.info(f"Compatibility validation complete: {report.is_compatible}")
        
        return report
    
    def _detect_project_name(self) -> str:
        """Detect project name."""
        pyproject = self.config.project_root / "pyproject.toml"
        if pyproject.exists():
            try:
                import tomllib
            except ImportError:
                import tomli as tomllib
            
            with open(pyproject, 'rb') as f:
                data = tomllib.load(f)
                if 'project' in data:
                    return data['project'].get('name', '')
                if 'tool' in data and 'poetry' in data['tool']:
                    return data['tool']['poetry'].get('name', '')
        
        return self.config.project_root.name
    
    def _detect_project_version(self) -> str:
        """Detect project version."""
        pyproject = self.config.project_root / "pyproject.toml"
        if pyproject.exists():
            try:
                import tomllib
            except ImportError:
                import tomli as tomllib
            
            with open(pyproject, 'rb') as f:
                data = tomllib.load(f)
                if 'project' in data:
                    return data['project'].get('version', '0.0.0')
                if 'tool' in data and 'poetry' in data['tool']:
                    return data['tool']['poetry'].get('version', '0.0.0')
        
        return "0.0.0"
    
    def _get_python_requires(self) -> Optional[str]:
        """Get python_requires from project configuration."""
        pyproject = self.config.project_root / "pyproject.toml"
        if pyproject.exists():
            try:
                import tomllib
            except ImportError:
                import tomli as tomllib
            
            with open(pyproject, 'rb') as f:
                data = tomllib.load(f)
                if 'project' in data:
                    return data['project'].get('requires-python')
                if 'tool' in data and 'poetry' in data['tool']:
                    return data['tool']['poetry'].get('python')
        
        return None
    
    def _validate_python_version(self, report: CompatibilityReport):
        """Validate Python version compatibility."""
        # Check if current Python is supported
        current_ver = f"{report.current_python.major}.{report.current_python.minor}"
        if current_ver in self.python_eol:
            eol_date = self.python_eol[current_ver]
            if datetime.now() > datetime.fromisoformat(eol_date):
                report.warnings.append(CompatibilityIssue(
                    issue_type="python_eol",
                    severity=IssueSeverity.HIGH,
                    description=f"Python {current_ver} is end-of-life (EOL: {eol_date})",
                    current_version=current_ver,
                    suggestion=f"Upgrade to Python 3.9 or later"
                ))
        
        # Check python_requires against target versions
        if report.python_requires:
            try:
                specifier = SpecifierSet(report.python_requires)
                for target in report.target_python_versions:
                    if not specifier.contains(target.value):
                        report.issues.append(CompatibilityIssue(
                            issue_type="python_requires_mismatch",
                            severity=IssueSeverity.CRITICAL,
                            description=f"Target Python {target.value} does not satisfy python_requires '{report.python_requires}'",
                            required_version=report.python_requires,
                            current_version=target.value,
                            suggestion=f"Update python_requires or drop support for Python {target.value}"
                        ))
                        report.is_compatible = False
            except Exception as e:
                logger.warning(f"Invalid python_requires specifier: {e}")
    
    def _scan_source_files(self, report: CompatibilityReport):
        """Scan source files for feature usage."""
        python_files = list(self.config.project_root.rglob("*.py"))
        
        for file_path in python_files:
            if self._should_ignore(file_path):
                continue
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                tree = ast.parse(content)
                features = self.feature_detector.detect(tree, str(file_path))
                
                for feature in features:
                    min_version = PythonFeatureRegistry.get_minimum_version(feature)
                    
                    if feature not in report.detected_features:
                        report.detected_features[feature] = []
                    report.detected_features[feature].append(str(file_path))
                    
                    # Check against target versions
                    if min_version:
                        for target in report.target_python_versions:
                            target_ver = version.parse(target.value)
                            min_ver = version.parse(min_version.value)
                            
                            if target_ver < min_ver:
                                issue = CompatibilityIssue(
                                    issue_type="feature_not_available",
                                    severity=IssueSeverity.CRITICAL,
                                    description=f"Feature '{feature}' requires Python {min_version.value} but target is {target.value}",
                                    file_path=str(file_path),
                                    feature=feature,
                                    required_version=min_version.value,
                                    current_version=target.value,
                                    suggestion=f"Remove feature usage or drop support for Python {target.value}"
                                )
                                report.issues.append(issue)
                                report.is_compatible = False
                
                # Check import compatibility
                if self.config.check_imports:
                    self._check_import_compatibility(tree, str(file_path), report)
                
            except SyntaxError as e:
                report.issues.append(CompatibilityIssue(
                    issue_type="syntax_error",
                    severity=IssueSeverity.CRITICAL,
                    description=f"Syntax error: {e}",
                    file_path=str(file_path),
                    line_number=e.lineno
                ))
                report.is_compatible = False
            except Exception as e:
                logger.warning(f"Failed to scan {file_path}: {e}")
    
    def _check_import_compatibility(self, tree: ast.AST, file_path: str, report: CompatibilityReport):
        """Check import compatibility."""
        class ImportVisitor(ast.NodeVisitor):
            def visit_Import(self, node):
                for alias in node.names:
                    self._check_import(alias.name)
            
            def visit_ImportFrom(self, node):
                if node.module:
                    self._check_import(node.module)
            
            def _check_import(self, module_name: str):
                top_module = module_name.split('.')[0]
                
                # Check standard library modules that were added in specific versions
                stdlib_added = {
                    "dataclasses": PythonVersion.PY37,
                    "importlib.metadata": PythonVersion.PY38,
                    "zoneinfo": PythonVersion.PY39,
                    "graphlib": PythonVersion.PY39,
                    "tomllib": PythonVersion.PY311,
                }
                
                if top_module in stdlib_added:
                    min_version = stdlib_added[top_module]
                    for target in report.target_python_versions:
                        target_ver = version.parse(target.value)
                        min_ver = version.parse(min_version.value)
                        
                        if target_ver < min_ver:
                            report.issues.append(CompatibilityIssue(
                                issue_type="stdlib_not_available",
                                severity=IssueSeverity.CRITICAL,
                                description=f"Module '{top_module}' requires Python {min_version.value}",
                                file_path=file_path,
                                line_number=node.lineno,
                                required_version=min_version.value,
                                current_version=target.value,
                                suggestion=f"Use backport or drop Python {target.value} support"
                            ))
                            report.is_compatible = False
        
        visitor = ImportVisitor()
        visitor.visit(tree)
    
    def _analyze_dependencies(self, report: CompatibilityReport):
        """Analyze project dependencies."""
        # Find requirement files
        req_file = self.config.project_root / "requirements.txt"
        if req_file.exists():
            deps = self.dependency_analyzer.analyze_requirements(req_file)
            report.dependencies.extend(deps)
        
        dev_req = self.config.project_root / "requirements-dev.txt"
        if dev_req.exists():
            deps = self.dependency_analyzer.analyze_requirements(dev_req)
            for dep in deps:
                dep.metadata['dev'] = True
            report.dependencies.extend(deps)
        
        pyproject = self.config.project_root / "pyproject.toml"
        if pyproject.exists():
            deps = self.dependency_analyzer.analyze_pyproject(pyproject)
            report.dependencies.extend(deps)
        
        # Categorize dependencies
        for dep in report.dependencies:
            if not dep.installed_version:
                report.missing_dependencies.append(dep.name)
                if not self.config.ignore_missing_deps:
                    report.issues.append(CompatibilityIssue(
                        issue_type="missing_dependency",
                        severity=IssueSeverity.HIGH,
                        description=f"Dependency '{dep.name}' is not installed",
                        suggestion=f"Run: pip install {dep.name}"
                    ))
                    report.is_compatible = False
            
            elif not dep.is_compatible:
                report.issues.append(CompatibilityIssue(
                    issue_type="version_mismatch",
                    severity=IssueSeverity.HIGH,
                    description=f"Dependency '{dep.name}' version {dep.installed_version} does not satisfy '{dep.required_version}'",
                    required_version=dep.required_version,
                    current_version=dep.installed_version,
                    suggestion=f"Run: pip install '{dep.name}{dep.required_version}'"
                ))
                report.is_compatible = False
            
            if not dep.is_latest and dep.latest_version:
                report.outdated_dependencies.append(dep)
            
            if dep.has_vulnerabilities:
                report.vulnerable_dependencies.append(dep)
                for vuln in dep.vulnerabilities:
                    report.warnings.append(CompatibilityIssue(
                        issue_type="vulnerability",
                        severity=IssueSeverity.HIGH,
                        description=f"Vulnerability in {dep.name}: {vuln}",
                        suggestion=f"Upgrade {dep.name} to latest version"
                    ))
            
            if dep.is_deprecated:
                report.warnings.append(CompatibilityIssue(
                    issue_type="deprecated_dependency",
                    severity=IssueSeverity.MEDIUM,
                    description=f"Dependency '{dep.name}' is deprecated: {dep.deprecation_message or 'No message'}",
                    suggestion="Find alternative package"
                ))
            
            # Check license compatibility
            if self.config.check_license_compatibility and dep.license_type:
                if dep.license_type not in self.config.allowed_licenses:
                    report.warnings.append(CompatibilityIssue(
                        issue_type="license_incompatible",
                        severity=IssueSeverity.MEDIUM,
                        description=f"Dependency '{dep.name}' has license '{dep.license_type}' which is not in allowed list",
                        suggestion="Review license compatibility"
                    ))
    
    def _check_version_constraints(self, report: CompatibilityReport):
        """Check version constraints."""
        for dep in report.dependencies:
            if dep.python_requires:
                try:
                    specifier = SpecifierSet(dep.python_requires)
                    current_ver = f"{report.current_python.major}.{report.current_python.minor}"
                    
                    if not specifier.contains(current_ver):
                        report.issues.append(CompatibilityIssue(
                            issue_type="python_requires_dep",
                            severity=IssueSeverity.CRITICAL,
                            description=f"Dependency '{dep.name}' requires Python {dep.python_requires} but current is {current_ver}",
                            required_version=dep.python_requires,
                            current_version=current_ver,
                            suggestion=f"Upgrade Python or find compatible version of {dep.name}"
                        ))
                        report.is_compatible = False
                except Exception:
                    pass
    
    def _should_ignore(self, file_path: Path) -> bool:
        """Check if file should be ignored."""
        path_str = str(file_path)
        for pattern in self.config.ignore_patterns:
            if pattern in path_str:
                return True
        return False
    
    def _generate_summary(self, report: CompatibilityReport) -> str:
        """Generate validation summary."""
        if report.is_compatible:
            return f"✅ Compatible with target Python versions: {', '.join(v.value for v in report.target_python_versions)}"
        else:
            return f"❌ Compatibility issues found: {len(report.issues)} errors, {len(report.warnings)} warnings"
    
    def _generate_recommendations(self, report: CompatibilityReport) -> List[str]:
        """Generate recommendations."""
        recommendations = []
        
        if report.issues:
            recommendations.append(f"Fix {len(report.issues)} compatibility issues")
        
        if report.outdated_dependencies:
            recommendations.append(f"Update {len(report.outdated_dependencies)} outdated dependencies")
        
        if report.vulnerable_dependencies:
            recommendations.append(f"Address vulnerabilities in {len(report.vulnerable_dependencies)} packages")
        
        if report.python_requires:
            current_ver = f"{report.current_python.major}.{report.current_python.minor}"
            try:
                specifier = SpecifierSet(report.python_requires)
                if not specifier.contains(current_ver):
                    recommendations.append(f"Current Python {current_ver} does not satisfy python_requires '{report.python_requires}'")
            except Exception:
                pass
        
        return recommendations
    
    def _save_report(self, report: CompatibilityReport):
        """Save report to state."""
        reports = self.state.get('reports', [])
        reports.append({
            'timestamp': report.validated_at.isoformat(),
            'project': report.project_name,
            'is_compatible': report.is_compatible,
            'issues': len(report.issues),
            'warnings': len(report.warnings),
            'outdated_deps': len(report.outdated_dependencies),
            'vulnerable_deps': len(report.vulnerable_dependencies)
        })
        
        if len(reports) > 50:
            reports = reports[-50:]
        
        self.state.set('reports', reports)
        self.state.save()
    
    def export_report(self, report: CompatibilityReport,
                      output_path: Optional[Path] = None,
                      format: str = 'markdown') -> str:
        """Export compatibility report."""
        
        if format == 'json':
            data = {
                'validated_at': report.validated_at.isoformat(),
                'project': report.project_name,
                'version': report.project_version,
                'current_python': report.current_python.version,
                'target_python_versions': [v.value for v in report.target_python_versions],
                'is_compatible': report.is_compatible,
                'summary': report.summary,
                'issues': [
                    {
                        'type': i.issue_type,
                        'severity': i.severity.value,
                        'description': i.description,
                        'file': i.file_path,
                        'line': i.line_number,
                        'suggestion': i.suggestion
                    }
                    for i in report.issues
                ],
                'warnings': [
                    {
                        'type': w.issue_type,
                        'description': w.description,
                        'suggestion': w.suggestion
                    }
                    for w in report.warnings
                ],
                'dependencies': [
                    {
                        'name': d.name,
                        'required': d.required_version,
                        'installed': d.installed_version,
                        'compatible': d.is_compatible,
                        'latest': d.latest_version,
                        'vulnerable': d.has_vulnerabilities
                    }
                    for d in report.dependencies
                ],
                'detected_features': report.detected_features,
                'recommendations': report.recommendations
            }
            
            content = json.dumps(data, indent=2)
            
        else:  # markdown
            lines = [
                f"# Compatibility Validation Report",
                "",
                f"**Project:** {report.project_name} ({report.project_version})",
                f"**Validated:** {report.validated_at.strftime('%Y-%m-%d %H:%M:%S')}",
                f"**Current Python:** {report.current_python.version}",
                f"**Target Python Versions:** {', '.join(v.value for v in report.target_python_versions)}",
                f"**Status:** {report.summary}",
                "",
                "## Summary",
                "",
                f"- **Compatible:** {'✅ Yes' if report.is_compatible else '❌ No'}",
                f"- **Issues:** {len(report.issues)}",
                f"- **Warnings:** {len(report.warnings)}",
                f"- **Dependencies:** {len(report.dependencies)}",
                f"- **Outdated:** {len(report.outdated_dependencies)}",
                f"- **Vulnerable:** {len(report.vulnerable_dependencies)}",
                ""
            ]
            
            if report.issues:
                lines.extend([
                    "## ❌ Issues",
                    ""
                ])
                for issue in report.issues:
                    lines.append(f"### {issue.issue_type} ({issue.severity.value})")
                    lines.append(f"**Description:** {issue.description}")
                    if issue.file_path:
                        lines.append(f"**File:** {issue.file_path}:{issue.line_number or 'N/A'}")
                    if issue.suggestion:
                        lines.append(f"**Suggestion:** {issue.suggestion}")
                    lines.append("")
            
            if report.warnings:
                lines.extend([
                    "## ⚠️ Warnings",
                    ""
                ])
                for warning in report.warnings[:20]:
                    lines.append(f"- **{warning.issue_type}:** {warning.description}")
                lines.append("")
            
            if report.detected_features:
                lines.extend([
                    "## Detected Python Features",
                    "",
                    "| Feature | Minimum Python | Files |",
                    "|---------|---------------|-------|",
                ])
                for feature, files in report.detected_features.items():
                    min_ver = PythonFeatureRegistry.get_minimum_version(feature)
                    lines.append(f"| {feature} | {min_ver.value if min_ver else 'N/A'} | {len(files)} |")
                lines.append("")
            
            if report.recommendations:
                lines.extend([
                    "## Recommendations",
                    ""
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
        logger.info("CompatibilityValidator closed")


# ============================================================
# CLI ENTRY POINT
# ============================================================

def main():
    """CLI entry point for compatibility validator."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate Python version and dependency compatibility")
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--target", choices=[v.value for v in PythonVersion], action="append",
                       help="Target Python versions")
    parser.add_argument("--output", "-o", type=Path, help="Output report path")
    parser.add_argument("--format", choices=["json", "markdown"], default="markdown")
    parser.add_argument("--no-deps", action="store_true", help="Skip dependency checking")
    parser.add_argument("--scan-vulns", action="store_true", help="Scan for vulnerabilities")
    parser.add_argument("--check-licenses", action="store_true", help="Check license compatibility")
    
    args = parser.parse_args()
    
    targets = [PythonVersion(t) for t in args.target] if args.target else [
        PythonVersion.PY38, PythonVersion.PY39, PythonVersion.PY310, PythonVersion.PY311
    ]
    
    config = CompatibilityValidatorConfig(
        project_root=args.project_root,
        target_python_versions=targets,
        check_dependencies=not args.no_deps,
        scan_vulnerabilities=args.scan_vulns,
        check_license_compatibility=args.check_licenses
    )
    
    validator = CompatibilityValidator(config)
    
    report = validator.validate()
    
    output = validator.export_report(report, args.output, args.format)
    
    if not args.output:
        print(output)
    else:
        print(f"Report saved to {args.output}")
    
    print(f"\n{report.summary}")
    
    if config.fail_on_incompatible and not report.is_compatible:
        exit(1)
    
    validator.close()


if __name__ == "__main__":
    main()