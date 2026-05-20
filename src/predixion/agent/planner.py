from predixion.config import settings
from predixion.llm.base import LLMProvider
from predixion.models import Plan
from predixion.tools import ToolRegistry
from predixion.utils.logging import get_logger

logger = get_logger(__name__)


def make_plan(question: str, registry: ToolRegistry, llm: LLMProvider) -> Plan:
    tool_names = registry.names()
    max_steps = min(settings.max_plan_steps, 6)
    system = (
        "You are the planner for a bounded research agent. "
        "Output a Plan in the exact JSON schema. "
        f"Use 3-{max_steps} steps maximum, unless the question is trivial and can be "
        "answered with one step. "
        "Each step's suggested_tool MUST be one of the registry's tool names, OR "
        '"none" if the step needs no tool. '
        "Plan should be linear and minimal; do not include redundant searches. "
        "Include assumptions for anything the question leaves ambiguous."
    )
    user = (
        f"Question:\n{question}\n\n"
        "Available tools:\n"
        f"{_format_tool_catalog(registry.catalog())}\n\n"
        "Plan schema:\n"
        "{\n"
        '  "question": "string",\n'
        '  "steps": [\n'
        "    {\n"
        '      "id": 1,\n'
        '      "description": "what this step is trying to accomplish",\n'
        '      "rationale": "why it is needed",\n'
        f'      "suggested_tool": "one of: {", ".join(tool_names + ["none"])}"\n'
        "    }\n"
        "  ],\n"
        '  "assumptions": ["string"]\n'
        "}\n"
    )

    plan = llm.structured(system, user, schema=Plan, temperature=0.0)
    allowed_tools = set(tool_names + ["none"])
    for step in plan.steps:
        if step.suggested_tool not in allowed_tools:
            logger.warning(
                "planner_invalid_tool",
                step_id=step.id,
                suggested_tool=step.suggested_tool,
                allowed_tools=sorted(allowed_tools),
            )
            step.suggested_tool = "none"
    return plan


def _format_tool_catalog(catalog: list[dict]) -> str:
    return "\n".join(
        f"- {tool['name']}: {tool['description']}"
        for tool in catalog
    )


__all__ = ["make_plan"]
