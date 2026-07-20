"""Extract the deploy-role inline policy from bootstrap.yaml as JSON.

Used by harden-role.yml so bootstrap.yaml stays the single source of truth.
Resolves !Sub with the real account id; ${GitHubRepo} -> aalumvej26.

Usage: extract_role_policy.py <account_id> [--without-deny]
  --without-deny drops the NeverModifySelf statement — needed while staging,
  because that Deny takes effect immediately and would block the remaining
  hardening steps if applied too early.
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


def main() -> int:
    account_id = sys.argv[1]
    without_deny = "--without-deny" in sys.argv

    with open("bootstrap.yaml") as f:
        template = yaml.load(f, Loader=CfnLoader)

    policies = template["Resources"]["DeployRole"]["Properties"]["Policies"]
    doc = next(p for p in policies if p["PolicyName"] == "aalumvej26-scoped")["PolicyDocument"]
    doc = resolve(doc, account_id)

    if without_deny:
        doc["Statement"] = [s for s in doc["Statement"] if s.get("Sid") != "NeverModifySelf"]

    json.dump(doc, sys.stdout, indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
