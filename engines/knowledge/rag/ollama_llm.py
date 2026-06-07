from collections.abc import AsyncIterator

import httpx

from .base_llm import BaseLLM


class OllamaLLM(BaseLLM):

    def __init__(self, model: str = "llama3"):
        self.model = model
        self.url = "http://localhost:11434/api/generate"

    async def ainvoke(self, prompt: str) -> str:

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.url,
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                },
            )

            data = response.json()
            return data.get("response", "")

    async def _stream_impl(self, prompt: str) -> AsyncIterator[str]:

        async with httpx.AsyncClient(timeout=None) as client:

            async with client.stream(
                "POST",
                self.url,
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": True,
                },
            ) as response:

                async for line in response.aiter_lines():
                    if line:
                        yield line

    def astream(self, prompt: str) -> AsyncIterator[str]:
        return self._stream_impl(prompt)
