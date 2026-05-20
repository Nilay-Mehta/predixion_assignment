from bot.llm.gemini import GeminiProvider
from bot.models import Plan


class _Response:
    def __init__(self, text: str) -> None:
        self.text = text


class _FakeModels:
    def __init__(self) -> None:
        self.calls = 0

    def generate_content(self, **kwargs) -> _Response:
        self.calls += 1
        if self.calls == 1:
            return _Response('{"question": "q", "steps": []}')
        return _Response(
            """
            {
              "question": "q",
              "steps": [
                {
                  "id": 1,
                  "description": "d",
                  "rationale": "r",
                  "suggested_tool": "none"
                }
              ],
              "assumptions": []
            }
            """
        )


class _FakeClient:
    def __init__(self) -> None:
        self.models = _FakeModels()


def main() -> None:
    provider = GeminiProvider.__new__(GeminiProvider)
    provider.model_name = "fake"
    provider.client = _FakeClient()
    plan = provider.structured("system", "user", Plan)
    ok = plan.steps[0].suggested_tool == "none" and provider.client.models.calls == 2
    print("PASS" if ok else "FAIL")


if __name__ == "__main__":
    main()
