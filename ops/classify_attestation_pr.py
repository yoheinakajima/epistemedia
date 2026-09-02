#!/usr/bin/env python3
"""Classify paths for the trusted open-docket receipt-child attester."""

from __future__ import annotations

import argparse
import json
import re
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


def paths_from_api_payload(payload: object) -> list[str]:
    """Extract filenames from gh api --paginate --slurp output."""

    if not isinstance(payload, list):
        raise ValueError("changed-file API response must be a JSON array of pages")
    paths: list[str] = []
    for page in payload:
        if not isinstance(page, list):
            raise ValueError("each changed-file API page must be a JSON array")
        for item in page:
            if not isinstance(item, dict) or not isinstance(item.get("filename"), str):
                raise ValueError("each changed-file API item must have a string filename")
            paths.append(item["filename"])
    return paths


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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--paths-file", type=Path, required=True)
    parser.add_argument("--github-output", type=Path, required=True)
    args = parser.parse_args()
    try:
        payload = json.loads(args.paths_file.read_text(encoding="utf-8"))
        paths = paths_from_api_payload(payload)
        result = classify_attestation_paths(paths)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"attestation classification failed: {exc}", file=sys.stderr)
        return 1
    with args.github_output.open("a", encoding="utf-8") as output:
        output.write(f"mode={result['mode']}\n")
        output.write(f"eligible={str(result['eligible']).lower()}\n")
        if result["parent"] is not None:
            output.write(f"parent={result['parent']}\n")
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
