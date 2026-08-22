"""Verify EM-0019 source artifacts and an independently authored review receipt."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import xml.etree.ElementTree as ET
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

from build_candidate import CANDIDATE_PATH

REPO_ROOT = Path(__file__).resolve().parents[3]
RESEARCH_DIR = CANDIDATE_PATH.parent
REVIEW_RECEIPT_DIR = RESEARCH_DIR / "review-receipts"
REPOSITORY_URL = "https://github.com/yoheinakajima/epistemedia"
RECEIPT_FORMAT = "epistemedia-research-review-receipt-v0.1"
REVIEW_PACKET_PATHS = tuple(
    sorted(
        str(path.relative_to(REPO_ROOT))
        for path in (
            RESEARCH_DIR / "README.md",
            RESEARCH_DIR / "build_candidate.py",
            RESEARCH_DIR / "candidate-dossier.json",
            RESEARCH_DIR / "verify_retrievals.py",
        )
    )
)

ARTIFACTS = {
    "edition-skurnik-2005": {
        "filename": "epistemedia-skurnik-jcr2005.pdf",
        "format": "pdf",
    },
    "edition-handbook-2011": {
        "filename": "epistemedia-handbook-page.html",
        "format": "html",
    },
    "edition-ecker-2020": {
        "filename": "epistemedia-pmc7447737.xml",
        "format": "xml",
    },
    "edition-prike-2023": {
        "filename": "epistemedia-pmc10317933.xml",
        "format": "xml",
    },
    "edition-ecker-2023": {
        "filename": "epistemedia-pmc10096191.xml",
        "format": "xml",
    },
    "edition-autry-2021": {
        "filename": "crossref-autry-2021.json",
        "format": "crossref-json",
    },
    "edition-pluviano-2017": {
        "filename": "pluviano-2017.xml",
        "format": "xml",
    },
    "edition-pluviano-2019": {
        "filename": "pluviano-2019.pdf",
        "format": "pdf",
    },
    "edition-thomas-2024": {
        "filename": "crossref-thomas-2024.json",
        "format": "crossref-json",
    },
    "edition-nibat-2026": {
        "filename": "nibat-2026.pdf",
        "format": "pdf",
    },
}
DATA_ARTIFACTS = {
    ("edition-autry-2021", 0): "autry-2021-experiment-1-inference.xlsx",
    ("edition-autry-2021", 1): "autry-2021-experiment-2-inference.xlsx",
    ("edition-thomas-2024", 0): "thomas-2024-data.xlsx",
}
PRIMARY_MEDIA_TYPES = {
    "edition-skurnik-2005": "application/pdf",
    "edition-handbook-2011": "text/html",
    "edition-schwarz-2016": "application/pdf",
    "edition-ecker-2020": "application/xml",
    "edition-prike-2023": "application/xml",
    "edition-ecker-2023": "application/xml",
    "edition-autry-2021": "application/json",
    "edition-pluviano-2017": "application/xml",
    "edition-pluviano-2019": "application/pdf",
    "edition-thomas-2024": "application/json",
    "edition-nibat-2026": "application/pdf",
}
WORKBOOK_MEDIA_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

SHA256_PATTERN = re.compile(r"^[a-f0-9]{64}$")
COMMIT_PATTERN = re.compile(r"^[a-f0-9]{40}$")


class TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self.parts.append(data)


def fail(message: str) -> None:
    raise SystemExit(message)


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def require_exact_fields(record: dict[str, Any], fields: set[str], context: str) -> None:
    require(isinstance(record, dict), f"{context}: must be an object")
    missing = sorted(fields - record.keys())
    extra = sorted(record.keys() - fields)
    require(not missing, f"{context}: missing fields: {', '.join(missing)}")
    require(not extra, f"{context}: unknown fields: {', '.join(extra)}")


def require_string(value: Any, context: str) -> str:
    require(isinstance(value, str) and bool(value.strip()), f"{context}: must be non-empty text")
    return value


def require_sha256(value: Any, context: str) -> str:
    digest = require_string(value, context)
    require(SHA256_PATTERN.fullmatch(digest) is not None, f"{context}: invalid SHA-256")
    return digest


def require_commit(value: Any, context: str) -> str:
    commit = require_string(value, context)
    require(COMMIT_PATTERN.fullmatch(commit) is not None, f"{context}: invalid commit SHA")
    return commit


def require_timestamp(value: Any, context: str) -> datetime:
    timestamp = require_string(value, context)
    require(timestamp.endswith("Z"), f"{context}: must be UTC and end in Z")
    try:
        parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    except ValueError:
        fail(f"{context}: invalid ISO 8601 timestamp")
    return parsed


def sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def normalize(value: str) -> str:
    value = value.replace("\u00a0", " ")
    value = re.sub(r"(?<=\w)-\s+(?=\w)", "", value)
    value = re.sub(r"\s+", " ", value).strip()
    value = re.sub(r"\s+([,.;:!?)\]])", r"\1", value)
    return re.sub(r"([(\[])\s+", r"\1", value)


def extract_markup(value: str) -> str:
    parser = TextExtractor()
    parser.feed(value)
    return normalize(" ".join(parser.parts))


def extract_text(path: Path, artifact_format: str) -> str:
    if artifact_format == "pdf":
        completed = subprocess.run(
            ["pdftotext", str(path), "-"],
            check=True,
            capture_output=True,
            text=True,
        )
        return normalize(completed.stdout)
    if artifact_format == "html":
        return extract_markup(path.read_text(encoding="utf-8"))
    if artifact_format == "crossref-json":
        payload = json.loads(path.read_text(encoding="utf-8"))
        abstract = payload.get("message", {}).get("abstract")
        require(isinstance(abstract, str), f"{path}: Crossref record has no abstract")
        return extract_markup(abstract)
    root = ET.parse(path).getroot()
    return normalize(" ".join(root.itertext()))


def git_bytes(*args: str, check: bool = True) -> bytes:
    completed = subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        capture_output=True,
        check=False,
    )
    if check and completed.returncode != 0:
        fail(
            f"git {' '.join(args)} failed ({completed.returncode}): "
            + completed.stderr.decode("utf-8", errors="replace").strip()
        )
    return completed.stdout


def git_text(*args: str) -> str:
    return git_bytes(*args).decode("utf-8").strip()


def packet_entries_from_worktree() -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for relative in REVIEW_PACKET_PATHS:
        payload = (REPO_ROOT / relative).read_bytes()
        entries.append({"path": relative, "sha256": sha256(payload), "bytes": len(payload)})
    return entries


def packet_digest(entries: list[dict[str, Any]]) -> str:
    hasher = hashlib.sha256()
    for entry in sorted(entries, key=lambda item: item["path"]):
        path = str(entry["path"])
        payload = (REPO_ROOT / path).read_bytes()
        hasher.update(path.encode("utf-8"))
        hasher.update(b"\0")
        hasher.update(str(len(payload)).encode("ascii"))
        hasher.update(b"\0")
        hasher.update(payload)
    return hasher.hexdigest()


def span_verification(candidate: dict[str, Any], span: dict[str, Any]) -> str:
    editions = {record["key"]: record for record in candidate["editions"]}
    pointer = span["locator"]["pointer"]
    matched = re.fullmatch(r"/excerpts/(\d+)/text", pointer)
    require(matched is not None, f"{span['key']}: unsupported excerpt pointer")
    excerpt = editions[span["edition_key"]]["content"]["excerpts"][int(matched.group(1))]
    return str(excerpt["verification"])


def verify_artifacts(artifact_dir: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    candidate = json.loads(CANDIDATE_PATH.read_text(encoding="utf-8"))
    editions = {record["key"]: record for record in candidate["editions"]}
    spans = candidate["spans"]
    verified: list[dict[str, Any]] = []
    for edition_key, spec in ARTIFACTS.items():
        edition = editions[edition_key]
        artifact = edition["content"]["artifact"]
        path = artifact_dir / str(spec["filename"])
        require(path.is_file(), f"{path}: required artifact is missing")
        payload = path.read_bytes()
        observed_digest = sha256(payload)
        require(
            observed_digest == artifact["sha256"],
            f"{path}: digest {observed_digest} does not match {artifact['sha256']}",
        )
        require(
            len(payload) == artifact["bytes"],
            f"{path}: byte length {len(payload)} does not match {artifact['bytes']}",
        )
        full_text = extract_text(path, str(spec["format"]))
        excerpt_count = 0
        for index, item in enumerate(edition["content"]["excerpts"]):
            if item["verification"] != "artifact":
                continue
            exact = normalize(item["text"])
            require(
                exact in full_text,
                f"{path}: excerpt {index} not found after deterministic normalization",
            )
            excerpt_count += 1
        verified.append(
            {
                "edition_key": edition_key,
                "filename": path.name,
                "sha256": observed_digest,
                "bytes": len(payload),
                "excerpts_verified": excerpt_count,
            }
        )

    verified_data_artifacts: list[dict[str, Any]] = []
    for (edition_key, data_index), filename in DATA_ARTIFACTS.items():
        artifact = editions[edition_key]["content"]["data_artifacts"][data_index]
        path = artifact_dir / filename
        require(path.is_file(), f"{path}: required data artifact is missing")
        payload = path.read_bytes()
        observed_digest = sha256(payload)
        require(
            observed_digest == artifact["sha256"],
            f"{path}: digest {observed_digest} does not match {artifact['sha256']}",
        )
        require(
            len(payload) == artifact["bytes"],
            f"{path}: byte length {len(payload)} does not match {artifact['bytes']}",
        )
        verified_data_artifacts.append(
            {
                "edition_key": edition_key,
                "data_index": data_index,
                "label": artifact["label"],
                "filename": path.name,
                "sha256": observed_digest,
                "bytes": len(payload),
            }
        )

    not_machine_verified = [
        {
            "span_key": record["key"],
            "edition_key": record["edition_key"],
            "verification": span_verification(candidate, record),
            "reason": "Exact provider read-back requires an independent reviewer receipt.",
        }
        for record in spans
        if span_verification(candidate, record) != "artifact"
    ]
    return candidate, {
        "verified": verified,
        "data_artifacts_verified": verified_data_artifacts,
        "not_machine_verified": not_machine_verified,
        "independent_review_complete": False,
    }


def validate_snapshot(snapshot: dict[str, Any], context: str) -> None:
    require(isinstance(snapshot, dict), f"{context}: must be an object")
    status = snapshot.get("status")
    if status == "captured":
        require_exact_fields(snapshot, {"status", "sha256", "bytes"}, context)
        require_sha256(snapshot["sha256"], f"{context}.sha256")
        require(
            isinstance(snapshot["bytes"], int) and snapshot["bytes"] > 0,
            f"{context}.bytes: must be a positive integer",
        )
    elif status == "unavailable":
        require_exact_fields(snapshot, {"status", "attempted_url", "http_failure"}, context)
        require_string(snapshot["attempted_url"], f"{context}.attempted_url")
        require_string(snapshot["http_failure"], f"{context}.http_failure")
    else:
        fail(f"{context}.status: must be captured or unavailable")


def validate_sources(
    sources: list[dict[str, Any]],
    candidate: dict[str, Any],
    machine_result: dict[str, Any],
) -> None:
    require(isinstance(sources, list) and bool(sources), "receipt.sources: must be non-empty")
    source_keys: set[str] = set()
    by_key: dict[str, dict[str, Any]] = {}
    editions = {record["key"]: record for record in candidate["editions"]}
    works = {record["key"]: record for record in candidate["source_works"]}
    for index, source in enumerate(sources):
        context = f"receipt.sources[{index}]"
        require_exact_fields(
            source,
            {
                "source_key",
                "edition_key",
                "role",
                "label",
                "url",
                "edition_label",
                "retrieved_at",
                "media_type",
                "license_treatment",
                "snapshot",
            },
            context,
        )
        key = require_string(source["source_key"], f"{context}.source_key")
        require(key not in source_keys, f"{context}.source_key: duplicate {key}")
        source_keys.add(key)
        by_key[key] = source
        edition_key = require_string(source["edition_key"], f"{context}.edition_key")
        require(edition_key in editions, f"{context}.edition_key: unknown edition")
        require(
            source["edition_label"] == editions[edition_key]["edition_label"],
            f"{context}.edition_label: does not match candidate",
        )
        require(
            source["role"] in {"primary-artifact", "data-artifact", "readback", "alternate-copy"},
            f"{context}.role: unsupported role",
        )
        for field in ("label", "url", "media_type", "license_treatment"):
            require_string(source[field], f"{context}.{field}")
        require_timestamp(source["retrieved_at"], f"{context}.retrieved_at")
        validate_snapshot(source["snapshot"], f"{context}.snapshot")

    machine = {record["edition_key"]: record for record in machine_result["verified"]}
    machine_data = {
        (record["edition_key"], record["data_index"]): record
        for record in machine_result["data_artifacts_verified"]
    }
    for edition_key, edition in editions.items():
        artifact = edition["content"]["artifact"]
        key = f"{edition_key}-primary"
        require(key in by_key, f"receipt.sources: missing {key}")
        source = by_key[key]
        require(source["role"] == "primary-artifact", f"{key}: wrong role")
        require(source["label"] == "primary artifact", f"{key}: wrong label")
        require(source["url"] == artifact["retrieved_from"], f"{key}: URL mismatch")
        require(
            source["media_type"] == PRIMARY_MEDIA_TYPES[edition_key],
            f"{key}: media type mismatch",
        )
        require(
            source["license_treatment"] == works[edition["work_key"]]["license"],
            f"{key}: license treatment mismatch",
        )
        snapshot = source["snapshot"]
        if artifact["sha256"] is None:
            require(snapshot["status"] == "unavailable", f"{key}: must record unavailable")
            require(
                snapshot["attempted_url"] == artifact["retrieved_from"],
                f"{key}: attempted URL mismatch",
            )
        else:
            require(snapshot["status"] == "captured", f"{key}: must record captured")
            require(snapshot["sha256"] == artifact["sha256"], f"{key}: digest mismatch")
            require(snapshot["bytes"] == artifact["bytes"], f"{key}: byte length mismatch")
            require(edition_key in machine, f"{key}: captured bytes were not locally verified")
            require(
                machine[edition_key]["sha256"] == snapshot["sha256"],
                f"{key}: local digest mismatch",
            )
            require(
                machine[edition_key]["bytes"] == snapshot["bytes"], f"{key}: local length mismatch"
            )

        for data_index, data_artifact in enumerate(edition["content"].get("data_artifacts", []), 1):
            data_key = f"{edition_key}-data-{data_index}"
            require(data_key in by_key, f"receipt.sources: missing {data_key}")
            data_source = by_key[data_key]
            require(data_source["role"] == "data-artifact", f"{data_key}: wrong role")
            require(data_source["label"] == data_artifact["label"], f"{data_key}: label mismatch")
            require(
                data_source["media_type"] == WORKBOOK_MEDIA_TYPE,
                f"{data_key}: media type mismatch",
            )
            require(
                data_source["url"] == data_artifact["retrieved_from"], f"{data_key}: URL mismatch"
            )
            require(
                data_source["license_treatment"] == data_artifact["license_treatment"],
                f"{data_key}: license treatment mismatch",
            )
            data_snapshot = data_source["snapshot"]
            require(data_snapshot["status"] == "captured", f"{data_key}: must be captured")
            require(
                data_snapshot["sha256"] == data_artifact["sha256"], f"{data_key}: digest mismatch"
            )
            require(
                data_snapshot["bytes"] == data_artifact["bytes"], f"{data_key}: length mismatch"
            )
            machine_key = (edition_key, data_index - 1)
            require(machine_key in machine_data, f"{data_key}: bytes were not locally verified")
            require(
                machine_data[machine_key]["sha256"] == data_snapshot["sha256"],
                f"{data_key}: local digest mismatch",
            )
            require(
                machine_data[machine_key]["bytes"] == data_snapshot["bytes"],
                f"{data_key}: local length mismatch",
            )

        for readback_index, readback in enumerate(
            edition["content"].get("readback_sources", []), 1
        ):
            readback_key = f"{edition_key}-readback-{readback_index}"
            require(readback_key in by_key, f"receipt.sources: missing {readback_key}")
            readback_source = by_key[readback_key]
            require(readback_source["role"] == "readback", f"{readback_key}: wrong role")
            require(
                readback_source["media_type"] == "text/html",
                f"{readback_key}: media type mismatch",
            )
            require(
                readback_source["license_treatment"] == works[edition["work_key"]]["license"],
                f"{readback_key}: license treatment mismatch",
            )
            require(
                readback_source["label"] == readback["label"], f"{readback_key}: label mismatch"
            )
            require(
                readback_source["url"] == readback["retrieved_from"],
                f"{readback_key}: URL mismatch",
            )


def validate_spans(spans: list[dict[str, Any]], candidate: dict[str, Any]) -> None:
    require(isinstance(spans, list) and bool(spans), "receipt.spans: must be non-empty")
    by_key: dict[str, dict[str, Any]] = {}
    for index, record in enumerate(spans):
        context = f"receipt.spans[{index}]"
        require_exact_fields(
            record,
            {
                "span_key",
                "edition_key",
                "locator",
                "expected_sha256",
                "observed_sha256",
                "verification",
                "match",
            },
            context,
        )
        key = require_string(record["span_key"], f"{context}.span_key")
        require(key not in by_key, f"{context}.span_key: duplicate {key}")
        by_key[key] = record
        require_sha256(record["expected_sha256"], f"{context}.expected_sha256")
        require_sha256(record["observed_sha256"], f"{context}.observed_sha256")
        require(record["match"] is True, f"{context}.match: must be true")

    expected_keys = {record["key"] for record in candidate["spans"]}
    require(
        set(by_key) == expected_keys, "receipt.spans: keys do not exactly match candidate spans"
    )
    for span in candidate["spans"]:
        record = by_key[span["key"]]
        expected_digest = span["digest"].removeprefix("sha256:")
        require(record["edition_key"] == span["edition_key"], f"{span['key']}: edition mismatch")
        require(record["locator"] == span["locator"]["label"], f"{span['key']}: locator mismatch")
        require(
            record["expected_sha256"] == expected_digest, f"{span['key']}: expected digest mismatch"
        )
        require(
            record["observed_sha256"] == expected_digest, f"{span['key']}: observed digest mismatch"
        )
        require(
            record["verification"] == span_verification(candidate, span),
            f"{span['key']}: verification mode mismatch",
        )


def validate_commands(commands: list[dict[str, Any]]) -> None:
    require(isinstance(commands, list) and bool(commands), "receipt.commands: must be non-empty")
    joined_commands: list[str] = []
    for index, command in enumerate(commands):
        context = f"receipt.commands[{index}]"
        require_exact_fields(
            command,
            {
                "argv",
                "cwd",
                "started_at",
                "completed_at",
                "exit_code",
                "stdout_sha256",
                "stderr_sha256",
            },
            context,
        )
        argv = command["argv"]
        require(
            isinstance(argv, list)
            and bool(argv)
            and all(isinstance(item, str) and item for item in argv),
            f"{context}.argv: must be a non-empty string array",
        )
        require_string(command["cwd"], f"{context}.cwd")
        started = require_timestamp(command["started_at"], f"{context}.started_at")
        completed = require_timestamp(command["completed_at"], f"{context}.completed_at")
        require(completed >= started, f"{context}: completion precedes start")
        require(command["exit_code"] == 0, f"{context}.exit_code: must be zero")
        require_sha256(command["stdout_sha256"], f"{context}.stdout_sha256")
        require_sha256(command["stderr_sha256"], f"{context}.stderr_sha256")
        joined_commands.append(" ".join(argv))

    required = {
        "candidate build check": lambda value: "build_candidate.py" in value and "--check" in value,
        "retrieval verification": lambda value: "verify_retrievals.py" in value,
        "full repository check": lambda value: (
            value.split()[0].endswith("make") and "check" in value.split()
        ),
    }
    for label, predicate in required.items():
        require(
            any(predicate(value) for value in joined_commands), f"receipt.commands: missing {label}"
        )


def validate_review_receipt(
    receipt_path: Path,
    candidate: dict[str, Any],
    machine_result: dict[str, Any],
) -> dict[str, Any]:
    resolved = receipt_path.resolve()
    try:
        relative_receipt = resolved.relative_to(REVIEW_RECEIPT_DIR.resolve())
    except ValueError:
        fail(f"{receipt_path}: receipt must be inside {REVIEW_RECEIPT_DIR.relative_to(REPO_ROOT)}")
    require(relative_receipt.suffix == ".json", f"{receipt_path}: receipt must be JSON")
    require(resolved.is_file(), f"{receipt_path}: receipt does not exist")
    receipt_repo_path = str(resolved.relative_to(REPO_ROOT))
    tracked = git_bytes("ls-files", "--error-unmatch", receipt_repo_path, check=False)
    require(bool(tracked.strip()), f"{receipt_path}: receipt must be tracked in Git")

    receipt = json.loads(resolved.read_text(encoding="utf-8"))
    require_exact_fields(
        receipt,
        {
            "format",
            "reviewer",
            "repository",
            "started_at",
            "completed_at",
            "git_state",
            "commands",
            "sources",
            "spans",
            "findings",
            "limitations",
            "decision",
        },
        "receipt",
    )
    require(receipt["format"] == RECEIPT_FORMAT, "receipt.format: unsupported format")
    started = require_timestamp(receipt["started_at"], "receipt.started_at")
    completed = require_timestamp(receipt["completed_at"], "receipt.completed_at")
    require(completed >= started, "receipt: completion precedes start")

    reviewer = receipt["reviewer"]
    require_exact_fields(
        reviewer,
        {
            "id",
            "fresh_clone",
            "independent_retrieval",
            "authoring_agent_artifacts_used",
            "notes",
        },
        "receipt.reviewer",
    )
    require(reviewer["id"] == "codex-independent-reviewer", "receipt.reviewer.id: wrong reviewer")
    require(reviewer["fresh_clone"] is True, "receipt.reviewer.fresh_clone: must be true")
    require(
        reviewer["independent_retrieval"] is True,
        "receipt.reviewer.independent_retrieval: must be true",
    )
    require(
        reviewer["authoring_agent_artifacts_used"] is False,
        "receipt.reviewer.authoring_agent_artifacts_used: must be false",
    )
    require_string(reviewer["notes"], "receipt.reviewer.notes")

    repository = receipt["repository"]
    require_exact_fields(
        repository,
        {
            "url",
            "reviewed_head",
            "reviewed_base",
            "reviewed_tree",
            "diff_sha256",
            "dossier_id",
            "packet_sha256",
            "candidate_files",
        },
        "receipt.repository",
    )
    require(repository["url"] == REPOSITORY_URL, "receipt.repository.url: wrong repository")
    reviewed_head = require_commit(repository["reviewed_head"], "receipt.repository.reviewed_head")
    reviewed_base = require_commit(repository["reviewed_base"], "receipt.repository.reviewed_base")
    reviewed_tree = require_commit(repository["reviewed_tree"], "receipt.repository.reviewed_tree")
    require_sha256(repository["diff_sha256"], "receipt.repository.diff_sha256")
    require_sha256(repository["packet_sha256"], "receipt.repository.packet_sha256")
    require(
        repository["dossier_id"] == candidate["dossier_id"],
        "receipt.repository.dossier_id: stale dossier identity",
    )

    require(
        git_text("rev-parse", f"{reviewed_head}^{{tree}}") == reviewed_tree,
        "receipt.repository.reviewed_tree: does not match reviewed head",
    )
    require(
        git_text("merge-base", reviewed_base, reviewed_head) == reviewed_base,
        "receipt.repository.reviewed_base: is not an ancestor of reviewed head",
    )
    require(
        git_text("rev-parse", "origin/main") == reviewed_base,
        "receipt.repository.reviewed_base: origin/main changed; fresh review required",
    )
    ancestry = subprocess.run(
        ["git", "merge-base", "--is-ancestor", reviewed_head, "HEAD"],
        cwd=REPO_ROOT,
        check=False,
    )
    require(ancestry.returncode == 0, "receipt.repository.reviewed_head: not an ancestor of HEAD")
    changed_after_review = set(
        filter(None, git_text("diff", "--name-only", reviewed_head, "HEAD").splitlines())
    )
    allowed_prefix = str(REVIEW_RECEIPT_DIR.relative_to(REPO_ROOT)) + "/"
    require(
        all(path.startswith(allowed_prefix) for path in changed_after_review),
        "reviewed packet changed after review receipt was authored",
    )

    observed_diff = git_bytes(
        "diff",
        "--binary",
        "--full-index",
        "--no-ext-diff",
        reviewed_base,
        reviewed_head,
        "--",
        str(RESEARCH_DIR.relative_to(REPO_ROOT)),
    )
    require(
        sha256(observed_diff) == repository["diff_sha256"],
        "receipt.repository.diff_sha256: stale diff",
    )

    expected_entries = packet_entries_from_worktree()
    candidate_files = repository["candidate_files"]
    require(
        isinstance(candidate_files, list), "receipt.repository.candidate_files: must be an array"
    )
    for index, entry in enumerate(candidate_files):
        require_exact_fields(entry, {"path", "sha256", "bytes"}, f"candidate_files[{index}]")
        require_string(entry["path"], f"candidate_files[{index}].path")
        require_sha256(entry["sha256"], f"candidate_files[{index}].sha256")
        require(
            isinstance(entry["bytes"], int) and entry["bytes"] > 0,
            f"candidate_files[{index}].bytes: must be positive",
        )
    require(candidate_files == expected_entries, "receipt.repository.candidate_files: stale packet")
    require(
        repository["packet_sha256"] == packet_digest(expected_entries),
        "receipt.repository.packet_sha256: stale packet digest",
    )
    for entry in expected_entries:
        committed = git_bytes("show", f"{reviewed_head}:{entry['path']}")
        require(
            sha256(committed) == entry["sha256"], f"{entry['path']}: differs from reviewed head"
        )
        require(
            len(committed) == entry["bytes"], f"{entry['path']}: length differs from reviewed head"
        )

    git_state = receipt["git_state"]
    require_exact_fields(
        git_state,
        {
            "fresh_clone",
            "pre_review_clean",
            "post_review_clean",
            "unchanged_during_review",
            "pre_review_head",
            "post_review_head",
        },
        "receipt.git_state",
    )
    for field in (
        "fresh_clone",
        "pre_review_clean",
        "post_review_clean",
        "unchanged_during_review",
    ):
        require(git_state[field] is True, f"receipt.git_state.{field}: must be true")
    require(
        git_state["pre_review_head"] == reviewed_head, "receipt.git_state.pre_review_head mismatch"
    )
    require(
        git_state["post_review_head"] == reviewed_head,
        "receipt.git_state.post_review_head mismatch",
    )
    require(not git_text("status", "--porcelain"), "current worktree is not clean")

    validate_commands(receipt["commands"])
    validate_sources(receipt["sources"], candidate, machine_result)
    validate_spans(receipt["spans"], candidate)

    findings = receipt["findings"]
    require(isinstance(findings, list), "receipt.findings: must be an array")
    for index, finding in enumerate(findings):
        require_exact_fields(
            finding,
            {"severity", "status", "text"},
            f"receipt.findings[{index}]",
        )
        require(
            finding["severity"] in {"material", "minor", "informational"},
            f"receipt.findings[{index}].severity: unsupported",
        )
        require(
            finding["status"] in {"resolved", "informational"},
            f"receipt.findings[{index}].status: unresolved finding",
        )
        require_string(finding["text"], f"receipt.findings[{index}].text")
    limitations = receipt["limitations"]
    require(
        isinstance(limitations, list)
        and bool(limitations)
        and all(isinstance(item, str) and item for item in limitations),
        "receipt.limitations: must be a non-empty string array",
    )
    require(receipt["decision"] == "pass", "receipt.decision: must be pass")

    return {
        "format": receipt["format"],
        "reviewer_id": reviewer["id"],
        "reviewed_head": reviewed_head,
        "reviewed_base": reviewed_base,
        "reviewed_tree": reviewed_tree,
        "receipt_path": receipt_repo_path,
        "decision": receipt["decision"],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-dir", type=Path, default=Path("/tmp"))
    parser.add_argument("--review-receipt", type=Path)
    parser.add_argument("--require-complete", action="store_true")
    args = parser.parse_args()
    candidate, result = verify_artifacts(args.artifact_dir)
    if args.review_receipt is not None:
        result["review_receipt"] = validate_review_receipt(
            args.review_receipt,
            candidate,
            result,
        )
        result["independent_review_complete"] = True
    print(json.dumps(result, indent=2))
    if args.require_complete and not result["independent_review_complete"]:
        fail("independent source-span review is incomplete: provide a valid --review-receipt")


if __name__ == "__main__":
    main()
