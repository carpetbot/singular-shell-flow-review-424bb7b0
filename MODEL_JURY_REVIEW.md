# Model Jury — local implementation review

**Scope:** branch `model-jury-graph`, based on approved `e064eeb`. The current behavior specification is `shuenrui/singular-flows` commit `db27a89a2dd99d80d32017fd0ad6c0eb764912a1`, `designs/model-jury/{rules.py,test_rules.py,DESIGN.md,CODEX-BRIEF.md}`, explicitly authorized after the original archive freeze. Existing manifests and all prompts remain unchanged. This replacement ZIP is published on the review branch for Sofa's approval; it is not deployed. No paid inference or deployment was performed for this revision.

## Acceptance evidence

| # | Criterion | Executed evidence / outcome |
|---|---|---|
| 1 | Twelve JS reference cases plus pinned Python | `tests/graph.test.mjs` includes all 12 cases, including exact case 11 must-have assertions and case 12 quote-error assertions. Current complete Node suite: 64 passing tests. Pinned Python reference: 12/12 passing. Current evidence uses the `38-*` reports; unnumbered final reports describe the preceding build. |
| 2 | Real offline browser, blind judge request | Chromium via installed Playwright, actual loader/UI/API code. Five calls with intercepted fake responses; contestant IDs, `slot_1..3` and private map absent from the judge body. Exact captured body: `judge-request.offline.json`. Lite/Pro/mobile screenshots are explicitly offline fixtures. |
| 3 | Same-maker judge, zero calls | Real Chromium test and `same-maker.offline.json`: stopped before any gateway call. |
| 4 | Contestant HTTP 500 behavior | `one-http500.offline.json`: five total calls, two ranked answers, failed node receipt retained. `two-http500.offline.json`: four total calls, zero judge calls, clean minimum-answer stop. A separate Node case proves the engine excludes a failed anonymous placeholder even if a judge scores it. |
| 5 | Unknown cost never wins best value | JS reference case 8 reproduces the original Python case: unknown-cost best overall cannot win value; known-cost near-best wins. Unknown API usage instead stops future graph calls under the budget policy; it is never silently replaced with zero. |
| 6 | Careful mode | `careful.offline.json`: exactly six calls rather than five, two judge calls, same label-to-answer mapping in reverse order, gaps of exactly 2 flagged. Node test proves the preflight includes the extra call and rejects a cap between the normal and careful estimates before any call. |
| 7 | Legacy regression / protected bytes | Actual Chromium requests captured for both base and current: four Cold Email bodies plus one Motion Trimmer body are identical; `legacy-request-bodies.diff` is 0 bytes. `protected-hashes.json` verifies 15 protected files, including all four locked files and every prior manifest/prompt. Base suite: 23 Node + 12 Python tests pass; initial build: 51 Node + 18 Python tests pass; replacement: 64 Node and 10 targeted browser tests pass, including the new careful-pass fixtures. The parent independently reran the legacy request comparison on the replacement with zero differences. Only gallery-count expectations change from two cards to three. |
| 8 | Static source/test/doc denial | `static-denials.json`: GET and HEAD return 404 on source and copied-runtime servers for Python source, tests, docs, encoded/query and traversal paths. Runtime root, graph JS, manifest and prompt return 200. Existing proxy-security suite also passes. |
| 9 | Replacement review ZIP and SHA256 | `dist/model-jury-review.zip` and adjacent `.sha256`; exact byte manifest in `reports/model-jury/package.json`. ZIP CRC, source/copied/ZIP byte equality and seven verbatim prompt copies verified. Replacement is published for review; unauthenticated download hash is verified by the parent before handoff. |

## Implementation

- `js/graph.js`: four named built-ins, safe template scope, model selection from inputs, ordered minimum graph scheduler, atomic group reservation before `Promise.allSettled`, per-call checks, failure receipts, deadline/abort, JSON validation, tally from slot receipts, careful reversal.
- `js/graph-ui.js`: required task/model/cap form; post-selection estimate; live status; Lite winner/value/folded others; Pro rubric, scores/quotes, tokens/cost receipts, final slot map and flags. No node graph visualization.
- `js/views/skills.js`: graph prompt loading, exact-ID priced model dropdown, one new gallery entry and graph-only routing. Legacy request construction and runner implementations remain untouched.
- `skills/impossibuild__model-jury/`: new deployable manifest and seven verbatim prompts. Added required `rubric_writer` picker and `model_from_input` on the otherwise unassigned rubric node. No models assigned by default. Draft cap retained as a user-visible placeholder, not live budget guidance.

## TDD and review notes

### Current independent-review corrections

- Must-have failures are a sorted, deduplicated union of both careful passes before ranking. Any failure excludes an answer from overall/value eligibility and ranks it below eligible answers. Different failure sets emit `criterion: "must_haves"` with both sorted lists in `scores`, including disagreements where both passes fail different requirements.
- Quote failures are also unioned. An invented quote is a judge error: only that criterion/pass score is capped at 2; capped pass averages are averaged, and score gaps of 2+ remain flagged. Quote errors **do not disqualify** an answer. This follows final pin `db27a89`; superseded intermediate instructions/experiments are not final behavior or a deviation.
- Model picker prices use three significant digits for display only; budget arithmetic and exact catalog values are untouched. Every picker has a labeled type-to-filter searchbox, preserving the selected exact ID while filtering case-insensitively. IDs ending `-latest` are hidden and rejected by graph preflight without normalization or fallback.
- When winner and value are the same answer, copy is exactly “The winner is also the best value.” Failed contestants in Lite show their exact model ID and “no answer (gateway error 500)”; technical details remain Pro-only.
- Strict TDD evidence: `30-must-have-{red,green}.txt`, `31-prices-{red,green}.txt`, `32-value-{red,green}.txt`, `34-final-quote-{red,green}.txt`, `35-failure-label-{red,green}.txt`, `36-alias-{red,green}.txt`, `37-search-{red,green}.txt`. `33-updated-spec-*` records superseded interim instructions, not final acceptance. Case 12's exact reference assertions already passed with quote disqualification, so additional winner/value eligibility tests were necessary and failed before the final correction. A browser follow-up assertion was narrowed to avoid matching `0.0%` inside valid `50.0%` savings.
- Final verification: `38-node-final.txt` passes 64/64 Node tests; `38-python-reference.txt` passes 12/12 tests at the pinned spec; `38-browser-final.txt` passes 10 real offline Chromium cases plus 2 proxy-security cases; `38-packaged-browser-final.txt` passes the same 10 browser cases against the copied runtime. `38-protected-final.txt` verifies 15 base hashes, 23 frozen files against HEAD and all seven prompts against the final pin. `38-package-final.txt` verifies the 37-file ZIP, CRC, source/copy/archive byte equality and GET/HEAD serving restrictions.
- Browser evidence is written to isolated scratch directories to avoid replacing unrelated screenshots and existing captured reports. Current browser suite includes second-pass-only must-have and invented-quote fixtures, exact failure copy, equality copy, search selection persistence and mutable-alias exclusion.

Each new behavior slice was tested and its intended failure observed before the corresponding engine/UI implementation; per-slice red/green transcripts are retained. Reference case 9 and positive careful integration expanded already-green behavior from earlier slices and required no new production changes; their first passing observations are retained as regression evidence, not mislabeled as red tests. The timeout red test exposed a real hang, terminated by the execution timeout; the fix then passes a 20ms injected-deadline test. Early float-equality and browser-whitespace assertion issues were corrected in tests; the genuine feature failures remain in transcripts.

Additional tested safeguards: nonnumeric/missing caps; unroutable/non-chat/router IDs; missing prices; unknown code nodes; per-call overrun/unknown-usage refusal; atomic parallel reservation; invalid rubric/judge JSON with billed attempt retained; private-map/identity template access blocked; exact punctuation-bearing catalog IDs; exact graph receipt pricing without the legacy client's colon normalization; Python-compatible ties-to-even rounding.

Self-review: no credential values in runtime source, no eval/Function construction, no executable code from manifests, no protected-file edits. No independent reviewer was spawned in this one-shot subagent; parent review remains required before release. The local commit, if created, does not claim an independent `[verified]` approval.

## Commands

Run from the shell root:

```sh
node --test tests/*.test.mjs
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p 'test_*.py' -v
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s ../spec-repo/designs/model-jury -p test_rules.py -v
PYTHONDONTWRITEBYTECODE=1 python3 reports/model-jury/legacy_compare.py
PYTHONDONTWRITEBYTECODE=1 python3 reports/model-jury/build_verify_package.py
JURY_APP_ROOT="$PWD/dist/model-jury-shell" PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p test_model_jury.py -v
```

The reference Python and original private design are not included in the deployable ZIP or local review-evidence ZIP. Their executions remain logged locally. `legacy_compare.py` expects the approved base extracted at sibling `base-e064eeb`; the package verification additionally checks prompt copies against the original sibling archive extraction.

## Limitations / remaining release gates

- No real model quality, real billing, live routing or external deployment was tested. All inference replies were explicitly fake offline fixtures; public pricing is a recorded catalog fixture for tests and fetched dynamically by the actual application.
- Cost caps are client-side heuristics, not guaranteed billing caps. Already-started parallel upstream calls may still bill after timeout or another result makes cost unknown.
- Maker identity uses the provider prefix, exactly as the reference. Fine-tunes/rebrands and self-identifying answer text can defeat true anonymity; no maker genealogy or content rewriting is added.
- The pinned reference's careful-pass semantics are retained: must-have failures disqualify; quote errors cap scores but do not disqualify. Both pass records and disagreement flags are available, not an independent fact check.
- Independent re-review passed with no security or logic concerns after the final correction. Sofa approval remains a release gate. The public ZIP uses the runtime allowlist, not the private archive or incidental design sources.
