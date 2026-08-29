#!/usr/bin/env python3
"""Route every docket-sensitive PR through accepted-base validators."""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path


def classify_paths(paths: list[str]) -> str:
    if any(path.startswith("research/open-dockets/submissions/") for path in paths):
        return "submission"
    if any(path.startswith("research/open-dockets/") for path in paths):
        return "promotion"
    return "normal"


def changed_paths(candidate: Path, base_sha: str) -> list[str]:
    if not base_sha:
        return []
    output = subprocess.run(
        ["git", "-C", str(candidate), "diff", "--name-only", f"{base_sha}...HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    return output.splitlines()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--base-sha", default="")
    parser.add_argument("--github-output", type=Path, required=True)
    args = parser.parse_args()
    mode = classify_paths(changed_paths(args.candidate.resolve(), args.base_sha))
    with args.github_output.open("a", encoding="utf-8") as output:
        output.write(f"mode={mode}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
