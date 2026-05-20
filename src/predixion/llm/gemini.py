from google import genai
from google.genai import types
from pydantic import ValidationError

from predixion.config import settings
from predixion.llm.base import T


class GeminiProvider:
    name = "gemini"

    def __init__(self) -> None:
        if not settings.google_api_key:
            msg = "GOOGLE_API_KEY is required for GeminiProvider"
            raise ValueError(msg)
        self.model_name = settings.gemini_model
        self.client = genai.Client(api_key=settings.google_api_key)

    def complete(
        self,
        system: str,
        user: str,
        *,
        temperature: float = 0.2,
        max_tokens: int | None = None,
    ) -> str:
        config = types.GenerateContentConfig(
            system_instruction=system,
            temperature=temperature,
            max_output_tokens=max_tokens,
        )
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=user,
            config=config,
        )
        return response.text

    def structured(
        self,
        system: str,
        user: str,
        schema: type[T],
        *,
        temperature: float = 0.0,
    ) -> T:
        return self._structured_with_repair(
            system=system,
            user=user,
            schema=schema,
            temperature=temperature,
            repaired=False,
        )

    def _structured_with_repair(
        self,
        *,
        system: str,
        user: str,
        schema: type[T],
        temperature: float,
        repaired: bool,
    ) -> T:
        config = types.GenerateContentConfig(
            system_instruction=system,
            temperature=temperature,
            response_mime_type="application/json",
            response_schema=schema,
        )
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=user,
            config=config,
        )
        try:
            return schema.model_validate_json(response.text)
        except ValidationError as exc:
            if repaired:
                raise
            repair_user = (
                f"{user}\n\nThe previous response failed Pydantic validation. "
                f"Return only valid JSON matching the requested schema. Validation error:\n{exc}"
            )
            return self._structured_with_repair(
                system=system,
                user=repair_user,
                schema=schema,
                temperature=temperature,
                repaired=True,
            )


__all__ = ["GeminiProvider"]
