import json

from groq import Groq
from pydantic import ValidationError

from bot.config import settings
from bot.llm.base import T


class GroqProvider:
    name = "groq"

    def __init__(self) -> None:
        if not settings.groq_api_key:
            msg = "GROQ_API_KEY is required for GroqProvider"
            raise ValueError(msg)
        self.client = Groq(api_key=settings.groq_api_key)
        self.model_name = settings.groq_model

    def complete(
        self,
        system: str,
        user: str,
        *,
        temperature: float = 0.2,
        max_tokens: int | None = None,
    ) -> str:
        response = self.client.chat.completions.create(
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            model=self.model_name,
            temperature=temperature,
            max_tokens=max_tokens or 4096,
        )
        return response.choices[0].message.content or ""

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
        structured_system = (
            f"{system}\n\n"
            "Return a single JSON object matching this JSON schema exactly:\n"
            f"{json.dumps(schema.model_json_schema(), indent=2)}"
        )
        response = self.client.chat.completions.create(
            messages=[
                {"role": "system", "content": structured_system},
                {"role": "user", "content": user},
            ],
            model=self.model_name,
            temperature=temperature,
            max_tokens=4096,
            response_format={"type": "json_object"},
        )
        content = response.choices[0].message.content or ""
        try:
            return schema.model_validate_json(content)
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


__all__ = ["GroqProvider"]
