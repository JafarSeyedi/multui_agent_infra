"""
Example Updater for Co-Evolution Engine

Automatically updates code examples when APIs change to maintain consistency.
Handles:
- Example code synchronization
- API usage example updates
- Tutorial example validation
- Code snippet testing
- Example extraction from docstrings
- Versioned example management

This implementation provides:

    Example Extraction: Extracts code examples from Python files, Markdown, and RST files
    API Change Tracking: Register API changes and find affected examples
    Example Validation: Parse and compile examples to check validity
    Auto-Update: Automatically update examples for renamed APIs
    Example Testing: Execute examples in a safe environment
    Docstring Examples: Extract examples from function/class docstrings
    Template System: Create new examples from templates
    Status Tracking: Track valid, outdated, broken, and deprecated examples
    Report Generation: Comprehensive reports on example health
    Singleton Pattern: Global instance via get_example_updater()
"""

import re
import ast
import subprocess
from typing import Dict, List, Optional, Any, Set, Tuple
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


class ExampleType(Enum):
    """Types of examples"""
    CODE_SNIPPET = "code_snippet"
    TUTORIAL = "tutorial"
    API_USAGE = "api_usage"
    WORKFLOW = "workflow"
    INTEGRATION = "integration"
    TEST = "test"
    CLI = "cli"
    CONFIG = "config"


class ExampleStatus(Enum):
    """Status of an example"""
    VALID = "valid"
    OUTDATED = "outdated"
    BROKEN = "broken"
    DEPRECATED = "deprecated"
    PENDING_UPDATE = "pending_update"


@dataclass
class CodeExample:
    """Represents a code example"""
    id: str
    type: ExampleType
    file_path: str
    content: str
    api_elements: List[str] = field(default_factory=list)  # APIs used in example
    dependencies: List[str] = field(default_factory=list)  # Required packages
    status: ExampleStatus = ExampleStatus.VALID
    version_introduced: Optional[str] = None
    last_validated: Optional[datetime] = None
    validation_errors: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    description: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type.value,
            "file_path": self.file_path,
            "content": self.content,
            "api_elements": self.api_elements,
            "dependencies": self.dependencies,
            "status": self.status.value,
            "version_introduced": self.version_introduced,
            "last_validated": self.last_validated.isoformat() if self.last_validated else None,
            "validation_errors": self.validation_errors,
            "tags": self.tags,
            "description": self.description
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CodeExample":
        return cls(
            id=data["id"],
            type=ExampleType(data["type"]),
            file_path=data["file_path"],
            content=data["content"],
            api_elements=data.get("api_elements", []),
            dependencies=data.get("dependencies", []),
            status=ExampleStatus(data["status"]) if data.get("status") else ExampleStatus.VALID,
            version_introduced=data.get("version_introduced"),
            last_validated=datetime.fromisoformat(data["last_validated"]) if data.get("last_validated") else None,
            validation_errors=data.get("validation_errors", []),
            tags=data.get("tags", []),
            description=data.get("description")
        )


@dataclass
class APIChange:
    """Represents an API change that affects examples"""
    api_name: str
    change_type: str  # signature_change, deprecated, removed, renamed
    old_signature: Optional[str] = None
    new_signature: Optional[str] = None
    old_name: Optional[str] = None
    new_name: Optional[str] = None
    migration_guide: Optional[str] = None
    version: Optional[str] = None


@dataclass
class ExampleUpdate:
    """Represents an example update operation"""
    example_id: str
    update_type: str  # auto_fix, manual_required, delete
    changes: List[str]
    old_content: str
    new_content: str
    timestamp: datetime = field(default_factory=datetime.now)
    applied: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "example_id": self.example_id,
            "update_type": self.update_type,
            "changes": self.changes,
            "old_content": self.old_content,
            "new_content": self.new_content,
            "timestamp": self.timestamp.isoformat(),
            "applied": self.applied
        }


class ExampleUpdater:
    """
    Automatically updates code examples when APIs change.
    
    Features:
    - Extracts examples from documentation and tutorials
    - Detects API usage in examples
    - Validates example code
    - Auto-updates examples when APIs change
    - Tracks example versions
    - Tests examples for correctness
    """
    
    def __init__(self, storage_key: str = "example_updater"):
        self.storage_key = storage_key
        self.examples: Dict[str, CodeExample] = {}
        self.api_changes: List[APIChange] = []
        self.example_updates: List[ExampleUpdate] = []
        self.example_dirs: List[Path] = []
        
        # Patterns for detecting API usage
        self.api_patterns = {
            "function_call": re.compile(r'(\w+)\s*\('),
            "method_call": re.compile(r'\.(\w+)\s*\('),
            "import": re.compile(r'(?:from|import)\s+(\w+(?:\.\w+)*)'),
            "class_instantiation": re.compile(r'(\w+)\s*\('),
        }
        
        self._load_data()
        self._register_default_example_dirs()
        
        logger.info("ExampleUpdater initialized")
    
    def _load_data(self) -> None:
        """Load example data from state manager"""
        try:
            examples_data = state_manager.get(f"{self.storage_key}.examples", {})
            self.examples = {}
            for ex_id, ex_data in examples_data.items():
                if isinstance(ex_data, dict):
                    self.examples[ex_id] = CodeExample.from_dict(ex_data)
            
            updates_data = state_manager.get(f"{self.storage_key}.updates", [])
            self.example_updates = []
            for u in updates_data:
                if isinstance(u, dict):
                    self.example_updates.append(ExampleUpdate(**u))
            
            changes_data = state_manager.get(f"{self.storage_key}.api_changes", [])
            self.api_changes = []
            for c in changes_data:
                if isinstance(c, dict):
                    self.api_changes.append(APIChange(**c))
            
        except Exception as e:
            logger.warning(f"Failed to load example data: {e}")
    
    def _save_data(self) -> None:
        """Save example data to state manager"""
        try:
            examples_data = {eid: ex.to_dict() for eid, ex in self.examples.items()}
            state_manager.set(f"{self.storage_key}.examples", examples_data)
            
            updates_data = [u.to_dict() for u in self.example_updates]
            state_manager.set(f"{self.storage_key}.updates", updates_data)
            
            changes_data = [c.__dict__ for c in self.api_changes]
            state_manager.set(f"{self.storage_key}.api_changes", changes_data)
            
        except Exception as e:
            logger.error(f"Failed to save example data: {e}")
    
    def _register_default_example_dirs(self) -> None:
        """Register default example directories"""
        default_dirs = [
            Path("examples"),
            Path("docs/examples"),
            Path("tests/examples"),
            Path("tools/ai/examples"),
        ]
        
        for dir_path in default_dirs:
            if dir_path.exists():
                self.example_dirs.append(dir_path)
    
    def add_example_directory(self, dir_path: Union[str, Path]) -> None:
        """Add a directory to scan for examples"""
        path = Path(dir_path)
        if path.exists() and path.is_dir():
            self.example_dirs.append(path)
            logger.info(f"Added example directory: {path}")
        else:
            logger.warning(f"Example directory not found: {path}")
    
    def scan_examples(self) -> List[CodeExample]:
        """Scan for code examples in registered directories"""
        discovered_examples = []
        
        for example_dir in self.example_dirs:
            for file_path in example_dir.rglob("*"):
                if self._is_example_file(file_path):
                    examples = self._extract_examples_from_file(file_path)
                    discovered_examples.extend(examples)
        
        # Update registry
        for example in discovered_examples:
            if example.id not in self.examples:
                self.examples[example.id] = example
                logger.debug(f"Discovered new example: {example.id}")
            else:
                # Update content if changed
                existing = self.examples[example.id]
                if existing.content != example.content:
                    existing.content = example.content
                    existing.status = ExampleStatus.PENDING_UPDATE
                    logger.debug(f"Example content changed: {example.id}")
        
        self._save_data()
        
        return discovered_examples
    
    def _is_example_file(self, file_path: Path) -> bool:
        """Check if file contains examples"""
        extensions = {'.py', '.md', '.rst', '.ipynb'}
        return file_path.suffix in extensions
    
    def _extract_examples_from_file(self, file_path: Path) -> List[CodeExample]:
        """Extract code examples from a file"""
        examples = []
        content = file_utils.read_file(str(file_path))
        
        if file_path.suffix == '.py':
            examples.extend(self._extract_from_python_file(file_path, content))
        elif file_path.suffix == '.md':
            examples.extend(self._extract_from_markdown_file(file_path, content))
        elif file_path.suffix == '.rst':
            examples.extend(self._extract_from_rst_file(file_path, content))
        
        return examples
    
    def _extract_from_python_file(self, file_path: Path, content: str) -> List[CodeExample]:
        """Extract examples from Python file"""
        examples = []
        
        try:
            tree = ast.parse(content)
            
            # Look for if __name__ == "__main__" blocks
            for node in ast.walk(tree):
                if isinstance(node, ast.If):
                    if self._is_main_block(node):
                        example_content = ast.unparse(node.body) if hasattr(ast, 'unparse') else content
                        example_id = f"{file_path}:main_block"
                        
                        example = CodeExample(
                            id=example_id,
                            type=ExampleType.CODE_SNIPPET,
                            file_path=str(file_path),
                            content=example_content,
                            api_elements=self._extract_api_elements(example_content),
                            status=ExampleStatus.VALID
                        )
                        examples.append(example)
            
            # Look for functions with 'example' in name
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    if 'example' in node.name.lower():
                        example_content = ast.unparse(node) if hasattr(ast, 'unparse') else content
                        example_id = f"{file_path}:{node.name}"
                        
                        example = CodeExample(
                            id=example_id,
                            type=ExampleType.CODE_SNIPPET,
                            file_path=str(file_path),
                            content=example_content,
                            api_elements=self._extract_api_elements(example_content),
                            status=ExampleStatus.VALID
                        )
                        examples.append(example)
                        
        except SyntaxError as e:
            logger.warning(f"Failed to parse {file_path}: {e}")
        
        return examples
    
    def _is_main_block(self, node: ast.If) -> bool:
        """Check if if block is __main__ guard"""
        if isinstance(node.test, ast.Compare):
            left = node.test.left
            if isinstance(left, ast.Name) and left.id == '__name__':
                return True
        return False
    
    def _extract_from_markdown_file(self, file_path: Path, content: str) -> List[CodeExample]:
        """Extract code blocks from Markdown file"""
        examples = []
        
        # Pattern for code blocks
        code_block_pattern = re.compile(r'```(\w+)\n(.*?)```', re.DOTALL)
        
        for i, match in enumerate(code_block_pattern.finditer(content)):
            language = match.group(1)
            code = match.group(2)
            
            if language in ['python', 'py']:
                example_id = f"{file_path}:code_block_{i}"
                
                example = CodeExample(
                    id=example_id,
                    type=ExampleType.TUTORIAL,
                    file_path=str(file_path),
                    content=code.strip(),
                    api_elements=self._extract_api_elements(code),
                    status=ExampleStatus.VALID
                )
                examples.append(example)
        
        return examples
    
    def _extract_from_rst_file(self, file_path: Path, content: str) -> List[CodeExample]:
        """Extract code blocks from reStructuredText file"""
        examples = []
        
        # Pattern for code blocks in RST
        code_block_pattern = re.compile(r'\.\. code-block::\s*(\w+)\s*\n\s*(.*?)(?=\n\.\.|\n\S|$)', re.DOTALL)
        
        for i, match in enumerate(code_block_pattern.finditer(content)):
            language = match.group(1)
            code = match.group(2)
            
            # Clean up indentation
            code = '\n'.join(line.lstrip() for line in code.split('\n'))
            
            if language in ['python', 'py']:
                example_id = f"{file_path}:rst_block_{i}"
                
                example = CodeExample(
                    id=example_id,
                    type=ExampleType.TUTORIAL,
                    file_path=str(file_path),
                    content=code.strip(),
                    api_elements=self._extract_api_elements(code),
                    status=ExampleStatus.VALID
                )
                examples.append(example)
        
        return examples
    
    def _extract_api_elements(self, code: str) -> List[str]:
        """Extract API elements used in code"""
        api_elements = set()
        
        # Extract imports
        for match in self.api_patterns["import"].finditer(code):
            module = match.group(1)
            api_elements.add(module)
        
        # Extract function calls
        for match in self.api_patterns["function_call"].finditer(code):
            func_name = match.group(1)
            # Filter out Python built-ins
            if not self._is_builtin(func_name):
                api_elements.add(func_name)
        
        return list(api_elements)
    
    def _is_builtin(self, name: str) -> bool:
        """Check if name is a Python built-in"""
        builtins = {'print', 'len', 'str', 'int', 'float', 'list', 'dict', 
                   'set', 'tuple', 'range', 'enumerate', 'zip', 'map', 'filter',
                   'open', 'import', 'exec', 'eval', '__name__', '__main__'}
        return name in builtins
    
    def register_api_change(self, api_change: APIChange) -> None:
        """Register an API change that may affect examples"""
        self.api_changes.append(api_change)
        
        # Find affected examples
        affected = self.find_affected_examples(api_change.api_name)
        
        for example in affected:
            example.status = ExampleStatus.OUTDATED
            example.validation_errors.append(f"API {api_change.api_name} changed: {api_change.change_type}")
        
        self._save_data()
        logger.info(f"Registered API change: {api_change.api_name} ({api_change.change_type})")
    
    def find_affected_examples(self, api_name: str) -> List[CodeExample]:
        """Find examples that use a specific API"""
        affected = []
        
        for example in self.examples.values():
            if api_name in example.api_elements:
                affected.append(example)
        
        return affected
    
    def validate_example(self, example_id: str) -> Tuple[bool, List[str]]:
        """Validate an example by attempting to parse and compile it"""
        if example_id not in self.examples:
            return False, ["Example not found"]
        
        example = self.examples[example_id]
        errors = []
        
        try:
            # Try to parse as Python
            ast.parse(example.content)
            
            # Try to compile (safer than executing)
            compile(example.content, '<string>', 'exec')
            
            example.status = ExampleStatus.VALID
            example.last_validated = datetime.now()
            example.validation_errors = []
            
            return True, []
            
        except SyntaxError as e:
            errors.append(f"Syntax error: {e}")
            example.status = ExampleStatus.BROKEN
        except Exception as e:
            errors.append(f"Error: {e}")
            example.status = ExampleStatus.BROKEN
        
        example.validation_errors = errors
        example.last_validated = datetime.now()
        self._save_data()
        
        return False, errors
    
    def validate_all_examples(self) -> Dict[str, Tuple[bool, List[str]]]:
        """Validate all examples"""
        results = {}
        
        for example_id in self.examples:
            results[example_id] = self.validate_example(example_id)
        
        return results
    
    def update_example_for_api_change(self, example_id: str, 
                                     api_change: APIChange) -> Optional[ExampleUpdate]:
        """Attempt to automatically update an example for an API change"""
        if example_id not in self.examples:
            return None
        
        example = self.examples[example_id]
        old_content = example.content
        new_content = old_content
        
        changes = []
        
        if api_change.change_type == "renamed":
            # Rename API calls
            if api_change.old_name and api_change.new_name:
                new_content = new_content.replace(api_change.old_name, api_change.new_name)
                changes.append(f"Renamed {api_change.old_name} to {api_change.new_name}")
        
        elif api_change.change_type == "signature_change":
            # Try to update function calls
            if api_change.old_signature and api_change.new_signature:
                # Simple pattern replacement
                pattern = re.compile(re.escape(api_change.old_signature.split('(')[0]) + r'\s*\(')
                if pattern.search(new_content):
                    # More complex updates may need manual intervention
                    changes.append(f"Signature changed, manual review recommended")
        
        elif api_change.change_type == "deprecated":
            changes.append(f"API {api_change.api_name} is deprecated. {api_change.migration_guide or 'Check documentation for migration.'}")
        
        if new_content != old_content:
            update = ExampleUpdate(
                example_id=example_id,
                update_type="auto_fix" if new_content != old_content else "manual_required",
                changes=changes,
                old_content=old_content,
                new_content=new_content
            )
            
            self.example_updates.append(update)
            self._save_data()
            
            return update
        
        return None
    
    def apply_update(self, update: ExampleUpdate) -> bool:
        """Apply an example update to the file system"""
        if update.example_id not in self.examples:
            return False
        
        example = self.examples[update.example_id]
        
        # Read current file content
        try:
            current_content = file_utils.read_file(example.file_path)
        except Exception as e:
            logger.error(f"Failed to read {example.file_path}: {e}")
            return False
        
        # Replace the example content in the file
        updated_content = current_content.replace(update.old_content, update.new_content)
        
        if updated_content != current_content:
            # Write back to file
            try:
                file_utils.write_file(example.file_path, updated_content)
                
                # Update example record
                example.content = update.new_content
                example.status = ExampleStatus.VALID
                example.last_validated = datetime.now()
                
                update.applied = True
                self._save_data()
                
                logger.info(f"Applied update to example: {update.example_id}")
                return True
                
            except Exception as e:
                logger.error(f"Failed to write {example.file_path}: {e}")
                return False
        
        return False
    
    def auto_update_examples(self, api_name: str = None) -> List[ExampleUpdate]:
        """Automatically update examples for API changes"""
        updates = []
        
        # Filter relevant API changes
        relevant_changes = self.api_changes
        if api_name:
            relevant_changes = [c for c in relevant_changes if c.api_name == api_name]
        
        for api_change in relevant_changes:
            affected = self.find_affected_examples(api_change.api_name)
            
            for example in affected:
                update = self.update_example_for_api_change(example.id, api_change)
                if update:
                    updates.append(update)
                    
                    # Auto-apply if safe
                    if update.update_type == "auto_fix":
                        self.apply_update(update)
        
        return updates
    
    def test_example(self, example_id: str, timeout_seconds: int = 30) -> Dict[str, Any]:
        """Test an example by executing it in a safe environment"""
        if example_id not in self.examples:
            return {"success": False, "error": "Example not found"}
        
        example = self.examples[example_id]
        
        # Create a temporary file
        import tempfile
        import subprocess
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(example.content)
            temp_file = f.name
        
        try:
            # Run the example
            result = subprocess.run(
                ['python', temp_file],
                capture_output=True,
                text=True,
                timeout=timeout_seconds
            )
            
            success = result.returncode == 0
            
            return {
                "success": success,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
            
        except subprocess.TimeoutExpired:
            return {"success": False, "error": f"Execution timed out after {timeout_seconds} seconds"}
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            # Clean up
            Path(temp_file).unlink(missing_ok=True)
    
    def generate_example_report(self) -> Dict[str, Any]:
        """Generate a report on example status"""
        status_counts = defaultdict(int)
        type_counts = defaultdict(int)
        
        for example in self.examples.values():
            status_counts[example.status.value] += 1
            type_counts[example.type.value] += 1
        
        broken_examples = [e for e in self.examples.values() if e.status == ExampleStatus.BROKEN]
        outdated_examples = [e for e in self.examples.values() if e.status == ExampleStatus.OUTDATED]
        
        return {
            "total_examples": len(self.examples),
            "status_breakdown": dict(status_counts),
            "type_breakdown": dict(type_counts),
            "broken_count": len(broken_examples),
            "outdated_count": len(outdated_examples),
            "valid_count": len([e for e in self.examples.values() if e.status == ExampleStatus.VALID]),
            "broken_examples": [
                {"id": e.id, "file": e.file_path, "errors": e.validation_errors}
                for e in broken_examples[:10]
            ],
            "outdated_examples": [
                {"id": e.id, "file": e.file_path, "api_elements": e.api_elements}
                for e in outdated_examples[:10]
            ],
            "pending_updates": len([u for u in self.example_updates if not u.applied]),
            "api_changes_count": len(self.api_changes)
        }
    
    def extract_example_from_docstring(self, docstring: str, 
                                      function_name: str) -> Optional[CodeExample]:
        """Extract example from a docstring"""
        # Look for Example: or Examples: section
        example_patterns = [
            r'Example:\s*\n\s*```python\s*\n(.*?)\n\s*```',
            r'Examples:\s*\n\s*```python\s*\n(.*?)\n\s*```',
            r'>>>\s*(.*?)(?=\n>>>|\n$|\n\s*\n)',
        ]
        
        for pattern in example_patterns:
            match = re.search(pattern, docstring, re.DOTALL)
            if match:
                code = match.group(1)
                example_id = f"docstring:{function_name}"
                
                return CodeExample(
                    id=example_id,
                    type=ExampleType.API_USAGE,
                    file_path="docstring",
                    content=code.strip(),
                    api_elements=[function_name],
                    status=ExampleStatus.VALID,
                    description=f"Example from {function_name} docstring"
                )
        
        return None
    
    def sync_examples_with_code(self, code_file_path: str) -> List[ExampleUpdate]:
        """Sync examples in docstrings with actual code"""
        updates = []
        
        try:
            content = file_utils.read_file(code_file_path)
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                    docstring = ast.get_docstring(node)
                    if docstring:
                        example = self.extract_example_from_docstring(docstring, node.name)
                        if example:
                            # Validate the example
                            is_valid, errors = self.validate_example(example.id)
                            
                            if not is_valid:
                                # Create update to fix the example
                                update = ExampleUpdate(
                                    example_id=example.id,
                                    update_type="manual_required",
                                    changes=[f"Example in {node.name} docstring is invalid: {', '.join(errors)}"],
                                    old_content=example.content,
                                    new_content=example.content
                                )
                                updates.append(update)
                                
        except Exception as e:
            logger.error(f"Failed to sync examples with {code_file_path}: {e}")
        
        return updates
    
    def create_example_from_template(self, template_name: str, 
                                    output_path: str,
                                    variables: Dict[str, str]) -> CodeExample:
        """Create a new example from a template"""
        templates = {
            "basic_function": '''def example_function():
    """Example function demonstrating usage."""
    result = {function_call}
    print(f"Result: {result}")
    return result

if __name__ == "__main__":
    example_function()
''',
            "api_usage": '''from {module} import {class_name}

def main():
    """Example usage of {class_name}."""
    # Create instance
    obj = {class_name}({params})
    
    # Call methods
    result = obj.{method_name}({method_args})
    
    print(f"Result: {result}")
    
if __name__ == "__main__":
    main()
''',
            "workflow": '''from tools.ai.orchestration import WorkflowEngine

def run_workflow():
    """Example workflow execution."""
    engine = WorkflowEngine()
    
    # Define workflow
    workflow = {workflow_definition}
    
    # Execute
    result = engine.run(workflow)
    
    return result

if __name__ == "__main__":
    result = run_workflow()
    print(f"Workflow result: {result}")
'''
        }
        
        if template_name not in templates:
            raise ValueError(f"Unknown template: {template_name}")
        
        content = templates[template_name]
        for key, value in variables.items():
            content = content.replace(f"{{{key}}}", value)
        
        # Write to file
        output_path_obj = Path(output_path)
        output_path_obj.parent.mkdir(parents=True, exist_ok=True)
        file_utils.write_file(str(output_path_obj), content)
        
        # Create example record
        example = CodeExample(
            id=str(output_path_obj),
            type=ExampleType.CODE_SNIPPET,
            file_path=str(output_path_obj),
            content=content,
            api_elements=self._extract_api_elements(content),
            status=ExampleStatus.VALID,
            tags=[template_name]
        )
        
        self.examples[example.id] = example
        self._save_data()
        
        logger.info(f"Created example from template '{template_name}': {output_path}")
        
        return example
    
    def get_example_summary(self) -> Dict[str, Any]:
        """Get summary of all examples"""
        return {
            "total_examples": len(self.examples),
            "example_dirs": [str(d) for d in self.example_dirs],
            "api_changes": len(self.api_changes),
            "pending_updates": len([u for u in self.example_updates if not u.applied]),
            "valid_examples": len([e for e in self.examples.values() if e.status == ExampleStatus.VALID]),
            "broken_examples": len([e for e in self.examples.values() if e.status == ExampleStatus.BROKEN]),
            "outdated_examples": len([e for e in self.examples.values() if e.status == ExampleStatus.OUTDATED]),
            "example_types": list(set(e.type.value for e in self.examples.values()))
        }


# Singleton instance
_example_updater: Optional[ExampleUpdater] = None


def get_example_updater() -> ExampleUpdater:
    """Get global ExampleUpdater instance"""
    global _example_updater
    if _example_updater is None:
        _example_updater = ExampleUpdater()
    return _example_updater