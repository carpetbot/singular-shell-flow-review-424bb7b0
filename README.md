# Singular community shell — ordered flows

Plain browser ES modules plus the existing Python same-origin proxy. No build step and no added runtime package dependencies. The v0.1 Motion Trimmer manifest and prompt remain unchanged.

## Local use

Requires Python 3.9+ (verified here with 3.12.3). Run `python3 proxy.py 8730` from this folder and open `http://localhost:8730/#/skills`. The proxy's existing command binds all interfaces; use firewall/reverse-proxy access controls rather than exposing this development server directly to the Internet. Opening the shell normally fetches gateway pricing; running a skill requires the user's own browser-held API key. No key is included in this delivery.

## Prospect → Cold Email

Paste your notes about one prospect, your offer/proof, sender name, and desired ask. The four ordered steps pull quoted facts, select an angle, write one email and two follow-ups, then audit factual support and tone. Extraction distinguishes quoted signals from **inferred** likely problems; a quote does not establish an inferred problem as fact. An angle below fit score 3 stops cleanly and skips drafting/checking. Human review remains necessary even when the audit says pass.

This flow does **not** browse the web, verify source material externally, or send email. The exact model IDs and prompt text were supplied in the brief. The recorded unauthenticated public catalog lists all required models as routable and supplies prices; actual paid inference, availability, JSON-format support, and billing were **not live-tested**. No paid requests were made.

## Execution contract

- Gallery loader tries `singular.flow.json`, then `singular.skill.json` **only on HTTP 404**. Other manifest/prompt failures are surfaced rather than treated as templates. Inline system/user prompts are not fetched. Loaded prompts are attached to the manifest so both the card/openRunner path and legacy runner receive them.
- Templates accept whitespace and dotted paths, including `steps.<id>.output`. Missing values render empty. Only own properties are traversed; prototype-related keys are forbidden. Both system and user templates render from prior **raw** output strings, not reformatted JSON.
- All primary/fallback models must be explicit provider/model IDs, never `auto` or routing aliases. Steps execute serially, with waiting/running/done/failed/skipped notifications. A step stores raw output, parsed JSON (or null), last receipt and every attempt receipt.
- JSON fences are stripped before parsing. Invalid JSON gets one retry on the same model with `Return valid JSON only.` appended. A second invalid JSON response fails the step and skips later steps. **JSON failure alone never triggers a fallback.** This follows the final brief, superseding the earlier suggestion to fall back on JSON errors.
- HTTP failures use the ordered fallback IDs. Authentication/authorization/balance failures stop without trying more models. A fallback model gets its own one-repair allowance. All attempts, including invalid JSON and HTTP errors, remain in the cost record.
- Flow JSON requests send only the existing request fields plus `response_format: {"type":"json_object"}`. A browser AbortSignal is passed to fetch for the run deadline; it is not an API body option. The run deadline defaults to, and is capped at, 180 seconds.
- The panel previews only the first step; shows model/status/attempt token totals and estimates; renders configured nested JSON output paths as escaped plain text with Copy buttons; and provides an expandable all-step raw-output/attempt view.

## Cost estimates, not billing enforcement

`max_cost_per_run_usd` is a **client-side estimate ceiling, not an exact or gateway-enforced billing cap**. Gateway usage receipts provide token counts, not proof of billed charges. Catalog prices, tokenizer differences, hidden provider work, timeout behavior, and actual bills can differ.

Preflight requires known finite nonnegative **numeric** input/output pricing for every primary and fallback. It sums the **normal route: one primary call per step**, using each step's maximum output allowance (`max_output_tokens || 2048`). Estimated input tokens are `ceil(UTF-8 bytes / 4) + 128` framing tokens per call. Prior output placeholders use **4 bytes per allowed output token**, with every repeated downstream reference counted separately. Conditional JSON repairs and mutually exclusive fallback paths are not reserved in advance; their prices are validated up front and each actual attempt must pass the per-call guard. These are documented heuristics, not tokenizer guarantees. The recorded public catalog (`as_of: 2026-10-24T16:56:21.780Z`) gives **$0.020897823799080003** for the small Sample/hiring input in `reports/preflight-acceptance.json`: four offline calls complete at the unchanged $0.10 ceiling; $0.001 blocks before any call.

Before every call, another estimate is compared with the remaining ceiling. After every response, actual reported token usage is priced from the catalog and accumulated, including repairs. If accumulated cost exceeds the ceiling or becomes unknown, execution stops before another call. Missing pricing/usage is **unknown, never zero**. HTTP error attempts without usage get a clearly labeled conservative per-call estimate; transport failures/timeouts without a receipt have unknown cost and stop the flow. Aborting the browser request cannot guarantee cancellation or prevent an upstream charge already in progress.

The legacy runner retains its original separate per-call estimate behavior; this flow ceiling must not be read as upgrading legacy billing guarantees.

## Static serving and deployment handoff

Only the shell HTML/CSS, JS modules, skill manifests, and skill prompt Markdown are publicly served. All `.py` source, tests, docs/reports, archives, hidden paths, traversal, directory listings, and symlinks are denied for static GET and HEAD, including encoded paths and query strings. Keep the proxy as the entry server; a different web server must enforce the same allowlist. Do not serve the repository with an unrestricted generic static server.

`dist/singular-shell/` and `dist/singular-shell-flow.zip` are deployment handoff artifacts, **not a deployment**. The production folder/archive contains source, exact prompts, this README, deployment notes and the test report; tests and browser screenshots are excluded. Tests remain in this working tree for reproducibility. No remote writes or contacts were made. Deployment remains Alice's responsibility.

## Tests

- `node --test tests/flow.test.mjs` — Node built-in runner; offline injected chat/catalog/fetch fixtures only.
- `python3 -m unittest discover -s tests -p test_proxy.py -v` — actual GET/HEAD requests to an ephemeral loopback Python server, no gateway requests.
- `python3 -m unittest discover -s tests -p test_ui.py -v` — optional real Chromium smoke via Python Playwright and system `chromium`. Pricing/chat responses are explicitly offline browser route fixtures. External requests are blocked. Requires `playwright` and installed system Chromium; production does not.

See `TEST_REPORT.md` and `reports/` for executed results and the red-green tracer-bullet ledger. Live model/gateway integration, real billing accuracy, output quality, broad device/accessibility testing, and production reverse-proxy/TLS setup remain outstanding.
