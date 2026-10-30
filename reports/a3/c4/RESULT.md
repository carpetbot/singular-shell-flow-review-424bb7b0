# Final A3 Part A evidence

Artifact: `dist/shell-ux-v1-a3.zip`
SHA256: `1d8dc68a5563fb8f7d5e40b0d4d61d8e444f4dff87da4d971f25aca9a59288e9`
49 runtime files; deterministic rebuild; source/archive/relocated/runtime copies
all byte-equal (`final-provenance.json`). Frozen21/21 unchanged;118 extracted
GET/HEAD allow/deny checks; zero credential-pattern hits or unexpected upstream.

Final COMPLETE suites (not the earlier failed/partial runs):
- `python3 tests/verify_a3.py --label a3-final-source`:101 Node /156 Python PASS.
- `python3 tests/verify_a3.py --runtime reports/a3/package-a3/relocated/runtime --label a3-final-packaged`:101 Node /156 Python PASS.
- `python3 tests/package_a3.py`, `tests/check_a3_frozen.py`, `tests/verify_final_a3.py`:PASS.
All Chromium fixtures use real IDB/Web Locks; guards remain through teardown.
Logs: `../a3-final-{source,packaged}-{node,python}.log` and results JSONs.

RED before fixes is preserved for missing canonical routing/prefill, single-job
metadata, static unknown-JS disclosure and the real cross-tab hydration-window
old-account redisplay race. Final8 integration tests,17 detail tests and1 empty-
work clarification pass within the full156; they are not added twice to totals.
Earlier card tests now select by identity after day sorting and explicitly clear
optional cache to retain delayed-network cancellation coverage. No security or
recovery checks were dropped. See A3-HANDOFF.md for exact scope and test history.

Actual route screenshots at1280px and390px are labeled OFFLINE FIXTURE; footage
is the decoded synthetic test MP4, not a model render or stock image. No baseline
A1/A2 evidence changed. Self-review covered DOM escaping, gateway id validation,
known/unknown amounts, old-account async lifecycle, one-shot prefill, safe paid
identity preservation, optional cache failure and explicit static publication.

Limits: no live gateway params verification or deployment; no reconstructed
missing prompts/inputs/receipts; gateway-only status refresh is explicit rather
than fabricated local polling ownership. Part B nonvideo engine conversion and
run capture are NEXT, not bundled or claimed. Parent must verify the final push
and artifact and notify both Shuenrui and Sofa; worker made no Slack API call.
