# Checkpoint 2 review-blocker regression evidence

Scope: only the two HIGH review blockers at base
`74634a698bf64b60fe0546d8a456ae5118328a37`. No live inference, credentials,
push, deployment, package, A3 or presentation polish.

## Vertical regressions

All browser tests use `/usr/bin/chromium`, actual IndexedDB transactions and browser
Web Locks. The harness intercepts loopback inference endpoints and aborts all
non-loopback browser requests. Responses are explicit offline fixtures.

Run a focused case from the repository root with:

```sh
PYTHONPATH=tests python3 -m unittest test_durable_video_browser.DurableVideoBrowser.test_interrupted_planner_reload_allows_new_render -v
```

| Evidence prefix (`c2-review-`) | Actual RED | GREEN evidence |
| --- | --- | --- |
| `planner` | Reloaded planning-only run blocks new render: zero POSTs instead of one | `planner-green.log`, final Python suite |
| `retry` | Initial IDB add abort refuses POST, but identical retry reaches POST with empty durable prompt | `retry-green.log`, final Python suite; before-POST assertions include inputs, canonical request, plan and receipts |
| `reload` | Reload after add abort loses edited prompt and plan restoration | `reload-green.log`, final Python suite |
| `conflict` | Nonidentical retry corrupts the stored recovery snapshot; subsequent reload loses original prompt | `edge-green.log`, final Python suite |
| `draft-binding` | Another brief with the same canonical body supplies the wrong inputs/receipts on reload | Final Python suite; exact token/version/body binding selects the original snapshot |
| `old-placeholder` | Existing pre-marker migration placeholder rejects metadata restoration | `edge-green.log`, final Python suite |
| `abandoned-notice` | Account replacement marks the old plan abandoned but returning to that account has no visible notice | Final Python suite |

Additional durable-browser regressions cover active cross-tab planners (not
abandoned), account replacement while planning, old checkpoint planning-only rows,
and tokenless creating/rendering rows (still block). Run-store browser tests cover
one-time enrichment, hash/token/version/quote mismatch rejection, credential and
cross-account rejection, real transaction-abort rollback, repeat migration,
append-only receipts, and immutable request fields after enrichment.

`c2-review-focused.log` retains the first focused-suite result, whose only error was
the new cross-tab fixture reading settings before hydration. The first complete
suite's same fixture error is retained in `c2-review-python-harness-failure.log`.
The corrected fixture waits for the rendered settings input, not the static view
container or an async wait predicate. These are not final passes.

## Final commands and results

```sh
# Repository root:
node --test tests/*.test.mjs
# reports/a2/c2-regression-app (ignored runtime/tests/skills/catalog copy):
python3 -m unittest discover -s tests -p 'test_*.py' -v
# Repository root:
git diff --check
```

- `c2-review-node-final.log`: **98 tests, 98 pass, zero failures/skips**.
- `c2-review-python-final.log`: **85 tests, OK, zero failures/skips**; includes
  17 durable-video integration tests and 13 run-store browser tests.
- `c2-review-protected.log`: frozen engine plus every skill prompt/manifest
  compared byte-for-byte against the base, with no differences.
- Engine SHA256 remains
  `71986db49b64763229a90e4d4fe10ae78ebfc45b27070f6d32e675e21a31450b`.

Earlier baseline evidence is not overwritten. Generated screenshots/media from the
complete Python suite remain inside the ignored regression copy and are not part
of this narrow correction commit.

## Store evolution and limits

The database version remains 1. Migration adds an **internal-only**
`recovery_metadata_missing` marker to identity-only imports. Public create/update
payloads cannot set it. Only untouched deterministic pre-marker import placeholders
can acquire it on re-migration. The dedicated enrichment API checks the canonical
request hash and exact existing token/version/quote in a strict transaction, fills
previously absent metadata, and sets the marker false. Existing ordinary
create/update identity checks are unchanged. Enrichment cannot alter an already
bound prompt, inputs or model list; migration cannot reopen a filled metadata hole.

The UI retains the edited canonical snapshot on the durable planner row before the
render insert, then binds it to the engine identity. A matching body alone is not
enough to borrow another draft's brief or receipts. No engine token, quote, body,
planner prompt, FIELDS or manifest algorithm changed.

Data that never existed in either durable snapshots or legacy references cannot be
reconstructed. Abandoned text calls are not automatically retried or represented as
free/refunded. The notice says only that no video was submitted. No live billing or
inference claim is made.
