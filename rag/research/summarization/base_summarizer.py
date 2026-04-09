# rag/research/summarization/base_summarizer.py
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from rag.research.citation_manager import CitationManager

class BaseSummarizer(ABC):
    """قرارداد مشترک تمام Summarizer ها"""

    @abstractmethod
    async def summarize(
        self,
        query: str,
        plan: List[Dict[str, Any]],
        raw_evidence: List[Any],
        hidden_edges: List[Any],
        citation_manager: Optional[CitationManager] = None,
    ) -> str:
        """تولید خلاصه از متن ورودی"""
