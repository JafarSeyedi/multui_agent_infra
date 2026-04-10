from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional
from storage.base_storage import StorageAdapter
from storage.vector.base import VectorDBAdapter

from agents.base_agents.base_agent import BaseAgent
from .models.content_agents_1_8 import RewriteChange, TextRewriteInput, TextRewriteOutput


class TextRewriterAgent(BaseAgent):
    agent_name = "TextRewriterAgent"
    agent_version = "1.0.0"
    InputModel = TextRewriteInput
    OutputModel = TextRewriteOutput
    def __init__(
        self,
        agent_id: str,
        agent_name: str,
        llm,
        vector_db: Optional[VectorDBAdapter] = None,
        storage: Optional[StorageAdapter] = None,
        metadata: Optional[dict[str, Any]] = None,
    ):
        super().__init__(agent_id, agent_name, vector_db, storage, metadata)
        self.llm = llm

    async def execute(self, input_model: TextRewriteInput) -> TextRewriteOutput:
        rewritten = await self._rewrite_text(input_model)
        return TextRewriteOutput(
            rewritten_text = rewritten,
            changes = [
                RewriteChange(
                    original_segment=input_model.raw_text,
                    rewritten_segment=rewritten,
                    reason=f"Adapted for grade level {input_model.grade_level}",
                )
            ],
            agent_name = self.agent_name,
            readability_score = self._estimate_readability(rewritten),
            created_at = datetime.utcnow(),
        )

    async def _rewrite_text(self, input_model: TextRewriteInput) -> str:
        if self.llm is None:
            return self._fallback_rewrite(input_model)

        prompt = (
            "Rewrite the text for the requested learner profile.\n"
            f"Grade level: {input_model.grade_level}\n"
            f"Subject: {input_model.subject or 'general'}\n"
            f"Language: {input_model.language}\n"
            f"Text: {input_model.raw_text}"
        )
        if hasattr(self.llm, "generate"):
            return str(await self.llm.generate(prompt))
        if hasattr(self.llm, "complete"):
            return str(await self.llm.complete(prompt))
        if hasattr(self.llm, "ainvoke"):
            return str(await self.llm.ainvoke(prompt))
        return self._fallback_rewrite(input_model)

    def _fallback_rewrite(self, input_model: TextRewriteInput) -> str:
        text = input_model.raw_text.strip()
        if input_model.grade_level.lower() in {"elementary", "beginner", "grade_1", "grade_2", "grade_3"}:
            sentences = [sentence.strip() for sentence in text.replace("!", ".").replace("?", ".").split(".") if sentence.strip()]
            return ". ".join(sentences[:3]) + ("." if sentences else "")
        return text

    def _estimate_readability(self, text: str) -> float:
        words = [word for word in text.split() if word]
        if not words:
            return 0.0
        avg_word_len = sum(len(word) for word in words) / len(words)
        return round(max(0.0, min(1.0, 1.2 - (avg_word_len / 10))), 3)
