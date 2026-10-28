# Checkpoint 2 final narrow evidence-identity correction

Base: `a3b2ca6078311d2fec776f07a0a060e3f95b57d6`.

## Outcome

The same-session add-abort/replan blocker reproduced before the fix: brief A's
saved token, version and body were reused, but the durable row contained brief B's
inputs. The offline planner deliberately returns the same video prompt for both
briefs. Reload-only draft binding did not protect the mutable same-session draft.

- `video-runtime.js`: only the engine's initial insert may bind a planner snapshot.
  Retries do not rewrite the current draft request or rebind its planner row.
  Persistence resolves the original exact token/version/body-bound durable snapshot,
  checks the canonical request SHA256, and uses its brief, plan, prompt and receipts
  for render creation/enrichment. Missing original evidence with a planner draft
  fails closed. Neither current `draftId` nor matching prompt alone grants ownership.
- `video-ui.js`: Plan is disabled and its handler refuses planning while a submission
  is selected or any retained submission is unresolved. Terminal jobs require the
  explicit Make another version action before planning. Identical retry and Resume
  remain available as appropriate. The visible note explicitly states closing the
  view is not cancellation and explains terminal/new-version recovery.
- Two real-Chromium regressions cover the precise same-document sequence and a
  runtime-only bypass with an unrelated same-body draft. Before the one retry POST,
  the durable row must contain original inputs, receipts, outputs and identity.
  The unrelated draft must not acquire the old render identity. The UI case also
  checks a forced handler call makes no extra planner request, pending new-version
  remains disabled, and terminal explicit new-version unlocks planning without an
  extra video POST.

## Verification

All model/video responses are explicit loopback fixtures. Tests use real
`/usr/bin/chromium`, IndexedDB transactions and Web Locks; non-loopback browser
requests are blocked. No live key, inference, push, deployment or packaging.

Evidence in this directory:

| Log | Result |
| --- | --- |
| `c2-narrow-replan-red.log` | Before fix: durable row inputs contain unrelated brief B instead of original brief A |
| `c2-narrow-runtime-red.log` | Before fix: runtime-only retry similarly attaches unrelated brief B |
| `c2-narrow-green.log` | Both new regressions plus existing reload/changed-prompt protections: 4 passed |
| `c2-narrow-node-full.log` | Full Node suite: 98 passed, zero failures/skips |
| `c2-narrow-python-full.log` | Full Python suite: 87 passed, zero failures/skips; includes 19 durable-video and 13 run-store cases |
| `c2-narrow-protected.log` | Engine, run-store and all prompts/manifests unchanged against base; added-line security scan clean; tested isolated source equals working source |

Commands:

```sh
# Repository root
PYTHONPATH=tests python3 -m unittest test_durable_video_browser.DurableVideoBrowser.test_same_session_replan_after_add_abort_preserves_bound_evidence -v
PYTHONPATH=tests python3 -m unittest test_durable_video_browser.DurableVideoBrowser.test_runtime_retry_ignores_new_draft_with_same_body_after_add_abort -v
node --test tests/*.test.mjs
# Ignored reports/a2/regression-app/narrow copy of runtime/tests/skills/catalog
python3 -m unittest discover -s tests -p 'test_*.py' -v
# Repository root
git diff --check
```

The final Python suite ran in an ignored isolated app copy so legacy screenshot
and wire-report writes did not replace prior reviewer evidence. Final full-suite
source includes the strengthened terminal Plan-lock assertion and visible recovery
note. Existing IDB identity/enrichment rules and frozen engine behavior are unchanged.

Limits remain: absent original evidence cannot be reconstructed, closing is not
cancellation, and an unresolved no-id submission cannot be discarded as a new
version. No card polish or A3 work is included.
