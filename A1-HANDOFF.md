# A1 video recovery — local review handoff

## Delivered scope

Base: `d95c15323d435f19d2ff634d92484c4b9503b3f5`; branch: `ux-v1-part-a`.

- Visible **My work** links in the existing desktop/mobile navigation; reloadable `#/work` route.
- Authenticated gateway job list, explicit pagination, refresh, empty/error/retry states, model/date/prompt fallback. Dynamic gateway text is inserted using `textContent`.
- User-triggered playback via Authorization → bounded fetch → Blob URL; MP4 download reuses that Blob. No grid prefetch. One selected media object at a time, 100 MiB cap, 120-second media deadline and 30-second list deadline.
- Account changes/disconnect clear displayed jobs and media, abort pending requests, revoke object URLs and ignore stale completions. Route exit clears selected media. Existing settings are the only credential store; no new job/media persistence.
- Proxy allows GET list queries containing only unique `limit` (integer 1–100) and `cursor` (documented character/length bounds). Unknown/duplicate/invalid fields and every POST query are rejected before forwarding.

No A2/A3 changes: no IndexedDB, watcher, create/menu redesign or flow-page conversion. All existing modal flows remain. All `skills/` runtime files and `js/video.js` are byte-identical to base; quote logic, model picks, prompts, manifests and `FIELDS` remain unchanged. Proxy changes are limited to list-query validation.

## Verified execution

| Check | Result |
| --- | --- |
| `node --test tests/*.test.mjs` | **98 passed**, 0 failed |
| `python3 -m unittest discover -s tests -p 'test_*.py' -v` | **55 passed**, 0 failed |
| Packaged A1 proxy/browser acceptance (`test_work*.py`) | **10 passed**, 0 failed |
| Packaged existing video proxy suite | **8 passed**, 0 failed |
| Packaged static GET/HEAD allow/deny checks | **14 passed** |
| ZIP integrity, runtime file set and source equality | **41 runtime files**, all byte-equal |
| Frozen runtime files compared with base | **21 byte-equal files** |

A1 tests cover fake authenticated list + media, pagination without media prefetch, actual Chromium playback and byte-equal MP4 download, empty/auth error/retry, stale list/media responses, account switch/removal (including route re-entry after a missed cross-tab change), Blob revocation and 390px layout without horizontal overflow. All browser network traffic outside loopback is blocked. Fixtures are synthetic; screenshots are not model output.

The existing store's `hydrate` has a backward-compatible optional `clearMissingKey` flag, used only by recovery. Legacy callers retain their default behavior. Recovery rehydrates existing settings before listing and clears removed keys instead of retaining stale in-memory credentials.

Review blocker regression: optional model/status/prompt metadata is normalized to primitive strings with existing fallbacks; dates accept only strings or finite numeric seconds (including epoch zero), with invalid dates omitted. Chromium first reproduced the review payload (`model: {toString: null, valueOf: null}`): zero cards despite a loaded status. The new metadata test failed before the fix and now renders all five mixed-metadata fixtures without page errors. A second browser test injected a one-shot card-render exception and initially timed out waiting for a recoverable error. Rendering now occurs inside the load error boundary, cards are committed atomically, and control recovery runs in `finally` without rendering. The test verifies the honest retry status, enabled refresh, no uncaught errors, and a successful subsequent refresh. RED logs: `metadata-red.log`, `render-failure-red.log`; GREEN: `metadata-green.log`, `work-browser-final.log` (8 browser tests), plus full and extracted-package suites.

TDD observations: list pagination initially returned 404; the browser initially could not find My work navigation. Cross-tab immediate-clear and settings-removal tests subsequently failed before their fixes; malformed list identity and missing deadline tests also failed before fixes. Final suites are green. The first full Python run failed only because the legacy exact navigation assertion omitted the newly required link. Both exact Lite/Pro expectations were updated to require My work; no assertions or tests were removed or relaxed.

## Artifact

- `dist/shell-ux-v1-a1.zip`
- `dist/shell-ux-v1-a1.zip.sha256`
- SHA256: `a13cc007f383eb49741f517ac2b8f010ad81a36876d1ddcdbb24848b335a2404`
- Production runtime only: no tests, fixtures, reports, docs or repository metadata.
- Rebuild/check: `python3 tests/package_a1.py`.
- Extracted verification copy: sibling `a1-package-check/`.
- Local startup after extraction: `python3 proxy.py 8730`; open `http://127.0.0.1:8730/#/work` and connect a key in existing Settings.
- Packaged acceptance: `VIDEO_APP_ROOT=/absolute/path/to/extracted python3 -m unittest discover -s tests -p 'test_work*.py' -v`.

Evidence: `reports/a1/` (suite logs, package-verification JSON, offline 390px screenshot).

## Caveats / parent review

- No live inference, render, deployment, push or live authenticated list request was performed. The production `GET /v1/videos` item/`params.prompt` shape remains **unverified**. The UI accepts the pinned documented envelope and uses a fallback if a prompt is absent.
- The baseline has literal key-prefix labels/placeholders in three unchanged legacy views. The package scan records these baseline-only marker hits; they are not credentials. No real credential was used or written to logs/artifacts. The broader A2/A3 zero-prefix-copy criterion is not claimed by A1.
- No remaining test failures in final execution. Independent parent review is still required before any publication or deployment.
