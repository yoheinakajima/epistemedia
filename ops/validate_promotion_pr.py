#!/usr/bin/env python3
"""Validate one reviewed open-docket promotion using accepted-base code."""

from __future__ import annotations

import argparse
import base64
import hashlib
import html
import ipaddress
import json
import os
import re
import socket
import subprocess
import tempfile
import urllib.request
from pathlib import Path
from typing import Any
from urllib.parse import quote, urlsplit

from epistemedia.open_dockets import load_open_dockets, validate_submission_directory


def git(candidate: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(candidate), *args],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def changed(candidate: Path, start: str, end: str) -> list[str]:
    return git(candidate, "diff", "--name-only", f"{start}...{end}").splitlines()


def changed_status(candidate: Path, start: str, end: str) -> list[tuple[str, str]]:
    records = []
    for line in git(candidate, "diff", "--name-status", f"{start}...{end}").splitlines():
        status, path = line.split("\t", 1)
        records.append((status, path))
    return records


def github_json(path: str) -> Any:
    repository = os.environ["GITHUB_REPOSITORY"]
    request = urllib.request.Request(
        f"https://api.github.com/repos/{repository}/{path}",
        headers={
            "accept": "application/vnd.github+json",
            "authorization": f"Bearer {os.environ['GITHUB_TOKEN']}",
            "user-agent": "epistemedia-accepted-base-promotion-validator",
            "x-github-api-version": "2022-11-28",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def github_file(path: str, ref: str) -> bytes:
    payload = github_json(f"contents/{quote(path, safe='/')}?ref={quote(ref, safe='')}")
    if not isinstance(payload, dict) or payload.get("encoding") != "base64":
        raise ValueError(f"GitHub content response is not a base64 file: {path}")
    encoded = "".join(str(payload.get("content", "")).split())
    return base64.b64decode(encoded, validate=True)


def fetch_public(url: str, *, max_bytes: int = 25_000_000) -> bytes:
    parsed = urlsplit(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError(f"source URL is not public HTTP(S): {url}")
    addresses = {
        ipaddress.ip_address(record[4][0])
        for record in socket.getaddrinfo(
            parsed.hostname,
            parsed.port or (443 if parsed.scheme == "https" else 80),
            type=socket.SOCK_STREAM,
        )
    }
    if not addresses or any(not address.is_global for address in addresses):
        raise ValueError(f"source URL resolves to a non-public address: {url}")
    address = sorted(addresses, key=str)[0]
    pinned_address = f"[{address}]" if address.version == 6 else str(address)
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    with tempfile.TemporaryDirectory(prefix="epistemedia-pinned-source-") as tmp:
        output = Path(tmp) / "artifact"
        result = subprocess.run(
            [
                "curl",
                "--silent",
                "--show-error",
                "--fail-with-body",
                "--connect-timeout",
                "10",
                "--max-time",
                "20",
                "--max-filesize",
                str(max_bytes),
                "--noproxy",
                "*",
                "--proto",
                "=http,https",
                "--resolve",
                f"{parsed.hostname}:{port}:{pinned_address}",
                "--output",
                str(output),
                "--write-out",
                "%{http_code}",
                "--",
                url,
            ],
            check=False,
            capture_output=True,
            text=True,
            timeout=25,
        )
        if result.returncode != 0:
            raise ValueError(
                f"pinned source retrieval failed: {result.stderr.strip()[:500]}"
            )
        try:
            status = int(result.stdout.strip())
        except ValueError as exc:
            raise ValueError("pinned source retrieval returned no HTTP status") from exc
        if not 200 <= status < 300:
            raise ValueError(
                f"source URL redirects or returned non-success status {status}; "
                "record the final public carrier"
            )
        value = output.read_bytes()
    if len(value) > max_bytes:
        raise ValueError(
            f"independent source retrieval exceeds {max_bytes} bytes: {url}"
        )
    return value


def normalized_text(value: str) -> str:
    without_markup = re.sub(r"<[^>]+>", " ", value)
    return " ".join(html.unescape(without_markup).split())


def validate(candidate: Path, base_sha: str) -> dict[str, Any]:
    errors: list[str] = []
    head = git(candidate, "rev-parse", "HEAD")
    parent = git(candidate, "rev-parse", "HEAD^")
    parent_tree = git(candidate, "rev-parse", f"{parent}^{{tree}}")
    candidate_sha = os.environ.get("CANDIDATE_SHA")
    if candidate_sha and head != candidate_sha:
        errors.append("candidate checkout does not match pull-request head")
    receipt_paths = [
        path for path in changed(candidate, base_sha, head)
        if path.startswith("research/open-dockets/") and path.endswith("/promotion-receipt.json")
    ]
    if len(receipt_paths) != 1:
        errors.append("promotion must contain exactly one promotion receipt")
        receipt_path = None
    else:
        receipt_path = receipt_paths[0]
    receipt: dict[str, Any] = {}
    if receipt_path:
        receipt = json.loads((candidate / receipt_path).read_text(encoding="utf-8"))
        if receipt.get("reviewed_head") != parent:
            errors.append("promotion receipt does not bind the receipt commit parent")
        if receipt.get("reviewed_tree") != parent_tree:
            errors.append("promotion receipt does not bind the reviewed tree")
        slug_dir = str(Path(receipt_path).parent)
        expected_reviewed = {
            f"{slug_dir}/intake.json",
            f"{slug_dir}/proposal.json",
            f"{slug_dir}/review.json",
        }
        if set(changed(candidate, base_sha, parent)) != expected_reviewed:
            errors.append("reviewed parent must add exactly one three-file promoted docket")
        if set(changed_status(candidate, base_sha, parent)) != {
            ("A", path) for path in expected_reviewed
        }:
            errors.append("reviewed docket files must be newly added and immutable")
        receipt_delta = changed(candidate, parent, head)
        if receipt_delta != [receipt_path]:
            errors.append("receipt commit must add only the promotion receipt")
        if changed_status(candidate, parent, head) != [("A", receipt_path)]:
            errors.append("promotion receipt must be newly added in the receipt-only child")
    dockets, docket_errors = load_open_dockets(candidate)
    errors.extend(docket_errors)
    if receipt_path:
        slug = Path(receipt_path).parent.name
        if sum(docket.slug == slug for docket in dockets) != 1:
            errors.append("promoted docket did not load exactly once")
    source_pr_number = receipt.get("source_pr_number")
    if isinstance(source_pr_number, int) and source_pr_number > 0:
        source_pr = github_json(f"pulls/{source_pr_number}")
        if source_pr.get("html_url") != (
            f"https://github.com/{os.environ['GITHUB_REPOSITORY']}/pull/{source_pr_number}"
        ):
            errors.append("source pull request URL is not canonical")
        if source_pr.get("head", {}).get("sha") != receipt.get("source_pr_head"):
            errors.append("source pull request head drifted from the review binding")
        if source_pr.get("base", {}).get("sha") != base_sha:
            errors.append("source pull request does not target the promotion base")
        if source_pr.get("state") != "open" or source_pr.get("draft") is not True:
            errors.append("source submission must remain open and draft")
        if source_pr_number == int(os.environ.get("CURRENT_PR_NUMBER", "0")):
            errors.append("promotion pull request cannot be its own source submission")
        files = github_json(f"pulls/{source_pr_number}/files?per_page=100")
        paths = sorted(item.get("filename", "") for item in files)
        parents = {str(Path(path).parent) for path in paths}
        if any(item.get("status") != "added" for item in files):
            errors.append("source pull request files must all be newly added")
        if len(parents) != 1 or set(Path(path).name for path in paths) != {
            "PR_BODY.md", "intake.json", "proposal.json"
        }:
            errors.append("source pull request is not one exact submission-directory diff")
        elif receipt_path:
            source_parent = next(iter(parents))
            source_head = str(receipt.get("source_pr_head"))
            source_files = {
                name: github_file(f"{source_parent}/{name}", source_head)
                for name in ("PR_BODY.md", "intake.json", "proposal.json")
            }
            with tempfile.TemporaryDirectory(prefix="epistemedia-source-submission-") as tmp:
                submission_dir = Path(tmp) / "submission"
                submission_dir.mkdir()
                for name, value in source_files.items():
                    (submission_dir / name).write_bytes(value)
                errors.extend(
                    f"source submission: {error}"
                    for error in validate_submission_directory(submission_dir)
                )
            promoted_dir = candidate / Path(receipt_path).parent
            for name in ("intake.json", "proposal.json"):
                if source_files[name] != (promoted_dir / name).read_bytes():
                    errors.append(f"promoted {name} does not match the bound source submission")
            proposal = json.loads((promoted_dir / "proposal.json").read_text(encoding="utf-8"))
            intake = json.loads((promoted_dir / "intake.json").read_text(encoding="utf-8"))
            review = json.loads((promoted_dir / "review.json").read_text(encoding="utf-8"))
            source_reviews = {
                item["source_id"]: item for item in review.get("source_reviews", [])
                if isinstance(item, dict) and isinstance(item.get("source_id"), str)
            }
            aggregate_retrieved_bytes = 0
            for source in proposal.get("sources", []):
                source_id = source.get("source_id")
                remaining_budget = 100_000_000 - aggregate_retrieved_bytes
                if remaining_budget <= 0:
                    errors.append("independent CI aggregate source retrieval exceeds 100MB")
                    break
                try:
                    artifact = fetch_public(
                        source["url"], max_bytes=min(25_000_000, remaining_budget)
                    )
                except Exception as exc:
                    errors.append(f"independent CI retrieval failed for {source_id}: {exc}")
                    continue
                aggregate_retrieved_bytes += len(artifact)
                digest = hashlib.sha256(artifact).hexdigest()
                if digest != source_reviews.get(source_id, {}).get("artifact_sha256"):
                    errors.append(f"independent CI artifact digest mismatch for {source_id}")
                author_digests = {
                    event.get("artifact_sha256")
                    for event in intake.get("trace", {}).get("events", [])
                    if event.get("action") == "retrieve-source"
                    and event.get("target") == source.get("url")
                }
                if author_digests != {digest}:
                    errors.append(f"author trace artifact digest mismatch for {source_id}")
                media_type = str(source.get("media_type", "")).lower()
                if any(token in media_type for token in ("html", "text", "json", "xml")):
                    text = normalized_text(artifact.decode("utf-8", errors="replace"))
                    for span in source.get("exact_spans", []):
                        if normalized_text(str(span.get("quote", ""))) not in text:
                            errors.append(
                                f"independent CI text containment failed for {span.get('span_id')}"
                            )
    else:
        errors.append("promotion receipt source PR number is invalid")
    return {
        "format": "epistemedia-open-docket-promotion-check-v0.1",
        "valid": not errors,
        "base_sha": base_sha,
        "candidate_head": head,
        "reviewed_head": parent,
        "receipt_path": receipt_path,
        "errors": errors,
        "admitted": not errors,
        "merge_permitted": not errors,
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
