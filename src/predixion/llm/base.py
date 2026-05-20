from typing import Protocol, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class LLMProvider(Protocol):
    name: str

    def complete(
        self,
        system: str,
        user: str,
        *,
        temperature: float = 0.2,
        max_tokens: int | None = None,
    ) -> str: ...

    def structured(
        self,
        system: str,
        user: str,
        schema: type[T],
        *,
        temperature: float = 0.0,
    ) -> T: ...
