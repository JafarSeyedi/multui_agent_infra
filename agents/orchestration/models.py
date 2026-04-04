from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# -------------------------------
# TASK DEFINITION
# -------------------------------
class TaskDefinition(BaseModel):
    """
    تعریف یک تسک در orchestration
    """
    task_id: str
    agent_name: str

    payload: Dict[str, Any] = Field(default_factory=dict)

    # برای DAG
    depends_on: List[str] = Field(default_factory=list)

    # برای conditional routing
    condition: Optional[str] = None

    # برای self-refine یا loop
    max_iterations: Optional[int] = None

    # متادیتا برای هر تسک
    metadata: Dict[str, Any] = Field(default_factory=dict)


# -------------------------------
# ORCHESTRATION REQUEST
# -------------------------------
class OrchestrationRequest(BaseModel):
    """
    ورودی اصلی به OrchestratorAgent
    """
    interaction_mode: str = "pipeline"
    tasks: List[TaskDefinition]

    # context مشترک برای همه استراتژی‌ها
    context: Dict[str, Any] = Field(default_factory=dict)

    # متادیتای تکمیلی
    metadata: Dict[str, Any] = Field(default_factory=dict)


# -------------------------------
# RESULT OF EACH TASK
# -------------------------------
class TaskResult(BaseModel):
    """
    نتیجه اجرای یک تسک
    """
    task_id: str
    agent_name: str

    success: bool
    output: Any = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


# -------------------------------
# FULL ORCHESTRATION RESULT
# -------------------------------
class OrchestrationResult(BaseModel):
    """
    خروجی کامل orchestration
    """
    results: List[TaskResult]

    success: bool = True

    # context نهایی که توسط استراتژی ها آپدیت شده
    final_context: Dict[str, Any] = Field(default_factory=dict)

    metadata: Dict[str, Any] = Field(default_factory=dict)
