from collections.abc import AsyncIterator

from openai import AsyncOpenAI

from .base_llm import BaseLLM


class OpenAILLM(BaseLLM):

    def __init__(self, model: str = "gpt-4o-mini"):
        self.client = AsyncOpenAI()
        self.model = model

    async def ainvoke(self, prompt: str) -> str:
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
        )

        content = response.choices[0].message.content
        return content or ""

    async def _stream_impl(self, prompt: str) -> AsyncIterator[str]:

        stream = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            stream=True,
        )

        async for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta

    def astream(self, prompt: str) -> AsyncIterator[str]:
        return self._stream_impl(prompt)
