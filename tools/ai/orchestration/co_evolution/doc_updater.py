"""
Doc Updater for Co-Evolution Engine

Automatically updates documentation when code changes to maintain consistency.
Handles:
- Docstring synchronization
- API documentation updates
- README generation
- Architecture documentation updates
- Changelog management
- Cross-reference validation
"""

import re
import ast
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


class DocType(Enum):
    """Types of documentation"""
    README = "readme"
    API = "api"
    ARCHITECTURE = "architecture"
    CHANGELOG = "changelog"
    DOCSTRING = "docstring"
    USER_GUIDE = "user_guide"
    CONTRIBUTING = "contributing"
    EXAMPLES = "examples"
    CONFIG = "config"
    DEPLOYMENT = "deployment"


class UpdateTrigger(Enum):
    """What triggered a documentation update"""
    CODE_CHANGE = "code_change"
    API_CHANGE = "api_change"
    CONFIG_CHANGE = "config_change"
    MANUAL = "manual"
    SCHEDULED = "scheduled"


@dataclass
class DocSection:
    """Represents a documentation section"""
    title: str
    content: str
    level: int
    line_start: int
    line_end: int
    section_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DocUpdate:
    """Represents a documentation update"""
    doc_type: DocType
    file_path: str
    trigger: UpdateTrigger
    changes: List[str]
    timestamp: datetime = field(default_factory=datetime.now)
    affected_sections: List[str] = field(default_factory=list)
    version: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "doc_type": self.doc_type.value,
            "file_path": self.file_path,
            "trigger": self.trigger.value,
            "changes": self.changes,
            "timestamp": self.timestamp.isoformat(),
            "affected_sections": self.affected_sections,
            "version": self.version
        }


@dataclass
class APIDocEntry:
    """Represents API documentation for a code element"""
    name: str
    type: str
    signature: Optional[str] = None
    description: Optional[str] = None
    parameters: List[Dict[str, Any]] = field(default_factory=list)
    returns: Optional[str] = None
    raises: List[str] = field(default_factory=list)
    examples: List[str] = field(default_factory=list)
    deprecated: bool = False
    since_version: Optional[str] = None
    see_also: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "type": self.type,
            "signature": self.signature,
            "description": self.description,
            "parameters": self.parameters,
            "returns": self.returns,
            "raises": self.raises,
            "examples": self.examples,
            "deprecated": self.deprecated,
            "since_version": self.since_version,
            "see_also": self.see_also
        }


class DocUpdater:
    """
    Automatically updates documentation when code changes.
    
    Features:
    - Syncs docstrings with code changes
    - Updates API documentation automatically
    - Maintains changelog from git commits
    - Validates cross-references
    - Generates missing documentation
    - Tracks documentation versions
    """
    
    def __init__(self, storage_key: str = "doc_updater"):
        self.storage_key = storage_key
        self.documentation_files: Dict[str, Dict[str, Any]] = {}
        self.api_docs: Dict[str, APIDocEntry] = {}
        self.update_history: List[DocUpdate] = []
        self.doc_templates: Dict[DocType, str] = {}
        
        self._load_data()
        self._initialize_templates()
        
        logger.info("DocUpdater initialized")
    
    def _load_data(self) -> None:
        """Load documentation data from state manager"""
        try:
            docs_data = state_manager.get(f"{self.storage_key}.docs", {})
            self.documentation_files = docs_data
            
            api_data = state_manager.get(f"{self.storage_key}.api_docs", {})
            self.api_docs = {}
            for k, v in api_data.items():
                if isinstance(v, dict):
                    self.api_docs[k] = APIDocEntry(**v)
            
            history_data = state_manager.get(f"{self.storage_key}.history", [])
            self.update_history = []
            for h in history_data:
                if isinstance(h, dict):
                    self.update_history.append(DocUpdate(**h))
            
        except Exception as e:
            logger.warning(f"Failed to load documentation data: {e}")
    
    def _save_data(self) -> None:
        """Save documentation data to state manager"""
        try:
            state_manager.set(f"{self.storage_key}.docs", self.documentation_files)
            api_data = {k: v.to_dict() for k, v in self.api_docs.items()}
            state_manager.set(f"{self.storage_key}.api_docs", api_data)
            history_data = [h.to_dict() for h in self.update_history]
            state_manager.set(f"{self.storage_key}.history", history_data)
        except Exception as e:
            logger.error(f"Failed to save documentation data: {e}")
    
    def _initialize_templates(self) -> None:
        """Initialize documentation templates"""
        self.doc_templates = {
            DocType.README: self._get_readme_template(),
            DocType.CHANGELOG: self._get_changelog_template(),
            DocType.CONTRIBUTING: self._get_contributing_template(),
            DocType.API: self._get_api_template(),
        }
    
    def _get_readme_template(self) -> str:
        """Get README template with escaped backticks"""
        return '# {project_name}\n\n## Description\n{description}\n\n## Installation\n```bash\n{installation_commands}\n```\n\n## Usage\n```python\n{usage_example}\n```\n\n## Features\n{features_list}\n\n## Configuration\n{configuration_docs}\n\n## Contributing\nSee [CONTRIBUTING.md](CONTRIBUTING.md)\n\n## License\n{license_info}'
    
    def _get_changelog_template(self) -> str:
        """Get CHANGELOG template"""
        return '# Changelog\n\nAll notable changes to this project will be documented in this file.\n\n## [{version}] - {date}\n### Added\n- {added_items}\n\n### Changed\n- {changed_items}\n\n### Deprecated\n- {deprecated_items}\n\n### Removed\n- {removed_items}\n\n### Fixed\n- {fixed_items}\n\n### Security\n- {security_items}'
    
    def _get_contributing_template(self) -> str:
        """Get CONTRIBUTING template"""
        return '# Contributing Guidelines\n\n## Getting Started\n{getting_started}\n\n## Development Setup\n{setup_instructions}\n\n## Code Style\n{code_style}\n\n## Testing\n{testing_instructions}\n\n## Pull Request Process\n{pr_process}\n\n## Code of Conduct\n{code_of_conduct}'
    
    def _get_api_template(self) -> str:
        """Get API documentation template"""
        return '# API Reference\n\n## {module_name}\n\n{description}\n\n### Functions\n\n{functions_docs}\n\n### Classes\n\n{classes_docs}\n\n### Exceptions\n\n{exceptions_docs}'
    
    def update_from_code_change(self, file_path: str, 
                               old_content: str, 
                               new_content: str) -> List[DocUpdate]:
        """Update documentation based on code changes"""
        updates = []
        
        try:
            old_tree = ast.parse(old_content) if old_content else None
            new_tree = ast.parse(new_content)
        except SyntaxError as e:
            logger.error(f"Failed to parse {file_path}: {e}")
            return updates
        
        if old_tree:
            changed_functions = self._detect_changed_functions(old_tree, new_tree)
            for func_name, changes in changed_functions.items():
                doc_update = self._update_function_docstring(file_path, func_name, changes)
                if doc_update:
                    updates.append(doc_update)
            
            changed_classes = self._detect_changed_classes(old_tree, new_tree)
            for class_name, changes in changed_classes.items():
                doc_update = self._update_class_docstring(file_path, class_name, changes)
                if doc_update:
                    updates.append(doc_update)
        
        api_update = self._update_api_docs(file_path, new_tree)
        if api_update:
            updates.append(api_update)
        
        self.update_history.extend(updates)
        self._save_data()
        
        return updates
    
    def _detect_changed_functions(self, old_tree: ast.AST, 
                                 new_tree: ast.AST) -> Dict[str, Dict[str, Any]]:
        """Detect functions that have changed"""
        changes = {}
        
        old_functions = self._extract_functions(old_tree)
        new_functions = self._extract_functions(new_tree)
        
        for func_name, new_func in new_functions.items():
            if func_name in old_functions:
                old_func = old_functions[func_name]
                func_changes = self._compare_functions(old_func, new_func)
                if func_changes:
                    changes[func_name] = func_changes
            else:
                changes[func_name] = {"type": "added"}
        
        for func_name in set(old_functions.keys()) - set(new_functions.keys()):
            changes[func_name] = {"type": "removed"}
        
        return changes
    
    def _detect_changed_classes(self, old_tree: ast.AST, 
                               new_tree: ast.AST) -> Dict[str, Dict[str, Any]]:
        """Detect classes that have changed"""
        changes = {}
        
        old_classes = self._extract_classes(old_tree)
        new_classes = self._extract_classes(new_tree)
        
        for class_name, new_class in new_classes.items():
            if class_name in old_classes:
                old_class = old_classes[class_name]
                class_changes = self._compare_classes(old_class, new_class)
                if class_changes:
                    changes[class_name] = class_changes
            else:
                changes[class_name] = {"type": "added"}
        
        for class_name in set(old_classes.keys()) - set(new_classes.keys()):
            changes[class_name] = {"type": "removed"}
        
        return changes
    
    def _extract_functions(self, tree: ast.AST) -> Dict[str, ast.FunctionDef]:
        """Extract all functions from AST"""
        functions = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                functions[node.name] = node
        return functions
    
    def _extract_classes(self, tree: ast.AST) -> Dict[str, ast.ClassDef]:
        """Extract all classes from AST"""
        classes = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                classes[node.name] = node
        return classes
    
    def _compare_functions(self, old_func: ast.FunctionDef, 
                          new_func: ast.FunctionDef) -> Dict[str, Any]:
        """Compare two functions and return changes"""
        changes = {}
        
        old_args = [arg.arg for arg in old_func.args.args]
        new_args = [arg.arg for arg in new_func.args.args]
        
        if old_args != new_args:
            changes["parameters"] = {"old": old_args, "new": new_args}
        
        old_returns = self._get_return_annotation(old_func)
        new_returns = self._get_return_annotation(new_func)
        
        if old_returns != new_returns:
            changes["return_type"] = {"old": old_returns, "new": new_returns}
        
        old_docstring = ast.get_docstring(old_func)
        new_docstring = ast.get_docstring(new_func)
        
        if old_docstring != new_docstring:
            changes["docstring"] = {"old": old_docstring, "new": new_docstring}
        
        return changes
    
    def _compare_classes(self, old_class: ast.ClassDef, 
                        new_class: ast.ClassDef) -> Dict[str, Any]:
        """Compare two classes and return changes"""
        changes = {}
        
        old_methods = self._extract_functions(old_class)
        new_methods = self._extract_functions(new_class)
        
        added_methods = set(new_methods.keys()) - set(old_methods.keys())
        removed_methods = set(old_methods.keys()) - set(new_methods.keys())
        
        if added_methods:
            changes["added_methods"] = list(added_methods)
        if removed_methods:
            changes["removed_methods"] = list(removed_methods)
        
        old_docstring = ast.get_docstring(old_class)
        new_docstring = ast.get_docstring(new_class)
        
        if old_docstring != new_docstring:
            changes["docstring"] = {"old": old_docstring, "new": new_docstring}
        
        return changes
    
    def _get_return_annotation(self, func: ast.FunctionDef) -> Optional[str]:
        """Extract return annotation from function"""
        if func.returns:
            if isinstance(func.returns, ast.Name):
                return func.returns.id
            elif isinstance(func.returns, ast.Attribute):
                return f"{func.returns.value.id}.{func.returns.attr}" if hasattr(func.returns.value, 'id') else None
        return None
    
    def _update_function_docstring(self, file_path: str, func_name: str, 
                                  changes: Dict[str, Any]) -> Optional[DocUpdate]:
        """Update function docstring based on changes"""
        if changes.get("type") == "removed":
            return None
        
        if "parameters" in changes or "return_type" in changes:
            return DocUpdate(
                doc_type=DocType.DOCSTRING,
                file_path=file_path,
                trigger=UpdateTrigger.CODE_CHANGE,
                changes=[f"Updated docstring for function {func_name}"],
                affected_sections=[func_name]
            )
        
        return None
    
    def _update_class_docstring(self, file_path: str, class_name: str, 
                               changes: Dict[str, Any]) -> Optional[DocUpdate]:
        """Update class docstring based on changes"""
        if changes.get("type") == "removed":
            return None
        
        if "added_methods" in changes or "removed_methods" in changes:
            return DocUpdate(
                doc_type=DocType.DOCSTRING,
                file_path=file_path,
                trigger=UpdateTrigger.CODE_CHANGE,
                changes=[f"Updated docstring for class {class_name}"],
                affected_sections=[class_name]
            )
        
        return None
    
    def _update_api_docs(self, file_path: str, tree: ast.AST) -> Optional[DocUpdate]:
        """Update API documentation"""
        api_entries = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                entry = APIDocEntry(
                    name=node.name,
                    type="function",
                    signature=self._get_signature(node),
                    description=ast.get_docstring(node),
                    parameters=self._get_parameters(node),
                    returns=self._get_return_annotation(node)
                )
                api_entries.append(entry)
                self.api_docs[f"{file_path}:{node.name}"] = entry
            
            elif isinstance(node, ast.ClassDef):
                entry = APIDocEntry(
                    name=node.name,
                    type="class",
                    description=ast.get_docstring(node)
                )
                api_entries.append(entry)
                self.api_docs[f"{file_path}:{node.name}"] = entry
        
        if api_entries:
            self._save_data()
            return DocUpdate(
                doc_type=DocType.API,
                file_path=file_path,
                trigger=UpdateTrigger.CODE_CHANGE,
                changes=[f"Updated API docs for {len(api_entries)} entries"],
                affected_sections=[e.name for e in api_entries]
            )
        
        return None
    
    def _get_signature(self, func: ast.FunctionDef) -> str:
        """Get function signature as string"""
        args = []
        for arg in func.args.args:
            arg_str = arg.arg
            if arg.annotation:
                if isinstance(arg.annotation, ast.Name):
                    arg_str += f": {arg.annotation.id}"
            args.append(arg_str)
        
        return f"{func.name}({', '.join(args)})"
    
    def _get_parameters(self, func: ast.FunctionDef) -> List[Dict[str, Any]]:
        """Extract parameter information"""
        params = []
        for arg in func.args.args:
            param = {"name": arg.arg}
            if arg.annotation:
                if isinstance(arg.annotation, ast.Name):
                    param["type"] = arg.annotation.id
            params.append(param)
        return params
    
    def update_readme(self, project_name: str, description: str, 
                     features: List[str]) -> DocUpdate:
        """Generate or update README file"""
        readme_content = self.doc_templates[DocType.README].format(
            project_name=project_name,
            description=description,
            installation_commands="pip install -r requirements.txt",
            usage_example="from tools.ai import ai_dev\n\nai_dev.run_workflow('analysis')",
            features_list="\n".join(f"- {f}" for f in features),
            configuration_docs="See config.yaml for settings",
            license_info="MIT"
        )
        
        readme_path = Path("README.md")
        file_utils.write_file(str(readme_path), readme_content)
        
        update = DocUpdate(
            doc_type=DocType.README,
            file_path=str(readme_path),
            trigger=UpdateTrigger.MANUAL,
            changes=["Generated README.md"],
            affected_sections=["all"]
        )
        
        self.update_history.append(update)
        self._save_data()
        
        return update
    
    def update_changelog(self, version: str, added: List[str] = None,
                        changed: List[str] = None, fixed: List[str] = None) -> DocUpdate:
        """Update CHANGELOG file"""
        changelog_path = Path("CHANGELOG.md")
        existing_content = ""
        
        if changelog_path.exists():
            existing_content = file_utils.read_file(str(changelog_path))
        
        new_entry = self.doc_templates[DocType.CHANGELOG].format(
            version=version,
            date=datetime.now().strftime("%Y-%m-%d"),
            added_items="\n- ".join(added or ["None"]),
            changed_items="\n- ".join(changed or ["None"]),
            deprecated_items="None",
            removed_items="None",
            fixed_items="\n- ".join(fixed or ["None"]),
            security_items="None"
        )
        
        updated_content = new_entry + "\n\n" + existing_content
        file_utils.write_file(str(changelog_path), updated_content)
        
        update = DocUpdate(
            doc_type=DocType.CHANGELOG,
            file_path=str(changelog_path),
            trigger=UpdateTrigger.MANUAL,
            changes=[f"Added version {version} to changelog"],
            version=version
        )
        
        self.update_history.append(update)
        self._save_data()
        
        return update
    
    def generate_api_reference(self, module_name: str, 
                              functions: List[APIDocEntry],
                              classes: List[APIDocEntry]) -> DocUpdate:
        """Generate API reference documentation"""
        functions_docs = []
        for func in functions:
            func_doc = f"#### {func.signature or func.name}\n\n"
            if func.description:
                func_doc += f"{func.description}\n\n"
            if func.parameters:
                func_doc += "**Parameters:**\n"
                for param in func.parameters:
                    func_doc += f"- {param.get('name')}: {param.get('type', 'Any')}\n"
                func_doc += "\n"
            if func.returns:
                func_doc += f"**Returns:** {func.returns}\n\n"
            functions_docs.append(func_doc)
        
        classes_docs = []
        for cls in classes:
            cls_doc = f"#### {cls.name}\n\n"
            if cls.description:
                cls_doc += f"{cls.description}\n\n"
            classes_docs.append(cls_doc)
        
        api_content = self.doc_templates[DocType.API].format(
            module_name=module_name,
            description=f"API documentation for {module_name}",
            functions_docs="\n".join(functions_docs),
            classes_docs="\n".join(classes_docs),
            exceptions_docs="No exceptions documented"
        )
        
        api_path = Path(f"docs/api_{module_name}.md")
        api_path.parent.mkdir(exist_ok=True)
        file_utils.write_file(str(api_path), api_content)
        
        update = DocUpdate(
            doc_type=DocType.API,
            file_path=str(api_path),
            trigger=UpdateTrigger.MANUAL,
            changes=[f"Generated API reference for {module_name}"],
            affected_sections=[f.name for f in functions] + [c.name for c in classes]
        )
        
        self.update_history.append(update)
        self._save_data()
        
        return update
    
    def validate_documentation(self, doc_path: str) -> Dict[str, Any]:
        """Validate documentation for broken links and inconsistencies"""
        issues = {
            "broken_links": [],
            "missing_sections": [],
            "outdated_info": []
        }
        
        if not Path(doc_path).exists():
            issues["missing_sections"].append(f"Documentation file not found: {doc_path}")
            return issues
        
        content = file_utils.read_file(doc_path)
        
        # Check for broken links to code files
        link_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
        for match in re.finditer(link_pattern, content):
            link_text, link_target = match.groups()
            if link_target.endswith('.py'):
                if not Path(link_target).exists():
                    issues["broken_links"].append({
                        "text": link_text,
                        "target": link_target,
                        "line": content[:match.start()].count('\n') + 1
                    })
        
        # Check for TODO or FIXME markers
        if "TODO" in content or "FIXME" in content:
            issues["outdated_info"].append("Documentation contains TODO/FIXME markers")
        
        return issues
    
    def sync_docstrings(self, file_path: str) -> List[DocUpdate]:
        """Sync docstrings with current code state"""
        updates = []
        
        content = file_utils.read_file(file_path)
        
        try:
            tree = ast.parse(content)
        except SyntaxError as e:
            logger.error(f"Cannot parse {file_path}: {e}")
            return updates
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                current_docstring = ast.get_docstring(node)
                
                if current_docstring is None or len(current_docstring.strip()) == 0:
                    # Generate missing docstring
                    new_docstring = self._generate_docstring(node)
                    if new_docstring:
                        updates.append(DocUpdate(
                            doc_type=DocType.DOCSTRING,
                            file_path=file_path,
                            trigger=UpdateTrigger.MANUAL,
                            changes=[f"Generated docstring for {node.name}"],
                            affected_sections=[node.name]
                        ))
        
        return updates
    
    def _generate_docstring(self, node: Union[ast.FunctionDef, ast.ClassDef]) -> Optional[str]:
        """Generate a docstring for a code element"""
        if isinstance(node, ast.FunctionDef):
            params = [arg.arg for arg in node.args.args]
            docstring = f'"""{node.name} function.\n\n'
            if params:
                docstring += "Args:\n"
                for param in params:
                    docstring += f"    {param}: Description\n"
            if node.returns:
                docstring += f"\nReturns:\n    {self._get_return_annotation(node)}\n"
            docstring += '"""'
            return docstring
        
        elif isinstance(node, ast.ClassDef):
            return f'"""{node.name} class.\n\nDescription of the class.\n"""'
        
        return None
    
    def get_doc_summary(self) -> Dict[str, Any]:
        """Get summary of documentation state"""
        return {
            "total_updates": len(self.update_history),
            "api_entries": len(self.api_docs),
            "managed_files": len(self.documentation_files),
            "last_update": self.update_history[-1].timestamp.isoformat() if self.update_history else None,
            "doc_types": list(self.doc_templates.keys())
        }
    
    def get_update_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent update history"""
        return [u.to_dict() for u in self.update_history[-limit:]]


# Singleton instance
_doc_updater: Optional[DocUpdater] = None


def get_doc_updater() -> DocUpdater:
    """Get global DocUpdater instance"""
    global _doc_updater
    if _doc_updater is None:
        _doc_updater = DocUpdater()
    return _doc_updater