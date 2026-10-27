# Sofa six-fix revision + approved five-second defaults — evidence

## Result / scope

Local replacement review build only. No paid calls, commit, push or deployment. Earlier disabled-generation/15-second review text is superseded by the user's explicit approval of five-second omitted-field defaults. Parent independent review and Sofa's review of this replacement ZIP remain required before deployment. Criterion 12 (real render quality, actual duration/resolution/content and settled billing) remains **UNVERIFIED**; the user will test after reviewed deployment with a securely entered capped key. Custom 10/15-second/aspect/audio mappings are still null/unconfirmed; the five-second default mode is enabled.

Runtime ZIP: `dist/motion-trimmer-video-review.zip`  
SHA256: `4346595ff81376624bea8650ab332bbed24729f20ce88ebc18b5ae7609ec94e4`  
Regular runtime files: **40**; ZIP CRC OK; every file equals current source and extracted package. No tests, pricing fixtures, private designs, reports, caches, nested builds or credentials in the ZIP.

Source, extracted-package and relocated-source runtime manifest SHA256 are identical:  
`9bb9c7ed9ffb057df55e70b6465f42507cb52ffdc43715344b773ff79bb7ee62`  
This is SHA256 of the ordered JSON `[path,file_sha256]` list (compact JSON separators), not the ZIP hash. Per-file source/copied hashes: `package-manifest.json`; machine-checked totals: `verification-summary.json`.

Public catalog snapshot: `tests/fixtures/video-pricing.json`, as_of `2026-10-27T07:04:16.704Z`, SHA256 `6f992c577a7c5934980244358f056ef8fbc5d9b7131aeed585b4afd5e51dc3bd`. It is committed-source-ready public fixture data, excluded from runtime. No paid result is implied. Default Node tests pin the saved timestamp; browser fixtures explicitly replace only their in-memory timestamp with the test's current time so clone tests remain repeatable.

## Full verified gates

| Actual suite | Pass | Fail / skip | Evidence |
|---|---:|---:|---|
| Source Node (original 83 plus new checks) | 90 | 0 / 0 | `source-node.log` |
| Source Python, actual offline Chromium (original 42 plus new checks) | 45 | 0 / 0 | `source-python.log` |
| Relocated source Node, unrelated caller CWD, denied original reads | 90 | 0 / 0 | `relocated-node.log` |
| Relocated source Python/Chromium, unrelated caller CWD, denied original reads | 45 | 0 / 0 | `relocated-python.log` |
| Python/Chromium with extracted-runtime app roots | 45 | 0 / 0 | `packaged-python.log` |

Package-aware Video UI/proxy, Lite/Pro and Model Jury suites use the extracted package roots. Legacy `test_ui.py` and generic `test_proxy.py` retain their original source harness, rather than falsely claiming they honor app-root variables. All 40 package bytes are independently identical to source. Twenty-nine protected old-flow engine/UI/manifest/prompt files match `378d6f4` exactly (`protected-hashes.json`); this revision makes no proxy change. Existing old-flow request-body regression checks remain passing, with the prior captured-body comparison at `../motion-video/legacy-compare.txt` still applicable to these unchanged bytes.

## Six vertical red → green slices

1. **Portable public pricing fixture.** `01-red.log` fails because test readers name the original home/scratch snapshot. `01-green.log` passes after adding `tests/fixtures/video-pricing.json` and source-relative URL/Path loads in `video.test.mjs`, `video-cross-tab.test.mjs`, and `test_video_browser.py`. The later approved fresh snapshot replaces the initial saved fixture without changing exact price expectations. A source-equivalent relocated copy contains runtime, tests, README and only the legacy public fixture outside tests; no old report trees. Full suites run from `/home/orangepi`, not the checkout. Node filesystem guards and Python audit hooks reject reads of original source and both original scratch price files, while allowing the relocated copy; `portability-guard.log` proves an attempted original fixture read is denied in both runtimes.
2. **Two-decimal video money only.** `02-red.log` fails on the missing formatter; `02-green.log` passes after `videoMoney` formats all quote/button/planner/video receipt amounts with two decimals. Numeric quote comparison/persistence remains exact. Node checks include small/zero/unknown values. Browser checks use $0.53/$0.21 and $0.00; frozen other-flow formatting/engines are untouched.
3. **Readable Lite plan, Pro-only JSON, shared prompt.** `03-red.log` fails because Lite exposes raw JSON; `03-green.log` passes with time-range/beat, overlay time/text and dropped-item lists. Prompt edits synchronize to JSON; Pro prompt edits synchronize back; switching modes preserves both without a call. Typed `validatePlan` remains the generation boundary. Browser tests edit a malicious HTML-looking description and verify literal text/no image element; all model values are escaped. Reviewed `source/video/lite-plan.png` and `pro-plan.png`: readable structured plan, raw editor only in Pro, no horizontal overflow; the modal intentionally scrolls vertically.
4. **Clear finished jobs.** `04-red.log` fails on the missing history operation; `04-green.log` passes with exclusive Web Lock + re-read + filter + write. Only completed/failed/rejected refs are removed. Creating/queued/processing/uncertain/unknown/unrecognized refs survive, including wrong-account unresolved refs and concurrent new work. Twenty finished refs clear and capacity recovers for a new job (`video-defaults.test.mjs`). `04-ui-red.log` fails on the missing button; `04-ui-green.log` proves clearing a selected finished entry selects/keeps the pending job and preserves Resume while preventing new generation. Existing new-version/idempotency/monotonic-save tests stay green.
5. **Continuous open-panel polling.** `05-red.log` catches the old three-minute deadline with fake elapsed time; `05-green.log` passes after removing the overall deadline, keeping 20-second status-request timeouts, 30-second other JSON requests and a 1-second initial/15-second maximum backoff. The abort-aware sleep ends on dispose. `05-ui-clock.log` advances real Chromium five minutes with the fake clock, sees continued polls, then closes and proves no further poll/no additional POST. Errors stop observation and show auth/credit/not-found/network diagnostics; explicit Resume is available rather than an error busy loop. Reload remains GET-only on explicit Resume. Existing close-during-create, cross-tab terminal persistence and pending-history guards remain green.
6. **Plain labels and messages.** `06-red.log` catches old platform labels; `06-green.log` passes for X / Instagram Reels / YouTube Shorts and removal of user-facing release-gate/explicit-generation/creating-key/idempotency-token/uncertain-submission jargon. “Make another version” and “the key you used to start this video” replace technical action copy. Internal recovery identifiers retain their technical names. The subsequently approved default mode replaces the interim disabled-generation banner completely.

## Approved five-second default mode (additional vertical slice)

`07-defaults-red.log` fails before default-mode support; `07-defaults-green.log` passes after guarded omitted-field generation. `07-ui-red.log` fails against the old disabled/15-second UI; `07-ui-green.log` passes with the fixed-five-second UI. `07-audio-red.log` catches a catalog/audio-label mismatch; `07-audio-green.log` passes after enforcing the documented audio default too.

- UI has no duration/aspect/audio controls. Planner times total exactly five seconds. Default framing is not promised; Wan audio on and MiniMax unspecified are labelled.
- Default catalog validation requires five seconds, expected resolution (Wan720p/Mini768p), expected audio default, routable video model and one exact numeric matching price. Missing defaults/config, stale timestamp, mismatches, unavailable/nonexact data and custom 10/15 durations refuse before POST. Timestamp age is at most 24 hours and no more than five minutes into the future. Fresh pricing/defaults are checked again before submit; numeric price equality is never rounded.
- Production `FIELDS` stays all null. Actual default-mode browser POST body has only `model`, `prompt`, `resolution`; no guessed custom field. Future documented adapter maps remain supported only through injected test configuration, never through query/localStorage overrides.
- `default-mode/default-wire.offline.json` records actual offline browser requests and five-second planner output. `default-mode/wan-five-seconds.png`, `minimax-five-seconds.png` and `lite-shot-list.png` show the actual UI. `default-capture.log` is the successful supplementary capture result. These are explicitly fake inference plus a synthetic one-second MP4, **not a model render proving five-second media**.

All prior five safety blockers remain exercised: shared request-derived idempotency/origin lock, all-history pending guard, bounded sanitized video errors, detectable incomplete chunk/overflow fetch failure with download-only recovery, and monotonic terminal persistence. See the named tests in the full logs; criteria 1–11 remain offline-only checks, never a live-quality/billing claim.

## Commands actually executed

From repository root (`R` below), after pre-creating `reports/motion-video-usability/source/{lite,jury,legacy,video}`:

```sh
node --test tests/*.test.mjs
VIDEO_LITE_EVIDENCE="$R/reports/motion-video-usability/source/lite" \
VIDEO_JURY_EVIDENCE="$R/reports/motion-video-usability/source/jury" \
VIDEO_LEGACY_EVIDENCE="$R/reports/motion-video-usability/source/legacy" \
VIDEO_EVIDENCE="$R/reports/motion-video-usability/source/video" \
python3 -m unittest discover -s tests -p 'test_*.py' -v
python3 reports/motion-video-usability/build_review.py
```

`build_review.py` creates ZIP, manifest, extracted runtime, relocated source and original-path guards. Relocated full suites were executed from `/home/orangepi` (unrelated CWD):

```sh
C="$R/reports/motion-video-usability/relocated-source"
node --require "$C/deny-original.cjs" --test "$C"/tests/*.test.mjs
PYTHONPATH="$C" \
VIDEO_LITE_EVIDENCE="$C/reports/verification/lite" \
VIDEO_JURY_EVIDENCE="$C/reports/verification/jury" \
VIDEO_LEGACY_EVIDENCE="$C/reports/verification/legacy" \
VIDEO_EVIDENCE="$C/reports/verification/video" \
python3 -m unittest discover -s "$C/tests" -p 'test_*.py' -v
```

All screenshot paths were below that test copy's ROOT and parents pre-created. The initial relocation attempt set TMPDIR to the very long nested source path; Chromium launch died with SIGTRAP and subsequent Playwright errors. That honest failed log is retained as `relocated-python-attempt1.log`. Re-running with the normal short configured scratch TMPDIR passed all 45; no production or test-code workaround was substituted. Original-fixture denial remained enabled. Scratch temp storage is runtime infrastructure, not a price-fixture dependency.

For package execution from the source root, with `A="$R/reports/motion-video-usability/packaged-runtime"` and pre-created package evidence directories:

```sh
VIDEO_APP_ROOT="$A" SINGULAR_UI_APP_ROOT="$A" JURY_APP_ROOT="$A" \
VIDEO_LITE_EVIDENCE="$R/reports/motion-video-usability/packaged/lite" \
VIDEO_JURY_EVIDENCE="$R/reports/motion-video-usability/packaged/jury" \
VIDEO_LEGACY_EVIDENCE="$R/reports/motion-video-usability/packaged/legacy" \
VIDEO_EVIDENCE="$R/reports/motion-video-usability/packaged/video" \
python3 -m unittest discover -s tests -p 'test_*.py' -v
python3 reports/motion-video-usability/capture_default.py
```

Targeted RED/GREEN commands were `node --test tests/video-usability.test.mjs`, `node --test tests/video.test.mjs`, `node --test tests/video-defaults.test.mjs`, and `python3 -m unittest discover -s tests -p test_video_browser.py -k <test_name> -v`, with isolated `VIDEO_EVIDENCE`. The logs above retain actual outcomes; the complete final suites supersede targeted intermediate counts.

## Publication boundary

Preserve pre-existing unrelated report/screenshot churn. Do not add entire generated verification trees: `relocated-source/` and `packaged-runtime/` are local workspaces and must be excluded from publication, as must old nested package checks. Select the current evidence index/logs/JSON/scripts/review screenshots only. The runtime ZIP itself is already allowlisted to 40 files. Parent independent review is still pending; this document is not that review and does not authorize deployment.
