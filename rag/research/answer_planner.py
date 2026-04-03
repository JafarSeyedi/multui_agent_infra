from __future__ import annotations

import json
from types import SimpleNamespace
from typing import Any, Dict, List, Optional

from rag.research.memory.reasoning.event_types import ReasoningEventType
from rag.research.memory.reasoning_memory import ReasoningMemory


class AnswerPlanner:
    def __init__(self, llm: Optional[Any] = None, reasoning: Optional[ReasoningMemory] = None):
        self.llm = llm
        self.reasoning = reasoning or ReasoningMemory()
        self.memory = None

    async def create_plan(
        self,
        query: str,
        raw_evidence: Optional[List[Any]] = None,
        graph_edges: Optional[List[Any]] = None,
    ):
        plan = await self._llm_plan(query, raw_evidence or [], graph_edges or [])
        if not plan:
            plan = self._fallback_plan(query, raw_evidence or [])

        self.reasoning.log(
            ReasoningEventType.PLANNING,
            "Answer plan created",
            meta={"sections": len(plan)},
        )
        return SimpleNamespace(sections=plan)

    async def _llm_plan(self, query: str, raw_evidence: List[Any], graph_edges: List[Any]) -> List[Dict[str, Any]]:
        if self.llm is None:
            return []

        evidence_preview = [self._evidence_to_text(item)[:220] for item in raw_evidence[:5]]
        prompt = (
            "Break the research question into structured report sections. "
            "Return JSON list with title, description, and evidence_ids fields.\n"
            f"Question: {query}\n"
            f"Evidence preview: {evidence_preview}\n"
            f"Graph edges: {[str(edge) for edge in graph_edges[:8]]}"
        )
        response = await self._complete(prompt)
        try:
            data = json.loads(response)
        except Exception:
            return []

        plan: List[Dict[str, Any]] = []
        for item in data if isinstance(data, list) else []:
            if not isinstance(item, dict):
                continue
            plan.append(
                {
                    "title": item.get("title", "Section"),
                    "description": item.get("description", ""),
                    "evidence_ids": item.get("evidence_ids", []),
                }
            )
        return plan

    def _fallback_plan(self, query: str, raw_evidence: List[Any]) -> List[Dict[str, Any]]:
        sections = [
            {"title": "Overview", "description": f"Direct answer to: {query}", "evidence_ids": [0, 1]},
            {"title": "Evidence", "description": "Key supporting findings", "evidence_ids": [0, 1, 2, 3]},
            {"title": "Implications", "description": "Meaning, risks, and next steps", "evidence_ids": [0, 2, 4]},
        ]
        if len(raw_evidence) > 4:
            sections.insert(
                2,
                {"title": "Comparative Analysis", "description": "Compare competing signals in the evidence", "evidence_ids": [1, 2, 3, 4]},
            )
        return sections

    async def _complete(self, prompt: str) -> str:
        if hasattr(self.llm, "complete"):
            return str(await self.llm.complete(prompt))
        if hasattr(self.llm, "generate"):
            return str(await self.llm.generate(prompt))
        if hasattr(self.llm, "ainvoke"):
            return str(await self.llm.ainvoke(prompt))
        raise TypeError("Unsupported LLM interface")

    def _evidence_to_text(self, item: Any) -> str:
        chunk = getattr(item, "chunk", item)
        return str(getattr(chunk, "text", item))
