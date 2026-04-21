# rag/research/base_research_agent.py
from abc import ABC, abstractmethod

class BaseResearchAgent(ABC):
    """قرارداد مشترک تمام Research Agent ها"""

    @abstractmethod
    async def run(self, query: str):
        """اجرای فرآیند تحقیق"""
        ...
