# Eval Rubric

Each dimension scored 1–5 from the trace files in `evals/results/`. Scores reflect what actually happened in the run, not aspirational behavior.

## Dimensions

- **Plan quality** — Are the steps sensible, ordered logically, and non-redundant for the question?
- **Tool selection** — Was the right tool used per step? Did the planner ignore obvious options (e.g., not using `github_search` on an open-source comparison)?
- **Source grounding** — Are cited URLs real, traceable to tool results, and substantively informative for the answer? Penalize fabricated, irrelevant, or padding citations.
- **Confidence calibration** — Does the confidence label match the actual evidence strength? Low for thin/missing data, high for well-sourced or trivially-true answers.
- **Edge case handling** — How did the agent behave on the unhappy path (tool failure, no results, fake entity, trivial query)? Penalize crashes, fabrication, or wasted retries.

## Scores

| Query | Plan | Tools | Grounding | Calibration | Edge | Total | Notes |
|---|---|---|---|---|---|---|---|
| vector_dbs | 4 | 5 | 4 | 3 | 5 | **21/25** | Strong plan and tools — both `web_search` and `github_search` used. Each key finding has a `[N]` citation referencing a real URL. The synthesizer picked Redis (a cache with vector capabilities) over canonical vector DBs (Qdrant, Chroma) because `github_search` is sorted by stars by default, surfacing Redis at 74k stars. `confidence=high` is slightly overstated given Redis is borderline. |
| indian_hr_saas | 3 | 3 | 3 | 2 | 4 | **15/25** | 2-step plan was thin for an enumeration task; could have done one fetch per company. The planner fabricated a placeholder URL (`example.com/startup1`) for step 2 — wasted a call but failed gracefully with a clean 404. Final answer included Rippling (US-based) as an "Indian" startup — factual slippage from search-snippet synthesis. Citation enforcement dropped most sources, leaving 1, yet `confidence=high` — overcalibrated. |
| mojo_state | 3 | 2 | 3 | 3 | 3 | **14/25** | Single `web_search` step; planner didn't reach for `github_search` (Mojo's repo) or `fetch_url` on Modular's blog. Sources cited are real (medium.com, reddit, quora) but not authoritative. `confidence=high` is slightly overstated for a recency-sensitive query — `medium` would have been more honest. |
| nonexistent_startup | 3 | 3 | 5 | 5 | 5 | **21/25** | Single-step plan; conservative but the result is what matters here. **The agent received irrelevant search hits and refused to cite them.** `sources=[]`, `confidence=low`, `short_answer` carries the `LOW CONFIDENCE - verify before relying on this answer.` prefix, and `key_findings` contains an explicit `"No reliable information was found..."` placeholder. This is the canonical no-hallucination demo, and it held. |
| trivial_math | 5 | 5 | 5 | 5 | 5 | **25/25** | Planner emitted a single `suggested_tool=none` step; synthesizer answered "4" directly. Zero fabricated sources, no warning prefix (high confidence is right). The strongest signal that the agent knows when not to use tools. |

## Aggregate

- **Total:** 96 / 125 (avg 3.84 / 5 per dimension)
- **Plan quality avg:** 3.6 — planner is conservative; tends toward minimal step counts on harder queries
- **Tool selection avg:** 3.6 — under-uses `github_search` and `fetch_url`; over-relies on `web_search` alone
- **Source grounding avg:** 4.0 — strong (no hallucination on the failure paths) but lets star-sorted `github_search` results bias comparison queries
- **Confidence calibration avg:** 3.6 — correct on the easy and hard ends (`trivial_math`, `nonexistent_startup`); overstated on `indian_hr_saas` (high with 1 source) and `mojo_state` (high on a recency-sensitive question)
- **Edge case handling avg:** 4.4 — strongest dimension; graceful on placeholder URL fetches, no-info searches, and the no-tool path

## Key takeaways

1. **No-hallucination behavior is reliable.** `nonexistent_startup` and `trivial_math` both refused to fabricate sources. This is the most important production property of a research agent.
2. **Confidence calibration is the weakest dimension.** `gpt-4o-mini` returns `high` confidence too readily even on thin grounding. An LLM-as-judge calibration pass would catch this; listed as future work.
3. **Planner is conservative on harder queries.** `mojo_state` and `indian_hr_saas` could have used `github_search` and multiple `fetch_url` calls to deepen sources. Future work: bias the planner toward broader step catalogs and let the executor prune.
4. **Tool selection is under-rotated.** Across 5 queries, `web_search` was used 5 times, `fetch_url` 1 time (and that one was a placeholder URL), `github_search` 1 time. The planner under-uses `github_search` on comparison queries.
5. **Citation enforcement makes findings traceable but doesn't fix calibration.** The `[N]` post-validation guarantees that *what is cited* is real, but the synthesizer can still overstate confidence on thinly-cited answers. Calibration is a separate axis.
