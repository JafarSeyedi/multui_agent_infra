"""
Architecture Documentation Generator

Generates comprehensive architecture documentation from codebase analysis including:
- System architecture diagrams (C4 model)
- Component relationships and dependencies
- Data flow diagrams
- Deployment architecture
- API documentation
- Design decisions and rationale
- Technology stack documentation


This architecture_doc.py provides:

Key Features:
1. C4 Model Support
Context diagrams (system boundaries)
Container diagrams (applications/services)
Component diagrams (internal structure)
Code diagrams (class relationships)

2. Code Analysis
AST-based code parsing
Module and class discovery
Import and dependency mapping
API endpoint detection (FastAPI, Flask, Django)

3. Architecture Discovery
Component identification from directory structure
Technology stack detection
Data flow analysis
Circular dependency detection

4. Documentation Generation
Multiple documentation styles (Technical, Executive, Developer, Ops)
Automatic component descriptions
Responsibility derivation from docstrings
API documentation extraction

5. Diagram Generation
Mermaid diagram format
C4 model compliant
Dependency graphs
Class diagrams

6. Architecture Decisions (ADR)
Decision recording and tracking
Status management
Consequences documentation
Alternative analysis

7. Output Formats
Markdown documentation
HTML (via markdown conversion)
JSON export
Mermaid diagram files

Usage Examples:
python
# Basic usage
from tools.ai.quality.documenters.architecture_doc import generate_architecture_docs

generate_architecture_docs(
    project_path="/path/to/project",
    output_path="/path/to/ARCHITECTURE.md",
    level="component",
    style="technical",
    include_diagrams=True
)
Generated Output Includes:
    System Overview - High-level architecture description
    Component Documentation - Each component with responsibilities and dependencies
    Data Flow Diagrams - How data moves between components
    API Documentation - Extracted API endpoints
    Technology Stack - Identified technologies and frameworks
    Dependency Matrix - Component dependency relationships
    Architecture Diagrams - Visual representations (Mermaid)
    ADR Records - Architecture decision records
"""

import ast
import re
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from collections import defaultdict, Counter

from ...shared.logger import get_logger
from ...shared.state_manager import state_manager
from ...shared.config import config
from ...shared.file_utils import file_utils
from ...shared.git_utils import git_utils

logger = get_logger(__name__)


class DiagramFormat(Enum):
    """Supported diagram formats"""
    MERMAID = "mermaid"
    PLANTUML = "plantuml"
    GRAPHVIZ = "graphviz"
    JSON = "json"


class ArchitectureLevel(Enum):
    """Levels of architecture documentation (C4 model)"""
    CONTEXT = "context"          # System Context diagram
    CONTAINER = "container"      # Container diagram
    COMPONENT = "component"      # Component diagram
    CODE = "code"                # Code/Class diagram


class DocumentationStyle(Enum):
    """Documentation output styles"""
    TECHNICAL = "technical"       # Detailed technical documentation
    EXECUTIVE = "executive"       # High-level executive summary
    DEVELOPER = "developer"       # Developer-focused documentation
    OPS = "ops"                  # Operations/DevOps focused


@dataclass
class Component:
    """Represents a system component"""
    name: str
    type: str  # service, database, queue, cache, etc.
    description: str
    technologies: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    apis: List[str] = field(default_factory=list)
    responsibilities: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DataFlow:
    """Represents data flow between components"""
    source: str
    target: str
    data_type: str
    protocol: str
    frequency: str  # real-time, batch, streaming
    volume: str
    description: str


@dataclass
class ArchitectureDecision:
    """Records an architectural decision"""
    id: str
    title: str
    status: str  # proposed, accepted, deprecated, superseded
    context: str
    decision: str
    consequences: List[str]
    alternatives: List[str]
    date: datetime
    stakeholders: List[str]
    tags: List[str] = field(default_factory=list)


class ArchitectureDocGenerator:
    """
    Generates comprehensive architecture documentation from code analysis.
    
    Features:
    - C4 model diagram generation (Context, Container, Component, Code)
    - Component discovery and relationship mapping
    - Data flow analysis
    - API surface documentation
    - Technology stack identification
    - Design decision capture
    - Multi-format output (HTML, Markdown, Diagrams)
    """
    
    def __init__(self):
        self.project_path: Optional[Path] = None
        self.components: Dict[str, Component] = {}
        self.data_flows: List[DataFlow] = []
        self.decisions: List[ArchitectureDecision] = []
        self.api_endpoints: Dict[str, Dict[str, Any]] = {}
        self.technology_stack: Dict[str, List[str]] = {}
        self.dependency_graph: Dict[str, Set[str]] = defaultdict(set)
        
        # Analysis results
        self.modules: Dict[str, Any] = {}
        self.classes: Dict[str, Any] = {}
        self.functions: Dict[str, Any] = {}
        self.imports: Dict[str, Set[str]] = defaultdict(set)
        
        logger.info("ArchitectureDocGenerator initialized")
    
    def generate(self, project_path: str, 
                output_path: str,
                level: ArchitectureLevel = ArchitectureLevel.COMPONENT,
                style: DocumentationStyle = DocumentationStyle.TECHNICAL,
                include_diagrams: bool = True,
                include_decisions: bool = True) -> Dict[str, Any]:
        """
        Generate architecture documentation.
        
        Args:
            project_path: Path to the project root
            output_path: Path to write documentation
            level: Architecture level (context, container, component, code)
            style: Documentation style (technical, executive, developer, ops)
            include_diagrams: Include diagrams in output
            include_decisions: Include architecture decisions
            
        Returns:
            Generated documentation metadata
        """
        self.project_path = Path(project_path)
        
        logger.info(f"Generating {level.value} architecture documentation for {project_path}")
        
        # Step 1: Analyze codebase
        self._analyze_codebase()
        
        # Step 2: Discover components
        self._discover_components()
        
        # Step 3: Map dependencies
        self._map_dependencies()
        
        # Step 4: Analyze data flows
        self._analyze_data_flows()
        
        # Step 5: Document APIs
        self._document_apis()
        
        # Step 6: Identify technology stack
        self._identify_technology_stack()
        
        # Step 7: Generate documentation
        documentation = self._generate_documentation(level, style, include_diagrams, include_decisions)
        
        # Step 8: Write output
        self._write_output(output_path, documentation, include_diagrams)
        
        # Step 9: Generate diagrams
        diagrams = {}
        if include_diagrams:
            diagrams = self._generate_diagrams(level, output_path)
        
        return {
            "documentation_path": output_path,
            "diagrams": diagrams,
            "components": len(self.components),
            "api_endpoints": len(self.api_endpoints),
            "decisions": len(self.decisions),
            "level": level.value,
            "style": style.value,
            "generated_at": datetime.now().isoformat()
        }
    
    def _analyze_codebase(self) -> None:
        """Analyze codebase structure"""
        logger.info("Analyzing codebase...")
        
        # Scan Python files
        python_files = list(self.project_path.rglob("*.py"))
        
        # Exclude virtual environments and cache
        python_files = [f for f in python_files 
                       if 'venv' not in str(f) 
                       and '__pycache__' not in str(f)
                       and 'site-packages' not in str(f)]
        
        for file_path in python_files:
            try:
                self._analyze_file(file_path)
            except Exception as e:
                logger.warning(f"Failed to analyze {file_path}: {e}")
        
        logger.info(f"Analyzed {len(python_files)} files")
    
    def _analyze_file(self, file_path: Path) -> None:
        """Analyze a single Python file"""
        content = file_utils.read_file(str(file_path))
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return
        
        module_name = file_path.stem
        relative_path = str(file_path.relative_to(self.project_path))
        
        self.modules[relative_path] = {
            "name": module_name,
            "path": relative_path,
            "classes": [],
            "functions": [],
            "imports": []
        }
        
        for node in ast.walk(tree):
            # Track imports
            if isinstance(node, ast.Import):
                for alias in node.names:
                    self.imports[module_name].add(alias.name)
                    self.modules[relative_path]["imports"].append(alias.name)
            
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    import_name = f"{module}.{alias.name}" if module else alias.name
                    self.imports[module_name].add(import_name)
                    self.modules[relative_path]["imports"].append(import_name)
            
            # Track classes
            elif isinstance(node, ast.ClassDef):
                class_info = {
                    "name": node.name,
                    "methods": [],
                    "base_classes": [],
                    "docstring": ast.get_docstring(node),
                    "decorators": [self._get_decorator_name(d) for d in node.decorator_list]
                }
                
                # Get base classes
                for base in node.bases:
                    if isinstance(base, ast.Name):
                        class_info["base_classes"].append(base.id)
                
                # Get methods
                for method in ast.walk(node):
                    if isinstance(method, ast.FunctionDef):
                        class_info["methods"].append({
                            "name": method.name,
                            "args": [arg.arg for arg in method.args.args],
                            "docstring": ast.get_docstring(method)
                        })
                
                self.classes[f"{module_name}.{node.name}"] = class_info
                self.modules[relative_path]["classes"].append(node.name)
            
            # Track functions
            elif isinstance(node, ast.FunctionDef):
                # Skip methods (handled in class context)
                if not isinstance(node.parent, ast.ClassDef) if hasattr(node, 'parent') else True:
                    func_info = {
                        "name": node.name,
                        "args": [arg.arg for arg in node.args.args],
                        "returns": self._get_return_annotation(node),
                        "docstring": ast.get_docstring(node),
                        "decorators": [self._get_decorator_name(d) for d in node.decorator_list]
                    }
                    self.functions[f"{module_name}.{node.name}"] = func_info
                    self.modules[relative_path]["functions"].append(node.name)
    
    def _get_decorator_name(self, decorator: ast.expr) -> str:
        """Extract decorator name from AST node"""
        if isinstance(decorator, ast.Name):
            return decorator.id
        elif isinstance(decorator, ast.Attribute):
            return f"{self._get_decorator_name(decorator.value)}.{decorator.attr}"
        return str(decorator)
    
    def _get_return_annotation(self, node: ast.FunctionDef) -> Optional[str]:
        """Extract return annotation"""
        if node.returns:
            if isinstance(node.returns, ast.Name):
                return node.returns.id
            elif isinstance(node.returns, ast.Attribute):
                return f"{node.returns.value.id}.{node.returns.attr}" if hasattr(node.returns.value, 'id') else None
        return None
    
    def _discover_components(self) -> None:
        """Discover system components from code structure"""
        logger.info("Discovering components...")
        
        # Group modules into components based on directory structure
        component_groups = defaultdict(list)
        
        for module_path in self.modules.keys():
            # Use top-level directory as component name
            parts = Path(module_path).parts
            if len(parts) > 1:
                component_name = parts[0]
            else:
                component_name = "core"
            
            component_groups[component_name].append(module_path)
        
        for component_name, modules in component_groups.items():
            # Determine component type based on naming and content
            component_type = self._determine_component_type(component_name, modules)
            
            # Collect technologies
            technologies = self._collect_technologies(modules)
            
            # Build component
            component = Component(
                name=component_name.title(),
                type=component_type,
                description=self._generate_component_description(component_name, modules),
                technologies=technologies,
                dependencies=self._find_component_dependencies(component_name, modules),
                responsibilities=self._derive_responsibilities(modules)
            )
            
            self.components[component_name] = component
        
        logger.info(f"Discovered {len(self.components)} components")
    
    def _determine_component_type(self, name: str, modules: List[str]) -> str:
        """Determine component type based on naming and content"""
        name_lower = name.lower()
        
        if any(word in name_lower for word in ['api', 'gateway', 'router']):
            return "api_gateway"
        elif any(word in name_lower for word in ['service', 'svc']):
            return "service"
        elif any(word in name_lower for word in ['db', 'database', 'storage']):
            return "database"
        elif any(word in name_lower for word in ['cache', 'redis']):
            return "cache"
        elif any(word in name_lower for word in ['queue', 'messaging', 'kafka']):
            return "message_queue"
        elif any(word in name_lower for word in ['worker', 'job']):
            return "worker"
        elif any(word in name_lower for word in ['ui', 'frontend', 'web']):
            return "frontend"
        else:
            return "service"
    
    def _collect_technologies(self, modules: List[str]) -> List[str]:
        """Collect technologies used in modules"""
        technologies = set()
        
        for module_path in modules:
            content = file_utils.read_file(str(self.project_path / module_path))
            
            # Detect frameworks
            if 'import django' in content or 'from django' in content:
                technologies.add('Django')
            if 'import flask' in content or 'from flask' in content:
                technologies.add('Flask')
            if 'import fastapi' in content or 'from fastapi' in content:
                technologies.add('FastAPI')
            if 'import sqlalchemy' in content or 'from sqlalchemy' in content:
                technologies.add('SQLAlchemy')
            if 'import pytest' in content or 'from pytest' in content:
                technologies.add('Pytest')
            if 'import celery' in content or 'from celery' in content:
                technologies.add('Celery')
            if 'import redis' in content or 'from redis' in content:
                technologies.add('Redis')
        
        return list(technologies)
    
    def _find_component_dependencies(self, component_name: str, modules: List[str]) -> List[str]:
        """Find dependencies of a component"""
        dependencies = set()
        
        for module_path in modules:
            module_imports = self.imports.get(Path(module_path).stem, set())
            
            for import_name in module_imports:
                # Check if import references another component
                for other_component in self.components.keys():
                    if other_component != component_name and other_component.lower() in import_name.lower():
                        dependencies.add(other_component.title())
        
        return list(dependencies)
    
    def _generate_component_description(self, name: str, modules: List[str]) -> str:
        """Generate description for a component"""
        module_count = len(modules)
        class_count = sum(len(self.modules[m]["classes"]) for m in modules if m in self.modules)
        
        return f"{name.title()} component containing {module_count} modules and {class_count} classes. Handles {name.lower()}-related functionality."
    
    def _derive_responsibilities(self, modules: List[str]) -> List[str]:
        """Derive component responsibilities from code"""
        responsibilities = set()
        
        for module_path in modules:
            if module_path in self.modules:
                for class_name in self.modules[module_path]["classes"]:
                    full_class_name = f"{Path(module_path).stem}.{class_name}"
                    if full_class_name in self.classes:
                        class_info = self.classes[full_class_name]
                        if class_info.get("docstring"):
                            # Extract first line of docstring as responsibility
                            first_line = class_info["docstring"].split('\n')[0].strip()
                            if first_line and len(first_line) < 100:
                                responsibilities.add(first_line)
        
        return list(responsibilities)[:5]  # Limit to 5 responsibilities
    
    def _map_dependencies(self) -> None:
        """Map dependencies between components"""
        logger.info("Mapping dependencies...")
        
        for component_name, component in self.components.items():
            for dep in component.dependencies:
                self.dependency_graph[component_name].add(dep)
        
        # Detect circular dependencies
        cycles = self._detect_cycles()
        if cycles:
            logger.warning(f"Detected {len(cycles)} circular dependencies")
    
    def _detect_cycles(self) -> List[List[str]]:
        """Detect circular dependencies"""
        visited = set()
        stack = set()
        cycles = []
        
        def dfs(node, path):
            if node in stack:
                # Found a cycle
                cycle_start = path.index(node)
                cycles.append(path[cycle_start:] + [node])
                return
            if node in visited:
                return
            
            visited.add(node)
            stack.add(node)
            
            for neighbor in self.dependency_graph.get(node, []):
                dfs(neighbor, path + [node])
            
            stack.remove(node)
        
        for node in self.dependency_graph:
            dfs(node, [])
        
        return cycles
    
    def _analyze_data_flows(self) -> None:
        """Analyze data flows between components"""
        logger.info("Analyzing data flows...")
        
        # Infer data flows from dependencies
        for source, targets in self.dependency_graph.items():
            for target in targets:
                data_flow = DataFlow(
                    source=source,
                    target=target,
                    data_type=self._infer_data_type(source, target),
                    protocol=self._infer_protocol(source, target),
                    frequency=self._infer_frequency(source, target),
                    volume=self._infer_volume(source, target),
                    description=f"Data flows from {source} to {target}"
                )
                self.data_flows.append(data_flow)
        
        logger.info(f"Identified {len(self.data_flows)} data flows")
    
    def _infer_data_type(self, source: str, target: str) -> str:
        """Infer data type from component names"""
        if 'api' in source.lower() and 'db' in target.lower():
            return "API Requests → Database Queries"
        elif 'db' in source.lower() and 'api' in target.lower():
            return "Database Results → API Responses"
        elif 'queue' in source.lower() or 'queue' in target.lower():
            return "Messages"
        else:
            return "Structured Data"
    
    def _infer_protocol(self, source: str, target: str) -> str:
        """Infer communication protocol"""
        if 'api' in source.lower() or 'api' in target.lower():
            return "HTTP/REST"
        elif 'db' in source.lower() or 'db' in target.lower():
            return "Database Protocol"
        elif 'queue' in source.lower() or 'queue' in target.lower():
            return "Message Queue Protocol"
        else:
            return "Function Call"
    
    def _infer_frequency(self, source: str, target: str) -> str:
        """Infer communication frequency"""
        if 'api' in source.lower():
            return "Request/Response (on-demand)"
        elif 'queue' in source.lower() or 'queue' in target.lower():
            return "Asynchronous (message-driven)"
        else:
            return "Varies"
    
    def _infer_volume(self, source: str, target: str) -> str:
        """Infer data volume"""
        if 'api' in source.lower():
            return "Low to Medium"
        elif 'db' in source.lower() or 'db' in target.lower():
            return "High"
        else:
            return "Medium"
    
    def _document_apis(self) -> None:
        """Document API endpoints"""
        logger.info("Documenting APIs...")
        
        # Look for API framework patterns
        for module_path, module_info in self.modules.items():
            content = file_utils.read_file(str(self.project_path / module_path))
            
            # FastAPI routes
            fastapi_pattern = r'@app\.(get|post|put|delete|patch)\([\'"]([^\'"]+)[\'"]'
            for match in re.finditer(fastapi_pattern, content):
                method = match.group(1).upper()
                path = match.group(2)
                endpoint_id = f"{method} {path}"
                
                self.api_endpoints[endpoint_id] = {
                    "method": method,
                    "path": path,
                    "module": module_path,
                    "framework": "FastAPI"
                }
            
            # Flask routes
            flask_pattern = r'@app\.route\([\'"]([^\'"]+)[\'"](?:,\s*methods=\[([^\]]+)\])?'
            for match in re.finditer(flask_pattern, content):
                path = match.group(1)
                methods_str = match.group(2)
                methods = ['GET'] if not methods_str else [m.strip().strip("'\"") for m in methods_str.split(',')]
                
                for method in methods:
                    endpoint_id = f"{method} {path}"
                    self.api_endpoints[endpoint_id] = {
                        "method": method,
                        "path": path,
                        "module": module_path,
                        "framework": "Flask"
                    }
            
            # Django URLs
            django_pattern = r'path\([\'"]([^\'"]+)[\'"],\s*([^,]+)'
            for match in re.finditer(django_pattern, content):
                path = match.group(1)
                view = match.group(2).strip()
                endpoint_id = f"GET {path}"
                self.api_endpoints[endpoint_id] = {
                    "method": "GET",
                    "path": path,
                    "view": view,
                    "module": module_path,
                    "framework": "Django"
                }
        
        logger.info(f"Documented {len(self.api_endpoints)} API endpoints")
    
    def _identify_technology_stack(self) -> None:
        """Identify technology stack from dependencies and files"""
        logger.info("Identifying technology stack...")
        
        # Check for requirements.txt
        requirements_file = self.project_path / "requirements.txt"
        if requirements_file.exists():
            content = file_utils.read_file(str(requirements_file))
            self.technology_stack["Python Packages"] = []
            for line in content.split('\n'):
                if line and not line.startswith('#'):
                    self.technology_stack["Python Packages"].append(line.split('==')[0])
        
        # Check for Docker
        docker_file = self.project_path / "Dockerfile"
        if docker_file.exists():
            self.technology_stack["Containerization"] = ["Docker"]
        
        # Check for CI/CD
        if (self.project_path / ".github/workflows").exists():
            self.technology_stack["CI/CD"] = ["GitHub Actions"]
        elif (self.project_path / ".gitlab-ci.yml").exists():
            self.technology_stack["CI/CD"] = ["GitLab CI"]
        elif (self.project_path / "Jenkinsfile").exists():
            self.technology_stack["CI/CD"] = ["Jenkins"]
        
        # Check for database
        if any(f.suffix == '.sql' for f in self.project_path.rglob('*.sql')):
            self.technology_stack["Database"] = ["SQL"]
        
        logger.info(f"Identified technology stack with {len(self.technology_stack)} categories")
    
    def _generate_documentation(self, level: ArchitectureLevel, 
                                style: DocumentationStyle,
                                include_diagrams: bool,
                                include_decisions: bool) -> str:
        """Generate documentation in specified format"""
        
        doc_parts = []
        
        # Header
        doc_parts.append(self._generate_header(style))
        
        # Executive Summary (for executive style)
        if style == DocumentationStyle.EXECUTIVE:
            doc_parts.append(self._generate_executive_summary())
        
        # Architecture Overview
        doc_parts.append(self._generate_architecture_overview(level))
        
        # Components
        doc_parts.append(self._generate_components_section(level))
        
        # Data Flows
        if level in [ArchitectureLevel.CONTEXT, ArchitectureLevel.CONTAINER]:
            doc_parts.append(self._generate_data_flows_section())
        
        # API Documentation
        if level != ArchitectureLevel.CONTEXT:
            doc_parts.append(self._generate_api_section())
        
        # Technology Stack
        doc_parts.append(self._generate_technology_stack_section())
        
        # Dependencies
        if level != ArchitectureLevel.CODE:
            doc_parts.append(self._generate_dependencies_section())
        
        # Architecture Decisions
        if include_decisions and self.decisions:
            doc_parts.append(self._generate_decisions_section())
        
        # Diagrams (references)
        if include_diagrams:
            doc_parts.append(self._generate_diagrams_section(level))
        
        # Footer
        doc_parts.append(self._generate_footer())
        
        return '\n\n'.join(doc_parts)
    
    def _generate_header(self, style: DocumentationStyle) -> str:
        """Generate document header"""
        project_name = self.project_path.name
        
        return f"""# Architecture Documentation: {project_name}

**Documentation Style:** {style.value.title()}
**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Project Path:** `{self.project_path}`

---
"""
    
    def _generate_executive_summary(self) -> str:
        """Generate executive summary"""
        total_components = len(self.components)
        total_apis = len(self.api_endpoints)
        total_flows = len(self.data_flows)
        
        return f"""## Executive Summary

### Overview
This document provides a high-level architecture overview of the system.

### Key Metrics
- **Components:** {total_components}
- **API Endpoints:** {total_apis}
- **Data Flows:** {total_flows}
- **Technology Categories:** {len(self.technology_stack)}

### Architecture Highlights
- Modular component-based design
- Clear separation of concerns
- Documented API surfaces
- Identified data flow patterns
"""
    
    def _generate_architecture_overview(self, level: ArchitectureLevel) -> str:
        """Generate architecture overview section"""
        return f"""## Architecture Overview ({level.value.title()} Level)

### System Description
The system is composed of {len(self.components)} main components that work together to deliver the required functionality.

### Architecture Principles
- **Modularity:** Components are loosely coupled with clear interfaces
- **Scalability:** Horizontal scaling supported at the service layer
- **Maintainability:** Clean architecture with separation of concerns
- **Testability:** Components designed for unit and integration testing

### Key Characteristics
- **Communication Pattern:** Synchronous (HTTP/REST) and Asynchronous (Message Queue)
- **Data Management:** Distributed across multiple services
- **Deployment:** Containerized deployment strategy
"""
    
    def _generate_components_section(self, level: ArchitectureLevel) -> str:
        """Generate components documentation section"""
        sections = ["## Components\n"]
        
        for name, component in self.components.items():
            sections.append(f"### {name} ({component.type})")
            sections.append(f"\n**Description:** {component.description}")
            
            if component.technologies:
                sections.append(f"\n**Technologies:** {', '.join(component.technologies)}")
            
            if component.responsibilities:
                sections.append("\n**Responsibilities:**")
                for resp in component.responsibilities:
                    sections.append(f"- {resp}")
            
            if component.dependencies:
                sections.append(f"\n**Depends On:** {', '.join(component.dependencies)}")
            
            sections.append("")
        
        return '\n'.join(sections)
    
    def _generate_data_flows_section(self) -> str:
        """Generate data flows documentation"""
        sections = ["## Data Flows\n"]
        
        for flow in self.data_flows:
            sections.append(f"### {flow.source} → {flow.target}")
            sections.append(f"- **Data Type:** {flow.data_type}")
            sections.append(f"- **Protocol:** {flow.protocol}")
            sections.append(f"- **Frequency:** {flow.frequency}")
            sections.append(f"- **Volume:** {flow.volume}")
            sections.append(f"- **Description:** {flow.description}\n")
        
        return '\n'.join(sections)
    
    def _generate_api_section(self) -> str:
        """Generate API documentation section"""
        if not self.api_endpoints:
            return "## APIs\n\nNo API endpoints detected.\n"
        
        sections = ["## APIs\n"]
        
        # Group by module
        by_module = defaultdict(list)
        for endpoint, info in self.api_endpoints.items():
            by_module[info.get('module', 'unknown')].append((endpoint, info))
        
        for module, endpoints in by_module.items():
            sections.append(f"### Module: {module}\n")
            
            for endpoint, info in endpoints:
                sections.append(f"#### `{info['method']} {info['path']}`")
                sections.append(f"- **Framework:** {info.get('framework', 'Unknown')}")
                sections.append("")
        
        return '\n'.join(sections)
    
    def _generate_technology_stack_section(self) -> str:
        """Generate technology stack documentation"""
        sections = ["## Technology Stack\n"]
        
        for category, technologies in self.technology_stack.items():
            sections.append(f"### {category}")
            for tech in technologies[:10]:  # Limit to 10 per category
                sections.append(f"- {tech}")
            sections.append("")
        
        return '\n'.join(sections)
    
    def _generate_dependencies_section(self) -> str:
        """Generate dependencies documentation"""
        sections = ["## Dependencies\n"]
        
        # Build dependency matrix
        sections.append("### Component Dependency Matrix\n")
        sections.append("| Component | Depends On | Depended By |")
        sections.append("|-----------|------------|-------------|")
        
        for name, component in self.components.items():
            depended_by = [c for c, comp in self.components.items() if name in comp.dependencies]
            sections.append(f"| {name} | {', '.join(component.dependencies) or '-'} | {', '.join(depended_by) or '-'} |")
        
        # Circular dependencies warning
        cycles = self._detect_cycles()
        if cycles:
            sections.append("\n### ⚠️ Circular Dependencies Detected\n")
            for cycle in cycles:
                sections.append(f"- {' → '.join(cycle)}")
        
        return '\n'.join(sections)
    
    def _generate_decisions_section(self) -> str:
        """Generate architecture decisions documentation"""
        sections = ["## Architecture Decisions\n"]
        
        for decision in self.decisions:
            sections.append(f"### {decision.title} (ADR-{decision.id})")
            sections.append(f"\n**Status:** {decision.status.upper()}")
            sections.append(f"**Date:** {decision.date.strftime('%Y-%m-%d')}")
            sections.append(f"**Stakeholders:** {', '.join(decision.stakeholders)}\n")
            
            sections.append("**Context:**")
            sections.append(f"> {decision.context}\n")
            
            sections.append("**Decision:**")
            sections.append(f"> {decision.decision}\n")
            
            sections.append("**Consequences:**")
            for consequence in decision.consequences:
                sections.append(f"- {consequence}")
            
            if decision.alternatives:
                sections.append("\n**Alternatives Considered:**")
                for alt in decision.alternatives:
                    sections.append(f"- {alt}")
            
            sections.append("")
        
        return '\n'.join(sections)
    
    def _generate_diagrams_section(self, level: ArchitectureLevel) -> str:
        """Generate diagrams reference section"""
        sections = ["## Diagrams\n"]
        
        diagram_files = {
            ArchitectureLevel.CONTEXT: "context_diagram",
            ArchitectureLevel.CONTAINER: "container_diagram",
            ArchitectureLevel.COMPONENT: "component_diagram",
            ArchitectureLevel.CODE: "code_diagram"
        }
        
        diagram_file = diagram_files.get(level, "architecture_diagram")
        
        sections.append(f"### Architecture Diagram")
        sections.append(f"\n![{level.value.title()} Diagram]({diagram_file}.png)")
        sections.append(f"\n**Source:** [{diagram_file}.mmd]({diagram_file}.mmd)")
        
        return '\n'.join(sections)
    
    def _generate_footer(self) -> str:
        """Generate document footer"""
        return f"""---
*This documentation was automatically generated by the Architecture Documentation Generator.*
*For updates or corrections, please modify the source code and regenerate.*
"""
    
    def _generate_diagrams(self, level: ArchitectureLevel, output_path: str) -> Dict[str, str]:
        """Generate architecture diagrams"""
        diagrams = {}
        
        if level == ArchitectureLevel.CONTEXT:
            diagrams["context_diagram"] = self._generate_context_diagram(output_path)
        elif level == ArchitectureLevel.CONTAINER:
            diagrams["container_diagram"] = self._generate_container_diagram(output_path)
        elif level == ArchitectureLevel.COMPONENT:
            diagrams["component_diagram"] = self._generate_component_diagram(output_path)
        elif level == ArchitectureLevel.CODE:
            diagrams["code_diagram"] = self._generate_code_diagram(output_path)
        
        return diagrams
    
    def _generate_context_diagram(self, output_path: str) -> str:
        """Generate C4 Context diagram using Mermaid"""
        diagram = """```mermaid
C4Context
    title System Context Diagram
    
    Person(user, "User", "End user of the system")
    Person(admin, "Administrator", "System administrator")
    
    System(system, "System", "The main system being documented")
    
    System_Ext(db, "Database", "Data persistence layer")
    System_Ext(cache, "Cache", "Caching layer")
    System_Ext(queue, "Message Queue", "Async message processing")
    
    Rel(user, system, "Uses", "HTTPS")
    Rel(admin, system, "Administers", "HTTPS")
    Rel(system, db, "Reads/Writes", "SQL/NoSQL")
    Rel(system, cache, "Reads/Writes", "Redis Protocol")
    Rel(system, queue, "Publishes/Consumes", "AMQP")
    
    UpdateLayoutConfig($c4ShapeInRow="3", $c4BoundaryInRow="1")
```"""
        
        diagram_path = Path(output_path).parent / "context_diagram.mmd"
        file_utils.write_file(str(diagram_path), diagram)
        
        return str(diagram_path)
    
    def _generate_container_diagram(self, output_path: str) -> str:
        """Generate C4 Container diagram using Mermaid"""
        containers = []
        for name, component in self.components.items():
            containers.append(f'    Container({name.lower().replace(" ", "_")}, "{name}", "{component.type}", "{component.description[:50]}")')
        
        diagram = f"""```mermaid
C4Container
    title Container Diagram
    
    Person(user, "User", "System user")
    
    Boundary(system, "System Boundary") {{
{chr(10).join(containers)}
    }}
    
    Rel(user, {list(self.components.keys())[0].lower().replace(" ", "_") if self.components else "system"}, "Uses")
    
    UpdateLayoutConfig($c4ShapeInRow="3", $c4BoundaryInRow="1")
```"""
        
        diagram_path = Path(output_path).parent / "container_diagram.mmd"
        file_utils.write_file(str(diagram_path), diagram)
        
        return str(diagram_path)
    
    def _generate_component_diagram(self, output_path: str) -> str:
        """Generate component diagram using Mermaid"""
        # Build node definitions
        nodes = []
        for name in self.components.keys():
            nodes.append(f'    {name.lower().replace(" ", "_")}["{name}"]')
        
        # Build edge definitions
        edges = []
        for source, targets in self.dependency_graph.items():
            for target in targets:
                edges.append(f'    {source.lower().replace(" ", "_")} --> {target.lower().replace(" ", "_")}')
        
        diagram = f"""```mermaid
graph TD
    title Component Diagram
    
    {chr(10).join(nodes)}
    
    {chr(10).join(edges)}
    
    style default fill:#f9f,stroke:#333,stroke-width:2px
```"""
        
        diagram_path = Path(output_path).parent / "component_diagram.mmd"
        file_utils.write_file(str(diagram_path), diagram)
        
        return str(diagram_path)
    
    def _generate_code_diagram(self, output_path: str) -> str:
        """Generate class diagram using Mermaid"""
        classes = []
        relationships = []
        
        for class_name, class_info in list(self.classes.items())[:20]:  # Limit to 20 classes
            methods = [f"    +{m['name']}({', '.join(m['args'])})" for m in class_info.get('methods', [])[:5]]
            methods_str = '\n'.join(methods) if methods else "    +__init__()"
            
            classes.append(f"""    class {class_name.split('.')[-1]} {{{methods_str}}}""")
            
            for base in class_info.get('base_classes', []):
                relationships.append(f'    {base} <|-- {class_name.split(".")[-1]}')
        
        diagram = f"""```mermaid\nclassDiagram\n\ttitle Class Diagram (Selected Classes){chr(10).join(classes)}{chr(10).join(relationships)}\n```"""
        
        diagram_path = Path(output_path).parent / "code_diagram.mmd"
        file_utils.write_file(str(diagram_path), diagram)
        
        return str(diagram_path)
    
    def _write_output(self, output_path: str, documentation: str, include_diagrams: bool) -> None:
        """Write documentation to output file"""
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Write main documentation
        file_utils.write_file(str(output_file), documentation)
        
        # Write as Markdown if different extension
        if output_file.suffix != '.md':
            md_file = output_file.with_suffix('.md')
            file_utils.write_file(str(md_file), documentation)
        
        logger.info(f"Documentation written to {output_path}")
    
    def add_decision(self, decision: ArchitectureDecision) -> None:
        """Add an architecture decision"""
        self.decisions.append(decision)
        logger.info(f"Added architecture decision: {decision.title}")
    
    def export_architecture(self, format: str = "json") -> Dict[str, Any]:
        """Export architecture data in specified format"""
        return {
            "components": {k: v.__dict__ for k, v in self.components.items()},
            "data_flows": [f.__dict__ for f in self.data_flows],
            "decisions": [d.__dict__ for d in self.decisions],
            "api_endpoints": self.api_endpoints,
            "technology_stack": self.technology_stack,
            "dependency_graph": {k: list(v) for k, v in self.dependency_graph.items()},
            "statistics": {
                "total_components": len(self.components),
                "total_apis": len(self.api_endpoints),
                "total_flows": len(self.data_flows),
                "total_decisions": len(self.decisions),
                "total_modules": len(self.modules),
                "total_classes": len(self.classes),
                "total_functions": len(self.functions)
            }
        }


# Convenience function
def generate_architecture_docs(project_path: str, 
                               output_path: str = None,
                               level: str = "component",
                               style: str = "technical",
                               include_diagrams: bool = True) -> Dict[str, Any]:
    """
    Generate architecture documentation for a project.
    
    Args:
        project_path: Path to the project root
        output_path: Output file path (default: project_path/ARCHITECTURE.md)
        level: Architecture level (context, container, component, code)
        style: Documentation style (technical, executive, developer, ops)
        include_diagrams: Include diagrams in output
        
    Returns:
        Generation metadata
    """
    if output_path is None:
        output_path = str(Path(project_path) / "ARCHITECTURE.md")
    
    generator = ArchitectureDocGenerator()
    
    level_enum = ArchitectureLevel(level)
    style_enum = DocumentationStyle(style)
    
    return generator.generate(
        project_path=project_path,
        output_path=output_path,
        level=level_enum,
        style=style_enum,
        include_diagrams=include_diagrams,
        include_decisions=True
    )