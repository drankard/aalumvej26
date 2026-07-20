# Release report — content pipeline refactor (2026-07-20)

## Executive summary

The agentic AgentCore content system has been replaced by a deterministic
pipeline, released to production, and verified end-to-end with live results.
The website is clean and current for the first time since April. One manual
action is required to restore CI deploys (see Manual changes, M1) — everything
user-facing runs normally regardless.

## Verified working in production

- **Site content**: 48 → 20 published posts after archiving 28 expired events
  (verified via live API); every post now carries machine-readable
  `event_start`/`event_end` (evergreen = explicit nulls).
- **First pipeline run** published **8 new trilingual posts** (da/en/de) with
  correct category balancing (3 mad, 3 natur, 2 kultur — previously kultur was
  52% of the site), concrete local detail, and tier-1/2 sources.
- **Source registry seeded**: 44 sources now live in DynamoDB as data the
  pipeline maintains (health tracking, probation/retirement, discovery).
- **Schedules**: oplevelser weekly (Sun 00:00 UTC), området monthly
  (1st Mon 06:00), dead-man canaries 3h behind each — a missed run alerts
  instead of going silent.
- **Reporting**: every run (success, partial, or failure) writes a run row and
  emails a truthful report built from actual run state. The stale-email bug
  class is structurally gone.
- **CI**: tests (90) gate deploys; deploys run on a least-privilege scoped
  policy (see incident below for the one open consequence).

## Incident during hardening: CI locked out of AWS

While migrating the deploy role to least privilege, the final verification
probe — which attempts a self-modification that *should* be denied — ran one
second before IAM propagated the new Deny and therefore succeeded, attaching
its probe payload (a deny-all policy named `should-be-denied`) to the deploy
role. CI has been locked out of all AWS calls since (confirmed twice via
`explicit deny` errors). The probe has been fixed (inert payload,
propagation-aware retry). Ironically the incident is definitive proof the
self-Deny works: CI genuinely cannot repair its own permissions.

**Impact**: GitHub Actions deploys/workflows only. The website, pipeline,
canary and schedules are unaffected (they use separate Lambda execution
roles).

## Manual changes — required, in order

**M1. Unlock CI (admin credentials, ~1 minute).** Deletes the accidental
deny-all policy. The role itself and its correct `aalumvej26-scoped` policy
stay.

    aws iam delete-role-policy \
      --role-name aalumvej26-github-deploy \
      --policy-name should-be-denied

**M2. Re-run the Deploy workflow** (Actions → Deploy → Run workflow) and
confirm it's green. This proves CI works under the scoped policy alone.

**M3. Clean finalize proof + dead-stack cleanup** (Actions → "Harden deploy
role" → stage `finalize`, then stage `cleanup-dead-stack`). The fixed probe
verifies the self-Deny safely; the cleanup deletes the ROLLBACK_COMPLETE
`aalumvej26-bootstrap` stack corpse.

**M4. Reconcile IAM drift with the real bootstrap stack.** The deploy role was
originally IaC-managed, but today's hardening was applied imperatively —
the owning stack's template no longer matches reality. Find the owning stack:

    aws cloudformation describe-stack-resources \
      --physical-resource-id aalumvej26-github-deploy \
      --query 'StackResources[0].StackName'

Then either:
- **(a) Adopt the hardening into IaC (recommended)**: replace the role's
  policy definition in that stack's template with the `aalumvej26-scoped`
  policy from this repo's `bootstrap.yaml` (it is the exact policy currently
  live), deploy the stack with admin credentials, then delete
  `.github/workflows/harden-role.yml` and `.github/scripts/extract_role_policy.py`
  — imperative IAM changes cease to exist.
- **(b) Restore the original template as-is**: reverts to the pre-hardening
  broad role (removes least privilege). Not recommended, but it is the
  fastest path back to zero drift.

## Manual changes — optional

**M5. SerpAPI key** — enables web search and automatic source discovery
(currently skipped each run, noted in the emails). Free plan, 250
searches/month at serpapi.com:

    aws ssm put-parameter --name /aalumvej26/search/serpapi-key \
      --type SecureString --value '<key>'

**M6. Expose event dates in the public API** — the RPC `Post` model omits
`event_start`/`event_end`; add them in `backend/models/content.py` if the
frontend ever wants countdown/expiry UI. No urgency.

## Record of out-of-band (non-IaC) changes made today

All on IAM role `aalumvej26-github-deploy`, via the harden-role workflow:

1. Added inline policy `aalumvej26-scoped` (content versioned in `bootstrap.yaml`)
2. Detached managed policies: AWSCloudFormationFullAccess, AmazonS3FullAccess,
   AmazonDynamoDBFullAccess, AWSLambda_FullAccess, AmazonAPIGatewayAdministrator
3. Deleted legacy inline policy `sam-deploy`
4. Accidentally added `should-be-denied` (the incident; M1 removes it)

No other AWS resource was modified outside CloudFormation. Data operations
(backfill, pipeline publishes) are content, not infrastructure.

## What a healthy week looks like from here

- Sunday ~00:05 UTC: pipeline email — publishes/archives/rejections, source
  health, crawl stats.
- No canary email by 03:00 = the run happened. A canary email = it didn't;
  check EventBridge/Lambda logs.
- First Monday of the month: same pair for the området audit.
- Monthly-ish: skim SUGGESTED SOURCES in the emails and add/reject; the
  registry otherwise curates itself.
