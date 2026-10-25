# Deployment notes — handoff only

**Owner: Alice. Nothing has been deployed.** No real API/model availability or billing test has been performed. This folder is a local handoff artifact, not a production-readiness certification.

## Contents

- `index.html`, `styles.css`, `js/`: plain browser application source.
- `skills/claw__motion-trimmer/`: original v0.1 skill.
- `skills/impossibuild__prospect-to-cold-email/`: supplied four-step flow manifest and all eight exact prompt files.
- `proxy.py`: required same-origin gateway proxy and static allowlist server.
- `README.md`, `TEST_REPORT.md`: behavior, cost limits, executed tests and outstanding live checks.

Tests and browser screenshots deliberately remain outside the production folder/archive. They are in the working source folder alongside `reports/`. No API keys, credentials, environment files or dependencies are bundled.

## Local validation of this folder

From the folder, run `python3 proxy.py 8730`, then open `http://localhost:8730/#/skills`. The default server binds all interfaces. Use only a trusted environment; do not expose the raw development server to the Internet. A normal startup fetches live gateway pricing; clicking Run with a real key may incur paid usage. The recorded public pricing snapshot was fetched without credentials; all chat tests used offline responses, not live inference.

Before any authorized release, Alice should:

1. Review source, manifest and exact prompts against the brief; retain the existing shell and Motion Trimmer route.
2. Put the Python application behind appropriate HTTPS, authentication/access controls and a reverse proxy. Do not replace it with unrestricted directory serving. Preserve static GET/HEAD denial for Python, tests, docs, archives, hidden paths, symlinks and directory listings.
3. Confirm the supplied exact primary/fallback model IDs exist and are routable, and that `/pricing.json` has the required numeric prices. Missing or unknown prices intentionally prevent flow execution.
4. Review the normal-route estimate and per-call retry/fallback guards with refreshed catalog prices. Preflight counts one primary call per step, input bytes/4 plus framing, output limits (default 2048), and every repeated downstream reference at 4 bytes/output token. It validates all fallback prices without reserving all mutually exclusive paths. The recorded public catalog yields $0.020897823799080003 for the small Sample/hiring input at the unchanged $0.10 ceiling; $0.001 refuses before any chat call. This is not a guaranteed billing cap. Every repair/fallback must fit accumulated receipt estimates plus its next-call estimate.
5. Only with explicit authorization for paid testing, exercise one real notes-to-email run, same-model JSON repair and HTTP fallback; inspect every usage receipt, actual model, token total and subsequent account charges. Confirm that `response_format` is honored. Timeout/cancellation cannot guarantee cancellation of upstream billing.
6. Review factual claims and inferred problems manually. This tool drafts text; it does not independently research prospects or send email.
7. Test mobile/responsive layout, keyboard/focus behavior, clipboard permissions, production reverse-proxy behavior and supported browsers. The executed UI smoke was Chromium desktop on loopback with offline API fixtures.

## Alice's deployment commands (not executed)

Obtain Shuenrui's approval to replace the live deployment. Extract the archive and enter its `singular-shell/` folder. Confirm the owning Pro account with `innstance status --json`, back up the current `/app` files and startup configuration, and arrange a rollback before replacement.

From the local extracted folder:

```sh
innstance machines push --app singular-shell . --to /app --yes-replace
```

On the app machine, stop or restart the existing listener through the established service mechanism first; starting another listener on occupied port 8080 will not activate this build. Then, if no service manager is configured, use the handover's start command:

```sh
cd /app && setsid nohup python3 proxy.py 8080 </dev/null >/tmp/app.log 2>&1 &
```

After deployment, check the live root and flow manifest return 200; check GET and HEAD `/proxy.py` return 404; open both gallery cards in a browser and confirm no import errors. Do not run paid inference without the approved capped key. The startup command is not a machine-reboot persistence fix.

Rollback is a deployment-owner operation: restore the prior shell artifact/configuration and restart its listener. This task made no remote writes and no commits.
