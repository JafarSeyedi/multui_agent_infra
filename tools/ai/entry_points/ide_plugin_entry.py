#!/usr/bin/env python3
"""
IDE Plugin Entry Point - Backend service for IDE plugins (VSCode, IntelliJ, etc.)

Part of the Entry Points module (entry_points/ide_plugin_entry.py)

VSCode Extension (TypeScript)
The actual VSCode extension (.vsix file) would be written in TypeScript and would:

Start the backend service (this Python file)

Communicate via LSP or custom protocol

Provide UI components (sidebar, status bar, commands)

Handle editor integration

Example VSCode Extension Structure:
text
vscode-extension/
├── package.json           # Extension manifest
├── src/
│   ├── extension.ts       # Main extension entry
│   ├── client.ts          # LSP client
│   ├── commands.ts        # Command handlers
│   ├── views.ts           # Sidebar views
│   └── status.ts          # Status bar
├── ai-dev-backend/        # Bundled Python backend
│   └── ide_plugin_entry.py
└── resources/
    └── icon.png
This architecture provides:

Separation of concerns - UI in TypeScript, AI logic in Python

Independent updates - Backend can update without extension update

Multiple IDE support - Same backend works with VSCode, IntelliJ, etc.

Performance - Heavy AI processing happens in separate process
"""

import sys
import json
import asyncio
import argparse
from pathlib import Path
from typing import Dict, List, Set, Optional, Any, Tuple, Union
from datetime import datetime
from enum import Enum
import traceback

from .base_entry_point import (
    BaseEntryPoint,
    EntryPointConfig,
    EntryPointType,
    ExecutionMode,
    EntryPointResult,
    ExitCode
)
from ..shared.logger import get_logger
from ..shared.config import Config
from ..orchestration.workflow_engine import WorkflowContext

logger = get_logger(__name__)


# ============================================================
# ENUMS AND CONSTANTS
# ============================================================

class ProtocolType(str, Enum):
    """Communication protocol type."""
    STDIO = "stdio"           # Standard input/output (LSP style)
    HTTP = "http"             # HTTP REST API
    WEBSOCKET = "websocket"   # WebSocket for real-time
    SOCKET = "socket"         # TCP Socket
    NAMED_PIPE = "named_pipe" # Named pipe (Windows)


class MessageType(str, Enum):
    """Type of message exchanged with IDE."""
    REQUEST = "request"
    RESPONSE = "response"
    NOTIFICATION = "notification"
    PROGRESS = "progress"
    ERROR = "error"
    EVENT = "event"


class CommandScope(str, Enum):
    """Scope of IDE command."""
    WORKSPACE = "workspace"
    FILE = "file"
    SELECTION = "selection"
    PROJECT = "project"


# ============================================================
# DATA MODELS
# ============================================================

class IDEMessage(BaseModel):
    """Message exchanged with IDE."""
    id: Optional[str] = None
    type: MessageType = MessageType.REQUEST
    method: str
    params: Dict[str, Any] = Field(default_factory=dict)
    result: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class IDERequest(BaseModel):
    """Request from IDE."""
    id: str
    method: str
    params: Dict[str, Any] = Field(default_factory=dict)
    scope: CommandScope = CommandScope.WORKSPACE
    files: List[str] = Field(default_factory=list)


class IDEResponse(BaseModel):
    """Response to IDE."""
    id: str
    result: Optional[Any] = None
    error: Optional[str] = None
    diagnostics: Optional[List[Dict[str, Any]]] = None
    actions: List[Dict[str, Any]] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Diagnostic(BaseModel):
    """Code diagnostic (error, warning, info)."""
    file: str
    line: int
    column: int
    severity: str  # error, warning, info, hint
    code: str
    message: str
    source: str = "ai-dev"
    suggestion: Optional[str] = None
    fix_available: bool = False


class CodeAction(BaseModel):
    """Code action (quick fix, refactor, etc.)."""
    title: str
    kind: str  # quickfix, refactor, source, etc.
    file: str
    line: int
    edit: Optional[Dict[str, Any]] = None
    command: Optional[Dict[str, Any]] = None
    is_preferred: bool = False


class IDEPluginConfig(EntryPointConfig):
    """Configuration for IDE plugin entry point."""
    # Protocol settings
    protocol: ProtocolType = ProtocolType.STDIO
    host: str = "127.0.0.1"
    port: int = 9876
    
    # Feature flags
    enable_analysis: bool = True
    enable_generation: bool = True
    enable_refinement: bool = True
    enable_completion: bool = True
    enable_diagnostics: bool = True
    enable_code_actions: bool = True
    enable_inlay_hints: bool = True
    
    # Real-time settings
    debounce_ms: int = 500
    analysis_on_change: bool = True
    analysis_on_save: bool = True
    
    # Limits
    max_file_size_mb: int = 10
    max_context_lines: int = 100
    completion_timeout_ms: int = 1000
    
    # IDE-specific
    ide_type: str = "vscode"  # vscode, intellij, eclipse, etc.
    workspace_path: Optional[Path] = None


# ============================================================
# IDE PLUGIN ENTRY POINT
# ============================================================

class IDEPluginEntryPoint(BaseEntryPoint):
    """
    Backend service for IDE plugins.
    
    Features:
    - LSP-style communication via stdio
    - HTTP/WebSocket server mode
    - Real-time code analysis
    - Code generation on demand
    - Refactoring suggestions
    - Diagnostic reporting
    - Code actions (quick fixes)
    - Inlay hints
    - Completion suggestions
    - Progress reporting
    
    Supported IDEs:
    - VSCode (via extension)
    - IntelliJ IDEA (via plugin)
    - Eclipse (via plugin)
    - Sublime Text (via plugin)
    - Vim/Neovim (via LSP)
    """
    
    def __init__(self, config: Optional[IDEPluginConfig] = None):
        """Initialize the IDE plugin entry point."""
        super().__init__(config)
        self.plugin_config: IDEPluginConfig = self.config
        
        # Message handlers
        self._handlers: Dict[str, callable] = {}
        self._register_handlers()
        
        # Pending requests
        self._pending_requests: Dict[str, asyncio.Future] = {}
        
        # Workspace state
        self._workspace_files: Set[str] = set()
        self._diagnostics: Dict[str, List[Diagnostic]] = {}
        
        # Protocol server
        self._server = None
        self._reader = None
        self._writer = None
    
    def _get_default_config(self) -> IDEPluginConfig:
        """Get default IDE plugin configuration."""
        return IDEPluginConfig(
            name="ide_plugin",
            entry_type=EntryPointType.IDE_PLUGIN,
            execution_mode=ExecutionMode.ASYNC,
            description="IDE plugin backend service for AI development framework"
        )
    
    # ============================================================
    # MESSAGE HANDLERS REGISTRATION
    # ============================================================
    
    def _register_handlers(self):
        """Register all message handlers."""
        # Lifecycle
        self._handlers["initialize"] = self._handle_initialize
        self._handlers["initialized"] = self._handle_initialized
        self._handlers["shutdown"] = self._handle_shutdown
        self._handlers["exit"] = self._handle_exit
        
        # Workspace
        self._handlers["workspace/didChangeConfiguration"] = self._handle_config_change
        self._handlers["workspace/didChangeWorkspaceFolders"] = self._handle_workspace_change
        self._handlers["workspace/didChangeWatchedFiles"] = self._handle_file_change
        
        # Documents
        self._handlers["textDocument/didOpen"] = self._handle_document_open
        self._handlers["textDocument/didChange"] = self._handle_document_change
        self._handlers["textDocument/didClose"] = self._handle_document_close
        self._handlers["textDocument/didSave"] = self._handle_document_save
        
        # AI Development specific
        self._handlers["ai/analyze"] = self._handle_analyze
        self._handlers["ai/generate"] = self._handle_generate
        self._handlers["ai/refine"] = self._handle_refine
        self._handlers["ai/complete"] = self._handle_complete
        self._handlers["ai/explain"] = self._handle_explain
        self._handlers["ai/fix"] = self._handle_fix
        self._handlers["ai/refactor"] = self._handle_refactor
        self._handlers["ai/test"] = self._handle_generate_test
        self._handlers["ai/docstring"] = self._handle_generate_docstring
        self._handlers["ai/review"] = self._handle_review
        
        # Diagnostics and actions
        self._handlers["textDocument/codeAction"] = self._handle_code_action
        self._handlers["textDocument/codeLens"] = self._handle_code_lens
        self._handlers["textDocument/inlayHint"] = self._handle_inlay_hint
        self._handlers["textDocument/completion"] = self._handle_completion
    
    # ============================================================
    # LIFECYCLE HANDLERS
    # ============================================================
    
    async def _handle_initialize(self, request: IDERequest) -> IDEResponse:
        """Handle initialize request."""
        logger.info(f"Initializing IDE plugin for {request.params.get('clientInfo', {}).get('name', 'unknown')}")
        
        # Store client capabilities
        self._client_capabilities = request.params.get("capabilities", {})
        
        # Set workspace path
        if "workspaceFolders" in request.params:
            folders = request.params["workspaceFolders"]
            if folders:
                self.plugin_config.workspace_path = Path(folders[0]["uri"].replace("file://", ""))
        
        return IDEResponse(
            id=request.id,
            result={
                "capabilities": {
                    "textDocumentSync": {
                        "openClose": True,
                        "change": 2,  # Incremental
                        "save": True
                    },
                    "codeActionProvider": self.plugin_config.enable_code_actions,
                    "codeLensProvider": {"resolveProvider": False},
                    "completionProvider": {
                        "triggerCharacters": [".", " ", "("],
                        "resolveProvider": True
                    },
                    "inlayHintProvider": self.plugin_config.enable_inlay_hints,
                    "workspace": {
                        "workspaceFolders": {"supported": True, "changeNotifications": True}
                    }
                },
                "serverInfo": {
                    "name": "AI Development Framework",
                    "version": self.config.version
                }
            }
        )
    
    async def _handle_initialized(self, request: IDERequest) -> IDEResponse:
        """Handle initialized notification."""
        logger.info("IDE plugin initialized")
        
        # Register workspace files
        if self.plugin_config.workspace_path:
            await self._scan_workspace()
        
        return IDEResponse(id=request.id, result={})
    
    async def _handle_shutdown(self, request: IDERequest) -> IDEResponse:
        """Handle shutdown request."""
        logger.info("Shutting down IDE plugin")
        self.request_shutdown()
        return IDEResponse(id=request.id, result={})
    
    async def _handle_exit(self, request: IDERequest) -> IDEResponse:
        """Handle exit notification."""
        logger.info("IDE plugin exit")
        return IDEResponse(id=request.id, result={})
    
    # ============================================================
    # WORKSPACE HANDLERS
    # ============================================================
    
    async def _handle_config_change(self, request: IDERequest) -> IDEResponse:
        """Handle configuration change."""
        settings = request.params.get("settings", {})
        ai_settings = settings.get("ai-dev", {})
        
        # Update configuration
        if "enableAnalysis" in ai_settings:
            self.plugin_config.enable_analysis = ai_settings["enableAnalysis"]
        if "enableGeneration" in ai_settings:
            self.plugin_config.enable_generation = ai_settings["enableGeneration"]
        if "debounceMs" in ai_settings:
            self.plugin_config.debounce_ms = ai_settings["debounceMs"]
        
        logger.debug(f"Configuration updated: {ai_settings}")
        return IDEResponse(id=request.id, result={})
    
    async def _handle_workspace_change(self, request: IDERequest) -> IDEResponse:
        """Handle workspace folders change."""
        logger.info("Workspace folders changed")
        await self._scan_workspace()
        return IDEResponse(id=request.id, result={})
    
    async def _handle_file_change(self, request: IDERequest) -> IDEResponse:
        """Handle watched file change."""
        changes = request.params.get("changes", [])
        for change in changes:
            uri = change.get("uri", "")
            file_type = change.get("type", 2)  # 1=created, 2=changed, 3=deleted
            
            file_path = self._uri_to_path(uri)
            
            if file_type == 1:  # Created
                self._workspace_files.add(file_path)
            elif file_type == 3:  # Deleted
                self._workspace_files.discard(file_path)
                if file_path in self._diagnostics:
                    del self._diagnostics[file_path]
        
        return IDEResponse(id=request.id, result={})
    
    # ============================================================
    # DOCUMENT HANDLERS
    # ============================================================
    
    async def _handle_document_open(self, request: IDERequest) -> IDEResponse:
        """Handle document open."""
        uri = request.params["textDocument"]["uri"]
        content = request.params["textDocument"]["text"]
        file_path = self._uri_to_path(uri)
        
        self._workspace_files.add(file_path)
        
        if self.plugin_config.enable_analysis:
            await self._analyze_document(file_path, content)
        
        return IDEResponse(id=request.id, result={})
    
    async def _handle_document_change(self, request: IDERequest) -> IDEResponse:
        """Handle document change."""
        uri = request.params["textDocument"]["uri"]
        changes = request.params.get("contentChanges", [])
        file_path = self._uri_to_path(uri)
        
        if changes and self.plugin_config.analysis_on_change:
            # Debounce analysis
            await asyncio.sleep(self.plugin_config.debounce_ms / 1000)
            
            content = changes[-1].get("text", "")
            if content:
                await self._analyze_document(file_path, content)
        
        return IDEResponse(id=request.id, result={})
    
    async def _handle_document_close(self, request: IDERequest) -> IDEResponse:
        """Handle document close."""
        uri = request.params["textDocument"]["uri"]
        file_path = self._uri_to_path(uri)
        
        # Clear diagnostics for closed file
        if file_path in self._diagnostics:
            del self._diagnostics[file_path]
            await self._publish_diagnostics(file_path, [])
        
        return IDEResponse(id=request.id, result={})
    
    async def _handle_document_save(self, request: IDERequest) -> IDEResponse:
        """Handle document save."""
        uri = request.params["textDocument"]["uri"]
        content = request.params.get("text", "")
        file_path = self._uri_to_path(uri)
        
        if self.plugin_config.analysis_on_save:
            await self._analyze_document(file_path, content)
        
        return IDEResponse(id=request.id, result={})
    
    # ============================================================
    # AI DEVELOPMENT HANDLERS
    # ============================================================
    
    async def _handle_analyze(self, request: IDERequest) -> IDEResponse:
        """Handle analyze request."""
        file_path = request.params.get("file")
        code = request.params.get("code")
        analysis_type = request.params.get("type", "all")
        
        if not file_path and not code:
            return IDEResponse(id=request.id, error="Either file or code must be provided")
        
        result = await self._run_analysis(file_path, code, analysis_type)
        
        return IDEResponse(
            id=request.id,
            result=result,
            diagnostics=self._convert_to_diagnostics(result)
        )
    
    async def _handle_generate(self, request: IDERequest) -> IDEResponse:
        """Handle generate request."""
        gen_type = request.params.get("type", "class")
        name = request.params.get("name")
        description = request.params.get("description")
        context = request.params.get("context", {})
        
        if not name:
            return IDEResponse(id=request.id, error="Name is required")
        
        result = await self.run_workflow_async(
            "generation_workflow",
            type=gen_type,
            name=name,
            description=description,
            **context
        )
        
        return IDEResponse(
            id=request.id,
            result={
                "code": result.get("code"),
                "file_path": result.get("file_path"),
                "imports": result.get("imports", [])
            }
        )
    
    async def _handle_refine(self, request: IDERequest) -> IDEResponse:
        """Handle refine request."""
        code = request.params.get("code")
        file_path = request.params.get("file")
        strategy = request.params.get("strategy", "fix_errors_first")
        
        if not code and not file_path:
            return IDEResponse(id=request.id, error="Either code or file must be provided")
        
        if file_path:
            code = Path(file_path).read_text()
        
        result = await self.run_workflow_async(
            "refinement_workflow",
            code=code,
            file_path=file_path,
            strategy=strategy
        )
        
        return IDEResponse(
            id=request.id,
            result={
                "refined_code": result.get("code"),
                "changes": result.get("changes", []),
                "quality_score": result.get("quality_score")
            }
        )
    
    async def _handle_complete(self, request: IDERequest) -> IDEResponse:
        """Handle code completion request."""
        code = request.params.get("code", "")
        position = request.params.get("position", {})
        file_path = request.params.get("file")
        
        # Get context around cursor
        line = position.get("line", 0)
        character = position.get("character", 0)
        context = self._extract_context(code, line, character)
        
        result = await self._get_completions(context, file_path)
        
        return IDEResponse(
            id=request.id,
            result={"items": result}
        )
    
    async def _handle_explain(self, request: IDERequest) -> IDEResponse:
        """Handle explain code request."""
        code = request.params.get("code")
        
        if not code:
            return IDEResponse(id=request.id, error="Code is required")
        
        result = await self.run_workflow_async(
            "analysis_workflow",
            type="explain",
            code=code
        )
        
        return IDEResponse(
            id=request.id,
            result={
                "explanation": result.get("explanation"),
                "complexity": result.get("complexity"),
                "suggestions": result.get("suggestions", [])
            }
        )
    
    async def _handle_fix(self, request: IDERequest) -> IDEResponse:
        """Handle fix code request."""
        code = request.params.get("code")
        issue = request.params.get("issue")
        
        if not code:
            return IDEResponse(id=request.id, error="Code is required")
        
        result = await self.run_workflow_async(
            "refinement_workflow",
            type="fix",
            code=code,
            target_issue=issue
        )
        
        return IDEResponse(
            id=request.id,
            result={
                "fixed_code": result.get("code"),
                "explanation": result.get("explanation")
            }
        )
    
    async def _handle_refactor(self, request: IDERequest) -> IDEResponse:
        """Handle refactor request."""
        code = request.params.get("code")
        refactor_type = request.params.get("refactor_type", "extract_method")
        selection = request.params.get("selection")
        
        if not code:
            return IDEResponse(id=request.id, error="Code is required")
        
        result = await self.run_workflow_async(
            "refinement_workflow",
            type="refactor",
            code=code,
            refactor_type=refactor_type,
            selection=selection
        )
        
        return IDEResponse(
            id=request.id,
            result={
                "refactored_code": result.get("code"),
                "changes": result.get("changes", [])
            }
        )
    
    async def _handle_generate_test(self, request: IDERequest) -> IDEResponse:
        """Handle generate test request."""
        code = request.params.get("code")
        file_path = request.params.get("file")
        
        if not code and not file_path:
            return IDEResponse(id=request.id, error="Either code or file must be provided")
        
        result = await self.run_workflow_async(
            "generation_workflow",
            type="test",
            code=code,
            target_path=file_path
        )
        
        return IDEResponse(
            id=request.id,
            result={
                "test_code": result.get("code"),
                "test_file": result.get("file_path")
            }
        )
    
    async def _handle_generate_docstring(self, request: IDERequest) -> IDEResponse:
        """Handle generate docstring request."""
        code = request.params.get("code")
        style = request.params.get("style", "google")
        
        if not code:
            return IDEResponse(id=request.id, error="Code is required")
        
        result = await self.run_workflow_async(
            "generation_workflow",
            type="docstring",
            code=code,
            style=style
        )
        
        return IDEResponse(
            id=request.id,
            result={
                "docstring": result.get("docstring"),
                "code_with_docstring": result.get("code")
            }
        )
    
    async def _handle_review(self, request: IDERequest) -> IDEResponse:
        """Handle code review request."""
        code = request.params.get("code")
        file_path = request.params.get("file")
        
        if not code and not file_path:
            return IDEResponse(id=request.id, error="Either code or file must be provided")
        
        result = await self._analyze_document(file_path, code, include_suggestions=True)
        
        return IDEResponse(
            id=request.id,
            result={
                "issues": result.get("issues", []),
                "suggestions": result.get("suggestions", []),
                "quality_score": result.get("quality_score")
            }
        )
    
    # ============================================================
    # LSP FEATURE HANDLERS
    # ============================================================
    
    async def _handle_code_action(self, request: IDERequest) -> IDEResponse:
        """Handle code action request."""
        uri = request.params["textDocument"]["uri"]
        range_info = request.params["range"]
        context = request.params.get("context", {})
        
        file_path = self._uri_to_path(uri)
        diagnostics = context.get("diagnostics", [])
        
        actions = []
        
        # Generate fix actions for each diagnostic
        for diag in diagnostics:
            if diag.get("source") == "ai-dev":
                actions.append(CodeAction(
                    title=f"Fix: {diag.get('message', '')[:50]}",
                    kind="quickfix",
                    file=file_path,
                    line=diag["range"]["start"]["line"],
                    command={
                        "title": "AI Fix",
                        "command": "ai-dev.fix",
                        "arguments": [file_path, diag]
                    }
                ).dict())
        
        # Add refactoring actions
        actions.append(CodeAction(
            title="✨ AI: Refactor this code",
            kind="refactor",
            file=file_path,
            line=range_info["start"]["line"],
            command={
                "title": "AI Refactor",
                "command": "ai-dev.refactor",
                "arguments": [file_path, range_info]
            }
        ).dict())
        
        actions.append(CodeAction(
            title="📝 AI: Generate docstring",
            kind="refactor",
            file=file_path,
            line=range_info["start"]["line"],
            command={
                "title": "Generate Docstring",
                "command": "ai-dev.generateDocstring",
                "arguments": [file_path, range_info]
            }
        ).dict())
        
        actions.append(CodeAction(
            title="🧪 AI: Generate tests",
            kind="refactor",
            file=file_path,
            line=range_info["start"]["line"],
            command={
                "title": "Generate Tests",
                "command": "ai-dev.generateTests",
                "arguments": [file_path]
            }
        ).dict())
        
        return IDEResponse(id=request.id, result=actions)
    
    async def _handle_code_lens(self, request: IDERequest) -> IDEResponse:
        """Handle code lens request."""
        uri = request.params["textDocument"]["uri"]
        file_path = self._uri_to_path(uri)
        
        lenses = []
        
        # Add complexity lens for functions
        if file_path in self._diagnostics:
            diagnostics = self._diagnostics[file_path]
            for diag in diagnostics:
                if diag.code == "COMPLEXITY_HIGH":
                    lenses.append({
                        "range": {
                            "start": {"line": diag.line, "character": 0},
                            "end": {"line": diag.line, "character": 0}
                        },
                        "command": {
                            "title": f"🔍 Complexity: {diag.message}",
                            "command": "ai-dev.showComplexity",
                            "arguments": [file_path, diag.line]
                        },
                        "data": diag.dict()
                    })
        
        # Add reference lens
        lenses.append({
            "range": {
                "start": {"line": 0, "character": 0},
                "end": {"line": 0, "character": 0}
            },
            "command": {
                "title": "📊 AI: Analyze this file",
                "command": "ai-dev.analyzeFile",
                "arguments": [file_path]
            }
        })
        
        return IDEResponse(id=request.id, result=lenses)
    
    async def _handle_inlay_hint(self, request: IDERequest) -> IDEResponse:
        """Handle inlay hint request."""
        uri = request.params["textDocument"]["uri"]
        range_info = request.params.get("range")
        
        hints = []
        
        # Add type hints for variables without annotations
        # This would parse the AST and suggest types
        
        return IDEResponse(id=request.id, result=hints)
    
    async def _handle_completion(self, request: IDERequest) -> IDEResponse:
        """Handle completion request."""
        uri = request.params["textDocument"]["uri"]
        position = request.params["position"]
        
        # Delegate to AI complete handler
        return await self._handle_complete(request)
    
    # ============================================================
    # CORE FUNCTIONALITY
    # ============================================================
    
    async def _scan_workspace(self):
        """Scan workspace for Python files."""
        if not self.plugin_config.workspace_path:
            return
        
        logger.info(f"Scanning workspace: {self.plugin_config.workspace_path}")
        
        for py_file in self.plugin_config.workspace_path.rglob("*.py"):
            if self._should_include_file(py_file):
                self._workspace_files.add(str(py_file))
        
        logger.info(f"Found {len(self._workspace_files)} Python files")
    
    def _should_include_file(self, file_path: Path) -> bool:
        """Check if file should be included."""
        exclude_patterns = ["__pycache__", ".git", ".venv", "venv", "dist", "build", ".pytest_cache"]
        path_str = str(file_path)
        return not any(p in path_str for p in exclude_patterns)
    
    async def _analyze_document(self, file_path: str, content: str, 
                                 include_suggestions: bool = True) -> Dict[str, Any]:
        """Analyze a document and publish diagnostics."""
        if not self.plugin_config.enable_analysis:
            return {}
        
        # Skip large files
        if len(content) > self.plugin_config.max_file_size_mb * 1024 * 1024:
            logger.warning(f"Skipping large file: {file_path}")
            return {}
        
        try:
            result = await self.run_workflow_async(
                "analysis_workflow",
                path=file_path,
                code=content,
                include_suggestions=include_suggestions
            )
            
            # Convert to diagnostics
            diagnostics = self._convert_to_diagnostics(result)
            self._diagnostics[file_path] = diagnostics
            
            # Publish to IDE
            await self._publish_diagnostics(file_path, diagnostics)
            
            return result
            
        except Exception as e:
            logger.error(f"Analysis failed for {file_path}: {e}")
            return {"error": str(e)}
    
    def _convert_to_diagnostics(self, analysis_result: Dict[str, Any]) -> List[Diagnostic]:
        """Convert analysis result to diagnostics."""
        diagnostics = []
        
        # Convert issues to diagnostics
        for issue in analysis_result.get("issues", []):
            severity = issue.get("severity", "warning")
            if severity == "error":
                diag_severity = 1  # Error
            elif severity == "warning":
                diag_severity = 2  # Warning
            elif severity == "info":
                diag_severity = 3  # Information
            else:
                diag_severity = 4  # Hint
            
            diagnostics.append(Diagnostic(
                file=analysis_result.get("file", ""),
                line=issue.get("line", 0),
                column=issue.get("column", 0),
                severity=diag_severity,
                code=issue.get("code", "unknown"),
                message=issue.get("message", ""),
                suggestion=issue.get("suggestion"),
                fix_available=issue.get("fixable", False)
            ))
        
        # Convert complexity issues
        for func in analysis_result.get("complex_functions", []):
            diagnostics.append(Diagnostic(
                file=analysis_result.get("file", ""),
                line=func.get("line", 0),
                column=0,
                severity=2,  # Warning
                code="COMPLEXITY_HIGH",
                message=f"High cyclomatic complexity ({func.get('complexity', 0)})",
                suggestion="Consider breaking down this function"
            ))
        
        return diagnostics
    
    async def _publish_diagnostics(self, file_path: str, diagnostics: List[Diagnostic]):
        """Publish diagnostics to IDE."""
        if not self.plugin_config.enable_diagnostics:
            return
        
        notification = IDEMessage(
            type=MessageType.NOTIFICATION,
            method="textDocument/publishDiagnostics",
            params={
                "uri": self._path_to_uri(file_path),
                "diagnostics": [
                    {
                        "range": {
                            "start": {"line": d.line, "character": d.column},
                            "end": {"line": d.line, "character": d.column + 1}
                        },
                        "severity": d.severity,
                        "code": d.code,
                        "source": d.source,
                        "message": d.message,
                        "data": {"suggestion": d.suggestion} if d.suggestion else {}
                    }
                    for d in diagnostics
                ]
            }
        )
        
        await self._send_message(notification)
    
    async def _run_analysis(self, file_path: Optional[str], code: Optional[str],
                            analysis_type: str) -> Dict[str, Any]:
        """Run analysis workflow."""
        return await self.run_workflow_async(
            "analysis_workflow",
            path=file_path,
            code=code,
            analysis_type=analysis_type
        )
    
    async def _get_completions(self, context: str, file_path: Optional[str]) -> List[Dict[str, Any]]:
        """Get code completions."""
        if not self.plugin_config.enable_completion:
            return []
        
        try:
            result = await asyncio.wait_for(
                self.run_workflow_async(
                    "generation_workflow",
                    type="completion",
                    context=context,
                    file_path=file_path
                ),
                timeout=self.plugin_config.completion_timeout_ms / 1000
            )
            
            return result.get("completions", [])
            
        except asyncio.TimeoutError:
            return []
        except Exception as e:
            logger.debug(f"Completion failed: {e}")
            return []
    
    def _extract_context(self, code: str, line: int, character: int) -> str:
        """Extract context around cursor for completion."""
        lines = code.split("\n")
        if line >= len(lines):
            return code
        
        # Get lines before and after cursor
        start = max(0, line - self.plugin_config.max_context_lines)
        end = min(len(lines), line + self.plugin_config.max_context_lines)
        
        context_lines = lines[start:end]
        return "\n".join(context_lines)
    
    # ============================================================
    # PROTOCOL COMMUNICATION
    # ============================================================
    
    async def execute_async(self) -> EntryPointResult:
        """Execute the IDE plugin service."""
        if self.plugin_config.protocol == ProtocolType.STDIO:
            return await self._run_stdio()
        elif self.plugin_config.protocol == ProtocolType.HTTP:
            return await self._run_http()
        elif self.plugin_config.protocol == ProtocolType.WEBSOCKET:
            return await self._run_websocket()
        else:
            return self.create_error_result(f"Unsupported protocol: {self.plugin_config.protocol}")
    
    async def _run_stdio(self) -> EntryPointResult:
        """Run using stdio protocol (LSP style)."""
        logger.info("Starting stdio server")
        
        loop = asyncio.get_event_loop()
        reader = asyncio.StreamReader()
        protocol = asyncio.StreamReaderProtocol(reader)
        
        await loop.connect_read_pipe(lambda: protocol, sys.stdin)
        writer_transport, writer_protocol = await loop.connect_write_pipe(
            asyncio.streams.FlowControlMixin, sys.stdout
        )
        writer = asyncio.StreamWriter(writer_transport, writer_protocol, reader, loop)
        
        self._reader = reader
        self._writer = writer
        
        # Read messages
        content_length = 0
        headers = {}
        
        while not self.is_shutdown_requested:
            try:
                # Read headers
                line = await reader.readline()
                line = line.decode().strip()
                
                if not line:
                    # End of headers, read content
                    content = await reader.readexactly(content_length)
                    message = json.loads(content.decode())
                    
                    # Process message
                    response = await self._process_message(message)
                    
                    # Send response if any
                    if response:
                        await self._send_message(response)
                    
                    content_length = 0
                    headers = {}
                else:
                    # Parse header
                    key, value = line.split(":", 1)
                    headers[key.strip().lower()] = value.strip()
                    if key.strip().lower() == "content-length":
                        content_length = int(value.strip())
                        
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error processing message: {e}")
        
        writer.close()
        await writer.wait_closed()
        
        return self.create_success_result("Stdio server stopped")
    
    async def _run_http(self) -> EntryPointResult:
        """Run using HTTP protocol."""
        from aiohttp import web
        
        logger.info(f"Starting HTTP server on {self.plugin_config.host}:{self.plugin_config.port}")
        
        async def handle_request(request: web.Request) -> web.Response:
            """Handle HTTP request."""
            try:
                body = await request.json()
                message = IDEMessage(**body)
                response = await self._process_message(message.dict())
                return web.json_response(response.dict())
            except Exception as e:
                logger.error(f"HTTP error: {e}")
                return web.json_response({"error": str(e)}, status=500)
        
        app = web.Application()
        app.router.add_post("/", handle_request)
        app.router.add_get("/health", lambda r: web.json_response({"status": "healthy"}))
        
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, self.plugin_config.host, self.plugin_config.port)
        await site.start()
        
        while not self.is_shutdown_requested:
            await asyncio.sleep(1)
        
        await runner.cleanup()
        
        return self.create_success_result("HTTP server stopped")
    
    async def _run_websocket(self) -> EntryPointResult:
        """Run using WebSocket protocol."""
        from aiohttp import web
        
        logger.info(f"Starting WebSocket server on {self.plugin_config.host}:{self.plugin_config.port}")
        
        async def handle_websocket(request: web.Request) -> web.WebSocketResponse:
            """Handle WebSocket connection."""
            ws = web.WebSocketResponse()
            await ws.prepare(request)
            
            logger.info("WebSocket client connected")
            
            async for msg in ws:
                if msg.type == web.WSMsgType.TEXT:
                    try:
                        data = json.loads(msg.data)
                        message = IDEMessage(**data)
                        response = await self._process_message(message.dict())
                        
                        if response:
                            await ws.send_json(response.dict())
                            
                    except Exception as e:
                        logger.error(f"WebSocket error: {e}")
                        await ws.send_json({"error": str(e)})
                
                elif msg.type == web.WSMsgType.ERROR:
                    logger.error(f"WebSocket error: {ws.exception()}")
            
            logger.info("WebSocket client disconnected")
            return ws
        
        app = web.Application()
        app.router.add_get("/", handle_websocket)
        app.router.add_get("/health", lambda r: web.json_response({"status": "healthy"}))
        
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, self.plugin_config.host, self.plugin_config.port)
        await site.start()
        
        while not self.is_shutdown_requested:
            await asyncio.sleep(1)
        
        await runner.cleanup()
        
        return self.create_success_result("WebSocket server stopped")
    
    async def _process_message(self, message_data: Dict[str, Any]) -> Optional[IDEMessage]:
        """Process an incoming message."""
        message = IDEMessage(**message_data)
        
        if message.type == MessageType.REQUEST:
            request = IDERequest(
                id=message.id,
                method=message.method,
                params=message.params
            )
            
            handler = self._handlers.get(message.method)
            if handler:
                try:
                    response = await handler(request)
                    return IDEMessage(
                        id=message.id,
                        type=MessageType.RESPONSE,
                        method=message.method,
                        result=response.result,
                        error={"message": response.error} if response.error else None
                    )
                except Exception as e:
                    logger.error(f"Handler error for {message.method}: {e}")
                    logger.debug(traceback.format_exc())
                    return IDEMessage(
                        id=message.id,
                        type=MessageType.RESPONSE,
                        method=message.method,
                        error={"message": str(e)}
                    )
            else:
                return IDEMessage(
                    id=message.id,
                    type=MessageType.RESPONSE,
                    method=message.method,
                    error={"message": f"Unknown method: {message.method}"}
                )
        
        elif message.type == MessageType.NOTIFICATION:
            handler = self._handlers.get(message.method)
            if handler:
                try:
                    await handler(IDERequest(
                        id=message.id or "notification",
                        method=message.method,
                        params=message.params
                    ))
                except Exception as e:
                    logger.error(f"Notification handler error for {message.method}: {e}")
        
        return None
    
    async def _send_message(self, message: IDEMessage):
        """Send a message to the IDE."""
        if self.plugin_config.protocol == ProtocolType.STDIO:
            content = json.dumps(message.dict(exclude_none=True))
            content_length = len(content)
            
            header = f"Content-Length: {content_length}\r\n\r\n"
            self._writer.write(header.encode())
            self._writer.write(content.encode())
            await self._writer.drain()
    
    # ============================================================
    # UTILITY METHODS
    # ============================================================
    
    def _uri_to_path(self, uri: str) -> str:
        """Convert file URI to path."""
        if uri.startswith("file://"):
            return uri[7:]
        return uri
    
    def _path_to_uri(self, path: str) -> str:
        """Convert path to file URI."""
        return f"file://{path}"
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check."""
        return {
            "status": "healthy",
            "protocol": self.plugin_config.protocol.value,
            "workspace": str(self.plugin_config.workspace_path) if self.plugin_config.workspace_path else None,
            "files_tracked": len(self._workspace_files),
            "handlers_registered": len(self._handlers),
            "timestamp": datetime.now().isoformat()
        }


# ============================================================
# CLI ENTRY POINT
# ============================================================

def main():
    """Main entry point for IDE plugin backend."""
    import sys
    
    parser = argparse.ArgumentParser(description="IDE Plugin Backend for AI Development Framework")
    parser.add_argument("--protocol", choices=["stdio", "http", "websocket"], default="stdio")
    parser.add_argument("--host", default="127.0.0.1", help="Host for HTTP/WebSocket")
    parser.add_argument("--port", type=int, default=9876, help="Port for HTTP/WebSocket")
    parser.add_argument("--workspace", type=Path, help="Workspace path")
    parser.add_argument("--no-analysis", action="store_true", help="Disable real-time analysis")
    parser.add_argument("--no-generation", action="store_true", help="Disable code generation")
    parser.add_argument("--verbose", "-v", action="count", default=0)
    
    args = parser.parse_args()
    
    config = IDEPluginConfig(
        protocol=ProtocolType(args.protocol),
        host=args.host,
        port=args.port,
        workspace_path=args.workspace,
        enable_analysis=not args.no_analysis,
        enable_generation=not args.no_generation
    )
    
    plugin = IDEPluginEntryPoint(config)
    
    try:
        asyncio.run(plugin.execute_async())
    except KeyboardInterrupt:
        logger.info("Shutdown requested")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()