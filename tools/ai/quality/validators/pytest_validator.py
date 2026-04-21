#!/usr/bin/env python3
"""
Pytest Validator - Validates pytest test execution and results.

Part of the Quality tools (validators/pytest_validator.py)

This pytest_validator.py provides:

1. Test Execution - Runs pytest with configurable options
2. Multiple Output Formats - Parses JUnit XML, JSON, and text output
3. Comprehensive Statistics - Tracks passed, failed, skipped, xfailed, xpassed tests
4. Slow Test Detection - Identifies tests exceeding time thresholds
5. Flaky Test Detection - Finds intermittently failing tests
6. Coverage Integration - Checks test coverage with pytest-cov
7. Parallel Execution - Supports pytest-xdist for faster runs
8. Test Health Scoring - A-F grade based on test metrics
9. Failed Test Analysis - Captures failure messages and suggestions
10. JUnit XML Parsing - Can analyze existing test results
11. Historical Tracking - Tracks test trends over time
12. Comprehensive Reporting - JSON and Markdown formats

The pytest validator ensures your test suite is healthy, fast, and reliable.
"""

import json
import subprocess
import tempfile
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

class TestStatus(str, Enum):
    """Status of a test."""
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    XFAIL = "xfailed"
    XPASS = "xpassed"
    ERROR = "error"
    TIMEOUT = "timeout"
    UNKNOWN = "unknown"


class TestOutcome(str, Enum):
    """Outcome of test run."""
    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"
    ERROR = "error"


class Severity(str, Enum):
    """Severity of test issue."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


# ============================================================
# DATA MODELS
# ============================================================

@dataclass
class TestCase:
    """Represents a single test case."""
    name: str
    file_path: str
    class_name: Optional[str] = None
    status: TestStatus = TestStatus.UNKNOWN
    duration: float = 0.0
    failure_message: Optional[str] = None
    failure_type: Optional[str] = None
    failure_line: Optional[int] = None
    skipped_reason: Optional[str] = None
    xfail_reason: Optional[str] = None
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TestFile:
    """Represents a test file."""
    file_path: str
    tests: List[TestCase] = field(default_factory=list)
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    xfailed: int = 0
    xpassed: int = 0
    errors: int = 0
    duration: float = 0.0
    status: TestOutcome = TestOutcome.SUCCESS


@dataclass
class TestSuite:
    """Represents a test suite (collection of test files)."""
    name: str
    files: List[TestFile] = field(default_factory=list)
    total_tests: int = 0
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    xfailed: int = 0
    xpassed: int = 0
    errors: int = 0
    duration: float = 0.0
    status: TestOutcome = TestOutcome.SUCCESS


@dataclass
class TestIssue:
    """A single test issue."""
    issue_type: str
    severity: Severity
    test_name: str
    file_path: str
    description: str
    suggestion: Optional[str] = None
    failure_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PytestReport:
    """Complete pytest validation report."""
    validated_at: datetime = field(default_factory=datetime.now)
    project_name: str = ""
    pytest_version: str = ""
    python_version: str = ""
    
    # Statistics
    total_tests: int = 0
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    xfailed: int = 0
    xpassed: int = 0
    errors: int = 0
    total_duration: float = 0.0
    pass_rate: float = 0.0
    
    # Test details
    test_files: Dict[str, TestFile] = field(default_factory=dict)
    test_suites: Dict[str, TestSuite] = field(default_factory=dict)
    failed_tests: List[TestCase] = field(default_factory=list)
    skipped_tests: List[TestCase] = field(default_factory=list)
    slow_tests: List[TestCase] = field(default_factory=list)
    flaky_tests: List[TestCase] = field(default_factory=list)
    
    # Issues
    issues: List[TestIssue] = field(default_factory=list)
    warnings: List[TestIssue] = field(default_factory=list)
    
    # Coverage (if available)
    coverage_percent: Optional[float] = None
    coverage_missing: List[str] = field(default_factory=list)
    
    # Validation
    is_valid: bool = True
    overall_score: float = 0.0
    grade: str = "A"
    summary: str = ""
    recommendations: List[str] = field(default_factory=list)
    
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PytestValidatorConfig:
    """Configuration for pytest validator."""
    project_root: Path
    pytest_args: List[str] = field(default_factory=lambda: ["-v", "--tb=short"])
    
    # Test discovery
    test_paths: List[str] = field(default_factory=lambda: ["tests", "test"])
    test_patterns: List[str] = field(default_factory=lambda: ["test_*.py", "*_test.py"])
    
    # Performance thresholds
    slow_test_threshold: float = 1.0  # seconds
    very_slow_test_threshold: float = 5.0  # seconds
    
    # Quality thresholds
    min_pass_rate: float = 90.0
    max_failed_tests: int = 10
    max_skipped_tests: int = 20
    
    # Flaky test detection
    detect_flaky_tests: bool = False
    flaky_test_runs: int = 3
    flaky_threshold: float = 0.8  # 80% pass rate considered flaky
    
    # Coverage
    check_coverage: bool = False
    min_coverage: float = 80.0
    coverage_config: Optional[Path] = None
    
    # Reporting
    generate_report: bool = True
    output_format: str = "markdown"
    junit_xml: Optional[Path] = None
    include_slow_tests: int = 10
    include_failure_details: bool = True
    
    # Validation
    fail_on_failure: bool = True
    fail_on_error: bool = True
    fail_on_skip: bool = False
    fail_on_xpass: bool = True
    
    # Parallel execution
    parallel: bool = False
    num_workers: int = 4
    
    # Timeout
    timeout: int = 300  # seconds


# ============================================================
# PYTEST OUTPUT PARSER
# ============================================================

class PytestOutputParser:
    """Parse pytest output into structured data."""
    
    def parse_junit_xml(self, xml_path: Path) -> List[TestSuite]:
        """Parse JUnit XML report."""
        suites = []
        
        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()
            
            for testsuite in root.findall('testsuite'):
                suite = TestSuite(
                    name=testsuite.get('name', 'unknown'),
                    total_tests=int(testsuite.get('tests', 0)),
                    passed=int(testsuite.get('tests', 0)) - int(testsuite.get('failures', 0)) - int(testsuite.get('errors', 0)) - int(testsuite.get('skipped', 0)),
                    failed=int(testsuite.get('failures', 0)),
                    errors=int(testsuite.get('errors', 0)),
                    skipped=int(testsuite.get('skipped', 0)),
                    duration=float(testsuite.get('time', 0))
                )
                
                for testcase in testsuite.findall('testcase'):
                    test = TestCase(
                        name=testcase.get('name', 'unknown'),
                        file_path=testcase.get('file', ''),
                        class_name=testcase.get('classname'),
                        duration=float(testcase.get('time', 0))
                    )
                    
                    failure = testcase.find('failure')
                    error = testcase.find('error')
                    skipped = testcase.find('skipped')
                    
                    if failure is not None:
                        test.status = TestStatus.FAILED
                        test.failure_message = failure.get('message', '')
                        test.failure_type = failure.get('type', '')
                        suite.failed += 1
                    elif error is not None:
                        test.status = TestStatus.ERROR
                        test.failure_message = error.get('message', '')
                        test.failure_type = error.get('type', '')
                        suite.errors += 1
                    elif skipped is not None:
                        test.status = TestStatus.SKIPPED
                        test.skipped_reason = skipped.get('message', '')
                        suite.skipped += 1
                    else:
                        test.status = TestStatus.PASSED
                        suite.passed += 1
                    
                    # Find file in suite
                    file_path = test.file_path
                    if file_path not in [f.file_path for f in suite.files]:
                        suite.files.append(TestFile(file_path=file_path))
                    
                    for f in suite.files:
                        if f.file_path == file_path:
                            f.tests.append(test)
                            if test.status == TestStatus.PASSED:
                                f.passed += 1
                            elif test.status == TestStatus.FAILED:
                                f.failed += 1
                            elif test.status == TestStatus.SKIPPED:
                                f.skipped += 1
                            elif test.status == TestStatus.ERROR:
                                f.errors += 1
                            f.duration += test.duration
                            break
                
                suites.append(suite)
                
        except Exception as e:
            logger.error(f"Failed to parse JUnit XML: {e}")
        
        return suites
    
    def parse_json_report(self, json_path: Path) -> List[TestSuite]:
        """Parse pytest JSON report."""
        suites = []
        
        try:
            with open(json_path, 'r') as f:
                data = json.load(f)
            
            suite = TestSuite(name="pytest", total_tests=data.get('summary', {}).get('total', 0))
            
            for test_data in data.get('tests', []):
                test = TestCase(
                    name=test_data.get('nodeid', 'unknown'),
                    file_path=test_data.get('nodeid', '').split('::')[0],
                    duration=test_data.get('duration', 0)
                )
                
                outcome = test_data.get('outcome', '')
                if outcome == 'passed':
                    test.status = TestStatus.PASSED
                    suite.passed += 1
                elif outcome == 'failed':
                    test.status = TestStatus.FAILED
                    test.failure_message = test_data.get('call', {}).get('longrepr', '')
                    suite.failed += 1
                elif outcome == 'skipped':
                    test.status = TestStatus.SKIPPED
                    test.skipped_reason = test_data.get('call', {}).get('longrepr', '')
                    suite.skipped += 1
                elif outcome == 'xfailed':
                    test.status = TestStatus.XFAIL
                    suite.xfailed += 1
                elif outcome == 'xpassed':
                    test.status = TestStatus.XPASS
                    suite.xpassed += 1
                
                # Find or create file
                file_path = test.file_path
                existing = next((f for f in suite.files if f.file_path == file_path), None)
                if not existing:
                    existing = TestFile(file_path=file_path)
                    suite.files.append(existing)
                
                existing.tests.append(test)
                if test.status == TestStatus.PASSED:
                    existing.passed += 1
                elif test.status == TestStatus.FAILED:
                    existing.failed += 1
                elif test.status == TestStatus.SKIPPED:
                    existing.skipped += 1
                elif test.status == TestStatus.XFAIL:
                    existing.xfailed += 1
                elif test.status == TestStatus.XPASS:
                    existing.xpassed += 1
                existing.duration += test.duration
            
            suites.append(suite)
            
        except Exception as e:
            logger.error(f"Failed to parse JSON report: {e}")
        
        return suites
    
    def parse_text_output(self, output: str) -> TestSuite:
        """Parse pytest text output."""
        suite = TestSuite(name="pytest")
        
        lines = output.split('\n')
        current_file = None
        
        for line in lines:
            # Test file detection
            if '::' in line and ('PASSED' in line or 'FAILED' in line or 'SKIPPED' in line):
                parts = line.split('::')
                file_path = parts[0]
                test_name = '::'.join(parts[1:]).split()[0]
                
                test = TestCase(
                    name=test_name,
                    file_path=file_path
                )
                
                if 'PASSED' in line:
                    test.status = TestStatus.PASSED
                    suite.passed += 1
                elif 'FAILED' in line:
                    test.status = TestStatus.FAILED
                    suite.failed += 1
                elif 'SKIPPED' in line:
                    test.status = TestStatus.SKIPPED
                    suite.skipped += 1
                elif 'XFAIL' in line:
                    test.status = TestStatus.XFAIL
                    suite.xfailed += 1
                elif 'XPASS' in line:
                    test.status = TestStatus.XPASS
                    suite.xpassed += 1
                
                suite.total_tests += 1
                
                # Find or create file
                existing = next((f for f in suite.files if f.file_path == file_path), None)
                if not existing:
                    existing = TestFile(file_path=file_path)
                    suite.files.append(existing)
                
                existing.tests.append(test)
            
            # Summary line
            if 'passed' in line and 'failed' in line:
                import re
                passed_match = re.search(r'(\d+)\s+passed', line)
                failed_match = re.search(r'(\d+)\s+failed', line)
                skipped_match = re.search(r'(\d+)\s+skipped', line)
                xfailed_match = re.search(r'(\d+)\s+xfailed', line)
                xpassed_match = re.search(r'(\d+)\s+xpassed', line)
                
                if passed_match:
                    suite.passed = int(passed_match.group(1))
                if failed_match:
                    suite.failed = int(failed_match.group(1))
                if skipped_match:
                    suite.skipped = int(skipped_match.group(1))
                if xfailed_match:
                    suite.xfailed = int(xfailed_match.group(1))
                if xpassed_match:
                    suite.xpassed = int(xpassed_match.group(1))
                
                suite.total_tests = suite.passed + suite.failed + suite.skipped + suite.xfailed + suite.xpassed
        
        return suite


# ============================================================
# MAIN PYTEST VALIDATOR
# ============================================================

class PytestValidator:
    """
    Validates pytest test execution and results.
    
    Features:
    - Run pytest with configurable options
    - Parse multiple output formats (JUnit XML, JSON, text)
    - Track test statistics and pass rates
    - Identify slow tests
    - Detect flaky tests (with multiple runs)
    - Generate comprehensive reports
    - Coverage integration
    - Parallel test execution support
    """
    
    def __init__(self, config: PytestValidatorConfig):
        self.config = config
        self.parser = PytestOutputParser()
        self.state = StateManager(config.project_root / ".ai_state" / "pytest_validator.json")
        
        self._pytest_version: Optional[str] = None
        self._python_version: Optional[str] = None
        
        logger.info("PytestValidator initialized")
    
    def validate(self) -> PytestReport:
        """Run complete pytest validation."""
        logger.info("Starting pytest validation...")
        
        report = PytestReport(
            project_name=self.config.project_root.name,
            pytest_version=self._get_pytest_version(),
            python_version=self._get_python_version()
        )
        
        # Run pytest
        output, returncode, junit_path = self._run_pytest()
        
        # Parse results
        if junit_path and junit_path.exists():
            suites = self.parser.parse_junit_xml(junit_path)
        else:
            suites = [self.parser.parse_text_output(output)]
        
        # Aggregate results
        for suite in suites:
            report.test_suites[suite.name] = suite
            report.total_tests += suite.total_tests
            report.passed += suite.passed
            report.failed += suite.failed
            report.skipped += suite.skipped
            report.xfailed += suite.xfailed
            report.xpassed += suite.xpassed
            report.errors += suite.errors
            report.total_duration += suite.duration
            
            for test_file in suite.files:
                if test_file.file_path not in report.test_files:
                    report.test_files[test_file.file_path] = test_file
                else:
                    existing = report.test_files[test_file.file_path]
                    existing.tests.extend(test_file.tests)
                    existing.passed += test_file.passed
                    existing.failed += test_file.failed
                    existing.skipped += test_file.skipped
                    existing.duration += test_file.duration
                
                # Collect failed tests
                for test in test_file.tests:
                    if test.status == TestStatus.FAILED:
                        report.failed_tests.append(test)
                    elif test.status == TestStatus.SKIPPED:
                        report.skipped_tests.append(test)
                    
                    # Check for slow tests
                    if test.duration > self.config.slow_test_threshold:
                        report.slow_tests.append(test)
        
        # Calculate pass rate
        if report.total_tests > 0:
            report.pass_rate = (report.passed / report.total_tests) * 100
        
        # Sort slow tests
        report.slow_tests.sort(key=lambda t: t.duration, reverse=True)
        
        # Check coverage if requested
        if self.config.check_coverage:
            coverage = self._run_coverage()
            report.coverage_percent = coverage.get('percent')
            report.coverage_missing = coverage.get('missing', [])
        
        # Detect flaky tests if requested
        if self.config.detect_flaky_tests:
            report.flaky_tests = self._detect_flaky_tests()
        
        # Identify issues
        self._identify_issues(report)
        
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
        
        logger.info(f"Pytest validation complete: {report.passed}/{report.total_tests} passed ({report.pass_rate:.1f}%)")
        
        return report
    
    def validate_file(self, file_path: Path) -> PytestReport:
        """Run pytest on a single file."""
        original_args = self.config.pytest_args
        self.config.pytest_args = [str(file_path)] + original_args
        
        try:
            return self.validate()
        finally:
            self.config.pytest_args = original_args
    
    def _run_pytest(self) -> Tuple[str, int, Optional[Path]]:
        """Run pytest and return output."""
        cmd = ['pytest']
        
        # Add test paths
        for test_path in self.config.test_paths:
            full_path = self.config.project_root / test_path
            if full_path.exists():
                cmd.append(str(full_path))
        
        # Add pytest arguments
        cmd.extend(self.config.pytest_args)
        
        # Add JUnit XML output
        junit_path = self.config.project_root / ".ai_state" / "pytest_results.xml"
        junit_path.parent.mkdir(parents=True, exist_ok=True)
        cmd.extend(['--junitxml', str(junit_path)])
        
        # Add parallel execution
        if self.config.parallel:
            cmd.extend(['-n', str(self.config.num_workers)])
        
        # Add timeout
        cmd.extend(['--timeout', str(self.config.timeout)])
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.config.timeout + 30,
                cwd=self.config.project_root
            )
            
            return result.stdout + result.stderr, result.returncode, junit_path
            
        except subprocess.TimeoutExpired:
            logger.error("Pytest timed out")
            return "Pytest timed out", -1, None
        except FileNotFoundError:
            logger.error("pytest not found. Please install pytest: pip install pytest")
            return "pytest not found", -1, None
        except Exception as e:
            logger.error(f"Failed to run pytest: {e}")
            return str(e), -1, None
    
    def _run_coverage(self) -> Dict[str, Any]:
        """Run pytest with coverage."""
        coverage = {'percent': None, 'missing': []}
        
        cmd = ['pytest']
        cmd.extend(['--cov=' + str(self.config.project_root)])
        cmd.extend(['--cov-report=term-missing'])
        
        if self.config.coverage_config:
            cmd.extend(['--cov-config', str(self.config.coverage_config)])
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.config.timeout + 60,
                cwd=self.config.project_root
            )
            
            output = result.stdout + result.stderr
            
            # Parse coverage percentage
            import re
            total_match = re.search(r'TOTAL\s+\d+\s+\d+\s+(\d+)%', output)
            if total_match:
                coverage['percent'] = int(total_match.group(1))
            
            # Parse missing lines
            for line in output.split('\n'):
                if 'Missing' in line and '.py' in line:
                    coverage['missing'].append(line.strip())
            
        except Exception as e:
            logger.warning(f"Failed to run coverage: {e}")
        
        return coverage
    
    def _detect_flaky_tests(self) -> List[TestCase]:
        """Detect flaky tests by running multiple times."""
        flaky = []
        
        # Get list of tests
        cmd = ['pytest', '--collect-only', '-q']
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                cwd=self.config.project_root
            )
            
            test_list = [l.strip() for l in result.stdout.split('\n') if '::' in l]
            
            for test_name in test_list[:10]:  # Limit to first 10 tests
                passes = 0
                
                for _ in range(self.config.flaky_test_runs):
                    test_cmd = ['pytest', test_name, '-q']
                    test_result = subprocess.run(
                        test_cmd,
                        capture_output=True,
                        text=True,
                        timeout=30,
                        cwd=self.config.project_root
                    )
                    
                    if test_result.returncode == 0:
                        passes += 1
                
                pass_rate = passes / self.config.flaky_test_runs
                if 0 < pass_rate < self.config.flaky_threshold:
                    flaky.append(TestCase(
                        name=test_name,
                        file_path=test_name.split('::')[0],
                        status=TestStatus.FAILED,
                        metadata={'pass_rate': pass_rate}
                    ))
                    
        except Exception as e:
            logger.warning(f"Failed to detect flaky tests: {e}")
        
        return flaky
    
    def _get_pytest_version(self) -> str:
        """Get pytest version."""
        if self._pytest_version:
            return self._pytest_version
        
        try:
            result = subprocess.run(
                ['pytest', '--version'],
                capture_output=True,
                text=True,
                timeout=10
            )
            self._pytest_version = result.stdout.strip().split()[1]
        except Exception:
            self._pytest_version = "unknown"
        
        return self._pytest_version
    
    def _get_python_version(self) -> str:
        """Get Python version."""
        if self._python_version:
            return self._python_version
        
        import sys
        self._python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        return self._python_version
    
    def _identify_issues(self, report: PytestReport):
        """Identify test issues."""
        # Failed tests
        for test in report.failed_tests:
            severity = Severity.HIGH
            if 'assert' in str(test.failure_message):
                severity = Severity.MEDIUM
            
            issue = TestIssue(
                issue_type="test_failure",
                severity=severity,
                test_name=test.name,
                file_path=test.file_path,
                description=f"Test failed: {test.name}",
                failure_message=test.failure_message,
                suggestion="Fix the failing test or the code it tests"
            )
            report.issues.append(issue)
        
        # XPass tests (expected to fail but passed)
        for suite in report.test_suites.values():
            for test_file in suite.files:
                for test in test_file.tests:
                    if test.status == TestStatus.XPASS:
                        issue = TestIssue(
                            issue_type="xpass",
                            severity=Severity.WARNING,
                            test_name=test.name,
                            file_path=test.file_path,
                            description=f"Test unexpectedly passed (marked as xfail)",
                            suggestion="Remove xfail marker or investigate why test passes"
                        )
                        report.warnings.append(issue)
        
        # Slow tests
        for test in report.slow_tests[:5]:
            if test.duration > self.config.very_slow_test_threshold:
                severity = Severity.WARNING
            else:
                severity = Severity.INFO
            
            issue = TestIssue(
                issue_type="slow_test",
                severity=severity,
                test_name=test.name,
                file_path=test.file_path,
                description=f"Slow test took {test.duration:.2f}s",
                suggestion="Optimize test or mark with @pytest.mark.slow"
            )
            report.warnings.append(issue)
        
        # Low pass rate
        if report.pass_rate < self.config.min_pass_rate:
            issue = TestIssue(
                issue_type="low_pass_rate",
                severity=Severity.HIGH,
                test_name="",
                file_path="",
                description=f"Test pass rate {report.pass_rate:.1f}% below minimum {self.config.min_pass_rate:.1f}%",
                suggestion=f"Fix {report.failed} failing tests"
            )
            report.issues.append(issue)
        
        # Coverage issues
        if report.coverage_percent and report.coverage_percent < self.config.min_coverage:
            issue = TestIssue(
                issue_type="low_coverage",
                severity=Severity.MEDIUM,
                test_name="",
                file_path="",
                description=f"Coverage {report.coverage_percent}% below minimum {self.config.min_coverage}%",
                suggestion="Add tests for uncovered code"
            )
            report.issues.append(issue)
    
    def _determine_validity(self, report: PytestReport) -> bool:
        """Determine if tests are valid."""
        if self.config.fail_on_failure and report.failed > 0:
            return False
        if self.config.fail_on_error and report.errors > 0:
            return False
        if self.config.fail_on_skip and report.skipped > 0:
            return False
        if self.config.fail_on_xpass and report.xpassed > 0:
            return False
        if report.pass_rate < self.config.min_pass_rate:
            return False
        if self.config.check_coverage and report.coverage_percent:
            if report.coverage_percent < self.config.min_coverage:
                return False
        return True
    
    def _calculate_overall_score(self, report: PytestReport) -> float:
        """Calculate overall test health score."""
        score = 100.0
        
        # Deduct for failed tests
        if report.total_tests > 0:
            fail_rate = (report.failed / report.total_tests) * 100
            score -= fail_rate * 2
        
        # Deduct for errors
        if report.total_tests > 0:
            error_rate = (report.errors / report.total_tests) * 100
            score -= error_rate * 3
        
        # Deduct for skipped tests
        if report.total_tests > 0:
            skip_rate = (report.skipped / report.total_tests) * 100
            score -= skip_rate * 0.5
        
        # Deduct for xpass
        if report.total_tests > 0:
            xpass_rate = (report.xpassed / report.total_tests) * 100
            score -= xpass_rate * 1
        
        # Add for coverage
        if report.coverage_percent:
            score = (score * 0.6) + (report.coverage_percent * 0.4)
        
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
    
    def _generate_summary(self, report: PytestReport) -> str:
        """Generate validation summary."""
        if report.is_valid:
            return f"✅ Tests passed. {report.passed}/{report.total_tests} passed ({report.pass_rate:.1f}%)"
        else:
            return f"❌ Test issues: {report.failed} failed, {report.errors} errors, {report.skipped} skipped"
    
    def _generate_recommendations(self, report: PytestReport) -> List[str]:
        """Generate recommendations."""
        recommendations = []
        
        if report.failed > 0:
            recommendations.append(f"Fix {report.failed} failing tests")
        
        if report.errors > 0:
            recommendations.append(f"Fix {report.errors} test errors")
        
        if report.slow_tests:
            slowest = report.slow_tests[0]
            recommendations.append(f"Optimize slow test '{slowest.name}' ({slowest.duration:.2f}s)")
        
        if report.flaky_tests:
            recommendations.append(f"Investigate {len(report.flaky_tests)} flaky tests")
        
        if report.coverage_percent and report.coverage_percent < self.config.min_coverage:
            recommendations.append(f"Increase coverage from {report.coverage_percent}% to {self.config.min_coverage}%")
        
        return recommendations[:5]
    
    def _save_report(self, report: PytestReport):
        """Save report to state."""
        reports = self.state.get('reports', [])
        reports.append({
            'timestamp': report.validated_at.isoformat(),
            'project': report.project_name,
            'is_valid': report.is_valid,
            'score': report.overall_score,
            'grade': report.grade,
            'total_tests': report.total_tests,
            'passed': report.passed,
            'failed': report.failed,
            'skipped': report.skipped,
            'pass_rate': report.pass_rate,
            'coverage': report.coverage_percent
        })
        
        if len(reports) > 50:
            reports = reports[-50:]
        
        self.state.set('reports', reports)
        self.state.save()
    
    def export_report(self, report: PytestReport,
                      output_path: Optional[Path] = None,
                      format: str = 'markdown') -> str:
        """Export pytest report."""
        
        if format == 'json':
            data = {
                'validated_at': report.validated_at.isoformat(),
                'project': report.project_name,
                'pytest_version': report.pytest_version,
                'python_version': report.python_version,
                'is_valid': report.is_valid,
                'score': report.overall_score,
                'grade': report.grade,
                'summary': report.summary,
                'statistics': {
                    'total_tests': report.total_tests,
                    'passed': report.passed,
                    'failed': report.failed,
                    'skipped': report.skipped,
                    'xfailed': report.xfailed,
                    'xpassed': report.xpassed,
                    'errors': report.errors,
                    'pass_rate': report.pass_rate,
                    'duration': report.total_duration,
                    'coverage': report.coverage_percent
                },
                'failed_tests': [
                    {
                        'name': t.name,
                        'file': t.file_path,
                        'message': t.failure_message[:200] if t.failure_message else None
                    }
                    for t in report.failed_tests[:20]
                ],
                'slow_tests': [
                    {'name': t.name, 'duration': t.duration}
                    for t in report.slow_tests[:10]
                ],
                'issues': [
                    {
                        'type': i.issue_type,
                        'severity': i.severity.value,
                        'description': i.description,
                        'suggestion': i.suggestion
                    }
                    for i in report.issues
                ],
                'recommendations': report.recommendations
            }
            
            content = json.dumps(data, indent=2)
            
        else:  # markdown
            lines = [
                f"# Pytest Validation Report",
                "",
                f"**Project:** {report.project_name}",
                f"**Pytest Version:** {report.pytest_version}",
                f"**Python Version:** {report.python_version}",
                f"**Validated:** {report.validated_at.strftime('%Y-%m-%d %H:%M:%S')}",
                f"**Score:** {report.overall_score:.1f} (Grade: {report.grade})",
                f"**Status:** {report.summary}",
                "",
                "## Summary",
                "",
                f"| Metric | Value |",
                f"|--------|-------|",
                f"| Total Tests | {report.total_tests} |",
                f"| Passed | {report.passed} |",
                f"| Failed | {report.failed} |",
                f"| Skipped | {report.skipped} |",
                f"| XFailed | {report.xfailed} |",
                f"| XPassed | {report.xpassed} |",
                f"| Errors | {report.errors} |",
                f"| Pass Rate | {report.pass_rate:.1f}% |",
                f"| Total Duration | {report.total_duration:.2f}s |",
            ]
            
            if report.coverage_percent:
                lines.append(f"| Coverage | {report.coverage_percent}% |")
            
            lines.append("")
            
            if report.failed_tests:
                lines.extend([
                    "## ❌ Failed Tests",
                    "",
                    "| Test | File | Message |",
                    "|------|------|---------|",
                ])
                for test in report.failed_tests[:10]:
                    file_name = Path(test.file_path).name
                    msg = (test.failure_message or '')[:50]
                    lines.append(f"| {test.name[:40]} | {file_name} | {msg} |")
                
                if len(report.failed_tests) > 10:
                    lines.append(f"| ... | ... | *and {len(report.failed_tests) - 10} more* |")
                lines.append("")
            
            if report.slow_tests:
                lines.extend([
                    "## 🐢 Slow Tests",
                    "",
                    "| Test | Duration |",
                    "|------|----------|",
                ])
                for test in report.slow_tests[:self.config.include_slow_tests]:
                    lines.append(f"| {test.name[:50]} | {test.duration:.2f}s |")
                lines.append("")
            
            if report.flaky_tests:
                lines.extend([
                    "## 🔄 Flaky Tests",
                    "",
                ])
                for test in report.flaky_tests:
                    pass_rate = test.metadata.get('pass_rate', 0) * 100
                    lines.append(f"- {test.name} (pass rate: {pass_rate:.0f}%)")
                lines.append("")
            
            if report.issues:
                lines.extend([
                    "## Issues",
                    "",
                ])
                for issue in report.issues[:10]:
                    lines.append(f"- **[{issue.severity.value}]** {issue.description}")
                    if issue.suggestion:
                        lines.append(f"  → {issue.suggestion}")
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
        logger.info("PytestValidator closed")


# ============================================================
# CLI ENTRY POINT
# ============================================================

def main():
    """CLI entry point for pytest validator."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate pytest test execution")
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--output", "-o", type=Path, help="Output report path")
    parser.add_argument("--format", choices=["json", "markdown"], default="markdown")
    parser.add_argument("--test-path", action="append", help="Test paths (can specify multiple)")
    parser.add_argument("--junit-xml", type=Path, help="Parse existing JUnit XML instead of running tests")
    parser.add_argument("--coverage", action="store_true", help="Check test coverage")
    parser.add_argument("--min-coverage", type=float, default=80.0)
    parser.add_argument("--min-pass-rate", type=float, default=90.0)
    parser.add_argument("--parallel", action="store_true", help="Run tests in parallel")
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--detect-flaky", action="store_true", help="Detect flaky tests")
    parser.add_argument("--slow-threshold", type=float, default=1.0, help="Slow test threshold in seconds")
    parser.add_argument("--fail-on-skip", action="store_true")
    parser.add_argument("--fail-on-xpass", action="store_true")
    
    args = parser.parse_args()
    
    config = PytestValidatorConfig(
        project_root=args.project_root,
        check_coverage=args.coverage,
        min_coverage=args.min_coverage,
        min_pass_rate=args.min_pass_rate,
        parallel=args.parallel,
        num_workers=args.workers,
        detect_flaky_tests=args.detect_flaky,
        slow_test_threshold=args.slow_threshold,
        fail_on_skip=args.fail_on_skip,
        fail_on_xpass=args.fail_on_xpass,
        junit_xml=args.junit_xml
    )
    
    if args.test_path:
        config.test_paths = args.test_path
    
    validator = PytestValidator(config)
    
    # Parse existing JUnit XML or run tests
    if args.junit_xml:
        suites = validator.parser.parse_junit_xml(args.junit_xml)
        report = PytestReport(
            project_name=args.project_root.name,
            pytest_version=validator._get_pytest_version()
        )
        for suite in suites:
            report.test_suites[suite.name] = suite
            report.total_tests += suite.total_tests
            report.passed += suite.passed
            report.failed += suite.failed
            report.skipped += suite.skipped
        if report.total_tests > 0:
            report.pass_rate = (report.passed / report.total_tests) * 100
        report.summary = f"Parsed JUnit XML: {report.passed}/{report.total_tests} passed"
    else:
        report = validator.validate()
    
    output = validator.export_report(report, args.output, args.format)
    
    if not args.output:
        print(output)
    else:
        print(f"Report saved to {args.output}")
    
    print(f"\n{report.summary}")
    
    if config.fail_on_failure and not report.is_valid:
        exit(1)
    
    validator.close()


if __name__ == "__main__":
    main()