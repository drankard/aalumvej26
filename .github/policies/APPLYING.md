# Applying the deploy-role policy

> **CURRENT STATE: the deploy role carries `AdministratorAccess`.**
>
> Least privilege cost three rolled-back deploys and was blocking the actual
> work, so it was set aside deliberately rather than by neglect. The scoped
> policy in `deploy-role-scoped.json` remains the target to return to, and
> `boundary.json` remains the control that would make returning safe.
>
> This is a real exposure and worth stating plainly: the role is assumable by
> GitHub Actions on `refs/heads/main`, so anything that executes during a build —
> including a compromised npm or pip dependency — reaches the whole AWS account.
>
> It is a smaller step than it appears. Before this, the role already held
> `iam:CreateRole` and `iam:AttachRolePolicy` with no constraint on which policy
> could be attached, plus `iam:PassRole` to Lambda: create a role, attach
> `AdministratorAccess`, pass it to a function. The escalation path was already
> open. This makes it explicit instead of latent.
>
> To undo: attach the scoped policy below, detach `AdministratorAccess`, then run
> `harden-role` with `stage=create-boundary` and enable `ENFORCE_BOUNDARY`.

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

Nothing further is needed from an admin. Tell Claude the policy is applied and
the rest is driven from this repo:

| Step | How |
| --- | --- |
| Enable the content rebuild | change the `ENABLE_CONTENT_REBUILD` fallback in `deploy.yml` from `'false'` to `'true'`, merge, watch the deploy |
| Enable access logs | same, `ENABLE_ACCESS_LOGS` |
| Create the permissions boundary | run the `harden-role` workflow with `stage=create-boundary` |
| Enforce the boundary | same fallback change for `ENFORCE_BOUNDARY` |

Each is a separate merge and a separate deploy, verified green before the next.
They are deliberately not batched: each needs a permission to have landed before
the stack asserts it, and IAM is eventually consistent — losing that race is
exactly how the 29 Jul rollback happened.

The `vars.*` indirection stays so the switches can still be forced off from the
GitHub UI without a commit, but the default now lives in code, where it can be
changed by whoever is doing the work rather than only by a repo admin.
