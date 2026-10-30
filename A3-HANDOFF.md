# A3 Part A handoff — review build, NOT deployed

Repository: `carpetbot/singular-shell-flow-review-424bb7b0`.
Review branch: `ux-v1-part-a`; local build branch: `ux-v1-a3-build`.
Pinned spec: `940e8c764922fb10e15e2fdc3383fffc0313eb3f`.
Frozen engine/prompts/manifests base: `d95c15323d435f19d2ff634d92484c4b9503b3f5`.
A2 comparison base: `7efe1eddb28fd30d2bd93229103917102985be16`.

## Published checkpoints / final publication
- Checkpoint1: `a0cb828873b746c2acb4aafd13478f9f27a7a4ef` — transactional
  ready notices and live My work, independently reviewed by Sofa.
- Checkpoint2: `c5702cf78d8e6c51d6957457aa81830b1183a3f9` — navigation/Create,
  completed/published independently by parent; see `A3-CHECKPOINT-2.md`.
- Checkpoint3: `4e5c9142d9091059df89e5bf2ed279d126238967` — real VIDEO page,
  inline Connect, exact Lite copy, guarded automatic quotes. Pushed fast-forward
  and independently read back before finishing detail/package integration.
- Final checkpoint: this handoff's commit on `ux-v1-part-a`; the exact pushed SHA
  and independent `git ls-remote` readback are returned in the worker's final report.

No production deployment, restart, live site modification, real key lookup, live
video-list/status call, upstream inference or paid render was performed. The
live site remains A2 according to the parent's supplied status, not a new probe.
No Slack API was attempted; parent must verify the publication and notify both
Shuenrui and Sofa. This is not a claim that either has approved the final build.

## Production artifact
- `dist/shell-ux-v1-a3.zip`
- `dist/shell-ux-v1-a3.zip.sha256`
- SHA256: `1d8dc68a5563fb8f7d5e40b0d4d61d8e444f4dff87da4d971f25aca9a59288e9`
- 49 runtime files. No repository metadata, tests, reports, handoff docs,
  credentials or extra Python modules. `proxy.py` is the required server runtime;
  its source is denied over GET and HEAD. No A2 artifact was overwritten.
- Deterministic second rebuild is byte-identical. Every archived byte equals
  source and the independently relocated extraction; every runtime byte also
  equals both completed source/package regression trees. Exact manifest and
  checks: `reports/a3/c4/package-verification.json`, `final-provenance.json`.
- All 21 frozen engine/prompt/manifest files match pinned base byte-for-byte.
  `js/video.js` SHA256 remains
  `71986db49b64763229a90e4d4fe10ae78ebfc45b27070f6d32e675e21a31450b`.
- Explicit `STATIC_ASSETS` allowlist exactly matches the public runtime assets,
  including every new JS module. 118 extracted-server GET/HEAD checks pass,
  including denial of injected unknown JS, Python, tests, reports, encoded paths,
  directories and fake secret-file paths. The server-side forwarding deny guard
  records zero unexpected upstream attempts during these checks.
- No credential-pattern hits in runtime. Unchanged baseline literal prefix labels
  remain in chat/settings/skills; their exact lines are checked against base.
  This is deliberately not a false claim that all literal key-prefix markers
  were removed from the original application.

## Delivered Part A
### Navigation, Create and VIDEO
See checkpoint2/3 handoffs for their detailed evidence. The default is `#/create`;
Create / My work / Settings remain desktop/mobile primary navigation, and
Chat/Models remain Pro-only. Compatibility `#/skills` still works. Outcome cards
price from the actual in-memory catalog/frozen quote/preflight helpers; model-
dependent or missing prices stay honestly unknown. Pickup cards use saved prompt
or title, distinguish Planning from Rendering and now open canonical detail ids.

VIDEO uses `#/flow/claw__motion-trimmer-video`, a route-owned page reusing the
binding rather than modal chrome. The exact Lite caveat, Plan my video, inline
key entry before inputs, separately billed planning disclosure, fresh quote-driven
Generate price and charged-only-if-it-renders note are present. Detailed caveats,
raw plan and model/receipt diagnostics are Pro-only. Quote edits/races/expiry,
canonical retry/new-version recovery, save-before-network and unknown-cost rules
remain defended. No quote refresh or Connect action creates a paid submission.

### Your work and canonical detail
- Empty heading is `Your work`. Without a key there is a real masked inline
  Connect form and Refresh is hidden, not merely disabled. A plain paragraph
  explains that videos appear here and text/email/comparison capture comes next.
- Day-grouped cards support All / Videos / Emails / Comparisons / Rendering and
  title/prompt search. Local/gateway jobs merge by gateway job identity, while
  links use durable run ids. Bound planner snapshots do not duplicate the render
  card; standalone plans remain visible without pretending they have MP4 output.
- Primary links use `#/work/<durableId>`. Gateway-only entries explicitly use
  encoded `gateway:<jobId>` names, never a gateway id masquerading as a local id.
  Ready-notice Open and Create pickups now reach these proper detail routes.
  Existing query recovery and explicit inline Open video remain compatibility
  actions, preserving old recovery/poster behavior.
- Output-first detail plays authenticated fetch → bounded blob → video and offers
  Download MP4, Copy prompt and Run again with changes. It shows recorded status,
  cost, model, created time and prompt; Pro shows actual per-step receipts or an
  honest missing-evidence message. Clipboard/output escaping and full downloads
  are exercised, not just visible button labels.
- Gateway-only detail uses ONE authenticated single-job status read with bounded
  timeout and validated identity/cost/optional metadata, not a 100-page list walk.
  Missing prompts are not invented. Unrelated local notifications do not repeat
  that lookup; Refresh status is explicit and terminal state cannot regress.
- Run again passes only whitelisted creative fields (`topic/context/platform`),
  account hash, source run id and timestamp. It carries no key, paid token,
  canonical request, saved quote or render identity. The one-shot prefill is
  account/age validated, consumed and removed. It never submits or bypasses an
  unresolved original request; original inputs missing on this device disable it.
- App-owned observation, origin/account/job transactional notice claim, historical
  terminal suppression, monotone polling and nonowner live updates are preserved.
  Route teardown aborts/revokes media and rejects stale reads. An additional RED
  reproduction found old cards/drafts could reappear inside the Settings hydration
  window after a cross-tab change. Explicit hydration gates now keep them removed
  through that window; both real-browser regressions pass.

### Optional bounded media/preview caches
MP4s are fetched only on explicit opening, not for grid previews. Cache scope is
account hash + validated job id. IndexedDB MP4 payload is bounded globally at
64 MiB /16 rows with transactional oldest-first eviction across accounts. Videos
larger than the cache limit can still play/download within the existing 100 MiB
fetch limit. Optional write failure does not block playback; timed-out/blocked
opens close late connections. Existing posters are only captured from opened,
decoded/presented frames, remain bounded at 2 MiB /64 rows and are account-scoped.
Poster/decoder/canvas/cache failures never invent a preview or require regeneration.

## Actual final verification
Both complete suites ran after the final runtime changes:

| Runtime | Node | Python (including real Chromium) |
|---|---:|---:|
| Isolated source | 101/101 | 156/156 |
| Relocated extracted ZIP | 101/101 | 156/156 |

Zero failures/errors/skips/cancellations. Browser tests use `/usr/bin/chromium`,
real IndexedDB/Web Locks and explicitly offline gateway/model fixtures. Browser
interception and the server deny boundary remain active through about:blank and
shutdown, with zero unexpected forwarding asserted. No live gateway data/results
are substituted for fixtures. Screenshots are labeled OFFLINE FIXTURE and were
visually inspected at desktop and 390px.

Commands actually used:
```
python3 tests/package_a3.py
python3 tests/check_a3_frozen.py
python3 tests/verify_a3.py --label a3-final-source
python3 tests/verify_a3.py --runtime reports/a3/package-a3/relocated/runtime --label a3-final-packaged
python3 tests/verify_final_a3.py
```
For an independent rerun choose NEW labels; the runner refuses to overwrite prior
suite logs. Build/extract the archive before starting a packaged suite; do not
replace that extraction while a suite is running.

Final evidence:
- `reports/a3/a3-final-{source,packaged}-{node,python}.log`
- `reports/a3/a3-final-{source,packaged}-results.json`
- `reports/a3/c4/final-provenance.{json,log}`, `package-verification.json`, `frozen.json`
- `reports/a3/c4/integration-red.log`, `hydration-red.log`, `static-red.log`
- `reports/a3/c4/integration-final-green.log`, `detail-green.log`, `work-connect-green.log`
- Single-job gateway RED/GREEN: `reports/a3/c3-detail/gateway-status-{red,green}.log`
- Final actual-route desktop/phone screenshots: `reports/a3/c4/*-OFFLINE-FIXTURE.png`
  (also generated independently in the isolated source/package test trees).

- Supplemental cache behavior probe: `python3 tests/cache_behavior_probe.py`.
  Against checkpoint3 it fails on **2 media fetches vs1 expected**, without
  importing a missing cache module or depending on a setup failure. The final
  source and relocated ZIP each pass this additional1-case probe. Logs:
  `reports/a3/c4/cache-behavior-{baseline-red,source-green,packaged-green}.log`.
  This supplementary probe is outside the discovery glob and is not added to
  the156 full-suite count above.

Earlier exploratory/partial/failed logs are not final passing evidence. Baseline
A1/A2 screenshot/wire evidence was kept unchanged. Legacy assertion adaptations
are limited to the new title/route/card ordering and explicit cache semantics:
security, malformed-metadata, delayed-download, account isolation, IDB abort,
canonical retry and cross-tab ownership assertions remain in place. A cache miss
is explicitly prepared when testing delayed network media rather than weakening
that stale-response test.

## Changed production files since A2
`index.html`, `styles.css`, `proxy.py`; `js/app.js`, `js/key-connect.js`,
`js/media-cache.js`, `js/poster-cache.js`, `js/run-store.js`, `js/video-runtime.js`,
`js/video-ui.js`, `js/work-api.js`, and `js/views/{create,skills,video-flow,work-detail,work}.js`.
The exact hash inventory is in the package verification report.

## Limits / next phase
- This completes the A3 Part A review build, NOT every item in the combined Part
  A+B brief. Cold Email, Model Jury and Motion Trimmer still use their existing
  functional modals and do NOT capture runs in this store. Part B is next after
  A3 review. Generic mixed-record filter/detail tests use explicit synthetic local
  records; they are not evidence that those nonvideo engines already save history.
- No authorized real list/status call was made to verify whether this gateway's
  production `params` includes a prompt. Known fixture fields are handled; absent
  gateway prompts say Prompt saved on another device. Original inputs/planner
  receipts missing from this browser cannot be reconstructed.
- Durable local rendering records resume via the app watcher. Gateway-only jobs
  without local submission history use explicit Refresh status/Refresh videos;
  no original paid request or local ownership is fabricated for another device.
- Durable receipt cost stays unknown if it was never recorded. Gateway-only
  status/list cost is shown only when its field is a validated finite amount;
  missing usage/cost is never silently converted to zero.
- Account hashing/cache scoping is isolation, not encryption or protection against
  arbitrary same-origin scripts/devtools. Settings retain the existing browser
  key-storage policy. Clearing browser data removes local history/cache.
- Ready notices retain the documented durable-claim-to-DOM crash gap and possible
  browser background throttling. They are not OS push notifications.
- Legacy recovery references remain while the frozen legacy writer exists.
- No deployment is authorized. Parent owns final remote/artifact verification,
  notification to both Shuenrui/Sofa, review approval and any later deployment.
