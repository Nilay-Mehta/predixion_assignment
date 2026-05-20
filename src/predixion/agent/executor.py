import json
import time
from datetime import datetime, timezone

from pydantic import BaseModel

from predixion.config import settings
from predixion.llm.base import LLMProvider
from predixion.models import Plan, ToolCall
from predixion.tools import ToolRegistry
from predixion.utils.injection import is_tainted
from predixion.utils.logging import get_logger

logger = get_logger(__name__)


class SearchRewrite(BaseModel):
    query: str


def execute_plan(plan: Plan, registry: ToolRegistry, llm: LLMProvider) -> list[ToolCall]:
    tool_calls: list[ToolCall] = []
    llm_calls = 0
    total_steps = len(plan.steps)

    for index, step in enumerate(plan.steps, start=1):
        if step.suggested_tool == "none":
            logger.info(
                "executor_step_skipped",
                message=f"[step {index}/{total_steps}] none -> skipped",
                step_id=step.id,
            )
            continue
        if llm_calls >= settings.max_llm_calls_per_run:
            logger.warning(
                "executor_llm_call_cap_hit",
                max_llm_calls=settings.max_llm_calls_per_run,
                completed_tool_calls=len(tool_calls),
            )
            break

        tool = registry.get(step.suggested_tool)
        args = _pick_tool_args(plan, step.id, tool.name, tool.description, tool.args_schema, llm)
        llm_calls += 1

        tool_call = _run_tool_call(step.id, tool.name, args, tool)
        if (
            tool.name == "web_search"
            and tool_call.ok
            and isinstance(tool_call.result, dict)
            and len(tool_call.result.get("results", [])) == 0
            and llm_calls < settings.max_llm_calls_per_run
        ):
            rewritten = _rewrite_search_query(plan.question, args.model_dump(mode="json"), llm)
            llm_calls += 1
            retry_args = tool.args_schema.model_validate(
                {"query": rewritten.query, "max_results": args.model_dump().get("max_results", 5)}
            )
            tool_call = _run_tool_call(step.id, tool.name, retry_args, tool)

        tool_calls.append(tool_call)
        _log_progress(index, total_steps, tool_call)

    execute_plan.llm_calls = llm_calls
    return tool_calls


execute_plan.llm_calls = 0


def _pick_tool_args(
    plan: Plan,
    step_id: int,
    tool_name: str,
    tool_description: str,
    schema: type[BaseModel],
    llm: LLMProvider,
) -> BaseModel:
    step = next(item for item in plan.steps if item.id == step_id)
    system = (
        "You are picking tool arguments. Output only valid JSON matching the schema. "
        "Be precise and minimal."
    )
    user = (
        f"Original question:\n{plan.question}\n\n"
        f"Full plan context:\n{plan.model_dump_json(indent=2)}\n\n"
        f"Current step:\n{step.description}\n\n"
        f"Tool:\n{tool_name}: {tool_description}\n\n"
        f"Tool argument schema:\n{json.dumps(schema.model_json_schema(), indent=2)}"
    )
    return llm.structured(system, user, schema=schema, temperature=0.0)


def _run_tool_call(step_id: int, tool_name: str, args: BaseModel, tool: object) -> ToolCall:
    started_at = datetime.now(timezone.utc)
    start = time.perf_counter()
    args_dict = args.model_dump(mode="json")
    try:
        result = tool.run(args)  # type: ignore[attr-defined]
        result_dict = result.model_dump(mode="json")
        tainted = _result_is_tainted(tool_name, result_dict)
        return ToolCall(
            step_id=step_id,
            tool=tool_name,
            args=args_dict,
            started_at=started_at,
            duration_ms=int((time.perf_counter() - start) * 1000),
            ok=True,
            result=result_dict,
            tainted=tainted,
        )
    except Exception as exc:
        return ToolCall(
            step_id=step_id,
            tool=tool_name,
            args=args_dict,
            started_at=started_at,
            duration_ms=int((time.perf_counter() - start) * 1000),
            ok=False,
            error=str(exc),
            result=None,
        )


def _rewrite_search_query(question: str, previous_args: dict, llm: LLMProvider) -> SearchRewrite:
    system = "Rewrite the failed web search query. Output only valid JSON."
    user = (
        f"Original question:\n{question}\n\n"
        f"Previous search args returned no results:\n{json.dumps(previous_args, indent=2)}\n\n"
        "Return a broader, simpler query."
    )
    return llm.structured(system, user, schema=SearchRewrite, temperature=0.0)


def _result_is_tainted(tool_name: str, result: dict) -> bool:
    if tool_name not in {"fetch_url", "web_search"}:
        return False
    return is_tainted(json.dumps(result, ensure_ascii=False))


def _log_progress(index: int, total_steps: int, tool_call: ToolCall) -> None:
    count = _result_count(tool_call.result)
    query = tool_call.args.get("query") or tool_call.args.get("url") or ""
    logger.info(
        "executor_step_complete",
        message=(
            f"[step {index}/{total_steps}] {tool_call.tool}('{query}') -> "
            f"{count} results, {tool_call.duration_ms / 1000:.1f}s, ok={tool_call.ok}"
        ),
        step_id=tool_call.step_id,
        tool=tool_call.tool,
        ok=tool_call.ok,
        duration_ms=tool_call.duration_ms,
        result_count=count,
    )


def _result_count(result: object) -> int:
    if not isinstance(result, dict):
        return 0
    if "results" in result and isinstance(result["results"], list):
        return len(result["results"])
    if "repos" in result and isinstance(result["repos"], list):
        return len(result["repos"])
    if result.get("text"):
        return 1
    return 0


__all__ = ["execute_plan"]
