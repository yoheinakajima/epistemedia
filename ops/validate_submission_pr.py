#!/usr/bin/env python3
"""Validate an untrusted docket-submission PR using accepted-base code only."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import subprocess
import urllib.request
from pathlib import Path

from epistemedia.open_dockets import (
    SUBMISSION_ROOT,
    validate_question_novelty,
    validate_submission_directory,
)
from epistemedia.research_kit import parse_utc_timestamp


def github_json(path: str) -> object:
    request = urllib.request.Request(
        f"https://api.github.com/repos/{os.environ['GITHUB_REPOSITORY']}/{path}",
        headers={
            "accept": "application/vnd.github+json",
            "authorization": f"Bearer {os.environ['GITHUB_TOKEN']}",
            "user-agent": "epistemedia-accepted-base-submission-validator",
            "x-github-api-version": "2022-11-28",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def _github_time(value: object, path: str, errors: list[str]) -> dt.datetime | None:
    return parse_utc_timestamp(value, path, errors)


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
            proposal_path = directory / "proposal.json"
            if proposal_path.is_file() and not proposal_path.is_symlink():
                try:
                    proposal = json.loads(proposal_path.read_text(encoding="utf-8"))
                except json.JSONDecodeError:
                    proposal = None
                if isinstance(proposal, dict):
                    errors.extend(
                        validate_question_novelty(
                            candidate, str(proposal.get("question", ""))
                        )
                    )
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
                            errors.append(
                                "proposal digest already exists in an accepted open docket"
                            )
                if isinstance(intake, dict) and os.environ.get("CURRENT_PR_NUMBER"):
                    head = subprocess.run(
                        ["git", "-C", str(candidate), "rev-parse", "HEAD"],
                        check=True,
                        capture_output=True,
                        text=True,
                    ).stdout.strip()
                    pr_number = int(os.environ["CURRENT_PR_NUMBER"])
                    pr = github_json(f"pulls/{pr_number}")
                    commit = github_json(f"commits/{head}")
                    base_commit = github_json(f"commits/{base_sha}")
                    if not all(
                        isinstance(item, dict) for item in (pr, commit, base_commit)
                    ):
                        errors.append("GitHub submission metadata is malformed")
                    else:
                        if pr.get("head", {}).get("sha") != head:
                            errors.append("source PR head does not match the immutable candidate commit")
                        if pr.get("base", {}).get("sha") != base_sha:
                            errors.append("source PR base does not match accepted main")
                        if pr.get("state") != "open" or pr.get("draft") is not True:
                            errors.append("source submission must remain open and draft")
                        time_errors: list[str] = []
                        runtime_started = _github_time(
                            json.loads((directory / "proposal.json").read_text())["runtime"]["started_at"],
                            "proposal.runtime.started_at",
                            time_errors,
                        )
                        runtime_completed = _github_time(
                            json.loads((directory / "proposal.json").read_text())["runtime"]["completed_at"],
                            "proposal.runtime.completed_at",
                            time_errors,
                        )
                        submitted = _github_time(
                            intake.get("submitted_at"), "intake.submitted_at", time_errors
                        )
                        author_time = _github_time(
                            commit.get("commit", {}).get("author", {}).get("date"),
                            "GitHub commit author time",
                            time_errors,
                        )
                        committer_time = _github_time(
                            commit.get("commit", {}).get("committer", {}).get("date"),
                            "GitHub commit committer time",
                            time_errors,
                        )
                        pr_created = _github_time(
                            pr.get("created_at"), "GitHub PR created_at", time_errors
                        )
                        base_committer_time = _github_time(
                            base_commit.get("commit", {}).get("committer", {}).get("date"),
                            "accepted base commit committer time",
                            time_errors,
                        )
                        ordered = [
                            base_committer_time,
                            runtime_started,
                            runtime_completed,
                            submitted,
                            author_time,
                            committer_time,
                            pr_created,
                        ]
                        if not time_errors and all(value is not None for value in ordered):
                            values = [value for value in ordered if value is not None]
                            if values != sorted(values):
                                time_errors.append(
                                    "chronology must satisfy accepted base commit <= runtime start <= completion <= intake submission <= commit author <= commit committer <= server PR creation"
                                )
                        errors.extend(time_errors)
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
    result["queue_validated"] = result["valid"]
    result["required_check_intentionally_blocking"] = True
    print(json.dumps(result, indent=2, sort_keys=True))
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
