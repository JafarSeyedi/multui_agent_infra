"""Visitor pattern for model validation and export.

Provides a ModelVisitor interface and a Visitable protocol
that model classes can implement to accept visitors.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Protocol


class Visitable(Protocol):
    """Protocol for visitable model objects."""
    def accept(self, visitor: ModelVisitor) -> Any: ...


class ModelVisitor(ABC):
    """Abstract visitor for process models.

    Implementations can traverse model trees to perform
    validation, export, metrics calculation, or simulation.
    """

    @abstractmethod
    def visit_process(self, process: Any) -> Any: ...
    @abstractmethod
    def visit_activity(self, activity: Any) -> Any: ...
    @abstractmethod
    def visit_gateway(self, gateway: Any) -> Any: ...
    @abstractmethod
    def visit_event(self, event: Any) -> Any: ...
    @abstractmethod
    def visit_sequence_flow(self, flow: Any) -> Any: ...
    @abstractmethod
    def visit_subprocess(self, subprocess: Any) -> Any: ...

    def visit(self, node: Any) -> Any:
        """Dispatch to the appropriate visit_* method based on node type."""
        from ...document.models.osdm_models import (
            Process, SubProcess, Activity, Gateway, Event, SequenceFlow,
        )
        if isinstance(node, Process):
            return self.visit_process(node)
        if isinstance(node, SubProcess):
            return self.visit_subprocess(node)
        if isinstance(node, Activity):
            return self.visit_activity(node)
        if isinstance(node, Gateway):
            return self.visit_gateway(node)
        if isinstance(node, Event):
            return self.visit_event(node)
        if isinstance(node, SequenceFlow):
            return self.visit_sequence_flow(node)
        return None
