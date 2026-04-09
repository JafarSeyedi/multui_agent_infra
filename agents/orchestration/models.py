# agents/orchestration/models.py
from typing import Any, Dict, List, Optional, Literal
from datetime import datetime
from pydantic import BaseModel, Field
import uuid


# -------------------------------
# TASK DEFINITION
# -------------------------------
class TaskDefinition(BaseModel):
    """تعریف یک تسک در orchestration"""
    task_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    agent_name: str

    payload: Dict[str, Any] = Field(default_factory=dict)
    
    # فیلدهای اضافی برای autogen و سایر backend ها
    description: Optional[str] = None
    system_message: Optional[str] = None

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
    """ورودی اصلی به OrchestratorAgent"""
    workflow_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    scenario: str = "pipeline"
    tasks: List[TaskDefinition]

    # context مشترک برای همه استراتژی‌ها
    context: Dict[str, Any] = Field(default_factory=dict)

    # متادیتای تکمیلی
    metadata: Dict[str, Any] = Field(default_factory=dict)


# -------------------------------
# RESULT OF EACH TASK
# -------------------------------
class TaskResult(BaseModel):
    """نتیجه اجرای یک تسک"""
    task_id: str
    agent_name: str

    success: bool
    output: Any = None
    error: Optional[str] = None
    
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    metadata: Dict[str, Any] = Field(default_factory=dict)


# -------------------------------
# FULL ORCHESTRATION RESULT
# -------------------------------
class OrchestrationResult(BaseModel):
    """خروجی کامل orchestration"""
    workflow_id: Optional[str] = None
    scenario: Optional[str] = None
    
    results: List[TaskResult]
    success: bool = True

    # context نهایی که توسط استراتژی ها آپدیت شده
    final_context: Dict[str, Any] = Field(default_factory=dict)

    # tracking اجرا
    backend_used: str = "native"
    status: Literal["success", "partial", "failed"] = "success"
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # یادداشت‌ها و لاگ‌ها
    notes: List[str] = Field(default_factory=list)

    metadata: Dict[str, Any] = Field(default_factory=dict)


# -------------------------------
# INTERACTION MODELS
# -------------------------------
class AgentMessage(BaseModel):
    message_id: str
    sender: str
    recipient: str
    message_type: str
    payload: Dict[str, Any] = Field(default_factory=dict)
    correlation_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class PipelineStep(BaseModel):
    step_id: str
    pipeline_name: str
    step_name: str
    sequence: int
    status: Literal["pending", "running", "completed", "failed", "skipped"] = "pending"
    metadata: Dict[str, Any] = Field(default_factory=dict)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class AgentInteraction(BaseModel):
    interaction_id: str
    user_id: Optional[str] = None
    agent_name: str
    request: Dict[str, Any] = Field(default_factory=dict)
    response: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ConversationTurn(BaseModel):
    conversation_id: str
    speaker: str
    message: str
    metadata: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
