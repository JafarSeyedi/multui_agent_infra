from abc import ABC, abstractmethod
from typing import AsyncIterator


class BaseLLM(ABC):

    @abstractmethod
    async def ainvoke(self, prompt: str) -> str:
        ...

    @abstractmethod
    def astream(self, prompt: str) -> AsyncIterator[str]:
        ...
