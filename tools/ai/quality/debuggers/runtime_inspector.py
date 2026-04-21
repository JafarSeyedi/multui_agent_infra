#!/usr/bin/env python3
"""
Runtime Inspector - Inspects Python runtime state, variables, and execution flow.

Part of the Quality tools (quality/debuggers/runtime_inspector.py)

This runtime_inspector.py provides:

1. Real-Time Variable Inspection - Tracks variable values, types, and mutations
2. Execution Tracing - Captures function calls, returns, exceptions, line execution
3. Breakpoint Support - Conditional breakpoints with hit counts
4. Watchpoint Support - Watch variable reads/writes
5. Runtime Snapshots - Periodic or manual state snapshots
6. Memory Tracking - Integration with tracemalloc
7. Call Stack Analysis - Full call stack with local variables
8. Hot Path Detection - Identifies frequently executed paths
9. Memory Leak Detection - Detects growing memory and persistent large objects
10. Variable Lifetime Analysis - Tracks when variables are created/destroyed
11. Async Support - Inspect async coroutines
12. Context Manager & Decorator - Easy integration with existing code
13. Comprehensive Reporting - JSON and Markdown formats

The runtime inspector provides deep visibility into Python execution, helping debug complex issues and optimize performance.
"""

import sys
import ast
import inspect
import threading
import asyncio
import tracemalloc
import linecache
from pathlib import Path
from typing import Dict, List, Set, Optional, Any, Tuple, Union, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from collections import defaultdict
import pprint

from ....shared.logger import get_logger
from ....shared.state_manager import StateManager

logger = get_logger(__name__)


# ============================================================
# ENUMS AND CONSTANTS
# ============================================================

class VariableScope(str, Enum):
    """Scope of a variable."""
    LOCAL = "local"
    GLOBAL = "global"
    ENCLOSING = "enclosing"
    BUILTIN = "builtin"
    INSTANCE = "instance"
    CLASS = "class"


class VariableState(str, Enum):
    """State of a variable."""
    DEFINED = "defined"
    UNDEFINED = "undefined"
    MUTATED = "mutated"
    DELETED = "deleted"
    UNUSED = "unused"


class ExecutionState(str, Enum):
    """State of execution."""
    NOT_STARTED = "not_started"
    RUNNING = "running"
    PAUSED = "paused"
    BREAKPOINT_HIT = "breakpoint_hit"
    EXCEPTION = "exception"
    COMPLETED = "completed"
    TERMINATED = "terminated"


class TraceEvent(str, Enum):
    """Type of trace event."""
    CALL = "call"
    RETURN = "return"
    EXCEPTION = "exception"
    LINE = "line"
    OPCODE = "opcode"
    VARIABLE_ACCESS = "variable_access"
    VARIABLE_CHANGE = "variable_change"
    MEMORY_ALLOCATION = "memory_allocation"


# ============================================================
# DATA MODELS
# ============================================================

@dataclass
class VariableInfo:
    """Information about a variable."""
    name: str
    value: Any
    type_name: str
    scope: VariableScope
    state: VariableState = VariableState.DEFINED
    defined_at: Optional[Tuple[str, int]] = None
    last_accessed: Optional[datetime] = None
    last_modified: Optional[datetime] = None
    access_count: int = 0
    modification_count: int = 0
    size_bytes: int = 0
    is_callable: bool = False
    is_iterable: bool = False
    is_context_manager: bool = False
    children: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.type_name:
            self.type_name = type(self.value).__name__
        self.is_callable = callable(self.value)
        self.is_iterable = hasattr(self.value, '__iter__') and not isinstance(self.value, (str, bytes))
        self.is_context_manager = hasattr(self.value, '__enter__') and hasattr(self.value, '__exit__')
        self.size_bytes = self._estimate_size()
    
    def _estimate_size(self) -> int:
        """Estimate memory size of value."""
        try:
            if hasattr(self.value, '__sizeof__'):
                return self.value.__sizeof__()
        except Exception:
            pass
        return sys.getsizeof(self.value)


@dataclass
class CallFrame:
    """Information about a call frame."""
    frame_id: str
    function_name: str
    file_path: str
    line_number: int
    depth: int
    locals: Dict[str, VariableInfo] = field(default_factory=dict)
    globals: Dict[str, VariableInfo] = field(default_factory=dict)
    arguments: Dict[str, Any] = field(default_factory=dict)
    return_value: Optional[Any] = None
    exception: Optional[Exception] = None
    execution_time_ms: float = 0.0
    memory_delta_bytes: int = 0
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Breakpoint:
    """A breakpoint in code."""
    id: str
    file_path: str
    line_number: int
    condition: Optional[str] = None
    enabled: bool = True
    temporary: bool = False
    hit_count: int = 0
    max_hits: Optional[int] = None
    ignore_count: int = 0
    actions: List[Callable] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Watchpoint:
    """A watchpoint on a variable."""
    id: str
    variable_name: str
    condition: Optional[str] = None
    watch_read: bool = True
    watch_write: bool = True
    enabled: bool = True
    hit_count: int = 0
    old_value: Optional[Any] = None
    new_value: Optional[Any] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TraceEvent_:
    """A trace event."""
    event_type: TraceEvent
    frame: CallFrame
    line_number: Optional[int] = None
    variable_name: Optional[str] = None
    old_value: Optional[Any] = None
    new_value: Optional[Any] = None
    exception: Optional[Exception] = None
    memory_allocated: int = 0
    memory_freed: int = 0
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RuntimeSnapshot:
    """A snapshot of runtime state."""
    snapshot_id: str
    timestamp: datetime = field(default_factory=datetime.now)
    execution_state: ExecutionState = ExecutionState.RUNNING
    current_frame: Optional[CallFrame] = None
    call_stack: List[CallFrame] = field(default_factory=list)
    all_variables: Dict[str, VariableInfo] = field(default_factory=dict)
    memory_usage_mb: float = 0.0
    cpu_time_ms: float = 0.0
    thread_count: int = 0
    open_files: List[str] = field(default_factory=list)
    open_connections: List[str] = field(default_factory=list)
    trace_events: List[TraceEvent_] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RuntimeInspectionReport:
    """Complete runtime inspection report."""
    inspected_at: datetime = field(default_factory=datetime.now)
    target_name: str = ""
    execution_duration_ms: float = 0.0
    
    # Snapshots
    snapshots: List[RuntimeSnapshot] = field(default_factory=list)
    initial_snapshot: Optional[RuntimeSnapshot] = None
    final_snapshot: Optional[RuntimeSnapshot] = None
    
    # Call analysis
    call_graph: Dict[str, List[str]] = field(default_factory=dict)
    hot_paths: List[List[str]] = field(default_factory=list)
    function_timings: Dict[str, float] = field(default_factory=dict)
    
    # Memory analysis
    memory_peaks: List[Tuple[datetime, float]] = field(default_factory=list)
    memory_leaks: List[Dict[str, Any]] = field(default_factory=list)
    large_objects: List[VariableInfo] = field(default_factory=list)
    
    # Variable analysis
    variable_lifetimes: Dict[str, Tuple[datetime, datetime]] = field(default_factory=dict)
    mutated_variables: List[str] = field(default_factory=list)
    unused_variables: List[str] = field(default_factory=list)
    
    # Issues detected
    issues: List[Dict[str, Any]] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    
    summary: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RuntimeInspectorConfig:
    """Configuration for runtime inspector."""
    project_root: Path
    trace_lines: bool = True
    trace_calls: bool = True
    trace_returns: bool = True
    trace_exceptions: bool = True
    trace_variables: bool = True
    trace_memory: bool = True
    max_trace_events: int = 10000
    max_snapshots: int = 100
    snapshot_interval_ms: int = 100
    max_variable_depth: int = 3
    max_string_length: int = 500
    max_collection_length: int = 100
    redact_sensitive: bool = True
    sensitive_patterns: List[str] = field(default_factory=lambda: [
        "password", "secret", "token", "key", "auth", "credential", "private"
    ])
    ignore_patterns: List[str] = field(default_factory=lambda: [
        "__pycache__", ".git", ".venv", "venv", "site-packages"
    ])
    include_builtins: bool = False
    include_stdlib: bool = False


# ============================================================
# VARIABLE INSPECTOR
# ============================================================

class VariableInspector:
    """Inspect and track variables at runtime."""
    
    def __init__(self, config: RuntimeInspectorConfig):
        self.config = config
        self.variables: Dict[str, VariableInfo] = {}
        self.variable_history: Dict[str, List[Tuple[datetime, Any]]] = defaultdict(list)
        self.access_counts: Dict[str, int] = defaultdict(int)
        self.modification_counts: Dict[str, int] = defaultdict(int)
    
    def inspect_frame(self, frame: inspect.FrameInfo) -> Dict[str, VariableInfo]:
        """Inspect variables in a frame."""
        variables = {}
        
        if frame.frame is None:
            return variables
        
        # Inspect locals
        for name, value in frame.frame.f_locals.items():
            if self._should_inspect_variable(name, value):
                var_info = self._create_variable_info(name, value, VariableScope.LOCAL)
                variables[name] = var_info
                self._track_variable(name, value)
        
        # Inspect globals (limited)
        if self.config.include_builtins:
            for name, value in frame.frame.f_globals.items():
                if name not in variables and self._should_inspect_variable(name, value):
                    var_info = self._create_variable_info(name, value, VariableScope.GLOBAL)
                    variables[name] = var_info
        
        return variables
    
    def _should_inspect_variable(self, name: str, value: Any) -> bool:
        """Check if variable should be inspected."""
        # Skip private/dunder unless configured
        if name.startswith('__') and name.endswith('__'):
            return False
        
        # Skip modules and classes unless configured
        if inspect.ismodule(value) or inspect.isclass(value):
            return False
        
        # Redact sensitive values
        if self.config.redact_sensitive:
            name_lower = name.lower()
            for pattern in self.config.sensitive_patterns:
                if pattern in name_lower:
                    return False
        
        return True
    
    def _create_variable_info(self, name: str, value: Any, 
                               scope: VariableScope) -> VariableInfo:
        """Create VariableInfo from value."""
        type_name = type(value).__name__
        
        # Format value for display
        formatted_value = self._format_value(value)
        
        info = VariableInfo(
            name=name,
            value=formatted_value,
            type_name=type_name,
            scope=scope
        )
        
        # Track history
        if name in self.variables:
            old_info = self.variables[name]
            if old_info.value != formatted_value:
                info.state = VariableState.MUTATED
                info.modification_count = old_info.modification_count + 1
            info.access_count = old_info.access_count
            info.last_accessed = datetime.now()
        
        self.variables[name] = info
        
        return info
    
    def _format_value(self, value: Any) -> Any:
        """Format value for display with depth limit."""
        return self._format_value_recursive(value, depth=0)
    
    def _format_value_recursive(self, value: Any, depth: int) -> Any:
        """Recursively format value."""
        if depth > self.config.max_variable_depth:
            return f"<max depth {self.config.max_variable_depth}>"
        
        if value is None:
            return None
        
        if isinstance(value, (int, float, bool, type(None))):
            return value
        
        if isinstance(value, str):
            if len(value) > self.config.max_string_length:
                return value[:self.config.max_string_length] + "..."
            return value
        
        if isinstance(value, (list, tuple, set)):
            if len(value) > self.config.max_collection_length:
                formatted = [self._format_value_recursive(v, depth + 1) 
                            for v in list(value)[:self.config.max_collection_length]]
                formatted.append(f"... ({len(value)} total)")
                return formatted
            return [self._format_value_recursive(v, depth + 1) for v in value]
        
        if isinstance(value, dict):
            if len(value) > self.config.max_collection_length:
                formatted = {}
                for i, (k, v) in enumerate(value.items()):
                    if i >= self.config.max_collection_length:
                        formatted["..."] = f"({len(value)} total)"
                        break
                    formatted[str(k)] = self._format_value_recursive(v, depth + 1)
                return formatted
            return {str(k): self._format_value_recursive(v, depth + 1) 
                    for k, v in value.items()}
        
        # Default to string representation
        return str(value)[:self.config.max_string_length]
    
    def _track_variable(self, name: str, value: Any):
        """Track variable changes over time."""
        self.variable_history[name].append((datetime.now(), value))
        
        # Limit history size
        if len(self.variable_history[name]) > 100:
            self.variable_history[name] = self.variable_history[name][-100:]
    
    def get_variable_history(self, name: str) -> List[Tuple[datetime, Any]]:
        """Get history of a variable."""
        return self.variable_history.get(name, [])
    
    def get_all_variables(self) -> Dict[str, VariableInfo]:
        """Get all tracked variables."""
        return self.variables.copy()


# ============================================================
# TRACE COLLECTOR
# ============================================================

class TraceCollector:
    """Collect execution trace events."""
    
    def __init__(self, config: RuntimeInspectorConfig):
        self.config = config
        self.events: List[TraceEvent_] = []
        self.call_stack: List[CallFrame] = []
        self.frame_counter: int = 0
        self.start_time: Optional[datetime] = None
        self.variable_inspector = VariableInspector(config)
    
    def start(self):
        """Start trace collection."""
        self.start_time = datetime.now()
        tracemalloc.start()
        sys.settrace(self._trace_callback)
        logger.debug("Trace collection started")
    
    def stop(self):
        """Stop trace collection."""
        sys.settrace(None)
        tracemalloc.stop()
        logger.debug("Trace collection stopped")
    
    def _trace_callback(self, frame: inspect.FrameInfo, event: str, arg: Any):
        """Trace callback function."""
        if len(self.events) >= self.config.max_trace_events:
            return self._trace_callback
        
        try:
            event_type = self._map_event_type(event)
            if event_type is None:
                return self._trace_callback
            
            # Create call frame
            call_frame = self._create_call_frame(frame, event, arg)
            
            # Create trace event
            trace_event = TraceEvent_(
                event_type=event_type,
                frame=call_frame,
                line_number=frame.f_lineno if frame else None,
                exception=arg if event == 'exception' else None
            )
            
            # Handle different event types
            if event == 'call':
                self.call_stack.append(call_frame)
                trace_event.metadata['args'] = self._extract_args(frame)
                
            elif event == 'return':
                if self.call_stack:
                    top_frame = self.call_stack[-1]
                    top_frame.return_value = arg
                    trace_event.metadata['return_value'] = self._format_value(arg)
                if self.call_stack:
                    self.call_stack.pop()
                    
            elif event == 'exception':
                if self.call_stack:
                    top_frame = self.call_stack[-1]
                    top_frame.exception = arg[1] if len(arg) > 1 else None
            
            # Track memory
            if self.config.trace_memory:
                current, peak = tracemalloc.get_traced_memory()
                trace_event.memory_allocated = current
            
            self.events.append(trace_event)
            
            # Limit events
            if len(self.events) > self.config.max_trace_events:
                self.events = self.events[-self.config.max_trace_events:]
            
        except Exception as e:
            logger.debug(f"Trace callback error: {e}")
        
        return self._trace_callback
    
    def _map_event_type(self, event: str) -> Optional[TraceEvent]:
        """Map Python event to TraceEvent."""
        if event == 'call' and self.config.trace_calls:
            return TraceEvent.CALL
        elif event == 'return' and self.config.trace_returns:
            return TraceEvent.RETURN
        elif event == 'exception' and self.config.trace_exceptions:
            return TraceEvent.EXCEPTION
        elif event == 'line' and self.config.trace_lines:
            return TraceEvent.LINE
        elif event == 'opcode':
            return TraceEvent.OPCODE
        return None
    
    def _create_call_frame(self, frame: inspect.FrameInfo, 
                           event: str, arg: Any) -> CallFrame:
        """Create a CallFrame from frame info."""
        self.frame_counter += 1
        
        # Get function name
        function_name = frame.f_code.co_name if frame else '<unknown>'
        if function_name == '<module>':
            function_name = Path(frame.f_code.co_filename).stem if frame else '<module>'
        
        # Inspect variables
        locals_vars = {}
        if self.config.trace_variables and frame:
            locals_vars = self.variable_inspector.inspect_frame(frame)
        
        # Get arguments
        arguments = {}
        if event == 'call' and frame:
            arguments = self._extract_args(frame)
        
        return CallFrame(
            frame_id=f"frame_{self.frame_counter}",
            function_name=function_name,
            file_path=frame.f_code.co_filename if frame else '<unknown>',
            line_number=frame.f_lineno if frame else 0,
            depth=len(self.call_stack),
            locals=locals_vars,
            arguments=arguments,
            execution_time_ms=0.0  # Would calculate from timestamps
        )
    
    def _extract_args(self, frame: inspect.FrameInfo) -> Dict[str, Any]:
        """Extract function arguments from frame."""
        args = {}
        
        try:
            arg_info = inspect.getargvalues(frame)
            for arg_name in arg_info.args:
                if arg_name in arg_info.locals:
                    args[arg_name] = self._format_value(arg_info.locals[arg_name])
            
            if arg_info.varargs:
                args[f"*{arg_info.varargs}"] = self._format_value(
                    arg_info.locals.get(arg_info.varargs, [])
                )
            
            if arg_info.keywords:
                args[f"**{arg_info.keywords}"] = self._format_value(
                    arg_info.locals.get(arg_info.keywords, {})
                )
        except Exception:
            pass
        
        return args
    
    def _format_value(self, value: Any) -> Any:
        """Format value for trace."""
        return self.variable_inspector._format_value(value)
    
    def get_events(self) -> List[TraceEvent_]:
        """Get collected events."""
        return self.events.copy()
    
    def clear(self):
        """Clear collected events."""
        self.events.clear()
        self.call_stack.clear()
        self.frame_counter = 0


# ============================================================
# BREAKPOINT MANAGER
# ============================================================

class BreakpointManager:
    """Manage breakpoints and watchpoints."""
    
    def __init__(self, config: RuntimeInspectorConfig):
        self.config = config
        self.breakpoints: Dict[str, Breakpoint] = {}
        self.watchpoints: Dict[str, Watchpoint] = {}
        self.breakpoint_counter: int = 0
        self.watchpoint_counter: int = 0
        self._original_trace = None
    
    def add_breakpoint(self, file_path: str, line_number: int,
                       condition: Optional[str] = None,
                       temporary: bool = False) -> str:
        """Add a breakpoint."""
        self.breakpoint_counter += 1
        bp_id = f"bp_{self.breakpoint_counter}"
        
        self.breakpoints[bp_id] = Breakpoint(
            id=bp_id,
            file_path=file_path,
            line_number=line_number,
            condition=condition,
            temporary=temporary
        )
        
        logger.debug(f"Breakpoint added at {file_path}:{line_number}")
        return bp_id
    
    def remove_breakpoint(self, bp_id: str) -> bool:
        """Remove a breakpoint."""
        if bp_id in self.breakpoints:
            del self.breakpoints[bp_id]
            return True
        return False
    
    def add_watchpoint(self, variable_name: str,
                       condition: Optional[str] = None,
                       watch_read: bool = True,
                       watch_write: bool = True) -> str:
        """Add a watchpoint on a variable."""
        self.watchpoint_counter += 1
        wp_id = f"wp_{self.watchpoint_counter}"
        
        self.watchpoints[wp_id] = Watchpoint(
            id=wp_id,
            variable_name=variable_name,
            condition=condition,
            watch_read=watch_read,
            watch_write=watch_write
        )
        
        logger.debug(f"Watchpoint added for variable '{variable_name}'")
        return wp_id
    
    def remove_watchpoint(self, wp_id: str) -> bool:
        """Remove a watchpoint."""
        if wp_id in self.watchpoints:
            del self.watchpoints[wp_id]
            return True
        return False
    
    def check_breakpoint(self, frame: inspect.FrameInfo) -> Optional[Breakpoint]:
        """Check if current location hits a breakpoint."""
        file_path = frame.f_code.co_filename
        line_number = frame.f_lineno
        
        for bp in self.breakpoints.values():
            if not bp.enabled:
                continue
            
            if bp.file_path == file_path and bp.line_number == line_number:
                if bp.ignore_count > 0:
                    bp.ignore_count -= 1
                    continue
                
                if bp.condition:
                    if not self._evaluate_condition(bp.condition, frame):
                        continue
                
                bp.hit_count += 1
                
                if bp.max_hits and bp.hit_count >= bp.max_hits:
                    bp.enabled = False
                
                if bp.temporary:
                    self.remove_breakpoint(bp.id)
                
                return bp
        
        return None
    
    def check_watchpoint(self, variable_name: str, is_write: bool,
                          old_value: Any, new_value: Any) -> Optional[Watchpoint]:
        """Check if variable access hits a watchpoint."""
        for wp in self.watchpoints.values():
            if not wp.enabled:
                continue
            
            if wp.variable_name != variable_name:
                continue
            
            if is_write and not wp.watch_write:
                continue
            
            if not is_write and not wp.watch_read:
                continue
            
            if wp.condition:
                # Would evaluate condition with old/new values
                pass
            
            wp.hit_count += 1
            wp.old_value = old_value
            wp.new_value = new_value
            
            return wp
        
        return None
    
    def _evaluate_condition(self, condition: str, frame: inspect.FrameInfo) -> bool:
        """Evaluate a breakpoint condition."""
        try:
            # Create safe evaluation context
            safe_globals = {
                '__builtins__': {
                    'len': len, 'str': str, 'int': int, 'float': float,
                    'bool': bool, 'list': list, 'dict': dict, 'set': set,
                    'tuple': tuple, 'isinstance': isinstance,
                    'type': type, 'range': range, 'enumerate': enumerate,
                    'zip': zip, 'any': any, 'all': all, 'sum': sum,
                    'min': min, 'max': max, 'abs': abs, 'round': round
                }
            }
            safe_locals = frame.f_locals.copy()
            
            return bool(eval(condition, safe_globals, safe_locals))
        except Exception:
            return False
    
    def list_breakpoints(self) -> List[Breakpoint]:
        """List all breakpoints."""
        return list(self.breakpoints.values())
    
    def list_watchpoints(self) -> List[Watchpoint]:
        """List all watchpoints."""
        return list(self.watchpoints.values())
    
    def clear_all(self):
        """Clear all breakpoints and watchpoints."""
        self.breakpoints.clear()
        self.watchpoints.clear()


# ============================================================
# SNAPSHOT MANAGER
# ============================================================

class SnapshotManager:
    """Manage runtime snapshots."""
    
    def __init__(self, config: RuntimeInspectorConfig):
        self.config = config
        self.snapshots: List[RuntimeSnapshot] = []
        self.snapshot_counter: int = 0
        self.last_snapshot_time: Optional[datetime] = None
    
    def take_snapshot(self, trace_collector: TraceCollector,
                      variable_inspector: VariableInspector,
                      execution_state: ExecutionState = ExecutionState.RUNNING) -> RuntimeSnapshot:
        """Take a snapshot of current runtime state."""
        self.snapshot_counter += 1
        
        now = datetime.now()
        
        # Get current frame
        current_frame = None
        if trace_collector.call_stack:
            current_frame = trace_collector.call_stack[-1]
        
        # Get memory usage
        memory_usage = 0.0
        if tracemalloc.is_tracing():
            current, _ = tracemalloc.get_traced_memory()
            memory_usage = current / (1024 * 1024)
        
        # Get CPU time
        cpu_time = 0.0
        try:
            import resource
            cpu_time = resource.getrusage(resource.RUSAGE_SELF).ru_utime
        except ImportError:
            import time
            cpu_time = time.process_time()
        
        # Get thread count
        thread_count = threading.active_count()
        
        # Get open files (platform dependent)
        open_files = []
        try:
            import psutil
            proc = psutil.Process()
            open_files = [f.path for f in proc.open_files()]
        except ImportError:
            pass
        
        snapshot = RuntimeSnapshot(
            snapshot_id=f"snap_{self.snapshot_counter}",
            timestamp=now,
            execution_state=execution_state,
            current_frame=current_frame,
            call_stack=trace_collector.call_stack.copy(),
            all_variables=variable_inspector.get_all_variables(),
            memory_usage_mb=memory_usage,
            cpu_time_ms=cpu_time * 1000,
            thread_count=thread_count,
            open_files=open_files,
            trace_events=trace_collector.get_events()
        )
        
        self.snapshots.append(snapshot)
        self.last_snapshot_time = now
        
        # Limit snapshots
        if len(self.snapshots) > self.config.max_snapshots:
            self.snapshots = self.snapshots[-self.config.max_snapshots:]
        
        return snapshot
    
    def get_snapshots(self) -> List[RuntimeSnapshot]:
        """Get all snapshots."""
        return self.snapshots.copy()
    
    def compare_snapshots(self, snap1: RuntimeSnapshot,
                           snap2: RuntimeSnapshot) -> Dict[str, Any]:
        """Compare two snapshots."""
        comparison = {
            'memory_delta_mb': snap2.memory_usage_mb - snap1.memory_usage_mb,
            'cpu_time_delta_ms': snap2.cpu_time_ms - snap1.cpu_time_ms,
            'thread_count_delta': snap2.thread_count - snap1.thread_count,
            'new_variables': [],
            'removed_variables': [],
            'modified_variables': [],
            'call_stack_changed': snap1.call_stack != snap2.call_stack
        }
        
        # Compare variables
        vars1 = set(snap1.all_variables.keys())
        vars2 = set(snap2.all_variables.keys())
        
        comparison['new_variables'] = list(vars2 - vars1)
        comparison['removed_variables'] = list(vars1 - vars2)
        
        for var_name in vars1 & vars2:
            v1 = snap1.all_variables[var_name]
            v2 = snap2.all_variables[var_name]
            if v1.value != v2.value:
                comparison['modified_variables'].append({
                    'name': var_name,
                    'old': v1.value,
                    'new': v2.value
                })
        
        return comparison


# ============================================================
# MAIN RUNTIME INSPECTOR
# ============================================================

class RuntimeInspector:
    """
    Inspects Python runtime state, variables, and execution flow.
    
    Features:
    - Real-time variable inspection
    - Execution tracing (calls, returns, exceptions)
    - Breakpoint and watchpoint support
    - Runtime snapshots
    - Memory tracking
    - Call stack analysis
    - Hot path detection
    - Memory leak detection
    - Variable lifetime tracking
    - Integration with debugger
    """
    
    def __init__(self, config: RuntimeInspectorConfig):
        self.config = config
        self.trace_collector = TraceCollector(config)
        self.variable_inspector = VariableInspector(config)
        self.breakpoint_manager = BreakpointManager(config)
        self.snapshot_manager = SnapshotManager(config)
        
        self.execution_state = ExecutionState.NOT_STARTED
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        
        # Async support
        self._async_tasks: Set[asyncio.Task] = set()
        
        self.state = StateManager(config.project_root / ".ai_state" / "runtime_inspector.json")
        
        logger.info("RuntimeInspector initialized")
    
    def start(self):
        """Start runtime inspection."""
        self.execution_state = ExecutionState.RUNNING
        self.start_time = datetime.now()
        self.trace_collector.start()
        
        # Take initial snapshot
        self.snapshot_manager.take_snapshot(
            self.trace_collector,
            self.variable_inspector,
            ExecutionState.RUNNING
        )
        
        logger.info("Runtime inspection started")
    
    def stop(self) -> RuntimeInspectionReport:
        """Stop runtime inspection and generate report."""
        self.execution_state = ExecutionState.COMPLETED
        self.end_time = datetime.now()
        self.trace_collector.stop()
        
        # Take final snapshot
        final_snapshot = self.snapshot_manager.take_snapshot(
            self.trace_collector,
            self.variable_inspector,
            ExecutionState.COMPLETED
        )
        
        # Generate report
        report = self._generate_report()
        
        logger.info("Runtime inspection stopped")
        
        return report
    
    def pause(self):
        """Pause inspection."""
        self.execution_state = ExecutionState.PAUSED
        self.trace_collector.stop()
        logger.debug("Runtime inspection paused")
    
    def resume(self):
        """Resume inspection."""
        self.execution_state = ExecutionState.RUNNING
        self.trace_collector.start()
        logger.debug("Runtime inspection resumed")
    
    def inspect(self, func: Callable, *args, **kwargs) -> RuntimeInspectionReport:
        """Inspect a function call."""
        self.start()
        
        try:
            result = func(*args, **kwargs)
            return result
        except Exception as e:
            self.execution_state = ExecutionState.EXCEPTION
            logger.error(f"Exception during inspection: {e}")
            raise
        finally:
            self.stop()
        
        return self._generate_report()
    
    async def inspect_async(self, coro) -> RuntimeInspectionReport:
        """Inspect an async coroutine."""
        self.start()
        
        try:
            task = asyncio.create_task(coro)
            self._async_tasks.add(task)
            result = await task
            return result
        except Exception as e:
            self.execution_state = ExecutionState.EXCEPTION
            logger.error(f"Exception during async inspection: {e}")
            raise
        finally:
            self._async_tasks.discard(task)
            self.stop()
        
        return self._generate_report()
    
    def take_snapshot(self) -> RuntimeSnapshot:
        """Take a manual snapshot."""
        return self.snapshot_manager.take_snapshot(
            self.trace_collector,
            self.variable_inspector,
            self.execution_state
        )
    
    def add_breakpoint(self, file_path: str, line_number: int,
                       condition: Optional[str] = None) -> str:
        """Add a breakpoint."""
        return self.breakpoint_manager.add_breakpoint(file_path, line_number, condition)
    
    def remove_breakpoint(self, bp_id: str) -> bool:
        """Remove a breakpoint."""
        return self.breakpoint_manager.remove_breakpoint(bp_id)
    
    def add_watchpoint(self, variable_name: str) -> str:
        """Add a watchpoint."""
        return self.breakpoint_manager.add_watchpoint(variable_name)
    
    def remove_watchpoint(self, wp_id: str) -> bool:
        """Remove a watchpoint."""
        return self.breakpoint_manager.remove_watchpoint(wp_id)
    
    def get_current_variables(self) -> Dict[str, VariableInfo]:
        """Get current variable values."""
        return self.variable_inspector.get_all_variables()
    
    def get_variable_history(self, name: str) -> List[Tuple[datetime, Any]]:
        """Get history of a variable."""
        return self.variable_inspector.get_variable_history(name)
    
    def get_call_stack(self) -> List[CallFrame]:
        """Get current call stack."""
        return self.trace_collector.call_stack.copy()
    
    def _generate_report(self) -> RuntimeInspectionReport:
        """Generate inspection report."""
        snapshots = self.snapshot_manager.get_snapshots()
        
        report = RuntimeInspectionReport(
            target_name="inspection",
            execution_duration_ms=(
                (self.end_time - self.start_time).total_seconds() * 1000
                if self.start_time and self.end_time else 0
            ),
            snapshots=snapshots,
            initial_snapshot=snapshots[0] if snapshots else None,
            final_snapshot=snapshots[-1] if snapshots else None
        )
        
        # Analyze call graph
        report.call_graph = self._build_call_graph()
        report.hot_paths = self._find_hot_paths()
        report.function_timings = self._calculate_function_timings()
        
        # Analyze memory
        report.memory_peaks = self._find_memory_peaks()
        report.memory_leaks = self._detect_memory_leaks()
        report.large_objects = self._find_large_objects()
        
        # Analyze variables
        report.variable_lifetimes = self._analyze_variable_lifetimes()
        report.mutated_variables = self._find_mutated_variables()
        report.unused_variables = self._find_unused_variables()
        
        # Detect issues
        report.issues = self._detect_issues(report)
        report.suggestions = self._generate_suggestions(report)
        
        report.summary = self._generate_summary(report)
        
        return report
    
    def _build_call_graph(self) -> Dict[str, List[str]]:
        """Build call graph from trace events."""
        graph = defaultdict(set)
        
        caller = None
        for event in self.trace_collector.get_events():
            if event.event_type == TraceEvent.CALL:
                if caller:
                    graph[caller].add(event.frame.function_name)
                caller = event.frame.function_name
            elif event.event_type == TraceEvent.RETURN:
                caller = None
        
        return {k: list(v) for k, v in graph.items()}
    
    def _find_hot_paths(self) -> List[List[str]]:
        """Find hot execution paths."""
        # Count call sequences
        path_counts = defaultdict(int)
        current_path = []
        
        for event in self.trace_collector.get_events():
            if event.event_type == TraceEvent.CALL:
                current_path.append(event.frame.function_name)
                path_key = " -> ".join(current_path[-5:])  # Last 5 calls
                path_counts[path_key] += 1
            elif event.event_type == TraceEvent.RETURN:
                if current_path:
                    current_path.pop()
        
        # Return top paths
        top_paths = sorted(path_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        return [path.split(" -> ") for path, _ in top_paths]
    
    def _calculate_function_timings(self) -> Dict[str, float]:
        """Calculate time spent in each function."""
        timings = defaultdict(float)
        call_times = {}
        
        for event in self.trace_collector.get_events():
            frame_id = event.frame.frame_id
            
            if event.event_type == TraceEvent.CALL:
                call_times[frame_id] = event.timestamp
            elif event.event_type == TraceEvent.RETURN:
                if frame_id in call_times:
                    duration = (event.timestamp - call_times[frame_id]).total_seconds() * 1000
                    timings[event.frame.function_name] += duration
                    del call_times[frame_id]
        
        return dict(timings)
    
    def _find_memory_peaks(self) -> List[Tuple[datetime, float]]:
        """Find memory usage peaks."""
        peaks = []
        
        for snapshot in self.snapshot_manager.snapshots:
            peaks.append((snapshot.timestamp, snapshot.memory_usage_mb))
        
        # Sort by memory usage
        peaks.sort(key=lambda x: x[1], reverse=True)
        return peaks[:5]
    
    def _detect_memory_leaks(self) -> List[Dict[str, Any]]:
        """Detect potential memory leaks."""
        leaks = []
        
        snapshots = self.snapshot_manager.snapshots
        if len(snapshots) < 2:
            return leaks
        
        # Compare first and last snapshot
        first = snapshots[0]
        last = snapshots[-1]
        
        # Check for consistently growing memory
        if last.memory_usage_mb > first.memory_usage_mb * 1.2:
            leaks.append({
                'type': 'growing_memory',
                'initial_mb': first.memory_usage_mb,
                'final_mb': last.memory_usage_mb,
                'growth_mb': last.memory_usage_mb - first.memory_usage_mb,
                'severity': 'high' if last.memory_usage_mb > first.memory_usage_mb * 2 else 'medium'
            })
        
        # Check for variables that exist in all snapshots
        persistent_vars = set(first.all_variables.keys())
        for snap in snapshots[1:]:
            persistent_vars &= set(snap.all_variables.keys())
        
        for var_name in persistent_vars:
            var = last.all_variables.get(var_name)
            if var and var.size_bytes > 1024 * 1024:  # > 1MB
                leaks.append({
                    'type': 'persistent_large_variable',
                    'variable': var_name,
                    'size_mb': var.size_bytes / (1024 * 1024),
                    'severity': 'medium'
                })
        
        return leaks
    
    def _find_large_objects(self) -> List[VariableInfo]:
        """Find large objects in memory."""
        large_objects = []
        
        if self.snapshot_manager.snapshots:
            final = self.snapshot_manager.snapshots[-1]
            for var in final.all_variables.values():
                if var.size_bytes > 1024 * 1024:  # > 1MB
                    large_objects.append(var)
        
        large_objects.sort(key=lambda x: x.size_bytes, reverse=True)
        return large_objects[:10]
    
    def _analyze_variable_lifetimes(self) -> Dict[str, Tuple[datetime, datetime]]:
        """Analyze when variables are created and destroyed."""
        lifetimes = {}
        
        # Track first and last appearance
        first_seen = {}
        last_seen = {}
        
        for snapshot in self.snapshot_manager.snapshots:
            for var_name in snapshot.all_variables:
                if var_name not in first_seen:
                    first_seen[var_name] = snapshot.timestamp
                last_seen[var_name] = snapshot.timestamp
        
        for var_name in first_seen:
            lifetimes[var_name] = (first_seen[var_name], last_seen.get(var_name, first_seen[var_name]))
        
        return lifetimes
    
    def _find_mutated_variables(self) -> List[str]:
        """Find variables that were modified."""
        mutated = []
        
        for name, info in self.variable_inspector.variables.items():
            if info.state == VariableState.MUTATED or info.modification_count > 0:
                mutated.append(name)
        
        return mutated
    
    def _find_unused_variables(self) -> List[str]:
        """Find variables that were defined but never accessed."""
        unused = []
        
        for name, info in self.variable_inspector.variables.items():
            if info.access_count == 0 and not name.startswith('_'):
                unused.append(name)
        
        return unused
    
    def _detect_issues(self, report: RuntimeInspectionReport) -> List[Dict[str, Any]]:
        """Detect runtime issues."""
        issues = []
        
        # Memory issues
        if report.memory_leaks:
            for leak in report.memory_leaks:
                issues.append({
                    'category': 'memory',
                    'type': leak['type'],
                    'description': f"Memory leak detected: {leak.get('variable', 'growing memory')}",
                    'severity': leak['severity'],
                    'details': leak
                })
        
        # Performance issues
        for func, time_ms in report.function_timings.items():
            if time_ms > 1000:  # > 1 second
                issues.append({
                    'category': 'performance',
                    'type': 'slow_function',
                    'description': f"Function '{func}' took {time_ms:.0f}ms",
                    'severity': 'high' if time_ms > 5000 else 'medium',
                    'details': {'function': func, 'time_ms': time_ms}
                })
        
        # Hot path issues
        for path in report.hot_paths:
            if len(path) > 10:
                issues.append({
                    'category': 'performance',
                    'type': 'deep_call_stack',
                    'description': f"Deep call stack detected ({len(path)} frames)",
                    'severity': 'medium',
                    'details': {'path': path}
                })
        
        # Variable issues
        if len(report.unused_variables) > 5:
            issues.append({
                'category': 'code_quality',
                'type': 'unused_variables',
                'description': f"{len(report.unused_variables)} unused variables detected",
                'severity': 'low',
                'details': {'count': len(report.unused_variables)}
            })
        
        return issues
    
    def _generate_suggestions(self, report: RuntimeInspectionReport) -> List[str]:
        """Generate improvement suggestions."""
        suggestions = []
        
        for issue in report.issues:
            if issue['category'] == 'memory' and issue['type'] == 'growing_memory':
                suggestions.append("Check for objects not being garbage collected")
            elif issue['category'] == 'memory' and issue['type'] == 'persistent_large_variable':
                suggestions.append(f"Consider clearing or reducing size of {issue['details'].get('variable', 'large variable')}")
            elif issue['category'] == 'performance' and issue['type'] == 'slow_function':
                suggestions.append(f"Profile and optimize '{issue['details']['function']}'")
            elif issue['category'] == 'performance' and issue['type'] == 'deep_call_stack':
                suggestions.append("Consider flattening deep call stacks")
            elif issue['category'] == 'code_quality' and issue['type'] == 'unused_variables':
                suggestions.append("Remove unused variables to improve code clarity")
        
        return suggestions[:5]
    
    def _generate_summary(self, report: RuntimeInspectionReport) -> str:
        """Generate inspection summary."""
        parts = []
        
        parts.append(f"Duration: {report.execution_duration_ms:.0f}ms")
        parts.append(f"Snapshots: {len(report.snapshots)}")
        parts.append(f"Functions called: {len(report.function_timings)}")
        parts.append(f"Memory peak: {max(p[1] for p in report.memory_peaks) if report.memory_peaks else 0:.1f}MB")
        parts.append(f"Issues: {len(report.issues)}")
        
        return " | ".join(parts)
    
    def export_report(self, report: RuntimeInspectionReport,
                      output_path: Optional[Path] = None,
                      format: str = 'markdown') -> str:
        """Export inspection report."""
        
        if format == 'json':
            import json
            data = {
                'inspected_at': report.inspected_at.isoformat(),
                'target': report.target_name,
                'duration_ms': report.execution_duration_ms,
                'snapshots': len(report.snapshots),
                'call_graph': report.call_graph,
                'hot_paths': [' -> '.join(p) for p in report.hot_paths],
                'function_timings': report.function_timings,
                'memory_peaks': [(t.isoformat(), m) for t, m in report.memory_peaks],
                'memory_leaks': report.memory_leaks,
                'large_objects': [
                    {'name': v.name, 'type': v.type_name, 'size_mb': v.size_bytes / (1024*1024)}
                    for v in report.large_objects
                ],
                'mutated_variables': report.mutated_variables,
                'unused_variables': report.unused_variables,
                'issues': report.issues,
                'suggestions': report.suggestions,
                'summary': report.summary
            }
            
            content = json.dumps(data, indent=2)
            
        else:  # markdown
            lines = [
                f"# Runtime Inspection Report",
                "",
                f"**Inspected:** {report.inspected_at.strftime('%Y-%m-%d %H:%M:%S')}",
                f"**Target:** {report.target_name}",
                f"**Duration:** {report.execution_duration_ms:.0f}ms",
                f"**Summary:** {report.summary}",
                "",
                "## Statistics",
                "",
                f"| Metric | Value |",
                f"|--------|-------|",
                f"| Snapshots | {len(report.snapshots)} |",
                f"| Functions Called | {len(report.function_timings)} |",
                f"| Memory Peak | {max(p[1] for p in report.memory_peaks) if report.memory_peaks else 0:.1f} MB |",
                f"| Mutated Variables | {len(report.mutated_variables)} |",
                f"| Unused Variables | {len(report.unused_variables)} |",
                "",
            ]
            
            if report.function_timings:
                lines.extend([
                    "## Function Timings",
                    "",
                    "| Function | Time (ms) |",
                    "|----------|-----------|",
                ])
                for func, time_ms in sorted(report.function_timings.items(), 
                                            key=lambda x: x[1], reverse=True)[:10]:
                    lines.append(f"| {func} | {time_ms:.2f} |")
                lines.append("")
            
            if report.hot_paths:
                lines.extend([
                    "## Hot Execution Paths",
                    "",
                ])
                for i, path in enumerate(report.hot_paths[:5], 1):
                    lines.append(f"{i}. {' → '.join(path)}")
                lines.append("")
            
            if report.memory_leaks:
                lines.extend([
                    "## ⚠️ Memory Leaks",
                    "",
                ])
                for leak in report.memory_leaks:
                    lines.append(f"- **{leak['type']}**: {leak.get('variable', 'N/A')} "
                                f"({leak.get('growth_mb', leak.get('size_mb', 0)):.1f}MB)")
                lines.append("")
            
            if report.large_objects:
                lines.extend([
                    "## Large Objects",
                    "",
                    "| Variable | Type | Size (MB) |",
                    "|----------|------|-----------|",
                ])
                for obj in report.large_objects[:10]:
                    lines.append(f"| {obj.name} | {obj.type_name} | {obj.size_bytes / (1024*1024):.2f} |")
                lines.append("")
            
            if report.issues:
                lines.extend([
                    "## Issues Detected",
                    "",
                ])
                for issue in report.issues:
                    lines.append(f"- **[{issue['category']}]** {issue['description']} ({issue['severity']})")
                lines.append("")
            
            if report.suggestions:
                lines.extend([
                    "## Suggestions",
                    "",
                ])
                for suggestion in report.suggestions:
                    lines.append(f"- {suggestion}")
                lines.append("")
            
            content = '\n'.join(lines)
        
        if output_path:
            output_path.write_text(content)
        
        return content
    
    def close(self):
        """Clean up resources."""
        if self.execution_state == ExecutionState.RUNNING:
            self.stop()
        self.state.save()
        logger.info("RuntimeInspector closed")


# ============================================================
# CONTEXT MANAGER
# ============================================================

class InspectContext:
    """Context manager for runtime inspection."""
    
    def __init__(self, config: RuntimeInspectorConfig):
        self.inspector = RuntimeInspector(config)
    
    def __enter__(self) -> RuntimeInspector:
        self.inspector.start()
        return self.inspector
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.inspector.stop()
        return False


# ============================================================
# DECORATOR
# ============================================================

def inspect_runtime(config: Optional[RuntimeInspectorConfig] = None):
    """Decorator to inspect function runtime."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            cfg = config or RuntimeInspectorConfig(project_root=Path.cwd())
            inspector = RuntimeInspector(cfg)
            result = inspector.inspect(func, *args, **kwargs)
            inspector.close()
            return result
        
        async def async_wrapper(*args, **kwargs):
            cfg = config or RuntimeInspectorConfig(project_root=Path.cwd())
            inspector = RuntimeInspector(cfg)
            result = await inspector.inspect_async(func(*args, **kwargs))
            inspector.close()
            return result
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return wrapper
    return decorator


# ============================================================
# CLI ENTRY POINT
# ============================================================

def main():
    """CLI entry point for runtime inspector."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Inspect Python runtime")
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--script", type=Path, help="Python script to inspect")
    parser.add_argument("--function", type=str, help="Function to inspect")
    parser.add_argument("--output", "-o", type=Path, help="Output report file")
    parser.add_argument("--format", choices=["json", "markdown"], default="markdown")
    parser.add_argument("--no-trace-lines", action="store_true")
    parser.add_argument("--no-trace-variables", action="store_true")
    parser.add_argument("--no-trace-memory", action="store_true")
    parser.add_argument("--snapshot-interval", type=int, default=100)
    
    args = parser.parse_args()
    
    config = RuntimeInspectorConfig(
        project_root=args.project_root,
        trace_lines=not args.no_trace_lines,
        trace_variables=not args.no_trace_variables,
        trace_memory=not args.no_trace_memory,
        snapshot_interval_ms=args.snapshot_interval
    )
    
    inspector = RuntimeInspector(config)
    
    if args.script:
        # Run script with inspection
        import runpy
        inspector.start()
        try:
            runpy.run_path(str(args.script))
        except Exception as e:
            logger.error(f"Script error: {e}")
        finally:
            report = inspector.stop()
    elif args.function:
        # Import and inspect function
        module_name, func_name = args.function.rsplit('.', 1)
        module = __import__(module_name, fromlist=[func_name])
        func = getattr(module, func_name)
        inspector.inspect(func)
        report = inspector._generate_report()
    else:
        print("Please specify --script or --function")
        sys.exit(1)
    
    output = inspector.export_report(report, args.output, args.format)
    
    if not args.output:
        print(output)
    else:
        print(f"Report saved to {args.output}")
    
    print(f"\n{report.summary}")
    
    inspector.close()


if __name__ == "__main__":
    main()