# A2 final handoff — durable video recovery + small My work finish

Local branch: `ux-v1-a2-build`. Final slice starts at independently reviewed
checkpoint 2 `f6106f059d9f0749aaf1e078159d6f38ee4fc77f`.
Approved A1 base: `62d252287f9ff0dda2289458bc7e562c59af1839`.
Frozen engine/prompt/manifest comparison base:
`d95c15323d435f19d2ff634d92484c4b9503b3f5`.

**Local artifact and commit only. No push, deploy, real key lookup, live list,
paid inference or new live render. Parent owns independent review and publication.**

## Artifact

- `dist/shell-ux-v1-a2.zip`
- `dist/shell-ux-v1-a2.zip.sha256`
- SHA256: `4d43c5fc72c2071dc79a7aa5bddbd1b3cc2bc635fee8d83e1e56df57d7874c04`
- 44 runtime files, 21 frozen files checked byte-for-byte. No tests, reports,
  credentials, repository metadata or handoff documents in the production ZIP.
- `tests/package_a2.py` builds deterministically, checks a second rebuild, compares
  every extracted file to source, and exercises 96 extracted-server GET/HEAD
  checks, including **all** JS modules and prompt/manifest assets. IDB, watcher,
  poster and My work imports are publicly allowlisted; Python source, tests,
  reports and directory listings are denied.

## A2 delivered scope

Checkpoint 1 and 2 implementation/review history remains documented in
`A2-CHECKPOINT-1.md`, `A2-CHECKPOINT-2.md`, and `reports/a2/C2-REVIEW-FIXES.md`.
This artifact includes their account-scoped durable store/migration, save-before-
network adapter, planner/retry recovery corrections, app-owned multi-tab video
watcher, ready notices and existing `#/work?video=<jobId>` Open path.

The final small slice changes only `js/views/work.js`, new
`js/poster-cache.js`, and two scoped CSS rules in production:

- Cards lead with the first nonblank prompt line, trimmed and limited to 120
  characters including an ellipsis. Missing prompts use `Video from <date>` when
  a valid date exists, otherwise `Video`. Job ids no longer serve as card titles.
  Text uses DOM `textContent`, not HTML interpolation; known local prompts still
  win the local/gateway merge, and malformed optional metadata remains defended.
- Plain status labels: **Rendering / Ready / Failed**. Unknown nonterminal gateway
  states remain unresolved/Rendering rather than inventing successful completion.
- A completed video's poster is captured only after My work Open (including the
  ready-notice route) fetches that one video's authenticated media. No grid
  prefetch, gateway thumbnail URL, invented poster or MP4 cache was added.
- Capture waits for both a compositor frame and loaded data. The frame callback
  is registered before assigning `src`; both event orders are supported. Actual
  fixture-pixel assertions catch an unpainted black canvas, not just a JPEG URL.
- Posters use `singular-posters.v1` IndexedDB, scoped by the existing SHA256
  account id + validated job id. No key, authorization header or media URL is
  persisted. Only bounded JPEG data URLs are accepted: 128 KiB per encoded image,
  2 MiB encoded-image payload across the database, at most 64 rows, oldest first
  eviction across accounts. Row metadata is additionally bounded by those limits.
- Account changes/removal immediately remove cards/posters/player, abort work,
  cancel pending frame callbacks and revoke the video Blob URL. Persisted posters
  are retained for their own account, never shown for a replacement account.
- Canvas SecurityError, decode failure or optional cache failure does not replace
  the normal video/download with an error. Browsers without video-frame callbacks
  keep playback/download but do not create a new poster. Existing cached posters
  can still be displayed. This is a best-effort preview, not durable media storage.

The frozen `js/video.js` still hashes to
`71986db49b64763229a90e4d4fe10ae78ebfc45b27070f6d32e675e21a31450b`.
Quote/body/idempotency algorithms, FIELDS, prompts and manifests are unchanged.
`js/run-store.js` and `js/video-runtime.js` are unchanged from the reviewed
checkpoint-2 starting commit in this final slice.

## Offline harness correction

`tests/offline_browser.py` wraps each proxy-backed browser fixture with a
server-side forwarding deny guard, in addition to existing browser external-
route blocking. A request escaping browser interception receives a fixed local
503; no upstream opener runs and no auth/body/query data is logged. Unexpected
forwarding attempts are asserted empty after shutdown. Intentional guard testing
checks the recorded method/path then clears that one expected probe.

Teardown leaves each origin for `about:blank` with interception still installed,
then closes Chromium and the server. This prevents the former browser-route
removal race from reaching a live upstream and avoids disconnected-write noise.
The guard stays active throughout teardown. Existing static/proxy tests use only
static handlers or explicit loopback upstream servers.

## Verified results

Both the isolated source runtime **and** a separately relocated copy of the
extracted production ZIP pass the complete suites:

- **98/98 Node**, zero failures/cancelled/skipped.
- **95/95 Python**, zero failures/errors/skips: includes **19 durable-video**,
  **13 run-store**, **7 final-card/poster/harness** Chromium tests, one new
  static-disconnect harness unit test, plus all prior video/UI/proxy cases. Browser
  cases use real `/usr/bin/chromium`, real IndexedDB and Web Locks, with explicit
  offline gateway/model fixtures.
- Frozen-byte checks, deterministic ZIP rebuild and all source/archive bytes
  equal; 96 extracted static checks pass, zero unexpected upstream attempts.
- Raw poster-IDB scan excludes both fixture account keys; prior run-store and
  adapter credential defenses remain covered. Screenshot evidence demonstrates
  a decoded blue-frame poster, escaped title, Ready status and no mobile overflow.

Reproduce from this repository:

```sh
python3 tests/package_a2.py
python3 tests/verify_a2.py --label c3-source
python3 tests/verify_a2.py --runtime reports/a2/c3-package-check --label c3-packaged
```

Evidence: `reports/a2/c3-{source,packaged}-{node,python}.log`,
`c3-package-verification.json`, `c3-package-build.log`,
`c3-opened-poster-mobile.png`, and `C3-EVIDENCE.md`.
The isolated test trees are ignored and not included in the ZIP. Earlier baseline
screenshots/reports are not changed. Initial failed runs and RED tests are retained
separately and are not claimed as final passes.

## Explicit limits / A3 boundary

- This is final **A2**, not all of Part A or the complete pinned UX specification.
  A3 still owns Create/menu changes, page conversion of video/all other flow
  modals, full `#/work/<runId>` detail, grouped/filterable mixed-run history,
  non-video run-store UI, and the full bounded MP4/blob-cache specification.
- Existing flows still use their approved modal UI. My work Open uses the
  existing query route, not a claim that full run detail is delivered.
- No new live `/v1/videos` list call was authorized/performed. Gateway `params`
  shape is only fixture-tested; absent gateway prompts use the human fallback.
- Legacy recovery references remain intact while the frozen engine still writes
  them. Unscoped legacy data is not attributed to the current key. Missing planner
  metadata cannot be reconstructed, and abandoned text calls are not auto-retried.
- Browser account hashing is isolation, not encryption or a defense against
  arbitrary same-origin scripts/devtools. Clearing browser data removes local
  history/posters. Server ownership still governs gateway access.
- The three baseline-only literal key-prefix marker files are explicitly recorded
  in package verification (`js/views/chat.js`, `settings.js`, `skills.js`), and are
  byte-identical to the pinned base. They are labels/placeholders, not secrets;
  this is **not** a zero-prefix-marker claim. No broader legacy copy redesign
  was performed to hide those known baseline hits.
- For local artifact inspection: extract ZIP, run `python3 proxy.py 8730`, open
  loopback. Do not point tests at live inference. Deployment/rollback and live
  byte verification remain the parent's/reviewer's separately approved action.
