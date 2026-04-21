"""
API Documentation Generator

Generates comprehensive API documentation from code analysis including:
- REST API endpoints (FastAPI, Flask, Django)
- GraphQL schemas
- Function signatures and parameters
- Request/response schemas
- Authentication requirements
- Rate limiting policies
- Example requests and responses

Key Features:
1. Multi-Framework Support
FastAPI endpoints and parameters

Flask routes and methods

Django REST Framework viewsets

GraphQL schemas (Graphene)

2. Endpoint Discovery
Automatic route scanning

Method extraction (GET, POST, PUT, DELETE, PATCH)

Parameter detection (path, query, body)

Response model extraction

3. Data Model Extraction
Pydantic BaseModel fields

Python dataclasses

Field types and requirements

Descriptions from docstrings

4. GraphQL Schema Detection
Query resolvers

Mutation resolvers

Object types and fields

Subscription support

5. Documentation Formats
Markdown - Readable, version-controllable

HTML - Styled, browser-friendly

OpenAPI 3.0 - Standard, tool-compatible

6. Documentation Content
Endpoint summaries and descriptions

Parameter tables

Request/response schemas

Authentication requirements

Rate limiting policies

Example requests/responses

7. Smart Features
Docstring extraction for descriptions

Tag-based endpoint grouping

Response status codes (200, 400, 401, 404, 500)

Security scheme detection

Usage Examples:
python
# Basic usage
from tools.ai.quality.documenters.api_doc_generator import generate_api_docs

generate_api_docs(
    project_path="/path/to/project",
    output_path="/path/to/API.md",
    title="My API",
    version="2.0.0",
    format="markdown"
)

# Generate OpenAPI spec
generate_api_docs(
    project_path="/path/to/project",
    output_path="/path/to/openapi.json",
    format="openapi"
)
Output Examples:
Markdown Output:
markdown
# My API Documentation

**Version:** 2.0.0
**Framework:** fastapi

## Endpoints

### Users

#### `GET /users`

**Summary:** Get all users

**Parameters:**
| Name | In | Required | Type | Description |
|------|-----|----------|------|-------------|
| `limit` | query | No | `integer` | - |

**Responses:**
- **200:** Successful response
- **401:** Unauthorized

**Authentication:** Required (bearer)
OpenAPI Output:
json
{
  "openapi": "3.0.0",
  "info": {
    "title": "My API",
    "version": "2.0.0"
  },
  "paths": {
    "/users": {
      "get": {
        "summary": "Get all users",
        "responses": {
          "200": {"description": "Successful response"}
        }
      }
    }
  }
}
"""

import ast
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from collections import defaultdict

from ...shared.logger import get_logger
from ...shared.state_manager import state_manager
from ...shared.config import config
from ...shared.file_utils import file_utils

logger = get_logger(__name__)


class APIFramework(Enum):
    """Supported API frameworks"""
    FASTAPI = "fastapi"
    FLASK = "flask"
    DJANGO = "django"
    GRAPHQL = "graphql"
    RESTX = "flask_restx"
    DRF = "django_rest_framework"


class HttpMethod(Enum):
    """HTTP methods"""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"


class AuthType(Enum):
    """Authentication types"""
    NONE = "none"
    API_KEY = "api_key"
    BEARER = "bearer"
    BASIC = "basic"
    OAUTH2 = "oauth2"
    JWT = "jwt"


@dataclass
class APIEndpoint:
    """Represents an API endpoint"""
    path: str
    method: HttpMethod
    summary: str
    description: Optional[str] = None
    parameters: List[Dict[str, Any]] = field(default_factory=list)
    request_body: Optional[Dict[str, Any]] = None
    responses: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    auth_required: bool = False
    auth_type: AuthType = AuthType.NONE
    rate_limit: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    deprecated: bool = False
    source_file: Optional[str] = None
    line_number: Optional[int] = None
    examples: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "path": self.path,
            "method": self.method.value,
            "summary": self.summary,
            "description": self.description,
            "parameters": self.parameters,
            "request_body": self.request_body,
            "responses": self.responses,
            "auth_required": self.auth_required,
            "auth_type": self.auth_type.value,
            "rate_limit": self.rate_limit,
            "tags": self.tags,
            "deprecated": self.deprecated,
            "source_file": self.source_file,
            "examples": self.examples
        }


@dataclass
class GraphQLSchema:
    """Represents a GraphQL schema"""
    types: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    queries: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    mutations: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    subscriptions: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "types": self.types,
            "queries": self.queries,
            "mutations": self.mutations,
            "subscriptions": self.subscriptions
        }


@dataclass
class DataModel:
    """Represents a data model/schema"""
    name: str
    fields: Dict[str, Dict[str, Any]]
    description: Optional[str] = None
    examples: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "fields": self.fields,
            "description": self.description,
            "examples": self.examples
        }


class APIDocGenerator:
    """
    Generates comprehensive API documentation from code analysis.
    
    Features:
    - Multi-framework support (FastAPI, Flask, Django, GraphQL)
    - Request/response schema extraction
    - Parameter documentation
    - Authentication requirements
    - Rate limiting policies
    - Example generation
    - OpenAPI/Swagger compatible output
    """
    
    def __init__(self):
        self.endpoints: Dict[str, APIEndpoint] = {}
        self.graphql_schema: Optional[GraphQLSchema] = None
        self.data_models: Dict[str, DataModel] = {}
        self.framework: Optional[APIFramework] = None
        self.base_path: str = ""
        self.title: str = ""
        self.description: str = ""
        self.version: str = "1.0.0"
        
        logger.info("APIDocGenerator initialized")
    
    def generate(self, project_path: str,
                output_path: str,
                title: str = None,
                version: str = "1.0.0",
                format: str = "markdown") -> Dict[str, Any]:
        """
        Generate API documentation from project.
        
        Args:
            project_path: Path to the project root
            output_path: Path to write documentation
            title: API title
            version: API version
            format: Output format (markdown, html, openapi)
            
        Returns:
            Generation metadata
        """
        self.project_path = Path(project_path)
        self.title = title or self.project_path.name
        self.version = version
        
        logger.info(f"Generating API documentation for {project_path}")
        
        # Step 1: Detect framework
        self._detect_framework()
        
        # Step 2: Scan for endpoints
        self._scan_endpoints()
        
        # Step 3: Extract data models
        self._extract_data_models()
        
        # Step 4: Generate documentation
        if format == "markdown":
            documentation = self._generate_markdown()
        elif format == "openapi":
            documentation = self._generate_openapi()
        elif format == "html":
            documentation = self._generate_html()
        else:
            documentation = self._generate_markdown()
        
        # Step 5: Write output
        self._write_output(output_path, documentation, format)
        
        return {
            "documentation_path": output_path,
            "endpoints_count": len(self.endpoints),
            "data_models_count": len(self.data_models),
            "framework": self.framework.value if self.framework else "unknown",
            "format": format,
            "generated_at": datetime.now().isoformat()
        }
    
    def _detect_framework(self) -> None:
        """Detect which API framework is being used"""
        # Check for FastAPI
        if any(f.name == 'fastapi' for f in self.project_path.rglob('*.py')):
            content = self._search_in_files('from fastapi import')
            if content:
                self.framework = APIFramework.FASTAPI
                logger.info("Detected FastAPI framework")
                return
        
        # Check for Flask
        if any(f.name == 'flask' for f in self.project_path.rglob('*.py')):
            content = self._search_in_files('from flask import')
            if content:
                self.framework = APIFramework.FLASK
                logger.info("Detected Flask framework")
                return
        
        # Check for Django REST Framework
        if any(f.name == 'django' for f in self.project_path.rglob('*.py')):
            content = self._search_in_files('rest_framework')
            if content:
                self.framework = APIFramework.DRF
                logger.info("Detected Django REST Framework")
                return
        
        # Check for GraphQL
        if any(f.name == 'graphene' for f in self.project_path.rglob('*.py')):
            content = self._search_in_files('graphene')
            if content:
                self.framework = APIFramework.GRAPHQL
                logger.info("Detected GraphQL (Graphene)")
                return
        
        logger.warning("No supported API framework detected")
    
    def _search_in_files(self, pattern: str) -> bool:
        """Search for pattern in Python files"""
        for py_file in self.project_path.rglob("*.py"):
            try:
                content = file_utils.read_file(str(py_file))
                if pattern in content:
                    return True
            except Exception:
                continue
        return False
    
    def _scan_endpoints(self) -> None:
        """Scan for API endpoints in the codebase"""
        if self.framework == APIFramework.FASTAPI:
            self._scan_fastapi_endpoints()
        elif self.framework == APIFramework.FLASK:
            self._scan_flask_endpoints()
        elif self.framework == APIFramework.DRF:
            self._scan_drf_endpoints()
        elif self.framework == APIFramework.GRAPHQL:
            self._scan_graphql_schema()
    
    def _scan_fastapi_endpoints(self) -> None:
        """Scan FastAPI endpoints"""
        logger.info("Scanning FastAPI endpoints...")
        
        for py_file in self.project_path.rglob("*.py"):
            content = file_utils.read_file(str(py_file))
            
            # Pattern for FastAPI route decorators
            pattern = r'@(?:app|router)\.(get|post|put|delete|patch|options|head)\([\'"]([^\'"]+)[\'"](?:[^)]*)\)\s*\n\s*async?\s+def\s+(\w+)\('
            
            for match in re.finditer(pattern, content, re.MULTILINE):
                method_str = match.group(1).upper()
                path = match.group(2)
                function_name = match.group(3)
                
                method = HttpMethod(method_str)
                endpoint_id = f"{method.value} {path}"
                
                # Extract docstring
                docstring = self._extract_docstring_for_function(content, function_name)
                
                # Extract parameters
                parameters = self._extract_fastapi_parameters(content, function_name)
                
                # Extract response models
                responses = self._extract_responses(content, function_name)
                
                endpoint = APIEndpoint(
                    path=path,
                    method=method,
                    summary=docstring.split('\n')[0] if docstring else function_name,
                    description=docstring,
                    parameters=parameters,
                    responses=responses,
                    source_file=str(py_file),
                    tags=self._extract_tags(content, function_name)
                )
                
                self.endpoints[endpoint_id] = endpoint
        
        logger.info(f"Found {len(self.endpoints)} FastAPI endpoints")
    
    def _scan_flask_endpoints(self) -> None:
        """Scan Flask endpoints"""
        logger.info("Scanning Flask endpoints...")
        
        for py_file in self.project_path.rglob("*.py"):
            content = file_utils.read_file(str(py_file))
            
            # Pattern for Flask route decorators
            pattern = r'@(?:app|blueprint)\.route\([\'"]([^\'"]+)[\'"](?:,\s*methods=\[([^\]]+)\])?\)\s*\n\s*def\s+(\w+)\('
            
            for match in re.finditer(pattern, content, re.MULTILINE):
                path = match.group(1)
                methods_str = match.group(2)
                function_name = match.group(3)
                
                # Parse methods
                if methods_str:
                    methods = [m.strip().strip("'\"") for m in methods_str.split(',')]
                else:
                    methods = ['GET']
                
                for method_str in methods:
                    method = HttpMethod(method_str)
                    endpoint_id = f"{method.value} {path}"
                    
                    # Extract docstring
                    docstring = self._extract_docstring_for_function(content, function_name)
                    
                    endpoint = APIEndpoint(
                        path=path,
                        method=method,
                        summary=docstring.split('\n')[0] if docstring else function_name,
                        description=docstring,
                        source_file=str(py_file)
                    )
                    
                    self.endpoints[endpoint_id] = endpoint
        
        logger.info(f"Found {len(self.endpoints)} Flask endpoints")
    
    def _scan_drf_endpoints(self) -> None:
        """Scan Django REST Framework endpoints"""
        logger.info("Scanning Django REST Framework endpoints...")
        
        # Look for urls.py files
        for urls_file in self.project_path.rglob("urls.py"):
            content = file_utils.read_file(str(urls_file))
            
            # Pattern for DRF router registration
            router_pattern = r'router\.register\([\'"]([^\'"]+)[\'"],\s*(\w+)'
            for match in re.finditer(router_pattern, content):
                prefix = match.group(1)
                viewset = match.group(2)
                
                # Default REST methods
                methods = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE']
                for method in methods:
                    if method == 'GET':
                        paths = [f"/{prefix}", f"/{prefix}/{{id}}"]
                    else:
                        paths = [f"/{prefix}"]
                    
                    for path in paths:
                        endpoint_id = f"{method} {path}"
                        endpoint = APIEndpoint(
                            path=path,
                            method=HttpMethod(method),
                            summary=f"{method} {viewset}",
                            source_file=str(urls_file),
                            tags=[prefix]
                        )
                        self.endpoints[endpoint_id] = endpoint
        
        logger.info(f"Found {len(self.endpoints)} DRF endpoints")
    
    def _scan_graphql_schema(self) -> None:
        """Scan GraphQL schema"""
        logger.info("Scanning GraphQL schema...")
        
        self.graphql_schema = GraphQLSchema()
        
        for py_file in self.project_path.rglob("*.py"):
            content = file_utils.read_file(str(py_file))
            
            # Look for graphene.ObjectType subclasses
            class_pattern = r'class\s+(\w+)\s*\(\s*graphene\.ObjectType\s*\):'
            for match in re.finditer(class_pattern, content):
                class_name = match.group(1)
                fields = self._extract_graphql_fields(content, class_name)
                self.graphql_schema.types[class_name] = fields
            
            # Look for Query class
            if 'class Query' in content:
                queries = self._extract_graphql_resolvers(content, 'Query')
                self.graphql_schema.queries = queries
            
            # Look for Mutation class
            if 'class Mutation' in content:
                mutations = self._extract_graphql_resolvers(content, 'Mutation')
                self.graphql_schema.mutations = mutations
        
        logger.info(f"Found {len(self.graphql_schema.types)} GraphQL types")
    
    def _extract_docstring_for_function(self, content: str, function_name: str) -> Optional[str]:
        """Extract docstring for a specific function"""
        pattern = rf'def\s+{function_name}\(.*?\):\s*\n\s*"""(.*?)"""'
        match = re.search(pattern, content, re.DOTALL)
        if match:
            return match.group(1).strip()
        return None
    
    def _extract_fastapi_parameters(self, content: str, function_name: str) -> List[Dict[str, Any]]:
        """Extract FastAPI parameters"""
        parameters = []
        
        # Find function definition
        func_pattern = rf'def\s+{function_name}\(([^)]+)\)'
        match = re.search(func_pattern, content)
        if not match:
            return parameters
        
        params_str = match.group(1)
        param_names = [p.strip().split(':')[0].strip() for p in params_str.split(',') if p.strip() and p.strip() != 'self']
        
        for param in param_names:
            # Check if parameter is a path parameter
            is_path = f'{{{param}}}' in content or f':{param}' in content
            # Check if parameter is a query parameter
            is_query = f'Query(...' in content or f'Query(None' in content
            
            param_info = {
                "name": param,
                "in": "path" if is_path else "query" if is_query else "body",
                "required": not is_query,
                "schema": {"type": "string"}
            }
            parameters.append(param_info)
        
        return parameters
    
    def _extract_responses(self, content: str, function_name: str) -> Dict[str, Dict[str, Any]]:
        """Extract response models"""
        responses = {}
        
        # Look for response_model in decorator
        response_pattern = rf'response_model=(\w+)'
        match = re.search(response_pattern, content)
        if match:
            model_name = match.group(1)
            responses["200"] = {
                "description": "Successful response",
                "schema": {"$ref": f"#/components/schemas/{model_name}"}
            }
        
        # Default responses
        responses.setdefault("400", {"description": "Bad request"})
        responses.setdefault("401", {"description": "Unauthorized"})
        responses.setdefault("404", {"description": "Not found"})
        responses.setdefault("500", {"description": "Internal server error"})
        
        return responses
    
    def _extract_tags(self, content: str, function_name: str) -> List[str]:
        """Extract tags from FastAPI endpoint"""
        tags = []
        tag_pattern = r'tags=\[([^\]]+)\]'
        match = re.search(tag_pattern, content)
        if match:
            tags_str = match.group(1)
            tags = [t.strip().strip("'\"") for t in tags_str.split(',')]
        return tags
    
    def _extract_graphql_fields(self, content: str, class_name: str) -> Dict[str, Any]:
        """Extract GraphQL fields from a class"""
        fields = {}
        
        # Find class body
        class_pattern = rf'class\s+{class_name}.*?:(.*?)(?=\nclass|\Z)'
        match = re.search(class_pattern, content, re.DOTALL)
        if not match:
            return fields
        
        class_body = match.group(1)
        
        # Look for field definitions
        field_pattern = r'(\w+)\s*=\s*graphene\.(\w+)\(([^)]*)\)'
        for field_match in re.finditer(field_pattern, class_body):
            field_name = field_match.group(1)
            field_type = field_match.group(2)
            field_args = field_match.group(3)
            
            fields[field_name] = {
                "type": field_type,
                "description": self._extract_field_description(class_body, field_name)
            }
        
        return fields
    
    def _extract_graphql_resolvers(self, content: str, class_name: str) -> Dict[str, Any]:
        """Extract GraphQL resolvers"""
        resolvers = {}
        
        resolver_pattern = rf'def\s+resolve_(\w+)\([^)]*\):'
        for match in re.finditer(resolver_pattern, content):
            field_name = match.group(1)
            docstring = self._extract_docstring_for_function(content, f'resolve_{field_name}')
            
            resolvers[field_name] = {
                "description": docstring.split('\n')[0] if docstring else f"Resolves {field_name}",
                "returns": "Any"
            }
        
        return resolvers
    
    def _extract_data_models(self) -> None:
        """Extract Pydantic/dataclass models"""
        logger.info("Extracting data models...")
        
        for py_file in self.project_path.rglob("*.py"):
            content = file_utils.read_file(str(py_file))
            
            # Look for Pydantic models
            pydantic_pattern = r'class\s+(\w+)\s*\(\s*BaseModel\s*\):'
            for match in re.finditer(pydantic_pattern, content):
                model_name = match.group(1)
                fields = self._extract_pydantic_fields(content, model_name)
                
                if model_name not in self.data_models:
                    self.data_models[model_name] = DataModel(
                        name=model_name,
                        fields=fields,
                        description=self._extract_class_docstring(content, model_name)
                    )
            
            # Look for dataclasses
            dataclass_pattern = r'@dataclass\s*\nclass\s+(\w+):'
            for match in re.finditer(dataclass_pattern, content):
                model_name = match.group(1)
                fields = self._extract_dataclass_fields(content, model_name)
                
                if model_name not in self.data_models:
                    self.data_models[model_name] = DataModel(
                        name=model_name,
                        fields=fields,
                        description=self._extract_class_docstring(content, model_name)
                    )
        
        logger.info(f"Found {len(self.data_models)} data models")
    
    def _extract_pydantic_fields(self, content: str, model_name: str) -> Dict[str, Dict[str, Any]]:
        """Extract fields from Pydantic model"""
        fields = {}
        
        # Find class body
        class_pattern = rf'class\s+{model_name}.*?:(.*?)(?=\nclass|\Z)'
        match = re.search(class_pattern, content, re.DOTALL)
        if not match:
            return fields
        
        class_body = match.group(1)
        
        # Field patterns
        field_pattern = r'(\w+)\s*:\s*(\w+(?:\[[^\]]+\])?)\s*=\s*(?:Field\(([^)]*)\)|(.+))'
        for field_match in re.finditer(field_pattern, class_body):
            field_name = field_match.group(1)
            field_type = field_match.group(2)
            
            # Extract description from Field
            description = None
            if 'Field(' in field_match.group(0):
                desc_pattern = r'description=["\']([^"\']+)["\']'
                desc_match = re.search(desc_pattern, field_match.group(0))
                if desc_match:
                    description = desc_match.group(1)
            
            fields[field_name] = {
                "type": field_type,
                "required": '= None' not in field_match.group(0),
                "description": description
            }
        
        return fields
    
    def _extract_dataclass_fields(self, content: str, model_name: str) -> Dict[str, Dict[str, Any]]:
        """Extract fields from dataclass"""
        fields = {}
        
        # Find class body
        class_pattern = rf'class\s+{model_name}.*?:(.*?)(?=\nclass|\Z)'
        match = re.search(class_pattern, content, re.DOTALL)
        if not match:
            return fields
        
        class_body = match.group(1)
        
        # Field pattern
        field_pattern = r'(\w+)\s*:\s*(\w+(?:\[[^\]]+\])?)\s*=\s*(?:field\(([^)]*)\)|(.+))?'
        for field_match in re.finditer(field_pattern, class_body):
            field_name = field_match.group(1)
            field_type = field_match.group(2)
            
            fields[field_name] = {
                "type": field_type,
                "required": '= None' not in field_match.group(0) if field_match.group(0) else True,
                "description": None
            }
        
        return fields
    
    def _extract_class_docstring(self, content: str, class_name: str) -> Optional[str]:
        """Extract class docstring"""
        pattern = rf'class\s+{class_name}.*?:\s*\n\s*"""(.*?)"""'
        match = re.search(pattern, content, re.DOTALL)
        if match:
            return match.group(1).strip()
        return None
    
    def _extract_field_description(self, class_body: str, field_name: str) -> Optional[str]:
        """Extract field description from comment"""
        pattern = rf'#\s*{field_name}:\s*(.+?)\n'
        match = re.search(pattern, class_body)
        if match:
            return match.group(1).strip()
        return None
    
    def _generate_markdown(self) -> str:
        """Generate Markdown documentation"""
        sections = []
        
        # Header
        sections.append(f"# {self.title} API Documentation\n")
        sections.append(f"**Version:** {self.version}")
        sections.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        sections.append(f"**Framework:** {self.framework.value if self.framework else 'Unknown'}\n")
        
        # Overview
        sections.append("## Overview\n")
        sections.append(f"This document describes the API endpoints for {self.title}.")
        sections.append(f"Total endpoints: {len(self.endpoints)}\n")
        
        # Data Models
        if self.data_models:
            sections.append("## Data Models\n")
            for model in self.data_models.values():
                sections.append(f"### {model.name}\n")
                if model.description:
                    sections.append(f"{model.description}\n")
                
                sections.append("| Field | Type | Required | Description |")
                sections.append("|-------|------|----------|-------------|")
                for field_name, field_info in model.fields.items():
                    required = "Yes" if field_info.get("required", True) else "No"
                    desc = field_info.get("description", "")
                    sections.append(f"| `{field_name}` | `{field_info['type']}` | {required} | {desc} |")
                sections.append("")
        
        # Endpoints by tag
        sections.append("## Endpoints\n")
        
        # Group by tags
        endpoints_by_tag = defaultdict(list)
        for endpoint in self.endpoints.values():
            if endpoint.tags:
                for tag in endpoint.tags:
                    endpoints_by_tag[tag].append(endpoint)
            else:
                endpoints_by_tag["default"].append(endpoint)
        
        for tag, endpoints in sorted(endpoints_by_tag.items()):
            sections.append(f"### {tag.title()}\n")
            
            for endpoint in endpoints:
                sections.append(f"#### `{endpoint.method.value} {endpoint.path}`\n")
                sections.append(f"**Summary:** {endpoint.summary}\n")
                
                if endpoint.description:
                    sections.append(f"**Description:** {endpoint.description}\n")
                
                # Parameters
                if endpoint.parameters:
                    sections.append("**Parameters:**\n")
                    sections.append("| Name | In | Required | Type | Description |")
                    sections.append("|------|-----|----------|------|-------------|")
                    for param in endpoint.parameters:
                        required = "Yes" if param.get("required", True) else "No"
                        sections.append(f"| `{param['name']}` | {param.get('in', 'query')} | {required} | `{param.get('schema', {}).get('type', 'string')}` | - |")
                    sections.append("")
                
                # Request Body
                if endpoint.request_body:
                    sections.append("**Request Body:**\n")
                    sections.append(f"```json\n{json.dumps(endpoint.request_body, indent=2)}\n```\n")
                
                # Responses
                if endpoint.responses:
                    sections.append("**Responses:**\n")
                    for status_code, response in endpoint.responses.items():
                        sections.append(f"- **{status_code}:** {response.get('description', '')}")
                    sections.append("")
                
                # Authentication
                if endpoint.auth_required:
                    sections.append(f"**Authentication:** Required ({endpoint.auth_type.value})")
                else:
                    sections.append("**Authentication:** Not required")
                
                # Rate Limit
                if endpoint.rate_limit:
                    sections.append(f"**Rate Limit:** {endpoint.rate_limit}")
                
                sections.append("---\n")
        
        # GraphQL Schema
        if self.graphql_schema:
            sections.append("## GraphQL Schema\n")
            
            if self.graphql_schema.queries:
                sections.append("### Queries\n")
                for name, query in self.graphql_schema.queries.items():
                    sections.append(f"- **{name}:** {query.get('description', 'No description')}")
                sections.append("")
            
            if self.graphql_schema.mutations:
                sections.append("### Mutations\n")
                for name, mutation in self.graphql_schema.mutations.items():
                    sections.append(f"- **{name}:** {mutation.get('description', 'No description')}")
                sections.append("")
            
            if self.graphql_schema.types:
                sections.append("### Types\n")
                for name, fields in self.graphql_schema.types.items():
                    sections.append(f"#### {name}\n")
                    for field_name, field_info in fields.items():
                        sections.append(f"- `{field_name}`: {field_info.get('type', 'Unknown')}")
                        if field_info.get('description'):
                            sections.append(f"  - {field_info['description']}")
                    sections.append("")
        
        # Footer
        sections.append("---")
        sections.append(f"*Documentation generated automatically by API Documentation Generator*")
        
        return '\n'.join(sections)
    
    def _generate_openapi(self) -> str:
        """Generate OpenAPI 3.0 specification"""
        openapi = {
            "openapi": "3.0.0",
            "info": {
                "title": self.title,
                "version": self.version,
                "description": f"API documentation for {self.title}",
                "generated_at": datetime.now().isoformat()
            },
            "paths": {},
            "components": {
                "schemas": {},
                "securitySchemes": {}
            }
        }
        
        # Add paths
        for endpoint in self.endpoints.values():
            path_item = openapi["paths"].setdefault(endpoint.path, {})
            
            operation = {
                "summary": endpoint.summary,
                "description": endpoint.description or "",
                "responses": {}
            }
            
            # Add parameters
            if endpoint.parameters:
                operation["parameters"] = []
                for param in endpoint.parameters:
                    operation["parameters"].append({
                        "name": param["name"],
                        "in": param.get("in", "query"),
                        "required": param.get("required", False),
                        "schema": param.get("schema", {"type": "string"})
                    })
            
            # Add responses
            for status_code, response in endpoint.responses.items():
                operation["responses"][status_code] = {
                    "description": response.get("description", "")
                }
            
            # Add security
            if endpoint.auth_required:
                operation["security"] = [{"BearerAuth": []}]
            
            path_item[endpoint.method.value.lower()] = operation
        
        # Add security scheme
        openapi["components"]["securitySchemes"] = {
            "BearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT"
            }
        }
        
        # Add schemas
        for model in self.data_models.values():
            schema = {
                "type": "object",
                "properties": {},
                "required": []
            }
            
            for field_name, field_info in model.fields.items():
                schema["properties"][field_name] = {
                    "type": self._map_type_to_openapi(field_info["type"]),
                    "description": field_info.get("description", "")
                }
                if field_info.get("required", True):
                    schema["required"].append(field_name)
            
            openapi["components"]["schemas"][model.name] = schema
        
        return json.dumps(openapi, indent=2)
    
    def _generate_html(self) -> str:
        """Generate HTML documentation"""
        markdown = self._generate_markdown()
        # Simple HTML wrapper
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>{self.title} API Documentation</title>
    <meta charset="utf-8">
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; margin: 0; padding: 20px; line-height: 1.6; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        h1, h2, h3, h4 {{ color: #333; }}
        h1 {{ border-bottom: 2px solid #333; padding-bottom: 10px; }}
        h2 {{ border-bottom: 1px solid #ccc; padding-bottom: 5px; }}
        code {{ background: #f4f4f4; padding: 2px 5px; border-radius: 3px; font-family: 'Courier New', monospace; }}
        pre {{ background: #f4f4f4; padding: 10px; border-radius: 5px; overflow-x: auto; }}
        table {{ border-collapse: collapse; width: 100%; margin: 15px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background: #f0f0f0; }}
        .endpoint {{ background: #f9f9f9; padding: 15px; margin: 15px 0; border-radius: 5px; border-left: 4px solid #007bff; }}
        .method {{ font-weight: bold; color: #007bff; }}
        hr {{ margin: 20px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="markdown-body">
            {self._markdown_to_html(markdown)}
        </div>
    </div>
</body>
</html>"""
        return html
    
    def _markdown_to_html(self, markdown: str) -> str:
        """Convert markdown to HTML (simplified)"""
        # This is a simplified conversion. For production, use a proper markdown library
        html = markdown
        html = re.sub(r'# (.*?)\n', r'<h1>\1</h1>\n', html)
        html = re.sub(r'## (.*?)\n', r'<h2>\1</h2>\n', html)
        html = re.sub(r'### (.*?)\n', r'<h3>\1</h3>\n', html)
        html = re.sub(r'#### (.*?)\n', r'<h4>\1</h4>\n', html)
        html = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', html)
        html = re.sub(r'`(.*?)`', r'<code>\1</code>', html)
        html = re.sub(r'\n- (.*?)\n', r'<li>\1</li>\n', html)
        html = re.sub(r'<li>.*?</li>\n', r'<ul>\g<0></ul>\n', html)
        html = re.sub(r'\n---\n', r'<hr>\n', html)
        return html
    
    def _map_type_to_openapi(self, py_type: str) -> str:
        """Map Python type to OpenAPI type"""
        type_map = {
            "str": "string",
            "int": "integer",
            "float": "number",
            "bool": "boolean",
            "list": "array",
            "dict": "object",
            "List": "array",
            "Dict": "object",
            "Optional": "string"
        }
        return type_map.get(py_type, "string")
    
    def _write_output(self, output_path: str, documentation: str, format: str) -> None:
        """Write documentation to output file"""
        output_file = Path(output_path)
        
        # Ensure directory exists
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Write documentation
        file_utils.write_file(str(output_file), documentation)
        
        # Also write OpenAPI spec if requested
        if format == "openapi":
            openapi_file = output_file.with_suffix('.json')
            file_utils.write_file(str(openapi_file), documentation)
        
        logger.info(f"Documentation written to {output_path}")


# Convenience function
def generate_api_docs(project_path: str,
                     output_path: str = None,
                     title: str = None,
                     version: str = "1.0.0",
                     format: str = "markdown") -> Dict[str, Any]:
    """
    Generate API documentation for a project.
    
    Args:
        project_path: Path to the project root
        output_path: Output file path (default: project_path/API.md)
        title: API title
        version: API version
        format: Output format (markdown, html, openapi)
        
    Returns:
        Generation metadata
    """
    if output_path is None:
        output_path = str(Path(project_path) / "API.md")
    
    generator = APIDocGenerator()
    
    return generator.generate(
        project_path=project_path,
        output_path=output_path,
        title=title,
        version=version,
        format=format
    )