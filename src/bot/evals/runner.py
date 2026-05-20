import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from bot.agent import execute_plan, make_plan, synthesize
from bot.llm import get_llm
from bot.models import FinalAnswer, Plan, RunTrace, Step
from bot.tools import default_registry
from bot.utils.guardrails import apply_low_confidence_guardrail

ROOT = Path.cwd()
QUERIES_PATH = ROOT / "evals" / "queries.yaml"
RESULTS_DIR = ROOT / "evals" / "results"


def main() -> None:
    queries = _load_queries()
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    index: list[dict[str, Any]] = []

    for query in queries:
        query_id = query["id"]
        print(f"[evals] running: {query_id}")
        trace, ok = _run_one(query["query"])
        path = RESULTS_DIR / f"{query_id}.json"
        path.write_text(json.dumps(trace.model_dump(mode="json"), indent=2), encoding="utf-8")
        print(f"[evals] saved: evals/results/{query_id}.json")
        index.append(
            {
                "id": query_id,
                "total_duration_ms": trace.total_duration_ms,
                "confidence": trace.final_answer.confidence,
                "n_sources": len(trace.final_answer.sources),
                "llm_calls": trace.llm_calls,
                "ok": ok,
            }
        )
        time.sleep(2)

    (RESULTS_DIR / "index.json").write_text(json.dumps(index, indent=2), encoding="utf-8")


def _load_queries() -> list[dict[str, Any]]:
    with QUERIES_PATH.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def _run_one(question: str) -> tuple[RunTrace, bool]:
    started = time.perf_counter()
    plan: Plan | None = None
    tool_calls = []
    ok = True
    try:
        llm = get_llm()
        registry = default_registry()
        plan = make_plan(question, registry, llm)
        tool_calls = execute_plan(plan, registry, llm)
        final_answer = synthesize(question, plan, tool_calls, llm)
        if execute_plan.cap_hit:
            final_answer.confidence = "low"
            final_answer.limitations.append("LLM call cap hit; eval answer may be partial.")
    except Exception as exc:
        ok = False
        if plan is None:
            plan = Plan(
                question=question,
                steps=[
                    Step(
                        id=1,
                        description="Eval pipeline failed before planning completed.",
                        rationale="Record a structured failure trace.",
                        suggested_tool="none",
                    )
                ],
            )
        final_answer = _failure_answer(question, exc)
    final_answer = apply_low_confidence_guardrail(final_answer)

    return (
        RunTrace(
            question=question,
            plan=plan,
            tool_calls=tool_calls,
            final_answer=final_answer,
            total_duration_ms=int((time.perf_counter() - started) * 1000),
            llm_calls=1 + execute_plan.llm_calls + synthesize.llm_calls,
        ),
        ok,
    )


def _failure_answer(question: str, exc: Exception) -> FinalAnswer:
    error_class = type(exc).__name__
    error_message = str(exc)
    if len(error_message) > 200:
        error_message = f"{error_message[:200]}..."
    summary = f"{error_class}: {error_message}"
    return FinalAnswer(
        question=question,
        short_answer=f"Could not produce a grounded answer for: {question}",
        key_findings=[f"The agent could not complete due to: {summary}"],
        sources=[],
        confidence="low",
        confidence_rationale=f"Pipeline failed before synthesis: {summary}",
        limitations=[f"Pipeline error: {summary}"],
        assumptions=[],
        next_steps=[
            "Retry after the provider's rate limit / quota window has reset.",
            "Try a different LLM provider via the LLM_PROVIDER env var.",
        ],
    )


if __name__ == "__main__":
    main()
