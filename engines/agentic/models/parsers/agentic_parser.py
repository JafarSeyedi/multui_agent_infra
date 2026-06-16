# engines/agentic/models/parsers/agentic_parser.py
from __future__ import annotations

from ..agentic_models import WorkflowRun


def parse_workflow_run(data: dict) -> WorkflowRun:
    return WorkflowRun(
        workflow_id=data.get("workflow_id", ""),
        workflow=data.get("workflow", ""),
        inputs=data.get("inputs", {}),
        outputs=data.get("outputs", {}),
        status=data.get("status", "pending"),
    )
