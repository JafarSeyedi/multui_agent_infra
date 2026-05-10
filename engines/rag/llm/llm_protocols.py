from collections.abc import AsyncIterator
from typing import Protocol
from typing import runtime_checkable


@runtime_checkable
class AsyncLLM(Protocol):

    async def ainvoke(self, prompt: str) -> str: ...

    def astream(self, prompt: str) -> AsyncIterator[str]: ...
