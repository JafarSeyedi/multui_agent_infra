"""
Test Updater for Co-Evolution Engine

Automatically updates tests when code changes to maintain consistency.
Handles:
- Test synchronization with code changes
- Test generation for new functions/classes
- Test assertion updates
- Mock updates when APIs change
- Test coverage maintenance
- Regression test creation

This implementation provides:

    Test Discovery: Scans for pytest and unittest tests in test directories
    Test Extraction: Extracts test cases with assertions, mocks, and fixtures
    Code Change Tracking: Register code changes and find affected tests
    Auto-Update: Automatically update tests for signature changes, parameter changes
    Test Generation: Generate new tests for untested functions
    Regression Tests: Create regression tests for bug fixes
    Mock Updates: Update mock paths when code changes
    Coverage Reporting: Generate test coverage reports
    Test Execution: Run tests and update statuses automatically
    Singleton Pattern: Global instance via get_test_updater()
"""

import re
import ast
import inspect
from typing import Dict, List, Optional, Any, Set, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from enum import Enum
from collections import defaultdict

from ....shared.logger import get_logger
from ....shared.state_manager import state_manager
from ....shared.config import config
from ....shared.file_utils import file_utils

logger = get_logger(__name__)


class TestType(Enum):
    """Types of tests"""
    UNIT = "unit"
    INTEGRATION = "integration"
    FUNCTIONAL = "functional"
    REGRESSION = "regression"
    PERFORMANCE = "performance"
    MOCK = "mock"
    FIXTURE = "fixture"


class TestStatus(Enum):
    """Status of a test"""
    PASSING = "passing"
    FAILING = "failing"
    OUTDATED = "outdated"
    SKIPPED = "skipped"
    NEEDS_UPDATE = "needs_update"
    DEPRECATED = "deprecated"


@dataclass
class TestCase:
    """Represents a test case"""
    id: str
    name: str
    file_path: str
    test_type: TestType
    target_function: Optional[str] = None
    target_class: Optional[str] = None
    assertions: List[str] = field(default_factory=list)
    mocks: List[str] = field(default_factory=list)
    fixtures: List[str] = field(default_factory=list)
    status: TestStatus = TestStatus.PASSING
    last_run: Optional[datetime] = None
    last_duration: float = 0.0
    error_message: Optional[str] = None
    code: str = ""
    line_number: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "file_path": self.file_path,
            "test_type": self.test_type.value,
            "target_function": self.target_function,
            "target_class": self.target_class,
            "assertions": self.assertions,
            "mocks": self.mocks,
            "fixtures": self.fixtures,
            "status": self.status.value,
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "last_duration": self.last_duration,
            "error_message": self.error_message,
            "code": self.code,
            "line_number": self.line_number
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TestCase":
        return cls(
            id=data["id"],
            name=data["name"],
            file_path=data["file_path"],
            test_type=TestType(data["test_type"]),
            target_function=data.get("target_function"),
            target_class=data.get("target_class"),
            assertions=data.get("assertions", []),
            mocks=data.get("mocks", []),
            fixtures=data.get("fixtures", []),
            status=TestStatus(data["status"]) if data.get("status") else TestStatus.PASSING,
            last_run=datetime.fromisoformat(data["last_run"]) if data.get("last_run") else None,
            last_duration=data.get("last_duration", 0.0),
            error_message=data.get("error_message"),
            code=data.get("code", ""),
            line_number=data.get("line_number", 0)
        )


@dataclass
class CodeChange:
    """Represents a change in code that affects tests"""
    file_path: str
    element_name: str
    element_type: str  # function, class, method, parameter
    change_type: str   # added, removed, modified, signature_change
    old_signature: Optional[str] = None
    new_signature: Optional[str] = None
    added_parameters: List[str] = field(default_factory=list)
    removed_parameters: List[str] = field(default_factory=list)
    changed_return_type: Optional[str] = None


@dataclass
class TestUpdate:
    """Represents a test update operation"""
    test_id: str
    update_type: str  # auto_fix, regenerate, manual_required, delete
    changes: List[str]
    old_code: str
    new_code: str
    timestamp: datetime = field(default_factory=datetime.now)
    applied: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "test_id": self.test_id,
            "update_type": self.update_type,
            "changes": self.changes,
            "old_code": self.old_code,
            "new_code": self.new_code,
            "timestamp": self.timestamp.isoformat(),
            "applied": self.applied
        }


class TestUpdater:
    """
    Automatically updates tests when code changes.
    
    Features:
    - Detects code changes that affect tests
    - Updates test assertions automatically
    - Regenerates tests for modified APIs
    - Maintains test coverage
    - Creates regression tests for bug fixes
    - Updates mocks when signatures change
    """
    
    def __init__(self, storage_key: str = "test_updater"):
        self.storage_key = storage_key
        self.tests: Dict[str, TestCase] = {}
        self.code_changes: List[CodeChange] = []
        self.test_updates: List[TestUpdate] = []
        self.test_dirs: List[Path] = []
        
        # Test frameworks supported
        self.test_frameworks = ["pytest", "unittest"]
        
        self._load_data()
        self._register_default_test_dirs()
        
        logger.info("TestUpdater initialized")
    
    def _load_data(self) -> None:
        """Load test data from state manager"""
        try:
            tests_data = state_manager.get(f"{self.storage_key}.tests", {})
            self.tests = {}
            for test_id, test_data in tests_data.items():
                if isinstance(test_data, dict):
                    self.tests[test_id] = TestCase.from_dict(test_data)
            
            updates_data = state_manager.get(f"{self.storage_key}.updates", [])
            self.test_updates = []
            for u in updates_data:
                if isinstance(u, dict):
                    self.test_updates.append(TestUpdate(**u))
            
            changes_data = state_manager.get(f"{self.storage_key}.code_changes", [])
            self.code_changes = []
            for c in changes_data:
                if isinstance(c, dict):
                    self.code_changes.append(CodeChange(**c))
            
        except Exception as e:
            logger.warning(f"Failed to load test data: {e}")
    
    def _save_data(self) -> None:
        """Save test data to state manager"""
        try:
            tests_data = {tid: test.to_dict() for tid, test in self.tests.items()}
            state_manager.set(f"{self.storage_key}.tests", tests_data)
            
            updates_data = [u.to_dict() for u in self.test_updates]
            state_manager.set(f"{self.storage_key}.updates", updates_data)
            
            changes_data = [c.__dict__ for c in self.code_changes]
            state_manager.set(f"{self.storage_key}.code_changes", changes_data)
            
        except Exception as e:
            logger.error(f"Failed to save test data: {e}")
    
    def _register_default_test_dirs(self) -> None:
        """Register default test directories"""
        default_dirs = [
            Path("tests"),
            Path("test"),
            Path("tools/ai/tests"),
            Path("tools/ai/test"),
        ]
        
        for dir_path in default_dirs:
            if dir_path.exists():
                self.test_dirs.append(dir_path)
    
    def add_test_directory(self, dir_path: Union[str, Path]) -> None:
        """Add a directory to scan for tests"""
        path = Path(dir_path)
        if path.exists() and path.is_dir():
            self.test_dirs.append(path)
            logger.info(f"Added test directory: {path}")
    
    def scan_tests(self) -> List[TestCase]:
        """Scan for tests in registered directories"""
        discovered_tests = []
        
        for test_dir in self.test_dirs:
            for file_path in test_dir.rglob("test_*.py"):
                tests = self._extract_tests_from_file(file_path)
                discovered_tests.extend(tests)
        
        # Update registry
        for test in discovered_tests:
            if test.id not in self.tests:
                self.tests[test.id] = test
                logger.debug(f"Discovered new test: {test.id}")
            else:
                # Update if changed
                existing = self.tests[test.id]
                if existing.code != test.code:
                    existing.code = test.code
                    existing.status = TestStatus.NEEDS_UPDATE
        
        self._save_data()
        
        return discovered_tests
    
    def _extract_tests_from_file(self, file_path: Path) -> List[TestCase]:
        """Extract test cases from a test file"""
        tests = []
        content = file_utils.read_file(str(file_path))
        
        try:
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                # Extract test functions (pytest style)
                if isinstance(node, ast.FunctionDef):
                    if node.name.startswith("test_"):
                        test = self._create_test_case_from_function(node, file_path, content)
                        tests.append(test)
                
                # Extract test classes (unittest style)
                elif isinstance(node, ast.ClassDef):
                    if node.name.startswith("Test"):
                        for method in ast.walk(node):
                            if isinstance(method, ast.FunctionDef):
                                if method.name.startswith("test_"):
                                    test = self._create_test_case_from_method(method, node, file_path, content)
                                    tests.append(test)
        
        except SyntaxError as e:
            logger.warning(f"Failed to parse {file_path}: {e}")
        
        return tests
    
    def _create_test_case_from_function(self, func: ast.FunctionDef, 
                                        file_path: Path, 
                                        content: str) -> TestCase:
        """Create TestCase from a test function"""
        # Extract assertions
        assertions = self._extract_assertions(func)
        
        # Extract mocks
        mocks = self._extract_mocks(func)
        
        # Extract fixtures
        fixtures = self._extract_fixtures(func)
        
        # Get function code
        func_code = ast.unparse(func) if hasattr(ast, 'unparse') else ""
        
        # Try to determine target
        target_func = self._infer_target_function(func, content)
        
        test_id = f"{file_path}:{func.name}"
        
        return TestCase(
            id=test_id,
            name=func.name,
            file_path=str(file_path),
            test_type=TestType.UNIT,
            target_function=target_func,
            assertions=assertions,
            mocks=mocks,
            fixtures=fixtures,
            code=func_code,
            line_number=func.lineno
        )
    
    def _create_test_case_from_method(self, method: ast.FunctionDef,
                                     class_node: ast.ClassDef,
                                     file_path: Path,
                                     content: str) -> TestCase:
        """Create TestCase from a test method"""
        assertions = self._extract_assertions(method)
        mocks = self._extract_mocks(method)
        fixtures = self._extract_fixtures(method)
        
        method_code = ast.unparse(method) if hasattr(ast, 'unparse') else ""
        
        test_id = f"{file_path}:{class_node.name}.{method.name}"
        
        return TestCase(
            id=test_id,
            name=f"{class_node.name}.{method.name}",
            file_path=str(file_path),
            test_type=TestType.UNIT,
            target_class=class_node.name,
            target_function=method.name,
            assertions=assertions,
            mocks=mocks,
            fixtures=fixtures,
            code=method_code,
            line_number=method.lineno
        )
    
    def _extract_assertions(self, func: ast.FunctionDef) -> List[str]:
        """Extract assertion statements from function"""
        assertions = []
        
        for node in ast.walk(func):
            if isinstance(node, ast.Assert):
                # Convert assert node to string
                if hasattr(ast, 'unparse'):
                    assertions.append(ast.unparse(node))
                else:
                    assertions.append("assert")
            elif isinstance(node, ast.Expr):
                if isinstance(node.value, ast.Call):
                    if hasattr(node.value.func, 'attr'):
                        if node.value.func.attr.startswith('assert'):
                            if hasattr(ast, 'unparse'):
                                assertions.append(ast.unparse(node))
        
        return assertions
    
    def _extract_mocks(self, func: ast.FunctionDef) -> List[str]:
        """Extract mock objects from function"""
        mocks = []
        
        for node in ast.walk(func):
            if isinstance(node, ast.Call):
                if hasattr(node.func, 'attr'):
                    if 'patch' in node.func.attr or 'Mock' in node.func.attr:
                        if hasattr(ast, 'unparse'):
                            mocks.append(ast.unparse(node))
        
        return mocks
    
    def _extract_fixtures(self, func: ast.FunctionDef) -> List[str]:
        """Extract fixture names from function"""
        fixtures = []
        
        # Look for pytest fixtures in decorators
        for decorator in func.decorator_list:
            if isinstance(decorator, ast.Name):
                if decorator.id == 'pytest.fixture':
                    fixtures.append(func.name)
            elif isinstance(decorator, ast.Attribute):
                if decorator.attr == 'fixture':
                    fixtures.append(func.name)
        
        # Look for fixture parameters
        for arg in func.args.args:
            arg_name = arg.arg
            # Common fixture names
            if arg_name in ['client', 'db', 'session', 'mock_', 'fixture']:
                fixtures.append(arg_name)
        
        return fixtures
    
    def _infer_target_function(self, func: ast.FunctionDef, content: str) -> Optional[str]:
        """Infer the target function being tested"""
        # Look for calls to functions being tested
        for node in ast.walk(func):
            if isinstance(node, ast.Call):
                if hasattr(node.func, 'id'):
                    func_name = node.func.id
                    # Skip test helpers
                    if not func_name.startswith('assert') and not func_name.startswith('mock'):
                        return func_name
                elif hasattr(node.func, 'attr'):
                    return node.func.attr
        
        # Try to infer from test name
        if func.name.startswith('test_'):
            # Remove 'test_' prefix
            target = func.name[5:]
            if target:
                return target
        
        return None
    
    def register_code_change(self, code_change: CodeChange) -> None:
        """Register a code change that may affect tests"""
        self.code_changes.append(code_change)
        
        # Find affected tests
        affected = self.find_affected_tests(code_change)
        
        for test in affected:
            test.status = TestStatus.OUTDATED
            test.error_message = f"Code changed: {code_change.element_name} ({code_change.change_type})"
        
        self._save_data()
        logger.info(f"Registered code change: {code_change.element_name} ({code_change.change_type})")
    
    def find_affected_tests(self, code_change: CodeChange) -> List[TestCase]:
        """Find tests affected by a code change"""
        affected = []
        
        for test in self.tests.values():
            if code_change.element_type == "function":
                if test.target_function == code_change.element_name:
                    affected.append(test)
            elif code_change.element_type == "class":
                if test.target_class == code_change.element_name:
                    affected.append(test)
            elif code_change.element_type == "method":
                if test.target_function == code_change.element_name:
                    affected.append(test)
        
        return affected
    
    def update_test_for_change(self, test_id: str, 
                              code_change: CodeChange) -> Optional[TestUpdate]:
        """Attempt to automatically update a test for a code change"""
        if test_id not in self.tests:
            return None
        
        test = self.tests[test_id]
        old_code = test.code
        new_code = old_code
        changes = []
        
        if code_change.change_type == "signature_change":
            # Update function calls in test
            if code_change.old_signature and code_change.new_signature:
                # Parse old and new parameter names
                old_params = self._parse_parameters(code_change.old_signature)
                new_params = self._parse_parameters(code_change.new_signature)
                
                # Update test code with new parameters
                for old_param, new_param in zip(old_params, new_params):
                    if old_param != new_param:
                        pattern = re.compile(rf'\b{re.escape(old_param)}\b')
                        new_code = pattern.sub(new_param, new_code)
                        changes.append(f"Renamed parameter {old_param} to {new_param}")
        
        elif code_change.change_type == "added_parameters":
            # Add default values for new parameters in test calls
            for param in code_change.added_parameters:
                # Add parameter with default value
                pattern = re.compile(rf'(\b{re.escape(test.target_function or "")}\s*\()')
                new_code = pattern.sub(rf'\1{param}=None, ', new_code)
                changes.append(f"Added parameter {param} with default value")
        
        elif code_change.change_type == "removed_parameters":
            # Remove deleted parameters from test calls
            for param in code_change.removed_parameters:
                pattern = re.compile(rf',?\s*{re.escape(param)}=[^,)]+')
                new_code = pattern.sub('', new_code)
                changes.append(f"Removed parameter {param}")
        
        elif code_change.change_type == "changed_return_type":
            # Update assertions for new return type
            changes.append(f"Return type changed to {code_change.changed_return_type}. Review assertions.")
        
        if new_code != old_code:
            update = TestUpdate(
                test_id=test_id,
                update_type="auto_fix" if changes else "manual_required",
                changes=changes,
                old_code=old_code,
                new_code=new_code
            )
            
            self.test_updates.append(update)
            self._save_data()
            
            return update
        
        return None
    
    def _parse_parameters(self, signature: str) -> List[str]:
        """Parse parameter names from function signature"""
        params = []
        # Simple regex to extract parameter names
        pattern = re.compile(r'(\w+)\s*[:=]')
        matches = pattern.findall(signature)
        if matches:
            params = matches
        else:
            # Try without type hints
            pattern2 = re.compile(r'\(([^)]+)\)')
            match = pattern2.search(signature)
            if match:
                param_str = match.group(1)
                params = [p.strip().split('=')[0].strip() for p in param_str.split(',') if p.strip()]
        
        return params
    
    def apply_update(self, update: TestUpdate) -> bool:
        """Apply a test update to the file system"""
        if update.test_id not in self.tests:
            return False
        
        test = self.tests[update.test_id]
        
        try:
            # Read current file content
            current_content = file_utils.read_file(test.file_path)
            
            # Replace the test code
            updated_content = current_content.replace(update.old_code, update.new_code)
            
            if updated_content != current_content:
                # Write back to file
                file_utils.write_file(test.file_path, updated_content)
                
                # Update test record
                test.code = update.new_code
                test.status = TestStatus.PASSING
                
                update.applied = True
                self._save_data()
                
                logger.info(f"Applied update to test: {update.test_id}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to apply update to {test.file_path}: {e}")
        
        return False
    
    def auto_update_tests(self, code_change: CodeChange = None) -> List[TestUpdate]:
        """Automatically update tests for code changes"""
        updates = []
        
        relevant_changes = self.code_changes
        if code_change:
            relevant_changes = [code_change]
        
        for change in relevant_changes:
            affected = self.find_affected_tests(change)
            
            for test in affected:
                update = self.update_test_for_change(test.id, change)
                if update:
                    updates.append(update)
                    
                    # Auto-apply if safe
                    if update.update_type == "auto_fix":
                        self.apply_update(update)
        
        return updates
    
    def generate_test_for_function(self, function_name: str, 
                                  source_file: str) -> Optional[TestCase]:
        """Generate a test for a function that lacks tests"""
        # Parse source file to get function signature
        try:
            content = file_utils.read_file(source_file)
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name == function_name:
                    # Generate test code
                    test_code = self._generate_test_code(node, source_file)
                    
                    # Create test file path
                    test_file = self._get_test_file_path(source_file)
                    
                    # Append test to file
                    self._append_test_to_file(test_file, test_code)
                    
                    # Create test case record
                    test_id = f"{test_file}:test_{function_name}"
                    test_case = TestCase(
                        id=test_id,
                        name=f"test_{function_name}",
                        file_path=str(test_file),
                        test_type=TestType.UNIT,
                        target_function=function_name,
                        code=test_code,
                        status=TestStatus.PASSING
                    )
                    
                    self.tests[test_id] = test_case
                    self._save_data()
                    
                    logger.info(f"Generated test for function: {function_name}")
                    return test_case
        
        except Exception as e:
            logger.error(f"Failed to generate test for {function_name}: {e}")
        
        return None
    
    def _generate_test_code(self, func: ast.FunctionDef, source_file: str) -> str:
        """Generate test code for a function"""
        func_name = func.name
        params = [arg.arg for arg in func.args.args]
        
        # Skip self parameter for methods
        if params and params[0] == 'self':
            params = params[1:]
        
        # Generate test
        test_code = f'''
def test_{func_name}():
    """Test {func_name} function."""
    # TODO: Add proper test data
    # Test with valid input
    result = {func_name}({', '.join(['test_value'] * len(params)) if params else ''})
    
    # TODO: Add assertions based on expected behavior
    assert result is not None
    # assert result == expected_value
    
    # Test with edge cases
    # TODO: Add edge case tests
'''
        
        return test_code.strip()
    
    def _get_test_file_path(self, source_file: str) -> Path:
        """Get corresponding test file path for a source file"""
        source_path = Path(source_file)
        
        # Determine test directory
        if self.test_dirs:
            test_dir = self.test_dirs[0]
        else:
            test_dir = Path("tests")
        
        # Create test file path
        test_file = test_dir / f"test_{source_path.name}"
        test_file.parent.mkdir(parents=True, exist_ok=True)
        
        return test_file
    
    def _append_test_to_file(self, test_file: Path, test_code: str) -> None:
        """Append test code to test file"""
        if test_file.exists():
            content = file_utils.read_file(str(test_file))
            content += "\n\n" + test_code
        else:
            content = f'''"""
Test module for {test_file.stem.replace('test_', '')}
"""

import pytest
{test_code}
'''
        
        file_utils.write_file(str(test_file), content)
    
    def create_regression_test(self, bug_description: str, 
                              failing_code: str,
                              expected_behavior: str) -> TestCase:
        """Create a regression test for a bug fix"""
        test_name = f"test_regression_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        test_code = f'''
def {test_name}():
    """Regression test for bug: {bug_description[:100]}
    
    Expected behavior: {expected_behavior}
    """
    # TODO: Implement test based on bug report
    
    # This test should fail before the fix and pass after
    # {failing_code[:200]}
    
    # Assert expected behavior
    assert True  # Replace with actual assertion
'''
        
        # Create test file
        test_file = Path("tests") / "test_regression.py"
        test_file.parent.mkdir(parents=True, exist_ok=True)
        
        self._append_test_to_file(test_file, test_code)
        
        test_id = f"{test_file}:{test_name}"
        test_case = TestCase(
            id=test_id,
            name=test_name,
            file_path=str(test_file),
            test_type=TestType.REGRESSION,
            code=test_code,
            status=TestStatus.NEEDS_UPDATE
        )
        
        self.tests[test_id] = test_case
        self._save_data()
        
        logger.info(f"Created regression test: {test_name}")
        
        return test_case
    
    def update_mocks_for_change(self, test_id: str, 
                               old_mock_path: str,
                               new_mock_path: str) -> bool:
        """Update mock paths in a test"""
        if test_id not in self.tests:
            return False
        
        test = self.tests[test_id]
        old_code = test.code
        new_code = old_code.replace(old_mock_path, new_mock_path)
        
        if new_code != old_code:
            test.code = new_code
            test.mocks = [m.replace(old_mock_path, new_mock_path) for m in test.mocks]
            
            update = TestUpdate(
                test_id=test_id,
                update_type="auto_fix",
                changes=[f"Updated mock path: {old_mock_path} -> {new_mock_path}"],
                old_code=old_code,
                new_code=new_code,
                applied=True
            )
            
            self.test_updates.append(update)
            self._save_data()
            
            # Apply to file
            self.apply_update(update)
            
            return True
        
        return False
    
    def get_test_coverage_report(self) -> Dict[str, Any]:
        """Generate test coverage report"""
        total_tests = len(self.tests)
        passing = len([t for t in self.tests.values() if t.status == TestStatus.PASSING])
        failing = len([t for t in self.tests.values() if t.status == TestStatus.FAILING])
        outdated = len([t for t in self.tests.values() if t.status == TestStatus.OUTDATED])
        needs_update = len([t for t in self.tests.values() if t.status == TestStatus.NEEDS_UPDATE])
        
        by_type = defaultdict(int)
        for test in self.tests.values():
            by_type[test.test_type.value] += 1
        
        return {
            "total_tests": total_tests,
            "passing": passing,
            "failing": failing,
            "outdated": outdated,
            "needs_update": needs_update,
            "pass_rate": (passing / total_tests * 100) if total_tests > 0 else 0,
            "by_type": dict(by_type),
            "affected_by_changes": len(self.code_changes),
            "pending_updates": len([u for u in self.test_updates if not u.applied])
        }
    
    def run_tests(self, test_pattern: str = None) -> Dict[str, Any]:
        """Run tests and update status"""
        import subprocess
        
        cmd = ['pytest', '-v', '--tb=short']
        if test_pattern:
            cmd.append(f"-k={test_pattern}")
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=Path.cwd()
            )
            
            # Parse output to update test statuses
            self._update_test_statuses_from_output(result.stdout)
            
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
            
        except Exception as e:
            logger.error(f"Failed to run tests: {e}")
            return {"success": False, "error": str(e)}
    
    def _update_test_statuses_from_output(self, output: str) -> None:
        """Update test statuses based on pytest output"""
        # Parse pytest output for test results
        passed_pattern = re.compile(r'(\S+)\s+PASSED')
        failed_pattern = re.compile(r'(\S+)\s+FAILED')
        
        for match in passed_pattern.finditer(output):
            test_name = match.group(1)
            for test in self.tests.values():
                if test.name in test_name:
                    test.status = TestStatus.PASSING
                    test.last_run = datetime.now()
        
        for match in failed_pattern.finditer(output):
            test_name = match.group(1)
            for test in self.tests.values():
                if test.name in test_name:
                    test.status = TestStatus.FAILING
                    test.last_run = datetime.now()
        
        self._save_data()
    
    def get_test_summary(self) -> Dict[str, Any]:
        """Get summary of all tests"""
        return {
            "total_tests": len(self.tests),
            "test_dirs": [str(d) for d in self.test_dirs],
            "code_changes": len(self.code_changes),
            "pending_updates": len([u for u in self.test_updates if not u.applied]),
            "test_types": list(set(t.test_type.value for t in self.tests.values())),
            "most_failing": [
                {"id": t.id, "name": t.name, "error": t.error_message}
                for t in self.tests.values()
                if t.status == TestStatus.FAILING
            ][:10]
        }


# Singleton instance
_test_updater: Optional[TestUpdater] = None


def get_test_updater() -> TestUpdater:
    """Get global TestUpdater instance"""
    global _test_updater
    if _test_updater is None:
        _test_updater = TestUpdater()
    return _test_updater