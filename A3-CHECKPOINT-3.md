# A3 checkpoint 3 — route-owned VIDEO page

Base: published checkpoint 2 `c5702cf78d8e6c51d6957457aa81830b1183a3f9`.
This checkpoint is VIDEO page integration only, not completed A3 or a deployment.
Run-detail/My work/cache drafts are deliberately excluded from this commit.

## Delivered
- `#/flow/claw__motion-trimmer-video` is a real route-owned, two-column page
  (stacked at 390px), not an iframe, modal or hidden modal chrome. Create and the
  compatibility `#/skills` video card both navigate here. Direct reload/back and
  active Create navigation are exercised by real Chromium.
- Shared markup/binding extraction preserves the existing durable engine boundary.
  An explicit compatibility modal export remains for old callers/regression tests;
  it is no longer the public VIDEO entry. Other three flows remain unchanged
  modal implementations for Part B.
- Lite caveat is exactly `5-second clip · landscape for now · you approve the price first`.
  Detailed draft/timeline/overlay/platform/upload/stitch/music/audio/framing limits
  and raw JSON/model receipts remain Pro-only. Actual Lite DOM was asserted,
  including absence of duplicated legacy/default caveats.
- `Plan my video` has adjacent plain disclosure that planning uses a separately
  billed text call. Successful planning automatically obtains a fresh validated
  quote. Generate displays `Generate · $X.XX`, and the note is exactly
  `charged only if it renders`. No hardcoded display price; quote functions,
  FIELDS, canonical body, token and version algorithms are frozen.
- Prompt/plan/model edits invalidate the old quote immediately. Sequence+spec
  checks reject out-of-order responses; expiry disables old prices. Pro retains
  manual refresh. New-version and identical-retry flows retain their existing
  engine defenses. Quote refresh/new-version preparation never sends a paid POST.
- Real inline masked key entry and Connect appear before the form inputs when
  disconnected. Connect uses existing Settings/account lifecycle, makes no key
  validation/inference request and stores no key in IDB/URLs/prefill. Connected
  state says key connected / runs save to My work. Account removal/replacement,
  cross-tab changes, async teardown and stale-media cleanup are covered.

## Verification and evidence
- Actual behavior RED before wiring: `reports/a3/c3-integration/routes-red.log`
  (3 missing-route/page behavior failures, not syntax/import/setup failures).
- Clarification RED: `reports/a3/clarifications/red.log` (missing automatic quote,
  inline Connect and exact Lite copy; the separate My work case belongs to cp4).
- Earlier shared-binding RED and planner-prefill evidence remain under
  `reports/a3/c3-video/`; no baseline screenshots were regenerated in this commit.
- Complete isolated checkpoint runtime:
  `python3 tests/verify_a3.py --checkpoint3 --label c3-verified`
  **98/98 Node; 127/127 Python, zero failures/errors/skips.** Logs:
  `reports/a3/c3-verified-node.log`, `c3-verified-python.log`, `c3-verified-results.json`.
  This includes 13 page, 3 router and 3 VIDEO clarification cases, alongside all
  retained storage/recovery/proxy/security tests. Real `/usr/bin/chromium`, real
  IndexedDB/Web Locks, explicit offline fixtures and the server forwarding deny
  guard remain active through teardown. No upstream inference/list/render.
- After visual inspection, one heading typography rule and screenshot scroll-to-top
  setup were finalized. Final styles and route tests were copied into the isolated
  runtime and all 3 router/desktop/390px cases rerun successfully:
  `reports/a3/c3-integration/isolated-final-ui.log`. No engine/binding changes after
  the full pass. Final OFFLINE FIXTURE screenshots: the four
  `reports/a3/c3-integration/video-{1280,390}-{lite,pro}-OFFLINE-FIXTURE.png` files.
- All 21 frozen files match pinned base d95c153 exactly:
  `python3 tests/check_a3_frozen.py`, `reports/a3/c3-integration/frozen.json`.
  Frozen video SHA256 is
  `71986db49b64763229a90e4d4fe10ae78ebfc45b27070f6d32e675e21a31450b`.
- Self-review: static owned markup/escaped planner text; no key diagnostics,
  account-epoch checks before async UI work, quote race rejection and cleanup;
  clean `git diff --check`. Earlier c3-source failures were test-harness defects
  (counting a separate interception handler and reading before async recovery),
  corrected without dropping the underlying assertions and superseded by final pass.

## Remaining / honest boundaries
No final ZIP or deployment is claimed. Checkpoint 4 still owns durable-id run
routes, ready-notice/pickup destination changes, My work inline empty state,
group/search/filter integration and bounded authenticated media cache/package.
Text/email/comparison capture is Part B, after A3, not delivered by this page.
Missing legacy planner metadata cannot be reconstructed; account hashing is
isolation, not encryption. Legacy recovery entries remain while old writers exist.
