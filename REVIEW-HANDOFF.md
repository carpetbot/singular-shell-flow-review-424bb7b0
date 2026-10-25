# Sofa independent review handoff

## Status / permission boundary
Local build complete. Nothing deployed to Innstance and no paid model inference was performed. Publishing this review repo is code transfer only, not approval to replace the live site. Hold deployment until Sofa reports independent review results and Shuenrui approves. Alice owns deployment through the existing Pro login; do not copy that login here.

## What to review
Plain JavaScript plus proxy.py shell, adding ordered runtime.steps[] flows without breaking v0.1 Motion Trimmer. The supplied prospect-notes-to-email flow uses extraction, angle selection, writing plus two follow-ups, then audit. Exact supplied model identifiers and prompts are in skills/impossibuild__prospect-to-cold-email/. No web research and no email sending are implemented. Prior outputs are raw strings; JSON parse repair retries once per model; HTTP errors use ordered fallback models except terminal auth/authorization/balance failures. Estimate controls are not billing caps.

Changed pre-existing source: js/views/skills.js, js/api.js, proxy.py. New production source: js/flow.js, js/flow-ui.js, flow manifest and eight prompts. Other original shell source files are unchanged. Prompt loader wiring is fixed. Static Python/source/test/doc/archive paths are denied under proxy.py.

## Exact original artifact
`dist/singular-shell-flow.zip` is the same production ZIP attached in Slack. SHA256 is in SHA256SUMS. `dist/singular-shell/` is its extracted contents. Repository root includes additional test source and recorded evidence; do not deploy the repository root or substitute an unrestricted static server.

## Reproduce without spend
Node built-in runner, Python stdlib for proxy checks; Python Playwright and installed system Chromium for optional UI smoke. No real API key is needed. Browser smoke uses offline chat interception and blocks external requests. A normal browser visit outside these tests fetches live pricing; never enter a real key or run inference during offline review.

    node --test tests/flow.test.mjs
    python3 -m unittest discover -s tests -p test_proxy.py -v
    python3 -m unittest discover -s tests -p test_ui.py -v
    node reports/estimate_probe.mjs
    PYTHONDONTWRITEBYTECODE=1 python3 reports/verify_package.py

The packaged verification script requires dist/singular-shell/ and its ZIP, both included. Prevent/remove generated dist/singular-shell/__pycache__ before repeat package checks; the verification excludes caches.

## Prior executed results, not proof of live inference
19 Node tests, 2 proxy tests and 1 real Chromium UI smoke passed. Public pricing snapshot is complete in reports/catalog-live.json. Small Sample/hiring input has estimated normal-route cost $0.020897823799080003; default $0.10 permits four offline fixture calls; $0.001 refuses before any chat call. Receipts/chat outputs in tests are fixtures, not provider results. See TEST_REPORT.md and reports/ for evidence and TDD ledger.

## Risks Sofa already identified: inspect and report, not silently bypass
1. Missing token usage makes cost unknown and stops subsequent calls. Live gateway usage coverage unverified.
2. stop_if currently requires a numeric JSON value. A string fit_score such as "2" will not trigger a numeric threshold; schema validation/coercion needs review.
3. Existing Settings routing.maxPrice behavior is inherited; price units and interaction with exact-model requests must be verified before a paid run. Inspect js/store.js and js/api.js rather than assuming it is a per-run dollar limit.
4. Gallery card currently says '4 steps · exact models', while actual IDs appear inside the runner; full gallery model-list requirement is not implemented.
5. The client API receipt uses the gateway-reported model when supplied; that does not independently prove which upstream actually executed.

## Deployment boundary
Alice uses DEPLOYMENT.md after approval, including account check, backup, push, existing-listener restart and rollback. A nohup command is not a reboot persistence solution. Production root/manifest should return 200 and GET/HEAD /proxy.py 404. Live model/JSON-format support, semantic output quality and actual billing remain outstanding and require the approved capped key.

## Reply requested from Sofa
Confirm downloaded ZIP hash, files/code reviewed and independent test results. Separate blockers from live-only risks. State deploy/no-deploy recommendation. Do not claim live completion from offline fixtures.
