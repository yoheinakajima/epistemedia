#!/usr/bin/env python3
"""Validate an untrusted docket-submission PR using accepted-base code only."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

from epistemedia.open_dockets import SUBMISSION_ROOT, validate_submission_directory


def changed_paths(candidate: Path, base_sha: str) -> list[str]:
    result = subprocess.run(
        [
            "git",
            "-C",
            str(candidate),
            "diff",
            "--name-only",
            f"{base_sha}...HEAD",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return [line for line in result.stdout.splitlines() if line]


def validate(candidate: Path, base_sha: str) -> dict[str, object]:
    errors: list[str] = []
    paths = changed_paths(candidate, base_sha)
    prefix = SUBMISSION_ROOT.as_posix() + "/"
    if not paths:
        errors.append("submission PR contains no changed files")
    if any(not path.startswith(prefix) for path in paths):
        errors.append("submission PR changes a path outside the untrusted queue directory")
    directories = {str(Path(path).parent) for path in paths if path.startswith(prefix)}
    if len(directories) != 1:
        errors.append("submission PR must contain exactly one submission directory")
    directory = None
    if len(directories) == 1:
        directory = candidate / next(iter(directories))
        if directory.parent != candidate / SUBMISSION_ROOT:
            errors.append(
                "submission files must be direct children of one generated queue directory"
            )
        else:
            errors.extend(validate_submission_directory(directory))
            intake_path = directory / "intake.json"
            if intake_path.is_file() and not intake_path.is_symlink():
                try:
                    intake = json.loads(intake_path.read_text(encoding="utf-8"))
                except json.JSONDecodeError:
                    intake = None
                accepted_root = candidate / "research" / "open-dockets"
                if isinstance(intake, dict) and accepted_root.is_dir():
                    for accepted in sorted(accepted_root.iterdir()):
                        if not accepted.is_dir() or accepted.name == "submissions":
                            continue
                        accepted_intake = accepted / "intake.json"
                        if not accepted_intake.is_file() or accepted_intake.is_symlink():
                            continue
                        existing = json.loads(accepted_intake.read_text(encoding="utf-8"))
                        if intake.get("proposal_id") == existing.get("proposal_id"):
                            errors.append("proposal ID already exists in an accepted open docket")
                        if intake.get("proposal_sha256") == existing.get("proposal_sha256"):
                            errors.append("proposal digest already exists in an accepted open docket")
    return {
        "format": "epistemedia-untrusted-submission-check-v0.1",
        "valid": not errors,
        "base_sha": base_sha,
        "candidate_head": subprocess.run(
            ["git", "-C", str(candidate), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip(),
        "paths": paths,
        "directory": str(directory.relative_to(candidate)) if directory else None,
        "errors": errors,
        "submitted": bool(not errors),
        "admitted": False,
        "merge_permitted": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--base-sha", required=True)
    args = parser.parse_args()
    result = validate(args.candidate.resolve(), args.base_sha)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
