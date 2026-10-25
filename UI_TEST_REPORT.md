# Singular Lite / Pro — local UI review report

**Status: built and locally verified; not deployed or published. Independent Sofa review is next.**

## Review delivery

- Source: `/home/orangepi/projects/singular-shell-ui`, branch `ui-lite-pro`.
- Reviewed baseline: `9f5beb17e33a82d67b41ab3085bece985ef1d75c`.
- Deployable ZIP: `dist/singular-shell-ui.zip` — **41,008 bytes**, 27 files.
- SHA256: `d5082c587766932d8da130a8dcef4449d6d31f30191d3c450604e902ad8d8850`.
- Extracted runnable folder: `dist/singular-shell-ui/`.
- Start instructions: `UI_README.md` (included as the bundle's `README.md`).
- The predecessor ZIP `dist/singular-shell-flow.zip` is untouched. SHA256 remains
  `563fff6a88d1fd70e35d3c541cd21129fee68e50acfe7e6d6532177ef661f6a2`.

## Exactly seven review screenshots

All screenshots were generated in real headless `/usr/bin/chromium` through Python Playwright,
against the **extracted runtime package** on loopback HTTP. Desktop is 1440 × 1000;
mobile is 390 × 844. The files were visually inspected. `reports/review/screenshots.json`
records each viewport, mode and fixture disclosure.

1. `reports/review/01-lite-gallery.png` — default outcome-first template track.
2. `reports/review/02-lite-form.png` — fictional sample, no-key guidance, required context,
   collapsed optional details.
3. `reports/review/03-lite-completed-result.png` — qualified model audit, subject/body,
   two follow-ups, Copy and readable estimated cost.
4. `reports/review/04-pro-gallery.png` — additional navigation and template identifiers.
5. `reports/review/05-pro-form-breakdown.png` — Configure primary, adjacent Pro inspector;
   exact models, selection rationale, references and original prompt expanders.
6. `reports/review/06-pro-completed-breakdown.png` — the same completed result beside
   step receipts, output excerpts and prompt/raw-output expanders.
7. `reports/review/07-mobile-lite-form-progress.png` — lower form and four human-readable
   progress states, captured with the first offline request deliberately paused.

**Every completed result and running state uses explicit offline gateway fixtures.**
No real model generated these drafts or audited them. The fictional input and model replies
live in tests only; no fake result is embedded in the app. Fixture usage is 15 input / 20 output
tokens per successful response, so screenshot estimates are not claims about typical live cost.
The production sample button fills fictional input only, never sends or runs it.

## What changed

- Singular's supplied warm near-black tokens, restrained hierarchy, Manrope/Geist/IBM Plex Mono
  font declarations and fallbacks; 260px horizontal template cards, keyboard affordances,
  responsive controls, reduced motion and visible focus.
- Lite defaults to Flows + Settings. Pro adds Chat + Models. Direct Chat/Models routes in
  Lite resolve to the gallery without inference. The switch uses `singular.ui.mode`, outside
  settings/key storage, and does not rerender the active form.
- Five required prospect fields remain visible; role, proof and ask are under More details.
  Fictional sample inputs are explicitly labelled. Without a key, the form stays usable,
  Run is disabled, and links point to the real Singular root → Settings and shell Settings.
- Both Motion Trimmer and Prospect → Cold Email remain available; legacy preview/run is
  regression-tested in Pro. The execution code path is shared by Lite and Pro.
- Lite preserves stop/error messages and next actions, unknown cost and skipped dashes.
  Pass audit text is only **“AI check passed — review before sending”**, never an unqualified
  factual-verification claim. Fix issues and failed/skipped/unknown checks are distinguished.
- Pro preserves the Lite result and exposes all step cards with arrows, exact requested models,
  supplied selection rationales, prior-output references, receipt/fallback model information,
  output excerpts, accumulated tokens/attempts/estimates, raw output, original templates and
  rendered run-context base prompts. Keys are redacted in dynamic inspection output.
- Hidden catalog banner now stays hidden; an initial pricing-fetch failure shows recovery guidance. Catalog/status strings and context values are escaped;
  absent catalog data has a recovery view instead of a broken skeleton/null-element handler.
- Modal focus/keyboard navigation, Escape and return focus are managed; header Lite/Pro remains
  usable while background navigation is inert. Mobile tested at 390px with 44px mode controls.

### Source scope

Production presentation files modified:
`index.html`, `styles.css`, `js/app.js`, `js/chrome.js`, `js/ui.js`, `js/flow-ui.js`,
`js/views/skills.js`, `js/views/settings.js`, `js/views/models.js`.

New presentation module: `js/presentation.js`. Production-only diff, including the new module:
`reports/ui-production.diff`. Screenshot checksums: `reports/review/SHA256SUMS`.
Only `steps[].plain_label` and `steps[].why` were added to the Prospect flow manifest.
New tests, build/integrity/package scripts, logs, report and seven screenshots are outside
production. Existing smoke assertions are retained; the smoke now selects Pro for preview/raw
inspection and expects the corrected qualified audit UI.

## Locked-scope verification

`python3 reports/verify_ui_integrity.py` passed:

- All **14 locked files** match the reviewed commit and the before-edit SHA256 baseline.
- `js/flow.js`, including the numeric-string fit-score fix, is byte-for-byte unchanged.
- `js/api.js`, `proxy.py`, `js/store.js`, every existing prompt and the complete Motion Trimmer
  manifest are byte-for-byte unchanged.
- Removing the two allowed optional metadata fields makes the entire flow manifest both
  semantically equal **and byte-for-byte equal** to the original. Exact model/fallback IDs,
  prompts, caps, limits and all other metadata are untouched.
- The original source `/home/orangepi/projects/singular-shell` and published-artifact repository
  were not modified. No new runtime dependencies or proxy allowlist paths were introduced.

Full hashes: `reports/ui-locked-baseline.json` and `reports/ui-integrity.txt`.

## TDD tracer bullets and evidence

New behavior was introduced in small end-to-end RED → GREEN slices rather than a single
implementation followed by a smoke test. The logs retain expected failures before changes:

| Slice | RED observed | GREEN evidence |
|---|---|---|
| View-level default/persistence/nav/route guard | no `data-mode=lite` | `ui-mode-red.txt` → `ui-mode-green.txt` |
| Outcome gallery + fictional form/no-key/toggle retention | card was DIV rather than keyboard button | `ui-form-red.txt` → `ui-form-green.txt` |
| Readable cost + qualified audit/error result | exponential cost and missing qualified audit | `ui-result-red.txt` → `ui-result-green.txt` |
| Pro receipt/template/reference inspection | missing breakdown | `ui-pro-red.txt` → `ui-pro-green.txt` |
| Human step labels + pre-run inspector + in-flight toggle | original labels instead of approved plain labels | `ui-running-red.txt` → `ui-running-green.txt` |
| Mobile/accessibility/Lite settings/legacy no-key surface | 38px mode target instead of 44px | `ui-accessible-red.txt` → `ui-accessible-green.txt` |
| Untrusted status/catalog and missing-catalog recovery | injected IMG and persistent skeleton | `ui-safety-red.txt` → `ui-safety-green.txt` |
| Readability refinement after visual inspection | tiny over-precise cents and narrow/nonadjacent inspector | `ui-readability-red.txt` → `ui-readability-green.txt` |
| Failed first-load pricing status | initial catalog failure left the banner hidden | `ui-boot-banner-red.txt` → `ui-boot-banner-green.txt` |

Logs are under `reports/`. Preservation checks and additional fixture coverage intentionally
remain green regression guards, not claims that existing engine functionality was rebuilt.

## Final verification output

### Node

```text
node --test tests/*.test.mjs
ℹ tests 23
ℹ pass 23
ℹ fail 0
ℹ skipped 0
```

Includes all original 20 tests plus three presentation tests. The unchanged engine's
ordered chaining, public-price/default-cap preflight, budget guards, string fit-score stop,
repair/fallback accounting and unknown-usage behavior remain covered.

### Python / real Chromium

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p 'test_*.py' -v
Ran 12 tests in 36.044s
OK
```

Includes the original two proxy tests and legacy/flow browser smoke, plus nine Lite/Pro
acceptance tests. Browser assertions cover default/persistence/guarded routing, no-key sample
with zero calls, optional disclosure, input/result retention across mode changes, a deliberately
paused in-flight request with no duplicate calls, four-step pass, legacy/fix/stop paths, clipboard,
escaping, fallback receipt model with two attempts, unknown usage stopping further calls, check
failure preserving the draft as Not checked, mobile geometry/focus, and the seven review shots.

### Extracted-package Chromium replay

```text
PYTHONDONTWRITEBYTECODE=1 SINGULAR_UI_APP_ROOT=/home/orangepi/projects/singular-shell-ui/dist/singular-shell-ui \
  python3 -m unittest discover -s tests -p test_lite_pro.py -v
Ran 9 tests in 30.385s
OK
```

### Archive / packaged HTTP

```text
PYTHONDONTWRITEBYTECODE=1 python3 reports/verify_ui_package.py
ZIP CRC passed; source/extracted/ZIP byte equivalence: 27 files
Packaged proxy: GET/HEAD public files: 25; GET/HEAD denied paths: 11; root 200
No gateway requests.
```

The ZIP excludes tests, fixtures, reports, screenshots, logs, secrets, caches and nested archives.
Static verification serves every expected JS module/prompt/manifest via the unchanged proxy,
and checks source, docs, tests, reports, archives, directory and traversal denial. `git diff --check`
also passed. Full final outputs are `ui-node-final.txt`, `ui-python-final.txt`,
`ui-packaged-browser.txt`, `ui-package-verification.txt` and `ui-build.txt`.

## Visual review / remaining decisions

- Surface choice: Explore gallery; Configure runner; Inspect secondary in Pro.
- Self-audit: **0/10 design-slop tells** after refinement; no gradients, generic icon-topper tiles, accent rails, blur/glass, fake metrics,
  centered marketing hero or new decorative icon system. System fallback typography is visible
  in offline screenshots because all external requests (including fonts) are blocked.
- All seven screenshots were inspected for hierarchy, reading order, controls and viewport fit.
  The inspector was widened and moved adjacent to Configure after the first review; tiny cost
  precision was reduced without showing positive usage as zero. Native panel scrolling remains
  necessary for long prompts, all four inspection cards and mobile forms; it is not hidden data.
- The supplied public tokens inform the treatment. Authenticated `/c/new` content/order was
  not visible, so exact reproduction of that unseen page is **not claimed**.
- Receipt model is a gateway echo when provided, otherwise the unchanged API's requested-model
  fallback. Base run-context prompts are reconstructed from actual inputs/prior outputs; conditional
  repair message history is not stored by this runtime and is not invented in the UI.
- Live model output quality, factual reliability, real latency, key validation and billing were
  **not tested**. Estimates and the supplied model-selection rationales are not benchmark claims.
- Next: Sofa independently reviews this ZIP and the seven files; parent handles any approved
  downloadable review handoff. No deployment, publication, remote writes or paid API calls occurred.
