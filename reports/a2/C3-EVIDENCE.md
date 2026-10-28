# A2 checkpoint 3 evidence index

## Final acceptance

- `c3-source-{node,python}.log`: complete isolated source suites, **98 Node + 95 Python**, no failures/skips/teardown tracebacks.
- `c3-packaged-{node,python}.log`: the same complete suites against a relocated extracted production runtime, **98 + 95**, no failures/skips/teardown tracebacks.
- `c3-final-verification.{json,log}`: programmatic test/class counts, byte equality of source/ZIP/extracted/tested runtimes, protected engine/store/runtime comparison, scoped runtime static scan.
- `c3-package-verification.json`, `c3-package-build.log`: deterministic rebuild equality, all 44 runtime files equal source, 21 frozen files equal baseline, all 96 extracted GET/HEAD checks, known unchanged literal prefix markers.
- `c3-opened-poster-mobile.png`: final real offline Chromium screenshot, actual blue decoded fixture frame, escaped prompt title and Ready label, mobile no-overflow assertion.
- `c3-poster-repeat-final.log`: ten consecutive final focused real-browser runs with callback/encoding diagnostics.

## RED → GREEN slices

- `c3-titles-{red,green}.log`: first-nonblank prompt titles, truncation, escaping, human date/no-date fallback and plain statuses.
- `c3-poster-{red,green}.log`: poster absent before Open, present after Open, reload persistence without a second content request, account isolation and raw-IDB fake-key exclusion.
- `c3-offline-{red,green}.log`: server fixture denies forwarding even without browser interception; upstream opener is never invoked; fixed response contains no diagnostics/key.
- `c3-frame-pixels-{red,green}.log`: an image URL alone was insufficient; decoded JPEG pixels must match the blue offline fixture rather than a black unpainted surface.
- `c3-frame-registration-{red,green}.log`: register the compositor callback before assigning source to avoid missing a fast paused first frame.
- `c3-frame-readiness-{red,green}.log`: compositor callback can precede `loadeddata` with readyState 1. Capture now waits for both conditions in either order. Final GREEN also covers SecurityError, bad media decode and bounded cache eviction.
- `c3-static-disconnect-{red,green}.log`: cancelled static-file writes suppress only BrokenPipe/ConnectionReset; real handler errors still surface and the upstream-attempt assertion remains active.

## Retained diagnostic / non-final runs

- `c3-cards-complete.log`: initial test instrumentation error (Playwright auto-invoked a returned assigned function); corrected the test wrapper, not production error handling.
- `c3-packaged-frame-race-failure.log`: full-suite paused-frame callback/readiness race, resolved by the explicit readiness regression above.
- `c3-final-poster-repeat.log`: pre-final diagnostic captured a frame callback at readyState 1, later readyState 4 with no poster; this isolated the dropped-capture condition.
- `c3-packaged-static-disconnect.log`: earlier suite passed but had an aborted **static** response BrokenPipe traceback, not an upstream request; final handler fix and both full suites are clean.
- `c3-offscreen-red.log` is a hypothesis probe that **passed**, not RED evidence. Small viewport alone did not reproduce the race. Earlier repeat/probe logs are diagnostic, not final acceptance.
- `c3_capture.py`, `c3_frame_probe.py`, `c3_poster_repeat.py`, `c3_verify_final.py` are local reproducibility/evidence helpers, not runtime package contents.

No live credentials, gateway list, paid inference, push or deployment was used.
Prior checkpoint evidence and baseline screenshots are unchanged; full tests write only inside ignored A2 copies.
