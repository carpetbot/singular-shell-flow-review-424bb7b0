# Model Jury local review build

This is a local review artifact, not a deployment. No real inference was performed. Use your own Singular key only after review and approval of a capped live test.

## Run locally

```sh
python3 proxy.py 8730
```

Open `http://127.0.0.1:8730/#/skills`, select Model Jury, enter the task, then pick three contestant models, a different-maker judge, and a rubric writer. Every model picker has a type-to-filter searchbox and uses exact routable chat IDs from the pricing catalog; mutable IDs ending `-latest` are excluded and rejected by graph validation. Filtering preserves the selected ID, and prices display three significant digits without rounding budget calculations. No default model is assigned. The rubric writer is a separate required picker because the supplied draft did not assign that node a model.

The required numeric run-estimate cap defaults to the draft's $0.25 placeholder. Review the estimate after choosing models. Careful mode adds one judge request with the same labels in reverse order. Estimates are heuristics, not guaranteed billing caps. Failed HTTP calls without usage receipts retain a conservative estimate; missing usage or unpriced actual models stop further calls rather than becoming zero.

Lite shows the winner, best value and folded other answers. Pro reveals the rubric, scores and quotes, receipts, tokens, final slot map and disagreement flags. There is no node-graph visualization. Only the UI view-mode preference is persisted by existing shell behavior; this feature does not save tasks or answers.

Careful-mode scoring follows `shuenrui/singular-flows` specification commit `db27a89a2dd99d80d32017fd0ad6c0eb764912a1`. A must-have failure in either pass counts: the union is ranked below eligible answers and cannot win overall or value. Different must-have sets are flagged with both lists. Invented quotes are judge errors, not answer disqualifications: the affected criterion/pass score is capped at 2, capped pass averages are averaged, quote failures are unioned, and score gaps of 2+ are flagged. Pro retains both judge records.

When both winning cards refer to one answer, the result says “The winner is also the best value.” Failed contestants show their exact model ID and plain gateway/no-answer status in Lite; raw technical errors remain in Pro.

## Scope and compatibility

- New graph engine: `js/graph.js`; new presentation: `js/graph-ui.js`.
- Loader/gallery routing: `js/views/skills.js`.
- New runtime data: `skills/impossibuild__model-jury/`.
- Protected legacy engine, API, store, proxy, and all prior manifests/prompts remain byte-identical to `e064eeb`.
- Exactly four registered code built-ins, no executable manifest code.
- Contestants run concurrently using `Promise.allSettled`; all group estimates are reserved atomically before any request.
- No automatic retries or fallbacks in this minimum graph engine. Invalid rubric/judge JSON stops with the attempted call's receipt retained.
- Graph ordering follows the supplied ordered manifest; this is not a general DAG editor or arbitrary dependency solver.

## Deployment and rollback

Do not deploy this review build without approval. The unchanged server must be restarted by the authorized operator when a future release changes source; a second process on an occupied port is not a deployment. Preserve the approved predecessor ZIP, app directory and exact process command before any future release. Rollback means restoring that approved artifact and restarting the actual listener, then checking the root page, exact static bytes and GET/HEAD denials. No remote target, credentials, publication or deployment is configured by this artifact.

The static server intentionally denies Python source, tests, docs, directory listings and traversal paths. This README is packaged for the reviewer but is not served over HTTP.
