# Applying the deploy-role policy

`deploy-role-scoped.json` is generated from `bootstrap.yaml` and exists so the
policy can be applied from a browser, with no CLI. Regenerate it after any change
to `bootstrap.yaml`:

    python3 .github/scripts/extract_role_policy.py <account-id> --without-boundary

## Why this is a manual step

Nothing applies `bootstrap.yaml`. The live role is not CloudFormation-managed —
the `aalumvej26-bootstrap` stack is a ROLLBACK_COMPLETE corpse — and the role
carries an explicit Deny on `iam:PutRolePolicy` against itself, so CI cannot
apply it either.

That Deny does **not** restrict a human admin. An identity-based Deny only
applies when that role is the principal making the call. Acting under your own
admin identity, you can edit the role normally.

## Steps (AWS Console, no CLI)

1. IAM → Roles → `aalumvej26-github-deploy`
2. Permissions tab. Note what is attached — there should be an inline policy
   named `aalumvej26-scoped`. If a legacy `sam-deploy` inline policy is also
   present, leave it alone for now; it is additive and removing it is a separate
   decision.
3. Open `aalumvej26-scoped` → Edit → JSON.
4. Replace the entire document with the contents of
   `.github/policies/deploy-role-scoped.json`.
5. Save.

If the explicit Deny on self-modification lives inside `aalumvej26-scoped`,
replacing the document removes it as a side effect. That is acceptable — it
closed no real escalation path (see `README.md` in this folder) — but note it
happened, because it changes whether CI could self-sync in future.

## Deliberately excluded

This document has **no** `iam:PermissionsBoundary` conditions. They reference a
managed policy that does not exist yet, and applying them first makes every
`CreateRole` fail, which rolls back the whole deploy. The boundary rollout is a
separate, later sequence documented in `README.md`.

## After applying

Set these repository variables one at a time, confirming a green deploy between
each (Settings → Secrets and variables → Actions → Variables):

| Variable | Value | Unlocks |
| --- | --- | --- |
| `ENABLE_CONTENT_REBUILD` | `true` | content-pipeline runs republish the site themselves |
| `ENABLE_ACCESS_LOGS` | `true` | CloudFront logs — the only view of AI-crawler traffic |

Then re-run the Deploy workflow. Do not set both in one run: each needs a
permission that has to land before the stack asserts it.
