# A2 checkpoint 2 — durable video adapter + app-owned observer

Base: checkpoint 1 `aa171a4248fd1c30f00930de6d3f1151720cae15`.
Local branch: `ux-v1-a2-build`. This is a working checkpoint, **not a final Part A
package**. No push, deploy, credentials, live inference, or new live render.

## Implemented

- `js/video-runtime.js` opens the account-scoped IndexedDB handle and migrates
  legacy references before enabling the video UI. Initialization/migration failures
  are visible and block generation; unscoped references produce a recovery notice.
  Originals remain in localStorage and migration repeats under its existing lock.
- A `VideoSession` subclass wraps its awaited `save` boundary. The frozen engine
  still owns canonical bodies, quote refresh/approval, token/version creation,
  origin creation locks, status validation, rejection handling, and media checks.
  Its legacy save is followed by an awaited strict IDB commit **before paid POST**.
  A failure can leave a legacy pending reference, but cannot fall back to a paid
  request. Public pricing refresh remains in the engine's original order.
- Planner inputs/running state commit before chat. Final plan/prompt and attempt
  receipts commit before being displayed. Render records retain inputs, edited
  canonical prompt, plan and planner receipts. Reopening after reload restores
  the available local plan, prompt and receipts; a fresh quote remains required.
- Pending guards consult both stores. Uncertain no-id references are never
  automatically submitted or polled. Durable pending records block a new logical
  render even after legacy references are removed. Explicit identical retries
  continue through the unchanged engine and reuse its saved token.
- Boot starts one app-owned observer, independent of the modal/route. A per-account,
  per-job Web Lock gives one polling owner across tabs, with takeover after reload
  or owner disappearance. It uses the frozen `resume` validation path with injected
  sleep: 5 seconds increasing to 30 seconds; request failures back off to 60 seconds.
  Observation stops at 24 hours, preserving an unresolved record rather than
  inventing a failed settlement. Undated legacy jobs receive an explicitly named
  observation-start timestamp, not a fabricated historical creation time.
- Terminal state and receipts go through run-store's transactional monotone merges.
  A successful observer emits “Your video is ready” with Open; immediate completed
  create responses also announce readiness. My work has a rendering dot and merges
  durable video references with gateway rows by job id without regressing terminal
  truth or dropping a known local prompt.
- Open uses the existing My work screen with `#/work?video=<jobId>` and authenticated
  media fetch. No A3 menu or flow-page conversion was introduced.
- Account replacement/removal invalidates the runtime synchronously, aborts
  polling/media, closes/discards the old IDB handle, removes notices, and closes the
  old-account video view through its real modal cleanup. Late completions cannot
  display old-account output. Other-account legacy references remain intact.

## Verification

All gateway responses are explicit offline fixtures; real `/usr/bin/chromium`,
real IndexedDB transactions and real browser Web Locks are used, not fake IDB.

Final commands (runtime/tests/catalog copied into ignored
`reports/a2/c2-regression-app/`, keeping baseline reports untouched):

```sh
node --test tests/*.test.mjs
python3 -m unittest discover -s tests -p 'test_*.py' -v
```

Final results: **98/98 Node**, **76/76 Python**, zero failures/skips. Python includes
**10 new durable-video integration tests**, **11 run-store browser tests**, and
all 15 retained video browser tests.

New coverage: plan commit before chat; render identity/prompt commit before POST;
route departure followed by durable completion + ready notice + working Open;
reload resume with no POST; single cross-tab observer; account isolation/epoch
cleanup; uncertain no-id reload without resubmission and IDB-only pending guard;
real transaction-abort refusal before paid chat/render; immediate completed create;
24-hour stop; gateway/local merge; reload restoration of plan/prompt/receipts.

Evidence:
- `c2-{01,02,03,04}-{red,green}.log`: vertical integration/bug slices.
- `c2-dot-{red,green}.log`, `c2-merge-{red,green}.log`,
  `c2-restore-{red,green}.log`: focused UI/merge/restoration evidence.
- `c2-node-final.log`, `c2-python-final.log`: final complete suites.
- `c2-protected-and-idb-scan.log`: protected-source comparison and raw real-IDB
  credential scan after actual fixture plan/render completion.

`js/video.js`, run-store, every prompt and manifest remain byte-identical to
checkpoint 1. Frozen engine SHA256:
`71986db49b64763229a90e4d4fe10ae78ebfc45b27070f6d32e675e21a31450b`.

## Test-harness issues resolved

- Previous modal-owned cancellation assertions were intentionally updated to the
  approved app-owned continuation contract. Poll waits now allow the specified
  five-second/backoff interval instead of assuming the old one-second loop.
- Cross-tab fixtures now save their fake key through the real settings API; direct
  in-memory mutation incorrectly looked like a disconnect when another tab saved
  default settings. Same-key settings changes do not invalidate the runtime.
- Legacy pending-guard fixtures now keep their gateway status queued; otherwise
  the new automatic observer can legitimately complete them before the assertion.
  The observed full-suite fixture race is retained in `c2-python-fixture-race.log`.
- The restoration test now actually reloads before reopening (clicking an inert
  gallery under an open modal is not a reopen). Its corrected RED was reproduced
  against the earlier checkpoint UI in the isolated tree, then GREEN against the
  implementation. Browser clocks are installed before app timers for the timeout
  test. Initial full-suite failures are retained, not presented as final passes.

## Remaining authorized small A2 checkpoint 3 / later parts

No card/title/poster polish, full run-detail route, bounded media cache, final
package, or A3 navigation/flow-page work is claimed here. My work retains A1's
simple list presentation; local planning-only records are durable and restored in
video UI, while its list merge currently displays video request references.
Part B text-run capture is untouched. Parent performs independent review and any
push; do not deploy or package this checkpoint as completed Part A.
