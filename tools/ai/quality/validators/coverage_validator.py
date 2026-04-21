#!/usr/bin/env python3
"""
Coverage Validator - Validates test coverage and enforces coverage thresholds.

Part of the Quality tools (validators/coverage_validator.py)

This coverage_validator.py provides:

1. Multiple Coverage Formats - JSON, XML (Cobertura), LCOV, pytest-cov
2. Comprehensive Metrics - Line, branch, statement, function, class coverage
3. Configurable Thresholds - Per metric with warning and error levels
4. File and Module Analysis - Aggregated and per-file coverage
5. Uncovered Code Identification - Finds completely uncovered files and blocks
6. Critical Coverage Gaps - Identifies high-priority coverage issues
7. Grade Calculation - A-F grade based on weighted coverage score
8. Coverage Trends - Historical tracking of coverage metrics
9. Actionable Recommendations - Specific suggestions for improvement
10. pytest-cov Integration - Can run tests automatically
11. Comprehensive Reporting - JSON and Markdown formats
12. Consecutive Uncovered Blocks - Finds large gaps in coverage

The coverage validator ensures your codebase maintains adequate test coverage and helps identify areas needing additional testing.
"""

import json
import subprocess
import xml.etree.ElementTree as ET
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

class CoverageType(str, Enum):
    """Type of coverage metric."""
    LINE = "line"
    BRANCH = "branch"
    STATEMENT = "statement"
    FUNCTION = "function"
    METHOD = "method"
    CLASS = "class"
    PATH = "path"
    CONDITION = "condition"


class CoverageFormat(str, Enum):
    """Coverage report format."""
    COVERAGE_JSON = "coverage_json"
    COVERAGE_XML = "coverage_xml"
    Pytest_Cov = "pytest_cov"
    COBERTURA = "cobertura"
    LCOV = "lcov"
    HTML = "html"


class Severity(str, Enum):
    """Severity of coverage violation."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


# ============================================================
# DATA MODELS
# ============================================================

@dataclass
class CoverageThreshold:
    """Threshold for a coverage metric."""
    coverage_type: CoverageType
    warning_threshold: float  # Percentage (0-100)
    error_threshold: float    # Percentage (0-100)
    scope: str = "global"     # global, module, class, function
    description: str = ""


@dataclass
class CoverageViolation:
    """A single coverage violation."""
    coverage_type: CoverageType
    severity: Severity
    entity_name: str
    file_path: str
    actual_coverage: float
    threshold: float
    description: str
    suggestion: Optional[str] = None
    line_ranges: List[Tuple[int, int]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FileCoverage:
    """Coverage metrics for a single file."""
    file_path: str
    lines_total: int = 0
    lines_covered: int = 0
    lines_missed: int = 0
    line_coverage: float = 0.0
    
    branches_total: int = 0
    branches_covered: int = 0
    branches_missed: int = 0
    branch_coverage: float = 0.0
    
    statements_total: int = 0
    statements_covered: int = 0
    statement_coverage: float = 0.0
    
    functions_total: int = 0
    functions_covered: int = 0
    function_coverage: float = 0.0
    
    classes_total: int = 0
    classes_covered: int = 0
    class_coverage: float = 0.0
    
    uncovered_lines: List[int] = field(default_factory=list)
    uncovered_branches: List[Tuple[int, int]] = field(default_factory=list)
    
    complexity: int = 0
    num_statements: int = 0
    
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ModuleCoverage:
    """Coverage metrics for a module/package."""
    name: str
    files: List[str] = field(default_factory=list)
    total_lines: int = 0
    covered_lines: int = 0
    line_coverage: float = 0.0
    branch_coverage: float = 0.0
    file_coverages: Dict[str, FileCoverage] = field(default_factory=dict)


@dataclass
class CoverageReport:
    """Complete coverage validation report."""
    validated_at: datetime = field(default_factory=datetime.now)
    project_name: str = ""
    
    # Overall metrics
    total_files: int = 0
    total_lines: int = 0
    covered_lines: int = 0
    line_coverage: float = 0.0
    
    total_branches: int = 0
    covered_branches: int = 0
    branch_coverage: float = 0.0
    
    total_statements: int = 0
    covered_statements: int = 0
    statement_coverage: float = 0.0
    
    total_functions: int = 0
    covered_functions: int = 0
    function_coverage: float = 0.0
    
    total_classes: int = 0
    covered_classes: int = 0
    class_coverage: float = 0.0
    
    # Detailed coverage
    file_coverages: Dict[str, FileCoverage] = field(default_factory=dict)
    module_coverages: Dict[str, ModuleCoverage] = field(default_factory=dict)
    
    # Violations
    violations: List[CoverageViolation] = field(default_factory=list)
    warnings: List[CoverageViolation] = field(default_factory=list)
    
    # Uncovered code
    uncovered_files: List[str] = field(default_factory=list)
    poorly_covered_files: List[Tuple[str, float]] = field(default_factory=list)
    critical_uncovered: List[Dict[str, Any]] = field(default_factory=list)
    
    # Validation
    is_valid: bool = True
    overall_score: float = 0.0
    grade: str = "A"
    summary: str = ""
    recommendations: List[str] = field(default_factory=list)
    
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CoverageValidatorConfig:
    """Configuration for coverage validator."""
    project_root: Path
    coverage_file: Optional[Path] = None
    coverage_format: CoverageFormat = CoverageFormat.COVERAGE_JSON
    
    # Thresholds
    thresholds: List[CoverageThreshold] = field(default_factory=lambda: [
        CoverageThreshold(CoverageType.LINE, 80.0, 70.0, "global", "Line coverage threshold"),
        CoverageThreshold(CoverageType.BRANCH, 75.0, 65.0, "global", "Branch coverage threshold"),
        CoverageThreshold(CoverageType.STATEMENT, 80.0, 70.0, "global", "Statement coverage threshold"),
        CoverageThreshold(CoverageType.FUNCTION, 85.0, 75.0, "global", "Function coverage threshold"),
        CoverageThreshold(CoverageType.CLASS, 90.0, 80.0, "global", "Class coverage threshold"),
    ])
    
    # File patterns
    source_patterns: List[str] = field(default_factory=lambda: ["engines/**/*.py", "tools/**/*.py"])
    test_patterns: List[str] = field(default_factory=lambda: ["tests/**/*.py", "test_*.py"])
    ignore_patterns: List[str] = field(default_factory=lambda: [
        "__pycache__", "*.pyc", ".git", ".venv", "venv", "dist", "build",
        "migrations", "alembic", "setup.py", "conftest.py", "__init__.py"
    ])
    
    # Validation
    fail_on_error: bool = True
    fail_on_warning: bool = False
    min_overall_coverage: float = 80.0
    min_file_coverage: float = 50.0
    
    # Reporting
    generate_report: bool = True
    output_format: str = "markdown"
    include_uncovered_lines: bool = True
    max_uncovered_to_show: int = 50


# ============================================================
# COVERAGE PARSERS
# ============================================================

class CoverageParser:
    """Parse coverage reports from various formats."""
    
    @staticmethod
    def parse_coverage_json(file_path: Path) -> Dict[str, FileCoverage]:
        """Parse coverage.json file."""
        file_coverages = {}
        
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            # coverage.py JSON format
            if 'files' in data:
                for file_path, file_data in data['files'].items():
                    fc = FileCoverage(file_path=file_path)
                    
                    # Summary
                    summary = file_data.get('summary', {})
                    fc.lines_total = summary.get('num_statements', 0)
                    fc.lines_covered = summary.get('covered_lines', 0)
                    fc.lines_missed = summary.get('missing_lines', 0)
                    fc.line_coverage = summary.get('percent_covered', 0.0)
                    
                    fc.branches_total = summary.get('num_branches', 0)
                    fc.branches_covered = summary.get('covered_branches', 0)
                    fc.branch_coverage = summary.get('percent_covered', 0.0) if fc.branches_total > 0 else 100.0
                    
                    # Uncovered lines
                    if 'missing_lines' in file_data:
                        fc.uncovered_lines = file_data['missing_lines']
                    
                    # Uncovered branches
                    if 'missing_branches' in file_data:
                        for branch in file_data['missing_branches']:
                            fc.uncovered_branches.append((branch['line'], branch.get('exit', 0)))
                    
                    file_coverages[file_path] = fc
            
            # Pytest-cov JSON format
            elif 'totals' in data:
                for file_path, file_data in data.get('files', {}).items():
                    fc = FileCoverage(file_path=file_path)
                    
                    summary = file_data.get('summary', {})
                    fc.statements_total = summary.get('num_statements', 0)
                    fc.statements_covered = summary.get('covered_statements', 0)
                    fc.statement_coverage = summary.get('percent_covered', 0.0)
                    
                    fc.lines_missed = file_data.get('excluded_lines', [])
                    
                    file_coverages[file_path] = fc
            
        except Exception as e:
            logger.error(f"Failed to parse coverage JSON: {e}")
        
        return file_coverages
    
    @staticmethod
    def parse_coverage_xml(file_path: Path) -> Dict[str, FileCoverage]:
        """Parse coverage.xml (Cobertura format)."""
        file_coverages = {}
        
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            # Find all class elements (files)
            for package in root.findall('.//package'):
                for cls in package.findall('classes/class'):
                    file_path = cls.get('filename', '')
                    if not file_path:
                        continue
                    
                    fc = FileCoverage(file_path=file_path)
                    
                    # Line coverage
                    lines = cls.find('lines')
                    if lines is not None:
                        for line in lines.findall('line'):
                            line_num = int(line.get('number', 0))
                            hits = int(line.get('hits', 0))
                            branch = line.get('branch', 'false')
                            
                            fc.lines_total += 1
                            if hits > 0:
                                fc.lines_covered += 1
                            else:
                                fc.uncovered_lines.append(line_num)
                            
                            if branch == 'true':
                                fc.branches_total += 2
                                condition_coverage = line.get('condition-coverage', '')
                                if condition_coverage:
                                    covered, total = condition_coverage.split('/')
                                    fc.branches_covered += int(covered.strip('%'))
                    
                    if fc.lines_total > 0:
                        fc.line_coverage = (fc.lines_covered / fc.lines_total) * 100
                    if fc.branches_total > 0:
                        fc.branch_coverage = (fc.branches_covered / fc.branches_total) * 100
                    
                    file_coverages[file_path] = fc
                    
        except Exception as e:
            logger.error(f"Failed to parse coverage XML: {e}")
        
        return file_coverages
    
    @staticmethod
    def parse_lcov(file_path: Path) -> Dict[str, FileCoverage]:
        """Parse LCOV format."""
        file_coverages = {}
        current_file = None
        
        try:
            with open(file_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    
                    if line.startswith('SF:'):
                        current_file = line[3:]
                        file_coverages[current_file] = FileCoverage(file_path=current_file)
                    
                    elif line.startswith('DA:') and current_file:
                        parts = line[3:].split(',')
                        line_num = int(parts[0])
                        hits = int(parts[1])
                        
                        fc = file_coverages[current_file]
                        fc.lines_total += 1
                        if hits > 0:
                            fc.lines_covered += 1
                        else:
                            fc.uncovered_lines.append(line_num)
                    
                    elif line.startswith('BRDA:') and current_file:
                        parts = line[5:].split(',')
                        fc = file_coverages[current_file]
                        fc.branches_total += 1
                        if parts[3] != '-':
                            fc.branches_covered += 1
                    
                    elif line.startswith('end_of_record'):
                        if current_file:
                            fc = file_coverages[current_file]
                            if fc.lines_total > 0:
                                fc.line_coverage = (fc.lines_covered / fc.lines_total) * 100
                            if fc.branches_total > 0:
                                fc.branch_coverage = (fc.branches_covered / fc.branches_total) * 100
                        current_file = None
                        
        except Exception as e:
            logger.error(f"Failed to parse LCOV file: {e}")
        
        return file_coverages
    
    @staticmethod
    def run_pytest_cov(project_root: Path, output_file: Path) -> Dict[str, FileCoverage]:
        """Run pytest with coverage and parse results."""
        try:
            cmd = [
                "pytest",
                f"--cov={project_root}",
                "--cov-report=json",
                f"--cov-report=term",
                "--cov-branch"
            ]
            
            result = subprocess.run(cmd, cwd=project_root, capture_output=True, text=True, timeout=300)
            
            # Find coverage.json
            coverage_json = project_root / "coverage.json"
            if coverage_json.exists():
                return CoverageParser.parse_coverage_json(coverage_json)
            
        except Exception as e:
            logger.error(f"Failed to run pytest-cov: {e}")
        
        return {}


# ============================================================
# MAIN COVERAGE VALIDATOR
# ============================================================

class CoverageValidator:
    """
    Validates test coverage and enforces coverage thresholds.
    
    Features:
    - Multiple coverage formats (JSON, XML, LCOV)
    - Line, branch, statement, function, class coverage
    - Configurable thresholds per metric
    - File and module level analysis
    - Uncovered code identification
    - Coverage trend analysis
    - Grade calculation
    - Comprehensive reporting
    - Integration with pytest-cov
    """
    
    def __init__(self, config: CoverageValidatorConfig):
        self.config = config
        self.state = StateManager(config.project_root / ".ai_state" / "coverage_validator.json")
        
        # Build threshold lookup
        self.threshold_map: Dict[Tuple[CoverageType, str], CoverageThreshold] = {}
        for threshold in config.thresholds:
            self.threshold_map[(threshold.coverage_type, threshold.scope)] = threshold
        
        logger.info("CoverageValidator initialized")
    
    def validate(self) -> CoverageReport:
        """Run complete coverage validation."""
        logger.info("Starting coverage validation...")
        
        report = CoverageReport(
            project_name=self.config.project_root.name
        )
        
        # Get coverage data
        file_coverages = self._get_coverage_data()
        
        if not file_coverages:
            logger.warning("No coverage data found")
            report.summary = "No coverage data available"
            return report
        
        report.file_coverages = file_coverages
        
        # Calculate overall metrics
        self._calculate_overall_metrics(report)
        
        # Build module coverages
        report.module_coverages = self._build_module_coverages(file_coverages)
        
        # Check thresholds
        self._check_thresholds(report)
        
        # Find uncovered and poorly covered files
        report.uncovered_files = [
            f for f, fc in file_coverages.items() 
            if fc.line_coverage == 0 and not self._is_test_file(f)
        ]
        
        report.poorly_covered_files = [
            (f, fc.line_coverage) for f, fc in file_coverages.items()
            if fc.line_coverage < self.config.min_file_coverage and not self._is_test_file(f)
        ]
        report.poorly_covered_files.sort(key=lambda x: x[1])
        
        # Identify critical uncovered code
        report.critical_uncovered = self._identify_critical_uncovered(report)
        
        # Calculate overall score and grade
        report.overall_score, report.grade = self._calculate_overall_score(report)
        
        # Determine validity
        report.is_valid = len(report.violations) == 0
        if self.config.fail_on_warning and report.warnings:
            report.is_valid = False
        
        if report.line_coverage < self.config.min_overall_coverage:
            report.is_valid = False
        
        # Generate summary and recommendations
        report.summary = self._generate_summary(report)
        report.recommendations = self._generate_recommendations(report)
        
        # Save report
        self._save_report(report)
        
        logger.info(f"Coverage validation complete: {report.line_coverage:.1f}% line coverage")
        
        return report
    
    def _get_coverage_data(self) -> Dict[str, FileCoverage]:
        """Get coverage data from configured source."""
        if self.config.coverage_file:
            if self.config.coverage_format == CoverageFormat.COVERAGE_JSON:
                return CoverageParser.parse_coverage_json(self.config.coverage_file)
            elif self.config.coverage_format == CoverageFormat.COVERAGE_XML:
                return CoverageParser.parse_coverage_xml(self.config.coverage_file)
            elif self.config.coverage_format == CoverageFormat.LCOV:
                return CoverageParser.parse_lcov(self.config.coverage_file)
        
        # Try to find coverage file automatically
        coverage_files = [
            self.config.project_root / "coverage.json",
            self.config.project_root / "coverage.xml",
            self.config.project_root / "coverage.lcov",
            self.config.project_root / "htmlcov" / "coverage.json",
        ]
        
        for cov_file in coverage_files:
            if cov_file.exists():
                if cov_file.suffix == '.json':
                    return CoverageParser.parse_coverage_json(cov_file)
                elif cov_file.suffix == '.xml':
                    return CoverageParser.parse_coverage_xml(cov_file)
                elif cov_file.suffix == '.lcov':
                    return CoverageParser.parse_lcov(cov_file)
        
        # Run pytest-cov as fallback
        return CoverageParser.run_pytest_cov(self.config.project_root, 
                                             self.config.project_root / "coverage.json")
    
    def _calculate_overall_metrics(self, report: CoverageReport):
        """Calculate overall coverage metrics."""
        for fc in report.file_coverages.values():
            if self._is_test_file(fc.file_path):
                continue
            
            report.total_files += 1
            
            report.total_lines += fc.lines_total
            report.covered_lines += fc.lines_covered
            
            report.total_branches += fc.branches_total
            report.covered_branches += fc.branches_covered
            
            report.total_statements += fc.statements_total
            report.covered_statements += fc.statements_covered
            
            report.total_functions += fc.functions_total
            report.covered_functions += fc.functions_covered
            
            report.total_classes += fc.classes_total
            report.covered_classes += fc.classes_covered
        
        if report.total_lines > 0:
            report.line_coverage = (report.covered_lines / report.total_lines) * 100
        if report.total_branches > 0:
            report.branch_coverage = (report.covered_branches / report.total_branches) * 100
        if report.total_statements > 0:
            report.statement_coverage = (report.covered_statements / report.total_statements) * 100
        if report.total_functions > 0:
            report.function_coverage = (report.covered_functions / report.total_functions) * 100
        if report.total_classes > 0:
            report.class_coverage = (report.covered_classes / report.total_classes) * 100
    
    def _build_module_coverages(self, file_coverages: Dict[str, FileCoverage]) -> Dict[str, ModuleCoverage]:
        """Build module-level coverage aggregations."""
        modules = {}
        
        for file_path, fc in file_coverages.items():
            if self._is_test_file(file_path):
                continue
            
            # Extract module name from file path
            parts = Path(file_path).parts
            if len(parts) > 1:
                module_name = parts[0]
            else:
                module_name = "root"
            
            if module_name not in modules:
                modules[module_name] = ModuleCoverage(name=module_name)
            
            module = modules[module_name]
            module.files.append(file_path)
            module.total_lines += fc.lines_total
            module.covered_lines += fc.lines_covered
            module.file_coverages[file_path] = fc
        
        # Calculate module coverage
        for module in modules.values():
            if module.total_lines > 0:
                module.line_coverage = (module.covered_lines / module.total_lines) * 100
            
            # Calculate branch coverage
            total_branches = sum(fc.branches_total for fc in module.file_coverages.values())
            covered_branches = sum(fc.branches_covered for fc in module.file_coverages.values())
            if total_branches > 0:
                module.branch_coverage = (covered_branches / total_branches) * 100
        
        return modules
    
    def _check_thresholds(self, report: CoverageReport):
        """Check coverage against thresholds."""
        # Global thresholds
        coverage_values = {
            CoverageType.LINE: report.line_coverage,
            CoverageType.BRANCH: report.branch_coverage,
            CoverageType.STATEMENT: report.statement_coverage,
            CoverageType.FUNCTION: report.function_coverage,
            CoverageType.CLASS: report.class_coverage,
        }
        
        for cov_type, value in coverage_values.items():
            key = (cov_type, "global")
            if key in self.threshold_map:
                threshold = self.threshold_map[key]
                
                if value < threshold.error_threshold:
                    violation = CoverageViolation(
                        coverage_type=cov_type,
                        severity=Severity.CRITICAL if value < threshold.error_threshold * 0.8 else Severity.HIGH,
                        entity_name="global",
                        file_path="",
                        actual_coverage=value,
                        threshold=threshold.error_threshold,
                        description=f"Global {cov_type.value} coverage ({value:.1f}%) is below error threshold ({threshold.error_threshold:.1f}%)",
                        suggestion=self._get_suggestion(cov_type, value, threshold.error_threshold)
                    )
                    report.violations.append(violation)
                
                elif value < threshold.warning_threshold:
                    violation = CoverageViolation(
                        coverage_type=cov_type,
                        severity=Severity.MEDIUM,
                        entity_name="global",
                        file_path="",
                        actual_coverage=value,
                        threshold=threshold.warning_threshold,
                        description=f"Global {cov_type.value} coverage ({value:.1f}%) is below warning threshold ({threshold.warning_threshold:.1f}%)",
                        suggestion=self._get_suggestion(cov_type, value, threshold.warning_threshold)
                    )
                    report.warnings.append(violation)
        
        # File-level thresholds
        for file_path, fc in report.file_coverages.items():
            if self._is_test_file(file_path):
                continue
            
            if fc.line_coverage < self.config.min_file_coverage:
                violation = CoverageViolation(
                    coverage_type=CoverageType.LINE,
                    severity=Severity.HIGH,
                    entity_name=Path(file_path).name,
                    file_path=file_path,
                    actual_coverage=fc.line_coverage,
                    threshold=self.config.min_file_coverage,
                    description=f"File line coverage ({fc.line_coverage:.1f}%) is below minimum ({self.config.min_file_coverage:.1f}%)",
                    line_ranges=[(1, fc.lines_total)] if fc.uncovered_lines else [],
                    suggestion=f"Add tests for {file_path}"
                )
                report.violations.append(violation)
    
    def _identify_critical_uncovered(self, report: CoverageReport) -> List[Dict[str, Any]]:
        """Identify critical uncovered code sections."""
        critical = []
        
        for file_path, fc in report.file_coverages.items():
            if self._is_test_file(file_path):
                continue
            
            # Files with zero coverage
            if fc.line_coverage == 0 and fc.lines_total > 10:
                critical.append({
                    'type': 'zero_coverage_file',
                    'file': file_path,
                    'lines': fc.lines_total,
                    'severity': 'high'
                })
            
            # Files with large uncovered blocks
            if fc.uncovered_lines:
                blocks = self._find_consecutive_uncovered(fc.uncovered_lines)
                for start, end in blocks:
                    if end - start >= 20:
                        critical.append({
                            'type': 'large_uncovered_block',
                            'file': file_path,
                            'lines': (start, end),
                            'size': end - start + 1,
                            'severity': 'medium'
                        })
            
            # Complex functions with low coverage
            if fc.complexity > 20 and fc.line_coverage < 50:
                critical.append({
                    'type': 'complex_low_coverage',
                    'file': file_path,
                    'complexity': fc.complexity,
                    'coverage': fc.line_coverage,
                    'severity': 'high'
                })
        
        return critical[:20]
    
    def _find_consecutive_uncovered(self, lines: List[int]) -> List[Tuple[int, int]]:
        """Find consecutive ranges of uncovered lines."""
        if not lines:
            return []
        
        lines = sorted(lines)
        ranges = []
        start = lines[0]
        end = lines[0]
        
        for line in lines[1:]:
            if line == end + 1:
                end = line
            else:
                ranges.append((start, end))
                start = line
                end = line
        
        ranges.append((start, end))
        return ranges
    
    def _calculate_overall_score(self, report: CoverageReport) -> Tuple[float, str]:
        """Calculate overall coverage score and grade."""
        # Weighted average of coverage metrics
        weights = {
            CoverageType.LINE: 0.35,
            CoverageType.BRANCH: 0.30,
            CoverageType.STATEMENT: 0.20,
            CoverageType.FUNCTION: 0.10,
            CoverageType.CLASS: 0.05,
        }
        
        score = 0.0
        total_weight = 0.0
        
        coverage_values = {
            CoverageType.LINE: report.line_coverage,
            CoverageType.BRANCH: report.branch_coverage,
            CoverageType.STATEMENT: report.statement_coverage,
            CoverageType.FUNCTION: report.function_coverage,
            CoverageType.CLASS: report.class_coverage,
        }
        
        for cov_type, weight in weights.items():
            if cov_type in coverage_values:
                score += coverage_values[cov_type] * weight
                total_weight += weight
        
        if total_weight > 0:
            score = score / total_weight
        
        # Deduct for violations
        score -= len(report.violations) * 2
        score -= len(report.warnings) * 0.5
        
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
    
    def _get_suggestion(self, cov_type: CoverageType, value: float, threshold: float) -> str:
        """Get suggestion for improving coverage."""
        suggestions = {
            CoverageType.LINE: f"Add tests to cover untested lines (need {(threshold - value):.1f}% more)",
            CoverageType.BRANCH: "Add tests for conditional branches (if/else, try/except)",
            CoverageType.STATEMENT: "Add tests to execute uncovered statements",
            CoverageType.FUNCTION: "Add tests for untested functions and methods",
            CoverageType.CLASS: "Add tests for untested classes",
        }
        return suggestions.get(cov_type, "Add more tests to improve coverage")
    
    def _is_test_file(self, file_path: str) -> bool:
        """Check if file is a test file."""
        path = Path(file_path)
        return ('test' in path.stem.lower() or 
                'tests/' in file_path or 
                path.parent.name == 'tests')
    
    def _generate_summary(self, report: CoverageReport) -> str:
        """Generate validation summary."""
        if report.is_valid:
            return f"✅ Coverage validation passed. Overall: {report.line_coverage:.1f}% (Grade: {report.grade})"
        else:
            return f"❌ Coverage issues found: {len(report.violations)} violations, {len(report.warnings)} warnings"
    
    def _generate_recommendations(self, report: CoverageReport) -> List[str]:
        """Generate recommendations."""
        recommendations = []
        
        if report.line_coverage < 80:
            recommendations.append(f"Increase line coverage from {report.line_coverage:.1f}% to at least 80%")
        
        if report.branch_coverage < 75:
            recommendations.append(f"Add branch coverage tests (currently {report.branch_coverage:.1f}%)")
        
        if report.uncovered_files:
            recommendations.append(f"Add tests for {len(report.uncovered_files)} completely uncovered files")
        
        if report.poorly_covered_files:
            top = report.poorly_covered_files[0]
            recommendations.append(f"Focus on '{top[0]}' (only {top[1]:.1f}% covered)")
        
        if report.critical_uncovered:
            recommendations.append(f"Address {len(report.critical_uncovered)} critical coverage gaps")
        
        return recommendations[:5]
    
    def _save_report(self, report: CoverageReport):
        """Save report to state."""
        reports = self.state.get('reports', [])
        reports.append({
            'timestamp': report.validated_at.isoformat(),
            'project': report.project_name,
            'is_valid': report.is_valid,
            'line_coverage': report.line_coverage,
            'branch_coverage': report.branch_coverage,
            'score': report.overall_score,
            'grade': report.grade,
            'violations': len(report.violations),
            'warnings': len(report.warnings)
        })
        
        if len(reports) > 50:
            reports = reports[-50:]
        
        self.state.set('reports', reports)
        self.state.save()
    
    def export_report(self, report: CoverageReport,
                      output_path: Optional[Path] = None,
                      format: str = 'markdown') -> str:
        """Export coverage report."""
        
        if format == 'json':
            data = {
                'validated_at': report.validated_at.isoformat(),
                'project': report.project_name,
                'is_valid': report.is_valid,
                'score': report.overall_score,
                'grade': report.grade,
                'summary': report.summary,
                'metrics': {
                    'line_coverage': report.line_coverage,
                    'branch_coverage': report.branch_coverage,
                    'statement_coverage': report.statement_coverage,
                    'function_coverage': report.function_coverage,
                    'class_coverage': report.class_coverage,
                    'total_lines': report.total_lines,
                    'covered_lines': report.covered_lines,
                    'total_files': report.total_files
                },
                'violations': [
                    {
                        'type': v.coverage_type.value,
                        'severity': v.severity.value,
                        'entity': v.entity_name,
                        'file': v.file_path,
                        'actual': v.actual_coverage,
                        'threshold': v.threshold
                    }
                    for v in report.violations
                ],
                'uncovered_files': report.uncovered_files,
                'poorly_covered_files': report.poorly_covered_files,
                'recommendations': report.recommendations
            }
            
            content = json.dumps(data, indent=2)
            
        else:  # markdown
            lines = [
                f"# Coverage Validation Report",
                "",
                f"**Project:** {report.project_name}",
                f"**Validated:** {report.validated_at.strftime('%Y-%m-%d %H:%M:%S')}",
                f"**Score:** {report.overall_score:.1f} (Grade: {report.grade})",
                f"**Status:** {report.summary}",
                "",
                "## Coverage Summary",
                "",
                f"| Metric | Coverage | Status |",
                f"|--------|----------|--------|",
                f"| Lines | {report.line_coverage:.1f}% | {self._get_status_emoji(report.line_coverage, 80)} |",
                f"| Branches | {report.branch_coverage:.1f}% | {self._get_status_emoji(report.branch_coverage, 75)} |",
                f"| Statements | {report.statement_coverage:.1f}% | {self._get_status_emoji(report.statement_coverage, 80)} |",
                f"| Functions | {report.function_coverage:.1f}% | {self._get_status_emoji(report.function_coverage, 85)} |",
                f"| Classes | {report.class_coverage:.1f}% | {self._get_status_emoji(report.class_coverage, 90)} |",
                "",
                f"**Total Lines:** {report.total_lines:,}",
                f"**Covered Lines:** {report.covered_lines:,}",
                f"**Total Files:** {report.total_files}",
                "",
            ]
            
            if report.violations:
                lines.extend([
                    "## ❌ Violations",
                    "",
                    "| Type | Severity | Entity | Actual | Threshold |",
                    "|------|----------|--------|--------|-----------|",
                ])
                for v in report.violations[:20]:
                    lines.append(f"| {v.coverage_type.value} | {v.severity.value} | {v.entity_name[:30]} | {v.actual_coverage:.1f}% | {v.threshold:.1f}% |")
                lines.append("")
            
            if report.uncovered_files:
                lines.extend([
                    "## Completely Uncovered Files",
                    "",
                ])
                for f in report.uncovered_files[:10]:
                    lines.append(f"- `{f}`")
                if len(report.uncovered_files) > 10:
                    lines.append(f"- *...and {len(report.uncovered_files) - 10} more*")
                lines.append("")
            
            if report.poorly_covered_files:
                lines.extend([
                    "## Poorly Covered Files (<50%)",
                    "",
                    "| File | Coverage |",
                    "|------|----------|",
                ])
                for f, cov in report.poorly_covered_files[:10]:
                    lines.append(f"| `{Path(f).name}` | {cov:.1f}% |")
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
    
    def _get_status_emoji(self, value: float, threshold: float) -> str:
        """Get status emoji based on coverage value."""
        if value >= threshold:
            return "✅"
        elif value >= threshold * 0.8:
            return "⚠️"
        else:
            return "❌"
    
    def close(self):
        """Clean up resources."""
        self.state.save()
        logger.info("CoverageValidator closed")


# ============================================================
# CLI ENTRY POINT
# ============================================================

def main():
    """CLI entry point for coverage validator."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate test coverage")
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--coverage-file", type=Path, help="Coverage report file")
    parser.add_argument("--format", choices=["json", "markdown"], default="markdown")
    parser.add_argument("--output", "-o", type=Path, help="Output report path")
    parser.add_argument("--min-coverage", type=float, default=80.0, help="Minimum overall coverage")
    parser.add_argument("--min-file-coverage", type=float, default=50.0, help="Minimum file coverage")
    parser.add_argument("--fail-on-warning", action="store_true")
    parser.add_argument("--run-pytest", action="store_true", help="Run pytest to generate coverage")
    
    args = parser.parse_args()
    
    config = CoverageValidatorConfig(
        project_root=args.project_root,
        coverage_file=args.coverage_file,
        min_overall_coverage=args.min_coverage,
        min_file_coverage=args.min_file_coverage,
        fail_on_warning=args.fail_on_warning
    )
    
    if args.run_pytest:
        config.coverage_format = CoverageFormat.Pytest_Cov
    
    validator = CoverageValidator(config)
    
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