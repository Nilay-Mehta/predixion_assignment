# bot

bot is a CLI research agent for the Predixion AI assignment. It plans a bounded research workflow, calls external tools, and returns a structured `FinalAnswer` with sources, confidence, limitations, assumptions, and next steps.

## Quick Start

Requirements: Python 3.11+.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
```

Create `.env`:

```env
LLM_PROVIDER=github_models
GITHUB_MODELS_TOKEN=your_github_pat_with_models_permission
GITHUB_MODELS_MODEL=gpt-4o-mini
TAVILY_API_KEY=your_tavily_key
GITHUB_TOKEN=optional_but_recommended_for_higher_github_rate_limits
```

Where to get each key (all free tiers):

- **GitHub Models token** — github.com/settings/personal-access-tokens/new → create fine-grained PAT → Account permissions → Models → Read. ~150 req/day on `gpt-4o-mini`.
- **Tavily** — tavily.com → sign up → copy default `tvly-dev-...` key. 1000 credits/month free.
- **GitHub token** — github.com/settings/tokens → classic or fine-grained, no scopes required for public repo search. Optional; without it `github_search` is limited to 60 req/hr.

Alternative LLM providers (set `LLM_PROVIDER` accordingly):
- `gemini` — Google AI Studio key (`GOOGLE_API_KEY`), `GEMINI_MODEL=gemini-2.5-flash-lite` for higher free RPD
- `groq` — console.groq.com key (`GROQ_API_KEY`), `GROQ_MODEL=llama-3.3-70b-versatile`

Run:

```powershell
bot ask "Compare the top 3 open-source vector databases for a startup building RAG products."
```

Useful commands:

```powershell
bot plan "Compare open-source vector DBs"
bot tools list
bot tools call github_search --query "vector database" --sort stars
python -m bot.evals.runner
```

The system supports multiple LLM providers behind the same `LLMProvider` interface: `github_models`, `gemini`, and `groq`. The canonical eval run uses `gpt-4o-mini` via GitHub Models because it was the most reliable free-tier provider during testing.

## Architecture

The agent is a bounded planner-executor-synthesizer pipeline, not an open-ended ReAct loop.

```text
                   +----------+
   user question ->| Planner  |-- Plan(steps[], assumptions[])
                   +----------+
                        |
                        v
                   +----------+    +------------+
                   | Executor |<-->| Tools      |  web_search, fetch_url, github_search
                   +----------+    +------------+
                        |
                        v  list[ToolCall] with results, errors, timings
                   +-------------+
                   | Synthesizer |-- FinalAnswer (Pydantic)
                   +-------------+
```

Planner sees only the question and tool catalog. Executor chooses arguments and runs tools. Synthesizer receives the plan plus tool traces, drops tainted sources, enforces source grounding, and emits the final typed answer. Each full run can be saved as `runs/<timestamp>.json`.

## 1. Why An Agentic Approach?

Research questions need fresh, multi-source information that the model may not know: recent startups, niche regional companies, current project status, and source-backed comparisons. The agent decomposes the question into research steps, calls tools, and grounds claims in retrieved URLs. A single LLM call would be faster, but it would be much easier for it to invent facts or cite unverifiable sources.

## 2. What Tools Did You Use, And Why?

`web_search` uses Tavily for broad discovery and extracted page content. `fetch_url` uses `httpx` plus `trafilatura` for deeper reads when a snippet is too shallow. `github_search` uses the GitHub Search API for structured repo facts such as stars, language, license, topics, and last update.

Those three tools cover the intended research loop: discover sources, inspect specific pages, and gather structured open-source project metadata. More tools would add planner complexity without much extra value for this assignment.

## 3. How Does The System Handle Bad Tool Results?

Tool calls use retry handling for transient network failures and timeouts. Failed tools are recorded as `ToolCall(ok=False, error=...)` rather than crashing the whole run. Empty search results can trigger one query rewrite. Weak or empty results are filtered. If all usable evidence is missing, the final answer is low confidence with explicit limitations.

GitHub rate-limit errors are surfaced clearly, and traces preserve each tool's arguments, timings, result, and error state for debugging.

## 4. How Do You Reduce Hallucinations?

The final answer is a Pydantic model, not free-form text. The synthesizer prompt says to use only tool results and never invent URLs. More importantly, code post-validates that every `FinalAnswer.sources[].url` appears in the tool results. Sources that fail grounding are removed, and if grounding collapses entirely the answer is retried or downgraded.

Fetched/search content also passes through a prompt-injection sniffer. Suspicious content is marked `tainted=True` and excluded from synthesis.

## 5. How Would You Make This Production-Ready?

Production hardening would add persistent storage for traces, raw result storage, caching for repeated queries, async execution for independent steps, tenant-specific budgets, provider routing, and proper observability with OpenTelemetry or Langfuse. Eval runs should become CI gates with regression thresholds for source grounding, confidence calibration, and latency.

The current implementation is deliberately small: one CLI, one bounded loop, three tools, and readable traces.

## 6. What Would You Monitor In Production?

Operational metrics: latency percentiles, tool error rates, LLM validation failures, rate-limit errors, and cost per query.

Quality metrics: confidence distribution, source count and domain diversity, grounding failure rate, prompt-injection hit rate, and eval score drift.

Capacity metrics: Tavily quota usage, GitHub API rate limit, and provider-specific LLM quota burn.

## 7. What Were The Key Tradeoffs?

The main tradeoff is determinism over adaptivity. A planner-executor pipeline is easier to inspect and bound than an open ReAct loop, but it is less able to pivot mid-run. The executor mitigates this with one reformulated search retry.

The project also chooses hand-rolled orchestration over LangChain/LangGraph to keep the control flow obvious. It uses a CLI instead of a UI because the assignment values the agent loop, failure handling, and traceability over polish.

## Known Limitations

- Stale information is not detected if search returns old pages for a current question.
- Source bias and viewpoint diversity are not enforced.
- English-only sources are assumed.
- Paywalled content is limited to whatever `trafilatura` can extract unauthenticated.
- The eval set is only five hand-curated queries, not a statistically meaningful benchmark.

## Eval Results

Eval artifacts live in `evals/`:

- `evals/queries.yaml` - five test queries
- `evals/results/` - saved traces
- `evals/results/index.json` - summary metrics
- `evals/results-notes.md` - what worked, what broke, and manual notes
- `evals/rubric.md` - manual scoring sheet

The latest canonical run used GitHub Models `gpt-4o-mini`.

## Sample Outputs

Representative traces are in `samples/`:

- `samples/01_happy_path.json`
- `samples/02_graceful_failure.json`
- `samples/03_tool_skip.json`

## Future Improvements

Highest-value next steps:

- Add a non-agentic baseline flag and compare direct LLM output against the grounded agent.
- Add an LLM-as-judge evaluator for grounding, completeness, and calibration.
- Add inline citations per key finding.
- Cache tool results on disk for faster eval iteration.
- Run independent tool steps asynchronously.
- Add memory for follow-up questions.
- Wrap the agent with FastAPI for a production-shaped API surface.
