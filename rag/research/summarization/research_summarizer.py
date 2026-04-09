# rag/research/summarization/research_summarizer.py
from __future__ import annotations

from typing import Any, Iterable, List, Optional, Dict
from rag.research.summarization.base_summarizer import BaseSummarizer

from rag.research.citation_manager import CitationManager

class ResearchSummarizer(BaseSummarizer):
    def __init__(self, llm: Optional[Any], guard=None):
        self.llm = llm
        self.guard = guard

    async def summarize(
        self,
        query: str,
        plan: Optional[List[Dict[str, Any]]] = None,
        raw_evidence: Optional[List[Any]] = None,
        hidden_edges: Optional[List[Any]] = None,
        citation_manager: Optional[CitationManager] = None,
        evidence_chunks: Optional[List[Any]] = None,
    ) -> str:
        chunks = evidence_chunks or [
            getattr(item, "chunk", item) for item in (raw_evidence or [])
        ]
        evidence_chunks = evidence_chunks or []
        if self.llm is None:
            return await self._fallback_summary(query, evidence_chunks)

        prompt = self.build_prompt(
            query=query,
            plan=plan,
            chunks=chunks,
            hidden_edges=hidden_edges or [],
        )

        if hasattr(self.llm, 'generate'):
            answer = await self.llm.generate(prompt)
        elif hasattr(self.llm, 'complete'):
            answer = await self.llm.complete(prompt)
        elif hasattr(self.llm, 'ainvoke'):
            answer = await self.llm.ainvoke(prompt)
        else:
            raise TypeError('Unsupported LLM interface')

        result = self.enforce_citations(answer, citation_manager)

        if self.guard and not self.guard.is_safe(result):
            return await self._fallback_summary(query, chunks)

        return result

    def build_prompt(
        self,
        query: str,
        plan: Any,
        chunks: List[Any],
        hidden_edges: List[Any],
    ) -> str:
        sections = getattr(plan, "sections", plan) if plan else []
        evidence_text = "\n".join(
            str(getattr(c, "text", c)) for c in chunks
        )
        edges_text = "\n".join(str(e) for e in hidden_edges)

        return (
            f"Query: {query}\n\n"
            f"Plan sections: {sections}\n\n"
            f"Evidence:\n{evidence_text}\n\n"
            f"Graph connections:\n{edges_text}"
        )

    def enforce_citations(
        self,
        text: str,
        citation_manager: Optional[CitationManager],
    ) -> str:
        if citation_manager is None:
            return text
        return citation_manager.inject_citations(text) if hasattr(citation_manager, "inject_citations") else text

    async def _fallback_summary(self, query: str, chunks: List[Any]) -> str:
        texts = [str(getattr(c, "text", c)) for c in chunks[:3]]
        joined = "\n".join(texts)
        prompt = f"Summarize briefly for: {query}\n\n{joined}"

        if self.llm is None:
            return joined

        return await self.llm.complete(prompt)
