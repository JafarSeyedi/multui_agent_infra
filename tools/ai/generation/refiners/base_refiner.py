#!/usr/bin/env python3
"""
Base Refiner - Abstract base classes for all refiners.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from enum import Enum


class RefinementScope(str, Enum):
    """Scope of refinement operation."""
    LINE = "line"
    FUNCTION = "function"
    CLASS = "class"
    MODULE = "module"
    PACKAGE = "package"
    CROSS_MODULE = "cross_module"


class ChangeType(str, Enum):
    """Type of change being made."""
    FIX = "fix"                    # Bug fix
    STYLE = "style"               # Style/formatting
    REFACTOR = "refactor"         # Code restructuring
    OPTIMIZE = "optimize"         # Performance optimization
    FEATURE = "feature"           # Feature addition
    API_CHANGE = "api_change"     # Breaking API change
    DEPENDENCY = "dependency"     # Dependency update


@dataclass
class RefinementContext:
    """Context for refinement operation."""
    scope: RefinementScope
    change_type: ChangeType
    target_file: Path
    affected_files: List[Path] = field(default_factory=list)
    affected_tests: List[Path] = field(default_factory=list)
    affected_docs: List[Path] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    breaking_changes: bool = False
    requires_migration: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RefinementResult:
    """Result of refinement operation."""
    success: bool
    original_code: str
    refined_code: str
    context: RefinementContext
    changes_made: List[str] = field(default_factory=list)
    functionality_preserved: bool = True
    tests_updated: bool = False
    docs_updated: bool = False
    validation_errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    backup_path: Optional[Path] = None
    diff: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseRefiner(ABC):
    """Abstract base class for all refiners."""
    
    def __init__(self, config: Optional[Any] = None):
        self.config = config
    
    @abstractmethod
    def refine(self, code: str, context: RefinementContext) -> RefinementResult:
        """Refine code according to context."""
        pass
    
    @abstractmethod
    def can_handle(self, context: RefinementContext) -> bool:
        """Check if this refiner can handle the context."""
        pass
    
    @abstractmethod
    def get_priority(self) -> int:
        """Get priority (lower = higher priority)."""
        pass


class SafetyCheck(ABC):
    """Abstract base class for safety checks."""
    
    @abstractmethod
    def check(self, original: str, refined: str, context: RefinementContext) -> Tuple[bool, List[str]]:
        """Check if refinement is safe. Returns (is_safe, issues)."""
        pass