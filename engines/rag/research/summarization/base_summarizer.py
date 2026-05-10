# rag/research/summarization/base_summarizer.py
from abc import ABC
from abc import abstractmethod
from typing import Any

from engines.rag.research.citation_manager import CitationManager

class BaseSummarizer(ABC):
    """قرارداد مشترک تمام Summarizer ها"""

    @abstractmethod
    async def summarize(
        self,
        query: str,
        plan: list[dict[str, Any]] | None = None,
        raw_evidence: list[Any] | None = None,
        hidden_edges: list[Any] | None = None,
        citation_manager: CitationManager | None = None,
    ) -> str:
        """تولید خلاصه از متن ورودی"""
        ...
