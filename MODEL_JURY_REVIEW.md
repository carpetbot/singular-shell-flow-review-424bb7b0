# Model Jury — local implementation review

**Scope:** branch `model-jury-graph`, based on approved `e064eeb`. Branch and runtime review ZIP publication to `carpetbot/singular-shell-flow-review-424bb7b0` were authorized for review. No paid inference or deployment. The supplied archive remains the specification; no later private-repository changes were fetched for this build.

## Acceptance evidence

| # | Criterion | Executed evidence / outcome |
|---|---|---|
| 1 | Ten JS reference cases plus original Python | `tests/graph.test.mjs` begins with all 10 reference cases. The complete Node suite and copied-runtime Node suite each pass 51 tests. Original Python reference passes 10/10 unchanged. See `reports/model-jury/node-final.txt`, `packaged-node.txt`, `python-reference.txt`. |
| 2 | Real offline browser, blind judge request | Chromium via installed Playwright, actual loader/UI/API code. Five calls with intercepted fake responses; contestant IDs, `slot_1..3` and private map absent from the judge body. Exact captured body: `judge-request.offline.json`. Lite/Pro/mobile screenshots are explicitly offline fixtures. |
| 3 | Same-maker judge, zero calls | Real Chromium test and `same-maker.offline.json`: stopped before any gateway call. |
| 4 | Contestant HTTP 500 behavior | `one-http500.offline.json`: five total calls, two ranked answers, failed node receipt retained. `two-http500.offline.json`: four total calls, zero judge calls, clean minimum-answer stop. A separate Node case proves the engine excludes a failed anonymous placeholder even if a judge scores it. |
| 5 | Unknown cost never wins best value | JS reference case 8 reproduces the original Python case: unknown-cost best overall cannot win value; known-cost near-best wins. Unknown API usage instead stops future graph calls under the budget policy; it is never silently replaced with zero. |
| 6 | Careful mode | `careful.offline.json`: exactly six calls rather than five, two judge calls, same label-to-answer mapping in reverse order, gaps of exactly 2 flagged. Node test proves the preflight includes the extra call and rejects a cap between the normal and careful estimates before any call. |
| 7 | Legacy regression / protected bytes | Actual Chromium requests captured for both base and current: four Cold Email bodies plus one Motion Trimmer body are identical; `legacy-request-bodies.diff` is 0 bytes. `protected-hashes.json` verifies 15 protected files, including all four locked files and every prior manifest/prompt. Base suite: 23 Node + 12 Python tests pass; current: 51 Node + 18 Python tests pass. Only gallery-count expectations change from two cards to three. |
| 8 | Static source/test/doc denial | `static-denials.json`: GET and HEAD return 404 on source and copied-runtime servers for Python source, tests, docs, encoded/query and traversal paths. Runtime root, graph JS, manifest and prompt return 200. Existing proxy-security suite also passes. |
| 9 | Review ZIP and SHA256 | `dist/model-jury-review.zip` and adjacent `.sha256`; exact byte manifest in `reports/model-jury/package.json`. ZIP CRC, source/copied/ZIP byte equality and seven verbatim prompt copies verified. The runtime ZIP is published on the review branch for download, not deployed. |

## Implementation

- `js/graph.js`: four named built-ins, safe template scope, model selection from inputs, ordered minimum graph scheduler, atomic group reservation before `Promise.allSettled`, per-call checks, failure receipts, deadline/abort, JSON validation, tally from slot receipts, careful reversal.
- `js/graph-ui.js`: required task/model/cap form; post-selection estimate; live status; Lite winner/value/folded others; Pro rubric, scores/quotes, tokens/cost receipts, final slot map and flags. No node graph visualization.
- `js/views/skills.js`: graph prompt loading, exact-ID priced model dropdown, one new gallery entry and graph-only routing. Legacy request construction and runner implementations remain untouched.
- `skills/impossibuild__model-jury/`: new deployable manifest and seven verbatim prompts. Added required `rubric_writer` picker and `model_from_input` on the otherwise unassigned rubric node. No models assigned by default. Draft cap retained as a user-visible placeholder, not live budget guidance.

## TDD and review notes

Each new behavior slice was tested and its intended failure observed before the corresponding engine/UI implementation; per-slice red/green transcripts are retained. Reference case 9 and positive careful integration expanded already-green behavior from earlier slices and required no new production changes; their first passing observations are retained as regression evidence, not mislabeled as red tests. The timeout red test exposed a real hang, terminated by the execution timeout; the fix then passes a 20ms injected-deadline test. Early float-equality and browser-whitespace assertion issues were corrected in tests; the genuine feature failures remain in transcripts.

Additional tested safeguards: nonnumeric/missing caps; unroutable/non-chat/router IDs; missing prices; unknown code nodes; per-call overrun/unknown-usage refusal; atomic parallel reservation; invalid rubric/judge JSON with billed attempt retained; private-map/identity template access blocked; exact punctuation-bearing catalog IDs; exact graph receipt pricing without the legacy client's colon normalization; Python-compatible ties-to-even rounding.

Self-review: no credential values in runtime source, no eval/Function construction, no executable code from manifests, no protected-file edits. No independent reviewer was spawned in this one-shot subagent; parent review remains required before release. The local commit, if created, does not claim an independent `[verified]` approval.

## Commands

Run from the shell root:

```sh
node --test tests/*.test.mjs
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p 'test_*.py' -v
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s ../model-jury -p test_rules.py -v
PYTHONDONTWRITEBYTECODE=1 python3 reports/model-jury/legacy_compare.py
PYTHONDONTWRITEBYTECODE=1 python3 reports/model-jury/build_verify_package.py
JURY_APP_ROOT="$PWD/dist/model-jury-shell" PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p test_model_jury.py -v
```

The reference Python and original private design are not included in the deployable ZIP or local review-evidence ZIP. Their executions remain logged locally. `legacy_compare.py` expects the approved base extracted at sibling `base-e064eeb`; the package verification additionally checks prompt copies against the original sibling archive extraction.

## Limitations / remaining release gates

- No real model quality, real billing, live routing or external deployment was tested. All inference replies were explicitly fake offline fixtures; public pricing is a recorded catalog fixture for tests and fetched dynamically by the actual application.
- Cost caps are client-side heuristics, not guaranteed billing caps. Already-started parallel upstream calls may still bill after timeout or another result makes cost unknown.
- Maker identity uses the provider prefix, exactly as the reference. Fine-tunes/rebrands and self-identifying answer text can defeat true anonymity; no maker genealogy or content rewriting is added.
- The reference's careful-pass ranking semantics are retained; the report exposes both passes and disagreement flags rather than claiming an independent fact check.
- Independent code review and Sofa approval remain release gates. The public ZIP uses the runtime allowlist, not the private archive or incidental design sources.
