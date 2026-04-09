from typing import Protocol, AsyncIterator, runtime_checkable


@runtime_checkable
class AsyncLLM(Protocol):

    async def ainvoke(self, prompt: str) -> str: ...

    def astream(self, prompt: str) -> AsyncIterator[str]: ...
