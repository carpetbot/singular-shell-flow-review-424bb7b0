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

Original checkpoint results: **98/98 Node**, **76/76 Python**, zero failures/skips. Python includes
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

At the original checkpoint, `js/video.js`, run-store, every prompt and manifest were
byte-identical to checkpoint 1. The review correction below explicitly evolves
run-store's migration metadata; `js/video.js`, prompts and manifests remain unchanged.
Frozen engine SHA256:
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

## Checkpoint 2 review correction — only the two blockers

Against base `74634a698bf64b60fe0546d8a456ae5118328a37`:

- **Interrupted planner:** new planner rows use a separate `-plan` flow and hold a
  per-plan browser Web Lock. Reload releases ownership; account invalidation
  releases ownership and finalizes the old account's record before closing its
  store. Orphans, including old checkpoint planner-only rows, become `failed` with
  `outputs.planner_state: abandoned` and an explicit interruption explanation.
  Account initialization surfaces the retained abandonment notice. Another tab's
  live planner is not abandoned. Render guards still block creating/uncertain
  submissions, including tokenless rendering rows; no tokenless-render exemption
  was added to the store or runtime.
- **IDB abort then identical retry:** the edited prompt/canonical request is first
  saved with the durable planner snapshot. The engine's subsequent exact token,
  version and body hash bind that snapshot before the render-row insert. The
  original legacy-save ordering and engine token/body algorithms are unchanged.
  Migration-created placeholders now carry an internal `recovery_metadata_missing`
  marker. A dedicated one-time enrichment transaction verifies the exact body hash,
  token, plan id and quote, commits the brief/plan/prompt/request/planner receipts,
  then closes the metadata hole before POST. Ordinary create/update identity rules
  are unchanged. Deterministic, untouched pre-marker import placeholders can be
  upgraded; normal durable rows cannot opt in. Reload restoration selects the
  token/version-bound snapshot, not an unrelated plan with the same body. A rejected
  nonidentical retry cannot overwrite the durable recovery draft.

Both review blockers were reproduced in failing real-Chromium regressions **before**
the corresponding fix. Additional vertical RED/GREEN slices cover reload restoration,
conflicting retries, same-body/different-brief recovery, pre-marker placeholders and
abandonment visibility after account replacement. Evidence and commands are indexed
in `reports/a2/C2-REVIEW-FIXES.md`.

Final correction results: **98/98 Node**, **85/85 Python**, zero failures/skips.
Python now includes **17 durable-video integration tests**, **13 run-store browser
tests**, and all retained browser/proxy/UI cases. No key or paid inference was used;
all gateway/model responses were offline fixtures. The full Python suite ran in an
ignored repository-local copy, avoiding changes to earlier evidence. The first full
run's new cross-tab fixture waited on the static `#view` shell before hydration;
waiting for the actual settings input fixed the harness, not production boot logic.
Its failure log is retained separately from the final passing suite.

Limits: this does not reconstruct planner metadata absent from both durable snapshots
and legacy references, does not retry abandoned text calls automatically, and does
not claim live billing/inference validation. No card polish, A3, packaging, push or
deploy was performed.

## Final narrow same-session identity correction

The same-document add-abort → changed brief / same planner prompt → retry path
was still able to attach a newly planned brief to the old submission identity.
Only initial engine insertion now binds a planner snapshot; retries independently
resolve and hash-check the original token/version/body-bound durable evidence.
The UI locks replanning until explicit terminal Make another version, guards the
handler, and explains that closing is not cancellation. The runtime-only bypass
regression proves safety does not depend on the UI lock.

Both new Chromium cases reproduced RED before the fix. Final suites: **98/98 Node**,
**87/87 Python**, zero failures/skips, including **19 durable-video** and **13
run-store** cases. Engine, run-store, prompts and manifests are unchanged against
`a3b2ca6078311d2fec776f07a0a060e3f95b57d6`. Commands and retained RED/GREEN evidence:
`reports/a2/C2-NARROW-IDENTITY-FIX.md`. No live inference, packaging, push or deploy.

## Remaining authorized small A2 checkpoint 3 / later parts

No card/title/poster polish, full run-detail route, bounded media cache, final
package, or A3 navigation/flow-page work is claimed here. My work retains A1's
simple list presentation; local planning-only records are durable and restored in
video UI, while its list merge currently displays video request references.
Part B text-run capture is untouched. Parent performs independent review and any
push; do not deploy or package this checkpoint as completed Part A.
