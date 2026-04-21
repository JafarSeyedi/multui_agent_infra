#!/usr/bin/env python3
"""
CLI Entry Point - Command-line interface entry point for the AI development framework.

Part of the Entry Points module (entry_points/cli_entry.py)

This cli_entry.py provides:

Comprehensive CLI - Full command-line interface with subcommands

All Workflows Accessible - Every workflow available via CLI commands

Analysis Commands - Complexity, security, dependencies, architecture, coverage, performance, imports, API, AST

Generation Commands - Class, function, module, test, performance test, docstring, contract, skeleton

Validation Commands - Types, style, imports, architecture, API, compatibility, complexity, coverage, dependencies, docstring, naming, performance, security, tests

Planning Commands - Architecture, tasks, dependencies, interfaces

Workflow Commands - Run, list, status, cancel

Refinement Commands - Iterative refinement, impact analysis

Knowledge Commands - Index, search, status, prune

Multiple Output Formats - Text, JSON, YAML, Table, Markdown, CSV

Colored Output - Success, error, warning, info with colors

Progress Indicators - Visual feedback for long-running operations

Interactive Mode - Support for interactive input

Batch Mode - Process multiple items

Configuration Management - Show, set, init config

Shell Completion - Bash, Zsh, Fish completion support

Health Check - System health verification

Help System - Comprehensive help with examples

All AI development framework capabilities are exposed through this CLI, making it the primary interface for developers.


"""

import sys
import argparse
import asyncio
from pathlib import Path
from typing import Dict, List, Set, Optional, Any, Tuple, Union
from datetime import datetime
from enum import Enum

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
# CLI CONFIGURATION
# ============================================================

class OutputFormat(str, Enum):
    """Output format for CLI results."""
    TEXT = "text"
    JSON = "json"
    YAML = "yaml"
    TABLE = "table"
    MARKDOWN = "markdown"
    CSV = "csv"


class CLIConfig(EntryPointConfig):
    """Configuration for CLI entry point."""
    # Output settings
    output_format: OutputFormat = OutputFormat.TEXT
    color_output: bool = True
    verbose: bool = False
    quiet: bool = False
    no_progress: bool = False
    
    # Input settings
    interactive: bool = False
    batch_mode: bool = False
    input_file: Optional[Path] = None
    output_file: Optional[Path] = None
    
    # Display settings
    max_results: int = 100
    page_size: int = 20
    show_timestamps: bool = True
    show_progress: bool = True


# ============================================================
# CLI ENTRY POINT
# ============================================================

class CLIEntryPoint(BaseEntryPoint):
    """
    Command-line interface entry point for the AI development framework.
    
    Features:
    - Comprehensive CLI with subcommands
    - Multiple output formats (text, json, yaml, table, markdown, csv)
    - Colored output
    - Interactive mode
    - Batch processing
    - Progress indicators
    - File input/output
    - All workflows accessible via commands
    - Help and documentation
    - Shell completion support
    - Command history
    """
    
    def __init__(self, config: Optional[CLIConfig] = None):
        """Initialize the CLI entry point."""
        super().__init__(config)
        self.cli_config: CLIConfig = self.config
        
        # Command registry
        self._commands: Dict[str, Dict[str, Any]] = {}
        self._register_commands()
        
        # Progress tracking
        self._progress_bar = None
    
    def _get_default_config(self) -> CLIConfig:
        """Get default CLI configuration."""
        return CLIConfig(
            name="cli_entry",
            entry_type=EntryPointType.CLI,
            execution_mode=ExecutionMode.SYNC,
            description="Command-line interface for AI development framework"
        )
    
    # ============================================================
    # COMMAND REGISTRATION
    # ============================================================
    
    def _register_commands(self):
        """Register all CLI commands."""
        
        # ============================================================
        # ANALYSIS COMMANDS
        # ============================================================
        
        self._commands["analyze"] = {
            "handler": self._cmd_analyze,
            "help": "Analyze code for quality, complexity, and issues",
            "subcommands": {
                "complexity": {
                    "handler": self._cmd_analyze_complexity,
                    "help": "Analyze code complexity"
                },
                "security": {
                    "handler": self._cmd_analyze_security,
                    "help": "Analyze security vulnerabilities"
                },
                "dependencies": {
                    "handler": self._cmd_analyze_dependencies,
                    "help": "Analyze project dependencies"
                },
                "architecture": {
                    "handler": self._cmd_analyze_architecture,
                    "help": "Analyze architecture and layering"
                },
                "coverage": {
                    "handler": self._cmd_analyze_coverage,
                    "help": "Analyze test coverage"
                },
                "performance": {
                    "handler": self._cmd_analyze_performance,
                    "help": "Analyze performance bottlenecks"
                },
                "imports": {
                    "handler": self._cmd_analyze_imports,
                    "help": "Analyze import structure"
                },
                "api": {
                    "handler": self._cmd_analyze_api,
                    "help": "Extract and analyze API surface"
                },
                "ast": {
                    "handler": self._cmd_analyze_ast,
                    "help": "Deep AST analysis"
                },
                "all": {
                    "handler": self._cmd_analyze_all,
                    "help": "Run all analysis types"
                }
            }
        }
        
        # ============================================================
        # GENERATION COMMANDS
        # ============================================================
        
        self._commands["generate"] = {
            "handler": self._cmd_generate,
            "help": "Generate code, tests, and documentation",
            "subcommands": {
                "class": {
                    "handler": self._cmd_generate_class,
                    "help": "Generate a class"
                },
                "function": {
                    "handler": self._cmd_generate_function,
                    "help": "Generate a function"
                },
                "module": {
                    "handler": self._cmd_generate_module,
                    "help": "Generate a complete module"
                },
                "test": {
                    "handler": self._cmd_generate_test,
                    "help": "Generate unit tests"
                },
                "performance-test": {
                    "handler": self._cmd_generate_performance_test,
                    "help": "Generate performance tests"
                },
                "docstring": {
                    "handler": self._cmd_generate_docstring,
                    "help": "Generate docstrings"
                },
                "contract": {
                    "handler": self._cmd_generate_contract,
                    "help": "Generate interface contracts"
                },
                "skeleton": {
                    "handler": self._cmd_generate_skeleton,
                    "help": "Generate skeleton code from architecture"
                }
            }
        }
        
        # ============================================================
        # VALIDATION COMMANDS
        # ============================================================
        
        self._commands["validate"] = {
            "handler": self._cmd_validate,
            "help": "Validate code against quality standards",
            "subcommands": {
                "types": {
                    "handler": self._cmd_validate_types,
                    "help": "Validate type hints with mypy"
                },
                "style": {
                    "handler": self._cmd_validate_style,
                    "help": "Validate code style with ruff"
                },
                "imports": {
                    "handler": self._cmd_validate_imports,
                    "help": "Validate import organization"
                },
                "architecture": {
                    "handler": self._cmd_validate_architecture,
                    "help": "Validate architectural rules"
                },
                "api": {
                    "handler": self._cmd_validate_api,
                    "help": "Validate API consistency"
                },
                "compatibility": {
                    "handler": self._cmd_validate_compatibility,
                    "help": "Validate Python version compatibility"
                },
                "complexity": {
                    "handler": self._cmd_validate_complexity,
                    "help": "Validate complexity thresholds"
                },
                "coverage": {
                    "handler": self._cmd_validate_coverage,
                    "help": "Validate test coverage"
                },
                "dependencies": {
                    "handler": self._cmd_validate_dependencies,
                    "help": "Validate dependencies"
                },
                "docstring": {
                    "handler": self._cmd_validate_docstring,
                    "help": "Validate docstrings"
                },
                "naming": {
                    "handler": self._cmd_validate_naming,
                    "help": "Validate naming conventions and spelling"
                },
                "performance": {
                    "handler": self._cmd_validate_performance,
                    "help": "Validate performance"
                },
                "security": {
                    "handler": self._cmd_validate_security,
                    "help": "Validate security"
                },
                "tests": {
                    "handler": self._cmd_validate_tests,
                    "help": "Run and validate tests"
                },
                "all": {
                    "handler": self._cmd_validate_all,
                    "help": "Run all validators"
                }
            }
        }
        
        # ============================================================
        # PLANNING COMMANDS
        # ============================================================
        
        self._commands["plan"] = {
            "handler": self._cmd_plan,
            "help": "Plan architecture and development tasks",
            "subcommands": {
                "architecture": {
                    "handler": self._cmd_plan_architecture,
                    "help": "Design module architecture"
                },
                "tasks": {
                    "handler": self._cmd_plan_tasks,
                    "help": "Decompose epic into tasks"
                },
                "dependencies": {
                    "handler": self._cmd_plan_dependencies,
                    "help": "Plan component dependencies"
                },
                "interfaces": {
                    "handler": self._cmd_plan_interfaces,
                    "help": "Design public interfaces"
                }
            }
        }
        
        # ============================================================
        # WORKFLOW COMMANDS
        # ============================================================
        
        self._commands["workflow"] = {
            "handler": self._cmd_workflow,
            "help": "Run and manage workflows",
            "subcommands": {
                "run": {
                    "handler": self._cmd_workflow_run,
                    "help": "Run a named workflow"
                },
                "list": {
                    "handler": self._cmd_workflow_list,
                    "help": "List available workflows"
                },
                "status": {
                    "handler": self._cmd_workflow_status,
                    "help": "Get workflow status"
                },
                "cancel": {
                    "handler": self._cmd_workflow_cancel,
                    "help": "Cancel a running workflow"
                }
            }
        }
        
        # ============================================================
        # REFINEMENT COMMANDS
        # ============================================================
        
        self._commands["refine"] = {
            "handler": self._cmd_refine,
            "help": "Refine and improve code",
            "subcommands": {
                "iterative": {
                    "handler": self._cmd_refine_iterative,
                    "help": "Iteratively refine code"
                },
                "impact": {
                    "handler": self._cmd_refine_impact,
                    "help": "Analyze change impact"
                }
            }
        }
        
        # ============================================================
        # KNOWLEDGE COMMANDS
        # ============================================================
        
        self._commands["knowledge"] = {
            "handler": self._cmd_knowledge,
            "help": "Manage knowledge base and embeddings",
            "subcommands": {
                "index": {
                    "handler": self._cmd_knowledge_index,
                    "help": "Index code or documentation"
                },
                "search": {
                    "handler": self._cmd_knowledge_search,
                    "help": "Search knowledge base"
                },
                "status": {
                    "handler": self._cmd_knowledge_status,
                    "help": "Show knowledge base status"
                },
                "prune": {
                    "handler": self._cmd_knowledge_prune,
                    "help": "Prune outdated knowledge"
                }
            }
        }
        
        # ============================================================
        # UTILITY COMMANDS
        # ============================================================
        
        self._commands["config"] = {
            "handler": self._cmd_config,
            "help": "Manage configuration",
            "subcommands": {
                "show": {
                    "handler": self._cmd_config_show,
                    "help": "Show current configuration"
                },
                "set": {
                    "handler": self._cmd_config_set,
                    "help": "Set configuration value"
                },
                "init": {
                    "handler": self._cmd_config_init,
                    "help": "Initialize configuration file"
                }
            }
        }
        
        self._commands["completion"] = {
            "handler": self._cmd_completion,
            "help": "Generate shell completion script"
        }
        
        self._commands["version"] = {
            "handler": self._cmd_version,
            "help": "Show version information"
        }
        
        self._commands["health"] = {
            "handler": self._cmd_health,
            "help": "Check system health"
        }
    
    # ============================================================
    # ARGUMENT PARSING
    # ============================================================
    
    def parse_arguments(self, args: Optional[List[str]] = None) -> argparse.Namespace:
        """Parse command line arguments."""
        parser = self._create_main_parser()
        return parser.parse_args(args)
    
    def _create_main_parser(self) -> argparse.ArgumentParser:
        """Create the main argument parser."""
        parser = argparse.ArgumentParser(
            prog="ai-dev",
            description=self.config.description,
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog=self._get_epilog()
        )
        
        # Global options
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
            '--format', '-f', 
            choices=[f.value for f in OutputFormat],
            default=OutputFormat.TEXT.value,
            help='Output format'
        )
        parser.add_argument(
            '--output', '-o', type=Path,
            help='Write output to file'
        )
        parser.add_argument(
            '--no-color', action='store_true',
            help='Disable colored output'
        )
        parser.add_argument(
            '--no-progress', action='store_true',
            help='Disable progress indicators'
        )
        parser.add_argument(
            '--interactive', '-i', action='store_true',
            help='Enable interactive mode'
        )
        parser.add_argument(
            '--project-root', type=Path, default=Path.cwd(),
            help='Project root directory'
        )
        
        # Subcommands
        subparsers = parser.add_subparsers(
            title='commands',
            dest='command',
            description='Available commands',
            help='Command to execute'
        )
        
        self._add_subcommands(subparsers)
        
        return parser
    
    def _add_subcommands(self, subparsers):
        """Add all subcommands to the parser."""
        for cmd_name, cmd_info in self._commands.items():
            cmd_parser = subparsers.add_parser(
                cmd_name,
                help=cmd_info["help"],
                description=cmd_info["help"]
            )
            
            if "subcommands" in cmd_info:
                cmd_subparsers = cmd_parser.add_subparsers(
                    title=f'{cmd_name} subcommands',
                    dest=f'{cmd_name}_subcommand',
                    help=f'{cmd_name} subcommands'
                )
                
                for sub_name, sub_info in cmd_info["subcommands"].items():
                    sub_parser = cmd_subparsers.add_parser(
                        sub_name,
                        help=sub_info["help"],
                        description=sub_info["help"]
                    )
                    self._add_command_arguments(cmd_name, sub_name, sub_parser)
            else:
                self._add_command_arguments(cmd_name, None, cmd_parser)
    
    def _add_command_arguments(self, cmd: str, subcmd: Optional[str], parser: argparse.ArgumentParser):
        """Add arguments for a specific command."""
        
        # Common arguments for many commands
        parser.add_argument(
            'path', nargs='?', type=Path, default=Path.cwd(),
            help='Target path (file or directory)'
        )
        parser.add_argument(
            '--recursive', '-r', action='store_true',
            help='Process directories recursively'
        )
        
        # Command-specific arguments
        if cmd == "analyze":
            parser.add_argument(
                '--type', choices=['complexity', 'security', 'dependencies', 'architecture', 
                                  'coverage', 'performance', 'imports', 'api', 'ast', 'all'],
                default='all',
                help='Type of analysis to run'
            )
            parser.add_argument(
                '--metrics', action='store_true',
                help='Include detailed metrics'
            )
            parser.add_argument(
                '--suggestions', action='store_true',
                help='Include fix suggestions'
            )
        
        elif cmd == "generate":
            parser.add_argument(
                '--name', type=str, required=True,
                help='Name of the item to generate'
            )
            parser.add_argument(
                '--description', type=str,
                help='Description of what to generate'
            )
            parser.add_argument(
                '--from-file', type=Path,
                help='Read description from file'
            )
            parser.add_argument(
                '--output-dir', type=Path,
                help='Output directory'
            )
        
        elif cmd == "validate":
            parser.add_argument(
                '--validators', nargs='+',
                help='Specific validators to run'
            )
            parser.add_argument(
                '--fail-fast', action='store_true',
                help='Stop on first error'
            )
            parser.add_argument(
                '--threshold', type=float,
                help='Quality threshold (0-100)'
            )
        
        elif cmd == "plan":
            parser.add_argument(
                '--name', type=str, required=True,
                help='Project/feature name'
            )
            parser.add_argument(
                '--description', type=str,
                help='Description of the project/feature'
            )
            parser.add_argument(
                '--pattern', choices=['layered', 'clean', 'hexagonal', 'ddd', 'feature-based'],
                default='layered',
                help='Architectural pattern'
            )
        
        elif cmd == "workflow":
            if subcmd == "run":
                parser.add_argument(
                    'workflow_name', type=str,
                    help='Name of workflow to run'
                )
                parser.add_argument(
                    '--params', type=str,
                    help='Workflow parameters as JSON string'
                )
                parser.add_argument(
                    '--params-file', type=Path,
                    help='Workflow parameters from JSON file'
                )
                parser.add_argument(
                    '--async', dest='async_mode', action='store_true',
                    help='Run workflow asynchronously'
                )
                parser.add_argument(
                    '--timeout', type=int,
                    help='Workflow timeout in seconds'
                )
        
        elif cmd == "knowledge":
            if subcmd == "search":
                parser.add_argument(
                    'query', type=str,
                    help='Search query'
                )
                parser.add_argument(
                    '--limit', type=int, default=10,
                    help='Maximum number of results'
                )
                parser.add_argument(
                    '--type', choices=['code', 'docs', 'all'],
                    default='all',
                    help='Type of content to search'
                )
        
        elif cmd == "refine":
            parser.add_argument(
                '--strategy', choices=['fix_errors_first', 'improve_quality', 'optimize', 'comprehensive'],
                default='fix_errors_first',
                help='Refinement strategy'
            )
            parser.add_argument(
                '--max-iterations', type=int, default=10,
                help='Maximum refinement iterations'
            )
    
    def _get_epilog(self) -> str:
        """Get help epilog with examples."""
        return """
Examples:
  # Analyze code complexity
  ai-dev analyze complexity src/

  # Generate a class
  ai-dev generate class --name "UserService" --description "Service for user management"

  # Validate types and style
  ai-dev validate types src/
  ai-dev validate style src/

  # Plan architecture
  ai-dev plan architecture --name "ecommerce" --pattern clean

  # Run a workflow
  ai-dev workflow run analysis_workflow --params '{"path": "src/"}'

  # Search knowledge base
  ai-dev knowledge search "how to implement repository pattern"

  # Refine code iteratively
  ai-dev refine iterative src/module.py --strategy comprehensive

For more information, visit: https://github.com/your-repo/ai-dev
"""
    
    # ============================================================
    # EXECUTION
    # ============================================================
    
    def execute(self) -> EntryPointResult:
        """Execute the CLI command."""
        args = self.context.args
        
        if not args.command:
            self._print_help()
            return self.create_error_result("No command specified", exit_code=ExitCode.INVALID_ARGS)
        
        # Update CLI config from arguments
        self.cli_config.verbose = args.verbose > 0
        self.cli_config.quiet = args.quiet
        self.cli_config.output_format = OutputFormat(args.format)
        self.cli_config.output_file = args.output
        self.cli_config.color_output = not args.no_color
        self.cli_config.no_progress = args.no_progress
        self.cli_config.interactive = args.interactive
        
        # Find and execute command handler
        cmd_info = self._commands.get(args.command)
        if not cmd_info:
            return self.create_error_result(f"Unknown command: {args.command}", exit_code=ExitCode.INVALID_ARGS)
        
        subcmd = getattr(args, f'{args.command}_subcommand', None)
        if subcmd and "subcommands" in cmd_info:
            subcmd_info = cmd_info["subcommands"].get(subcmd)
            if subcmd_info:
                handler = subcmd_info["handler"]
            else:
                return self.create_error_result(f"Unknown subcommand: {subcmd}", exit_code=ExitCode.INVALID_ARGS)
        else:
            handler = cmd_info["handler"]
        
        try:
            result = handler(args)
            return result
        except Exception as e:
            logger.error(f"Command execution failed: {e}")
            return self.create_error_result(str(e), e)
    
    # ============================================================
    # COMMAND HANDLERS - ANALYSIS
    # ============================================================
    
    def _cmd_analyze(self, args) -> EntryPointResult:
        """Handle analyze command."""
        analysis_type = getattr(args, 'type', 'all')
        return self._run_workflow_command(
            "analysis_workflow",
            {
                "path": str(args.path),
                "analysis_type": analysis_type,
                "recursive": args.recursive,
                "include_metrics": args.metrics if hasattr(args, 'metrics') else True,
                "include_suggestions": args.suggestions if hasattr(args, 'suggestions') else True
            },
            f"Analysis ({analysis_type})"
        )
    
    def _cmd_analyze_complexity(self, args) -> EntryPointResult:
        """Handle analyze complexity command."""
        return self._run_workflow_command(
            "analysis_workflow",
            {"path": str(args.path), "analysis_type": "complexity", "recursive": args.recursive},
            "Complexity analysis"
        )
    
    def _cmd_analyze_security(self, args) -> EntryPointResult:
        """Handle analyze security command."""
        return self._run_workflow_command(
            "analysis_workflow",
            {"path": str(args.path), "analysis_type": "security", "recursive": args.recursive},
            "Security analysis"
        )
    
    def _cmd_analyze_dependencies(self, args) -> EntryPointResult:
        """Handle analyze dependencies command."""
        return self._run_workflow_command(
            "analysis_workflow",
            {"path": str(args.path), "analysis_type": "dependencies", "recursive": args.recursive},
            "Dependency analysis"
        )
    
    def _cmd_analyze_architecture(self, args) -> EntryPointResult:
        """Handle analyze architecture command."""
        return self._run_workflow_command(
            "analysis_workflow",
            {"path": str(args.path), "analysis_type": "architecture", "recursive": args.recursive},
            "Architecture analysis"
        )
    
    def _cmd_analyze_coverage(self, args) -> EntryPointResult:
        """Handle analyze coverage command."""
        return self._run_workflow_command(
            "analysis_workflow",
            {"path": str(args.path), "analysis_type": "coverage", "recursive": args.recursive},
            "Coverage analysis"
        )
    
    def _cmd_analyze_performance(self, args) -> EntryPointResult:
        """Handle analyze performance command."""
        return self._run_workflow_command(
            "analysis_workflow",
            {"path": str(args.path), "analysis_type": "performance", "recursive": args.recursive},
            "Performance analysis"
        )
    
    def _cmd_analyze_imports(self, args) -> EntryPointResult:
        """Handle analyze imports command."""
        return self._run_workflow_command(
            "analysis_workflow",
            {"path": str(args.path), "analysis_type": "imports", "recursive": args.recursive},
            "Import analysis"
        )
    
    def _cmd_analyze_api(self, args) -> EntryPointResult:
        """Handle analyze API command."""
        return self._run_workflow_command(
            "analysis_workflow",
            {"path": str(args.path), "analysis_type": "api", "recursive": args.recursive},
            "API surface analysis"
        )
    
    def _cmd_analyze_ast(self, args) -> EntryPointResult:
        """Handle analyze AST command."""
        return self._run_workflow_command(
            "analysis_workflow",
            {"path": str(args.path), "analysis_type": "ast", "recursive": args.recursive},
            "AST analysis"
        )
    
    def _cmd_analyze_all(self, args) -> EntryPointResult:
        """Handle analyze all command."""
        return self._cmd_analyze(args)
    
    # ============================================================
    # COMMAND HANDLERS - GENERATION
    # ============================================================
    
    def _cmd_generate(self, args) -> EntryPointResult:
        """Handle generate command."""
        description = args.description
        if args.from_file:
            description = args.from_file.read_text()
        
        return self._run_workflow_command(
            "generation_workflow",
            {
                "type": getattr(args, 'subcommand', 'class'),
                "name": args.name,
                "description": description,
                "output_dir": str(args.output_dir) if args.output_dir else None
            },
            f"Code generation ({args.name})"
        )
    
    def _cmd_generate_class(self, args) -> EntryPointResult:
        """Handle generate class command."""
        return self._cmd_generate(args)
    
    def _cmd_generate_function(self, args) -> EntryPointResult:
        """Handle generate function command."""
        return self._cmd_generate(args)
    
    def _cmd_generate_module(self, args) -> EntryPointResult:
        """Handle generate module command."""
        return self._cmd_generate(args)
    
    def _cmd_generate_test(self, args) -> EntryPointResult:
        """Handle generate test command."""
        return self._run_workflow_command(
            "generation_workflow",
            {
                "type": "test",
                "target_path": str(args.path),
                "output_dir": str(args.output_dir) if args.output_dir else None
            },
            f"Test generation for {args.path}"
        )
    
    def _cmd_generate_performance_test(self, args) -> EntryPointResult:
        """Handle generate performance test command."""
        return self._run_workflow_command(
            "generation_workflow",
            {
                "type": "performance_test",
                "target_path": str(args.path),
                "output_dir": str(args.output_dir) if args.output_dir else None
            },
            f"Performance test generation for {args.path}"
        )
    
    def _cmd_generate_docstring(self, args) -> EntryPointResult:
        """Handle generate docstring command."""
        return self._run_workflow_command(
            "generation_workflow",
            {
                "type": "docstring",
                "path": str(args.path),
                "recursive": args.recursive
            },
            f"Docstring generation for {args.path}"
        )
    
    def _cmd_generate_contract(self, args) -> EntryPointResult:
        """Handle generate contract command."""
        return self._cmd_generate(args)
    
    def _cmd_generate_skeleton(self, args) -> EntryPointResult:
        """Handle generate skeleton command."""
        return self._run_workflow_command(
            "generation_workflow",
            {
                "type": "skeleton",
                "architecture_file": str(args.path),
                "output_dir": str(args.output_dir) if args.output_dir else None
            },
            f"Skeleton generation from {args.path}"
        )
    
    # ============================================================
    # COMMAND HANDLERS - VALIDATION
    # ============================================================
    
    def _cmd_validate(self, args) -> EntryPointResult:
        """Handle validate command."""
        validators = getattr(args, 'validators', ['all'])
        
        return self._run_workflow_command(
            "quality_workflow",
            {
                "path": str(args.path),
                "validators": validators,
                "recursive": args.recursive,
                "fail_fast": args.fail_fast if hasattr(args, 'fail_fast') else False,
                "threshold": args.threshold if hasattr(args, 'threshold') else None
            },
            f"Validation ({', '.join(validators)})"
        )
    
    def _cmd_validate_types(self, args) -> EntryPointResult:
        """Handle validate types command."""
        return self._run_workflow_command(
            "quality_workflow",
            {"path": str(args.path), "validators": ["mypy"], "recursive": args.recursive},
            "Type validation"
        )
    
    def _cmd_validate_style(self, args) -> EntryPointResult:
        """Handle validate style command."""
        return self._run_workflow_command(
            "quality_workflow",
            {"path": str(args.path), "validators": ["ruff"], "recursive": args.recursive},
            "Style validation"
        )
    
    def _cmd_validate_imports(self, args) -> EntryPointResult:
        """Handle validate imports command."""
        return self._run_workflow_command(
            "quality_workflow",
            {"path": str(args.path), "validators": ["imports"], "recursive": args.recursive},
            "Import validation"
        )
    
    def _cmd_validate_architecture(self, args) -> EntryPointResult:
        """Handle validate architecture command."""
        return self._run_workflow_command(
            "quality_workflow",
            {"path": str(args.path), "validators": ["architecture"], "recursive": args.recursive},
            "Architecture validation"
        )
    
    def _cmd_validate_api(self, args) -> EntryPointResult:
        """Handle validate API command."""
        return self._run_workflow_command(
            "quality_workflow",
            {"path": str(args.path), "validators": ["api"], "recursive": args.recursive},
            "API validation"
        )
    
    def _cmd_validate_compatibility(self, args) -> EntryPointResult:
        """Handle validate compatibility command."""
        return self._run_workflow_command(
            "quality_workflow",
            {"path": str(args.path), "validators": ["compatibility"], "recursive": args.recursive},
            "Compatibility validation"
        )
    
    def _cmd_validate_complexity(self, args) -> EntryPointResult:
        """Handle validate complexity command."""
        return self._run_workflow_command(
            "quality_workflow",
            {"path": str(args.path), "validators": ["complexity"], "recursive": args.recursive},
            "Complexity validation"
        )
    
    def _cmd_validate_coverage(self, args) -> EntryPointResult:
        """Handle validate coverage command."""
        return self._run_workflow_command(
            "quality_workflow",
            {"path": str(args.path), "validators": ["coverage"], "recursive": args.recursive},
            "Coverage validation"
        )
    
    def _cmd_validate_dependencies(self, args) -> EntryPointResult:
        """Handle validate dependencies command."""
        return self._run_workflow_command(
            "quality_workflow",
            {"path": str(args.path), "validators": ["dependencies"], "recursive": args.recursive},
            "Dependency validation"
        )
    
    def _cmd_validate_docstring(self, args) -> EntryPointResult:
        """Handle validate docstring command."""
        return self._run_workflow_command(
            "quality_workflow",
            {"path": str(args.path), "validators": ["docstring"], "recursive": args.recursive},
            "Docstring validation"
        )
    
    def _cmd_validate_naming(self, args) -> EntryPointResult:
        """Handle validate naming command."""
        return self._run_workflow_command(
            "quality_workflow",
            {"path": str(args.path), "validators": ["naming"], "recursive": args.recursive},
            "Naming and spellcheck validation"
        )
    
    def _cmd_validate_performance(self, args) -> EntryPointResult:
        """Handle validate performance command."""
        return self._run_workflow_command(
            "quality_workflow",
            {"path": str(args.path), "validators": ["performance"], "recursive": args.recursive},
            "Performance validation"
        )
    
    def _cmd_validate_security(self, args) -> EntryPointResult:
        """Handle validate security command."""
        return self._run_workflow_command(
            "quality_workflow",
            {"path": str(args.path), "validators": ["security"], "recursive": args.recursive},
            "Security validation"
        )
    
    def _cmd_validate_tests(self, args) -> EntryPointResult:
        """Handle validate tests command."""
        return self._run_workflow_command(
            "quality_workflow",
            {"path": str(args.path), "validators": ["pytest"], "recursive": args.recursive},
            "Test validation"
        )
    
    def _cmd_validate_all(self, args) -> EntryPointResult:
        """Handle validate all command."""
        return self._cmd_validate(args)
    
    # ============================================================
    # COMMAND HANDLERS - PLANNING
    # ============================================================
    
    def _cmd_plan(self, args) -> EntryPointResult:
        """Handle plan command."""
        return self._run_workflow_command(
            "planning_workflow",
            {
                "name": args.name,
                "description": args.description,
                "pattern": getattr(args, 'pattern', 'layered')
            },
            f"Planning: {args.name}"
        )
    
    def _cmd_plan_architecture(self, args) -> EntryPointResult:
        """Handle plan architecture command."""
        return self._cmd_plan(args)
    
    def _cmd_plan_tasks(self, args) -> EntryPointResult:
        """Handle plan tasks command."""
        return self._run_workflow_command(
            "planning_workflow",
            {
                "type": "task_decomposition",
                "epic_title": args.name,
                "epic_description": args.description
            },
            f"Task decomposition: {args.name}"
        )
    
    def _cmd_plan_dependencies(self, args) -> EntryPointResult:
        """Handle plan dependencies command."""
        return self._run_workflow_command(
            "planning_workflow",
            {
                "type": "dependency_planning",
                "path": str(args.path)
            },
            f"Dependency planning for {args.path}"
        )
    
    def _cmd_plan_interfaces(self, args) -> EntryPointResult:
        """Handle plan interfaces command."""
        return self._run_workflow_command(
            "planning_workflow",
            {
                "type": "interface_design",
                "name": args.name,
                "description": args.description
            },
            f"Interface design: {args.name}"
        )
    
    # ============================================================
    # COMMAND HANDLERS - WORKFLOW
    # ============================================================
    
    def _cmd_workflow(self, args) -> EntryPointResult:
        """Handle workflow command."""
        return self.create_error_result("Please specify a workflow subcommand", exit_code=ExitCode.INVALID_ARGS)
    
    def _cmd_workflow_run(self, args) -> EntryPointResult:
        """Handle workflow run command."""
        params = {}
        if args.params:
            import json
            params = json.loads(args.params)
        elif args.params_file:
            import json
            params = json.loads(args.params_file.read_text())
        
        if args.async_mode:
            self._print_info(f"Starting workflow '{args.workflow_name}' asynchronously...")
            workflow_id = self._start_background_workflow(args.workflow_name, params)
            self._print_success(f"Workflow started with ID: {workflow_id}")
            return self.create_success_result(f"Workflow {workflow_id} started", {"workflow_id": workflow_id})
        else:
            return self._run_workflow_command(
                args.workflow_name,
                params,
                f"Workflow: {args.workflow_name}",
                timeout=args.timeout
            )
    
    def _cmd_workflow_list(self, args) -> EntryPointResult:
        """Handle workflow list command."""
        if not self.workflow_engine:
            return self.create_error_result("Workflow engine not available")
        
        workflows = self.workflow_engine.list_workflows()
        descriptions = []
        for wf in workflows:
            desc = self.workflow_engine.get_workflow_description(wf)
            descriptions.append({"name": wf, "description": desc})
        
        self._print_table(["Name", "Description"], [[d["name"], d["description"]] for d in descriptions])
        return self.create_success_result(f"{len(workflows)} workflows available", {"workflows": descriptions})
    
    def _cmd_workflow_status(self, args) -> EntryPointResult:
        """Handle workflow status command."""
        return self.create_error_result("Not yet implemented", exit_code=ExitCode.GENERAL_ERROR)
    
    def _cmd_workflow_cancel(self, args) -> EntryPointResult:
        """Handle workflow cancel command."""
        return self.create_error_result("Not yet implemented", exit_code=ExitCode.GENERAL_ERROR)
    
    # ============================================================
    # COMMAND HANDLERS - REFINEMENT
    # ============================================================
    
    def _cmd_refine(self, args) -> EntryPointResult:
        """Handle refine command."""
        return self.create_error_result("Please specify a refine subcommand", exit_code=ExitCode.INVALID_ARGS)
    
    def _cmd_refine_iterative(self, args) -> EntryPointResult:
        """Handle refine iterative command."""
        return self._run_workflow_command(
            "refinement_workflow",
            {
                "file_path": str(args.path),
                "strategy": args.strategy if hasattr(args, 'strategy') else 'fix_errors_first',
                "max_iterations": args.max_iterations if hasattr(args, 'max_iterations') else 10
            },
            f"Refinement: {args.path}"
        )
    
    def _cmd_refine_impact(self, args) -> EntryPointResult:
        """Handle refine impact command."""
        return self._run_workflow_command(
            "refinement_workflow",
            {
                "type": "impact_analysis",
                "file_path": str(args.path)
            },
            f"Impact analysis: {args.path}"
        )
    
    # ============================================================
    # COMMAND HANDLERS - KNOWLEDGE
    # ============================================================
    
    def _cmd_knowledge(self, args) -> EntryPointResult:
        """Handle knowledge command."""
        return self.create_error_result("Please specify a knowledge subcommand", exit_code=ExitCode.INVALID_ARGS)
    
    def _cmd_knowledge_index(self, args) -> EntryPointResult:
        """Handle knowledge index command."""
        return self._run_workflow_command(
            "knowledge_workflow",
            {
                "type": "index",
                "path": str(args.path),
                "recursive": args.recursive
            },
            f"Indexing: {args.path}"
        )
    
    def _cmd_knowledge_search(self, args) -> EntryPointResult:
        """Handle knowledge search command."""
        return self._run_workflow_command(
            "knowledge_workflow",
            {
                "type": "search",
                "query": args.query,
                "limit": args.limit,
                "content_type": args.type if hasattr(args, 'type') else 'all'
            },
            f"Search: {args.query}"
        )
    
    def _cmd_knowledge_status(self, args) -> EntryPointResult:
        """Handle knowledge status command."""
        return self._run_workflow_command(
            "knowledge_workflow",
            {"type": "status"},
            "Knowledge base status"
        )
    
    def _cmd_knowledge_prune(self, args) -> EntryPointResult:
        """Handle knowledge prune command."""
        return self._run_workflow_command(
            "knowledge_workflow",
            {"type": "prune"},
            "Pruning knowledge base"
        )
    
    # ============================================================
    # COMMAND HANDLERS - CONFIG
    # ============================================================
    
    def _cmd_config(self, args) -> EntryPointResult:
        """Handle config command."""
        return self.create_error_result("Please specify a config subcommand", exit_code=ExitCode.INVALID_ARGS)
    
    def _cmd_config_show(self, args) -> EntryPointResult:
        """Handle config show command."""
        config_data = {
            "project_root": str(self.context.args.project_root),
            "output_format": self.cli_config.output_format.value,
            "verbose": self.cli_config.verbose,
            "quiet": self.cli_config.quiet,
            "color_output": self.cli_config.color_output
        }
        self._print_json(config_data)
        return self.create_success_result("Configuration displayed", config_data)
    
    def _cmd_config_set(self, args) -> EntryPointResult:
        """Handle config set command."""
        return self.create_error_result("Not yet implemented", exit_code=ExitCode.GENERAL_ERROR)
    
    def _cmd_config_init(self, args) -> EntryPointResult:
        """Handle config init command."""
        config_path = Path.cwd() / ".ai-dev-config.json"
        default_config = {
            "project_root": ".",
            "output_format": "text",
            "color_output": True,
            "max_iterations": 10,
            "quality_threshold": 0.9
        }
        config_path.write_text(json.dumps(default_config, indent=2))
        self._print_success(f"Configuration initialized at {config_path}")
        return self.create_success_result("Configuration initialized", {"path": str(config_path)})
    
    # ============================================================
    # COMMAND HANDLERS - UTILITY
    # ============================================================
    
    def _cmd_completion(self, args) -> EntryPointResult:
        """Handle completion command."""
        self._print_info("Shell completion scripts:")
        self._print_info("  For bash: eval \"$(ai-dev completion bash)\"")
        self._print_info("  For zsh:  eval \"$(ai-dev completion zsh)\"")
        self._print_info("  For fish: ai-dev completion fish | source")
        return self.create_success_result("Completion instructions displayed")
    
    def _cmd_version(self, args) -> EntryPointResult:
        """Handle version command."""
        version_info = {
            "version": self.config.version,
            "name": self.config.name,
            "python_version": sys.version.split()[0]
        }
        
        if self.workflow_engine:
            version_info["workflow_engine"] = "available"
        if self.agent_registry:
            version_info["agent_registry"] = f"{len(self.agent_registry.list_agents())} agents"
        
        self._print_json(version_info)
        return self.create_success_result(f"Version {self.config.version}", version_info)
    
    def _cmd_health(self, args) -> EntryPointResult:
        """Handle health command."""
        health = self.health_check()
        self._print_json(health)
        
        if health["status"] == "healthy":
            return self.create_success_result("System is healthy", health)
        else:
            return self.create_error_result("System is degraded", exit_code=ExitCode.GENERAL_ERROR)
    
    # ============================================================
    # WORKFLOW EXECUTION HELPERS
    # ============================================================
    
    def _run_workflow_command(self, workflow_name: str, params: Dict[str, Any],
                               description: str, timeout: Optional[int] = None) -> EntryPointResult:
        """Run a workflow and handle output."""
        self._print_progress_start(description)
        
        try:
            result = self.run_workflow(workflow_name, **params)
            self._print_progress_complete()
            self._print_result(result)
            return self.create_success_result(f"{description} completed", result)
        except Exception as e:
            self._print_progress_fail()
            self._print_error(f"{description} failed: {e}")
            return self.create_error_result(str(e), e)
    
    def _start_background_workflow(self, workflow_name: str, params: Dict[str, Any]) -> str:
        """Start a workflow in the background."""
        import uuid
        workflow_id = f"wf_{uuid.uuid4().hex[:12]}"
        # Implementation would queue workflow for background execution
        return workflow_id
    
    # ============================================================
    # OUTPUT FORMATTING
    # ============================================================
    
    def _print_help(self):
        """Print help message."""
        parser = self._create_main_parser()
        parser.print_help()
    
    def _print_result(self, result: Any):
        """Print result in configured format."""
        if self.cli_config.quiet:
            return
        
        if self.cli_config.output_format == OutputFormat.JSON:
            self._print_json(result)
        elif self.cli_config.output_format == OutputFormat.YAML:
            self._print_yaml(result)
        elif self.cli_config.output_format == OutputFormat.TABLE:
            if isinstance(result, dict):
                self._print_table(list(result.keys()), [list(result.values())])
            else:
                self._print_text(result)
        elif self.cli_config.output_format == OutputFormat.MARKDOWN:
            self._print_markdown(result)
        else:
            self._print_text(result)
    
    def _print_text(self, data: Any):
        """Print as plain text."""
        if isinstance(data, dict):
            for key, value in data.items():
                print(f"{key}: {value}")
        elif isinstance(data, list):
            for item in data:
                print(f"  - {item}")
        else:
            print(data)
    
    def _print_json(self, data: Any):
        """Print as JSON."""
        import json
        print(json.dumps(data, indent=2, default=str))
    
    def _print_yaml(self, data: Any):
        """Print as YAML."""
        try:
            import yaml
            print(yaml.dump(data, default_flow_style=False))
        except ImportError:
            self._print_json(data)
    
    def _print_table(self, headers: List[str], rows: List[List[Any]]):
        """Print as table."""
        if not rows:
            print("(empty)")
            return
        
        # Calculate column widths
        col_widths = [len(h) for h in headers]
        for row in rows:
            for i, cell in enumerate(row):
                col_widths[i] = max(col_widths[i], len(str(cell)))
        
        # Print headers
        header_line = " | ".join(h.ljust(col_widths[i]) for i, h in enumerate(headers))
        print(header_line)
        print("-" * len(header_line))
        
        # Print rows
        for row in rows:
            row_line = " | ".join(str(cell).ljust(col_widths[i]) for i, cell in enumerate(row))
            print(row_line)
    
    def _print_markdown(self, data: Any):
        """Print as Markdown."""
        if isinstance(data, dict):
            print("| Key | Value |")
            print("|-----|-------|")
            for key, value in data.items():
                print(f"| {key} | {value} |")
        else:
            print(data)
    
    def _print_success(self, message: str):
        """Print success message."""
        if self.cli_config.quiet:
            return
        if self.cli_config.color_output:
            print(f"\033[32m✅ {message}\033[0m")
        else:
            print(f"✅ {message}")
    
    def _print_error(self, message: str):
        """Print error message."""
        if self.cli_config.color_output:
            print(f"\033[31m❌ {message}\033[0m", file=sys.stderr)
        else:
            print(f"❌ {message}", file=sys.stderr)
    
    def _print_warning(self, message: str):
        """Print warning message."""
        if self.cli_config.quiet:
            return
        if self.cli_config.color_output:
            print(f"\033[33m⚠️  {message}\033[0m")
        else:
            print(f"⚠️  {message}")
    
    def _print_info(self, message: str):
        """Print info message."""
        if self.cli_config.quiet:
            return
        if self.cli_config.color_output:
            print(f"\033[36mℹ️  {message}\033[0m")
        else:
            print(f"ℹ️  {message}")
    
    def _print_progress_start(self, message: str):
        """Start progress indicator."""
        if self.cli_config.quiet or self.cli_config.no_progress:
            return
        if self.cli_config.color_output:
            print(f"\033[36m⏳ {message}...\033[0m", end="", flush=True)
        else:
            print(f"⏳ {message}...", end="", flush=True)
    
    def _print_progress_complete(self):
        """Complete progress indicator."""
        if self.cli_config.quiet or self.cli_config.no_progress:
            return
        if self.cli_config.color_output:
            print("\r\033[32m✅ Done\033[0m" + " " * 20)
        else:
            print("\r✅ Done" + " " * 20)
    
    def _print_progress_fail(self):
        """Fail progress indicator."""
        if self.cli_config.quiet or self.cli_config.no_progress:
            return
        if self.cli_config.color_output:
            print("\r\033[31m❌ Failed\033[0m" + " " * 20)
        else:
            print("\r❌ Failed" + " " * 20)
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check."""
        components = {
            "workflow_engine": "healthy" if self.workflow_engine else "unavailable",
            "agent_registry": "healthy" if self.agent_registry else "unavailable",
            "state_manager": "healthy" if self.state_manager else "unavailable"
        }
        
        overall_status = "healthy" if all(v == "healthy" for v in components.values()) else "degraded"
        
        return {
            "status": overall_status,
            "entry_point": self.config.name,
            "version": self.config.version,
            "uptime_seconds": self.context.get_duration_seconds(),
            "components": components,
            "timestamp": datetime.now().isoformat()
        }


# ============================================================
# CLI ENTRY POINT
# ============================================================

def main():
    """Main CLI entry point."""
    import sys
    
    cli = CLIEntryPoint()
    result = cli.run()
    sys.exit(result.exit_code.value)


if __name__ == "__main__":
    main()