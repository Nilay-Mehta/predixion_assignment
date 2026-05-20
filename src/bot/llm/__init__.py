from bot.config import settings
from bot.llm.base import LLMProvider
from bot.llm.gemini import GeminiProvider
from bot.llm.groq import GroqProvider

PROVIDERS = {
    "gemini": GeminiProvider,
    "groq": GroqProvider,
}


def get_llm() -> LLMProvider:
    try:
        provider = PROVIDERS[settings.llm_provider]
    except KeyError as exc:
        msg = f"Unsupported LLM provider: {settings.llm_provider}"
        raise ValueError(msg) from exc
    return provider()


__all__ = ["GeminiProvider", "GroqProvider", "LLMProvider", "PROVIDERS", "get_llm"]
