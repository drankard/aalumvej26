"""Report deploy-role permissions a PR adds that the live role will not have.

bootstrap.yaml is a description, not a deployment. Nothing applies it — the live
role is not CloudFormation-managed and denies modifying itself, so only an
account admin can realign it. A PR that adds a permission here and a resource
needing it in template.yaml therefore deploys, rolls back, and skips the
frontend publish.

Prints markdown to stdout when the PR adds permissions, and nothing at all when
it does not. Silence means no action needed; it is not an error channel.

Usage: diff_role_permissions.py <base bootstrap.yaml> <head bootstrap.yaml>
"""
from __future__ import annotations

import sys

import yaml


class CfnLoader(yaml.SafeLoader):
    pass


def _any_node(loader, node):
    """Resolve a CloudFormation intrinsic whatever shape it takes.

    The same tag appears in more than one form — !GetAtt is scalar in
    `!GetAtt DeployRole.Arn` and a sequence in list form — so dispatch on the
    node type rather than assuming one per tag. This script only needs the
    Action lists to survive parsing; the intrinsic values themselves are never
    compared.
    """
    if isinstance(node, yaml.ScalarNode):
        return loader.construct_scalar(node)
    if isinstance(node, yaml.SequenceNode):
        return loader.construct_sequence(node)
    return loader.construct_mapping(node)


for tag in ("!Sub", "!Ref", "!Condition", "!GetAtt",
            "!Not", "!Equals", "!If", "!And", "!Or", "!Join", "!Select"):
    CfnLoader.add_constructor(tag, _any_node)


def permissions(path: str) -> set[str]:
    """Every Allow-ed action in the scoped policy, flattened."""
    with open(path) as f:
        doc = yaml.load(f, Loader=CfnLoader)
    try:
        policies = doc["Resources"]["DeployRole"]["Properties"]["Policies"]
        statements = next(
            p for p in policies if p["PolicyName"] == "aalumvej26-scoped"
        )["PolicyDocument"]["Statement"]
    except (KeyError, TypeError, StopIteration):
        return set()

    out: set[str] = set()
    for st in statements:
        if st.get("Effect") != "Allow":
            continue
        actions = st.get("Action") or []
        out.update(actions if isinstance(actions, list) else [actions])
    return out


def main() -> int:
    base, head = permissions(sys.argv[1]), permissions(sys.argv[2])
    added = sorted(head - base)
    removed = sorted(base - head)
    if not added and not removed:
        return 0

    print("### Deploy role changed — the live role will not pick this up\n")
    print(
        "`bootstrap.yaml` describes the role; nothing applies it. The live role "
        "is not CloudFormation-managed and carries an explicit Deny on modifying "
        "itself, so CI cannot resync it. **An account admin has to apply this "
        "manually.**\n"
    )
    if added:
        print("**Permissions this PR expects the role to have:**\n")
        for a in added:
            print(f"- `{a}`")
        print()
        print(
            "If anything in `template.yaml` needs one of these, keep it behind a "
            "default-off parameter until the role has actually been updated — "
            "otherwise the stack update fails, rolls back, and the frontend "
            "publish is skipped along with it.\n"
        )
    if removed:
        print("**Permissions this PR drops:**\n")
        for r in removed:
            print(f"- `{r}`")
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
