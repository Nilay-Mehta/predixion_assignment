from typing import Literal

from pydantic import BaseModel, Field, HttpUrl

Confidence = Literal["high", "medium", "low"]


class Source(BaseModel):
    url: HttpUrl
    title: str
    used_for: list[str] = Field(default_factory=list)


class FinalAnswer(BaseModel):
    question: str
    short_answer: str
    key_findings: list[str] = Field(min_length=1)
    sources: list[Source] = Field(default_factory=list)
    confidence: Confidence
    confidence_rationale: str
    limitations: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    next_steps: list[str] = Field(default_factory=list)
