# Eval Rubric

Each dimension scored 1–5 from the trace files in `evals/results/`. Scores reflect what actually happened in the run, not aspirational behavior.

## Dimensions

- **Plan quality** — Are the steps sensible, ordered logically, and non-redundant for the question?
- **Tool selection** — Was the right tool used per step? Did the planner ignore obvious options (e.g., not using github_search on an open-source comparison)?
- **Source grounding** — Are cited URLs real, traceable to tool results, and substantively informative for the answer? Penalize fabricated, irrelevant, or padding citations.
- **Confidence calibration** — Does the confidence label match the actual evidence strength? Low for thin/missing data, high for well-sourced or trivially-true answers.
- **Edge case handling** — How did the agent behave on the unhappy path (tool failure, no results, fake entity, trivial query)? Penalize crashes, fabrication, or wasted retries.

## Scores

| Query | Plan quality | Tool selection | Source grounding | Confidence calibration | Edge case handling | Total | Notes |
|---|---|---|---|---|---|---|---|
| vector_dbs | 4 | 5 | 4 | 3 | 5 | **21/25** | Strong plan and tools; both web_search and github_search used. Cited URLs are real, but the synthesizer picked Redis (a cache with vector support) over Qdrant/Chroma/Milvus because github_search was sorted by stars — `high` confidence is overstated given the lean toward star-count over relevance. |
| indian_hr_saas | 3 | 3 | 3 | 3 | 4 | **16/25** | 2-step plan was thin for an enumeration task; could have done one fetch per company. The planner fabricated a placeholder URL (`example.com/startup1`) for step 2 — wasted a call but failed gracefully. Final answer included Rippling (US-based) as an "Indian" startup — geography error from search-snippet synthesis. Medium confidence partially excuses it but should arguably be lower. |
| mojo_state | 3 | 2 | 3 | 4 | 3 | **15/25** | Single web_search step; planner didn't reach for github_search (Mojo's repo) or fetch on Modular's blog. Sources cited are real (medium.com, reddit, quora) but not authoritative. Medium confidence is honest about the thin evidence. No failure to test edge handling here. |
| nonexistent_startup | 3 | 3 | 5 | 5 | 5 | **21/25** | Single-step plan; conservative but the result is what matters here. **The agent received one irrelevant search hit (clay.com OpenAI funding page) and refused to cite it.** Sources: `[]`. Confidence: `low`. Honest limitations. This is the canonical no-hallucination demo. |
| trivial_math | 5 | 5 | 5 | 5 | 5 | **25/25** | Planner emitted a single `suggested_tool=none` step; synthesizer answered "4" directly. Zero fabricated sources to pretend research happened. Confidence: high (correct). The strongest signal that the agent knows when not to use tools. |

## Aggregate

- **Total:** 98 / 125 (avg 3.92 / 5 per dimension)
- **Plan quality avg:** 3.6 — planner is conservative; tends toward minimal step counts on harder queries
- **Tool selection avg:** 3.6 — under-uses github_search and fetch_url; over-relies on web_search alone
- **Source grounding avg:** 4.0 — strong (no hallucination on the failure paths) but lets star-sorted github results bias comparison queries
- **Confidence calibration avg:** 4.0 — correct on the easy and hard ends (trivial, nonexistent); overstated on vector_dbs
- **Edge case handling avg:** 4.4 — strongest dimension; graceful on placeholder URL fetches, no-info searches, and the no-tool path

## Key takeaways

1. **No-hallucination behavior is reliable.** `nonexistent_startup` and `trivial_math` both refused to fabricate sources. This is the most important production property.
2. **Planner is conservative.** On both `mojo_state` and `nonexistent_startup`, deeper plans (multiple tool types per query) would likely raise quality. Future work: have the planner produce a wider catalog of steps and let the executor prune.
3. **Tool selection is under-rotated.** Across 5 queries, `web_search` was used 5 times, `fetch_url` 1 time (and that one was a placeholder URL), `github_search` 1 time. The planner under-uses github_search on comparison queries and fetch_url on enumeration queries.
4. **Synthesizer occasionally over-confident.** `vector_dbs` returned `high` despite the github_search returning Redis (a cache, not primarily a vector DB) as the top hit. A judge step or grounding-quality heuristic would help.
