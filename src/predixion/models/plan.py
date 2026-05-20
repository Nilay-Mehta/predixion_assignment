from typing import Literal

from pydantic import BaseModel, Field

ToolName = Literal["web_search", "fetch_url", "github_search", "none"]


class Step(BaseModel):
    id: int = Field(ge=1)
    description: str
    rationale: str
    suggested_tool: ToolName


class Plan(BaseModel):
    question: str
    steps: list[Step] = Field(min_length=1, max_length=6)
    assumptions: list[str] = Field(default_factory=list)
