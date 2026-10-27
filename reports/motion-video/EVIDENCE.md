# Motion Trimmer → Video · local evidence index

## Result
Offline implementation complete against base `378d6f4` and private spec `shuenrui/singular-flows@960213c` (v0.0.2 overrides v0.0.1). **Criteria 1–11 pass offline. Criterion 12 is explicitly NOT performed / release-blocked.** No deployment, external push, paid model call or authenticated discovery request occurred. Independent parent review remains pending. Source changes are left uncommitted on local branch `motion-trimmer-video` for that review.

Runtime ZIP: source-root `dist/motion-trimmer-video-review.zip` (relative to this index: `../../dist/motion-trimmer-video-review.zip`). SHA256:

`eddadf7dfa6343c891b1c7c7b7cf370c91963ba4bc5b480e3274338608afe83d`

40 runtime/readme regular files; 63,875 bytes. CRC and every source/copied-folder/ZIP byte verified, including a post-test read-only integrity check. The ZIP excludes private design, pricing fixtures, test Python, reports, caches and credentials. Required runtime `proxy.py` is included. Full usage/privacy/recovery/rollback guidance: source-root `MOTION_VIDEO_REVIEW.md` (also inside ZIP).

All model responses are explicitly **offline fake inference fixtures**. The MP4 is a locally generated H.264 320×180, 1.000-second synthetic navy rectangle fixture; it is deliberately NOT evidence of a 15-second Wan render, model quality, adapter duration mapping, output resolution or real settled billing.

## Acceptance criteria

| # | Status | Executed proof |
|---|---|---|
| 1 | PASS offline | `tests/test_video_browser.py::test_02_confirmed_offline_brief_player_download_retry`: actual new modal, one structured planner response, explicit price button, one create job, authenticated content, Blob player actual playback (`currentTime > 0.1`), Download MP4 with byte equality, reload recovery. `packaged-playback.txt`, `packaged/offline-player.png`, `packaged/offline-download.mp4`, `packaged/video-wire.offline.json`. |
| 2 | PASS offline | New additive gallery card; legacy Motion Trimmer remains separate planning-only. Default/unconfigured gallery plans and quotes but Generate stays disabled. Browser test 01 plus `legacy-compare.txt` actual unchanged planning-only request. No plan response automatically submits video. |
| 3 | PASS offline | Node exact catalog tests exercise both exact routable IDs at 5/10/15 seconds, fixed 720p/768p and all six recorded prices. Unsupported duration/model, missing/unknown/string price and changed quote refuse before POST. Browser test 03 verifies missing config disables Generate; typed JSON edits fail before POST. Unconfirmed duration map independently blocks POST. |
| 4 | PASS offline | Node submit test locks before await; concurrent clicks produce one POST. Network-lost response persists uncertain reference first. Reload + identical prompt/config retries the same token AND byte-identical body; changed body refuses. Browser tests 02/04 exercise double-click and response-loss/reload retry. New explicit terminal version gets a different token and preserves prior receipt. No automatic POST retry or regeneration. |
| 5 | PASS offline | Browser tests 02/04/05 reload or close/reopen and explicitly Resume an existing job using GET only, same creating key. Wrong-key hash blocks before request. Uncertain creation stores no prompt/key; user must re-enter identical request to retry the same saved idempotency token, not generate afresh. |
| 6 | PASS offline | Node and browser cover queued, processing, completed, failed, uncertain network, create 401/402 rejection, planner auth/credit, status HTTP errors and content errors separately. Failed job → known settled zero per documented failed-job contract; pending server zero → unknown, never free. Explicit recovery after definite auth/credit rejection. Browser 05/06 prove closing stops polling, including close while create response is outstanding. Node bounded abort signals/backoff/deadline; no fabricated percent progress. |
| 7 | PASS offline | Browser 02 first content GET returns 502, then Retry download only succeeds, retaining completed status and settled receipt. Exactly one create POST. No automatic paid regeneration. |
| 8 | PASS offline | Node rejects arbitrary result host, job path, query, fragment, protocol-relative URL and malformed ID. Authenticated fetch derives only safe `/v1/videos/{id}/content`, rejects redirects and uses creating key. Blob URLs contain no key; revoke verified on replacement/dispose; close observer and pagehide clean up. Recovery log has only references/hashes/token, not prompt/API key. Real proxy loopback rejects media redirects and invalid content paths; authorization never forwarded externally. |
| 9 | PASS offline | Node asserts pending `cost_usd:0` remains unknown, completed missing cost remains unknown, failed zero is known, and versions retain separate quotes/settlements. UI shows planner attempt usage estimates separately from video quoted/pending/settled receipts, including prior versions. `packaged/video-wire.offline.json` contains actual offline request bodies and visible receipts; Authorization values are not saved. |
| 10 | PASS offline | Eight real-Chromium video tests, all network route fixtures registered before navigation with non-loopback requests aborted. Synthetic media plays and downloads; retry/recovery/price refusal/errors tested. Screenshot has prominent OFFLINE FAKE INFERENCE banner. Mobile modal overflow checked. These are not real inference results. |
| 11 | PASS offline | `legacy-compare.txt` captures actual browser POST bodies against approved `378d6f4`: Cold Email 4, old Motion Trimmer 1, Model Jury 5, byte-identical (deterministic offline shuffle); `legacy-base-bodies.offline.json`, `legacy-current-bodies.offline.json`. `protected-hashes.json`: 29 protected engine/UI/manifest/prompt files unchanged. Full Node 72/72 and Python 35/35 pass. GET/HEAD source/traversal/query/encoded/symlink/directory denial tests pass. Real loopback upstream proves first media bytes arrive BEFORE upstream finishes, POST-only idempotency forwarding, unchanged legacy body, declared oversize 413, unknown-size cap, no redirect. Copied runtime server gets 24 GET/HEAD probes; runtime ZIP CRC/bytes exact. |
| 12 | BLOCKED / NOT PERFORMED | No authorized live capped-key render. All three undocumented field names remain `null` in one config map; ordinary builder emits ONLY model/prompt/resolution and ordinary Generate is disabled. `fixture_duration` exists only in injected offline tests, not production configuration. June must confirm actual duration forwarding; aspect/audio must remain unexposed until confirmed. Separately obtain user approval and capped key for one controlled 5s/480p Wan diagnostic; inspect actual adapter parameters, downloadable video, media duration/resolution and settled charge. Normal gallery remains fixed 720p/768p. Nothing in offline results substitutes for this gate. |

## Final verification outputs
- `node-final.txt`: source Node built-in runner, **72 tests passed**.
- `python-final.txt`: full source Python/Chromium/security suite, **35 tests passed**.
- `packaged-node.txt`: **72 tests passed** using isolated test harness importing copied runtime modules/manifests.
- `packaged-python.txt`: **13 tests passed** directly against copied runtime proxy (8 browser + 5 loopback media tests).
- `packaged-playback.txt`: latest actual playback and byte-identical download check against copied runtime, **1 passed**.
- `packaged-legacy-browser.txt`: copied runtime Model Jury browser suite, **10 passed**.
- `packaged-cold-email-browser.txt`: copied runtime Lite/Pro/Cold Email browser suite, **9 passed**.
- `package-verification.json`, `package-build.txt`: allowlist, CRC, every source/copy/ZIP byte and exact copied-server probes.
- `final-integrity.json`: post-test CRC/equivalence/no-extra-files, ZIP hash, runtime file SHA256s, spec fingerprint, catalog timestamp and static security scan with no matched literal credential/shell/eval/pickle patterns. Independent reviewer is still pending.
- `catalog-offline.json`: supplied public snapshot `as_of=2026-10-27T03:44:09.577Z`; never used as evidence of successful inference.

## TDD tracer bullets (raw plaintext retained)
01 exact quote/documented body/release gate → `01-red.txt`, `01-green.txt`.
02 structured planner/typed edits/5xx-only backup/receipts → `02-red.txt`, `02-green.txt`.
03 explicit submit/idempotency/uncertain reload → `03-red.txt`, `03-green.txt`.
04 resume → safe content/Blob download/retry/lifecycle → `04-red.txt`, `04-green.txt`.
05 bounded abortable polling / stop semantics → `05-red.txt`, `05-green.txt`.
06 gallery-to-player browser vertical slice, including native-fetch receiver correction → `06-browser-red.txt`, `06-browser-green.txt`.
07 narrow proxy media pipeline against real loopback upstream → `07-proxy-red.txt`, `07-proxy-green.txt`.
08 close-during-create race regression → `08-browser-red.txt`, `08-browser-green.txt`.
09 screenshot-discovered oversized download action regression → `09-layout-red.txt`, `09-layout-green.txt`.
10 definite auth/credit rejection recovery regression → `10-auth-red.txt`, `10-auth-green.txt`, `10-auth-browser-green.txt`.

Additional boundary checks were added against already-implemented behavior and passed; they are not mislabeled as new red/green cycles. Initial exploratory final-suite attempts exposed only isolated report-directory harness collisions; final paths are separated under `legacy-ui/`, `lite-ui/`, `jury-ui/`, and `packaged/`. No unrelated historical screenshot reports changed.

## Reproduction (from source worktree)
```
node --test tests/*.test.mjs
PYTHONDONTWRITEBYTECODE=1 VIDEO_LEGACY_EVIDENCE="$PWD/reports/motion-video/legacy-ui" VIDEO_LITE_EVIDENCE="$PWD/reports/motion-video/lite-ui" VIDEO_JURY_EVIDENCE="$PWD/reports/motion-video/jury-ui" python3 -m unittest discover -s tests -p 'test_*.py' -v
PYTHONDONTWRITEBYTECODE=1 python3 reports/motion-video/legacy_compare.py
PYTHONDONTWRITEBYTECODE=1 python3 reports/motion-video/build_verify_package.py
```
Legacy comparison uses the adjacent local `motion-trimmer-video-base-378d6f4` extracted from `git archive 378d6f4`. Chromium `/usr/bin/chromium`, Python Playwright, Node built-ins; no paid calls. Packaging rebuilds ZIP timestamps and therefore requires a new SHA review; read-only `final-integrity.json` is the final artifact evidence, not permission to publish.

Known limits: uncertain creation cannot be recovered if the exact prompt/configuration and creating key are lost; no plaintext prompt is saved. Do not clear references while pending. A full/unreadable recovery store fails closed, with manual support review required. Planner estimates are heuristic and receipts do not independently verify billing. Generated creative quality, actual adapter parameters and live charge remain unverified. Multi-tab cross-session coordination is not a promised feature. No live service was deployed or restarted.
