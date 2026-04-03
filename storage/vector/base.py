from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class VectorDBAdapter(ABC):

    @abstractmethod
    async def create_index(
        self,
        name: str,
        dimension: int,
        config: Optional[Dict] = None
    ):
        pass

    @abstractmethod
    async def upsert(
        self,
        ids: List[str],
        vectors: List[List[float]],
        metadata: List[Dict]
    ):
        pass

    @abstractmethod
    async def batch_upsert(
        self,
        items: List[Dict]
    ):
        pass

    @abstractmethod
    async def query(
        self,
        vector: List[float],
        top_k: int = 5,
        filters: Optional[Dict] = None
    ) -> List[Dict]:
        pass

    @abstractmethod
    async def delete(self, ids: List[str]):
        pass
