# Concurrent-poll lost-update fix — offline evidence

## Scope and implementation

Only production code changed in this follow-up: `js/video.js` save reconciliation and the post-save polling terminal decision. Under the existing exclusive Web Lock, reread the latest same-token recovery record; reject mismatched creating key, plan/version, request hash or already-known job ID. Keep persisted completed/failed state against a conflicting delayed observation, preserve an existing settled receipt and original quote, retain prior recovery metadata/history, and restore the caller to the reconciled record. Polling returns the reconciled terminal status rather than continuing from a delayed processing response. Explicit new-version identity generation remains unchanged.

Tests changed: `tests/video-cross-tab.test.mjs`. Handoff documentation changed: `MOTION_VIDEO_REVIEW.md`. Existing proxy source/checks and legacy request builders were not edited by this follow-up. Production duration/aspectRatio/audio remain null; real generation is still disabled.

## Strict red/green evidence

- `red.log`: before the fix, the two-session delayed processing reproduction failed for both completed and failed: terminal status and settled charge were overwritten; failure error was erased.
- `green-persistence.log`: both terminal storage/caller/onChange/download/new-version assertions passed after locked reconciliation.
- `red-return.log`: the next assertion exposed that polling still continued from its stale response rather than returning the reconciled terminal state; both terminal cases failed as intended.
- `green.log`: post-save polling now returns terminal truth; all seven tests at that stage passed.
- Additional regression coverage checks same-terminal unknown-cost observations, settled receipt/quote/prior metadata preservation, strict identity mismatch rejection, and delayed old-version updates leaving a distinct newer identity/history intact. Existing stale-create retry checks retain identical request bytes and idempotency token. Creation already holds the same exclusive lock over its POST; no separate unlocked concurrent create path was introduced.

## Final regressions

- `node.log`: `node --test tests/*.test.mjs` — **83 passed, 0 failed**.
- `python.log`: `python3 -m unittest discover -s tests -p 'test_*.py' -v` — **42 passed, OK**, including real Chromium two-tab tests and loopback proxy/media checks. Evidence directories were precreated beneath this repository; VIDEO_EVIDENCE/VIDEO_LITE_EVIDENCE/VIDEO_LEGACY_EVIDENCE/VIDEO_JURY_EVIDENCE all point into this isolated report tree.
- `legacy-compare.log`: captured actual offline POST bodies against base 378d6f4: cold email 4, old Motion Trimmer 1, Model Jury 5 — all byte-structure equal; 29 protected files byte-identical. Captured bodies and hashes are adjacent.
- `git diff --check` passed. `source-hashes.json` includes final runtime/test/doc/archive hashes. Null production field map and disabled-generation gate checked directly.

## Final local package

Rebuilt once after final runtime and README edits using the existing explicit allowlist packager, with its REPORT path redirected to this isolated directory. `package-verification.json` / `package.log`: **40 files**, ZIP CRC PASS, every ZIP/copy/source byte comparison PASS, **24 copied-server GET/HEAD probes PASS**. Reports/tests/private pricing are not packaged. The ZIP was not modified after this build.

- Archive: `dist/motion-trimmer-video-review.zip`
- SHA256: `89032c442e2726c60084378462cc4da9616d77ce3b4f614c50386cf0f976fa59`
- Sidecar: `dist/motion-trimmer-video-review.zip.sha256`
- `sha256sum -c motion-trimmer-video-review.zip.sha256` from `dist/`: OK.

The first sidecar command was invoked from the repository root and could not resolve its basename archive entry; rerunning from `dist/` passed. This was a verification working-directory error, not a package failure.

No commit, push, deploy or paid inference was performed. The inference/media replies in these tests are explicitly offline fixtures. Live adapter/charge acceptance remains blocked and unperformed; independent parent review remains required.
