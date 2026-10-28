# A3 checkpoint 1 — completion notices and live My work

Base: deployed/reviewed A2 `7efe1eddb28fd30d2bd93229103917102985be16`.
Branch: `ux-v1-a3-build`. Pinned brief: spec commit
`940e8c764922fb10e15e2fdc3383fffc0313eb3f`.

Only the two deferred A2 follow-ups are included. No navigation/Create/flow-page
redesign, new run-detail route, package, push, deployment, key retrieval or live
inference. Parent owns independent review/publication before checkpoint 2.

## Findings and RED reproduction

- **Missing ready notice is not an intended exclusion of migrated jobs.** The
  ordinary migrated processing job completed by this tab's successful HTTP
  `resume()` already eventually showed a toast on the base. An initial 500 ms
  assertion was too early; that timing probe is not claimed as the bug reproduction.
  The durable defect is that readiness depended on `resume()` returning normally.
  `watch()` also imports terminal progress from the retained legacy writer, then
  queries only `pending()`. A job made `done` by that import disappears from the
  pending set, without any readiness event if this tab's own HTTP observer errors
  or does not finish. The deterministic offline RED test keeps the local poll
  failing, finishes the legacy reference, and observes actual IDB `done` while the
  `#toasts` MutationObserver sees no ready notice. See `notice-red.log`.
- **My work listened only to same-document adapter-save events.** The watcher
  did not emit after a migration import or when a nonowner tab rediscovered a
  terminal record. Both same-tab legacy-import and cross-tab nonowner cards
  stayed Rendering. `work-red.log` contains both real-Chromium failures awaiting
  Ready, not failures of a mock store or manual Refresh.

## Implementation and semantics

- Runtime baselines current account rows after initial migration. Already-terminal
  startup/reload history does not generate notices. Previously observed rendering
  rows changing to done do generate a notice, including legacy-imported completion.
  Immediate successful create and successful HTTP resume keep their notice path.
- All paths use `claimVideoReady(jobId)`: one strict read/write transaction over
  existing `runs` + `meta`, confirming account-scoped committed `done` and claiming
  `video-ready:<account hash>:<job id>`. Competing handles/tabs and repeated scans
  cannot deliver duplicate notices. Marker contains no credential. It persists
  across reload/reconnect. The same job id in a different account is independent.
- **Cross-tab policy:** one origin/account/job notice, not one per tab. Polling
  remains owned by the existing per-job Web Lock. The first valid observer to
  commit the notification claim wins; it need not be the polling owner. Other
  tabs still update their cards. Open uses existing authenticated
  `#/work?video=<jobId>` playback and is epoch-guarded. Account invalidation removes
  old notices and cancels old work. No historical startup backfill/spam.
- This is exactly-once delivery during ordinary active-tab execution, with durable
  duplicate suppression. As with any DOM notification, a crash/account switch
  between claim commit and presentation can suppress presentation; the durable
  completed job remains in My work. This is not an OS/background notification or
  an impossible atomic transaction across IndexedDB and the browser DOM.
- Every active account runtime compares committed IDB snapshots, including
  terminals, and emits account-scoped `singular:runs` events when they change.
  Adapter saves emit immediately as before; legacy-import/nonowner discovery uses
  the existing five-second scan (background browser throttling can delay it).
  This adds no gateway polling owner, list refresh, or grid media request.
- Mounted My work accepts only its account's events, merges fresh local rows and
  rejects superseded asynchronous reads/account epochs. It does not reset the
  selected player, Blob URL or poster map. Existing terminal-monotone merge and
  known-prompt precedence remain intact. Route destroy removes its listener;
  account replacement/removal retains synchronous media/card cleanup.

## Verification

`tests/test_a3_followups_browser.py` runs real `/usr/bin/chromium`, real
IndexedDB/Web Locks, loopback-only explicit gateway fixtures. It reuses the
existing `offline_server` deny guard through browser and server teardown. No
upstream forwarding, real key, or paid inference is used. Coverage includes:

- migrated HTTP completion, MutationObserver ready notice and working Open;
- legacy-writer completion imported by watcher despite failing local polls;
- same-tab live Ready + saved local prompt, with no grid media downloads;
- nonowner live Ready without acquiring polling ownership; one notice across tabs;
- preserved selected player identity, Blob URL, poster, merged gateway prompt and
  media-request count after updates; stale legacy processing cannot reverse Ready;
- transactional premature/duplicate/other-account/reopened notification claims;
- queued account-old reads, foreign events, route listener cleanup and Open return;
- reload terminal history does not create a new ready notice.

Reproduce focused: `python3 -m unittest discover -s tests -p test_a3_followups_browser.py -v`.
Reproduce complete suites without changing baseline evidence:
`python3 tests/verify_a3.py` (copy under ignored `reports/a3/regression-app/`).
Results:

- **98/98 Node**, no failures/cancellations/skips (`full-node.log`).
- **104/104 Python**, no failures/errors/skips (`full-python.log`), using the final
  production runtime in the isolated full-suite copy.
- **9/9 final strengthened focused browser tests** (`focused-final.log`), including
  a second document running the actual frozen `VideoSession.resume()` as the
  legacy writer, rather than only editing a fixture reference.
- The updated either-tab notice-winner assertion in the retained single-poll-owner
  test also passes independently (`cross-tab-contract-green.log`). These last
  test-only strengthenings were run separately after the full-suite copy was made;
  no production code changed after that copy.
- Re-running the three final regressions against an isolated deployed-base runtime
  gives the expected **3/3 RED failures** (`final-fixture-base-red.log`): missing
  MutationObserver notice, stale same-tab card and stale nonowner card. Original
  vertical RED/GREEN logs remain alongside it. A diagnostic 500 ms notice probe
  and an interpreter missing Playwright are not counted as accepted RED evidence.
- All **21 frozen files** match base, zero protected mismatches, no production
  secret/debug/eval/shell scan hits, clean `git diff --check`
  (`protected-static-scan.json`). No baseline evidence or dist files changed.

The first complete pre-refactor pass was also clean (98 Node / 103 Python) and is
retained as `pre-refactor-*`; it is not substituted for the final counts above.

## Preserved boundaries

Production edits: only `js/video-runtime.js`, `js/run-store.js` (additive claim
method only), and `js/views/work.js`. No existing persistence reconciliation,
origin locks, planner evidence binding, paid POST ordering or pending guards were
changed. `js/video.js`, quote/FIELDS/idempotency algorithms, prompts and manifests
remain byte-identical to base. Frozen engine SHA256:
`71986db49b64763229a90e4d4fe10ae78ebfc45b27070f6d32e675e21a31450b`.
