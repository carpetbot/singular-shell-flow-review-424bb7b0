# A3 checkpoint 2 — navigation and Create

Base: checkpoint 1 `a0cb828873b746c2acb4aafd13478f9f27a7a4ef`.
Scope: desktop/mobile navigation and Create only. This is **not full A3**.
Video flow-page, inline Connect, Your work empty-state, run detail, media cache
and final ZIP work remain uncommitted drafts for the next checkpoints. No deploy,
live app key lookup, paid render, real inference or upstream video-list request.

## Delivered
- `#/create` is the default, including reload/back navigation. Desktop sidebar
  and390px bottom navigation lead with Create / My work / Settings; Chat/Models
  remain Pro-only. Existing `#/skills` is retained as a compatibility route.
- Four outcome-led cards use loaded manifests and catalog pricing: video quote,
  approximate email preflight, and explicit unknown/model-dependent costs where
  a defensible estimate is unavailable. No hardcoded $0.53 or invented zero price.
- Up to two recent account-scoped durable records are displayed with the first
  saved prompt line/title. Planning is distinct from Rendering. Key replacement
  and removal clear prior-account pickup cards. The later run-detail checkpoint
  will replace the existing My work/query recovery destination.
- Scoped Create CSS follows the pinned prototype's2-column desktop /1-column
  mobile grid, using existing tokens. Legacy gallery styles are untouched.

## Actual verification
Final isolated checkpoint runtime (not the mixed working tree):
`python3 tests/verify_a3.py --checkpoint2 --label c2-published`

- **98/98 Node**, zero failures/cancellations/skips.
- **108/108 Python**, zero failures/errors/skips, including4 new real-Chromium
  Create cases. Real IndexedDB/Web Locks, explicit loopback fixtures and existing
  browser+server forwarding deny guards remain active through teardown.
- Evidence: `reports/a3/c2-published-{node,python}.log` and
  `c2-published-results.json`. Earlier failed/partial runs are not counted.
- Final screenshots copied from that isolated run: `reports/a3/c2/published-create-390-OFFLINE-FIXTURE.png`
  and `published-create-desktop-OFFLINE-FIXTURE.png`. Both inspected visually.
- The original full run failed4 old presentation assumptions: Flows navigation,
  implicit old-gallery home, first-card selection and gallery screenshot heading.
  Legacy gallery/modal tests now explicitly navigate `#/skills`, while the nav
  label expectations become Create. No lifecycle/security assertions were removed.
  The imported fixture base class is deleted from the new test module namespace
  so unittest does not accidentally rerun15 legacy video cases as new coverage.
- Visual review also found a real issue missed by the old document-width check:
  Create inherited an internally scrolling carousel, clipping outcome cards on
  phones. A strengthened real390px test reproduced RED (`c2/mobile-grid-red.log`),
  then passed after the scoped grid fix (`c2/mobile-grid-green.log`). It checks
  internal scroll width, every card's horizontal bounds and vertical stacking.

## Isolation / preservation
`--checkpoint2` builds a throwaway runtime from committed checkpoint1 plus an
explicit list of navigation/Create overrides and relevant test adaptations.
Unfinished video/detail/cache changes in the shared working tree are excluded.
The final checkpoint-source files match that verified runtime byte-for-byte.
Frozen engine, prompts, manifests and pricing/idempotency algorithms remain
unchanged. The existing video modal remains intentionally functional in this
checkpoint until its route-page replacement is independently tested/published.

No final A3 ZIP is claimed, and this checkpoint is not deployed. Next: video page
with the reviewer's one-line Lite caveat, Plan my video/automatic quote/Generate
price, inline Connect and honest planner-charge disclosure; then run detail,
Your work empty state and bounded authenticated media recovery. Part B text-run
capture remains a subsequent phase, not something this Create page already saves.
