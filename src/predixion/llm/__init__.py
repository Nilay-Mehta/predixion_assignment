from predixion.config import settings
from predixion.llm.base import LLMProvider
from predixion.llm.gemini import GeminiProvider


def get_llm() -> LLMProvider:
    if settings.llm_provider == "gemini":
        return GeminiProvider()
    msg = f"Unsupported LLM provider: {settings.llm_provider}"
    raise ValueError(msg)


__all__ = ["GeminiProvider", "LLMProvider", "get_llm"]
