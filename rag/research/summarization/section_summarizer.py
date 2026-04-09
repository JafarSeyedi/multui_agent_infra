from __future__ import annotations

from typing import Any, Dict, List, Optional

from rag.research.citation_manager import CitationManager
from rag.research.memory.reasoning.event_types import ReasoningEventType
from rag.research.memory.reasoning_memory import ReasoningMemory
from rag.research.summarization.base_summarizer import BaseSummarizer

class SectionSummarizer(BaseSummarizer):
    """Builds a structured report from a plan and evidence bundle."""

    def __init__(self, llm: Optional[Any] = None, reasoning: Optional[ReasoningMemory] = None):
        self.llm = llm
        self.reasoning = reasoning or ReasoningMemory()

    async def summarize(
        self,
        query: str,
        plan: List[Dict[str, Any]],
        raw_evidence: List[Any],
        hidden_edges: List[Any],
        citation_manager: Optional[CitationManager] = None,
    ) -> str:
        compiled_sections: List[str] = []
        for section in plan:
            title = str(section.get("title", "Section"))
            description = str(section.get("description", "")).strip()
            supporting_items = self._select_supporting_evidence(section, raw_evidence)

            body_parts: List[str] = []
            if description:
                body_parts.append(description)
            for item in supporting_items:
                chunk = getattr(item, "chunk", item)
                text = str(getattr(chunk, "text", "")).strip()
                if not text:
                    continue
                citation = citation_manager.register_source(chunk) if citation_manager else ""
                body_parts.append(f"- {text} {citation}".strip())

            if title.lower().startswith("implication") and hidden_edges:
                body_parts.append(f"- Related graph links: {', '.join(map(str, hidden_edges[:5]))}")

            compiled_sections.append(f"## {title}\n" + "\n".join(body_parts).strip())
            self.reasoning.log(
                ReasoningEventType.SUMMARIZATION,
                "Section summarized",
                meta={"section": title, "evidence_items": len(supporting_items)},
            )

        report = "\n\n".join(compiled_sections)
        if citation_manager:
            references = citation_manager.build_reference_list()
            if references:
                report += "\n\n---\n### References\n" + "\n".join(references)
        return report

    def _select_supporting_evidence(self, section: Dict[str, Any], raw_evidence: List[Any]) -> List[Any]:
        evidence_ids = section.get("evidence_ids") or []
        selected = [raw_evidence[idx] for idx in evidence_ids if isinstance(idx, int) and 0 <= idx < len(raw_evidence)]
        return selected or raw_evidence[:3]
