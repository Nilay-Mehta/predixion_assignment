from bot.models import FinalAnswer

LOW_CONFIDENCE_PREFIX = "LOW CONFIDENCE - verify before relying on this answer.\n\n"
LOW_CONFIDENCE_LIMITATION = (
    "This answer is flagged low-confidence; treat as a research starting point, not a verified fact."
)


def apply_low_confidence_guardrail(answer: FinalAnswer) -> FinalAnswer:
    if answer.confidence != "low":
        return answer

    if not answer.short_answer.startswith(LOW_CONFIDENCE_PREFIX):
        answer.short_answer = f"{LOW_CONFIDENCE_PREFIX}{answer.short_answer}"

    if LOW_CONFIDENCE_LIMITATION not in answer.limitations:
        answer.limitations.append(LOW_CONFIDENCE_LIMITATION)

    return answer


__all__ = [
    "LOW_CONFIDENCE_LIMITATION",
    "LOW_CONFIDENCE_PREFIX",
    "apply_low_confidence_guardrail",
]
