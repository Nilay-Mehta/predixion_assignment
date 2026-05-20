import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path

import typer
from pydantic import BaseModel

from bot.agent import execute_plan, make_plan, synthesize
from bot.config import settings
from bot.llm import get_llm
from bot.models import FinalAnswer, Plan, RunTrace, Step
from bot.tools import default_registry
from bot.utils.logging import configure_logging

app = typer.Typer(help="bot AI research agent.")
tools_app = typer.Typer(help="Inspect and call registered tools.")
app.add_typer(tools_app, name="tools")


@app.callback()
def main() -> None:
    """bot AI research agent."""


@app.command()
def ask(
    question: str,
    save: bool = typer.Option(True, "--save/--no-save", help="Save run trace JSON."),
    verbose: bool = typer.Option(False, "--verbose", help="Enable info-level logs."),
) -> None:
    configure_logging(logging.INFO if verbose else logging.WARNING)
    started = time.perf_counter()
    llm = get_llm()
    registry = default_registry()
    plan_result: Plan | None = None
    tool_calls = []
    final_answer: FinalAnswer
    try:
        plan_result = make_plan(question, registry, llm)
        tool_calls = execute_plan(plan_result, registry, llm)
        final_answer = synthesize(question, plan_result, tool_calls, llm)
        if execute_plan.cap_hit:
            final_answer.confidence = "low"
            final_answer.limitations.append(
                f"LLM call cap hit at MAX_LLM_CALLS_PER_RUN={settings.max_llm_calls_per_run}; answer may be partial."
            )
    except Exception as exc:
        if plan_result is None:
            plan_result = Plan(
                question=question,
                steps=[
                    Step(
                        id=1,
                        description="Pipeline failed before planning completed.",
                        rationale="Return a structured failure answer instead of crashing.",
                        suggested_tool="none",
                    )
                ],
            )
            final_answer = _failure_answer(question, exc)
        else:
            final_answer = _failure_answer(question, exc)
    trace = RunTrace(
        question=question,
        plan=plan_result,
        tool_calls=tool_calls,
        final_answer=final_answer,
        total_duration_ms=int((time.perf_counter() - started) * 1000),
        llm_calls=1 + execute_plan.llm_calls + synthesize.llm_calls,
    )
    if save:
        path = _save_trace(trace)
        typer.echo(f"saved trace: {path}", err=True)
    _echo_model_json(final_answer)


@app.command()
def plan(question: str) -> None:
    registry = default_registry()
    llm = get_llm()
    result = make_plan(question, registry, llm)
    _echo_model_json(result)


@tools_app.command("list")
def list_tools() -> None:
    registry = default_registry()
    typer.echo(json.dumps(registry.catalog(), indent=2))


@tools_app.command("call")
def call_tool(
    tool_name: str,
    query: str | None = typer.Option(None, "--query", help="Search query."),
    url: str | None = typer.Option(None, "--url", help="URL to fetch."),
    max_results: int = typer.Option(5, "--max-results", min=1, max=10),
    sort: str = typer.Option("stars", "--sort", help="GitHub sort: stars, updated, best_match."),
) -> None:
    registry = default_registry()
    tool = registry.get(tool_name)
    payload = _tool_payload(tool_name, query=query, url=url, max_results=max_results, sort=sort)
    args = tool.args_schema.model_validate(payload)
    try:
        result = tool.run(args)
    except Exception as exc:
        typer.echo(f"{type(exc).__name__}: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    if isinstance(result, BaseModel):
        _echo_model_json(result)
    else:
        typer.echo(json.dumps(result, indent=2))


def _tool_payload(
    tool_name: str,
    *,
    query: str | None,
    url: str | None,
    max_results: int,
    sort: str,
) -> dict:
    if tool_name == "web_search":
        if not query:
            raise typer.BadParameter("--query is required for web_search")
        return {"query": query, "max_results": max_results}
    if tool_name == "fetch_url":
        if not url:
            raise typer.BadParameter("--url is required for fetch_url")
        return {"url": url}
    if tool_name == "github_search":
        if not query:
            raise typer.BadParameter("--query is required for github_search")
        return {"query": query, "max_results": max_results, "sort": sort}
    raise typer.BadParameter(f"unknown tool: {tool_name}")


def _echo_model_json(model: BaseModel) -> None:
    typer.echo(json.dumps(model.model_dump(mode="json"), indent=2))


def _save_trace(trace: RunTrace) -> Path:
    runs_dir = Path("runs")
    runs_dir.mkdir(exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = runs_dir / f"{stamp}.json"
    path.write_text(json.dumps(trace.model_dump(mode="json"), indent=2), encoding="utf-8")
    return path


def _failure_answer(question: str, exc: Exception) -> FinalAnswer:
    error_class = type(exc).__name__
    error_message = _truncate(str(exc), 200)
    error_summary = f"{error_class}: {error_message}"
    return FinalAnswer(
        question=question,
        short_answer=f"Could not produce a grounded answer for: {question}",
        key_findings=[f"The agent could not complete due to: {error_summary}"],
        sources=[],
        confidence="low",
        confidence_rationale=f"Pipeline failed before synthesis: {error_summary}",
        limitations=[f"Pipeline error: {error_class}: {error_message}"],
        assumptions=[],
        next_steps=[
            "Retry after the provider's rate limit / quota window has reset.",
            "Try a different LLM provider via the LLM_PROVIDER env var.",
        ],
    )


def _truncate(text: str, limit: int) -> str:
    return text if len(text) <= limit else f"{text[:limit]}..."


if __name__ == "__main__":
    app()
