# engines/agentic/tests/test_agentic_models.py
from engines.agentic.models.agentic_models import WorkflowRun, DelegateTask
from engines.agentic.models.parsers.agentic_parser import parse_workflow_run
from engines.agentic.models.writers.agentic_writer import write_workflow_run


def test_workflow_run():
    run = WorkflowRun(workflow="data_pipeline", inputs={"source": "s3"})
    assert run.workflow == "data_pipeline"


def test_workflow_roundtrip():
    run = WorkflowRun(workflow_id="wf-1", workflow="etl", inputs={"table": "users"}, outputs={"count": 100}, status="completed")
    data = write_workflow_run(run)
    parsed = parse_workflow_run(data)
    assert parsed.status == "completed"
    assert parsed.outputs["count"] == 100


def test_delegate_task():
    task = DelegateTask(task="summarize", context={"text": "long article"})
    assert task.task == "summarize"
