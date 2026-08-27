"""Fail-closed verification for the EM-0033 candidate research packet."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from build_packet import REQUIRED_LINEAGE_DIMENSIONS, build_derivations, build_packet

PACKET_ROOT = Path(__file__).resolve().parent
REPO_ROOT = PACKET_ROOT.parents[2]
SOURCE_RECORDS = PACKET_ROOT / "source-records.json"
CANDIDATE_PACKET = PACKET_ROOT / "candidate-packet.json"
DEFAULT_REVIEW_RECEIPT = PACKET_ROOT / "independent-review-receipt.json"
REPOSITORY_URL = "https://github.com/yoheinakajima/epistemedia"
REVIEW_FORMAT = "epistemedia-independent-research-review-v1"

EXPECTED_PACKET_ID = (
    "em:research-packet:sha256:8fc01c0581ede49eddcdf122c993506d5bc4eb33289628970bf7303d8aa71504"
)
EXPECTED_SOURCE_RECORDS = {
    "bytes": 52631,
    "sha256": "7a8158c560006da8d471d4bcaae689829e39790900d55da572fdbf610ebecf66",
}
EXPECTED_CANDIDATE_PACKET = {
    "bytes": 63817,
    "sha256": "ab3d2ca49c107b54b2d2eb7f4ac08db84ab2aa6d971a8b933d9980b56cef396e",
}
EXPECTED_SOURCE_IDS = {
    "source-argyle-1970",
    "source-argyle-1971",
    "source-birmingham-events-2020",
    "source-hampshire-pcc-2022",
    "source-hegstrom-1979",
    "source-lapakko-1997",
    "source-lapakko-2007",
    "source-mehrabian-author-qualification",
    "source-mehrabian-ferris-1967",
    "source-mehrabian-wiener-1967",
    "source-silent-messages-1971",
    "source-silent-messages-1981",
}
EXPECTED_CLAIM_IDS = {
    "claim-1981-edition",
    "claim-book-boundary",
    "claim-hegstrom-rebuttal",
    "claim-p1-tone-dominance",
    "claim-p2-face-tone",
    "claim-popular-rule",
    "claim-propagation",
    "claim-related-context",
    "claim-replication-search",
    "claim-seven-origin",
    "claim-three-coefficient-proposal",
}
EXPECTED_DERIVATION_IDS = {
    "derive-implied-vocal-verbal-ratio",
    "derive-p2-allocation-with-seven-reserved",
    "derive-p2-facial-vocal-ratio",
    "derive-proposed-facial-vocal-ratio",
    "derive-proposed-sum",
    "derive-ratio-difference",
}
EXPECTED_LINEAGE_EDGE_IDS = {
    "edge-p1-p2-author-social",
    "edge-p1-p2-grant",
    "edge-p1-p2-material",
    "edge-p1-p2-method",
    "edge-p1-p2-participant",
    "edge-p1-p2-scale",
    "edge-p1-p2-speaker",
    "edge-p1-p2-stimulus",
    "edge-p1-p2-proposal-derivation",
    "edge-p2-cites-p1",
    "edge-silent-messages-editions",
}
EXPECTED_PROPAGATION_IDS = {
    "propagation-birmingham-events",
    "propagation-hampshire-pcc",
    "propagation-lapakko-web-sample",
}


def fail(message: str) -> None:
    raise SystemExit(message)


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"cannot parse {path}: {exc}")
    require(isinstance(value, dict), f"{path}: root must be an object")
    return value


def sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def identity(path: Path) -> dict[str, Any]:
    payload = path.read_bytes()
    return {"bytes": len(payload), "sha256": sha256(payload)}


def git_bytes(*args: str, check: bool = True) -> bytes:
    result = subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
    )
    if check and result.returncode != 0:
        fail(f"git {' '.join(args)} failed: {result.stderr.decode(errors='replace').strip()}")
    return result.stdout


def git_text(*args: str, check: bool = True) -> str:
    return git_bytes(*args, check=check).decode().strip()


def require_exact_fields(value: Any, fields: set[str], context: str) -> None:
    require(isinstance(value, dict), f"{context}: must be an object")
    actual = set(value)
    require(actual == fields, f"{context}: fields differ: {sorted(actual ^ fields)}")


def require_string(value: Any, context: str) -> str:
    require(isinstance(value, str) and value.strip(), f"{context}: must be a string")
    return value


def require_sha256(value: Any, context: str) -> str:
    require_string(value, context)
    require(bool(re.fullmatch(r"[0-9a-f]{64}", value)), f"{context}: invalid SHA-256")
    return value


def require_commit(value: Any, context: str) -> str:
    require_string(value, context)
    require(bool(re.fullmatch(r"[0-9a-f]{40}", value)), f"{context}: invalid Git identity")
    return value


def require_timestamp(value: Any, context: str) -> datetime:
    require_string(value, context)
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        fail(f"{context}: invalid timestamp: {exc}")


def collect_ids(packet: dict[str, Any]) -> dict[str, set[str]]:
    content = packet["content"]
    sources = content["source_records"]
    return {
        "source_ids": {item["source_id"] for item in sources},
        "capture_ids": {
            capture["capture_id"] for source in sources for capture in source["captures"]
        },
        "span_ids": {
            span["span_id"] for source in sources for span in source.get("spans", [])
        },
        "claim_ids": {item["claim_id"] for item in content["claims"]},
        "derivation_ids": {item["derivation_id"] for item in content["derivations"]},
        "lineage_edge_ids": {item["edge_id"] for item in content["lineage_edges"]},
        "propagation_ids": {item["object_id"] for item in content["propagation_ledger"]},
        "follow_up_source_ids": {item["source_id"] for item in content["follow_up_ledger"]},
    }


def close(actual: float, expected: float, tolerance: float = 1e-12) -> bool:
    return abs(actual - expected) <= tolerance


def independently_recompute_derivations(packet: dict[str, Any]) -> None:
    content = packet["content"]
    observed = {item["derivation_id"]: item for item in content["derivations"]}
    expected = {
        item["derivation_id"]: item for item in build_derivations(content["derivation_inputs"])
    }
    require(set(observed) == set(expected), "derivation ID drift")
    for derivation_id, expected_item in expected.items():
        observed_result = observed[derivation_id]["result"]
        expected_result = expected_item["result"]
        if isinstance(expected_result, dict):
            require(
                set(observed_result) == set(expected_result),
                f"result fields drift: {derivation_id}",
            )
            for key, value in expected_result.items():
                require(close(observed_result[key], value), f"result drift: {derivation_id}.{key}")
        else:
            require(close(observed_result, expected_result), f"result drift: {derivation_id}")


def verify_packet() -> tuple[dict[str, Any], dict[str, Any]]:
    packet = load(CANDIDATE_PACKET)
    require(packet == build_packet(), "candidate packet deterministic rebuild drift")
    require(packet["packet_id"] == EXPECTED_PACKET_ID, "candidate packet ID drift")
    require(identity(SOURCE_RECORDS) == EXPECTED_SOURCE_RECORDS, "source-record identity drift")
    require(identity(CANDIDATE_PACKET) == EXPECTED_CANDIDATE_PACKET, "candidate identity drift")

    ids = collect_ids(packet)
    require(ids["source_ids"] == EXPECTED_SOURCE_IDS, "source set drift")
    require(ids["claim_ids"] == EXPECTED_CLAIM_IDS, "claim set drift")
    require(ids["derivation_ids"] == EXPECTED_DERIVATION_IDS, "derivation set drift")
    require(ids["lineage_edge_ids"] == EXPECTED_LINEAGE_EDGE_IDS, "lineage edge set drift")
    require(ids["propagation_ids"] == EXPECTED_PROPAGATION_IDS, "propagation set drift")

    content = packet["content"]
    counts = content["counts"]
    expected_counts = {
        "source_records": 12,
        "quote_minimal_spans": 40,
        "claims": 11,
        "derivations": 6,
        "lineage_groups": 6,
        "lineage_edges": 11,
        "propagation_objects": 3,
        "follow_up_objects": 5,
        "participant_data_roots": 5,
    }
    require(counts == expected_counts, "packet count drift")
    require(
        {item["dimension"] for item in content["lineage_edges"]}
        == REQUIRED_LINEAGE_DIMENSIONS,
        "lineage dimension drift",
    )
    require(
        content["recommendation"] == load(SOURCE_RECORDS)["recommendation"],
        "recommendation projection drift",
    )
    require(content["recommendation"]["author"] == "GO", "author recommendation drift")
    require(
        content["recommendation"]["independent_review"] == "pending",
        "candidate packet self-approved",
    )
    require(
        "93 percent of all communication is nonverbal"
        in content["recommendation"]["prohibited_interpretations"],
        "general-rule prohibition missing",
    )
    require(
        all(item["scientific_rule_evidence_credit"] == 0 for item in content["propagation_ledger"]),
        "propagation evidence-credit drift",
    )
    require(not list(PACKET_ROOT.glob("*.pdf")), "restricted PDF committed beside packet")
    require(not list(PACKET_ROOT.glob("*.html")), "raw HTML committed beside packet")
    require(not list(PACKET_ROOT.glob("*.xml")), "raw XML committed beside packet")
    independently_recompute_derivations(packet)
    return packet, {
        "packet_id": packet["packet_id"],
        "source_records": identity(SOURCE_RECORDS),
        "candidate_packet": identity(CANDIDATE_PACKET),
        "ids": ids,
        "counts": counts,
        "author_recommendation": content["recommendation"]["author"],
    }


def require_exact_coverage(actual: Any, expected: set[str], context: str) -> None:
    require(isinstance(actual, list), f"{context}: must be an array")
    require(actual == sorted(expected), f"{context}: incomplete or unsorted coverage")


def validate_commands(commands: Any) -> None:
    require(isinstance(commands, list) and commands, "receipt.commands: must be non-empty")
    rendered = []
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
            and argv
            and all(isinstance(item, str) and item for item in argv),
            f"{context}.argv: invalid",
        )
        require_string(command["cwd"], f"{context}.cwd")
        started = require_timestamp(command["started_at"], f"{context}.started_at")
        completed = require_timestamp(command["completed_at"], f"{context}.completed_at")
        require(completed >= started, f"{context}: completion precedes start")
        require(command["exit_code"] == 0, f"{context}.exit_code: must be zero")
        require_sha256(command["stdout_sha256"], f"{context}.stdout_sha256")
        require_sha256(command["stderr_sha256"], f"{context}.stderr_sha256")
        rendered.append(" ".join(argv))
    required = {
        "packet build": lambda value: "build_packet.py" in value and "--check" in value,
        "packet verification": lambda value: "verify_packet.py" in value,
        "repository check": lambda value: "make check" in value,
    }
    for label, predicate in required.items():
        require(any(predicate(value) for value in rendered), f"receipt.commands: missing {label}")


def validate_review_results(results: Any, summary: dict[str, Any]) -> None:
    require_exact_fields(
        results,
        {"sources", "spans", "derivations", "lineage_edges"},
        "review_results",
    )
    source_records = results["sources"]
    require(isinstance(source_records, list), "review_results.sources: must be an array")
    source_ids = set()
    reviewed_capture_ids = set()
    for index, record in enumerate(source_records):
        context = f"review_results.sources[{index}]"
        require_exact_fields(
            record,
            {
                "source_id",
                "capture_ids",
                "identity_checked",
                "access_and_gap_checked",
                "license_checked",
                "status",
            },
            context,
        )
        source_ids.add(require_string(record["source_id"], f"{context}.source_id"))
        require_exact_coverage(
            record["capture_ids"],
            set(record["capture_ids"]),
            f"{context}.capture_ids",
        )
        reviewed_capture_ids.update(record["capture_ids"])
        for field in ("identity_checked", "access_and_gap_checked", "license_checked"):
            require(record[field] is True, f"{context}.{field}: must be true")
        require(
            record["status"] in {"pass", "pass-with-declared-gap"},
            f"{context}.status: not pass",
        )
    require(source_ids == summary["ids"]["source_ids"], "source result coverage drift")
    require(
        reviewed_capture_ids == summary["ids"]["capture_ids"],
        "capture result coverage drift",
    )

    span_records = results["spans"]
    require(isinstance(span_records, list), "review_results.spans: must be an array")
    require(
        {item.get("span_id") for item in span_records} == summary["ids"]["span_ids"],
        "span result coverage drift",
    )
    for index, record in enumerate(span_records):
        context = f"review_results.spans[{index}]"
        require_exact_fields(record, {"span_id", "verification", "match"}, context)
        require_string(record["verification"], f"{context}.verification")
        require(record["match"] is True, f"{context}.match: must be true")

    derivation_records = results["derivations"]
    require(isinstance(derivation_records, list), "review_results.derivations: must be an array")
    require(
        {item.get("derivation_id") for item in derivation_records}
        == summary["ids"]["derivation_ids"],
        "derivation result coverage drift",
    )
    for index, record in enumerate(derivation_records):
        context = f"review_results.derivations[{index}]"
        require_exact_fields(record, {"derivation_id", "reproduced"}, context)
        require(record["reproduced"] is True, f"{context}.reproduced: must be true")

    edge_records = results["lineage_edges"]
    require(isinstance(edge_records, list), "review_results.lineage_edges: must be an array")
    require(
        {item.get("edge_id") for item in edge_records}
        == summary["ids"]["lineage_edge_ids"],
        "lineage result coverage drift",
    )
    for index, record in enumerate(edge_records):
        context = f"review_results.lineage_edges[{index}]"
        require_exact_fields(
            record,
            {"edge_id", "evidence_checked", "independence_effect_checked", "status"},
            context,
        )
        require(record["evidence_checked"] is True, f"{context}.evidence_checked: must be true")
        require(
            record["independence_effect_checked"] is True,
            f"{context}.independence_effect_checked: must be true",
        )
        require(record["status"] == "pass", f"{context}.status: must be pass")


def validate_receipt_document(
    receipt: dict[str, Any],
    packet: dict[str, Any],
    summary: dict[str, Any],
    *,
    check_git: bool,
) -> None:
    require_exact_fields(
        receipt,
        {
            "format",
            "task_id",
            "reviewer",
            "repository",
            "started_at",
            "completed_at",
            "git_state",
            "bindings",
            "coverage",
            "review_results",
            "commands",
            "findings",
            "limitations",
            "recommendation",
            "decision",
            "complete",
        },
        "receipt",
    )
    require(receipt["format"] == REVIEW_FORMAT, "receipt.format: unsupported")
    require(receipt["task_id"] == "EM-0033", "receipt.task_id: mismatch")
    started = require_timestamp(receipt["started_at"], "receipt.started_at")
    completed = require_timestamp(receipt["completed_at"], "receipt.completed_at")
    require(completed >= started, "receipt: completion precedes start")

    reviewer = receipt["reviewer"]
    require_exact_fields(
        reviewer,
        {
            "id",
            "role",
            "fresh_clone",
            "reviewer_was_author",
            "independent_public_retrieval",
            "authoring_notes_used_as_evidence",
            "notes",
        },
        "receipt.reviewer",
    )
    require(
        reviewer["id"] == "codex-independent-em0033-reviewer",
        "receipt.reviewer.id: wrong reviewer",
    )
    require(reviewer["role"] == "independent-reviewer", "receipt.reviewer.role: mismatch")
    require(reviewer["fresh_clone"] is True, "receipt.reviewer.fresh_clone: must be true")
    require(
        reviewer["reviewer_was_author"] is False,
        "receipt.reviewer.reviewer_was_author: must be false",
    )
    require(
        reviewer["independent_public_retrieval"] is True,
        "receipt.reviewer.independent_public_retrieval: must be true",
    )
    require(
        reviewer["authoring_notes_used_as_evidence"] is False,
        "receipt.reviewer.authoring_notes_used_as_evidence: must be false",
    )
    require_string(reviewer["notes"], "receipt.reviewer.notes")

    bindings = receipt["bindings"]
    require_exact_fields(bindings, {"packet_id", "source_records", "candidate_packet"}, "bindings")
    require(bindings["packet_id"] == summary["packet_id"], "receipt packet ID drift")
    require(bindings["source_records"] == summary["source_records"], "receipt source drift")
    require(bindings["candidate_packet"] == summary["candidate_packet"], "receipt packet drift")

    coverage = receipt["coverage"]
    require_exact_fields(
        coverage,
        {
            "source_ids",
            "capture_ids",
            "span_ids",
            "claim_ids",
            "derivation_ids",
            "lineage_edge_ids",
            "propagation_ids",
            "follow_up_source_ids",
        },
        "coverage",
    )
    for key, expected in summary["ids"].items():
        require_exact_coverage(coverage[key], expected, f"receipt.coverage.{key}")
    validate_review_results(receipt["review_results"], summary)

    require(receipt["recommendation"] == summary["author_recommendation"], "review differs")
    require(receipt["decision"] == "pass", "receipt.decision: must be pass")
    require(receipt["complete"] is True, "receipt.complete: must be true")
    limitations = receipt["limitations"]
    require(
        isinstance(limitations, list)
        and limitations
        and all(isinstance(item, str) and item.strip() for item in limitations),
        "receipt.limitations: must be non-empty",
    )
    findings = receipt["findings"]
    require(isinstance(findings, list), "receipt.findings: must be an array")
    for index, finding in enumerate(findings):
        require_exact_fields(finding, {"severity", "status", "text"}, f"findings[{index}]")
        require(finding["status"] in {"resolved", "informational"}, "unresolved finding")
        require(finding["severity"] in {"material", "minor", "informational"}, "bad severity")
        require_string(finding["text"], f"findings[{index}].text")
    validate_commands(receipt["commands"])

    repository = receipt["repository"]
    require_exact_fields(
        repository,
        {
            "url",
            "pull_request",
            "branch",
            "reviewed_base",
            "reviewed_author_head",
            "reviewed_author_tree",
            "diff_sha256",
        },
        "repository",
    )
    require(repository["url"] == REPOSITORY_URL, "receipt repository URL mismatch")
    require(repository["pull_request"] > 0, "receipt pull request invalid")
    require_string(repository["branch"], "receipt.repository.branch")
    base = require_commit(repository["reviewed_base"], "receipt.repository.reviewed_base")
    head = require_commit(
        repository["reviewed_author_head"], "receipt.repository.reviewed_author_head"
    )
    tree = require_commit(
        repository["reviewed_author_tree"], "receipt.repository.reviewed_author_tree"
    )
    require_sha256(repository["diff_sha256"], "receipt.repository.diff_sha256")

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
        "git_state",
    )
    clean_fields = (
        "fresh_clone",
        "pre_review_clean",
        "post_review_clean",
        "unchanged_during_review",
    )
    for field in clean_fields:
        require(git_state[field] is True, f"receipt.git_state.{field}: must be true")
    require(git_state["pre_review_head"] == head, "pre-review head mismatch")
    require(git_state["post_review_head"] == head, "post-review head mismatch")

    if not check_git:
        return
    require(git_text("rev-parse", f"{head}^{{tree}}") == tree, "reviewed tree mismatch")
    require(git_text("merge-base", base, head) == base, "reviewed base is not merge-base")
    origin_main = git_text("rev-parse", "origin/main")
    require(origin_main == base, "reviewed base is stale")
    require(git_text("merge-base", origin_main, head) == origin_main, "main not in author head")
    require(
        subprocess.run(
            ["git", "merge-base", "--is-ancestor", head, "HEAD"], cwd=REPO_ROOT, check=False
        ).returncode
        == 0,
        "reviewed author head is not an ancestor of HEAD",
    )
    changed_after = set(filter(None, git_text("diff", "--name-only", head, "HEAD").splitlines()))
    receipt_rel = str(DEFAULT_REVIEW_RECEIPT.relative_to(REPO_ROOT))
    require(changed_after == {receipt_rel}, "candidate changed after independent review")
    diff = git_bytes("diff", "--binary", "--full-index", "--no-ext-diff", base, head)
    require(sha256(diff) == repository["diff_sha256"], "review diff digest mismatch")
    require(not git_text("status", "--porcelain"), "current tracked or untracked state is dirty")
    tracked = git_text("ls-files", "--error-unmatch", receipt_rel, check=False)
    require(bool(tracked), "independent receipt must be tracked")


def valid_shape_fixture(packet: dict[str, Any], summary: dict[str, Any]) -> dict[str, Any]:
    empty_digest = sha256(b"")
    now = "2026-08-27T00:00:00Z"
    return {
        "format": REVIEW_FORMAT,
        "task_id": "EM-0033",
        "reviewer": {
            "id": "codex-independent-em0033-reviewer",
            "role": "independent-reviewer",
            "fresh_clone": True,
            "reviewer_was_author": False,
            "independent_public_retrieval": True,
            "authoring_notes_used_as_evidence": False,
            "notes": "Shape-only adversarial fixture.",
        },
        "repository": {
            "url": REPOSITORY_URL,
            "pull_request": 1,
            "branch": "fixture",
            "reviewed_base": "0" * 40,
            "reviewed_author_head": "1" * 40,
            "reviewed_author_tree": "2" * 40,
            "diff_sha256": empty_digest,
        },
        "started_at": now,
        "completed_at": now,
        "git_state": {
            "fresh_clone": True,
            "pre_review_clean": True,
            "post_review_clean": True,
            "unchanged_during_review": True,
            "pre_review_head": "1" * 40,
            "post_review_head": "1" * 40,
        },
        "bindings": {
            "packet_id": summary["packet_id"],
            "source_records": summary["source_records"],
            "candidate_packet": summary["candidate_packet"],
        },
        "coverage": {key: sorted(value) for key, value in summary["ids"].items()},
        "review_results": {
            "sources": [
                {
                    "source_id": source["source_id"],
                    "capture_ids": sorted(item["capture_id"] for item in source["captures"]),
                    "identity_checked": True,
                    "access_and_gap_checked": True,
                    "license_checked": True,
                    "status": "pass",
                }
                for source in packet["content"]["source_records"]
            ],
            "spans": [
                {"span_id": span_id, "verification": "fixture", "match": True}
                for span_id in sorted(summary["ids"]["span_ids"])
            ],
            "derivations": [
                {"derivation_id": derivation_id, "reproduced": True}
                for derivation_id in sorted(summary["ids"]["derivation_ids"])
            ],
            "lineage_edges": [
                {
                    "edge_id": edge_id,
                    "evidence_checked": True,
                    "independence_effect_checked": True,
                    "status": "pass",
                }
                for edge_id in sorted(summary["ids"]["lineage_edge_ids"])
            ],
        },
        "commands": [
            {
                "argv": ["python", "build_packet.py", "--check"],
                "cwd": ".",
                "started_at": now,
                "completed_at": now,
                "exit_code": 0,
                "stdout_sha256": empty_digest,
                "stderr_sha256": empty_digest,
            },
            {
                "argv": ["python", "verify_packet.py"],
                "cwd": ".",
                "started_at": now,
                "completed_at": now,
                "exit_code": 0,
                "stdout_sha256": empty_digest,
                "stderr_sha256": empty_digest,
            },
            {
                "argv": ["make", "check"],
                "cwd": ".",
                "started_at": now,
                "completed_at": now,
                "exit_code": 0,
                "stdout_sha256": empty_digest,
                "stderr_sha256": empty_digest,
            },
        ],
        "findings": [],
        "limitations": ["Shape-only fixture; no empirical pass is inferred."],
        "recommendation": summary["author_recommendation"],
        "decision": "pass",
        "complete": True,
    }


def run_adversarial_self_test(packet: dict[str, Any], summary: dict[str, Any]) -> None:
    fixture = valid_shape_fixture(packet, summary)
    validate_receipt_document(fixture, packet, summary, check_git=False)
    mutations = [
        lambda value: value["reviewer"].update({"reviewer_was_author": True}),
        lambda value: value["reviewer"].update({"authoring_notes_used_as_evidence": True}),
        lambda value: value["bindings"].update({"packet_id": "stale"}),
        lambda value: value["coverage"]["span_ids"].pop(),
        lambda value: value["review_results"]["spans"].pop(),
        lambda value: value["review_results"]["lineage_edges"][0].update(
            {"evidence_checked": False}
        ),
        lambda value: value.update({"limitations": []}),
        lambda value: value.update({"complete": False}),
        lambda value: value["commands"].pop(),
        lambda value: value.update(
            {"findings": [{"severity": "material", "status": "open", "text": "gap"}]}
        ),
    ]
    for index, mutate in enumerate(mutations):
        forged = copy.deepcopy(fixture)
        mutate(forged)
        try:
            validate_receipt_document(forged, packet, summary, check_git=False)
        except SystemExit:
            continue
        fail(f"adversarial receipt mutation {index} was accepted")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--review-receipt", type=Path, default=DEFAULT_REVIEW_RECEIPT)
    parser.add_argument("--require-review", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    packet, summary = verify_packet()
    if args.self_test:
        run_adversarial_self_test(packet, summary)
        summary["adversarial_receipt_tests"] = "passed"
    review = None
    if args.review_receipt.is_file() or args.require_review:
        require(args.review_receipt.is_file(), "independent review receipt missing")
        review = load(args.review_receipt)
        validate_receipt_document(review, packet, summary, check_git=True)
    summary["independent_review_complete"] = review is not None
    if review is not None:
        summary["reviewer"] = review["reviewer"]["id"]
        summary["review_decision"] = review["decision"]
    summary.pop("ids")
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
