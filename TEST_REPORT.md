# Test report — Singular multi-step flows

Executed locally on 2026-10-25 (+08:00). No deployment, paid requests, contacts, real credentials, commits or remote writes. The source directory is not a Git repository.

## Final executed results

| Check | Actual result |
|---|---|
| `node --test tests/flow.test.mjs` | **19 passed, 0 failed**, exit 0; 252.927559 ms |
| `python3 -m unittest discover -s tests -p test_proxy.py -v` | **2 passed**, exit 0; 0.578 s |
| `python3 -m unittest discover -s tests -p test_ui.py -v` | **1 passed**, exit 0; 3.582 s; real system Chromium |
| JS/Python syntax | `node --check` passed for 11 JS modules; `py_compile` passed for `proxy.py` |
| Browser runtime | No pageerror events; four flow calls plus legacy call; public-price snapshot and offline chat fixtures |
| Acceptance probe | `node reports/estimate_probe.mjs`: default $0.10 → done, 4 offline calls; $0.001 → failed, 0 calls |

Raw results: `reports/node-tests.txt`, `reports/proxy-tests.txt`, `reports/browser-tests.txt`. Environment details remain in `reports/environment.txt`. The browser uses installed system Chromium, not the unavailable bundled headless executable. Screenshots: `reports/flow-ui.png` and `reports/flow-ui-top.png`.

## Preflight correction: RED → GREEN

The TDD skill was loaded before modification. The regression used the supplied manifest, all eight exact prompts, and the recorded unauthenticated public catalog `reports/catalog-live.json` (`as_of: 2026-10-24T16:56:21.780Z`). No new model requests were made.

1. **RED:** ordinary small input at default $0.10 returned `failed`, estimating **$3.1479878254680003**; expected `done`. A second assertion showed fallback reservation increased the estimate from 0.000654 to 0.001922 instead of only validating its price. Both failures are recorded in `reports/preflight-red.txt`.
2. **GREEN:** input estimate is now `ceil(UTF-8 bytes / 4) + 128` framing tokens per call. Preflight sums one primary call per step, maximum output allowances, and every repeated downstream placeholder at 4 bytes/output token. All fallback prices are still validated up front. Conditional repairs and mutually exclusive fallbacks are not reserved in advance. The 17-test intermediate run passed (`reports/preflight-green.txt`).
3. **RED:** omitted output limit threw `Finite max_output_tokens required`; `reports/default-output-red.txt` records the failure. An added regression for refusing unaffordable repairs/fallbacks already passed against the existing per-call guard; it was not claimed as a new RED behavior.
4. **GREEN:** both preflight and request options consistently use `max_output_tokens || 2048`. Final 19-test suite passed. Browser smoke now uses the recorded public prices instead of artificially cheap stand-ins and also passed.

### Exact small-input acceptance

Input: prospect/company/sender `Sample`, research notes `The team is hiring.`, offer `Help with hiring.`; other fields omitted. The unchanged supplied four-step manifest estimates **$0.020897823799080003** on the recorded public catalog.

- Default **$0.10**: four injected offline chat results complete (`done`).
- Hard **$0.001**: preflight refuses with **zero chat calls**.
- Full machine-readable input, prices, estimate, and call counts: `reports/preflight-acceptance.json`.
- Reproduce with `node reports/estimate_probe.mjs`. This script performs no HTTP requests and uses no key.

These are **estimated costs, not guaranteed bills**. Catalog entries report all five required IDs as routable; that is not proof of successful paid inference or live JSON-format support.

## Retained coverage

- Flow-first loader, legacy fallback only on HTTP 404, prompt attachment, inline templates and eight supplied prompt files.
- Ordered steps/statuses; safe own-property paths; whitespace/dotted templates; prior raw outputs; repeated downstream references; default output limits.
- JSON fences, one same-model repair, failed second JSON attempt, no JSON-only fallback, per-fallback repair allowance.
- Explicit models/no auto; unknown primary/fallback pricing rejected before calls. Normal-route preflight validates fallback pricing without reserving every path.
- **Before every primary/repair/fallback call**, accumulated receipt estimates plus that call's actual rendered input/max-output estimate must fit the ceiling. Unaffordable fallback/repair tests verify exactly one prior call and no additional request. Invalid JSON and HTTP estimates/usage receipts remain accounted. Unknown usage or transport/timeout cost stops further calls. Authentication/authorization/balance failures remain terminal.
- Supported `response_format: {"type":"json_object"}`, abort signal, deadline, stop_if and downstream skip semantics retained.
- Real loopback GET/HEAD deny Python, encoded/query paths, tests, symlinks, traversal and directories; shell assets still served.
- Real Chromium card→runner smoke covers preview, four chained steps, nested plain-text output, escaping, clipboard, raw details, and legacy preview/run. No pageerrors; external requests blocked.

## Boundaries

Node tests inject offline chat/catalog/fetch functions without replacing the flow engine. Browser tests exercise the actual shell and Python server, intercepting pricing with the recorded public snapshot and chat with clearly offline responses. Proxy/package checks use real loopback HTTP. No test supplied a real API key or performed paid requests.

Input bytes/4 and synthetic output sizes are heuristics, not tokenizer bounds. Preflight is a normal-route estimate, not worst-case reservation; retries can leave insufficient budget for later steps and execution then stops at the next per-call guard. Receipt estimates can differ from real billing; an already-started request may exceed the estimate. Missing pricing/usage is unknown, never zero. Abort is not proof of upstream cancellation.

Outstanding: authorized real model/JSON-format integration, output quality, real usage/billing, mobile/accessibility/multi-browser testing, and production TLS/access controls. The tool does not research independently, enforce semantic JSON schemas/factual accuracy, or send email. Deployment remains Alice's responsibility.

## Verified artifacts

- Deployment folder: `/home/orangepi/projects/singular-shell/dist/singular-shell/`
- Archive: `/home/orangepi/projects/singular-shell/dist/singular-shell-flow.zip`
- Tests/evidence: `/home/orangepi/projects/singular-shell/tests/` and `reports/` (excluded from deployment archive).
- `reports/verify_package.py` checks exact source/deployment/ZIP bytes, ZIP CRC, credential/cache/test exclusion, and packaged loopback GET/HEAD serving/denials. Actual verification output and SHA256 are in `reports/package-verification.txt`.
