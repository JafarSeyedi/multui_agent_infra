from .openai_llm import OpenAILLM
from .ollama_llm import OllamaLLM
from .llm_protocols import AsyncLLM

def create_llm(provider: str, **kwargs) -> AsyncLLM:

    if provider == "openai":
        return OpenAILLM(**kwargs)

    if provider == "ollama":
        return OllamaLLM(**kwargs)

    raise ValueError(f"Unknown LLM provider: {provider}")
