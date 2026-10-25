# Singular Flows — Lite / Pro local review build

**Build only. Not deployed or published. Independent review is required before release.**

## Run locally

Requires Python 3.9+ and a modern browser. From this extracted folder:

```sh
python3 proxy.py 8730
```

Open `http://localhost:8730/`. The landing page is Flows; `/#/skills` remains compatible.
The unchanged proxy binds all interfaces. Keep this server on a trusted machine/network;
do not expose it directly to the Internet. Stop it with Ctrl-C. There are no Node/runtime
package dependencies or build/install steps.

A normal launch fetches the public pricing catalog. Real runs require your own Singular
key and can incur charges. This ZIP includes **no credentials, fixture responses, or sample
outputs**. “Try with sample” fills fictional input only and never starts a run.

Get a key from the public Singular site, then open its Settings. Add it in this shell's
Settings. The existing browser-local key storage and gateway/proxy handling are unchanged.

## Two view levels, one workflow

- **Lite (default):** Flows and Settings, five required context fields, optional “More details”,
  plain-language progress, reviewable draft, two follow-ups, Copy, qualified model-audit status.
- **Pro:** Adds Chat and Models navigation plus the same flow with requested/receipt models,
  selection rationale, referenced inputs/prior outputs, output excerpts, attempts, tokens,
  estimated costs, raw output, original templates and run-context prompt inspection.
- The header switch only changes presentation. It neither restarts a run nor changes models,
  prompts, routing, budgets, results or input values. Preference uses `singular.ui.mode`,
  separate from settings and keys. Research notes and flow results are not persisted.
- “AI check passed — review before sending” is a model audit, **not independent fact checking**.
  Issues and unperformed/failed checks are shown explicitly. No email is sent and no web research
  is performed by this flow. Estimates are not guaranteed billing charges or caps. Small positive
  estimates below 0.01¢ display `<0.01¢`; absent usage remains unknown; skipped steps display —.

## Review scope and limitations

The reviewed engine, API client, proxy, key/state module, every prompt and the legacy Motion
Trimmer manifest are byte-for-byte unchanged. The flow manifest has only optional per-step
`plain_label` and `why` metadata added; all other bytes, exact model/fallback IDs and limits
are unchanged. Selection rationales are supplied copy, not measured performance rankings.

Fonts use external Google Fonts with local/system fallbacks; no new static allowlist paths
or font files are introduced. Offline verification blocks font requests and exercises fallbacks.
This is a restrained interpretation of supplied public production tokens, not a claim to
reproduce the unseen authenticated `/c/new` template ordering or contents.

The separate review report and exactly seven review screenshots document **explicit offline
fixtures only**. No paid inference, real prospect data, key validation, live quality/cost claims,
remote writes, deployment or publication were performed. The review evidence is deliberately
outside the deployable folder/ZIP.

## Handoff / rollback

Start only after independent review and explicit approval. Preserve the existing live package
and process/start configuration before any later deployment. To roll back, restore that exact
previous package and restart the owning process using its approved host procedure. This build
does not change the proxy or prescribe a new hosting/restart mechanism. The previous reviewed
`singular-shell-flow.zip` remains untouched in the source repository.
