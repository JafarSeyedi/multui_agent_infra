# agents/interaction/interaction_models.py
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any
from typing import Literal

from pydantic import BaseModel
from pydantic import Field

from ..agents.base_agents.base_agent import BaseAgent
from ..agents.models import AgentOutput

class InteractionRequest(BaseModel):
    """ورودی اصلی به InteractionAgent"""
    workflow_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    scenario: str = "pipeline"
    agents: list[BaseAgent]

    # context مشترک برای همه استراتژی‌ها
    context: dict[str, Any] = Field(default_factory=dict)

    # متادیتای تکمیلی
    metadata: dict[str, Any] = Field(default_factory=dict)

class InteractionResult(BaseModel):
    """خروجی کامل orchestration"""
    workflow_id: str | None = None
    scenario: str | None = None

    results: list[AgentOutput]
    success: bool = True

    # context نهایی که توسط استراتژی ها آپدیت شده
    final_context: dict[str, Any] = Field(default_factory=dict)

    # tracking اجرا
    backend_used: str = "native"
    status: Literal["success", "partial", "failed"] = "success"
    started_at: datetime | None = None
    completed_at: datetime | None = None

    # یادداشت‌ها و لاگ‌ها
    notes: list[str] = Field(default_factory=list)

    metadata: dict[str, Any] = Field(default_factory=dict)

class AgentMessage(BaseModel):
    message_id: str
    sender: str
    recipient: str
    message_type: str
    payload: dict[str, Any] = Field(default_factory=dict)
    correlation_id: str | None = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
