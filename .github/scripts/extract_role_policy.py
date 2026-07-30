"""Extract the deploy-role inline policy from bootstrap.yaml as JSON.

Used by harden-role.yml so bootstrap.yaml stays the single source of truth.
Resolves !Sub with the real account id; ${GitHubRepo} -> aalumvej26.

Usage: extract_role_policy.py <account_id> [--without-deny] [--without-boundary]
  --without-deny drops Deny statements — retained for the older staged
  hardening flow. NeverModifySelf no longer exists (see bootstrap.yaml for
  why it was removed), so today this only affects NeverRemoveBoundary.

  --without-boundary strips the iam:PermissionsBoundary conditions. Needed in
  two places, both chicken-and-egg: when granting the role the policy-management
  rights it needs to *create* the boundary in the first place, and when reverting
  if a boundary change breaks a deploy. Without this flag the emitted policy
  refers to a managed policy that may not exist yet, and role creation would
  fail closed.
"""
from __future__ import annotations

import json
import sys

import yaml


class CfnLoader(yaml.SafeLoader):
    pass


def _sub(loader, node):
    return {"__sub__": loader.construct_scalar(node)}


def _passthrough(loader, node):
    return None


CfnLoader.add_constructor("!Sub", _sub)
for tag in ("!Ref", "!GetAtt", "!Not", "!Equals", "!If"):
    CfnLoader.add_constructor(tag, _passthrough)


def resolve(obj, account_id: str):
    if isinstance(obj, dict):
        if set(obj.keys()) == {"__sub__"}:
            s = obj["__sub__"]
            s = s.replace("${AWS::AccountId}", account_id)
            s = s.replace("${GitHubRepo}", "aalumvej26")
            s = s.replace("${GitHubOrg}", "drankard")
            return s
        return {k: resolve(v, account_id) for k, v in obj.items()}
    if isinstance(obj, list):
        return [resolve(v, account_id) for v in obj]
    return obj


BOUNDARY_CONDITION_KEY = "iam:PermissionsBoundary"


def strip_boundary_conditions(statements: list) -> list:
    """Drop iam:PermissionsBoundary conditions, and any statement that exists
    solely to enforce the boundary.

    A statement whose Condition becomes empty is emitted without a Condition —
    that is the pre-boundary behaviour we are reverting to, not a no-op.
    """
    out = []
    for s in statements:
        if s.get("Sid") == "NeverRemoveBoundary":
            continue
        cond = s.get("Condition")
        if isinstance(cond, dict):
            cond = {
                op: {k: v for k, v in kv.items() if k != BOUNDARY_CONDITION_KEY}
                for op, kv in cond.items()
            }
            cond = {op: kv for op, kv in cond.items() if kv}
            if cond:
                s = {**s, "Condition": cond}
            else:
                s = {k: v for k, v in s.items() if k != "Condition"}
        out.append(s)
    return out


def main() -> int:
    account_id = sys.argv[1]
    without_deny = "--without-deny" in sys.argv
    without_boundary = "--without-boundary" in sys.argv

    with open("bootstrap.yaml") as f:
        template = yaml.load(f, Loader=CfnLoader)

    policies = template["Resources"]["DeployRole"]["Properties"]["Policies"]
    doc = next(p for p in policies if p["PolicyName"] == "aalumvej26-scoped")["PolicyDocument"]
    doc = resolve(doc, account_id)

    if without_deny:
        doc["Statement"] = [s for s in doc["Statement"] if s.get("Effect") != "Deny"]
    if without_boundary:
        doc["Statement"] = strip_boundary_conditions(doc["Statement"])

    json.dump(doc, sys.stdout, indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
