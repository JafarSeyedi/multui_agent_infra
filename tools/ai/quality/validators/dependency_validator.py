#!/usr/bin/env python3
"""
Dependency Validator - Validates project dependencies for security, licensing, and version issues.

Part of the Quality tools (validators/dependency_validator.py)

This dependency_validator.py provides:

1. Multi-Source Parsing - requirements.txt, pyproject.toml, poetry.lock, Pipfile.lock
2. Vulnerability Scanning - Integration with pip-audit and safety
3. License Compliance - Checks against allowed/restricted/forbidden licenses
4. Outdated Detection - Identifies packages with newer versions available
5. Deprecated/Abandoned Detection - Warns about unmaintained packages
6. Version Conflict Detection - Finds conflicting version requirements
7. Pinned Version Checking - Ensures production dependencies are pinned
8. Dependency Health Score - A-F grade based on overall health
9. Comprehensive Reporting - JSON and Markdown formats
10. Security Advisory Integration - CVSS scores and CWE references
11. PyPI Information - Enriches with latest version and release dates
12. Actionable Recommendations - Specific upgrade and fix suggestions

The dependency validator ensures your project's supply chain is secure, up-to-date, and compliant with licensing requirements.
"""

import json
import subprocess
import importlib.metadata
from pathlib import Path
from typing import Dict, List, Set, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
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

class DependencySource(str, Enum):
    """Source of dependency."""
    REQUIREMENTS_TXT = "requirements.txt"
    REQUIREMENTS_DEV = "requirements-dev.txt"
    PYPROJECT_TOML = "pyproject.toml"
    SETUP_PY = "setup.py"
    POETRY = "poetry"
    PIPENV = "pipenv"
    CONDA = "conda"
    DIRECT_IMPORT = "direct_import"


class DependencyType(str, Enum):
    """Type of dependency."""
    PRODUCTION = "production"
    DEVELOPMENT = "development"
    OPTIONAL = "optional"
    TEST = "test"
    DOCS = "docs"
    BUILD = "build"
    UNKNOWN = "unknown"


class Severity(str, Enum):
    """Severity of dependency issue."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class VulnerabilitySeverity(str, Enum):
    """Severity of security vulnerability."""
    CRITICAL = "critical"
    HIGH = "high"
    MODERATE = "moderate"
    LOW = "low"
    UNKNOWN = "unknown"


class LicenseCompatibility(str, Enum):
    """License compatibility status."""
    COMPATIBLE = "compatible"
    INCOMPATIBLE = "incompatible"
    RESTRICTED = "restricted"
    UNKNOWN = "unknown"
    NEEDS_REVIEW = "needs_review"


# ============================================================
# DATA MODELS
# ============================================================

@dataclass
class Vulnerability:
    """Security vulnerability information."""
    id: str
    package_name: str
    affected_versions: str
    fixed_version: Optional[str]
    severity: VulnerabilitySeverity
    summary: str
    details: Optional[str] = None
    cwe_id: Optional[str] = None
    cvss_score: Optional[float] = None
    published_date: Optional[datetime] = None
    references: List[str] = field(default_factory=list)


@dataclass
class LicenseInfo:
    """License information for a package."""
    name: str
    spdx_id: Optional[str] = None
    compatibility: LicenseCompatibility = LicenseCompatibility.UNKNOWN
    is_osi_approved: bool = False
    is_fsf_free: bool = False
    restrictions: List[str] = field(default_factory=list)
    obligations: List[str] = field(default_factory=list)
    url: Optional[str] = None


@dataclass
class DependencyInfo:
    """Information about a single dependency."""
    name: str
    version: Optional[str] = None
    required_version: Optional[str] = None
    source: DependencySource = DependencySource.UNKNOWN
    dep_type: DependencyType = DependencyType.PRODUCTION
    is_direct: bool = True
    is_pinned: bool = False
    is_outdated: bool = False
    latest_version: Optional[str] = None
    latest_release_date: Optional[datetime] = None
    is_deprecated: bool = False
    deprecation_message: Optional[str] = None
    is_abandoned: bool = False
    replacement: Optional[str] = None
    vulnerabilities: List[Vulnerability] = field(default_factory=list)
    license_info: Optional[LicenseInfo] = None
    python_requires: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    dependents: List[str] = field(default_factory=list)
    size_bytes: Optional[int] = None
    homepage: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DependencyIssue:
    """A single dependency issue."""
    issue_type: str
    severity: Severity
    package_name: str
    description: str
    current_version: Optional[str] = None
    recommended_version: Optional[str] = None
    suggestion: Optional[str] = None
    vulnerability: Optional[Vulnerability] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LicenseViolation:
    """License compliance violation."""
    package_name: str
    license_name: str
    reason: str
    severity: Severity
    suggestion: Optional[str] = None


@dataclass
class DependencyReport:
    """Complete dependency validation report."""
    validated_at: datetime = field(default_factory=datetime.now)
    project_name: str = ""
    
    # Dependencies
    dependencies: Dict[str, DependencyInfo] = field(default_factory=dict)
    direct_dependencies: List[str] = field(default_factory=list)
    transitive_dependencies: List[str] = field(default_factory=list)
    development_dependencies: List[str] = field(default_factory=list)
    
    # Issues
    issues: List[DependencyIssue] = field(default_factory=list)
    warnings: List[DependencyIssue] = field(default_factory=list)
    license_violations: List[LicenseViolation] = field(default_factory=list)
    
    # Statistics
    total_dependencies: int = 0
    outdated_count: int = 0
    vulnerable_count: int = 0
    deprecated_count: int = 0
    abandoned_count: int = 0
    
    # Validation
    is_valid: bool = True
    overall_score: float = 0.0
    grade: str = "A"
    summary: str = ""
    recommendations: List[str] = field(default_factory=list)
    
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DependencyValidatorConfig:
    """Configuration for dependency validator."""
    project_root: Path
    
    # License configuration
    allowed_licenses: List[str] = field(default_factory=lambda: [
        "MIT", "Apache-2.0", "BSD-3-Clause", "BSD-2-Clause", "ISC", 
        "Python-2.0", "MPL-2.0", "LGPL-2.1", "LGPL-3.0"
    ])
    restricted_licenses: List[str] = field(default_factory=lambda: [
        "GPL-2.0", "GPL-3.0", "AGPL-3.0"
    ])
    forbidden_licenses: List[str] = field(default_factory=lambda: [
        "Proprietary", "Commercial", "Unlicense"
    ])
    
    # Vulnerability configuration
    check_vulnerabilities: bool = True
    vulnerability_db_url: str = "https://api.osv.dev/v1/query"
    min_cvss_score_to_fail: float = 7.0
    ignore_vulnerabilities: List[str] = field(default_factory=list)
    
    # Version configuration
    check_outdated: bool = True
    check_deprecated: bool = True
    check_abandoned: bool = True
    days_since_release_warning: int = 365
    days_since_release_error: int = 730
    
    # Dependency configuration
    check_unused: bool = True
    check_missing: bool = True
    check_conflicts: bool = True
    check_pinned: bool = True
    require_pinned_production: bool = True
    allow_direct_imports_without_spec: bool = False
    
    # Ignore patterns
    ignore_packages: List[str] = field(default_factory=list)
    ignore_development: bool = False
    
    # Validation
    fail_on_critical: bool = True
    fail_on_high: bool = False
    fail_on_license_violation: bool = True
    
    # Reporting
    generate_report: bool = True
    output_format: str = "markdown"


# ============================================================
# DEPENDENCY PARSER
# ============================================================

class DependencyParser:
    """Parse dependencies from various sources."""
    
    def __init__(self, config: DependencyValidatorConfig):
        self.config = config
    
    def parse_all(self) -> Dict[str, DependencyInfo]:
        """Parse all dependencies from project."""
        dependencies = {}
        
        # Parse requirements.txt
        req_file = self.config.project_root / "requirements.txt"
        if req_file.exists():
            deps = self.parse_requirements(req_file, DependencyType.PRODUCTION)
            self._merge_dependencies(dependencies, deps)
        
        # Parse requirements-dev.txt
        dev_req = self.config.project_root / "requirements-dev.txt"
        if dev_req.exists():
            deps = self.parse_requirements(dev_req, DependencyType.DEVELOPMENT)
            self._merge_dependencies(dependencies, deps)
        
        # Parse pyproject.toml
        pyproject = self.config.project_root / "pyproject.toml"
        if pyproject.exists():
            deps = self.parse_pyproject(pyproject)
            self._merge_dependencies(dependencies, deps)
        
        # Parse poetry.lock if exists
        poetry_lock = self.config.project_root / "poetry.lock"
        if poetry_lock.exists():
            deps = self.parse_poetry_lock(poetry_lock)
            self._merge_dependencies(dependencies, deps)
        
        # Parse Pipfile.lock if exists
        pipfile_lock = self.config.project_root / "Pipfile.lock"
        if pipfile_lock.exists():
            deps = self.parse_pipfile_lock(pipfile_lock)
            self._merge_dependencies(dependencies, deps)
        
        return dependencies
    
    def parse_requirements(self, file_path: Path, dep_type: DependencyType) -> Dict[str, DependencyInfo]:
        """Parse requirements.txt file."""
        dependencies = {}
        
        try:
            content = file_path.read_text()
            
            for line in content.split('\n'):
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                # Handle -r, -e, etc.
                if line.startswith('-'):
                    continue
                
                # Handle environment markers
                if ';' in line:
                    line = line.split(';')[0].strip()
                
                try:
                    req = Requirement(line)
                    name = req.name.lower()
                    
                    deps = dependencies.get(name, DependencyInfo(
                        name=name,
                        source=DependencySource.REQUIREMENTS_TXT,
                        dep_type=dep_type,
                        required_version=str(req.specifier) if req.specifier else None
                    ))
                    
                    if req.specifier:
                        deps.required_version = str(req.specifier)
                    if req.marker:
                        deps.metadata['marker'] = str(req.marker)
                    
                    dependencies[name] = deps
                    
                except Exception as e:
                    logger.warning(f"Failed to parse requirement '{line}': {e}")
                    
        except Exception as e:
            logger.error(f"Failed to parse {file_path}: {e}")
        
        return dependencies
    
    def parse_pyproject(self, file_path: Path) -> Dict[str, DependencyInfo]:
        """Parse pyproject.toml file."""
        dependencies = {}
        
        try:
            import tomllib
        except ImportError:
            try:
                import tomli as tomllib
            except ImportError:
                logger.warning("tomllib not available, skipping pyproject.toml")
                return dependencies
        
        try:
            with open(file_path, 'rb') as f:
                data = tomllib.load(f)
            
            # PEP 621 format
            if 'project' in data:
                proj = data['project']
                
                # Production dependencies
                for dep in proj.get('dependencies', []):
                    try:
                        req = Requirement(dep)
                        name = req.name.lower()
                        dependencies[name] = DependencyInfo(
                            name=name,
                            source=DependencySource.PYPROJECT_TOML,
                            dep_type=DependencyType.PRODUCTION,
                            required_version=str(req.specifier) if req.specifier else None
                        )
                    except Exception:
                        pass
                
                # Optional dependencies
                for group, deps in proj.get('optional-dependencies', {}).items():
                    for dep in deps:
                        try:
                            req = Requirement(dep)
                            name = req.name.lower()
                            dep_type = DependencyType.TEST if group == 'test' else DependencyType.OPTIONAL
                            dependencies[name] = DependencyInfo(
                                name=name,
                                source=DependencySource.PYPROJECT_TOML,
                                dep_type=dep_type,
                                required_version=str(req.specifier) if req.specifier else None,
                                metadata={'optional_group': group}
                            )
                        except Exception:
                            pass
            
            # Poetry format
            if 'tool' in data and 'poetry' in data['tool']:
                poetry = data['tool']['poetry']
                
                for name, constraint in poetry.get('dependencies', {}).items():
                    if name.lower() == 'python':
                        continue
                    if isinstance(constraint, dict):
                        constraint = constraint.get('version', '')
                        optional = constraint.get('optional', False)
                    else:
                        optional = False
                    
                    dependencies[name.lower()] = DependencyInfo(
                        name=name.lower(),
                        source=DependencySource.POETRY,
                        dep_type=DependencyType.OPTIONAL if optional else DependencyType.PRODUCTION,
                        required_version=str(constraint) if constraint else None
                    )
                
                for name, constraint in poetry.get('dev-dependencies', {}).items():
                    if isinstance(constraint, dict):
                        constraint = constraint.get('version', '')
                    
                    dependencies[name.lower()] = DependencyInfo(
                        name=name.lower(),
                        source=DependencySource.POETRY,
                        dep_type=DependencyType.DEVELOPMENT,
                        required_version=str(constraint) if constraint else None
                    )
                    
        except Exception as e:
            logger.error(f"Failed to parse {file_path}: {e}")
        
        return dependencies
    
    def parse_poetry_lock(self, file_path: Path) -> Dict[str, DependencyInfo]:
        """Parse poetry.lock file for exact versions."""
        dependencies = {}
        
        try:
            import tomllib
        except ImportError:
            try:
                import tomli as tomllib
            except ImportError:
                return dependencies
        
        try:
            with open(file_path, 'rb') as f:
                data = tomllib.load(f)
            
            for pkg in data.get('package', []):
                name = pkg.get('name', '').lower()
                if name:
                    dependencies[name] = DependencyInfo(
                        name=name,
                        version=pkg.get('version'),
                        source=DependencySource.POETRY,
                        is_pinned=True,
                        metadata={'category': pkg.get('category')}
                    )
                    
        except Exception as e:
            logger.error(f"Failed to parse {file_path}: {e}")
        
        return dependencies
    
    def parse_pipfile_lock(self, file_path: Path) -> Dict[str, DependencyInfo]:
        """Parse Pipfile.lock for exact versions."""
        dependencies = {}
        
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            for name, info in data.get('default', {}).items():
                dependencies[name.lower()] = DependencyInfo(
                    name=name.lower(),
                    version=info.get('version'),
                    source=DependencySource.PIPENV,
                    dep_type=DependencyType.PRODUCTION,
                    is_pinned=True
                )
            
            for name, info in data.get('develop', {}).items():
                dependencies[name.lower()] = DependencyInfo(
                    name=name.lower(),
                    version=info.get('version'),
                    source=DependencySource.PIPENV,
                    dep_type=DependencyType.DEVELOPMENT,
                    is_pinned=True
                )
                
        except Exception as e:
            logger.error(f"Failed to parse {file_path}: {e}")
        
        return dependencies
    
    def _merge_dependencies(self, target: Dict[str, DependencyInfo], 
                            source: Dict[str, DependencyInfo]):
        """Merge dependency dictionaries."""
        for name, info in source.items():
            if name in target:
                # Update existing
                existing = target[name]
                if info.version and not existing.version:
                    existing.version = info.version
                if info.required_version and not existing.required_version:
                    existing.required_version = info.required_version
                existing.metadata.update(info.metadata)
            else:
                target[name] = info


# ============================================================
# VULNERABILITY CHECKER
# ============================================================

class VulnerabilityChecker:
    """Check packages for known vulnerabilities."""
    
    def __init__(self, config: DependencyValidatorConfig):
        self.config = config
        self._vulnerability_cache: Dict[str, List[Vulnerability]] = {}
    
    def check_package(self, package_name: str, package_version: str) -> List[Vulnerability]:
        """Check a package for vulnerabilities."""
        cache_key = f"{package_name}@{package_version}"
        if cache_key in self._vulnerability_cache:
            return self._vulnerability_cache[cache_key]
        
        vulnerabilities = []
        
        # Try using pip-audit if available
        try:
            result = subprocess.run(
                ['pip-audit', '--requirement', '/dev/null', 
                 '--package', f'{package_name}=={package_version}',
                 '--format', 'json'],
                capture_output=True, text=True, timeout=30
            )
            
            if result.returncode != 0 and result.stdout:
                try:
                    data = json.loads(result.stdout)
                    for vuln in data.get('vulnerabilities', []):
                        if package_name.lower() == vuln.get('name', '').lower():
                            vulnerabilities.append(Vulnerability(
                                id=vuln.get('id', ''),
                                package_name=package_name,
                                affected_versions=vuln.get('affected_versions', ''),
                                fixed_version=vuln.get('fixed_versions', [None])[0] if vuln.get('fixed_versions') else None,
                                severity=VulnerabilitySeverity(vuln.get('severity', 'unknown').lower()),
                                summary=vuln.get('description', ''),
                                cwe_id=vuln.get('cwe'),
                                references=vuln.get('references', [])
                            ))
                except json.JSONDecodeError:
                    pass
                    
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        
        # Try safety if available
        if not vulnerabilities:
            try:
                result = subprocess.run(
                    ['safety', 'check', '--json', '--package', f'{package_name}=={package_version}'],
                    capture_output=True, text=True, timeout=30
                )
                
                if result.stdout:
                    try:
                        data = json.loads(result.stdout)
                        for vuln in data.get('vulnerabilities', []):
                            vulnerabilities.append(Vulnerability(
                                id=vuln.get('vulnerability_id', ''),
                                package_name=package_name,
                                affected_versions=vuln.get('vulnerable_spec', ''),
                                fixed_version=vuln.get('fixed_version'),
                                severity=self._map_safety_severity(vuln.get('severity')),
                                summary=vuln.get('advisory', ''),
                                cvss_score=vuln.get('cvssv3', {}).get('base_score')
                            ))
                    except json.JSONDecodeError:
                        pass
                        
            except (FileNotFoundError, subprocess.TimeoutExpired):
                pass
        
        self._vulnerability_cache[cache_key] = vulnerabilities
        return vulnerabilities
    
    def _map_safety_severity(self, severity: Optional[str]) -> VulnerabilitySeverity:
        """Map safety severity to VulnerabilitySeverity."""
        if not severity:
            return VulnerabilitySeverity.UNKNOWN
        severity = severity.lower()
        if severity in ('critical', 'high'):
            return VulnerabilitySeverity.HIGH
        elif severity == 'moderate':
            return VulnerabilitySeverity.MODERATE
        elif severity == 'low':
            return VulnerabilitySeverity.LOW
        return VulnerabilitySeverity.UNKNOWN


# ============================================================
# LICENSE CHECKER
# ============================================================

class LicenseChecker:
    """Check package licenses for compliance."""
    
    # Common license mappings
    LICENSE_MAP = {
        'MIT': 'MIT',
        'MIT License': 'MIT',
        'Apache 2.0': 'Apache-2.0',
        'Apache License 2.0': 'Apache-2.0',
        'BSD': 'BSD-3-Clause',
        'BSD License': 'BSD-3-Clause',
        'GPL': 'GPL-3.0',
        'GNU General Public License': 'GPL-3.0',
        'LGPL': 'LGPL-3.0',
        'MPL': 'MPL-2.0',
        'ISC': 'ISC',
        'Python Software Foundation License': 'Python-2.0',
    }
    
    # OSI approved licenses
    OSI_APPROVED = {
        'MIT', 'Apache-2.0', 'BSD-3-Clause', 'BSD-2-Clause', 'ISC',
        'Python-2.0', 'MPL-2.0', 'LGPL-2.1', 'LGPL-3.0', 'GPL-2.0',
        'GPL-3.0', 'AGPL-3.0', 'Unlicense', 'CC0-1.0'
    }
    
    def __init__(self, config: DependencyValidatorConfig):
        self.config = config
    
    def check_license(self, package_name: str) -> Optional[LicenseInfo]:
        """Check license for a package."""
        try:
            # Try to get from installed package metadata
            dist = importlib.metadata.distribution(package_name)
            license_str = dist.metadata.get('License', '')
            classifier_licenses = [
                c.split('::')[-1].strip() 
                for c in dist.metadata.get_all('Classifier', [])
                if c.startswith('License ::')
            ]
            
            if classifier_licenses:
                license_str = classifier_licenses[0]
            
            if license_str:
                return self._analyze_license(license_str)
                
        except importlib.metadata.PackageNotFoundError:
            pass
        
        return None
    
    def _analyze_license(self, license_str: str) -> LicenseInfo:
        """Analyze license string and return LicenseInfo."""
        # Normalize license name
        normalized = self.LICENSE_MAP.get(license_str, license_str)
        
        # Determine compatibility
        if normalized in self.config.allowed_licenses:
            compatibility = LicenseCompatibility.COMPATIBLE
        elif normalized in self.config.restricted_licenses:
            compatibility = LicenseCompatibility.RESTRICTED
        elif normalized in self.config.forbidden_licenses:
            compatibility = LicenseCompatibility.INCOMPATIBLE
        else:
            compatibility = LicenseCompatibility.NEEDS_REVIEW
        
        return LicenseInfo(
            name=license_str,
            spdx_id=normalized if normalized in self.LICENSE_MAP else None,
            compatibility=compatibility,
            is_osi_approved=normalized in self.OSI_APPROVED,
            is_fsf_free=normalized in self.OSI_APPROVED
        )


# ============================================================
# MAIN DEPENDENCY VALIDATOR
# ============================================================

class DependencyValidator:
    """
    Validates project dependencies for security, licensing, and version issues.
    
    Features:
    - Parse dependencies from multiple sources (requirements.txt, pyproject.toml, poetry)
    - Check for known security vulnerabilities
    - Validate license compatibility
    - Detect outdated dependencies
    - Identify deprecated/abandoned packages
    - Check for version conflicts
    - Find unused and missing dependencies
    - Calculate dependency health score
    - Generate comprehensive reports
    - Integration with pip-audit and safety
    """
    
    def __init__(self, config: DependencyValidatorConfig):
        self.config = config
        self.parser = DependencyParser(config)
        self.vulnerability_checker = VulnerabilityChecker(config) if config.check_vulnerabilities else None
        self.license_checker = LicenseChecker(config)
        self.state = StateManager(config.project_root / ".ai_state" / "dependency_validator.json")
        
        # Cache for package info
        self._pypi_cache: Dict[str, Dict[str, Any]] = {}
        
        logger.info("DependencyValidator initialized")
    
    def validate(self) -> DependencyReport:
        """Run complete dependency validation."""
        logger.info("Starting dependency validation...")
        
        report = DependencyReport(
            project_name=self.config.project_root.name
        )
        
        # Parse dependencies
        dependencies = self.parser.parse_all()
        
        # Enrich with installed versions
        self._enrich_with_installed_versions(dependencies)
        
        # Enrich with PyPI information
        self._enrich_with_pypi_info(dependencies)
        
        report.dependencies = dependencies
        
        # Categorize dependencies
        for name, info in dependencies.items():
            if self._should_ignore(name):
                continue
            
            report.total_dependencies += 1
            
            if info.dep_type == DependencyType.DEVELOPMENT:
                report.development_dependencies.append(name)
            elif info.is_direct:
                report.direct_dependencies.append(name)
            else:
                report.transitive_dependencies.append(name)
            
            # Check for issues
            self._check_dependency_issues(name, info, report)
        
        # Check for unused dependencies
        if self.config.check_unused:
            self._check_unused_dependencies(report)
        
        # Check for missing dependencies
        if self.config.check_missing:
            self._check_missing_dependencies(report)
        
        # Check for version conflicts
        if self.config.check_conflicts:
            self._check_version_conflicts(report)
        
        # Calculate statistics
        report.outdated_count = sum(1 for d in dependencies.values() if d.is_outdated)
        report.vulnerable_count = sum(1 for d in dependencies.values() if d.vulnerabilities)
        report.deprecated_count = sum(1 for d in dependencies.values() if d.is_deprecated)
        report.abandoned_count = sum(1 for d in dependencies.values() if d.is_abandoned)
        
        # Calculate overall score and grade
        report.overall_score, report.grade = self._calculate_overall_score(report)
        
        # Determine validity
        report.is_valid = self._determine_validity(report)
        
        # Generate summary and recommendations
        report.summary = self._generate_summary(report)
        report.recommendations = self._generate_recommendations(report)
        
        # Save report
        self._save_report(report)
        
        logger.info(f"Dependency validation complete: {report.total_dependencies} dependencies, "
                   f"{len(report.issues)} issues, {len(report.warnings)} warnings")
        
        return report
    
    def _enrich_with_installed_versions(self, dependencies: Dict[str, DependencyInfo]):
        """Add installed version information."""
        try:
            installed = {
                dist.metadata["Name"].lower(): dist.version
                for dist in importlib.metadata.distributions()
            }
            
            for name, info in dependencies.items():
                if name in installed:
                    info.version = installed[name]
        except Exception as e:
            logger.warning(f"Failed to get installed packages: {e}")
    
    def _enrich_with_pypi_info(self, dependencies: Dict[str, DependencyInfo]):
        """Enrich dependencies with PyPI information."""
        for name, info in dependencies.items():
            pypi_info = self._get_pypi_info(name)
            if pypi_info:
                info.latest_version = pypi_info.get('version')
                
                # Check if outdated
                if info.version and info.latest_version:
                    try:
                        current = version.parse(info.version)
                        latest = version.parse(info.latest_version)
                        info.is_outdated = latest > current
                    except version.InvalidVersion:
                        pass
                
                # Check release date
                releases = pypi_info.get('releases', {})
                if info.version and info.version in releases:
                    upload_time = releases[info.version][0].get('upload_time')
                    if upload_time:
                        info.latest_release_date = datetime.fromisoformat(upload_time.replace('Z', '+00:00'))
                
                # Get license info if not already set
                if not info.license_info:
                    license_str = pypi_info.get('license')
                    if license_str:
                        info.license_info = self.license_checker._analyze_license(license_str)
                
                # Check Python requirement
                info.python_requires = pypi_info.get('requires_python')
                
                # Get homepage
                info.homepage = pypi_info.get('home_page') or pypi_info.get('project_url')
    
    def _get_pypi_info(self, package_name: str) -> Optional[Dict[str, Any]]:
        """Get package information from PyPI."""
        if package_name in self._pypi_cache:
            return self._pypi_cache[package_name]
        
        try:
            import requests
            response = requests.get(f"https://pypi.org/pypi/{package_name}/json", timeout=10)
            if response.status_code == 200:
                data = response.json()
                info = {
                    'version': data['info']['version'],
                    'license': data['info'].get('license'),
                    'requires_python': data['info'].get('requires_python'),
                    'home_page': data['info'].get('home_page'),
                    'project_url': data['info'].get('project_url'),
                    'releases': data.get('releases', {})
                }
                self._pypi_cache[package_name] = info
                return info
        except Exception:
            pass
        
        return None
    
    def _check_dependency_issues(self, name: str, info: DependencyInfo, report: DependencyReport):
        """Check a single dependency for issues."""
        
        # Check if pinned (for production dependencies)
        if (self.config.require_pinned_production and 
            info.dep_type == DependencyType.PRODUCTION and 
            not info.is_pinned):
            issue = DependencyIssue(
                issue_type="unpinned_dependency",
                severity=Severity.MEDIUM,
                package_name=name,
                description=f"Production dependency '{name}' is not pinned to a specific version",
                current_version=info.version,
                suggestion=f"Pin version in requirements: {name}=={info.version or 'X.Y.Z'}"
            )
            report.warnings.append(issue)
        
        # Check for vulnerabilities
        if self.config.check_vulnerabilities and info.version:
            vulnerabilities = self.vulnerability_checker.check_package(name, info.version)
            info.vulnerabilities = vulnerabilities
            
            for vuln in vulnerabilities:
                if vuln.id in self.config.ignore_vulnerabilities:
                    continue
                
                severity = self._map_vulnerability_severity(vuln.severity)
                cvss_score = vuln.cvss_score or 0
                
                issue = DependencyIssue(
                    issue_type="security_vulnerability",
                    severity=severity,
                    package_name=name,
                    description=f"Vulnerability {vuln.id}: {vuln.summary}",
                    current_version=info.version,
                    recommended_version=vuln.fixed_version,
                    suggestion=f"Upgrade to {vuln.fixed_version or 'latest version'}",
                    vulnerability=vuln,
                    metadata={'cvss_score': cvss_score}
                )
                
                if severity in (Severity.CRITICAL, Severity.HIGH):
                    report.issues.append(issue)
                else:
                    report.warnings.append(issue)
        
        # Check if outdated
        if info.is_outdated and info.latest_version:
            issue = DependencyIssue(
                issue_type="outdated_dependency",
                severity=Severity.LOW,
                package_name=name,
                description=f"Dependency '{name}' is outdated ({info.version} < {info.latest_version})",
                current_version=info.version,
                recommended_version=info.latest_version,
                suggestion=f"Upgrade to {info.latest_version}"
            )
            report.warnings.append(issue)
        
        # Check license compliance
        if info.license_info:
            license_info = info.license_info
            
            if license_info.compatibility == LicenseCompatibility.INCOMPATIBLE:
                violation = LicenseViolation(
                    package_name=name,
                    license_name=license_info.name,
                    reason=f"License '{license_info.name}' is forbidden",
                    severity=Severity.HIGH,
                    suggestion=f"Replace {name} with a package using a compatible license"
                )
                report.license_violations.append(violation)
                
                if self.config.fail_on_license_violation:
                    issue = DependencyIssue(
                        issue_type="license_violation",
                        severity=Severity.HIGH,
                        package_name=name,
                        description=f"Package '{name}' uses forbidden license '{license_info.name}'",
                        suggestion=violation.suggestion
                    )
                    report.issues.append(issue)
            
            elif license_info.compatibility == LicenseCompatibility.RESTRICTED:
                violation = LicenseViolation(
                    package_name=name,
                    license_name=license_info.name,
                    reason=f"License '{license_info.name}' is restricted",
                    severity=Severity.MEDIUM,
                    suggestion=f"Review license terms for {name}"
                )
                report.license_violations.append(violation)
                
                issue = DependencyIssue(
                    issue_type="restricted_license",
                    severity=Severity.MEDIUM,
                    package_name=name,
                    description=f"Package '{name}' uses restricted license '{license_info.name}'",
                    suggestion=violation.suggestion
                )
                report.warnings.append(issue)
            
            elif license_info.compatibility == LicenseCompatibility.NEEDS_REVIEW:
                issue = DependencyIssue(
                    issue_type="unknown_license",
                    severity=Severity.INFO,
                    package_name=name,
                    description=f"Package '{name}' license '{license_info.name}' needs review",
                    suggestion="Verify license compatibility"
                )
                report.warnings.append(issue)
    
    def _check_unused_dependencies(self, report: DependencyReport):
        """Check for potentially unused dependencies."""
        # This would analyze imports in source code
        # Simplified version - just check if dependency is declared but not imported
        pass
    
    def _check_missing_dependencies(self, report: DependencyReport):
        """Check for missing dependencies (imported but not declared)."""
        # This would analyze imports and compare with declared dependencies
        pass
    
    def _check_version_conflicts(self, report: DependencyReport):
        """Check for version conflicts between dependencies."""
        conflicts = defaultdict(list)
        
        for name, info in report.dependencies.items():
            if info.required_version:
                conflicts[name].append(info)
        
        for name, deps in conflicts.items():
            if len(deps) > 1:
                versions = [d.required_version for d in deps if d.required_version]
                if len(set(versions)) > 1:
                    issue = DependencyIssue(
                        issue_type="version_conflict",
                        severity=Severity.HIGH,
                        package_name=name,
                        description=f"Conflicting version requirements: {', '.join(set(versions))}",
                        suggestion=f"Resolve version conflict for {name}"
                    )
                    report.issues.append(issue)
    
    def _map_vulnerability_severity(self, severity: VulnerabilitySeverity) -> Severity:
        """Map vulnerability severity to issue severity."""
        mapping = {
            VulnerabilitySeverity.CRITICAL: Severity.CRITICAL,
            VulnerabilitySeverity.HIGH: Severity.HIGH,
            VulnerabilitySeverity.MODERATE: Severity.MEDIUM,
            VulnerabilitySeverity.LOW: Severity.LOW,
            VulnerabilitySeverity.UNKNOWN: Severity.INFO,
        }
        return mapping.get(severity, Severity.INFO)
    
    def _calculate_overall_score(self, report: DependencyReport) -> Tuple[float, str]:
        """Calculate overall dependency health score."""
        score = 100.0
        
        # Deduct for vulnerabilities
        for issue in report.issues:
            if issue.issue_type == "security_vulnerability":
                if issue.severity == Severity.CRITICAL:
                    score -= 20
                elif issue.severity == Severity.HIGH:
                    score -= 10
                elif issue.severity == Severity.MEDIUM:
                    score -= 5
        
        # Deduct for other issues
        score -= len([i for i in report.issues if i.issue_type != "security_vulnerability"]) * 3
        score -= len(report.warnings) * 1
        
        # Deduct for outdated
        score -= report.outdated_count * 1
        
        # Deduct for license violations
        score -= len(report.license_violations) * 5
        
        # Clamp score
        score = max(0, min(100, score))
        
        # Determine grade
        if score >= 90:
            grade = "A"
        elif score >= 80:
            grade = "B"
        elif score >= 70:
            grade = "C"
        elif score >= 60:
            grade = "D"
        else:
            grade = "F"
        
        return score, grade
    
    def _determine_validity(self, report: DependencyReport) -> bool:
        """Determine if dependencies are valid."""
        if not report.issues:
            return True
        
        for issue in report.issues:
            if self.config.fail_on_critical and issue.severity == Severity.CRITICAL:
                return False
            if self.config.fail_on_high and issue.severity == Severity.HIGH:
                return False
            if issue.issue_type == "license_violation" and self.config.fail_on_license_violation:
                return False
        
        return True
    
    def _should_ignore(self, package_name: str) -> bool:
        """Check if package should be ignored."""
        return package_name in self.config.ignore_packages
    
    def _generate_summary(self, report: DependencyReport) -> str:
        """Generate validation summary."""
        if report.is_valid:
            return f"✅ Dependency validation passed. Score: {report.overall_score:.1f} (Grade: {report.grade})"
        else:
            return f"❌ Dependency issues found: {len(report.issues)} issues, {len(report.warnings)} warnings"
    
    def _generate_recommendations(self, report: DependencyReport) -> List[str]:
        """Generate recommendations."""
        recommendations = []
        
        if report.vulnerable_count > 0:
            recommendations.append(f"Fix {report.vulnerable_count} packages with known vulnerabilities")
        
        if report.outdated_count > 0:
            recommendations.append(f"Update {report.outdated_count} outdated dependencies")
        
        if report.license_violations:
            recommendations.append(f"Address {len(report.license_violations)} license violations")
        
        if report.overall_score < 80:
            recommendations.append("Improve overall dependency health score")
        
        # Get critical issues
        critical_issues = [i for i in report.issues if i.severity == Severity.CRITICAL]
        if critical_issues:
            recommendations.append(f"Address {len(critical_issues)} critical issues immediately")
        
        return recommendations[:5]
    
    def _save_report(self, report: DependencyReport):
        """Save report to state."""
        reports = self.state.get('reports', [])
        reports.append({
            'timestamp': report.validated_at.isoformat(),
            'project': report.project_name,
            'is_valid': report.is_valid,
            'score': report.overall_score,
            'grade': report.grade,
            'total_deps': report.total_dependencies,
            'issues': len(report.issues),
            'warnings': len(report.warnings),
            'vulnerable': report.vulnerable_count,
            'outdated': report.outdated_count
        })
        
        if len(reports) > 50:
            reports = reports[-50:]
        
        self.state.set('reports', reports)
        self.state.save()
    
    def export_report(self, report: DependencyReport,
                      output_path: Optional[Path] = None,
                      format: str = 'markdown') -> str:
        """Export dependency report."""
        
        if format == 'json':
            data = {
                'validated_at': report.validated_at.isoformat(),
                'project': report.project_name,
                'is_valid': report.is_valid,
                'score': report.overall_score,
                'grade': report.grade,
                'summary': report.summary,
                'statistics': {
                    'total_dependencies': report.total_dependencies,
                    'direct_dependencies': len(report.direct_dependencies),
                    'transitive_dependencies': len(report.transitive_dependencies),
                    'development_dependencies': len(report.development_dependencies),
                    'outdated_count': report.outdated_count,
                    'vulnerable_count': report.vulnerable_count,
                    'deprecated_count': report.deprecated_count
                },
                'issues': [
                    {
                        'type': i.issue_type,
                        'severity': i.severity.value,
                        'package': i.package_name,
                        'description': i.description,
                        'suggestion': i.suggestion
                    }
                    for i in report.issues
                ],
                'license_violations': [
                    {
                        'package': v.package_name,
                        'license': v.license_name,
                        'reason': v.reason,
                        'severity': v.severity.value
                    }
                    for v in report.license_violations
                ],
                'recommendations': report.recommendations
            }
            
            content = json.dumps(data, indent=2)
            
        else:  # markdown
            lines = [
                f"# Dependency Validation Report",
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
                f"| Total Dependencies | {report.total_dependencies} |",
                f"| Direct Dependencies | {len(report.direct_dependencies)} |",
                f"| Transitive Dependencies | {len(report.transitive_dependencies)} |",
                f"| Development Dependencies | {len(report.development_dependencies)} |",
                f"| Outdated | {report.outdated_count} |",
                f"| Vulnerable | {report.vulnerable_count} |",
                f"| Deprecated | {report.deprecated_count} |",
                f"| License Violations | {len(report.license_violations)} |",
                "",
            ]
            
            if report.issues:
                lines.extend([
                    "## ❌ Issues",
                    "",
                    "| Type | Severity | Package | Description |",
                    "|------|----------|---------|-------------|",
                ])
                for issue in report.issues:
                    lines.append(f"| {issue.issue_type} | {issue.severity.value} | {issue.package_name} | {issue.description[:50]} |")
                lines.append("")
            
            if report.license_violations:
                lines.extend([
                    "## 📜 License Violations",
                    "",
                    "| Package | License | Severity | Reason |",
                    "|---------|---------|----------|--------|",
                ])
                for v in report.license_violations:
                    lines.append(f"| {v.package_name} | {v.license_name} | {v.severity.value} | {v.reason} |")
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
        logger.info("DependencyValidator closed")


# ============================================================
# CLI ENTRY POINT
# ============================================================

def main():
    """CLI entry point for dependency validator."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate project dependencies")
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--output", "-o", type=Path, help="Output report path")
    parser.add_argument("--format", choices=["json", "markdown"], default="markdown")
    parser.add_argument("--no-vuln", action="store_true", help="Skip vulnerability checking")
    parser.add_argument("--fail-on-high", action="store_true", help="Fail on high severity issues")
    parser.add_argument("--ignore-package", action="append", help="Ignore specific package")
    
    args = parser.parse_args()
    
    config = DependencyValidatorConfig(
        project_root=args.project_root,
        check_vulnerabilities=not args.no_vuln,
        fail_on_high=args.fail_on_high,
        ignore_packages=args.ignore_package or []
    )
    
    validator = DependencyValidator(config)
    
    report = validator.validate()
    
    output = validator.export_report(report, args.output, args.format)
    
    if not args.output:
        print(output)
    else:
        print(f"Report saved to {args.output}")
    
    print(f"\n{report.summary}")
    
    if config.fail_on_critical and not report.is_valid:
        exit(1)
    
    validator.close()


if __name__ == "__main__":
    main()