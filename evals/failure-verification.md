# Failure Verification - Phase 4

Date: 2026-05-20

## Scenario A - Tool Timeout

Command:

```powershell
$env:TOOL_TIMEOUT_SECONDS='0.5'; .\.venv\Scripts\bot ask "Compare open-source vector databases"
```

Expected per `docs/05-failures.md`: tool timeout should be captured as failed `ToolCall` entries where applicable; executor should continue; final answer should not crash.

Actual: command completed successfully and saved `runs/20260520T023818Z.json`. The exact command did not trigger a timeout because the selected tools returned quickly and the plan did not use `fetch_url`. The Phase 2 direct forced-timeout smoke command did produce a clean error:

```text
ConnectTimeout: timed out
```

Status: PASS for no crash and clean timeout behavior when forced directly; PARTIAL for this exact scenario because no timeout occurred during the full agent run.

## Scenario B - No-Info Query

Command:

```powershell
.\.venv\Scripts\bot ask "Find the funding history of QuantumPickleAI, founded in 2023."
```

Expected per `docs/05-failures.md`: no fabricated funding history; low confidence; limitations should explain that no reliable information was found; next steps should suggest verification.

Actual: command completed and saved `runs/20260520T023624Z.json`. The answer set `confidence="low"`, stated that direct funding history for QuantumPickleAI could not be found, distinguished similar companies named "Pickle" / "Pickle Robot Company", and suggested verification next steps.

Status: PASS.

## Scenario C - Injection In Fetched Content

Command:

```powershell
.\.venv\Scripts\python tests\manual_injection.py
```

Expected per `docs/05-failures.md`: prompt-injection-like text is flagged as tainted.

Actual:

```text
PASS
```

Additional check: run traces include the `tainted` field on tool calls. Recent normal runs had `tainted=false`, as expected.

Status: PASS.

## Scenario D - Malformed LLM JSON

Command:

```powershell
.\.venv\Scripts\python tests\manual_repair.py
```

Expected per `docs/05-failures.md`: provider structured-output repair loop retries once after Pydantic validation failure.

Actual:

```text
PASS
```

The script uses a fake Gemini client: first response violates the `Plan` schema, second response is valid. `GeminiProvider.structured()` returns a valid `Plan` after two calls.

Status: PASS.

## LLM Call Cap

Command:

```powershell
$env:MAX_LLM_CALLS_PER_RUN='3'; .\.venv\Scripts\bot ask "Compare top 5 open-source vector databases by every possible axis"
```

Expected per `docs/05-failures.md`: executor stops adding new steps when the call budget is hit; final answer is partial and notes the cap.

Actual: command completed and saved `runs/20260520T023749Z.json`. The executor logged:

```json
{"max_llm_calls":3,"executor_llm_cap":2,"completed_tool_calls":2,"event":"executor_llm_call_cap_hit"}
```

The final answer returned `confidence="low"` and included this limitation:

```text
LLM call cap hit at MAX_LLM_CALLS_PER_RUN=3; answer may be partial.
```

Status: PASS.

## Trace JSON

Checked recent run traces with PowerShell `ConvertFrom-Json`:

```powershell
Get-Content -Raw .\runs\20260520T023818Z.json | ConvertFrom-Json | Out-Null
Get-Content -Raw .\runs\20260520T023624Z.json | ConvertFrom-Json | Out-Null
Get-Content -Raw .\runs\20260520T023749Z.json | ConvertFrom-Json | Out-Null
```

Actual:

```text
PASS
```

Status: PASS.
