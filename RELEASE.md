# Release checklist — content pipeline refactor

All steps run through GitHub Actions (only CI has AWS credentials). Do them in
order; each is idempotent and safe to re-run.

## 1. Merge this branch to `main`

- `Test` runs (backend pytest + frontend build).
- `Deploy` runs automatically. **It may fail at changeset execution** with an
  IAM error — the deploy role gains its new permissions in step 2. That's
  expected; nothing is partially applied (CloudFormation rolls back).

## 2. Actions → "Update bootstrap (deploy role)" → Run

- Input: the real name of the bootstrap CloudFormation stack (default guess:
  `aalumvej26-bootstrap` — check the CloudFormation console if unsure).
- Grants the deploy role: SQS (queue delete/create), CloudWatch alarms, and
  `bedrock:InvokeModel` (used by the backfill).

## 3. Actions → "Deploy" → Run workflow (if step 1's deploy failed)

The release changeset:
- creates `aalumvej26-content-pipeline-prod`, `aalumvej26-pipeline-canary-prod`,
  canary schedules, `aalumvej26-pipeline-dlq-prod`, pipeline error alarm
- retargets the two content schedules to the pipeline Lambda
- deletes the AgentCore runtime + role, invoker, notifier (+2 queues), validator
  (+1 queue), and their alarms

## 4. Create the SerpAPI key (one-time, optional but recommended)

Sign up at serpapi.com (free plan, 250 searches/mo), then store the key —
console → SSM Parameter Store:

- Name: `/aalumvej26/search/serpapi-key`
- Type: `SecureString`

Without it the pipeline still runs; search/source-discovery is skipped and the
email says so each run.

## 5. Actions → "Backfill event dates (one-off)"

1. Run with `apply=false` → read the plan in the job log (expect ~31 archives
   of expired March–June posts, ISO dates stamped on everything).
2. Run with `apply=true` → the live site is clean.

## 6. Actions → "Run content pipeline (manual)" → `oplevelser`

First real run. Expect in the email (arrives in ~5–10 min):
- "Source registry seeded with 44 sources" in NOTES (first run only)
- crawl stats over tiers 1/2/4, candidates, publishes with concrete titles
- possibly NEW/SUGGESTED SOURCES if the SerpAPI key is in place

Verify aalumvej26.dk shows fresh content and no expired events.

## 7. Confirm the safety net

- CloudWatch: `aalumvej26-content-pipeline-errors-prod` alarm exists, OK state.
- EventBridge: 4 enabled rules (2 pipelines, 2 canaries).
- Next Sunday: pipeline email ~00:00 UTC; silence + no canary alert by 03:00
  means healthy. A canary email means the run never happened — that is the
  alert this design guarantees.

## 8. Aftercare (optional)

- Remove the `bedrock-agentcore:*` statement from `bootstrap.yaml` (only needed
  to delete the legacy runtime) and re-run the bootstrap workflow.
- Watch 2–3 weekly emails: if candidate counts run thin, the SUGGESTED SOURCES
  section and gap-driven queries are the tuning knobs (`search.py`).

## Rollback

`git revert` the merge commit and push — Deploy restores the previous stack
(the AgentCore runtime is recreated from the still-present S3 artifact
parameters in the old template; posts/areas data are untouched throughout).
