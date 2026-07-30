# Permissions boundary

`boundary.json` is the ceiling attached to every IAM role the CI deploy role
creates or edits (the Lambda execution roles, the CodeBuild role). It is applied
via an `iam:PermissionsBoundary` condition in `bootstrap.yaml`, so the deploy
role is *unable* to create a role without it.

## Why it exists

Before it, the deploy role held `iam:CreateRole` plus `iam:AttachRolePolicy`
with no constraint on which policy could be attached, plus `iam:PassRole` to
Lambda. That is a complete privilege-escalation path: create a role, attach
`AdministratorAccess`, pass it to a Lambda, run anything. The `NeverModifySelf`
Deny that was in the policy did not close this — it only blocked the one route
nobody needed, while making every new resource type an admin task.

A boundary closes it. Effective permissions are always
`identity policy ∩ boundary`, so even `AdministratorAccess` on a CI-created role
grants nothing the boundary forbids.

## Why it allows `*` and denies narrowly

A boundary is a ceiling, not a least-privilege policy — the role's own policy
still does that job. Enumerating every service the application needs would risk
breaking the Lambdas at *runtime* rather than at deploy time, which is the worst
place to discover a missing permission and is especially bad here, where there
is no CLI access to diagnose it.

So the ceiling permits application work and subtracts only the identity control
plane: IAM, Organizations, account settings, and SSO/Identity Center. Those are
the services that turn a compromised deploy into persistent account access.

This deliberately does **not** try to limit blast radius on data (a compromised
pipeline can still reach the app's own DynamoDB table and S3 buckets — it needs
to, to function). It stops the escalation to *new identities*, which is the part
that survives a credential rotation.

## What it does not cover

The deploy role itself has no boundary — it cannot have this one, because it
legitimately needs `iam:CreateRole` to manage the app's roles, which the ceiling
forbids. So a change to the deploy role's own policy is still a privileged
operation; the control on that is review, since it requires a commit on `main`.

Closing that fully needs a two-role split: an unprivileged role for everyday
deploys, and a separate privileged role for IAM changes, assumable only from a
workflow bound to a GitHub Environment with required reviewers. That is
configurable entirely in the GitHub UI plus a trust-policy change, and is the
recommended next step rather than something this boundary achieves.

## Changing it

Edit `boundary.json`, then run the `harden-role` workflow with
`stage=apply-boundary`. It publishes a new default version of the managed policy.
`stage=revert-boundary` detaches it from the app roles and removes the
conditions, which is the escape hatch if a boundary change breaks a deploy.
