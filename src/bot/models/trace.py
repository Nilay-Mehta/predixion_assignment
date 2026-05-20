from datetime import datetime
from typing import Any

from pydantic import BaseModel

from bot.models.answer import FinalAnswer
from bot.models.plan import Plan


class ToolCall(BaseModel):
    step_id: int
    tool: str
    args: dict[str, Any]
    started_at: datetime
    duration_ms: int
    ok: bool
    error: str | None = None
    result: Any = None
    tainted: bool = False
    attempts: int = 1


class RunTrace(BaseModel):
    question: str
    plan: "Plan"
    tool_calls: list[ToolCall]
    final_answer: "FinalAnswer"
    total_duration_ms: int
    llm_calls: int
    approx_cost_usd: float | None = None
