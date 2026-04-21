# agents/agent_base_models.py
from pydantic import BaseModel, Field
from typing import Any, Dict, Optional, List
from datetime import datetime


# message = داده طبیعی (مثل user message یا query)
# message برای انسان‌خوان
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

    # پیام اصلی یا هدف
    message: Optional[str] = None

    # ورودی‌های ساخت‌یافته
    payload: Dict[str, Any] = Field(default_factory=dict)

    # کانتکست مشترک (shared context)
    context: Dict[str, Any] = Field(default_factory=dict)

    # اطلاعات اضافه → tracing, routing, strategy, priority
    metadata: Dict[str, Any] = Field(default_factory=dict)

# agent می‌تواند هم متن هم داده برگرداند
# برنامه تو هیچ‌وقت نمی‌ترکد چون همیشه یک structure ثابت دارد
# subclasses می‌توانند payload را غنی کنند
class AgentOutput(BaseModel):
    agent_id: Optional[str] = None
    agent_name: str

    # خروجی اصلی agent (LLM پاسخ یا نتیجه پردازش)
    message: Optional[str] = None

    # خروجی ساخت‌یافته
    payload: Dict[str, Any] = Field(default_factory=dict)

    # خطا (اگر وجود دارد)
    error: Optional[str] = None

    # برای orchestration و tracing
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AgentExecutionRecord(BaseModel):
    execution_id: str
    agent_name: str
    agent_version: str
    input_payload: Dict[str, Any]
    output_payload: Optional[Dict[str, Any]] = None
    status: str
    execution_time_ms: int
    error_message: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
