# rag/research/base_research_agent.py
from abc import ABC
from abc import abstractmethod

class BaseResearchAgent(ABC):
    """Common contract for all Research Agents"""

    @abstractmethod
    async def run(self, query: str):
        """Execute research process"""
        ...
