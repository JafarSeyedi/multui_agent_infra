#!/usr/bin/env python3
"""
Coverage Analyzer - Analyzes test coverage and identifies coverage gaps.

Part of the Quality tools (quality/testers/coverage_analyzer.py)

This coverage_analyzer.py provides:

Multi-Format Coverage Parsing - JSON, XML (Cobertura), LCOV formats

Pytest Integration - Run coverage automatically if no report provided

Comprehensive Metrics - Line, branch, statement, function, class coverage

Coverage Level Classification - Excellent, Good, Acceptable, Poor, Critical

Gap Detection - Identifies uncovered functions, classes, branches, blocks

Gap Prioritization - Scores gaps by severity, complexity, and criticality

Critical Path Detection - Identifies critical files with poor coverage

Test Recommendations - Generates specific, actionable test suggestions

Test Templates - Creates pytest templates for uncovered code

Coverage Trends - Tracks coverage changes over time

Module-Level Aggregation - Groups coverage by module/package

Grade Calculation - A-F grade based on weighted coverage metrics

LLM-Powered Suggestions - AI-enhanced recommendations

Comprehensive Reporting - JSON and Markdown formats

The coverage analyzer helps teams identify and prioritize test coverage gaps, making it easier to improve overall code quality and reduce bugs.
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

from ....shared.logger import get_logger
from ....shared.state_manager import StateManager
from ....shared.llm_client import LLMClient
from ....analysis.scanners.project_scanner import ProjectScanner, ProjectGraph
from ....analysis.scanners.ast_analyzer import ASTAnalyzer, ComplexityClass

logger = get_logger(__name__)


# ============================================================
# ENUMS AND CONSTANTS
# ============================================================

class CoverageLevel(str, Enum):
    """Coverage level classification."""
    EXCELLENT = "excellent"    # >= 90%
    GOOD = "good"              # 80-90%
    ACCEPTABLE = "acceptable"  # 70-80%
    POOR = "poor"              # 50-70%
    CRITICAL = "critical"      # < 50%
    NONE = "none"              # 0%


class CoverageType(str, Enum):
    """Type of coverage metric."""
    LINE = "line"
    BRANCH = "branch"
    STATEMENT = "statement"
    FUNCTION = "function"
    CLASS = "class"
    PATH = "path"
    CONDITION = "condition"
    MODIFIED = "modified"  # Only changed lines


class GapSeverity(str, Enum):
    """Severity of coverage gap."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class GapCategory(str, Enum):
    """Category of coverage gap."""
    UNTESTED_FUNCTION = "untested_function"
    UNTESTED_CLASS = "untested_class"
    UNTESTED_BRANCH = "untested_branch"
    UNTESTED_EXCEPTION = "untested_exception"
    UNTESTED_EDGE_CASE = "untested_edge_case"
    UNTESTED_ERROR_PATH = "untested_error_path"
    COMPLEX_CODE = "complex_code"
    CRITICAL_PATH = "critical_path"
    PUBLIC_API = "public_api"
    MODIFIED_CODE = "modified_code"


# ============================================================
# DATA MODELS
# ============================================================

@dataclass
class CoverageMetric:
    """Coverage metric for a file or component."""
    coverage_type: CoverageType
    covered: int
    total: int
    percentage: float
    level: CoverageLevel = CoverageLevel.NONE
    missing_items: List[Any] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FileCoverage:
    """Coverage information for a single file."""
    file_path: str
    relative_path: str
    lines_total: int = 0
    lines_covered: int = 0
    line_coverage: float = 0.0
    line_level: CoverageLevel = CoverageLevel.NONE
    
    branches_total: int = 0
    branches_covered: int = 0
    branch_coverage: float = 0.0
    branch_level: CoverageLevel = CoverageLevel.NONE
    
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
    uncovered_functions: List[str] = field(default_factory=list)
    uncovered_classes: List[str] = field(default_factory=list)
    
    complexity: int = 0
    is_test_file: bool = False
    priority_score: float = 0.0
    
    metrics: List[CoverageMetric] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ModuleCoverage:
    """Coverage information for a module/package."""
    name: str
    path: str
    files: List[str] = field(default_factory=list)
    file_coverages: Dict[str, FileCoverage] = field(default_factory=dict)
    
    total_lines: int = 0
    covered_lines: int = 0
    line_coverage: float = 0.0
    line_level: CoverageLevel = CoverageLevel.NONE
    
    total_branches: int = 0
    covered_branches: int = 0
    branch_coverage: float = 0.0
    
    total_functions: int = 0
    covered_functions: int = 0
    function_coverage: float = 0.0
    
    uncovered_files: List[str] = field(default_factory=list)
    priority_score: float = 0.0
    
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CoverageGap:
    """A specific coverage gap that needs attention."""
    gap_id: str
    category: GapCategory
    severity: GapSeverity
    file_path: str
    line_number: Optional[int] = None
    line_range: Optional[Tuple[int, int]] = None
    symbol_name: Optional[str] = None
    description: str = ""
    impact: str = ""
    suggestion: Optional[str] = None
    estimated_effort: str = "low"  # low, medium, high
    priority_score: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TestRecommendation:
    """Recommendation for improving coverage."""
    recommendation_id: str
    title: str
    description: str
    target_file: str
    target_symbols: List[str] = field(default_factory=list)
    test_template: Optional[str] = None
    priority: int = 1  # 1 (highest) to 5 (lowest)
    estimated_lines: int = 0
    estimated_effort: str = "low"
    impact_score: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CoverageReport:
    """Complete coverage analysis report."""
    analyzed_at: datetime = field(default_factory=datetime.now)
    project_name: str = ""
    
    # Overall metrics
    total_files: int = 0
    total_lines: int = 0
    covered_lines: int = 0
    line_coverage: float = 0.0
    line_level: CoverageLevel = CoverageLevel.NONE
    
    total_branches: int = 0
    covered_branches: int = 0
    branch_coverage: float = 0.0
    
    total_functions: int = 0
    covered_functions: int = 0
    function_coverage: float = 0.0
    
    total_classes: int = 0
    covered_classes: int = 0
    class_coverage: float = 0.0
    
    # Detailed coverage
    file_coverages: Dict[str, FileCoverage] = field(default_factory=dict)
    module_coverages: Dict[str, ModuleCoverage] = field(default_factory=dict)
    
    # Coverage by type
    coverage_by_type: Dict[CoverageType, CoverageMetric] = field(default_factory=dict)
    
    # Gaps and recommendations
    coverage_gaps: List[CoverageGap] = field(default_factory=list)
    critical_gaps: List[CoverageGap] = field(default_factory=list)
    recommendations: List[TestRecommendation] = field(default_factory=list)
    
    # Uncovered items
    uncovered_files: List[str] = field(default_factory=list)
    poorly_covered_files: List[Tuple[str, float]] = field(default_factory=list)
    uncovered_functions: List[Tuple[str, str]] = field(default_factory=list)  # (file, function)
    uncovered_classes: List[Tuple[str, str]] = field(default_factory=list)
    
    # Trends
    coverage_trend: List[Dict[str, Any]] = field(default_factory=list)
    
    # Scores and grades
    overall_score: float = 0.0
    grade: str = "F"
    
    # Summary
    summary: str = ""
    recommendations_summary: List[str] = field(default_factory=list)
    
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CoverageAnalyzerConfig:
    """Configuration for coverage analyzer."""
    project_root: Path
    coverage_file: Optional[Path] = None
    coverage_format: str = "coverage_json"  # coverage_json, coverage_xml, lcov
    
    # Thresholds
    excellent_threshold: float = 90.0
    good_threshold: float = 80.0
    acceptable_threshold: float = 70.0
    poor_threshold: float = 50.0
    
    # Analysis options
    analyze_complexity: bool = True
    analyze_modified_only: bool = False
    identify_gaps: bool = True
    generate_recommendations: bool = True
    prioritize_critical_paths: bool = True
    
    # Gap detection
    min_lines_for_gap: int = 5
    max_gaps_to_report: int = 50
    severity_weights: Dict[GapCategory, float] = field(default_factory=lambda: {
        GapCategory.UNTESTED_FUNCTION: 8.0,
        GapCategory.UNTESTED_CLASS: 7.0,
        GapCategory.UNTESTED_BRANCH: 5.0,
        GapCategory.UNTESTED_EXCEPTION: 6.0,
        GapCategory.UNTESTED_EDGE_CASE: 4.0,
        GapCategory.UNTESTED_ERROR_PATH: 5.0,
        GapCategory.COMPLEX_CODE: 7.0,
        GapCategory.CRITICAL_PATH: 10.0,
        GapCategory.PUBLIC_API: 9.0,
        GapCategory.MODIFIED_CODE: 8.0,
    })
    
    # File patterns
    source_patterns: List[str] = field(default_factory=lambda: ["**/*.py"])
    test_patterns: List[str] = field(default_factory=lambda: ["test_*.py", "*_test.py", "tests/**/*.py"])
    ignore_patterns: List[str] = field(default_factory=lambda: [
        "__pycache__", "*.pyc", ".git", ".venv", "venv", "dist", "build",
        ".pytest_cache", ".mypy_cache", ".ruff_cache", "migrations", "alembic",
        "setup.py", "conftest.py", "__init__.py"
    ])
    
    # Critical path patterns (files/functions that are especially important)
    critical_patterns: List[str] = field(default_factory=lambda: [
        "main.py", "app.py", "api.py", "core.py", "security.py", "auth.py"
    ])
    
    # LLM
    use_llm: bool = True
    llm_model: str = "deepseek-chat"
    
    # Output
    generate_report: bool = True
    output_format: str = "markdown"


# ============================================================
# COVERAGE PARSER
# ============================================================

class CoverageParser:
    """Parse coverage reports from various formats."""
    
    def __init__(self, config: CoverageAnalyzerConfig):
        self.config = config
    
    def parse(self, coverage_file: Optional[Path] = None) -> Dict[str, FileCoverage]:
        """Parse coverage file and return file coverages."""
        cov_file = coverage_file or self.config.coverage_file
        
        if not cov_file or not cov_file.exists():
            logger.warning(f"Coverage file not found: {cov_file}")
            return self._run_coverage()
        
        if cov_file.suffix == '.json':
            return self._parse_coverage_json(cov_file)
        elif cov_file.suffix == '.xml':
            return self._parse_coverage_xml(cov_file)
        elif cov_file.suffix == '.lcov':
            return self._parse_lcov(cov_file)
        else:
            logger.error(f"Unsupported coverage format: {cov_file.suffix}")
            return {}
    
    def _run_coverage(self) -> Dict[str, FileCoverage]:
        """Run pytest with coverage and parse results."""
        try:
            cmd = [
                "pytest",
                f"--cov={self.config.project_root}",
                "--cov-report=json",
                "--cov-report=term",
                "--cov-branch"
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,
                cwd=self.config.project_root
            )
            
            coverage_json = self.config.project_root / "coverage.json"
            if coverage_json.exists():
                return self._parse_coverage_json(coverage_json)
            
        except Exception as e:
            logger.error(f"Failed to run coverage: {e}")
        
        return {}
    
    def _parse_coverage_json(self, file_path: Path) -> Dict[str, FileCoverage]:
        """Parse coverage.json file."""
        file_coverages = {}
        
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            # coverage.py JSON format
            if 'files' in data:
                for file_path_str, file_data in data['files'].items():
                    if not self._should_include_file(file_path_str):
                        continue
                    
                    fc = self._create_file_coverage(file_path_str)
                    
                    summary = file_data.get('summary', {})
                    fc.lines_total = summary.get('num_statements', 0)
                    fc.lines_covered = summary.get('covered_lines', 0)
                    fc.line_coverage = summary.get('percent_covered', 0.0)
                    
                    fc.branches_total = summary.get('num_branches', 0)
                    fc.branches_covered = summary.get('covered_branches', 0)
                    if fc.branches_total > 0:
                        fc.branch_coverage = summary.get('percent_covered', 0.0)
                    else:
                        fc.branch_coverage = 100.0
                    
                    # Missing lines
                    if 'missing_lines' in file_data:
                        fc.uncovered_lines = file_data['missing_lines']
                    
                    # Missing branches
                    if 'missing_branches' in file_data:
                        for branch in file_data['missing_branches']:
                            fc.uncovered_branches.append((branch[0], branch[1]))
                    
                    fc.line_level = self._get_coverage_level(fc.line_coverage)
                    fc.branch_level = self._get_coverage_level(fc.branch_coverage)
                    fc.is_test_file = self._is_test_file(file_path_str)
                    
                    file_coverages[file_path_str] = fc
            
            # Pytest-cov JSON format
            elif 'totals' in data:
                for file_path_str, file_data in data.get('files', {}).items():
                    if not self._should_include_file(file_path_str):
                        continue
                    
                    fc = self._create_file_coverage(file_path_str)
                    
                    summary = file_data.get('summary', {})
                    fc.statements_total = summary.get('num_statements', 0)
                    fc.statements_covered = summary.get('covered_statements', 0)
                    fc.statement_coverage = summary.get('percent_covered', 0.0)
                    
                    fc.lines_missed = file_data.get('excluded_lines', [])
                    
                    fc.line_level = self._get_coverage_level(fc.line_coverage)
                    fc.is_test_file = self._is_test_file(file_path_str)
                    
                    file_coverages[file_path_str] = fc
                    
        except Exception as e:
            logger.error(f"Failed to parse coverage JSON: {e}")
        
        return file_coverages
    
    def _parse_coverage_xml(self, file_path: Path) -> Dict[str, FileCoverage]:
        """Parse coverage.xml (Cobertura format)."""
        file_coverages = {}
        
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            for package in root.findall('.//package'):
                for cls in package.findall('classes/class'):
                    file_path_str = cls.get('filename', '')
                    if not file_path_str or not self._should_include_file(file_path_str):
                        continue
                    
                    fc = self._create_file_coverage(file_path_str)
                    
                    lines_elem = cls.find('lines')
                    if lines_elem is not None:
                        for line in lines_elem.findall('line'):
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
                    
                    fc.line_level = self._get_coverage_level(fc.line_coverage)
                    fc.branch_level = self._get_coverage_level(fc.branch_coverage)
                    fc.is_test_file = self._is_test_file(file_path_str)
                    
                    file_coverages[file_path_str] = fc
                    
        except Exception as e:
            logger.error(f"Failed to parse coverage XML: {e}")
        
        return file_coverages
    
    def _parse_lcov(self, file_path: Path) -> Dict[str, FileCoverage]:
        """Parse LCOV format."""
        file_coverages = {}
        current_file = None
        
        try:
            with open(file_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    
                    if line.startswith('SF:'):
                        current_file = line[3:]
                        if self._should_include_file(current_file):
                            file_coverages[current_file] = self._create_file_coverage(current_file)
                    
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
                        if current_file and current_file in file_coverages:
                            fc = file_coverages[current_file]
                            if fc.lines_total > 0:
                                fc.line_coverage = (fc.lines_covered / fc.lines_total) * 100
                                fc.line_level = self._get_coverage_level(fc.line_coverage)
                            if fc.branches_total > 0:
                                fc.branch_coverage = (fc.branches_covered / fc.branches_total) * 100
                                fc.branch_level = self._get_coverage_level(fc.branch_coverage)
                            fc.is_test_file = self._is_test_file(current_file)
                        current_file = None
                        
        except Exception as e:
            logger.error(f"Failed to parse LCOV file: {e}")
        
        return file_coverages
    
    def _create_file_coverage(self, file_path: str) -> FileCoverage:
        """Create a FileCoverage object."""
        rel_path = str(Path(file_path).relative_to(self.config.project_root)) if self.config.project_root in Path(file_path).parents else file_path
        
        return FileCoverage(
            file_path=file_path,
            relative_path=rel_path
        )
    
    def _get_coverage_level(self, coverage: float) -> CoverageLevel:
        """Get coverage level from percentage."""
        if coverage >= self.config.excellent_threshold:
            return CoverageLevel.EXCELLENT
        elif coverage >= self.config.good_threshold:
            return CoverageLevel.GOOD
        elif coverage >= self.config.acceptable_threshold:
            return CoverageLevel.ACCEPTABLE
        elif coverage >= self.config.poor_threshold:
            return CoverageLevel.POOR
        elif coverage > 0:
            return CoverageLevel.CRITICAL
        else:
            return CoverageLevel.NONE
    
    def _should_include_file(self, file_path: str) -> bool:
        """Check if file should be included."""
        # Check ignore patterns
        for pattern in self.config.ignore_patterns:
            if pattern.replace('*', '') in file_path:
                return False
        
        # Check source patterns
        import fnmatch
        for pattern in self.config.source_patterns:
            if fnmatch.fnmatch(file_path, pattern):
                return True
        
        return False
    
    def _is_test_file(self, file_path: str) -> bool:
        """Check if file is a test file."""
        import fnmatch
        for pattern in self.config.test_patterns:
            if fnmatch.fnmatch(Path(file_path).name, pattern) or fnmatch.fnmatch(file_path, pattern):
                return True
        return False


# ============================================================
# GAP DETECTOR
# ============================================================

class GapDetector:
    """Detect coverage gaps and prioritize them."""
    
    def __init__(self, config: CoverageAnalyzerConfig):
        self.config = config
        self.scanner = ProjectScanner(project_root=config.project_root)
        self.ast_analyzer = ASTAnalyzer()
        self.gap_counter = 0
    
    def detect_gaps(self, file_coverages: Dict[str, FileCoverage],
                    project_graph: Optional[ProjectGraph] = None) -> List[CoverageGap]:
        """Detect coverage gaps."""
        gaps = []
        
        # Scan project if graph not provided
        if project_graph is None:
            project_graph = self.scanner.scan()
        
        for file_path, fc in file_coverages.items():
            if fc.is_test_file:
                continue
            
            # Skip files with good coverage
            if fc.line_coverage >= self.config.good_threshold:
                continue
            
            # Get module info
            module_info = project_graph.modules.get(self._file_to_module(file_path))
            if not module_info:
                continue
            
            # Detect uncovered functions
            for symbol in module_info.symbols:
                if symbol.symbol_type.value == 'function':
                    if self._is_uncovered_function(symbol, fc):
                        gap = self._create_function_gap(file_path, symbol, fc)
                        gaps.append(gap)
                
                elif symbol.symbol_type.value == 'class':
                    if self._is_uncovered_class(symbol, fc):
                        gap = self._create_class_gap(file_path, symbol, fc)
                        gaps.append(gap)
            
            # Detect uncovered branches
            if fc.uncovered_branches:
                for line_num, branch_id in fc.uncovered_branches[:10]:
                    gap = self._create_branch_gap(file_path, line_num, branch_id, fc)
                    gaps.append(gap)
            
            # Detect large uncovered blocks
            blocks = self._find_consecutive_uncovered(fc.uncovered_lines)
            for start, end in blocks:
                if end - start >= self.config.min_lines_for_gap:
                    gap = self._create_block_gap(file_path, start, end, fc)
                    gaps.append(gap)
            
            # Check critical paths
            if self._is_critical_file(file_path):
                if fc.line_coverage < self.config.good_threshold:
                    gap = self._create_critical_gap(file_path, fc)
                    gaps.append(gap)
        
        # Calculate priority scores and sort
        for gap in gaps:
            gap.priority_score = self._calculate_priority_score(gap)
        
        gaps.sort(key=lambda g: g.priority_score, reverse=True)
        
        # Limit number of gaps
        if len(gaps) > self.config.max_gaps_to_report:
            gaps = gaps[:self.config.max_gaps_to_report]
        
        return gaps
    
    def _file_to_module(self, file_path: str) -> str:
        """Convert file path to module name."""
        try:
            rel_path = Path(file_path).relative_to(self.config.project_root)
            parts = list(rel_path.parts)
            if parts[-1] == '__init__.py':
                parts = parts[:-1]
            else:
                parts[-1] = parts[-1].replace('.py', '')
            return '.'.join(parts)
        except ValueError:
            return Path(file_path).stem
    
    def _is_uncovered_function(self, symbol: Any, fc: FileCoverage) -> bool:
        """Check if function is uncovered."""
        # Function is uncovered if its lines have 0 coverage
        if symbol.line_start and symbol.line_end:
            for line in range(symbol.line_start, symbol.line_end + 1):
                if line in fc.uncovered_lines:
                    return True
        
        # Or if function name is in uncovered list
        return symbol.name in fc.uncovered_functions
    
    def _is_uncovered_class(self, symbol: Any, fc: FileCoverage) -> bool:
        """Check if class is uncovered."""
        if symbol.line_start and symbol.line_end:
            for line in range(symbol.line_start, symbol.line_end + 1):
                if line in fc.uncovered_lines:
                    return True
        
        return symbol.name in fc.uncovered_classes
    
    def _create_function_gap(self, file_path: str, symbol: Any, 
                              fc: FileCoverage) -> CoverageGap:
        """Create a function coverage gap."""
        self.gap_counter += 1
        
        # Check if function is public API
        is_public = not symbol.name.startswith('_')
        category = GapCategory.PUBLIC_API if is_public else GapCategory.UNTESTED_FUNCTION
        
        # Check complexity
        complexity = getattr(symbol, 'complexity', 0)
        if complexity > 10:
            category = GapCategory.COMPLEX_CODE
        
        severity = self._determine_severity(category, fc.line_coverage, complexity)
        
        return CoverageGap(
            gap_id=f"gap_{self.gap_counter:04d}",
            category=category,
            severity=severity,
            file_path=file_path,
            line_number=symbol.line_start,
            line_range=(symbol.line_start, symbol.line_end) if symbol.line_end else None,
            symbol_name=symbol.name,
            description=f"Uncovered {'public ' if is_public else ''}function '{symbol.name}' (complexity: {complexity})",
            impact=self._assess_impact(category, symbol),
            suggestion=self._generate_suggestion(category, symbol),
            estimated_effort=self._estimate_effort(symbol),
            metadata={'symbol_type': 'function', 'complexity': complexity}
        )
    
    def _create_class_gap(self, file_path: str, symbol: Any,
                           fc: FileCoverage) -> CoverageGap:
        """Create a class coverage gap."""
        self.gap_counter += 1
        
        is_public = not symbol.name.startswith('_')
        category = GapCategory.PUBLIC_API if is_public else GapCategory.UNTESTED_CLASS
        
        return CoverageGap(
            gap_id=f"gap_{self.gap_counter:04d}",
            category=category,
            severity=Severity.HIGH if is_public else Severity.MEDIUM,
            file_path=file_path,
            line_number=symbol.line_start,
            line_range=(symbol.line_start, symbol.line_end) if symbol.line_end else None,
            symbol_name=symbol.name,
            description=f"Uncovered {'public ' if is_public else ''}class '{symbol.name}'",
            impact=f"Class '{symbol.name}' has no test coverage",
            suggestion=f"Create test class for '{symbol.name}'",
            estimated_effort="medium",
            metadata={'symbol_type': 'class'}
        )
    
    def _create_branch_gap(self, file_path: str, line_num: int, branch_id: int,
                            fc: FileCoverage) -> CoverageGap:
        """Create a branch coverage gap."""
        self.gap_counter += 1
        
        return CoverageGap(
            gap_id=f"gap_{self.gap_counter:04d}",
            category=GapCategory.UNTESTED_BRANCH,
            severity=Severity.MEDIUM,
            file_path=file_path,
            line_number=line_num,
            description=f"Uncovered branch at line {line_num}",
            impact="Conditional logic not fully tested",
            suggestion=f"Add test case to cover the alternate branch at line {line_num}",
            estimated_effort="low",
            metadata={'branch_id': branch_id}
        )
    
    def _create_block_gap(self, file_path: str, start: int, end: int,
                           fc: FileCoverage) -> CoverageGap:
        """Create a block coverage gap."""
        self.gap_counter += 1
        
        size = end - start + 1
        severity = Severity.HIGH if size > 20 else Severity.MEDIUM if size > 10 else Severity.LOW
        
        return CoverageGap(
            gap_id=f"gap_{self.gap_counter:04d}",
            category=GapCategory.UNTESTED_FUNCTION,
            severity=severity,
            file_path=file_path,
            line_range=(start, end),
            description=f"Large uncovered block of {size} lines ({start}-{end})",
            impact=f"{size} lines of code with no test coverage",
            suggestion="Add tests to cover this code block",
            estimated_effort="medium" if size > 20 else "low",
            metadata={'size': size}
        )
    
    def _create_critical_gap(self, file_path: str, fc: FileCoverage) -> CoverageGap:
        """Create a critical file coverage gap."""
        self.gap_counter += 1
        
        return CoverageGap(
            gap_id=f"gap_{self.gap_counter:04d}",
            category=GapCategory.CRITICAL_PATH,
            severity=Severity.CRITICAL,
            file_path=file_path,
            description=f"Critical file '{Path(file_path).name}' has only {fc.line_coverage:.1f}% coverage",
            impact="Critical path code is not adequately tested",
            suggestion=f"Increase test coverage for {Path(file_path).name}",
            estimated_effort="high",
            metadata={'coverage': fc.line_coverage}
        )
    
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
    
    def _is_critical_file(self, file_path: str) -> bool:
        """Check if file is on critical path."""
        import fnmatch
        file_name = Path(file_path).name
        
        for pattern in self.config.critical_patterns:
            if fnmatch.fnmatch(file_name, pattern) or fnmatch.fnmatch(file_path, f"*{pattern}*"):
                return True
        
        return False
    
    def _determine_severity(self, category: GapCategory, coverage: float,
                            complexity: int = 0) -> GapSeverity:
        """Determine gap severity."""
        if category == GapCategory.CRITICAL_PATH:
            return GapSeverity.CRITICAL
        
        if category == GapCategory.PUBLIC_API:
            return GapSeverity.HIGH
        
        if complexity > 15:
            return GapSeverity.HIGH
        elif complexity > 10:
            return GapSeverity.MEDIUM
        
        if coverage < self.config.poor_threshold:
            return GapSeverity.HIGH
        elif coverage < self.config.acceptable_threshold:
            return GapSeverity.MEDIUM
        
        return GapSeverity.LOW
    
    def _assess_impact(self, category: GapCategory, symbol: Any) -> str:
        """Assess the impact of a coverage gap."""
        if category == GapCategory.PUBLIC_API:
            return f"Public API '{symbol.name}' has no test coverage - breaking changes may go undetected"
        elif category == GapCategory.COMPLEX_CODE:
            return f"Complex function '{symbol.name}' has no tests - high risk of bugs"
        else:
            return f"Untested code may contain hidden bugs"
    
    def _generate_suggestion(self, category: GapCategory, symbol: Any) -> str:
        """Generate test suggestion."""
        if category == GapCategory.PUBLIC_API:
            return f"Create unit tests for '{symbol.name}' covering normal cases, edge cases, and error conditions"
        elif category == GapCategory.COMPLEX_CODE:
            return f"Create focused tests for '{symbol.name}' - consider breaking down into smaller functions"
        else:
            return f"Add unit tests for '{symbol.name}'"
    
    def _estimate_effort(self, symbol: Any) -> str:
        """Estimate testing effort."""
        line_count = (symbol.line_end - symbol.line_start + 1) if symbol.line_end else 10
        
        if line_count > 50:
            return "high"
        elif line_count > 20:
            return "medium"
        else:
            return "low"
    
    def _calculate_priority_score(self, gap: CoverageGap) -> float:
        """Calculate priority score for a gap."""
        score = 0.0
        
        # Base weight from category
        score += self.config.severity_weights.get(gap.category, 5.0)
        
        # Severity multiplier
        severity_multipliers = {
            GapSeverity.CRITICAL: 2.0,
            GapSeverity.HIGH: 1.5,
            GapSeverity.MEDIUM: 1.0,
            GapSeverity.LOW: 0.5,
            GapSeverity.INFO: 0.2
        }
        score *= severity_multipliers.get(gap.severity, 1.0)
        
        # Adjust for size
        if gap.line_range:
            size = gap.line_range[1] - gap.line_range[0] + 1
            if size > 30:
                score *= 1.5
            elif size < 5:
                score *= 0.7
        
        # Critical file bonus
        if self._is_critical_file(gap.file_path):
            score *= 1.5
        
        return score


# ============================================================
# RECOMMENDATION GENERATOR
# ============================================================

class RecommendationGenerator:
    """Generate test recommendations."""
    
    def __init__(self, config: CoverageAnalyzerConfig):
        self.config = config
        self.llm = LLMClient() if config.use_llm else None
        self.rec_counter = 0
    
    def generate(self, gaps: List[CoverageGap],
                 file_coverages: Dict[str, FileCoverage]) -> List[TestRecommendation]:
        """Generate test recommendations."""
        recommendations = []
        
        # Group gaps by file
        gaps_by_file = defaultdict(list)
        for gap in gaps:
            gaps_by_file[gap.file_path].append(gap)
        
        for file_path, file_gaps in gaps_by_file.items():
            # Create file-level recommendation
            rec = self._create_file_recommendation(file_path, file_gaps, file_coverages.get(file_path))
            if rec:
                recommendations.append(rec)
        
        # Sort by priority
        recommendations.sort(key=lambda r: (r.priority, -r.impact_score))
        
        return recommendations[:20]
    
    def _create_file_recommendation(self, file_path: str, gaps: List[CoverageGap],
                                     fc: Optional[FileCoverage]) -> Optional[TestRecommendation]:
        """Create a file-level test recommendation."""
        self.rec_counter += 1
        
        # Determine priority based on worst gap
        worst_gap = max(gaps, key=lambda g: g.priority_score)
        
        # Collect uncovered symbols
        symbols = [g.symbol_name for g in gaps if g.symbol_name]
        
        # Estimate lines to cover
        uncovered_lines = fc.uncovered_lines if fc else []
        estimated_lines = len(uncovered_lines)
        
        # Determine effort
        if estimated_lines > 100:
            effort = "high"
        elif estimated_lines > 30:
            effort = "medium"
        else:
            effort = "low"
        
        # Generate test template
        test_template = self._generate_test_template(file_path, symbols, fc)
        
        # Calculate impact score
        impact_score = sum(g.priority_score for g in gaps) / len(gaps) if gaps else 0
        
        return TestRecommendation(
            recommendation_id=f"rec_{self.rec_counter:04d}",
            title=f"Add tests for {Path(file_path).name}",
            description=f"Increase test coverage for {Path(file_path).name} from {fc.line_coverage:.1f}% to at least {self.config.good_threshold:.0f}%",
            target_file=file_path,
            target_symbols=symbols,
            test_template=test_template,
            priority=1 if worst_gap.severity == GapSeverity.CRITICAL else 2 if worst_gap.severity == GapSeverity.HIGH else 3,
            estimated_lines=estimated_lines,
            estimated_effort=effort,
            impact_score=impact_score,
            metadata={'gaps_count': len(gaps), 'current_coverage': fc.line_coverage if fc else 0}
        )
    
    def _generate_test_template(self, file_path: str, symbols: List[str],
                                 fc: Optional[FileCoverage]) -> Optional[str]:
        """Generate a test template."""
        module_name = Path(file_path).stem
        
        lines = [
            f'"""',
            f'Unit tests for {module_name}.',
            f'"""',
            '',
            'import pytest',
            f'from {module_name} import *',
            '',
            ''
        ]
        
        for symbol in symbols[:5]:
            lines.append(f'class Test{symbol}:')
            lines.append(f'    """Tests for {symbol}."""')
            lines.append('')
            lines.append(f'    def test_{symbol.lower()}_basic(self):')
            lines.append(f'        """Test basic functionality."""')
            lines.append(f'        # TODO: Implement test')
            lines.append(f'        pass')
            lines.append('')
        
        if fc and fc.uncovered_lines:
            lines.append('# Uncovered lines to test:')
            for line in fc.uncovered_lines[:10]:
                lines.append(f'#   Line {line}')
        
        return '\n'.join(lines)


# ============================================================
# MAIN COVERAGE ANALYZER
# ============================================================

class CoverageAnalyzer:
    """
    Analyzes test coverage and identifies coverage gaps.
    
    Features:
    - Parse coverage reports (JSON, XML, LCOV)
    - Run pytest with coverage
    - Identify coverage gaps
    - Prioritize gaps by severity and impact
    - Generate test recommendations
    - Track coverage trends
    - LLM-powered suggestions
    - Comprehensive reporting
    """
    
    def __init__(self, config: CoverageAnalyzerConfig):
        self.config = config
        self.parser = CoverageParser(config)
        self.gap_detector = GapDetector(config)
        self.recommendation_generator = RecommendationGenerator(config)
        self.scanner = ProjectScanner(project_root=config.project_root)
        self.ast_analyzer = ASTAnalyzer()
        self.state = StateManager(config.project_root / ".ai_state" / "coverage_analyzer.json")
        
        logger.info("CoverageAnalyzer initialized")
    
    def analyze(self) -> CoverageReport:
        """Run complete coverage analysis."""
        logger.info("Starting coverage analysis...")
        
        report = CoverageReport(
            project_name=self.config.project_root.name
        )
        
        # Parse coverage data
        file_coverages = self.parser.parse()
        report.file_coverages = file_coverages
        
        if not file_coverages:
            logger.warning("No coverage data found")
            report.summary = "No coverage data available"
            return report
        
        # Calculate overall metrics
        self._calculate_overall_metrics(report)
        
        # Build module coverages
        report.module_coverages = self._build_module_coverages(file_coverages)
        
        # Create coverage metrics by type
        report.coverage_by_type = self._create_coverage_metrics(report)
        
        # Scan project for AST analysis
        project_graph = self.scanner.scan()
        
        # Identify uncovered items
        self._identify_uncovered_items(report)
        
        # Detect coverage gaps
        if self.config.identify_gaps:
            report.coverage_gaps = self.gap_detector.detect_gaps(file_coverages, project_graph)
            report.critical_gaps = [g for g in report.coverage_gaps if g.severity == GapSeverity.CRITICAL]
        
        # Generate recommendations
        if self.config.generate_recommendations:
            report.recommendations = self.recommendation_generator.generate(
                report.coverage_gaps, file_coverages
            )
        
        # Load coverage trend
        report.coverage_trend = self._load_coverage_trend(report)
        
        # Calculate overall score and grade
        report.overall_score, report.grade = self._calculate_overall_score(report)
        
        # Generate summary
        report.summary = self._generate_summary(report)
        report.recommendations_summary = self._generate_recommendations_summary(report)
        
        # Save report
        self._save_report(report)
        
        logger.info(f"Coverage analysis complete: {report.line_coverage:.1f}% line coverage")
        
        return report
    
    def _calculate_overall_metrics(self, report: CoverageReport):
        """Calculate overall coverage metrics."""
        for fc in report.file_coverages.values():
            if fc.is_test_file:
                continue
            
            report.total_files += 1
            
            report.total_lines += fc.lines_total
            report.covered_lines += fc.lines_covered
            
            report.total_branches += fc.branches_total
            report.covered_branches += fc.branches_covered
            
            report.total_functions += fc.functions_total
            report.covered_functions += fc.functions_covered
            
            report.total_classes += fc.classes_total
            report.covered_classes += fc.classes_covered
        
        if report.total_lines > 0:
            report.line_coverage = (report.covered_lines / report.total_lines) * 100
            report.line_level = self._get_coverage_level(report.line_coverage)
        
        if report.total_branches > 0:
            report.branch_coverage = (report.covered_branches / report.total_branches) * 100
        
        if report.total_functions > 0:
            report.function_coverage = (report.covered_functions / report.total_functions) * 100
        
        if report.total_classes > 0:
            report.class_coverage = (report.covered_classes / report.total_classes) * 100
    
    def _get_coverage_level(self, coverage: float) -> CoverageLevel:
        """Get coverage level from percentage."""
        if coverage >= self.config.excellent_threshold:
            return CoverageLevel.EXCELLENT
        elif coverage >= self.config.good_threshold:
            return CoverageLevel.GOOD
        elif coverage >= self.config.acceptable_threshold:
            return CoverageLevel.ACCEPTABLE
        elif coverage >= self.config.poor_threshold:
            return CoverageLevel.POOR
        elif coverage > 0:
            return CoverageLevel.CRITICAL
        else:
            return CoverageLevel.NONE
    
    def _build_module_coverages(self, file_coverages: Dict[str, FileCoverage]) -> Dict[str, ModuleCoverage]:
        """Build module-level coverage aggregations."""
        modules = {}
        
        for file_path, fc in file_coverages.items():
            if fc.is_test_file:
                continue
            
            # Extract module name from file path
            parts = Path(file_path).parts
            if len(parts) > 1:
                module_name = parts[0]
            else:
                module_name = "root"
            
            if module_name not in modules:
                modules[module_name] = ModuleCoverage(
                    name=module_name,
                    path=module_name
                )
            
            module = modules[module_name]
            module.files.append(file_path)
            module.file_coverages[file_path] = fc
            module.total_lines += fc.lines_total
            module.covered_lines += fc.lines_covered
            module.total_branches += fc.branches_total
            module.covered_branches += fc.branches_covered
            module.total_functions += fc.functions_total
            module.covered_functions += fc.functions_covered
            
            if fc.line_coverage == 0:
                module.uncovered_files.append(file_path)
        
        # Calculate module coverage
        for module in modules.values():
            if module.total_lines > 0:
                module.line_coverage = (module.covered_lines / module.total_lines) * 100
                module.line_level = self._get_coverage_level(module.line_coverage)
            if module.total_branches > 0:
                module.branch_coverage = (module.covered_branches / module.total_branches) * 100
            if module.total_functions > 0:
                module.function_coverage = (module.covered_functions / module.total_functions) * 100
        
        return modules
    
    def _create_coverage_metrics(self, report: CoverageReport) -> Dict[CoverageType, CoverageMetric]:
        """Create coverage metrics by type."""
        metrics = {}
        
        metrics[CoverageType.LINE] = CoverageMetric(
            coverage_type=CoverageType.LINE,
            covered=report.covered_lines,
            total=report.total_lines,
            percentage=report.line_coverage,
            level=report.line_level
        )
        
        metrics[CoverageType.BRANCH] = CoverageMetric(
            coverage_type=CoverageType.BRANCH,
            covered=report.covered_branches,
            total=report.total_branches,
            percentage=report.branch_coverage
        )
        
        metrics[CoverageType.FUNCTION] = CoverageMetric(
            coverage_type=CoverageType.FUNCTION,
            covered=report.covered_functions,
            total=report.total_functions,
            percentage=report.function_coverage
        )
        
        metrics[CoverageType.CLASS] = CoverageMetric(
            coverage_type=CoverageType.CLASS,
            covered=report.covered_classes,
            total=report.total_classes,
            percentage=report.class_coverage
        )
        
        return metrics
    
    def _identify_uncovered_items(self, report: CoverageReport):
        """Identify uncovered files, functions, and classes."""
        for file_path, fc in report.file_coverages.items():
            if fc.is_test_file:
                continue
            
            if fc.line_coverage == 0:
                report.uncovered_files.append(file_path)
            elif fc.line_coverage < self.config.poor_threshold:
                report.poorly_covered_files.append((file_path, fc.line_coverage))
            
            for func in fc.uncovered_functions:
                report.uncovered_functions.append((file_path, func))
            
            for cls in fc.uncovered_classes:
                report.uncovered_classes.append((file_path, cls))
        
        report.poorly_covered_files.sort(key=lambda x: x[1])
    
    def _load_coverage_trend(self, report: CoverageReport) -> List[Dict[str, Any]]:
        """Load historical coverage trend."""
        trend = self.state.get('coverage_trend', [])
        
        # Add current coverage
        trend.append({
            'timestamp': datetime.now().isoformat(),
            'line_coverage': report.line_coverage,
            'branch_coverage': report.branch_coverage,
            'function_coverage': report.function_coverage,
            'total_lines': report.total_lines
        })
        
        # Keep last 30 entries
        if len(trend) > 30:
            trend = trend[-30:]
        
        self.state.set('coverage_trend', trend)
        self.state.save()
        
        return trend
    
    def _calculate_overall_score(self, report: CoverageReport) -> Tuple[float, str]:
        """Calculate overall coverage score and grade."""
        # Weighted average of coverage metrics
        weights = {
            CoverageType.LINE: 0.35,
            CoverageType.BRANCH: 0.30,
            CoverageType.FUNCTION: 0.20,
            CoverageType.CLASS: 0.15
        }
        
        score = 0.0
        total_weight = 0.0
        
        for cov_type, weight in weights.items():
            metric = report.coverage_by_type.get(cov_type)
            if metric:
                score += metric.percentage * weight
                total_weight += weight
        
        if total_weight > 0:
            score = score / total_weight
        
        # Deduct for critical gaps
        score -= len(report.critical_gaps) * 2
        score -= len([g for g in report.coverage_gaps if g.severity == GapSeverity.HIGH]) * 0.5
        
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
    
    def _generate_summary(self, report: CoverageReport) -> str:
        """Generate analysis summary."""
        if report.line_coverage >= self.config.good_threshold:
            return f"✅ Good coverage: {report.line_coverage:.1f}% lines covered (Grade: {report.grade})"
        elif report.line_coverage >= self.config.acceptable_threshold:
            return f"⚠️ Acceptable coverage: {report.line_coverage:.1f}% lines covered (Grade: {report.grade})"
        else:
            return f"❌ Poor coverage: {report.line_coverage:.1f}% lines covered - {len(report.coverage_gaps)} gaps identified"
    
    def _generate_recommendations_summary(self, report: CoverageReport) -> List[str]:
        """Generate recommendations summary."""
        summary = []
        
        if report.critical_gaps:
            summary.append(f"Address {len(report.critical_gaps)} critical coverage gaps")
        
        if report.uncovered_files:
            summary.append(f"Add tests for {len(report.uncovered_files)} completely uncovered files")
        
        if report.branch_coverage < 70:
            summary.append(f"Improve branch coverage from {report.branch_coverage:.1f}% to at least 70%")
        
        if report.recommendations:
            summary.append(f"Follow {len(report.recommendations)} specific test recommendations")
        
        return summary[:5]
    
    def _save_report(self, report: CoverageReport):
        """Save report to state."""
        reports = self.state.get('reports', [])
        reports.append({
            'timestamp': report.analyzed_at.isoformat(),
            'project': report.project_name,
            'line_coverage': report.line_coverage,
            'branch_coverage': report.branch_coverage,
            'score': report.overall_score,
            'grade': report.grade,
            'gaps': len(report.coverage_gaps),
            'critical_gaps': len(report.critical_gaps),
            'recommendations': len(report.recommendations)
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
                'analyzed_at': report.analyzed_at.isoformat(),
                'project': report.project_name,
                'summary': report.summary,
                'score': report.overall_score,
                'grade': report.grade,
                'metrics': {
                    'line': {'covered': report.covered_lines, 'total': report.total_lines, 'percentage': report.line_coverage},
                    'branch': {'covered': report.covered_branches, 'total': report.total_branches, 'percentage': report.branch_coverage},
                    'function': {'covered': report.covered_functions, 'total': report.total_functions, 'percentage': report.function_coverage},
                    'class': {'covered': report.covered_classes, 'total': report.total_classes, 'percentage': report.class_coverage}
                },
                'gaps': [
                    {
                        'id': g.gap_id,
                        'category': g.category.value,
                        'severity': g.severity.value,
                        'file': g.file_path,
                        'line': g.line_number,
                        'symbol': g.symbol_name,
                        'description': g.description,
                        'priority_score': g.priority_score
                    }
                    for g in report.coverage_gaps[:50]
                ],
                'recommendations': [
                    {
                        'id': r.recommendation_id,
                        'title': r.title,
                        'target_file': r.target_file,
                        'priority': r.priority,
                        'estimated_effort': r.estimated_effort
                    }
                    for r in report.recommendations
                ],
                'uncovered_files': report.uncovered_files,
                'poorly_covered_files': report.poorly_covered_files,
                'recommendations_summary': report.recommendations_summary
            }
            
            content = json.dumps(data, indent=2)
            
        else:  # markdown
            lines = [
                f"# Coverage Analysis Report",
                "",
                f"**Project:** {report.project_name}",
                f"**Analyzed:** {report.analyzed_at.strftime('%Y-%m-%d %H:%M:%S')}",
                f"**Score:** {report.overall_score:.1f} (Grade: {report.grade})",
                f"**Status:** {report.summary}",
                "",
                "## Coverage Summary",
                "",
                f"| Metric | Covered | Total | Percentage | Level |",
                f"|--------|---------|-------|------------|-------|",
                f"| Lines | {report.covered_lines:,} | {report.total_lines:,} | {report.line_coverage:.1f}% | {report.line_level.value} |",
                f"| Branches | {report.covered_branches:,} | {report.total_branches:,} | {report.branch_coverage:.1f}% | - |",
                f"| Functions | {report.covered_functions} | {report.total_functions} | {report.function_coverage:.1f}% | - |",
                f"| Classes | {report.covered_classes} | {report.total_classes} | {report.class_coverage:.1f}% | - |",
                "",
                f"**Total Files:** {report.total_files}",
                "",
            ]
            
            if report.coverage_gaps:
                lines.extend([
                    "## 🔴 Critical Coverage Gaps",
                    "",
                    "| Priority | Category | File | Symbol | Description | Effort |",
                    "|----------|----------|------|--------|-------------|--------|",
                ])
                
                critical_gaps = [g for g in report.coverage_gaps if g.severity in (GapSeverity.CRITICAL, GapSeverity.HIGH)][:15]
                for gap in critical_gaps:
                    priority = "🔴" if gap.severity == GapSeverity.CRITICAL else "🟠"
                    file_name = Path(gap.file_path).name
                    lines.append(f"| {priority} | {gap.category.value} | {file_name} | {gap.symbol_name or '-'} | {gap.description[:40]} | {gap.estimated_effort} |")
                lines.append("")
            
            if report.recommendations:
                lines.extend([
                    "## 📋 Test Recommendations",
                    "",
                ])
                for i, rec in enumerate(report.recommendations[:10], 1):
                    priority_emoji = {1: "🔴", 2: "🟠", 3: "🟡"}.get(rec.priority, "🔵")
                    lines.append(f"### {i}. {priority_emoji} {rec.title}")
                    lines.append(f"**Target:** `{rec.target_file}`")
                    lines.append(f"**Effort:** {rec.estimated_effort} | **Lines to cover:** ~{rec.estimated_lines}")
                    lines.append(f"**Description:** {rec.description}")
                    if rec.test_template:
                        lines.append("")
                        lines.append("**Test Template:**")
                        lines.append("```python")
                        lines.append(rec.test_template)
                        lines.append("```")
                    lines.append("")
            
            if report.uncovered_files:
                lines.extend([
                    "## 📄 Completely Uncovered Files",
                    "",
                ])
                for f in report.uncovered_files[:15]:
                    lines.append(f"- `{f}`")
                if len(report.uncovered_files) > 15:
                    lines.append(f"- *...and {len(report.uncovered_files) - 15} more*")
                lines.append("")
            
            if report.recommendations_summary:
                lines.extend([
                    "## 🎯 Recommendations Summary",
                    "",
                ])
                for rec in report.recommendations_summary:
                    lines.append(f"- {rec}")
                lines.append("")
            
            content = '\n'.join(lines)
        
        if output_path:
            output_path.write_text(content)
        
        return content
    
    def close(self):
        """Clean up resources."""
        self.state.save()
        logger.info("CoverageAnalyzer closed")


# ============================================================
# CLI ENTRY POINT
# ============================================================

def main():
    """CLI entry point for coverage analyzer."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Analyze test coverage and identify gaps")
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--coverage-file", type=Path, help="Coverage report file")
    parser.add_argument("--output", "-o", type=Path, help="Output report path")
    parser.add_argument("--format", choices=["json", "markdown"], default="markdown")
    parser.add_argument("--run-coverage", action="store_true", help="Run pytest with coverage")
    parser.add_argument("--threshold", type=float, default=80.0, help="Coverage threshold for good coverage")
    parser.add_argument("--no-gaps", action="store_true", help="Skip gap detection")
    parser.add_argument("--no-recommendations", action="store_true", help="Skip recommendations")
    parser.add_argument("--no-llm", action="store_true", help="Disable LLM assistance")
    
    args = parser.parse_args()
    
    config = CoverageAnalyzerConfig(
        project_root=args.project_root,
        coverage_file=args.coverage_file,
        good_threshold=args.threshold,
        identify_gaps=not args.no_gaps,
        generate_recommendations=not args.no_recommendations,
        use_llm=not args.no_llm
    )
    
    analyzer = CoverageAnalyzer(config)
    
    report = analyzer.analyze()
    
    output = analyzer.export_report(report, args.output, args.format)
    
    if not args.output:
        print(output)
    else:
        print(f"Report saved to {args.output}")
    
    print(f"\n{report.summary}")
    print(f"Gaps: {len(report.coverage_gaps)} total, {len(report.critical_gaps)} critical")
    print(f"Recommendations: {len(report.recommendations)}")
    
    analyzer.close()


if __name__ == "__main__":
    main()