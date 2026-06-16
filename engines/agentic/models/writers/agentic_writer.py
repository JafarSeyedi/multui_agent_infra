# engines/agentic/models/writers/agentic_writer.py
from __future__ import annotations

from ..agentic_models import WorkflowRun


def write_workflow_run(run: WorkflowRun) -> dict:
    return {
        "workflow_id": run.workflow_id,
        "workflow": run.workflow,
        "inputs": run.inputs,
        "outputs": run.outputs,
        "status": run.status,
    }
