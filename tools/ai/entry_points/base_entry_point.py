#!/usr/bin/env python3
"""
Base Entry Point - Abstract base class for all system entry points.

Part of the Entry Points module (entry_points/base_entry_point.py)

This base_entry_point.py provides:

1. Abstract Base Class - Standardized lifecycle for all entry points
2. Lifecycle Management - setup(), validate(), execute(), teardown(), shutdown()
3. Signal Handling - Graceful shutdown on SIGINT, SIGTERM, SIGHUP
4. Argument Parsing - Standard CLI argument handling with extensibility
5. Configuration Management - Load from files and command line
6. Logging Setup - Configurable logging with verbosity levels
7. State Persistence - Optional state manager integration
8. Workflow Integration - Run workflows through the workflow engine
9. Retry Logic - Automatic retry with configurable attempts and delay
10. Async Support - Both sync and async execution modes
11. Metrics Collection - Execution time, request counts, error rates
12. Health Check - Standardized health check endpoint
13. Standard Exit Codes - Consistent exit codes across all entry points
14. Static Main Method - Easy CLI entry with BaseEntryPoint.main(MyEntryPoint)

All other entry points (cli_entry.py, api_entry.py, bot_entry.py, etc.) should inherit from this base class.
"""

import sys
import signal
import asyncio
import argparse
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Set, Optional, Any, Tuple, Union, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import traceback

from ..shared.logger import get_logger, LoggerConfig, LogLevel
from ..shared.config import Config
from ..shared.state_manager import StateManager
from ..orchestration.workflow_engine import WorkflowEngine, WorkflowContext
from ..orchestration.agent_registry import AgentRegistry

logger = get_logger(__name__)


# ============================================================
# ENUMS AND CONSTANTS
# ============================================================

class EntryPointType(str, Enum):
    """Type of entry point."""
    CLI = "cli"
    API = "api"
    BOT = "bot"
    WEB = "web"
    CI = "ci"
    GIT_HOOK = "git_hook"
    IDE_PLUGIN = "ide_plugin"
    WATCHER = "watcher"
    SCHEDULER = "scheduler"
    CUSTOM = "custom"


class ExecutionMode(str, Enum):
    """Execution mode for entry point."""
    SYNC = "sync"
    ASYNC = "async"
    BACKGROUND = "background"
    INTERACTIVE = "interactive"
    DAEMON = "daemon"


class ExitCode(int, Enum):
    """Standard exit codes."""
    SUCCESS = 0
    GENERAL_ERROR = 1
    INVALID_ARGS = 2
    CONFIG_ERROR = 3
    WORKFLOW_ERROR = 4
    TIMEOUT = 5
    INTERRUPTED = 130
    UNKNOWN = 255


# ============================================================
# DATA MODELS
# ============================================================

@dataclass
class EntryPointContext:
    """Context for entry point execution."""
    entry_point_name: str
    entry_point_type: EntryPointType
    execution_mode: ExecutionMode
    start_time: datetime = field(default_factory=datetime.now)
    args: Optional[argparse.Namespace] = None
    config: Optional[Config] = None
    workflow_context: Optional[WorkflowContext] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def get_duration_seconds(self) -> float:
        """Get execution duration in seconds."""
        return (datetime.now() - self.start_time).total_seconds()


@dataclass
class EntryPointResult:
    """Result of entry point execution."""
    exit_code: ExitCode = ExitCode.SUCCESS
    success: bool = True
    message: str = ""
    data: Optional[Any] = None
    error: Optional[Exception] = None
    error_traceback: Optional[str] = None
    workflow_result: Optional[Any] = None
    duration_seconds: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EntryPointConfig:
    """Configuration for an entry point."""
    name: str
    entry_type: EntryPointType
    execution_mode: ExecutionMode = ExecutionMode.SYNC
    description: str = ""
    version: str = "1.0.0"
    
    # Logging
    log_level: LogLevel = LogLevel.INFO
    log_file: Optional[Path] = None
    log_format: str = "console"
    
    # Timeouts
    startup_timeout: int = 30
    execution_timeout: int = 300
    shutdown_timeout: int = 10
    
    # Signal handling
    handle_signals: bool = True
    graceful_shutdown: bool = True
    
    # State persistence
    state_enabled: bool = True
    state_dir: Optional[Path] = None
    
    # Error handling
    exit_on_error: bool = True
    max_retries: int = 0
    retry_delay: float = 1.0
    
    # Features
    enable_profiling: bool = False
    enable_metrics: bool = True
    enable_health_check: bool = False
    
    metadata: Dict[str, Any] = field(default_factory=dict)


# ============================================================
# SIGNAL HANDLER
# ============================================================

class SignalHandler:
    """Handle OS signals for graceful shutdown."""
    
    def __init__(self):
        self.shutdown_requested = False
        self._original_handlers = {}
    
    def setup(self, callback: Optional[Callable] = None):
        """Setup signal handlers."""
        signals_to_handle = [signal.SIGINT, signal.SIGTERM]
        
        if sys.platform != 'win32':
            signals_to_handle.append(signal.SIGHUP)
        
        for sig in signals_to_handle:
            self._original_handlers[sig] = signal.signal(sig, self._handle_signal)
        
        self._callback = callback
    
    def _handle_signal(self, signum: int, frame):
        """Handle incoming signal."""
        logger.info(f"Received signal {signal.Signals(signum).name}")
        self.shutdown_requested = True
        
        if self._callback:
            self._callback(signum)
    
    def restore(self):
        """Restore original signal handlers."""
        for sig, handler in self._original_handlers.items():
            signal.signal(sig, handler)
    
    @property
    def is_shutdown_requested(self) -> bool:
        return self.shutdown_requested


# ============================================================
# BASE ENTRY POINT
# ============================================================

class BaseEntryPoint(ABC):
    """
    Abstract base class for all system entry points.
    
    Features:
    - Standardized initialization and shutdown
    - Signal handling for graceful termination
    - Argument parsing support
    - Configuration management
    - Logging setup
    - State persistence
    - Workflow orchestration
    - Error handling and retry logic
    - Metrics collection
    - Health check support
    
    Lifecycle:
    1. __init__() - Initialize
    2. parse_arguments() - Parse command line args
    3. load_configuration() - Load config files
    4. setup() - Setup logging, state, etc.
    5. validate() - Validate inputs
    6. execute() - Main execution
    7. teardown() - Cleanup
    8. shutdown() - Final shutdown
    """
    
    def __init__(self, config: Optional[EntryPointConfig] = None):
        """Initialize the entry point."""
        self.config = config or self._get_default_config()
        self.context = EntryPointContext(
            entry_point_name=self.config.name,
            entry_point_type=self.config.entry_type,
            execution_mode=self.config.execution_mode
        )
        
        self.signal_handler = SignalHandler()
        self.state_manager: Optional[StateManager] = None
        self.workflow_engine: Optional[WorkflowEngine] = None
        self.agent_registry: Optional[AgentRegistry] = None
        
        self._shutdown_requested = False
        self._retry_count = 0
        
        # Metrics
        self._metrics: Dict[str, Any] = {
            'start_time': None,
            'end_time': None,
            'requests_processed': 0,
            'errors_encountered': 0,
        }
    
    def _get_default_config(self) -> EntryPointConfig:
        """Get default configuration."""
        return EntryPointConfig(
            name=self.__class__.__name__,
            entry_type=EntryPointType.CUSTOM,
            description="Base entry point"
        )
    
    # ============================================================
    # LIFECYCLE METHODS
    # ============================================================
    
    def run(self, args: Optional[List[str]] = None) -> EntryPointResult:
        """
        Main entry point execution flow.
        
        Args:
            args: Command line arguments (uses sys.argv if None)
            
        Returns:
            EntryPointResult with execution details
        """
        self._metrics['start_time'] = datetime.now()
        
        try:
            # Parse arguments
            parsed_args = self.parse_arguments(args)
            self.context.args = parsed_args
            
            # Load configuration
            config = self.load_configuration(parsed_args)
            self.context.config = config
            
            # Setup
            self.setup()
            
            # Validate
            validation_errors = self.validate()
            if validation_errors:
                return EntryPointResult(
                    exit_code=ExitCode.INVALID_ARGS,
                    success=False,
                    message=f"Validation failed: {', '.join(validation_errors)}",
                    duration_seconds=self.context.get_duration_seconds()
                )
            
            # Execute with retry
            result = self._execute_with_retry()
            
            return result
            
        except KeyboardInterrupt:
            logger.info("Execution interrupted by user")
            return EntryPointResult(
                exit_code=ExitCode.INTERRUPTED,
                success=False,
                message="Interrupted by user",
                duration_seconds=self.context.get_duration_seconds()
            )
        except Exception as e:
            logger.error(f"Unhandled exception: {e}")
            logger.debug(traceback.format_exc())
            return EntryPointResult(
                exit_code=ExitCode.GENERAL_ERROR,
                success=False,
                message=str(e),
                error=e,
                error_traceback=traceback.format_exc(),
                duration_seconds=self.context.get_duration_seconds()
            )
        finally:
            self.teardown()
            self.shutdown()
            self._metrics['end_time'] = datetime.now()
    
    async def run_async(self, args: Optional[List[str]] = None) -> EntryPointResult:
        """
        Async entry point execution flow.
        
        Args:
            args: Command line arguments (uses sys.argv if None)
            
        Returns:
            EntryPointResult with execution details
        """
        self._metrics['start_time'] = datetime.now()
        
        try:
            parsed_args = self.parse_arguments(args)
            self.context.args = parsed_args
            
            config = self.load_configuration(parsed_args)
            self.context.config = config
            
            await self.setup_async()
            
            validation_errors = self.validate()
            if validation_errors:
                return EntryPointResult(
                    exit_code=ExitCode.INVALID_ARGS,
                    success=False,
                    message=f"Validation failed: {', '.join(validation_errors)}",
                    duration_seconds=self.context.get_duration_seconds()
                )
            
            result = await self._execute_async_with_retry()
            
            return result
            
        except asyncio.CancelledError:
            logger.info("Async execution cancelled")
            return EntryPointResult(
                exit_code=ExitCode.INTERRUPTED,
                success=False,
                message="Execution cancelled",
                duration_seconds=self.context.get_duration_seconds()
            )
        except Exception as e:
            logger.error(f"Unhandled async exception: {e}")
            logger.debug(traceback.format_exc())
            return EntryPointResult(
                exit_code=ExitCode.GENERAL_ERROR,
                success=False,
                message=str(e),
                error=e,
                error_traceback=traceback.format_exc(),
                duration_seconds=self.context.get_duration_seconds()
            )
        finally:
            await self.teardown_async()
            await self.shutdown_async()
            self._metrics['end_time'] = datetime.now()
    
    def _execute_with_retry(self) -> EntryPointResult:
        """Execute with retry logic."""
        while True:
            try:
                result = self.execute()
                self._retry_count = 0
                result.duration_seconds = self.context.get_duration_seconds()
                return result
            except Exception as e:
                self._metrics['errors_encountered'] += 1
                
                if self._retry_count < self.config.max_retries:
                    self._retry_count += 1
                    logger.warning(f"Execution failed (attempt {self._retry_count}/{self.config.max_retries}): {e}")
                    
                    if self.config.retry_delay > 0:
                        import time
                        time.sleep(self.config.retry_delay)
                else:
                    raise
    
    async def _execute_async_with_retry(self) -> EntryPointResult:
        """Execute async with retry logic."""
        while True:
            try:
                result = await self.execute_async()
                self._retry_count = 0
                result.duration_seconds = self.context.get_duration_seconds()
                return result
            except Exception as e:
                self._metrics['errors_encountered'] += 1
                
                if self._retry_count < self.config.max_retries:
                    self._retry_count += 1
                    logger.warning(f"Async execution failed (attempt {self._retry_count}/{self.config.max_retries}): {e}")
                    
                    if self.config.retry_delay > 0:
                        await asyncio.sleep(self.config.retry_delay)
                else:
                    raise
    
    # ============================================================
    # ABSTRACT METHODS (MUST BE IMPLEMENTED BY SUBCLASSES)
    # ============================================================
    
    @abstractmethod
    def execute(self) -> EntryPointResult:
        """
        Execute the main logic of the entry point.
        
        Must be implemented by subclasses.
        """
        pass
    
    # ============================================================
    # OVERRIDABLE METHODS
    # ============================================================
    
    def parse_arguments(self, args: Optional[List[str]] = None) -> argparse.Namespace:
        """
        Parse command line arguments.
        
        Override to add custom arguments.
        """
        parser = self._create_argument_parser()
        return parser.parse_args(args)
    
    def _create_argument_parser(self) -> argparse.ArgumentParser:
        """Create argument parser with standard options."""
        parser = argparse.ArgumentParser(
            description=self.config.description or f"{self.config.name} Entry Point",
            formatter_class=argparse.RawDescriptionHelpFormatter
        )
        
        parser.add_argument(
            '--version', action='version',
            version=f'%(prog)s {self.config.version}'
        )
        parser.add_argument(
            '--verbose', '-v', action='count', default=0,
            help='Increase verbosity (can be used multiple times)'
        )
        parser.add_argument(
            '--quiet', '-q', action='store_true',
            help='Suppress non-error output'
        )
        parser.add_argument(
            '--config', '-c', type=Path,
            help='Path to configuration file'
        )
        parser.add_argument(
            '--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
            help='Set logging level'
        )
        parser.add_argument(
            '--log-file', type=Path,
            help='Write logs to file'
        )
        parser.add_argument(
            '--state-dir', type=Path,
            help='Directory for state persistence'
        )
        parser.add_argument(
            '--no-state', action='store_true',
            help='Disable state persistence'
        )
        parser.add_argument(
            '--profile', action='store_true',
            help='Enable profiling'
        )
        parser.add_argument(
            '--timeout', type=int,
            help=f'Execution timeout in seconds (default: {self.config.execution_timeout})'
        )
        
        return parser
    
    def load_configuration(self, args: argparse.Namespace) -> Config:
        """
        Load configuration from files and arguments.
        
        Override to add custom configuration sources.
        """
        config = Config()
        
        # Load from config file if specified
        if args.config:
            config.load_file(args.config)
        
        # Override with command line arguments
        if args.log_level:
            config.set('logging.level', args.log_level)
        if args.log_file:
            config.set('logging.file', str(args.log_file))
        if args.state_dir:
            config.set('state.dir', str(args.state_dir))
        if args.no_state:
            config.set('state.enabled', False)
        if args.profile:
            config.set('profiling.enabled', True)
        if args.timeout:
            config.set('execution.timeout', args.timeout)
        
        # Set verbosity
        if args.verbose > 0:
            level = 'DEBUG' if args.verbose > 1 else 'INFO'
            config.set('logging.level', level)
        
        return config
    
    def setup(self):
        """Setup resources before execution."""
        # Setup logging
        self._setup_logging()
        
        # Setup signal handlers
        if self.config.handle_signals:
            self.signal_handler.setup(self._on_shutdown_signal)
        
        # Setup state manager
        if self.config.state_enabled:
            state_dir = self.config.state_dir or Path(".ai_state")
            self.state_manager = StateManager(state_dir)
        
        # Setup agent registry
        self.agent_registry = AgentRegistry()
        
        # Setup workflow engine
        self.workflow_engine = WorkflowEngine(
            agent_registry=self.agent_registry,
            state_manager=self.state_manager
        )
        
        logger.info(f"Entry point '{self.config.name}' setup complete")
    
    async def setup_async(self):
        """Async setup resources before execution."""
        self.setup()
        logger.info(f"Entry point '{self.config.name}' async setup complete")
    
    def validate(self) -> List[str]:
        """
        Validate inputs and configuration.
        
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        
        if not self.config.name:
            errors.append("Entry point name is required")
        
        if self.config.execution_timeout <= 0:
            errors.append("Execution timeout must be positive")
        
        return errors
    
    async def execute_async(self) -> EntryPointResult:
        """
        Async version of execute.
        
        Default implementation calls sync execute in thread pool.
        Override for true async implementation.
        """
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.execute)
    
    def teardown(self):
        """Cleanup resources after execution."""
        if self.state_manager:
            self.state_manager.save()
            self.state_manager.close()
        
        if self.config.handle_signals:
            self.signal_handler.restore()
        
        logger.info(f"Entry point '{self.config.name}' teardown complete")
    
    async def teardown_async(self):
        """Async cleanup resources after execution."""
        self.teardown()
        logger.info(f"Entry point '{self.config.name}' async teardown complete")
    
    def shutdown(self):
        """Final shutdown."""
        logger.info(f"Entry point '{self.config.name}' shutdown complete")
    
    async def shutdown_async(self):
        """Async final shutdown."""
        self.shutdown()
        logger.info(f"Entry point '{self.config.name}' async shutdown complete")
    
    # ============================================================
    # UTILITY METHODS
    # ============================================================
    
    def _setup_logging(self):
        """Setup logging configuration."""
        log_config = LoggerConfig(
            level=self.config.log_level,
            log_file=self.config.log_file,
            format=self.config.log_format
        )
        
        # Override from config if available
        if self.context.config:
            log_config.level = LogLevel(
                self.context.config.get('logging.level', self.config.log_level.value)
            )
            log_file = self.context.config.get('logging.file')
            if log_file:
                log_config.log_file = Path(log_file)
        
        # Setup logger
        from ..shared.logger import setup_logger
        setup_logger(log_config)
    
    def _on_shutdown_signal(self, signum: int):
        """Handle shutdown signal."""
        logger.info(f"Shutdown signal received: {signal.Signals(signum).name}")
        self._shutdown_requested = True
        self.shutdown()
    
    def create_workflow_context(self, **kwargs) -> WorkflowContext:
        """Create a workflow context."""
        return WorkflowContext(
            entry_point=self.config.name,
            start_time=datetime.now(),
            metadata=kwargs
        )
    
    def run_workflow(self, workflow_name: str, **kwargs) -> Any:
        """
        Run a named workflow.
        
        Args:
            workflow_name: Name of workflow to run
            **kwargs: Additional workflow parameters
            
        Returns:
            Workflow result
        """
        if not self.workflow_engine:
            raise RuntimeError("Workflow engine not initialized")
        
        context = self.create_workflow_context(**kwargs)
        return self.workflow_engine.run(workflow_name, context)
    
    async def run_workflow_async(self, workflow_name: str, **kwargs) -> Any:
        """
        Run a named workflow asynchronously.
        
        Args:
            workflow_name: Name of workflow to run
            **kwargs: Additional workflow parameters
            
        Returns:
            Workflow result
        """
        if not self.workflow_engine:
            raise RuntimeError("Workflow engine not initialized")
        
        context = self.create_workflow_context(**kwargs)
        return await self.workflow_engine.run_async(workflow_name, context)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get execution metrics."""
        metrics = self._metrics.copy()
        
        if self._metrics['start_time'] and self._metrics['end_time']:
            duration = (self._metrics['end_time'] - self._metrics['start_time']).total_seconds()
            metrics['duration_seconds'] = duration
            metrics['requests_per_second'] = (
                self._metrics['requests_processed'] / duration 
                if duration > 0 else 0
            )
        
        if self.workflow_engine:
            metrics['workflow'] = self.workflow_engine.get_metrics()
        
        return metrics
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform health check.
        
        Returns:
            Health status dictionary
        """
        return {
            'status': 'healthy',
            'entry_point': self.config.name,
            'entry_type': self.config.entry_type.value,
            'version': self.config.version,
            'uptime_seconds': self.context.get_duration_seconds() if self.context.start_time else 0,
            'workflow_engine': self.workflow_engine.health_check() if self.workflow_engine else None,
            'state_manager': self.state_manager is not None,
            'timestamp': datetime.now().isoformat()
        }
    
    def request_shutdown(self):
        """Request graceful shutdown."""
        self._shutdown_requested = True
        logger.info("Shutdown requested")
    
    @property
    def is_shutdown_requested(self) -> bool:
        """Check if shutdown was requested."""
        return self._shutdown_requested or self.signal_handler.is_shutdown_requested
    
    # ============================================================
    # STATIC UTILITY METHODS
    # ============================================================
    
    @staticmethod
    def create_success_result(message: str = "", data: Any = None) -> EntryPointResult:
        """Create a success result."""
        return EntryPointResult(
            exit_code=ExitCode.SUCCESS,
            success=True,
            message=message,
            data=data
        )
    
    @staticmethod
    def create_error_result(message: str, error: Optional[Exception] = None,
                            exit_code: ExitCode = ExitCode.GENERAL_ERROR) -> EntryPointResult:
        """Create an error result."""
        return EntryPointResult(
            exit_code=exit_code,
            success=False,
            message=message,
            error=error,
            error_traceback=traceback.format_exc() if error else None
        )
    
    @staticmethod
    def main(entry_point_class: type) -> int:
        """
        Static main method for easy CLI entry.
        
        Usage:
            if __name__ == "__main__":
                sys.exit(BaseEntryPoint.main(MyEntryPoint))
        """
        entry_point = entry_point_class()
        result = entry_point.run()
        
        if result.message:
            if result.success:
                print(f"✅ {result.message}")
            else:
                print(f"❌ {result.message}", file=sys.stderr)
        
        return result.exit_code.value


# ============================================================
# EXAMPLE USAGE
# ============================================================

if __name__ == "__main__":
    # Example of how to create a custom entry point
    class ExampleEntryPoint(BaseEntryPoint):
        """Example entry point implementation."""
        
        def _get_default_config(self) -> EntryPointConfig:
            return EntryPointConfig(
                name="example",
                entry_type=EntryPointType.CLI,
                description="Example entry point"
            )
        
        def parse_arguments(self, args: Optional[List[str]] = None) -> argparse.Namespace:
            parser = self._create_argument_parser()
            parser.add_argument('--input', '-i', type=str, help='Input file')
            parser.add_argument('--output', '-o', type=str, help='Output file')
            return parser.parse_args(args)
        
        def execute(self) -> EntryPointResult:
            input_file = self.context.args.input
            output_file = self.context.args.output
            
            if not input_file:
                return self.create_error_result("Input file is required", exit_code=ExitCode.INVALID_ARGS)
            
            logger.info(f"Processing {input_file} -> {output_file}")
            
            # Simulate work
            import time
            time.sleep(1)
            
            return self.create_success_result(
                message=f"Successfully processed {input_file}",
                data={'input': input_file, 'output': output_file}
            )
    
    # Run the example
    sys.exit(BaseEntryPoint.main(ExampleEntryPoint))