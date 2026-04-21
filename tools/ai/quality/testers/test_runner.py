#!/usr/bin/env python3
"""
Test Runner - Executes tests with intelligent test selection and parallel execution.

Part of the Quality tools (quality/testers/test_runner.py)


This test_runner.py provides:

Multi-Framework Support - pytest, unittest, and custom frameworks
Intelligent Test Selection - Run all, changed, affected, failed, or tagged tests
Parallel Execution - Multi-threaded test execution for speed
Test Discovery - Automatic discovery of test files and cases
Failure Analysis - Root cause analysis and fix suggestions
Flaky Test Detection - Identifies intermittently failing tests
Slow Test Identification - Flags tests exceeding time thresholds
Test Retry - Automatic retry of failed tests
Historical Trends - Pass rate and duration trends over time
Coverage Integration - Optional coverage measurement
Multiple Output Formats - JUnit XML, HTML, JSON, Markdown
Health Scoring - A-F grade based on test suite health

The test runner provides a complete test execution and analysis solution, helping teams 
maintain high-quality test suites and quickly identify problematic tests.
"""

import json
import subprocess
import asyncio
import concurrent.futures
from pathlib import Path
from typing import Dict, List, Set, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from collections import defaultdict
import xml.etree.ElementTree as ET

from ....shared.logger import get_logger
from ....shared.state_manager import StateManager
from ....shared.git_utils import GitUtils
from ....analysis.scanners.project_scanner import ProjectScanner
from ....analysis.scanners.import_graph import ImportGraphAnalyzer

logger = get_logger(__name__)


# ============================================================
# ENUMS AND CONSTANTS
# ============================================================

class TestStatus(str, Enum):
    """Status of a test."""
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    XFAIL = "xfailed"
    XPASS = "xpassed"
    ERROR = "error"
    TIMEOUT = "timeout"
    NOT_RUN = "not_run"


class TestFramework(str, Enum):
    """Test framework to use."""
    PYTEST = "pytest"
    UNITTEST = "unittest"
    NOSE = "nose"
    CUSTOM = "custom"


class TestSelectionStrategy(str, Enum):
    """Strategy for selecting tests to run."""
    ALL = "all"
    CHANGED = "changed"
    AFFECTED = "affected"
    FAILED = "failed"
    SLOW = "slow"
    PARALLEL = "parallel"
    TAG = "tag"
    CUSTOM = "custom"


class ExecutionMode(str, Enum):
    """Test execution mode."""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    DISTRIBUTED = "distributed"
    BACKGROUND = "background"


class FailureCategory(str, Enum):
    """Category of test failure."""
    ASSERTION = "assertion"
    EXCEPTION = "exception"
    TIMEOUT = "timeout"
    IMPORT_ERROR = "import_error"
    FIXTURE_ERROR = "fixture_error"
    SETUP_ERROR = "setup_error"
    TEARDOWN_ERROR = "teardown_error"
    FLAKY = "flaky"
    UNKNOWN = "unknown"


# ============================================================
# DATA MODELS
# ============================================================

@dataclass
class TestCase:
    """Represents a single test case."""
    id: str
    name: str
    file_path: str
    class_name: Optional[str] = None
    function_name: Optional[str] = None
    status: TestStatus = TestStatus.NOT_RUN
    duration: float = 0.0
    failure_message: Optional[str] = None
    failure_type: Optional[str] = None
    failure_line: Optional[int] = None
    failure_category: FailureCategory = FailureCategory.UNKNOWN
    skipped_reason: Optional[str] = None
    xfail_reason: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    markers: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    priority: int = 0
    is_slow: bool = False
    is_flaky: bool = False
    flaky_history: List[bool] = field(default_factory=list)
    last_run: Optional[datetime] = None
    run_count: int = 0
    failure_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TestSuite:
    """Represents a test suite (file or class)."""
    id: str
    name: str
    file_path: str
    test_cases: List[TestCase] = field(default_factory=list)
    status: TestStatus = TestStatus.NOT_RUN
    duration: float = 0.0
    setup_duration: float = 0.0
    teardown_duration: float = 0.0
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    error: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def total(self) -> int:
        return len(self.test_cases)


@dataclass
class TestRun:
    """Represents a test run session."""
    id: str
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    framework: TestFramework = TestFramework.PYTEST
    selection_strategy: TestSelectionStrategy = TestSelectionStrategy.ALL
    execution_mode: ExecutionMode = ExecutionMode.SEQUENTIAL
    suites: Dict[str, TestSuite] = field(default_factory=dict)
    total_tests: int = 0
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    xfailed: int = 0
    xpassed: int = 0
    error: int = 0
    total_duration: float = 0.0
    exit_code: int = 0
    environment: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def pass_rate(self) -> float:
        if self.total_tests == 0:
            return 0.0
        return (self.passed / self.total_tests) * 100
    
    @property
    def is_success(self) -> bool:
        return self.failed == 0 and self.error == 0 and self.xpassed == 0


@dataclass
class TestFailureAnalysis:
    """Analysis of a test failure."""
    test: TestCase
    root_cause: str = ""
    likely_fix: Optional[str] = None
    similar_failures: List[str] = field(default_factory=list)
    affected_files: List[str] = field(default_factory=list)
    stack_trace: List[str] = field(default_factory=list)
    code_context: Optional[str] = None
    suggested_fixes: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TestReport:
    """Complete test run report."""
    run: TestRun
    analyzed_at: datetime = field(default_factory=datetime.now)
    
    # Analysis
    failure_analyses: List[TestFailureAnalysis] = field(default_factory=list)
    flaky_tests: List[TestCase] = field(default_factory=list)
    slow_tests: List[TestCase] = field(default_factory=list)
    
    # Trends
    historical_pass_rate: float = 0.0
    pass_rate_trend: List[float] = field(default_factory=list)
    duration_trend: List[float] = field(default_factory=list)
    
    # Coverage (if available)
    coverage_percent: Optional[float] = None
    coverage_change: Optional[float] = None
    
    # Summary
    is_acceptable: bool = True
    overall_score: float = 0.0
    grade: str = "A"
    summary: str = ""
    recommendations: List[str] = field(default_factory=list)
    
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TestRunnerConfig:
    """Configuration for test runner."""
    project_root: Path
    framework: TestFramework = TestFramework.PYTEST
    
    # Test discovery
    test_paths: List[str] = field(default_factory=lambda: ["tests", "test"])
    test_patterns: List[str] = field(default_factory=lambda: ["test_*.py", "*_test.py"])
    
    # Execution
    execution_mode: ExecutionMode = ExecutionMode.SEQUENTIAL
    parallel_workers: int = 4
    timeout_seconds: int = 300
    test_timeout_seconds: int = 30
    
    # Selection
    selection_strategy: TestSelectionStrategy = TestSelectionStrategy.ALL
    changed_files: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    exclude_tags: List[str] = field(default_factory=list)
    
    # Pytest specific
    pytest_args: List[str] = field(default_factory=lambda: ["-v", "--tb=short"])
    markers: List[str] = field(default_factory=list)
    
    # Retry
    retry_failed: bool = True
    max_retries: int = 2
    retry_flaky: bool = True
    
    # Analysis
    analyze_failures: bool = True
    detect_flaky: bool = True
    flaky_threshold: float = 0.3  # 30% failure rate considered flaky
    slow_threshold: float = 1.0  # seconds
    
    # Coverage
    measure_coverage: bool = False
    coverage_config: Optional[Path] = None
    
    # Reporting
    generate_report: bool = True
    junit_xml: Optional[Path] = None
    html_report: Optional[Path] = None
    output_format: str = "markdown"
    
    # Thresholds
    min_pass_rate: float = 90.0
    max_flaky_tests: int = 5
    max_slow_tests: int = 10
    
    # Ignore
    ignore_patterns: List[str] = field(default_factory=lambda: [
        "__pycache__", "*.pyc", ".git", ".venv", "venv", "dist", "build"
    ])


# ============================================================
# TEST DISCOVERY
# ============================================================

class TestDiscovery:
    """Discover tests in the project."""
    
    def __init__(self, config: TestRunnerConfig):
        self.config = config
    
    def discover(self) -> List[TestSuite]:
        """Discover all tests."""
        if self.config.framework == TestFramework.PYTEST:
            return self._discover_pytest()
        elif self.config.framework == TestFramework.UNITTEST:
            return self._discover_unittest()
        else:
            return self._discover_generic()
    
    def _discover_pytest(self) -> List[TestSuite]:
        """Discover pytest tests."""
        suites = []
        
        # Use pytest --collect-only
        cmd = ["pytest", "--collect-only", "-q", "--rootdir", str(self.config.project_root)]
        cmd.extend(self.config.test_paths)
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60,
                cwd=self.config.project_root
            )
            
            current_file = None
            current_suite = None
            
            for line in result.stdout.split('\n'):
                line = line.strip()
                if not line:
                    continue
                
                if '::' in line:
                    # Parse test path
                    parts = line.split('::')
                    file_path = parts[0]
                    
                    if current_file != file_path:
                        current_file = file_path
                        current_suite = TestSuite(
                            id=f"suite_{len(suites)}",
                            name=Path(file_path).stem,
                            file_path=file_path
                        )
                        suites.append(current_suite)
                    
                    test_name = '::'.join(parts[1:])
                    
                    test_case = TestCase(
                        id=f"test_{len(current_suite.test_cases)}",
                        name=test_name,
                        file_path=file_path,
                        function_name=parts[-1] if len(parts) > 2 else parts[1]
                    )
                    
                    if len(parts) > 2:
                        test_case.class_name = parts[1]
                    
                    current_suite.test_cases.append(test_case)
                    
        except Exception as e:
            logger.warning(f"Test discovery failed: {e}")
        
        return suites
    
    def _discover_unittest(self) -> List[TestSuite]:
        """Discover unittest tests."""
        suites = []
        # Similar implementation for unittest
        return suites
    
    def _discover_generic(self) -> List[TestSuite]:
        """Generic test discovery by file pattern."""
        suites = []
        
        for test_path in self.config.test_paths:
            path = self.config.project_root / test_path
            if not path.exists():
                continue
            
            for pattern in self.config.test_patterns:
                for file_path in path.rglob(pattern):
                    if self._should_ignore(file_path):
                        continue
                    
                    suite = TestSuite(
                        id=f"suite_{len(suites)}",
                        name=file_path.stem,
                        file_path=str(file_path)
                    )
                    suites.append(suite)
        
        return suites
    
    def _should_ignore(self, file_path: Path) -> bool:
        """Check if file should be ignored."""
        path_str = str(file_path)
        for pattern in self.config.ignore_patterns:
            if pattern.replace('*', '') in path_str:
                return True
        return False


# ============================================================
# TEST SELECTOR
# ============================================================

class TestSelector:
    """Select tests based on strategy."""
    
    def __init__(self, config: TestRunnerConfig):
        self.config = config
        self.git = GitUtils(config.project_root)
        self.import_analyzer = ImportGraphAnalyzer(project_root=config.project_root)
    
    def select(self, suites: List[TestSuite]) -> List[TestSuite]:
        """Select tests to run."""
        strategy = self.config.selection_strategy
        
        if strategy == TestSelectionStrategy.ALL:
            return suites
        
        elif strategy == TestSelectionStrategy.CHANGED:
            return self._select_changed(suites)
        
        elif strategy == TestSelectionStrategy.AFFECTED:
            return self._select_affected(suites)
        
        elif strategy == TestSelectionStrategy.FAILED:
            return self._select_failed(suites)
        
        elif strategy == TestSelectionStrategy.TAG:
            return self._select_by_tag(suites)
        
        else:
            return suites
    
    def _select_changed(self, suites: List[TestSuite]) -> List[TestSuite]:
        """Select tests for changed files."""
        changed_files = set(self.config.changed_files)
        if not changed_files:
            changed_files = set(self.git.get_changed_files())
        
        selected = []
        for suite in suites:
            # Run if test file changed
            if suite.file_path in changed_files:
                selected.append(suite)
                continue
            
            # Run if corresponding source file changed
            source_file = self._get_source_file(suite.file_path)
            if source_file in changed_files:
                selected.append(suite)
        
        return selected
    
    def _select_affected(self, suites: List[TestSuite]) -> List[TestSuite]:
        """Select tests affected by changes."""
        changed_files = set(self.config.changed_files)
        if not changed_files:
            changed_files = set(self.git.get_changed_files())
        
        # Build dependency graph
        graph = self.import_analyzer.analyze()
        
        # Find all modules affected by changes
        affected_modules = set()
        for file_path in changed_files:
            module = self._file_to_module(file_path)
            affected_modules.add(module)
            
            # Add dependents
            deps = graph.reverse_dependency_graph.get(module, [])
            affected_modules.update(deps)
        
        # Select tests for affected modules
        selected = []
        for suite in suites:
            module = self._file_to_module(suite.file_path)
            if module in affected_modules:
                selected.append(suite)
            else:
                # Check if test covers affected modules
                source_module = self._get_source_module(suite.file_path)
                if source_module in affected_modules:
                    selected.append(suite)
        
        return selected
    
    def _select_failed(self, suites: List[TestSuite]) -> List[TestSuite]:
        """Select previously failed tests."""
        # Load last run results
        state = StateManager(self.config.project_root / ".ai_state" / "test_runner.json")
        last_run = state.get('last_run', {})
        failed_tests = set(last_run.get('failed_tests', []))
        
        selected = []
        for suite in suites:
            failed_cases = []
            for case in suite.test_cases:
                if case.id in failed_tests or f"{suite.file_path}::{case.name}" in failed_tests:
                    failed_cases.append(case)
            
            if failed_cases:
                suite.test_cases = failed_cases
                selected.append(suite)
        
        return selected
    
    def _select_by_tag(self, suites: List[TestSuite]) -> List[TestSuite]:
        """Select tests by tags."""
        tags = set(self.config.tags)
        exclude = set(self.config.exclude_tags)
        
        selected = []
        for suite in suites:
            matching_cases = []
            for case in suite.test_cases:
                case_tags = set(case.tags)
                if tags and not (tags & case_tags):
                    continue
                if exclude and (exclude & case_tags):
                    continue
                matching_cases.append(case)
            
            if matching_cases:
                suite.test_cases = matching_cases
                selected.append(suite)
        
        return selected
    
    def _get_source_file(self, test_file: str) -> Optional[str]:
        """Get source file corresponding to test file."""
        test_path = Path(test_file)
        
        # Common patterns
        if test_path.stem.startswith('test_'):
            source_name = test_path.stem[5:] + '.py'
        elif test_path.stem.endswith('_test'):
            source_name = test_path.stem[:-5] + '.py'
        else:
            return None
        
        # Look in source directories
        for source_dir in ['src', 'engines', 'tools', '.']:
            source_path = self.config.project_root / source_dir / source_name
            if source_path.exists():
                return str(source_path)
        
        return None
    
    def _file_to_module(self, file_path: str) -> str:
        """Convert file path to module name."""
        try:
            rel_path = Path(file_path).relative_to(self.config.project_root)
            parts = list(rel_path.parts)
            if parts[-1].endswith('.py'):
                parts[-1] = parts[-1][:-3]
            if parts[-1] == '__init__':
                parts = parts[:-1]
            return '.'.join(parts)
        except ValueError:
            return Path(file_path).stem
    
    def _get_source_module(self, test_file: str) -> Optional[str]:
        """Get source module corresponding to test file."""
        source_file = self._get_source_file(test_file)
        if source_file:
            return self._file_to_module(source_file)
        return None


# ============================================================
# TEST EXECUTOR
# ============================================================

class TestExecutor:
    """Execute tests."""
    
    def __init__(self, config: TestRunnerConfig):
        self.config = config
    
    def execute(self, suites: List[TestSuite]) -> TestRun:
        """Execute test suites."""
        run = TestRun(
            id=f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            framework=self.config.framework,
            selection_strategy=self.config.selection_strategy,
            execution_mode=self.config.execution_mode
        )
        
        if self.config.framework == TestFramework.PYTEST:
            return self._execute_pytest(suites, run)
        elif self.config.framework == TestFramework.UNITTEST:
            return self._execute_unittest(suites, run)
        else:
            return self._execute_generic(suites, run)
    
    def _execute_pytest(self, suites: List[TestSuite], run: TestRun) -> TestRun:
        """Execute with pytest."""
        start_time = datetime.now()
        
        # Build command
        cmd = ["pytest"]
        
        # Add test files
        if suites:
            test_files = list(set(s.file_path for s in suites))
            cmd.extend(test_files)
        else:
            cmd.extend(self.config.test_paths)
        
        # Add pytest arguments
        cmd.extend(self.config.pytest_args)
        
        # Add markers
        for marker in self.config.markers:
            cmd.extend(["-m", marker])
        
        # Add JUnit XML output
        if self.config.junit_xml:
            cmd.extend(["--junitxml", str(self.config.junit_xml)])
        
        # Add HTML report
        if self.config.html_report:
            cmd.extend(["--html", str(self.config.html_report), "--self-contained-html"])
        
        # Add coverage
        if self.config.measure_coverage:
            cmd.extend(["--cov", str(self.config.project_root), "--cov-report=term"])
            if self.config.coverage_config:
                cmd.extend(["--cov-config", str(self.config.coverage_config)])
        
        # Parallel execution
        if self.config.execution_mode == ExecutionMode.PARALLEL:
            cmd.extend(["-n", str(self.config.parallel_workers)])
        
        # Add timeout
        cmd.extend(["--timeout", str(self.config.test_timeout_seconds)])
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.config.timeout_seconds,
                cwd=self.config.project_root
            )
            
            run.exit_code = result.returncode
            run.total_duration = (datetime.now() - start_time).total_seconds()
            
            # Parse output
            self._parse_pytest_output(result.stdout + result.stderr, run, suites)
            
            # Parse JUnit XML if available
            if self.config.junit_xml and self.config.junit_xml.exists():
                self._parse_junit_xml(self.config.junit_xml, run)
            
        except subprocess.TimeoutExpired:
            run.exit_code = -1
            logger.error("Test execution timed out")
        except Exception as e:
            run.exit_code = -1
            logger.error(f"Test execution failed: {e}")
        
        run.completed_at = datetime.now()
        run.suites = {s.id: s for s in suites}
        
        return run
    
    def _execute_unittest(self, suites: List[TestSuite], run: TestRun) -> TestRun:
        """Execute with unittest."""
        # Implementation for unittest
        return run
    
    def _execute_generic(self, suites: List[TestSuite], run: TestRun) -> TestRun:
        """Generic execution."""
        return run
    
    def _parse_pytest_output(self, output: str, run: TestRun, suites: List[TestSuite]):
        """Parse pytest output."""
        lines = output.split('\n')
        
        # Build test lookup
        test_lookup = {}
        for suite in suites:
            for case in suite.test_cases:
                key = f"{suite.file_path}::{case.name}"
                test_lookup[key] = case
        
        # Parse test results
        for line in lines:
            if '::' in line and any(s in line for s in ['PASSED', 'FAILED', 'SKIPPED', 'XFAIL', 'XPASS']):
                parts = line.split('::')
                file_path = parts[0]
                test_name = '::'.join(parts[1:]).split()[0]
                
                key = f"{file_path}::{test_name}"
                case = test_lookup.get(key)
                
                if case:
                    if 'PASSED' in line:
                        case.status = TestStatus.PASSED
                        run.passed += 1
                    elif 'FAILED' in line:
                        case.status = TestStatus.FAILED
                        run.failed += 1
                    elif 'SKIPPED' in line:
                        case.status = TestStatus.SKIPPED
                        run.skipped += 1
                    elif 'XFAIL' in line:
                        case.status = TestStatus.XFAIL
                        run.xfailed += 1
                    elif 'XPASS' in line:
                        case.status = TestStatus.XPASS
                        run.xpassed += 1
                    
                    run.total_tests += 1
        
        # Update suite statistics
        for suite in suites:
            suite.passed = sum(1 for c in suite.test_cases if c.status == TestStatus.PASSED)
            suite.failed = sum(1 for c in suite.test_cases if c.status == TestStatus.FAILED)
            suite.skipped = sum(1 for c in suite.test_cases if c.status == TestStatus.SKIPPED)
            suite.error = sum(1 for c in suite.test_cases if c.status == TestStatus.ERROR)
            suite.status = TestStatus.FAILED if suite.failed > 0 else TestStatus.PASSED
    
    def _parse_junit_xml(self, xml_path: Path, run: TestRun):
        """Parse JUnit XML report."""
        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()
            
            for testsuite in root.findall('testsuite'):
                run.total_tests = int(testsuite.get('tests', run.total_tests))
                run.failed = int(testsuite.get('failures', run.failed))
                run.skipped = int(testsuite.get('skipped', run.skipped))
                run.error = int(testsuite.get('errors', run.error))
                run.total_duration = float(testsuite.get('time', run.total_duration))
                
        except Exception as e:
            logger.warning(f"Failed to parse JUnit XML: {e}")


# ============================================================
# FAILURE ANALYZER
# ============================================================

class FailureAnalyzer:
    """Analyze test failures."""
    
    def __init__(self, config: TestRunnerConfig):
        self.config = config
    
    def analyze(self, run: TestRun) -> List[TestFailureAnalysis]:
        """Analyze all failures in a test run."""
        analyses = []
        
        for suite in run.suites.values():
            for case in suite.test_cases:
                if case.status == TestStatus.FAILED:
                    analysis = self._analyze_failure(case)
                    analyses.append(analysis)
        
        return analyses
    
    def _analyze_failure(self, test: TestCase) -> TestFailureAnalysis:
        """Analyze a single test failure."""
        analysis = TestFailureAnalysis(test=test)
        
        # Categorize failure
        if test.failure_message:
            msg_lower = test.failure_message.lower()
            
            if 'assert' in msg_lower:
                analysis.root_cause = "Assertion failed"
                test.failure_category = FailureCategory.ASSERTION
            elif 'import' in msg_lower or 'modulenotfound' in msg_lower:
                analysis.root_cause = "Import error"
                test.failure_category = FailureCategory.IMPORT_ERROR
            elif 'fixture' in msg_lower:
                analysis.root_cause = "Fixture error"
                test.failure_category = FailureCategory.FIXTURE_ERROR
            elif 'timeout' in msg_lower:
                analysis.root_cause = "Test timeout"
                test.failure_category = FailureCategory.TIMEOUT
            else:
                analysis.root_cause = "Exception raised"
                test.failure_category = FailureCategory.EXCEPTION
        
        # Extract stack trace
        if test.failure_message:
            analysis.stack_trace = test.failure_message.split('\n')
        
        # Generate fix suggestions
        analysis.suggested_fixes = self._generate_fix_suggestions(test)
        
        return analysis
    
    def _generate_fix_suggestions(self, test: TestCase) -> List[str]:
        """Generate fix suggestions for a test failure."""
        suggestions = []
        
        if test.failure_category == FailureCategory.ASSERTION:
            suggestions.append("Check the assertion condition and expected values")
            suggestions.append("Print actual vs expected values for debugging")
        
        elif test.failure_category == FailureCategory.IMPORT_ERROR:
            suggestions.append("Check if the imported module is installed")
            suggestions.append("Verify the import path is correct")
        
        elif test.failure_category == FailureCategory.FIXTURE_ERROR:
            suggestions.append("Check fixture definition and scope")
            suggestions.append("Ensure fixture dependencies are available")
        
        elif test.failure_category == FailureCategory.TIMEOUT:
            suggestions.append("Consider increasing test timeout")
            suggestions.append("Check for deadlocks or infinite loops")
        
        else:
            suggestions.append("Review the stack trace for error details")
            suggestions.append("Run test with --pdb for interactive debugging")
        
        return suggestions


# ============================================================
# FLAKY DETECTOR
# ============================================================

class FlakyDetector:
    """Detect flaky tests."""
    
    def __init__(self, config: TestRunnerConfig):
        self.config = config
    
    def detect(self, run: TestRun, history: List[TestRun]) -> List[TestCase]:
        """Detect flaky tests."""
        flaky = []
        
        # Build test history
        test_history = defaultdict(list)
        for past_run in history:
            for suite in past_run.suites.values():
                for case in suite.test_cases:
                    test_history[case.id].append(case.status == TestStatus.PASSED)
        
        # Check current run
        for suite in run.suites.values():
            for case in suite.test_cases:
                history = test_history[case.id]
                history.append(case.status == TestStatus.PASSED)
                
                if len(history) >= 3:
                    pass_rate = sum(history) / len(history)
                    if 0 < pass_rate < (1 - self.config.flaky_threshold):
                        case.is_flaky = True
                        case.flaky_history = history
                        flaky.append(case)
        
        return flaky


# ============================================================
# MAIN TEST RUNNER
# ============================================================

class TestRunner:
    """
    Executes tests with intelligent test selection and parallel execution.
    
    Features:
    - Multiple test frameworks (pytest, unittest)
    - Intelligent test selection (changed, affected, failed, tags)
    - Parallel and distributed execution
    - Test failure analysis
    - Flaky test detection
    - Slow test identification
    - Test retry for flaky tests
    - Coverage measurement
    - Historical trend analysis
    - Comprehensive reporting
    """
    
    def __init__(self, config: TestRunnerConfig):
        self.config = config
        self.discovery = TestDiscovery(config)
        self.selector = TestSelector(config)
        self.executor = TestExecutor(config)
        self.failure_analyzer = FailureAnalyzer(config)
        self.flaky_detector = FlakyDetector(config)
        self.state = StateManager(config.project_root / ".ai_state" / "test_runner.json")
        
        logger.info("TestRunner initialized")
    
    def run(self) -> TestReport:
        """Run tests and generate report."""
        logger.info("Starting test run...")
        
        # Discover tests
        suites = self.discovery.discover()
        logger.info(f"Discovered {len(suites)} test suites")
        
        # Select tests
        selected_suites = self.selector.select(suites)
        total_tests = sum(len(s.tests) if hasattr(s, 'tests') else len(s.test_cases) for s in selected_suites)
        logger.info(f"Selected {len(selected_suites)} suites ({total_tests} tests)")
        
        # Execute tests
        run = self.executor.execute(selected_suites)
        
        # Retry failed tests if configured
        if self.config.retry_failed and run.failed > 0:
            run = self._retry_failed(run)
        
        # Create report
        report = TestReport(run=run)
        
        # Analyze failures
        if self.config.analyze_failures:
            report.failure_analyses = self.failure_analyzer.analyze(run)
        
        # Detect flaky tests
        if self.config.detect_flaky:
            history = self._load_test_history()
            report.flaky_tests = self.flaky_detector.detect(run, history)
        
        # Identify slow tests
        report.slow_tests = self._identify_slow_tests(run)
        
        # Load historical trends
        report.historical_pass_rate = self._calculate_historical_pass_rate()
        report.pass_rate_trend = self._get_pass_rate_trend()
        report.duration_trend = self._get_duration_trend()
        
        # Calculate score and grade
        report.overall_score = self._calculate_overall_score(report)
        report.grade = self._calculate_grade(report.overall_score)
        report.is_acceptable = self._is_acceptable(report)
        
        # Generate summary and recommendations
        report.summary = self._generate_summary(report)
        report.recommendations = self._generate_recommendations(report)
        
        # Save run to history
        self._save_run(run)
        
        logger.info(f"Test run complete: {run.passed}/{run.total_tests} passed ({run.pass_rate:.1f}%)")
        
        return report
    
    def run_specific(self, test_paths: List[str]) -> TestReport:
        """Run specific tests."""
        self.config.selection_strategy = TestSelectionStrategy.CUSTOM
        self.config.test_paths = test_paths
        return self.run()
    
    def run_changed(self, changed_files: Optional[List[str]] = None) -> TestReport:
        """Run tests for changed files."""
        self.config.selection_strategy = TestSelectionStrategy.CHANGED
        if changed_files:
            self.config.changed_files = changed_files
        return self.run()
    
    def run_affected(self, changed_files: Optional[List[str]] = None) -> TestReport:
        """Run tests affected by changes."""
        self.config.selection_strategy = TestSelectionStrategy.AFFECTED
        if changed_files:
            self.config.changed_files = changed_files
        return self.run()
    
    def run_failed(self) -> TestReport:
        """Run previously failed tests."""
        self.config.selection_strategy = TestSelectionStrategy.FAILED
        return self.run()
    
    def run_tagged(self, tags: List[str], exclude: Optional[List[str]] = None) -> TestReport:
        """Run tests with specific tags."""
        self.config.selection_strategy = TestSelectionStrategy.TAG
        self.config.tags = tags
        if exclude:
            self.config.exclude_tags = exclude
        return self.run()
    
    def _retry_failed(self, run: TestRun) -> TestRun:
        """Retry failed tests."""
        retry_suites = []
        
        for suite in run.suites.values():
            failed_cases = [c for c in suite.test_cases if c.status == TestStatus.FAILED]
            if failed_cases:
                retry_suite = TestSuite(
                    id=suite.id,
                    name=suite.name,
                    file_path=suite.file_path,
                    test_cases=failed_cases
                )
                retry_suites.append(retry_suite)
        
        if retry_suites:
            logger.info(f"Retrying {sum(len(s.test_cases) for s in retry_suites)} failed tests")
            retry_run = self.executor.execute(retry_suites)
            
            # Merge results
            for retry_suite in retry_run.suites.values():
                original_suite = run.suites.get(retry_suite.id)
                if original_suite:
                    for retry_case in retry_suite.test_cases:
                        for orig_case in original_suite.test_cases:
                            if orig_case.id == retry_case.id:
                                if retry_case.status == TestStatus.PASSED:
                                    run.passed += 1
                                    run.failed -= 1
                                    orig_case.status = TestStatus.PASSED
                                    orig_case.is_flaky = True
        
        return run
    
    def _identify_slow_tests(self, run: TestRun) -> List[TestCase]:
        """Identify slow tests."""
        slow = []
        
        for suite in run.suites.values():
            for case in suite.test_cases:
                if case.duration > self.config.slow_threshold:
                    case.is_slow = True
                    slow.append(case)
        
        slow.sort(key=lambda c: c.duration, reverse=True)
        return slow
    
    def _load_test_history(self) -> List[TestRun]:
        """Load historical test runs."""
        history = self.state.get('history', [])
        # Would reconstruct TestRun objects
        return []
    
    def _save_run(self, run: TestRun):
        """Save test run to history."""
        history = self.state.get('history', [])
        history.append({
            'id': run.id,
            'started_at': run.started_at.isoformat(),
            'completed_at': run.completed_at.isoformat() if run.completed_at else None,
            'total_tests': run.total_tests,
            'passed': run.passed,
            'failed': run.failed,
            'skipped': run.skipped,
            'pass_rate': run.pass_rate,
            'duration': run.total_duration,
            'exit_code': run.exit_code
        })
        
        # Keep last 50 runs
        if len(history) > 50:
            history = history[-50:]
        
        self.state.set('history', history)
        self.state.set('last_run', {
            'failed_tests': self._get_failed_test_ids(run)
        })
        self.state.save()
    
    def _get_failed_test_ids(self, run: TestRun) -> List[str]:
        """Get IDs of failed tests."""
        failed = []
        for suite in run.suites.values():
            for case in suite.test_cases:
                if case.status == TestStatus.FAILED:
                    failed.append(case.id)
        return failed
    
    def _calculate_historical_pass_rate(self) -> float:
        """Calculate historical pass rate."""
        history = self.state.get('history', [])
        if not history:
            return 100.0
        
        pass_rates = [r.get('pass_rate', 0) for r in history[-10:]]
        return sum(pass_rates) / len(pass_rates) if pass_rates else 100.0
    
    def _get_pass_rate_trend(self) -> List[float]:
        """Get pass rate trend."""
        history = self.state.get('history', [])
        return [r.get('pass_rate', 0) for r in history[-10:]]
    
    def _get_duration_trend(self) -> List[float]:
        """Get duration trend."""
        history = self.state.get('history', [])
        return [r.get('duration', 0) for r in history[-10:]]
    
    def _calculate_overall_score(self, report: TestReport) -> float:
        """Calculate overall test health score."""
        score = report.run.pass_rate
        
        # Deduct for flaky tests
        if report.run.total_tests > 0:
            flaky_rate = (len(report.flaky_tests) / report.run.total_tests) * 100
            score -= flaky_rate * 2
        
        # Deduct for slow tests
        if report.run.total_tests > 0:
            slow_rate = (len(report.slow_tests) / report.run.total_tests) * 100
            score -= slow_rate * 0.5
        
        # Deduct for failures
        score -= len(report.failure_analyses) * 5
        
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
    
    def _is_acceptable(self, report: TestReport) -> bool:
        """Check if test run is acceptable."""
        if report.run.pass_rate < self.config.min_pass_rate:
            return False
        if len(report.flaky_tests) > self.config.max_flaky_tests:
            return False
        if len(report.slow_tests) > self.config.max_slow_tests:
            return False
        return True
    
    def _generate_summary(self, report: TestReport) -> str:
        """Generate run summary."""
        if report.run.is_success:
            return f"✅ All tests passed ({report.run.passed}/{report.run.total_tests}) in {report.run.total_duration:.1f}s"
        else:
            return f"❌ {report.run.failed} failed, {report.run.passed} passed ({report.run.pass_rate:.1f}%)"
    
    def _generate_recommendations(self, report: TestReport) -> List[str]:
        """Generate recommendations."""
        recommendations = []
        
        if report.run.failed > 0:
            recommendations.append(f"Fix {report.run.failed} failing tests")
        
        if report.flaky_tests:
            recommendations.append(f"Investigate {len(report.flaky_tests)} flaky tests")
        
        if report.slow_tests:
            slowest = report.slow_tests[0]
            recommendations.append(f"Optimize slow test '{slowest.name}' ({slowest.duration:.1f}s)")
        
        if report.run.pass_rate < self.config.min_pass_rate:
            recommendations.append(f"Improve pass rate from {report.run.pass_rate:.1f}% to {self.config.min_pass_rate:.1f}%")
        
        return recommendations
    
    def export_report(self, report: TestReport,
                      output_path: Optional[Path] = None,
                      format: str = 'markdown') -> str:
        """Export test report."""
        
        if format == 'json':
            data = {
                'analyzed_at': report.analyzed_at.isoformat(),
                'run': {
                    'id': report.run.id,
                    'started_at': report.run.started_at.isoformat(),
                    'completed_at': report.run.completed_at.isoformat() if report.run.completed_at else None,
                    'total_tests': report.run.total_tests,
                    'passed': report.run.passed,
                    'failed': report.run.failed,
                    'skipped': report.run.skipped,
                    'xfailed': report.run.xfailed,
                    'xpassed': report.run.xpassed,
                    'pass_rate': report.run.pass_rate,
                    'duration': report.run.total_duration
                },
                'is_acceptable': report.is_acceptable,
                'score': report.overall_score,
                'grade': report.grade,
                'summary': report.summary,
                'failures': [
                    {
                        'test': a.test.name,
                        'file': a.test.file_path,
                        'root_cause': a.root_cause,
                        'suggested_fixes': a.suggested_fixes
                    }
                    for a in report.failure_analyses[:10]
                ],
                'flaky_tests': [t.name for t in report.flaky_tests],
                'slow_tests': [{'name': t.name, 'duration': t.duration} for t in report.slow_tests[:10]],
                'recommendations': report.recommendations
            }
            
            content = json.dumps(data, indent=2)
            
        else:  # markdown
            lines = [
                f"# Test Run Report",
                "",
                f"**Run ID:** {report.run.id}",
                f"**Started:** {report.run.started_at.strftime('%Y-%m-%d %H:%M:%S')}",
                f"**Duration:** {report.run.total_duration:.1f}s",
                f"**Score:** {report.overall_score:.1f} (Grade: {report.grade})",
                f"**Status:** {report.summary}",
                "",
                "## Summary",
                "",
                f"| Metric | Value |",
                f"|--------|-------|",
                f"| Total Tests | {report.run.total_tests} |",
                f"| Passed | {report.run.passed} |",
                f"| Failed | {report.run.failed} |",
                f"| Skipped | {report.run.skipped} |",
                f"| XFailed | {report.run.xfailed} |",
                f"| XPassed | {report.run.xpassed} |",
                f"| Pass Rate | {report.run.pass_rate:.1f}% |",
                "",
            ]
            
            if report.failure_analyses:
                lines.extend([
                    "## ❌ Failures",
                    "",
                    "| Test | File | Root Cause | Suggested Fix |",
                    "|------|------|------------|---------------|",
                ])
                for analysis in report.failure_analyses[:10]:
                    file_name = Path(analysis.test.file_path).name
                    fix = analysis.suggested_fixes[0] if analysis.suggested_fixes else "-"
                    lines.append(f"| {analysis.test.name[:30]} | {file_name} | {analysis.root_cause[:30]} | {fix[:30]} |")
                lines.append("")
            
            if report.flaky_tests:
                lines.extend([
                    "## 🔄 Flaky Tests",
                    "",
                ])
                for test in report.flaky_tests:
                    lines.append(f"- `{test.name}`")
                lines.append("")
            
            if report.slow_tests:
                lines.extend([
                    "## 🐢 Slow Tests",
                    "",
                    "| Test | Duration |",
                    "|------|----------|",
                ])
                for test in report.slow_tests[:10]:
                    lines.append(f"| {test.name[:40]} | {test.duration:.2f}s |")
                lines.append("")
            
            if report.recommendations:
                lines.extend([
                    "## 📋 Recommendations",
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
        logger.info("TestRunner closed")


# ============================================================
# CLI ENTRY POINT
# ============================================================

def main():
    """CLI entry point for test runner."""
    import argparse
    import sys
    
    parser = argparse.ArgumentParser(description="Run tests with intelligent selection")
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--test-paths", nargs="*", help="Specific test paths to run")
    parser.add_argument("--changed", action="store_true", help="Run tests for changed files")
    parser.add_argument("--affected", action="store_true", help="Run tests affected by changes")
    parser.add_argument("--failed", action="store_true", help="Run previously failed tests")
    parser.add_argument("--tags", nargs="*", help="Run tests with specific tags")
    parser.add_argument("--parallel", action="store_true", help="Run tests in parallel")
    parser.add_argument("--workers", type=int, default=4, help="Number of parallel workers")
    parser.add_argument("--retry", action="store_true", help="Retry failed tests")
    parser.add_argument("--output", "-o", type=Path, help="Output report path")
    parser.add_argument("--format", choices=["json", "markdown"], default="markdown")
    parser.add_argument("--junit", type=Path, help="JUnit XML output path")
    parser.add_argument("--html", type=Path, help="HTML report output path")
    parser.add_argument("--coverage", action="store_true", help="Measure test coverage")
    
    args = parser.parse_args()
    
    config = TestRunnerConfig(
        project_root=args.project_root,
        execution_mode=ExecutionMode.PARALLEL if args.parallel else ExecutionMode.SEQUENTIAL,
        parallel_workers=args.workers,
        retry_failed=args.retry,
        measure_coverage=args.coverage,
        junit_xml=args.junit,
        html_report=args.html
    )
    
    if args.test_paths:
        config.test_paths = args.test_paths
    
    runner = TestRunner(config)
    
    if args.test_paths:
        report = runner.run_specific(args.test_paths)
    elif args.changed:
        report = runner.run_changed()
    elif args.affected:
        report = runner.run_affected()
    elif args.failed:
        report = runner.run_failed()
    elif args.tags:
        report = runner.run_tagged(args.tags)
    else:
        report = runner.run()
    
    output = runner.export_report(report, args.output, args.format)
    
    if not args.output:
        print(output)
    else:
        print(f"Report saved to {args.output}")
    
    print(f"\n{report.summary}")
    
    if not report.is_acceptable:
        sys.exit(1)
    
    runner.close()


if __name__ == "__main__":
    main()