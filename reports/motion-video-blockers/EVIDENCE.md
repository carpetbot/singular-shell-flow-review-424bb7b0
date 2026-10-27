# Motion Trimmer → Video: four independent-review blockers

Status: fixed locally; **independent parent/reviewer verification still pending**. No publication, commit, paid call, deployment, push, or credential discovery. `FIELDS` is still exactly `{duration:null,aspectRatio:null,audio:null}`; production video creation remains disabled pending June's documented field confirmation and separate live-test authorization.

## Vertical TDD evidence

Each initial blocker was reproduced before its production fix, in sequence rather than a horizontal test pile:

| Blocker | RED | GREEN | Reproduced failure / behavior verified |
|---|---|---|---|
| Bounded/safe video HTTP errors | `01-errors-red.txt` | `01-errors-green.txt` | Unbounded `read(-1)`; now upstream error bodies are closed without reading (zero bytes, under 64 KiB), with a small fixed safe error response. |
| Cross-tab creation and stale history | `02-tabs-red.txt` | `02-tabs-green.txt` | Two independent POSTs, edited uncertain retry accepted, missing lock accepted; now exclusive Web Locks + locked storage refresh/merge, identical retries reuse saved token/body, unsafe lock absence fails closed. |
| All-history pending guard | `03-history-red.txt` | `03-history-green.txt` | Old completed selection bypassed pending history; now queued/processing/creating/uncertain same-account records all guard create/newVersion. |
| Detectable unknown-length overflow | `04-overflow-red.txt` | `04-overflow-green.txt` | Python saw normal EOF and Chromium accepted a successful 100 MiB prefix; now missing chunk terminator makes readers reject overflow. |

Additional acceptance steering was also handled vertically:
- `05-derived-token-{red,green}.txt`: token is SHA-256 of canonical `{planId,model,prompt,duration,resolution}`. Shared plan/version identity is persisted with the creating record before POST under the origin lock, not independently per tab. Explicit same-prompt regeneration after terminal completion gets a new identity/token; retries retain old token/body, including existing recovery records.
- `06-ui-guard-{red,green}.txt`: selecting a completed historical record cannot enable New/Generate with pending history.
- `07-live-tabs-{red,green}.txt`: two real Chromium documents approve Generate on the same scheduled instant; exactly one offline gateway POST/job is created. Storage events refresh the non-polling tab through terminal completion. This is separate from the deterministic Node lock fixture.
- `08-safe-message-{red,green}.txt`: fixed safe proxy `error_message`, never upstream diagnostic body/header reflection.
- `09-incomplete-{red,green}.txt`: Content-Length under/over mismatch and broken readers yield exactly `Download incomplete, retry download`, with no Blob.
- `10-retry-only-{red,green}.txt`: incomplete download offers download retry, disables generation actions, and successful retry does not POST another job.

Real loopback Chromium exercises the actual proxy, not intercepted media, with a 100 MiB + 64 KiB upstream response. It receives a first chunk before upstream release, then fetch rejects overflow within the bound. `VideoSession.download()` rejects both that overflow and a short declared-length transfer, creates zero Blobs, and returns the exact retry message. A successful unknown-length stream exactly at a reduced test bound completes normally. Proxy buffers at most a 64 KiB read chunk plus the one-byte overflow probe, never the whole video. No media redirects are followed.

## Full regression and legacy preservation

Worktree:
- `node --test tests/*.test.mjs`: **78 passed, 0 failed** (`node-full-final.txt`).
- `python3 -m unittest discover -s tests -p 'test_*.py' -v`: **42 passed** (`python-full-final.txt`).
- `legacy_compare.py` captured the actual three legacy flow payloads against base `378d6f4`: cold-email 4, Motion Trimmer 1, Model Jury 5 POST bodies byte-equivalent as objects; all **29 protected files byte-identical** (`legacy-compare.txt`, `protected-hashes.json`, `legacy-{base,current}-bodies.offline.json`). Replies are explicit offline fixtures, not live inference results.

Final ZIP extraction:
- Full Node suite: **78 passed, 0 failed** (`packaged-node.txt`).
- Full Python/browser suite: **42 passed** (`packaged-python.txt`).
- `verify_extracted.py` ran both suites against a fresh extraction plus external test fixtures, not the working-tree runtime. Source/ZIP/extracted runtime bytes were compared again after tests (`extracted-verification.json`). Test-only files were never added to the ZIP.

Encountered/resolved test harness issues: the first full run exposed a pre-existing 100 ms fixed timing assumption in close-during-submit; changed it to wait for the held request with a bounded deadline, preserving the assertion. The first extracted-suite run failed only because the screenshot manifest calls `relative_to(ROOT)` while evidence was configured in a sibling directory; final isolated evidence is beneath the extracted test ROOT, and the entire extracted suite was rerun successfully. Initial failed logs remain available, not disguised as green runs.

## Rebuilt artifact

The final review package was rebuilt once after production changes and documentation were complete:
- `dist/motion-trimmer-video-review.zip`
- SHA-256: `1eaba32de967fb23be17b806dc8802f015a58a773598dba8692f7596ccab53ad`
- **40 regular files**. CRC PASS; exact source/copy/ZIP/extraction byte equality PASS.
- Explicit runtime/handoff allowlist only: no private design docs, tests, reports, pricing snapshots, keys, caches or test fixture media.
- Packaged GET/HEAD root/static success and private/source/traversal/listing denial checks PASS (`package-verification.json`).
- Prior ZIP is superseded and must not be published. New ZIP remains local and independently unreviewed.

Changed production files in this follow-up: `js/video.js`, `js/video-ui.js`, `proxy.py`; handoff: `MOTION_VIDEO_REVIEW.md`. Tests: `tests/video.test.mjs`, new `tests/video-cross-tab.test.mjs`, `tests/test_video_proxy.py`, `tests/test_video_browser.py`. Build/check scripts and all follow-up logs are isolated under this directory. Pre-existing unrelated worktree modifications were left alone.
