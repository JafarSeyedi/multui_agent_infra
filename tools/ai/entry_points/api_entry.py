#!/usr/bin/env python3
"""
API Entry Point - REST API entry point for the AI development framework.

Part of the Entry Points module (entry_points/api_entry.py)

This api_entry.py provides:

1. FastAPI-Based REST API - Full REST API with FastAPI framework
2. Workflow Execution - Run workflows synchronously or asynchronously
3. Code Analysis Endpoints - Analyze complexity, security, style
4. Code Generation Endpoints - Generate classes, functions, tests
5. Validation Endpoints - Validate types, style, and more
6. Planning Endpoints - Plan architecture, decompose tasks
7. Health Check - Standardized health endpoint
8. Authentication - API key, Bearer token, Basic auth
9. Rate Limiting - Configurable request rate limiting
10. CORS Support - Cross-origin resource sharing
11. Background Tasks - Async workflow execution
12. Request Logging - Request ID tracking and timing
13. OpenAPI Documentation - Auto-generated Swagger/ReDoc docs
14. Metrics Endpoint - API usage metrics

The API entry point exposes all AI development framework capabilities through a clean REST interface.
"""

import json
import asyncio
import argparse
from pathlib import Path
from typing import Dict, List, Set, Optional, Any, Tuple, Union, Callable
from datetime import datetime
from enum import Enum

try:
    from fastapi import FastAPI, Request, Response, BackgroundTasks, HTTPException
    from fastapi.responses import JSONResponse, StreamingResponse
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.middleware.gzip import GZipMiddleware
    from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
    from fastapi.openapi.utils import get_openapi
    import uvicorn
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    FastAPI = None

from .base_entry_point import (
    BaseEntryPoint, 
    EntryPointConfig, 
    EntryPointType,
    ExecutionMode,
    EntryPointResult,
    EntryPointContext,
    ExitCode
)
from ..shared.logger import get_logger, LogLevel
from ..shared.config import Config
from ..orchestration.workflow_engine import WorkflowContext

logger = get_logger(__name__)


# ============================================================
# ENUMS AND CONSTANTS
# ============================================================

class HTTPMethod(str, Enum):
    """HTTP methods."""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"
    OPTIONS = "OPTIONS"
    HEAD = "HEAD"


class APIResponseStatus(str, Enum):
    """API response status."""
    SUCCESS = "success"
    ERROR = "error"
    PENDING = "pending"
    PROCESSING = "processing"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AuthMethod(str, Enum):
    """Authentication methods."""
    NONE = "none"
    API_KEY = "api_key"
    BEARER = "bearer"
    BASIC = "basic"
    OAUTH2 = "oauth2"


# ============================================================
# DATA MODELS
# ============================================================

from pydantic import BaseModel, Field
from typing import Optional as OptionalType


class APIResponse(BaseModel):
    """Standard API response format."""
    status: APIResponseStatus = APIResponseStatus.SUCCESS
    message: str = ""
    data: OptionalType[Any] = None
    request_id: OptionalType[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    duration_ms: OptionalType[float] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class WorkflowRequest(BaseModel):
    """Request to run a workflow."""
    workflow_name: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    async_mode: bool = False
    timeout: OptionalType[int] = None
    priority: int = 0
    tags: List[str] = Field(default_factory=list)


class WorkflowResponse(BaseModel):
    """Response from workflow execution."""
    workflow_id: str
    workflow_name: str
    status: str
    result: OptionalType[Any] = None
    error: OptionalType[str] = None
    started_at: datetime = Field(default_factory=datetime.now)
    completed_at: OptionalType[datetime] = None


class AnalyzeRequest(BaseModel):
    """Request to analyze code."""
    path: OptionalType[str] = None
    code: OptionalType[str] = None
    analysis_type: str = "full"  # full, complexity, security, style
    include_metrics: bool = True
    include_suggestions: bool = True


class GenerateRequest(BaseModel):
    """Request to generate code."""
    type: str  # class, function, module, test
    name: str
    description: str
    requirements: OptionalType[Dict[str, Any]] = None
    output_path: OptionalType[str] = None


class ValidateRequest(BaseModel):
    """Request to validate code."""
    path: OptionalType[str] = None
    code: OptionalType[str] = None
    validators: List[str] = Field(default_factory=lambda: ["all"])
    fail_fast: bool = False


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = "healthy"
    version: str
    uptime_seconds: float
    components: Dict[str, str] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)


class APIConfig(EntryPointConfig):
    """Configuration for API entry point."""
    host: str = "127.0.0.1"
    port: int = 8000
    workers: int = 1
    reload: bool = False
    
    # API settings
    api_prefix: str = "/api/v1"
    api_title: str = "AI Development Framework API"
    api_description: str = "REST API for AI-powered development tools"
    api_version: str = "1.0.0"
    
    # CORS
    cors_enabled: bool = True
    cors_origins: List[str] = field(default_factory=lambda: ["*"])
    cors_methods: List[str] = field(default_factory=lambda: ["*"])
    cors_headers: List[str] = field(default_factory=lambda: ["*"])
    
    # Authentication
    auth_enabled: bool = False
    auth_method: AuthMethod = AuthMethod.NONE
    api_keys: List[str] = field(default_factory=list)
    jwt_secret: OptionalType[str] = None
    
    # Rate limiting
    rate_limit_enabled: bool = False
    rate_limit_requests: int = 100
    rate_limit_period: int = 60  # seconds
    
    # Documentation
    docs_enabled: bool = True
    docs_url: str = "/docs"
    redoc_url: str = "/redoc"
    openapi_url: str = "/openapi.json"
    
    # Request limits
    max_request_size: int = 10 * 1024 * 1024  # 10MB
    request_timeout: int = 60
    
    # Background tasks
    max_background_tasks: int = 10
    task_timeout: int = 300


# ============================================================
# API ENTRY POINT
# ============================================================

class APIEntryPoint(BaseEntryPoint):
    """
    REST API entry point for the AI development framework.
    
    Features:
    - FastAPI-based REST API
    - Workflow execution endpoints
    - Code analysis endpoints
    - Code generation endpoints
    - Validation endpoints
    - Health check endpoint
    - Async background task support
    - Authentication (API key, Bearer, OAuth2)
    - Rate limiting
    - CORS support
    - OpenAPI documentation
    - Request/response logging
    - Metrics collection
    """
    
    def __init__(self, config: Optional[APIConfig] = None):
        """Initialize the API entry point."""
        if not FASTAPI_AVAILABLE:
            raise ImportError(
                "FastAPI is required for API entry point. "
                "Install with: pip install fastapi uvicorn"
            )
        
        super().__init__(config)
        self.api_config: APIConfig = self.config
        self.app: Optional[FastAPI] = None
        self._background_tasks: Dict[str, Any] = {}
        self._server: Optional[uvicorn.Server] = None
        
        # Request tracking
        self._request_count = 0
        self._active_requests = 0
    
    def _get_default_config(self) -> APIConfig:
        """Get default API configuration."""
        return APIConfig(
            name="api_entry",
            entry_type=EntryPointType.API,
            execution_mode=ExecutionMode.ASYNC,
            description="REST API entry point for AI development framework"
        )
    
    # ============================================================
    # LIFECYCLE METHODS
    # ============================================================
    
    def setup(self):
        """Setup API server."""
        super().setup()
        
        # Create FastAPI app
        self.app = FastAPI(
            title=self.api_config.api_title,
            description=self.api_config.api_description,
            version=self.api_config.api_version,
            docs_url=self.api_config.docs_url if self.api_config.docs_enabled else None,
            redoc_url=self.api_config.redoc_url if self.api_config.docs_enabled else None,
            openapi_url=self.api_config.openapi_url
        )
        
        # Add middleware
        self._setup_middleware()
        
        # Setup routes
        self._setup_routes()
        
        # Setup authentication
        if self.api_config.auth_enabled:
            self._setup_authentication()
        
        # Setup rate limiting
        if self.api_config.rate_limit_enabled:
            self._setup_rate_limiting()
        
        logger.info(f"API server configured on {self.api_config.host}:{self.api_config.port}")
    
    def _setup_middleware(self):
        """Setup FastAPI middleware."""
        # CORS
        if self.api_config.cors_enabled:
            self.app.add_middleware(
                CORSMiddleware,
                allow_origins=self.api_config.cors_origins,
                allow_credentials=True,
                allow_methods=self.api_config.cors_methods,
                allow_headers=self.api_config.cors_headers,
            )
        
        # GZip compression
        self.app.add_middleware(GZipMiddleware, minimum_size=1000)
        
        # Request logging middleware
        @self.app.middleware("http")
        async def log_requests(request: Request, call_next):
            self._request_count += 1
            self._active_requests += 1
            start_time = datetime.now()
            
            request_id = self._generate_request_id()
            request.state.request_id = request_id
            
            logger.debug(f"[{request_id}] {request.method} {request.url.path}")
            
            try:
                response = await call_next(request)
                duration_ms = (datetime.now() - start_time).total_seconds() * 1000
                
                logger.debug(
                    f"[{request_id}] {request.method} {request.url.path} "
                    f"-> {response.status_code} ({duration_ms:.2f}ms)"
                )
                
                response.headers["X-Request-ID"] = request_id
                response.headers["X-Response-Time"] = f"{duration_ms:.2f}ms"
                
                return response
            finally:
                self._active_requests -= 1
        
        # Authentication middleware
        if self.api_config.auth_enabled:
            @self.app.middleware("http")
            async def authenticate(request: Request, call_next):
                if self._should_skip_auth(request):
                    return await call_next(request)
                
                auth_header = request.headers.get("Authorization", "")
                
                if not auth_header:
                    return JSONResponse(
                        status_code=401,
                        content=self._error_response("Missing authorization header", "UNAUTHORIZED")
                    )
                
                if not self._verify_auth(auth_header):
                    return JSONResponse(
                        status_code=401,
                        content=self._error_response("Invalid authorization", "UNAUTHORIZED")
                    )
                
                return await call_next(request)
    
    def _setup_routes(self):
        """Setup API routes."""
        prefix = self.api_config.api_prefix
        
        # Health check
        @self.app.get(f"{prefix}/health", response_model=HealthResponse)
        async def health_check():
            return self.health_check()
        
        # Root
        @self.app.get("/")
        async def root():
            return {
                "name": self.api_config.api_title,
                "version": self.api_config.api_version,
                "docs": self.api_config.docs_url if self.api_config.docs_enabled else None,
                "status": "running"
            }
        
        # ============================================================
        # WORKFLOW ENDPOINTS
        # ============================================================
        
        @self.app.post(f"{prefix}/workflows/run", response_model=WorkflowResponse)
        async def run_workflow(request: WorkflowRequest, background_tasks: BackgroundTasks):
            """Run a workflow."""
            if not self.workflow_engine:
                raise HTTPException(503, "Workflow engine not available")
            
            workflow_id = self._generate_workflow_id()
            
            if request.async_mode:
                background_tasks.add_task(
                    self._execute_workflow_background,
                    workflow_id, request.workflow_name, request.parameters
                )
                return WorkflowResponse(
                    workflow_id=workflow_id,
                    workflow_name=request.workflow_name,
                    status="pending"
                )
            else:
                result = await self._execute_workflow_sync(
                    workflow_id, request.workflow_name, request.parameters, request.timeout
                )
                return WorkflowResponse(
                    workflow_id=workflow_id,
                    workflow_name=request.workflow_name,
                    status="completed",
                    result=result.get('result'),
                    error=result.get('error'),
                    completed_at=datetime.now()
                )
        
        @self.app.get(f"{prefix}/workflows/status/{{workflow_id}}")
        async def get_workflow_status(workflow_id: str):
            """Get workflow status."""
            task_info = self._background_tasks.get(workflow_id)
            if not task_info:
                raise HTTPException(404, f"Workflow {workflow_id} not found")
            
            return {
                "workflow_id": workflow_id,
                "status": task_info.get("status", "unknown"),
                "started_at": task_info.get("started_at"),
                "completed_at": task_info.get("completed_at"),
                "result": task_info.get("result"),
                "error": task_info.get("error")
            }
        
        @self.app.get(f"{prefix}/workflows/list")
        async def list_workflows():
            """List available workflows."""
            if not self.workflow_engine:
                return {"workflows": []}
            
            workflows = self.workflow_engine.list_workflows()
            return {
                "workflows": [
                    {"name": w, "description": self.workflow_engine.get_workflow_description(w)}
                    for w in workflows
                ]
            }
        
        @self.app.post(f"{prefix}/workflows/cancel/{{workflow_id}}")
        async def cancel_workflow(workflow_id: str):
            """Cancel a running workflow."""
            task_info = self._background_tasks.get(workflow_id)
            if not task_info:
                raise HTTPException(404, f"Workflow {workflow_id} not found")
            
            if task_info.get("status") not in ("pending", "processing"):
                raise HTTPException(400, f"Workflow {workflow_id} cannot be cancelled")
            
            task_info["status"] = "cancelled"
            self._background_tasks[workflow_id] = task_info
            
            return {"workflow_id": workflow_id, "status": "cancelled"}
        
        # ============================================================
        # ANALYSIS ENDPOINTS
        # ============================================================
        
        @self.app.post(f"{prefix}/analyze")
        async def analyze_code(request: AnalyzeRequest):
            """Analyze code."""
            if not request.path and not request.code:
                raise HTTPException(400, "Either path or code must be provided")
            
            workflow_params = {
                "path": request.path,
                "code": request.code,
                "analysis_type": request.analysis_type,
                "include_metrics": request.include_metrics,
                "include_suggestions": request.include_suggestions
            }
            
            result = await self.run_workflow_async("analysis_workflow", **workflow_params)
            
            return self._success_response("Analysis completed", result)
        
        @self.app.get(f"{prefix}/analyze/complexity")
        async def analyze_complexity(path: str):
            """Analyze code complexity."""
            result = await self.run_workflow_async(
                "analysis_workflow",
                path=path,
                analysis_type="complexity"
            )
            return self._success_response("Complexity analysis completed", result)
        
        @self.app.get(f"{prefix}/analyze/security")
        async def analyze_security(path: str):
            """Analyze security vulnerabilities."""
            result = await self.run_workflow_async(
                "analysis_workflow",
                path=path,
                analysis_type="security"
            )
            return self._success_response("Security analysis completed", result)
        
        # ============================================================
        # GENERATION ENDPOINTS
        # ============================================================
        
        @self.app.post(f"{prefix}/generate")
        async def generate_code(request: GenerateRequest):
            """Generate code."""
            workflow_params = {
                "type": request.type,
                "name": request.name,
                "description": request.description,
                "requirements": request.requirements,
                "output_path": request.output_path
            }
            
            result = await self.run_workflow_async("generation_workflow", **workflow_params)
            
            return self._success_response("Code generation completed", result)
        
        @self.app.post(f"{prefix}/generate/class")
        async def generate_class(
            name: str,
            description: str,
            output_path: OptionalType[str] = None
        ):
            """Generate a class."""
            return await generate_code(GenerateRequest(
                type="class",
                name=name,
                description=description,
                output_path=output_path
            ))
        
        @self.app.post(f"{prefix}/generate/function")
        async def generate_function(
            name: str,
            description: str,
            output_path: OptionalType[str] = None
        ):
            """Generate a function."""
            return await generate_code(GenerateRequest(
                type="function",
                name=name,
                description=description,
                output_path=output_path
            ))
        
        @self.app.post(f"{prefix}/generate/test")
        async def generate_test(
            target_path: str,
            output_path: OptionalType[str] = None
        ):
            """Generate tests for code."""
            result = await self.run_workflow_async(
                "generation_workflow",
                type="test",
                target_path=target_path,
                output_path=output_path
            )
            return self._success_response("Test generation completed", result)
        
        # ============================================================
        # VALIDATION ENDPOINTS
        # ============================================================
        
        @self.app.post(f"{prefix}/validate")
        async def validate_code(request: ValidateRequest):
            """Validate code."""
            if not request.path and not request.code:
                raise HTTPException(400, "Either path or code must be provided")
            
            workflow_params = {
                "path": request.path,
                "code": request.code,
                "validators": request.validators,
                "fail_fast": request.fail_fast
            }
            
            result = await self.run_workflow_async("quality_workflow", **workflow_params)
            
            return self._success_response("Validation completed", result)
        
        @self.app.get(f"{prefix}/validate/types")
        async def validate_types(path: str):
            """Validate type hints."""
            result = await self.run_workflow_async(
                "quality_workflow",
                path=path,
                validators=["mypy"]
            )
            return self._success_response("Type validation completed", result)
        
        @self.app.get(f"{prefix}/validate/style")
        async def validate_style(path: str):
            """Validate code style."""
            result = await self.run_workflow_async(
                "quality_workflow",
                path=path,
                validators=["ruff"]
            )
            return self._success_response("Style validation completed", result)
        
        # ============================================================
        # PLANNING ENDPOINTS
        # ============================================================
        
        @self.app.post(f"{prefix}/plan/architecture")
        async def plan_architecture(
            name: str,
            description: str,
            pattern: str = "layered"
        ):
            """Plan module architecture."""
            result = await self.run_workflow_async(
                "planning_workflow",
                type="architecture",
                name=name,
                description=description,
                pattern=pattern
            )
            return self._success_response("Architecture planning completed", result)
        
        @self.app.post(f"{prefix}/plan/tasks")
        async def decompose_tasks(
            epic_title: str,
            epic_description: str
        ):
            """Decompose epic into tasks."""
            result = await self.run_workflow_async(
                "planning_workflow",
                type="task_decomposition",
                epic_title=epic_title,
                epic_description=epic_description
            )
            return self._success_response("Task decomposition completed", result)
        
        # ============================================================
        # METRICS ENDPOINTS
        # ============================================================
        
        @self.app.get(f"{prefix}/metrics")
        async def get_metrics():
            """Get API metrics."""
            base_metrics = self.get_metrics()
            
            api_metrics = {
                "requests_total": self._request_count,
                "requests_active": self._active_requests,
                "background_tasks": len(self._background_tasks),
                "workflow_metrics": base_metrics.get("workflow", {})
            }
            
            return self._success_response("Metrics retrieved", api_metrics)
    
    def _setup_authentication(self):
        """Setup authentication."""
        if self.api_config.auth_method == AuthMethod.API_KEY:
            @self.app.middleware("http")
            async def api_key_auth(request: Request, call_next):
                if self._should_skip_auth(request):
                    return await call_next(request)
                
                api_key = request.headers.get("X-API-Key")
                if not api_key or api_key not in self.api_config.api_keys:
                    return JSONResponse(
                        status_code=401,
                        content=self._error_response("Invalid API key", "INVALID_API_KEY")
                    )
                
                return await call_next(request)
    
    def _setup_rate_limiting(self):
        """Setup rate limiting."""
        from collections import defaultdict
        import time
        
        rate_limit_store = defaultdict(list)
        
        @self.app.middleware("http")
        async def rate_limit(request: Request, call_next):
            if self._should_skip_auth(request):
                return await call_next(request)
            
            client_ip = request.client.host if request.client else "unknown"
            now = time.time()
            
            # Clean old requests
            rate_limit_store[client_ip] = [
                t for t in rate_limit_store[client_ip]
                if now - t < self.api_config.rate_limit_period
            ]
            
            if len(rate_limit_store[client_ip]) >= self.api_config.rate_limit_requests:
                return JSONResponse(
                    status_code=429,
                    content=self._error_response("Rate limit exceeded", "RATE_LIMIT_EXCEEDED")
                )
            
            rate_limit_store[client_ip].append(now)
            return await call_next(request)
    
    def _should_skip_auth(self, request: Request) -> bool:
        """Check if authentication should be skipped for this request."""
        skip_paths = [
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/"
        ]
        return any(request.url.path.endswith(p) for p in skip_paths)
    
    def _verify_auth(self, auth_header: str) -> bool:
        """Verify authentication header."""
        if self.api_config.auth_method == AuthMethod.BEARER:
            if auth_header.startswith("Bearer "):
                token = auth_header[7:]
                return self._verify_bearer_token(token)
        elif self.api_config.auth_method == AuthMethod.BASIC:
            if auth_header.startswith("Basic "):
                import base64
                try:
                    decoded = base64.b64decode(auth_header[6:]).decode()
                    username, password = decoded.split(":", 1)
                    return self._verify_credentials(username, password)
                except Exception:
                    return False
        return False
    
    def _verify_bearer_token(self, token: str) -> bool:
        """Verify bearer token."""
        if not self.api_config.jwt_secret:
            return False
        try:
            import jwt
            jwt.decode(token, self.api_config.jwt_secret, algorithms=["HS256"])
            return True
        except Exception:
            return False
    
    def _verify_credentials(self, username: str, password: str) -> bool:
        """Verify basic auth credentials."""
        # Override for custom credential verification
        return False
    
    # ============================================================
    # EXECUTION
    # ============================================================
    
    async def execute_async(self) -> EntryPointResult:
        """Execute the API server."""
        logger.info(f"Starting API server on {self.api_config.host}:{self.api_config.port}")
        
        config = uvicorn.Config(
            app=self.app,
            host=self.api_config.host,
            port=self.api_config.port,
            workers=self.api_config.workers,
            reload=self.api_config.reload,
            log_level=self.api_config.log_level.value.lower(),
            timeout_keep_alive=60,
            access_log=True
        )
        
        self._server = uvicorn.Server(config)
        
        try:
            await self._server.serve()
            return self.create_success_result("API server stopped normally")
        except asyncio.CancelledError:
            logger.info("API server cancelled")
            return self.create_success_result("API server cancelled")
        except Exception as e:
            logger.error(f"API server error: {e}")
            return self.create_error_result(f"API server error: {e}", e)
    
    def execute(self) -> EntryPointResult:
        """Execute the API server (sync wrapper)."""
        logger.info(f"Starting API server on {self.api_config.host}:{self.api_config.port}")
        
        try:
            uvicorn.run(
                app=self.app,
                host=self.api_config.host,
                port=self.api_config.port,
                workers=self.api_config.workers,
                reload=self.api_config.reload,
                log_level=self.api_config.log_level.value.lower()
            )
            return self.create_success_result("API server stopped normally")
        except KeyboardInterrupt:
            logger.info("API server interrupted")
            return self.create_success_result("API server interrupted")
        except Exception as e:
            logger.error(f"API server error: {e}")
            return self.create_error_result(f"API server error: {e}", e)
    
    # ============================================================
    # WORKFLOW EXECUTION
    # ============================================================
    
    async def _execute_workflow_sync(
        self, workflow_id: str, workflow_name: str, 
        parameters: Dict[str, Any], timeout: Optional[int] = None
    ) -> Dict[str, Any]:
        """Execute workflow synchronously."""
        timeout = timeout or self.api_config.request_timeout
        
        try:
            result = await asyncio.wait_for(
                self.run_workflow_async(workflow_name, **parameters),
                timeout=timeout
            )
            return {"result": result, "error": None}
        except asyncio.TimeoutError:
            return {"result": None, "error": f"Workflow timed out after {timeout}s"}
        except Exception as e:
            return {"result": None, "error": str(e)}
    
    async def _execute_workflow_background(
        self, workflow_id: str, workflow_name: str, parameters: Dict[str, Any]
    ):
        """Execute workflow in background."""
        self._background_tasks[workflow_id] = {
            "status": "processing",
            "started_at": datetime.now(),
            "completed_at": None,
            "result": None,
            "error": None
        }
        
        try:
            result = await self.run_workflow_async(workflow_name, **parameters)
            self._background_tasks[workflow_id].update({
                "status": "completed",
                "completed_at": datetime.now(),
                "result": result
            })
        except Exception as e:
            self._background_tasks[workflow_id].update({
                "status": "failed",
                "completed_at": datetime.now(),
                "error": str(e)
            })
    
    # ============================================================
    # UTILITY METHODS
    # ============================================================
    
    def _generate_request_id(self) -> str:
        """Generate unique request ID."""
        import uuid
        return str(uuid.uuid4())[:8]
    
    def _generate_workflow_id(self) -> str:
        """Generate unique workflow ID."""
        import uuid
        return f"wf_{uuid.uuid4().hex[:12]}"
    
    def _success_response(self, message: str, data: Any = None) -> Dict[str, Any]:
        """Create success response."""
        return {
            "status": APIResponseStatus.SUCCESS.value,
            "message": message,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
    
    def _error_response(self, message: str, error_code: str = "ERROR") -> Dict[str, Any]:
        """Create error response."""
        return {
            "status": APIResponseStatus.ERROR.value,
            "message": message,
            "error_code": error_code,
            "timestamp": datetime.now().isoformat()
        }
    
    def health_check(self) -> HealthResponse:
        """Perform health check."""
        components = {
            "workflow_engine": "healthy" if self.workflow_engine else "unavailable",
            "agent_registry": "healthy" if self.agent_registry else "unavailable",
            "state_manager": "healthy" if self.state_manager else "unavailable"
        }
        
        overall_status = "healthy" if all(v == "healthy" for v in components.values()) else "degraded"
        
        return HealthResponse(
            status=overall_status,
            version=self.api_config.api_version,
            uptime_seconds=self.context.get_duration_seconds(),
            components=components
        )
    
    def shutdown(self):
        """Shutdown API server."""
        if self._server:
            self._server.should_exit = True
        super().shutdown()
    
    async def shutdown_async(self):
        """Async shutdown API server."""
        if self._server:
            self._server.should_exit = True
            await self._server.shutdown()
        await super().shutdown_async()


# ============================================================
# CLI ENTRY POINT
# ============================================================

def main():
    """CLI entry point for API server."""
    import sys
    
    # Create and run API entry point
    api_entry = APIEntryPoint()
    
    # Customize argument parsing for API
    def parse_arguments(self, args=None):
        parser = self._create_argument_parser()
        parser.add_argument('--host', default='127.0.0.1', help='Host to bind to')
        parser.add_argument('--port', '-p', type=int, default=8000, help='Port to bind to')
        parser.add_argument('--workers', '-w', type=int, default=1, help='Number of workers')
        parser.add_argument('--reload', action='store_true', help='Enable auto-reload')
        parser.add_argument('--no-auth', action='store_true', help='Disable authentication')
        parser.add_argument('--api-key', action='append', help='API keys for authentication')
        return parser.parse_args(args)
    
    APIEntryPoint.parse_arguments = parse_arguments
    
    # Override config loading
    original_load_config = APIEntryPoint.load_configuration
    def load_configuration(self, args):
        config = original_load_config(self, args)
        self.api_config.host = args.host or self.api_config.host
        self.api_config.port = args.port or self.api_config.port
        self.api_config.workers = args.workers or self.api_config.workers
        self.api_config.reload = args.reload
        
        if args.no_auth:
            self.api_config.auth_enabled = False
        if args.api_key:
            self.api_config.auth_enabled = True
            self.api_config.auth_method = AuthMethod.API_KEY
            self.api_config.api_keys = args.api_key
        
        return config
    
    APIEntryPoint.load_configuration = load_configuration
    
    sys.exit(BaseEntryPoint.main(APIEntryPoint))


if __name__ == "__main__":
    main()