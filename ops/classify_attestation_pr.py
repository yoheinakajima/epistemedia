#!/usr/bin/env python3
"""Classify paths for the trusted open-docket receipt-child attester."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path, PurePosixPath

OPEN_DOCKET_PREFIX = "research/open-dockets/"
PROMOTION_FILES = {
    "controller-attestation.json",
    "intake.json",
    "proposal.json",
    "promotion-receipt.json",
    "review.json",
}
SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SHA = re.compile(r"^[0-9a-f]{40}$")


def pull_request_identity(payload: object, reviewed_head: str) -> tuple[str, str]:
    """Return one exact base/head pair or reject a stale workflow-run binding."""

    if not SHA.fullmatch(reviewed_head):
        raise ValueError("reviewed head must be an exact lowercase commit SHA")
    if not isinstance(payload, dict):
        raise ValueError("pull-request response must be a JSON object")
    try:
        state = payload["state"]
        base = payload["base"]["sha"]
        head = payload["head"]["sha"]
    except (KeyError, TypeError) as exc:
        raise ValueError("pull-request response lacks state/base/head identity") from exc
    if state != "open":
        raise ValueError("pull request must remain open")
    if not isinstance(base, str) or not SHA.fullmatch(base):
        raise ValueError("pull-request base must be an exact lowercase commit SHA")
    if not isinstance(head, str) or not SHA.fullmatch(head):
        raise ValueError("pull-request head must be an exact lowercase commit SHA")
    if head != reviewed_head:
        raise ValueError("pull-request head moved after the validation run")
    return base, head


def exact_git_changes(repository: Path, base: str, head: str) -> list[tuple[str, str]]:
    """Read an immutable merge-base diff without rename collapsing."""

    for label, value in (("base", base), ("head", head)):
        if not SHA.fullmatch(value):
            raise ValueError(f"{label} must be an exact lowercase commit SHA")
    command = [
        "git",
        "-C",
        str(repository),
        "diff",
        "--name-status",
        "--no-renames",
        "-z",
        f"{base}...{head}",
        "--",
    ]
    completed = subprocess.run(command, check=True, capture_output=True)
    fields = completed.stdout.split(b"\0")
    if fields[-1:] == [b""]:
        fields.pop()
    if len(fields) % 2:
        raise ValueError("git name-status output has an incomplete record")
    changes: list[tuple[str, str]] = []
    for index in range(0, len(fields), 2):
        status = fields[index].decode("ascii")
        path = fields[index + 1].decode("utf-8")
        if len(status) != 1 or status not in "ACDMTUXB":
            raise ValueError(f"unsupported git change status: {status}")
        changes.append((status, path))
    return changes


def classify_attestation_paths(paths: list[str]) -> dict[str, str | bool | None]:
    """Return an ordinary no-op or one exact promotion shape; reject all ambiguity."""

    if not paths:
        raise ValueError("pull request changed-path list must not be empty")
    if len(set(paths)) != len(paths):
        raise ValueError("pull request changed-path list contains duplicates")
    if not any(path.startswith(OPEN_DOCKET_PREFIX) for path in paths):
        return {"mode": "ordinary", "eligible": False, "parent": None}
    if len(paths) != len(PROMOTION_FILES):
        raise ValueError("docket-sensitive diff must contain exactly five promotion files")

    parsed = [PurePosixPath(path) for path in paths]
    parents = {path.parent for path in parsed}
    if len(parents) != 1:
        raise ValueError("promotion files must share one direct docket directory")
    parent = next(iter(parents))
    if (
        len(parent.parts) != 3
        or parent.parts[:2] != ("research", "open-dockets")
        or parent.name == "submissions"
        or not SLUG.fullmatch(parent.name)
    ):
        raise ValueError("promotion parent must be research/open-dockets/<slug>")
    if {path.name for path in parsed} != PROMOTION_FILES:
        raise ValueError("promotion file names do not match the exact receipt-child shape")
    return {"mode": "promotion", "eligible": True, "parent": str(parent)}


def classify_attestation_changes(
    changes: list[tuple[str, str]],
) -> dict[str, str | bool | None]:
    """Classify exact-SHA changes, requiring every promotion member to be newly added."""

    paths = [path for _, path in changes]
    if not any(path.startswith(OPEN_DOCKET_PREFIX) for path in paths):
        return classify_attestation_paths(paths)
    if any(status != "A" for status, _ in changes):
        raise ValueError("every exact promotion member must be newly added")
    return classify_attestation_paths(paths)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pr-file", type=Path, required=True)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--reviewed-head", required=True)
    parser.add_argument("--github-output", type=Path, required=True)
    args = parser.parse_args()
    try:
        payload = json.loads(args.pr_file.read_text(encoding="utf-8"))
        base, head = pull_request_identity(payload, args.reviewed_head)
        changes = exact_git_changes(args.repository, base, head)
        result = classify_attestation_changes(changes)
    except (
        OSError,
        UnicodeDecodeError,
        json.JSONDecodeError,
        subprocess.CalledProcessError,
        ValueError,
    ) as exc:
        print(f"attestation classification failed: {exc}", file=sys.stderr)
        return 1
    with args.github_output.open("a", encoding="utf-8") as output:
        output.write(f"base={base}\n")
        output.write(f"mode={result['mode']}\n")
        output.write(f"eligible={str(result['eligible']).lower()}\n")
        if result["parent"] is not None:
            output.write(f"parent={result['parent']}\n")
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
