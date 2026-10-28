# A2 checkpoint 1 — durable run foundation

Base: approved A1 `62d252287f9ff0dda2289458bc7e562c59af1839`.
Scope: additive IndexedDB module and offline Chromium tests only. No watcher,
card redesign, video engine changes, paid requests, key retrieval, deployment,
or push. App startup and existing UI are deliberately unchanged: the next
checkpoint must wire the adapter and fail-closed startup together, not silently
fall back to legacy storage after an IndexedDB error.

## API (`js/run-store.js`)

```js
import {openRunStore} from './run-store.js';
const runs = await openRunStore({key: activeKey});
const migration = await runs.migrateLegacy();
const pending = await runs.pending();
// Before ANY network request for a new logical request:
const saved = await runs.create({
  flow_id: 'claw__motion-trimmer-video', title: 'A boat',
  inputs: {topic: 'Boat'}, prompt: 'A boat', model_ids: ['exact-model-id'],
  idempotency_key: existingVideoEngineToken, plan_id: existingVersionIdentity,
  body_hash: existingCanonicalBodyHash, status: 'rendering'
});
// Await this commit before submitting; retry the SAME logical request identity.
await runs.update(saved.id, {video_job_id: job.id, video_status: job.status});
const detail = await runs.get(saved.id); // null for another account
const history = await runs.list();      // current account only
runs.close();
```

- Database: `singular-runs.v1`, schema version 1, `runs` and `meta` stores.
  Account identifier is the SHA-256 of the trimmed key, matching `VideoSession`.
  Key is transient in the scoped handle, never in a persisted record. Reject
  credential field names, active key values, common key prefixes, bearer values,
  cycles, unsupported structured values and invalid costs/identity fields.
- `create`, `update`, `migrateLegacy` resolve only after the real read/write
  transaction commits (strict durability). Opening performs an actual write probe.
  Missing key, unavailable DB, quota/abort, conflict or unreadable legacy data
  fail explicitly. No memory/localStorage fallback and no network in this module.
- A non-null idempotency token deduplicates creation atomically across tabs.
  Reusing it with changed request fields is rejected. A different token is blocked
  while any same-account/same-flow record is unresolved. Keep the existing
  `js/video.js` canonical request, token, version and quote algorithms unchanged.
  This store does not authorize POSTs or schedule them; the adapter must still
  coordinate requests and await storage before network.
- Updates merge inside a read/write transaction, not from a caller's stale
  snapshot. Immutable recovery identities cannot be replaced. Terminal state,
  known settlements and append-only receipt evidence cannot be regressed by a
  delayed observer. Distinct partial fields survive concurrent tab writes.
- `pending()` includes **all** running/rendering records, including uncertain
  creations with no job id. Do not filter only on `video_job_id` or the selected
  history entry. Returned pending records are not a command to resubmit.
- This is browser-local scoping, not encryption or a security boundary against
  arbitrary same-origin scripts/devtools. Close/discard the handle and clear UI
  synchronously when the active key changes. Never reuse an old account handle.

## Legacy migration and compatibility

Inspected the actual A1 `VideoSession` constructor, refresh/save/create/resume,
clear/version code and the original video commit. The persisted value is a JSON
array, not a dictionary of jobs. Entries carry `token`, `keyHash`, `planId`,
`bodyHash`, `quote`, `settled`, `status`, `id`, optional `error`. They do not
normally contain prompt/inputs or creation timestamps; no fabricated values are
inferred for missing historical data.

- Migration takes the existing `motion-video.v1` Web Lock used by the frozen
  video engine, then imports the current account in one IDB transaction.
- It preserves the complete credential-free source entry as `legacy`, plus
  explicit token/version/body hash/quote/settlement/job/status fields. Unknown
  costs stay null; failed/rejected zero settlements stay zero. Completed maps to
  `done`; failed/rejected to `failed`; every unresolved/unknown state to
  `rendering`, retaining the exact `video_status`.
- Stable account+token ids prevent duplicate imports. Existing durable entries
  with the same token are reconciled rather than duplicated. Later legacy
  progress is imported, but stale legacy snapshots cannot undo terminal state.
  Conflicting identities abort the entire batch, leaving both stores intact.
- **Legacy localStorage is never deleted in this checkpoint**, even after a
  successful durable commit. Existing tabs and the frozen video engine still
  write it. Repeat migration after reload/account change and before the next
  adapter's creation guard. Deletion requires retiring/dual-writing old writers.
- Entries with no `keyHash` cannot safely be attributed to whichever key happens
  to be connected. They remain untouched in legacy storage and are reported by
  the `unscoped` count; no outputs/job references leak into another account.
  Surface a recovery notice in the next UI slice; do not silently claim they
  migrated or delete them. Gateway listing remains the account ownership source.

## Verification

Real headless `/usr/bin/chromium` via Playwright, origin-local HTTP only; external
traffic blocked. No in-memory IndexedDB replacement. Coverage includes reload,
account isolation, migration/version/unknown settlement preservation, uncertain
pending discovery, two-tab migration and updates, idempotent creation, conflicts,
malformed legacy data, real transaction abort with quota fault injection,
missing key/DB, structured input validation and raw IndexedDB credential scan.

Commands:

```sh
python3 -m unittest discover -s tests -p test_run_store_browser.py -v
node --test tests/*.test.mjs
python3 -m unittest discover -s tests -p 'test_*.py' -v
```

Final results: **98/98 Node tests**, **64/64 Python tests**, including **9/9
new real-Chromium run-store tests**. No skipped tests or failures. Frozen
`js/video.js` and every prompt/manifest match A1 byte-for-byte; the protected-file
hashes and staged credential/execution scan are in `reports/a2/protected-and-scan.log`.

Evidence and vertical RED/GREEN logs: `reports/a2/`. Full Python regression runs
execute a runtime/tests copy beneath ignored `reports/a2/regression-app/` so
baseline A1 screenshots/reports remain untouched. `python-full.log` records the
final suite. Parent performs independent review before pushing WIP.

## Next checkpoint

Wire scoped initialization + migration/error display to startup/settings; build
an adapter without altering video engine algorithms; ensure no request is made
until migration and run creation commit. Resume queued/processing jobs via the
global watcher; uncertain no-id jobs need explicit identical-request recovery.
Add account-epoch cancellation, watcher notices, local/gateway merge and cards
only in the next authorized slice. This commit does not claim those flows are
already durable end-to-end.
