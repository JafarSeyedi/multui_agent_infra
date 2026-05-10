from abc import ABC
from abc import abstractmethod
from collections.abc import AsyncIterator


class BaseLLM(ABC):

    @abstractmethod
    async def ainvoke(self, prompt: str) -> str:
        ...

    @abstractmethod
    def astream(self, prompt: str) -> AsyncIterator[str]:
        ...
