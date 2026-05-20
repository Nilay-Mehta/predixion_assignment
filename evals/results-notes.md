# Eval Run — 2026-05-20

**LLM provider:** GitHub Models (`gpt-4o-mini`)
**Search:** Tavily (free tier, `search_depth=basic`)
**Pass rate:** 5/5 (`ok: true` across all queries)
**Wall-clock total:** ~80 seconds for all 5 queries

## What worked

- **All 5 queries completed end-to-end** with valid, schema-conformant FinalAnswer outputs.
- **Confidence calibration was correct across all queries:**
  - `high` for the well-sourced comparison (vector_dbs) and trivial arithmetic (trivial_math)
  - `medium` for partial-data enumeration (indian_hr_saas) and recency-sensitive synthesis (mojo_state)
  - `low` for the nonexistent entity (nonexistent_startup) — and with 0 sources, meaning no fabrication
- **Tool selection diversity:** across the 5 runs, `web_search`, `github_search`, `fetch_url`, and the `none` synthesis-only step were all used. The planner correctly chose `github_search` for the vector DB comparison (structured repo data) and skipped tools entirely for `trivial_math`.
- **Hallucination guards held:**
  - `nonexistent_startup` returned 0 sources rather than inventing any
  - `trivial_math` returned 0 sources rather than padding the answer with fake citations
- **Graceful failure handling visible in traces:**
  - `indian_hr_saas` step 2 attempted to fetch a planner-fabricated URL (`https://example.com/startup1`); the fetch failed cleanly (`ok=False`) and the run continued using the web_search results
- **LLM call budget:** 2–4 calls per query, well under the 12-call hard cap.
- **Speed:** 14–19s per query on `gpt-4o-mini`; total 5-query run completed in ~80s.

## What broke

- **Planner occasionally proposes placeholder URLs.** In `indian_hr_saas`, the plan included a `fetch_url("https://example.com/startup1")` step — a URL the planner constructed rather than pulling from the prior web_search results. The fetch failed gracefully and didn't poison the output, but it wastes one LLM call + one tool call per occurrence. **Mitigation for future work:** pass the titles+URLs from prior tool results into the planner/executor context when planning subsequent fetch steps, instead of relying on the model to remember them.
- **`mojo_state` and `nonexistent_startup` were under-investigated.** Both used a single `web_search` before synthesizing. For `nonexistent_startup`, conservative behavior is correct (`confidence=low` is right). For `mojo_state`, a deeper plan (web + github + fetch on Modular's blog) would have produced a stronger answer. The medium confidence is honest about that depth.
- **LLM provider portability is real but uneven.** During development we tested across multiple model variants (Gemini 2.5 Flash, Gemini 2.5 Flash Lite, Groq llama-3.3-70b-versatile, Groq llama-3.1-8b-instant, Groq openai/gpt-oss-120b, GitHub Models gpt-4o-mini). The smaller and weaker models exhibited clear regressions:
  - `llama-3.1-8b-instant`: planner hallucinated placeholder URLs (`https://github.com/your-database-1`); confidence calibration was broken (reported `high` confidence for the nonexistent QuantumPickleAI)
  - `openai/gpt-oss-120b`: planning was excellent (separate `github_search` per DB) but synthesis failed on `vector_dbs` (`ok=False`); `trivial_math` was overconservative (`confidence=low` for arithmetic)
  - `gpt-4o-mini` was the most reliable across all 5 queries on free-tier quotas — this is why it's the canonical provider for this eval.

## Per-query notes

- **vector_dbs** — `ok=true`, `confidence=high`, 3 sources, 4 LLM calls, 19s. Plan: `web_search` → `github_search` → `none` (synthesis). Clean comparison output; the most canonical example query and the agent handled it well.
- **indian_hr_saas** — `ok=true`, `confidence=medium`, 5 sources, 4 LLM calls, 19s. `web_search` returned 5 useful results; `fetch_url` tried a planner-fabricated URL (`example.com/startup1`) and failed gracefully. Medium confidence is appropriate — sources are from search snippets, not deep-read company pages.
- **mojo_state** — `ok=true`, `confidence=medium`, 3 sources, 3 LLM calls, 19s. Web search only; plan was conservative. The recency stress was handled by the synthesizer downgrading confidence rather than inventing 2026 details.
- **nonexistent_startup** — `ok=true`, `confidence=low`, 0 sources, 3 LLM calls, 14s. Single `web_search`, no sources cited in the final answer. **This is the most important behavior to verify** — the agent did not fabricate funding history, and it kept 0 sources rather than padding with weak matches.
- **trivial_math** — `ok=true`, `confidence=high`, 0 sources, 2 LLM calls, 7s. Planner correctly emitted a `suggested_tool=none` plan; synthesizer answered "4" directly. **No fabricated sources** to pretend research happened.

## Methodology notes (for honest disclosure in the README)

- **Sample size is small.** Five queries are not a statistically significant evaluation. Treat this as a smoke test that exercises distinct code paths (comparison, enumeration, recency, graceful failure, tool-skip), not a benchmark.
- **Manual rubric, not LLM-as-judge.** Scores in `evals/rubric.md` are filled in by hand from the trace files. An automated judge would be future work (listed as a stretch goal).
- **No held-out test set.** The 5 queries are hand-crafted to cover specific behaviors; we don't have a held-out set for regression tracking.
- **Provider variance documented but not formally measured.** We observed clear quality differences across LLM providers but didn't run the full 5-query eval through every provider for direct A/B comparison (free-tier quotas).

## Manual scores

Filled in after reviewing each trace JSON; rubric definitions in `evals/rubric.md`.

| Query | Plan quality | Tool selection | Source grounding | Confidence calibration | Edge case handling | Total |
|---|---|---|---|---|---|---|
| vector_dbs | 4 | 5 | 4 | 3 | 5 | 21/25 |
| indian_hr_saas | 3 | 3 | 3 | 3 | 4 | 16/25 |
| mojo_state | 3 | 2 | 3 | 4 | 3 | 15/25 |
| nonexistent_startup | 3 | 3 | 5 | 5 | 5 | 21/25 |
| trivial_math | 5 | 5 | 5 | 5 | 5 | 25/25 |
| **Total** | **3.6** | **3.6** | **4.0** | **4.0** | **4.4** | **98/125** |

See `evals/rubric.md` for per-query rationale and aggregate takeaways.
