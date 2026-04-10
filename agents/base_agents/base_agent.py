# agents/base_agent.py
from __future__ import annotations

import asyncio
import inspect
import time
import uuid
from datetime import datetime
from typing import Any, Optional, Type, TypeVar, Generic

from pydantic import BaseModel

from storage.base_storage import StorageAdapter
from storage.vector.base import VectorDBAdapter
from .models import AgentInput, AgentOutput, AgentExecutionRecord

TInput = TypeVar("TInput", bound=AgentInput)
TOutput = TypeVar("TOutput", bound=AgentOutput)


class BaseAgent(Generic[TInput, TOutput]):
    """Production-ready base class for typed educational agents."""

    # agent_id: str = ""
    # agent_name: str = "BaseAgent"
    agent_version: str = "1.0.0"

    input_model_class: Type[TInput]
    output_model_class: Type[TOutput]
    
    def __init__(
        self,
        agent_id: str,
        agent_name: str,
        vector_db: Optional[VectorDBAdapter] = None,
        storage: Optional[StorageAdapter] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> None:
        self.agent_id = agent_id
        self.agent_name = agent_name
        self.vector_db = vector_db
        self.storage = storage
        self.metadata = metadata or {}

    async def run(self, input_data: Any) -> TOutput:
        start = time.perf_counter()
        validated_input = self._validate_input(input_data)
        try:
            result = await self._invoke_execute(validated_input)
            validated_output = self._validate_output(result)
            await self._log_execution(validated_input, validated_output, start, status="success")
            return validated_output
        except Exception as exc:
            await self._log_execution(validated_input, None, start, status="failure", error_message=str(exc))
            raise

    def run_sync(self, input_data: Any) -> TOutput:
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(self.run(input_data))

        raise RuntimeError(
            "BaseAgent.run_sync() cannot be used inside an active asyncio event loop. "
            "Use `await agent.run(...)` instead, or call this method from a purely "
            "synchronous context (e.g., a separate thread or process)."
        )

    async def execute(self, input_model: TInput) -> TOutput:
        raise NotImplementedError(f"{self.agent_name} must implement execute().")

    def _validate_input(self, input_data: Any) -> TInput:
        if isinstance(input_data, self.input_model_class):
            return input_data
        if isinstance(input_data, BaseModel):
            input_data = self._model_dump(input_data)
        return self.input_model_class(**input_data)

    def _validate_output(self, result: Any) -> TOutput:
        if isinstance(result, self.output_model_class):
            return result
        if isinstance(result, BaseModel):
            result = self._model_dump(result)
        return self.output_model_class(**result)

    async def _invoke_execute(self, input_model: TInput) -> Any:
        result = self.execute(input_model)
        if inspect.isawaitable(result):
            return await result
        return result

    async def _log_execution(
        self,
        input_model: TInput,
        output_model: Optional[TOutput],
        start_time: float,
        status: str,
        error_message: Optional[str] = None,
    ) -> None:
        record = AgentExecutionRecord(
            execution_id=str(uuid.uuid4()),
            agent_name=self.agent_name,
            agent_version=self.agent_version,
            input_payload=self._model_dump(input_model),
            output_payload=self._model_dump(output_model) if output_model is not None else None,
            execution_time_ms=int((time.perf_counter() - start_time) * 1000),
            timestamp=datetime.utcnow(),
            status=status,
            error_message=error_message,
        )
        if self.storage is not None:
            await self.storage.save(
                f"exec_log:{self.agent_name}:{record.execution_id}",
                self._model_dump(record),
            )

    def _model_dump(self, model: BaseModel) -> dict[str, Any]:
        if hasattr(model, "model_dump"):
            return model.model_dump()
        return model.dict()