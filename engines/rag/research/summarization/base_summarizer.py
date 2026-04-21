# rag/research/summarization/base_summarizer.py
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from engines.rag.research.citation_manager import CitationManager

class BaseSummarizer(ABC):
    """قرارداد مشترک تمام Summarizer ها"""

    @abstractmethod
    async def summarize(
        self,
        query: str,
        plan: Optional[List[Dict[str, Any]]] = None,
        raw_evidence: Optional[List[Any]] = None,
        hidden_edges: Optional[List[Any]] = None,
        citation_manager: Optional[CitationManager] = None,
    ) -> str:
        """تولید خلاصه از متن ورودی"""
        ...
