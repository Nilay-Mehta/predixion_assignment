# Eval Run — 2026-05-20

**LLM provider:** GitHub Models (`gpt-4o-mini`)
**Search:** Tavily (free tier, `search_depth=basic`)
**Pass rate:** 5/5 (`ok: true` across all queries)
**Wall-clock total:** ~95 seconds for all 5 queries

## What worked

- **All 5 queries completed end-to-end** with valid, schema-conformant FinalAnswer outputs.
- **Citations enforced inline.** Every `key_finding` in a sourced answer ends with `[N]` indices pointing into the `sources` array. The synthesizer's post-validation drops any finding whose citations don't resolve to a real source URL — so reviewers can trace each claim back to a specific URL.
- **Low-confidence answers carry their own warning.** When `confidence="low"`, the `short_answer` is automatically prefixed with `LOW CONFIDENCE - verify before relying on this answer.` so the caveat travels with the output.
- **Hallucination guards held on the canonical paths:**
  - `nonexistent_startup` returned 0 sources and an explicit `"No reliable information was found..."` placeholder finding, rather than inventing funding rounds
  - `trivial_math` returned 0 sources and no fabricated citations
- **Graceful failure handling visible in traces:** `indian_hr_saas` step 2 attempted to fetch a planner-fabricated URL (`https://example.com/startup1`); the fetch failed cleanly (`ok=False`, 404) and the run continued using the web_search results.
- **Tool diversity used across the run:** `web_search`, `github_search`, `fetch_url`, and the `none` synthesis-only step all appeared at least once.
- **LLM call budget:** 2–4 calls per query, well under the 12-call hard cap.
- **Speed:** 6–26s per query on `gpt-4o-mini`; total 5-query run completed in ~95s.

## What broke (or didn't go as well as it could have)

- **Planner occasionally proposes placeholder URLs.** In `indian_hr_saas`, the plan included a `fetch_url("https://example.com/startup1")` step — a URL the planner constructed rather than pulling from the prior web_search results. The fetch failed gracefully (404) and didn't poison the output, but it wastes one LLM call + one tool call per occurrence. **Mitigation for future work:** pass the titles+URLs from prior tool results into the planner/executor context when planning subsequent fetch steps.
- **Run-to-run confidence variance on `gpt-4o-mini`.** Re-running the same query with the same prompts and tools occasionally produces different confidence labels (e.g., `indian_hr_saas` returned `medium` in an earlier run with 5 sources, `high` in this run with 1 cited source after citation filtering). This is non-determinism in the LLM, not a code regression — but it argues for either a temperature=0 enforcement at the synthesis step or an LLM-as-judge calibration pass (listed as future work).
- **`indian_hr_saas` answer included Rippling.** Rippling is a US-based company, not an Indian B2B SaaS startup. The synthesizer pulled the name from a web search snippet without checking geographic context. Confidence was reported `high`, which is overcalibrated given this kind of factual slippage. A more rigorous prompt or a fact-checking judge step would catch this.
- **`mojo_state` confidence was overstated.** A recency-sensitive query ("current state of Mojo as a Python alternative for ML in 2026") with only one web_search step returned `confidence=high` — `medium` would have been more honest about the depth of evidence.
- **`vector_dbs` favored star count over relevance.** `github_search` is sorted by stars by default, which surfaced Redis (a cache with vector capabilities, 74k stars) and pushed canonical vector DBs (Qdrant, Milvus, Chroma) below. The answer correctly listed Weaviate and Redis among the top 3; Redis is borderline.
- **LLM provider portability is real but uneven.** During development we tested across multiple model variants (Gemini 2.5 Flash, Gemini 2.5 Flash Lite, Groq `llama-3.3-70b-versatile`, Groq `llama-3.1-8b-instant`, Groq `openai/gpt-oss-120b`, GitHub Models `gpt-4o-mini`). Smaller/weaker models exhibited clear regressions:
  - `llama-3.1-8b-instant`: planner hallucinated placeholder URLs (`https://github.com/your-database-1`); confidence calibration was broken (reported `high` confidence for the nonexistent QuantumPickleAI)
  - `openai/gpt-oss-120b`: planning was excellent (separate `github_search` per DB) but synthesis failed on `vector_dbs`; `trivial_math` was overconservative (`confidence=low` for arithmetic)
  - `gpt-4o-mini` was the most reliable across all 5 queries on free-tier quotas — this is why it's the canonical provider for this eval.

## Per-query notes

- **vector_dbs** — `ok=true`, `confidence=high`, 3 sources, 4 LLM calls, 19s. Plan: `web_search` → `github_search` → `none` (synthesis). Citations: `[N]` references attached to each finding. Answer leans on Redis due to github_search star-sort bias, but cited sources are real and clickable.
- **indian_hr_saas** — `ok=true`, `confidence=high`, 1 source, 4 LLM calls, 26s. `web_search` returned 5 useful results; `fetch_url` tried a planner-fabricated URL (`example.com/startup1`) and failed gracefully. Citation filtering dropped most sources, leaving 1. Confidence `high` is overstated given the thin grounding and the Rippling-as-Indian error.
- **mojo_state** — `ok=true`, `confidence=high`, 3 sources, 3 LLM calls, 24s. Web search only; plan was conservative. The recency stress would have warranted `medium`; `high` is slightly overconfident.
- **nonexistent_startup** — `ok=true`, `confidence=low`, 0 sources, 4 LLM calls, 18s. Single `web_search`, no sources cited in the final answer. `short_answer` includes the low-confidence warning prefix; `key_findings` contains the explicit `"No reliable information was found..."` placeholder. **This is the most important behavior to verify and it held: the agent did not fabricate funding history.**
- **trivial_math** — `ok=true`, `confidence=high`, 0 sources, 2 LLM calls, 6s. Planner correctly emitted a `suggested_tool=none` plan; synthesizer answered "4" directly. No fabricated sources, no warning prefix (high confidence is right).

## Methodology notes (honest disclosure)

- **Sample size is small.** Five queries are not a statistically significant evaluation. Treat this as a smoke test that exercises distinct code paths (comparison, enumeration, recency, graceful failure, tool-skip), not a benchmark.
- **Manual rubric, not LLM-as-judge.** Scores in `rubric.md` are filled in by hand from the trace files. An automated judge would be future work.
- **No held-out test set.** The 5 queries are hand-crafted to cover specific behaviors; we don't have a held-out set for regression tracking.
- **gpt-4o-mini is non-deterministic at temperature > 0.** Confidence labels can drift between runs for the same query. Reported numbers reflect a single run.

## Manual scores

Per-query scores below; rubric definitions in `rubric.md`.

| Query | Plan quality | Tool selection | Source grounding | Confidence calibration | Edge case handling | Total |
|---|---|---|---|---|---|---|
| vector_dbs | 4 | 5 | 4 | 3 | 5 | 21/25 |
| indian_hr_saas | 3 | 3 | 3 | 2 | 4 | 15/25 |
| mojo_state | 3 | 2 | 3 | 3 | 3 | 14/25 |
| nonexistent_startup | 3 | 3 | 5 | 5 | 5 | 21/25 |
| trivial_math | 5 | 5 | 5 | 5 | 5 | 25/25 |
| **Total** | **3.6** | **3.6** | **4.0** | **3.6** | **4.4** | **96/125** |

See `rubric.md` for per-query rationale and aggregate takeaways.
