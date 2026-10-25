# Lite / Pro UI — independent review handoff

**Ready for Sofa review; NOT deployed. The live application remains the previously approved engine build.**

## Download and identity

- UI runtime ZIP: `dist/singular-shell-ui.zip`
- SHA256: `d5082c587766932d8da130a8dcef4449d6d31f30191d3c450604e902ad8d8850`
- Extracts to `singular-shell-ui/`; from that directory run `python3 proxy.py 8730` and open `http://localhost:8730/`.
- Source branch: `ui-lite-pro`, based on deployed engine commit `9f5beb17e33a82d67b41ab3085bece985ef1d75c`.
- This branch is published for byte-identical review only, not for production deployment. Do not deploy until Sofa has independently checked it and given go-ahead.

The older `dist/singular-shell-flow.zip`, `SHA256SUMS`, `TEST_REPORT.md`, and `REVIEW-HANDOFF.md` refer to the previous engine build. For this UI review use this document, `UI_TEST_REPORT.md`, `UI_README.md`, and `dist/singular-shell-ui.zip.sha256` instead.

## What changed

- Lite default: Flows and Settings, outcome-led template cards, five required prospect fields, collapsed optional details, fictional sample fill and no-key setup guidance.
- Human-readable four-step progress and draft/follow-ups with Copy. Audit pass is qualified as AI checking and human review is still required; failed/skipped/missing audit is Not checked.
- Pro: same inputs, results and execution; Chat/Models navigation, adjacent flow breakdown, model-selection rationale, dependencies, actual receipt model, fallback and attempt records, tokens/estimated costs, raw outputs and prompt expanders.
- Mode persists separately from key settings. Switching mode mid-run retains inputs/results and produces no extra inference calls.
- Warm near-black styling based on confirmed public Singular design tokens; no claim to reproduce inaccessible authenticated /c/new template contents/order.
- Fixes hidden red banner, readable cost formatting and skipped dashes. Catalog failure recovery and dialog keyboard/focus handling included.

## What did NOT change

Locked engine, API client, proxy, store/key handling, every prompt and Motion Trimmer manifest are byte-identical: 14 file hashes verified. The cold-email flow manifest adds only optional step plain_label/why metadata. Removing those additions restores the original manifest bytes. All models, fallbacks, budgets, token limits and timeout are unchanged. The original reviewed deployment ZIP is unchanged.

## Independent reproduction

The repository root contains test source and public pricing/offline fixtures; the runtime ZIP intentionally does not. Requires Node for its built-in test runner, Python 3.9+ for the runtime and Python Playwright plus installed system Chromium for browser checks. No real API key is required. Browser fixtures block external requests, including Google Fonts, so screenshots exercise system font fallbacks.

```sh
node --test tests/*.test.mjs
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p 'test_*.py' -v
PYTHONDONTWRITEBYTECODE=1 python3 reports/verify_ui_integrity.py
PYTHONDONTWRITEBYTECODE=1 python3 reports/verify_ui_package.py
PYTHONDONTWRITEBYTECODE=1 SINGULAR_UI_APP_ROOT="$PWD/dist/singular-shell-ui" python3 -m unittest discover -s tests -p test_lite_pro.py -v
```

Run from the repository root. These commands exercise offline fixtures, local loopback HTTP, ZIP CRC/byte checks and locked-source scope. A normal manual browser launch outside those tests fetches live public pricing; entering a real key and clicking Run may spend money, which is not authorized as part of this UI review.

## Executed checks

Parent independently reran 23 Node tests, 12 Python tests (including 9 Lite/Pro real Chromium acceptance tests), locked-file verification, package GET/HEAD checks and git diff --check; all passed. The child also replayed the 9 acceptance tests against the extracted runtime ZIP; see UI_TEST_REPORT.md for original evidence and explicit fixture disclosures. Parent inspected all seven screenshots.

## Exactly seven screenshots

All captured against the extracted ZIP in Chromium. Desktop 1440x1000; mobile 390x844. Completed drafts and in-progress requests are explicitly offline fixtures, not real model quality, cost, latency or billing measurements.

1. `reports/review/01-lite-gallery.png`
2. `reports/review/02-lite-form.png`
3. `reports/review/03-lite-completed-result.png`
4. `reports/review/04-pro-gallery.png`
5. `reports/review/05-pro-form-breakdown.png`
6. `reports/review/06-pro-completed-breakdown.png`
7. `reports/review/07-mobile-lite-form-progress.png`

Viewport/state disclosures and image checksums are in `reports/review/screenshots.json` and `reports/review/SHA256SUMS`.

## Feedback requested

Sofa: confirm ZIP fingerprint and independent tests; inspect gallery/form/results in Lite and Pro, mode switching before/during/after a run, no-key/sample behavior, audit pass/fix/not-checked distinctions, receipt/fallback/unknown/skipped displays, mobile keyboard/scrolling, and unchanged execution scope. Post your verdict and blockers before deployment.

Shuenrui: visual direction is ready for feedback; this is a review build, not the live restyle. Real inference quality, pricing/usage compatibility and account billing still need the separate approved capped-key test.
