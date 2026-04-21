# agents/interaction/interaction_models.py
from __future__ import annotations

from typing import Any, Dict, List, Optional, Literal
from datetime import datetime
from pydantic import BaseModel, Field
import uuid
from engines.agents.base_agents.base_agent import BaseAgent
from engines.agents.models import AgentOutput

class InteractionRequest(BaseModel):
    """ورودی اصلی به InteractionAgent"""
    workflow_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    scenario: str = "pipeline"
    agents: List[BaseAgent]

    # context مشترک برای همه استراتژی‌ها
    context: Dict[str, Any] = Field(default_factory=dict)

    # متادیتای تکمیلی
    metadata: Dict[str, Any] = Field(default_factory=dict)

class InteractionResult(BaseModel):
    """خروجی کامل orchestration"""
    workflow_id: Optional[str] = None
    scenario: Optional[str] = None
    
    results: List[AgentOutput]
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

class AgentMessage(BaseModel):
    message_id: str
    sender: str
    recipient: str
    message_type: str
    payload: Dict[str, Any] = Field(default_factory=dict)
    correlation_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
