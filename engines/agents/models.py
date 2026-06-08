# agents/agent_base_models.py
from datetime import datetime
from typing import Any

from pydantic import BaseModel
from pydantic import Field


# message = natural data (like user message or query)
# message for human readable
# payload برای ماشین‌خوان
# payload = داده ساخت‌یافته Agent-specificمثل:
#   - search_query
#   - doc_ids
#   - intermediate_results
#   - extracted_features
# context = shared context بین همه agentها (به orchestration مربوط است)
# metadata = tracing / routing / meta info internal info (مثل trace_id, retry, priority)

class AgentInput(BaseModel):
    agent_name: str

    # Main message or Objective
    message: str | None = None

    # Structured inputs
    payload: dict[str, Any] = Field(default_factory=dict)

    # کانتکست مشترک (shared context)
    context: dict[str, Any] = Field(default_factory=dict)

    # اطلاعات اضافه → tracing, routing, strategy, priority
    metadata: dict[str, Any] = Field(default_factory=dict)

# agent می‌تواند هم متن هم داده برگرداند
# برنامه تو هیچ‌وقت نمی‌ترکد چون همیشه یک structure ثابت دارد
# subclasses می‌توانند payload را غنی کنند
class AgentOutput(BaseModel):
    agent_id: str | None = None
    agent_name: str

    # خروجی اصلی agent (LLM پاسخ یا نتیجه پردازش)
    message: str | None = None

    # خروجی ساخت‌یافته
    payload: dict[str, Any] = Field(default_factory=dict)

    # خطا (اگر وجود دارد)
    error: str | None = None

    # برای orchestration و tracing
    metadata: dict[str, Any] = Field(default_factory=dict)


class AgentExecutionRecord(BaseModel):
    execution_id: str
    agent_name: str
    agent_version: str
    input_payload: dict[str, Any]
    output_payload: dict[str, Any] | None = None
    status: str
    execution_time_ms: int
    error_message: str | None = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
